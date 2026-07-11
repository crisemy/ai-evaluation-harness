from __future__ import annotations

import argparse
import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from harness.ci import BadgeGenerator
from harness.comparison import CompareConfig, ComparisonEngine, ModelSpec
from harness.contracts.risk import (
    ChangeType,
    HistoricalStability,
    RiskProfile,
    SafetyRelevance,
)
from harness.contracts.trace import ObservableEvent
from harness.errors import HarnessError
from harness.escalation import EscalationEngine, GateAction
from harness.evaluator import EvalSample, EvaluationConfigInput, EvaluationEngine
from harness.prompt_regression import PromptEntry, PromptRegressionMetric, PromptRegistry, PromptVersion
from harness.red_team import RedTeamExecutor
from harness.scheduler import EvalSchedule, SchedulerEngine
from harness.evaluator_rag import RAGEvaluator, RAGSample
from harness.evaluator_agent import AgentEvaluator, AgentSample, AgentTrajectory
from harness.executor import ExecutorConfig, PromptExecutor
from harness.loaders import JSONDatasetLoader
from harness.metrics import Contains, ExactMatch
from harness.metrics.rag import Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall
from harness.metrics.agent import StepCorrectness, GoalAchievement, ToolSelection, TrajectoryCoherence
from harness.observability import AlertEngine, AlertRule, DashboardGenerator, TimeSeriesStore
from harness.observers import TraceObserver
from harness.providers import OllamaProvider
from harness.providers.context import DatasetContextProvider
from harness.reporters import JSONReporter

logger = logging.getLogger(__name__)

METRIC_REGISTRY = {
    "exact_match": ExactMatch,
    "contains": Contains,
    "faithfulness": Faithfulness,
    "answer_relevancy": AnswerRelevancy,
    "context_precision": ContextPrecision,
    "context_recall": ContextRecall,
    "step_correctness": StepCorrectness,
    "goal_achievement": GoalAchievement,
    "tool_selection": ToolSelection,
    "trajectory_coherence": TrajectoryCoherence,
}


def _add_ci_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--ci-env", default="local", help="CI environment name (local, ci, staging, prod)")
    parser.add_argument("--release-id", default="", help="Release or PR identifier")
    parser.add_argument("--execution-id", default="", help="Unique execution identifier")
    parser.add_argument("--owner", default="", help="Owner or trigger of the evaluation")
    parser.add_argument("--coverage-min", type=float, default=0.0,
                        help="Minimum evaluation coverage fraction (fails if limit reduces below this)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="harness",
        description="AI Evaluation Harness — evaluate LLM prompt responses",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    eval_ = sub.add_parser("eval", help="Run a standard evaluation")
    eval_.add_argument("--dataset", "-d", required=True, help="Path to dataset file")
    eval_.add_argument("--provider", "-p", default="ollama", help="Provider name")
    eval_.add_argument("--model", "-m", default="phi3", help="Model name")
    eval_.add_argument(
        "--metrics", nargs="+", default=["exact_match", "contains"], help="Metrics to apply"
    )
    eval_.add_argument("--output", "-o", default="report.json", help="Output report path")
    eval_.add_argument("--temperature", type=float, default=0.1, help="Temperature")
    eval_.add_argument("--max-tokens", type=int, default=256, help="Max tokens per response")
    eval_.add_argument("--limit", type=int, default=0, help="Limit number of entries (0 = all)")
    eval_.add_argument("--change-type", choices=[t.value for t in ChangeType],
                       default=None, help="CORE risk change type for risk-based evaluation")
    eval_.add_argument("--safety-relevance", choices=[s.value for s in SafetyRelevance],
                       default=None, help="Safety relevance level for risk scoring")
    eval_.add_argument("--historical-stability", choices=[h.value for h in HistoricalStability],
                       default=None, help="Historical stability for risk multiplier")
    eval_.add_argument("--gate", choices=["pass", "warning", "block"], default=None,
                       help="Escalation gate: exit code reflects severity of failures")
    _add_ci_args(eval_)
    eval_.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    rag_ = sub.add_parser("rag-eval", help="Run a RAG evaluation with context documents")
    rag_.add_argument("--dataset", "-d", required=True, help="Path to RAG dataset file")
    rag_.add_argument("--provider", "-p", default="ollama", help="Provider name")
    rag_.add_argument("--model", "-m", default="phi3", help="Model name")
    rag_.add_argument(
        "--metrics", nargs="+", default=["faithfulness", "answer_relevancy", "context_precision", "context_recall"],
        help="RAG metrics to apply",
    )
    rag_.add_argument("--output", "-o", default="rag_report.json", help="Output report path")
    rag_.add_argument("--temperature", type=float, default=0.1, help="Temperature")
    rag_.add_argument("--max-tokens", type=int, default=512, help="Max tokens per response")
    rag_.add_argument("--limit", type=int, default=0, help="Limit number of entries (0 = all)")
    _add_ci_args(rag_)
    rag_.add_argument("--gate", choices=["pass", "warning", "block"], default=None,
                      help="Escalation gate: exit code reflects severity of failures")
    rag_.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    agent_ = sub.add_parser("agent-eval", help="Run an agent trajectory evaluation")
    agent_.add_argument("--dataset", "-d", required=True, help="Path to agent dataset file")
    agent_.add_argument("--provider", "-p", default="ollama", help="Provider name")
    agent_.add_argument("--model", "-m", default="phi3", help="Model name")
    agent_.add_argument(
        "--metrics", nargs="+",
        default=["step_correctness", "goal_achievement", "tool_selection", "trajectory_coherence"],
        help="Agent metrics to apply",
    )
    agent_.add_argument("--output", "-o", default="agent_report.json", help="Output report path")
    agent_.add_argument("--temperature", type=float, default=0.1, help="Temperature")
    agent_.add_argument("--max-tokens", type=int, default=512, help="Max tokens per response")
    agent_.add_argument("--limit", type=int, default=0, help="Limit number of entries (0 = all)")
    agent_.add_argument("--gate", choices=["pass", "warning", "block"], default=None,
                        help="Escalation gate: exit code reflects severity of failures")
    _add_ci_args(agent_)
    agent_.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    cmp_ = sub.add_parser("compare", help="Compare multiple models on the same dataset")
    cmp_.add_argument("--dataset", "-d", required=True, help="Path to dataset file")
    cmp_.add_argument(
        "--models", nargs="+", default=["phi3", "llama3.2"],
        help="Model names to compare (space-separated)",
    )
    cmp_.add_argument("--provider", "-p", default="ollama", help="Provider name")
    cmp_.add_argument(
        "--metrics", nargs="+", default=["exact_match", "contains"], help="Metrics to apply"
    )
    cmp_.add_argument("--output", "-o", default="comparison_report.json", help="Output report path")
    cmp_.add_argument("--temperature", type=float, default=0.1, help="Temperature")
    cmp_.add_argument("--max-tokens", type=int, default=256, help="Max tokens per response")
    cmp_.add_argument("--limit", type=int, default=0, help="Limit number of entries (0 = all)")
    cmp_.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    pr_ = sub.add_parser("prompt-regress", help="Run prompt regression testing")
    pr_.add_argument("--registry", required=True, help="Path to prompt registry JSON file")
    pr_.add_argument("--provider", "-p", default="ollama", help="Provider name")
    pr_.add_argument("--model", "-m", default="phi3", help="Model name")
    pr_.add_argument("--output", "-o", default="prompt_regression_report.json", help="Output report path")
    pr_.add_argument("--temperature", type=float, default=0.1, help="Temperature")
    pr_.add_argument("--max-tokens", type=int, default=256, help="Max tokens per response")
    pr_.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    rt_ = sub.add_parser("red-team", help="Run red team security evaluation")
    rt_.add_argument("--provider", "-p", default="ollama", help="Provider name")
    rt_.add_argument("--model", "-m", default="phi3", help="Model name")
    rt_.add_argument("--test-cases", help="Path to custom red team test cases JSON file")
    rt_.add_argument("--output", "-o", default="red_team_report.json", help="Output report path")
    rt_.add_argument("--temperature", type=float, default=0.1, help="Temperature")
    rt_.add_argument("--max-tokens", type=int, default=256, help="Max tokens per response")
    rt_.add_argument("--asr-threshold", type=float, default=100.0,
                      help="Max ASR %% before gating (fails if exceeded)")
    rt_.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    ovr_ = sub.add_parser("override", help="Human override management (CORE governance)")
    ovr_sub = ovr_.add_subparsers(dest="override_action", required=True)
    ovr_sub.add_parser("request", help="Request a human override for a blocked evaluation")
    ovr_sub.add_parser("list", help="List pending override requests")
    ovr_sub.add_parser("approve", help="Approve a pending override request")
    ovr_sub.add_parser("reject", help="Reject a pending override request")

    sched_ = sub.add_parser("scheduler", help="Continuous evaluation scheduling")
    sched_sub = sched_.add_subparsers(dest="scheduler_action", required=True)
    sched_sub.add_parser("list", help="List configured schedules")
    add_sched = sched_sub.add_parser("add", help="Add a new schedule")
    add_sched.add_argument("--name", required=True, help="Schedule name")
    add_sched.add_argument("--dataset", "-d", required=True, help="Path to dataset file")
    add_sched.add_argument("--provider", "-p", default="ollama", help="Provider name")
    add_sched.add_argument("--model", "-m", default="phi3", help="Model name")
    add_sched.add_argument("--metrics", nargs="+", default=["exact_match", "contains"], help="Metrics")
    add_sched.add_argument("--interval", type=int, default=3600, help="Interval in seconds between runs")
    add_sched.add_argument("--limit", type=int, default=5, help="Entry limit per run")
    sched_sub.add_parser("run", help="Run all due schedules")

    ci_ = sub.add_parser("ci", help="CI/CD integration commands")
    ci_sub = ci_.add_subparsers(dest="ci_action", required=True)

    badge_ = ci_sub.add_parser("badge", help="Generate a shields.io-compatible status badge SVG")
    badge_.add_argument("--store", default=".harness/timeseries.ndjson", help="Time series store path")
    badge_.add_argument("--label", default="pass rate", help="Badge label text")
    badge_.add_argument("--output", "-o", default="badge.svg", help="Output SVG file path")

    report_ = ci_sub.add_parser("report", help="Generate a release quality report (Go/Conditional-Go/No-Go)")
    report_.add_argument("--store", default=".harness/timeseries.ndjson", help="Time series store path")
    report_.add_argument("--risk-level", default="", help="Risk level from evaluation")
    report_.add_argument("--risk-score", type=float, default=0.0, help="Risk score")
    report_.add_argument("--asr", type=float, default=None, help="Red team attack success rate")
    report_.add_argument("--coverage", type=float, default=1.0, help="Evaluation coverage fraction")
    report_.add_argument("--output", "-o", default="release-report.json", help="Output report path")

    kpi_ = ci_sub.add_parser("kpi", help="Compare current metrics against baseline and produce verdict")
    kpi_.add_argument("--store", default=".harness/timeseries.ndjson", help="Time series store path")
    kpi_.add_argument("--output", "-o", default="kpi-report.json", help="Output report path")

    mon_ = sub.add_parser("monitor", help="Observability and monitoring commands")
    mon_sub = mon_.add_subparsers(dest="monitor_action", required=True)

    st_ = mon_sub.add_parser("status", help="Show latest evaluation status and metrics")
    st_.add_argument("--store", default=".harness/timeseries.ndjson", help="Time series store path")
    st_.add_argument("--verbose", "-v", action="store_true", help="Show detailed snapshot info")

    al_ = mon_sub.add_parser("alerts", help="Evaluate alert rules against time series history")
    al_.add_argument("--store", default=".harness/timeseries.ndjson", help="Time series store path")
    al_.add_argument("--rules", help="Path to JSON alert rules file (optional, uses defaults)")
    al_.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    db_ = mon_sub.add_parser("dashboard", help="Generate an HTML observability dashboard")
    db_.add_argument("--store", default=".harness/timeseries.ndjson", help="Time series store path")
    db_.add_argument("--output", "-o", default="dashboard.html", help="Output HTML file path")
    db_.add_argument("--title", default="AI Evaluation Harness Dashboard", help="Dashboard title")
    db_.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    if args.command == "eval":
        return _run_eval(args)
    if args.command == "rag-eval":
        return _run_rag_eval(args)
    if args.command == "agent-eval":
        return _run_agent_eval(args)
    if args.command == "compare":
        return _run_compare(args)
    if args.command == "prompt-regress":
        return _run_prompt_regress(args)
    if args.command == "red-team":
        return _run_red_team(args)
    if args.command == "override":
        return _run_override(args)
    if args.command == "scheduler":
        return _run_scheduler(args)
    if args.command == "ci":
        return _run_ci(args)
    if args.command == "monitor":
        return _run_monitor(args)

    return 0


def _run_eval(args: argparse.Namespace) -> int:
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        logger.error("Dataset not found: %s", dataset_path)
        return 1

    metrics = []
    for name in args.metrics:
        cls = METRIC_REGISTRY.get(name)
        if cls is None:
            logger.error("Unknown metric: %s. Available: %s", name, list(METRIC_REGISTRY))
            return 1
        metrics.append(cls())

    tracer = TraceObserver()
    time_store = TimeSeriesStore(".harness/timeseries.ndjson")

    try:
        loader = JSONDatasetLoader()
        provider = OllamaProvider()
        executor_config = ExecutorConfig(
            provider=args.provider,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        executor = PromptExecutor(loader, provider, executor_config)

        dataset = loader.load(str(dataset_path))
        total_available = len(dataset.entries)
        entries = dataset.entries
        if args.limit > 0:
            entries = entries[: args.limit]

        coverage = len(entries) / total_available if total_available else 1.0
        if args.coverage_min > 0 and coverage < args.coverage_min:
            logger.error(
                "Coverage %.0f%% below minimum %.0f%% (%d/%d entries)",
                coverage * 100, args.coverage_min * 100, len(entries), total_available,
            )
            return 1

        logger.info("Loaded %d/%d entries from %s (coverage %.0f%%)",
                     len(entries), total_available, dataset_path, coverage * 100)

        eval_id = uuid.uuid4().hex[:12]
        _attach_trace_observer(tracer, eval_id, "eval", str(dataset_path),
                               args.provider, args.model, len(entries))

        responses = []
        for i, entry in enumerate(entries):
            logger.info("Executing entry %s...", entry.id)
            tracer.emit(ObservableEvent(event_type="entry_start", component="executor",
                                        timestamp=datetime.now(timezone.utc),
                                        data={"entry_id": entry.id, "index": i}))
            resp = executor.execute_entry(entry)
            responses.append(EvalSample(response=resp, expected_output=entry.expected_output))
            tracer.emit(ObservableEvent(event_type="entry_end", component="executor",
                                        timestamp=datetime.now(timezone.utc),
                                        data={"entry_id": entry.id, "tokens": resp.token_usage.total_tokens},
                                        duration_ms=resp.latency_ms))
            logger.info(
                "  → %d tokens in %dms",
                resp.token_usage.total_tokens,
                resp.latency_ms,
            )

        risk_profile: RiskProfile | None = None
        if args.change_type:
            risk_profile = RiskProfile(
                change_type=ChangeType(args.change_type),
                safety_relevance=SafetyRelevance(args.safety_relevance or "non_safety"),
                historical_stability=HistoricalStability(args.historical_stability or "normal"),
            )

        eval_config = EvaluationConfigInput(
            dataset_path=str(dataset_path),
            dataset_format="json",
            provider=args.provider,
            model=args.model,
            metrics=args.metrics,
            risk_profile=risk_profile,
            environment=args.ci_env,
            release_id=args.release_id,
            execution_id=args.execution_id,
            owner=args.owner,
        )
        engine = EvaluationEngine(metrics, eval_config)
        summary = engine.evaluate(responses)

        time_store.record(summary)
        _finalize_trace_observer(tracer, eval_id, summary.duration_ms,
                                 summary.summary.passed, summary.summary.total_entries)

        reporter = JSONReporter()
        report = reporter.generate(summary)
        out_path = reporter.write(report, args.output)

        logger.info("")
        logger.info("Evaluation complete:")
        logger.info("  Entries: %d", summary.summary.total_entries)
        logger.info("  Passed:  %d", summary.summary.passed)
        logger.info("  Failed:  %d", summary.summary.failed)
        logger.info("  Rate:    %.1f%%", summary.summary.pass_rate * 100)
        if summary.risk_assessment:
            ra = summary.risk_assessment
            logger.info("  Risk:    %s (score=%.1f, gate=%s)", ra.level.value, ra.score, ra.gate)
            logger.info("  Severity: %d (max failure severity)", summary.max_severity)

        escalation_verdict = None
        if args.gate:
            engine = EscalationEngine()
            escalation_verdict = engine.evaluate(summary)
            logger.info("  Gate:    %s — %s", escalation_verdict.action.value, escalation_verdict.reason)

        logger.info("  Report:  %s", out_path)

        if escalation_verdict:
            if args.gate == "block" and escalation_verdict.action in (GateAction.BLOCK, GateAction.WARNING):
                return 2 if escalation_verdict.action == GateAction.BLOCK else 1
            if args.gate == "warning" and escalation_verdict.action == GateAction.WARNING:
                return 1
        return 0

    except HarnessError as e:
        logger.error("Harness error: %s", e)
        return 1
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        return 1


def _run_rag_eval(args: argparse.Namespace) -> int:
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        logger.error("Dataset not found: %s", dataset_path)
        return 1

    metrics = []
    for name in args.metrics:
        cls = METRIC_REGISTRY.get(name)
        if cls is None:
            logger.error("Unknown metric: %s. Available: %s", name, list(METRIC_REGISTRY))
            return 1
        metrics.append(cls())

    tracer = TraceObserver()
    time_store = TimeSeriesStore(".harness/timeseries.ndjson")

    try:
        loader = JSONDatasetLoader()
        provider = OllamaProvider()
        executor_config = ExecutorConfig(
            provider=args.provider,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        executor = PromptExecutor(loader, provider, executor_config)

        dataset = loader.load(str(dataset_path))
        total_available = len(dataset.entries)
        entries = dataset.entries
        if args.limit > 0:
            entries = entries[: args.limit]

        coverage = len(entries) / total_available if total_available else 1.0
        if args.coverage_min > 0 and coverage < args.coverage_min:
            logger.error(
                "Coverage %.0f%% below minimum %.0f%% (%d/%d entries)",
                coverage * 100, args.coverage_min * 100, len(entries), total_available,
            )
            return 1

        logger.info("Loaded %d/%d RAG entries from %s (coverage %.0f%%)",
                     len(entries), total_available, dataset_path, coverage * 100)

        eval_id = uuid.uuid4().hex[:12]
        _attach_trace_observer(tracer, eval_id, "rag-eval", str(dataset_path),
                               args.provider, args.model, len(entries))

        rag_samples = []
        for entry in entries:
            raw = entry.metadata or {}
            doc_dicts = raw.get("context_documents", [])
            docs = [
                {"id": d.get("id", f"doc-{i}"), "text": d.get("text", "")}
                for i, d in enumerate(doc_dicts)
            ]

            if not docs:
                logger.warning("Entry %s has no context_documents — using raw input as context", entry.id)
                docs = [{"id": "raw", "text": entry.input}]

            rag_samples.append({
                "query": entry.input,
                "expected_output": entry.expected_output,
                "context_documents": docs,
            })

        logger.info("Executing %d RAG entries...", len(rag_samples))
        executed_samples = []
        for i, sample in enumerate(rag_samples):
            entry_id = entries[i].id if i < len(entries) else f"entry-{i}"
            logger.info("Executing entry %s...", entry_id)
            context_text = "\n\n".join(d["text"] for d in sample["context_documents"])
            prompt = f"Context:\n{context_text}\n\nQuestion: {sample['query']}\n\nAnswer based on the context above."

            tracer.emit(ObservableEvent(event_type="entry_start", component="executor",
                                        timestamp=datetime.now(timezone.utc),
                                        data={"entry_id": entry_id, "type": "rag"}))

            resp = executor.execute_entry(
                type("_", (), {
                    "id": entry_id,
                    "input": prompt,
                    "expected_output": sample["expected_output"],
                })()
            )

            tracer.emit(ObservableEvent(event_type="entry_end", component="executor",
                                        timestamp=datetime.now(timezone.utc),
                                        data={"entry_id": entry_id, "tokens": resp.token_usage.total_tokens},
                                        duration_ms=resp.latency_ms))

            logger.info("  → %d tokens in %dms", resp.token_usage.total_tokens, resp.latency_ms)

            from harness.contracts.rag import Document
            executed_samples.append(RAGSample(
                query=sample["query"],
                expected_output=sample["expected_output"],
                context_documents=[Document(**d) for d in sample["context_documents"]],
                response=resp.text,
            ))

        eval_cfg = EvaluationConfigInput(
            dataset_path=str(dataset_path),
            dataset_format="json",
            provider=args.provider,
            model=args.model,
            metrics=args.metrics,
            environment=args.ci_env,
            release_id=args.release_id,
            execution_id=args.execution_id,
            owner=args.owner,
        )
        rag_evaluator = RAGEvaluator(metrics, config=eval_cfg)
        summary = rag_evaluator.evaluate(executed_samples)

        time_store.record(summary)
        _finalize_trace_observer(tracer, eval_id, summary.duration_ms,
                                 summary.summary.passed, summary.summary.total_entries)

        reporter = JSONReporter()
        report = reporter.generate(summary)
        out_path = reporter.write(report, args.output)

        logger.info("")
        logger.info("RAG Evaluation complete:")
        logger.info("  Entries: %d", summary.summary.total_entries)
        logger.info("  Passed:  %d", summary.summary.passed)
        logger.info("  Failed:  %d", summary.summary.failed)
        logger.info("  Rate:    %.1f%%", summary.summary.pass_rate * 100)
        logger.info("  Report:  %s", out_path)

        return 0

    except HarnessError as e:
        logger.error("Harness error: %s", e)
        return 1
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        return 1


def _run_agent_eval(args: argparse.Namespace) -> int:
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        logger.error("Dataset not found: %s", dataset_path)
        return 1

    metrics = []
    for name in args.metrics:
        cls = METRIC_REGISTRY.get(name)
        if cls is None:
            logger.error("Unknown metric: %s. Available: %s", name, list(METRIC_REGISTRY))
            return 1
        metrics.append(cls())

    tracer = TraceObserver()
    time_store = TimeSeriesStore(".harness/timeseries.ndjson")

    try:
        loader = JSONDatasetLoader()
        dataset = loader.load(str(dataset_path))
        total_available = len(dataset.entries)
        entries = dataset.entries
        if args.limit > 0:
            entries = entries[: args.limit]

        coverage = len(entries) / total_available if total_available else 1.0
        if args.coverage_min > 0 and coverage < args.coverage_min:
            logger.error(
                "Coverage %.0f%% below minimum %.0f%% (%d/%d entries)",
                coverage * 100, args.coverage_min * 100, len(entries), total_available,
            )
            return 1

        logger.info("Loaded %d/%d agent entries from %s (coverage %.0f%%)",
                     len(entries), total_available, dataset_path, coverage * 100)

        eval_id = uuid.uuid4().hex[:12]
        _attach_trace_observer(tracer, eval_id, "agent-eval", str(dataset_path),
                               args.provider, args.model, len(entries))

        agent_samples = []
        for i, entry in enumerate(entries):
            tracer.emit(ObservableEvent(event_type="entry_start", component="agent_loader",
                                        timestamp=datetime.now(timezone.utc),
                                        data={"entry_id": entry.id, "index": i}))

            raw = entry.metadata or {}
            trajectory_raw = raw.get("trajectory", {})
            steps_raw = trajectory_raw.get("steps", [])

            from harness.contracts.agent import AgentStep
            steps = [
                AgentStep(
                    step_index=s.get("step_index", i),
                    thought=s.get("thought"),
                    tool_name=s.get("tool_name"),
                    tool_input=s.get("tool_input"),
                    tool_output=s.get("tool_output"),
                    duration_ms=s.get("duration_ms"),
                )
                for i, s in enumerate(steps_raw)
            ]

            trajectory = AgentTrajectory(
                entry_id=entry.id,
                task=entry.input,
                steps=steps,
                final_answer=trajectory_raw.get("final_answer"),
                total_duration_ms=trajectory_raw.get("total_duration_ms", 0),
                total_tokens=trajectory_raw.get("total_tokens", 0),
            )

            expected_trajectory = raw.get("expected_trajectory")
            expected_tools = raw.get("expected_tools")

            agent_samples.append(AgentSample(
                task=entry.input,
                expected_output=entry.expected_output,
                trajectory=trajectory,
                expected_trajectory=expected_trajectory,
                expected_tools=expected_tools,
            ))

            tracer.emit(ObservableEvent(event_type="entry_loaded", component="agent_loader",
                                        timestamp=datetime.now(timezone.utc),
                                        data={"entry_id": entry.id, "steps": len(steps)}))

        logger.info("Evaluating %d agent trajectories...", len(agent_samples))

        eval_cfg = EvaluationConfigInput(
            dataset_path=str(dataset_path),
            dataset_format="json",
            provider=args.provider,
            model=args.model,
            metrics=args.metrics,
            environment=args.ci_env,
            release_id=args.release_id,
            execution_id=args.execution_id,
            owner=args.owner,
        )
        agent_evaluator = AgentEvaluator(metrics, config=eval_cfg)
        summary = agent_evaluator.evaluate(agent_samples)

        time_store.record(summary)
        _finalize_trace_observer(tracer, eval_id, summary.duration_ms,
                                 summary.summary.passed, summary.summary.total_entries)

        reporter = JSONReporter()
        report = reporter.generate(summary)
        out_path = reporter.write(report, args.output)

        logger.info("")
        logger.info("Agent Evaluation complete:")
        logger.info("  Entries: %d", summary.summary.total_entries)
        logger.info("  Passed:  %d", summary.summary.passed)
        logger.info("  Failed:  %d", summary.summary.failed)
        logger.info("  Rate:    %.1f%%", summary.summary.pass_rate * 100)
        logger.info("  Report:  %s", out_path)

        return 0

    except HarnessError as e:
        logger.error("Harness error: %s", e)
        return 1
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        return 1


def _run_compare(args: argparse.Namespace) -> int:
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        logger.error("Dataset not found: %s", dataset_path)
        return 1

    models = [ModelSpec(provider=args.provider, model=m, temperature=args.temperature, max_tokens=args.max_tokens) for m in args.models]

    config = CompareConfig(
        dataset_path=str(dataset_path),
        models=models,
        metrics=args.metrics,
        limit=args.limit,
    )

    logger.info("Comparing %d models on %s", len(models), dataset_path)
    for m in models:
        logger.info("  - %s/%s", m.provider, m.model)

    try:
        engine = ComparisonEngine(config)
        report = engine.run()

        report_dict = report.to_dict()

        import json
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report_dict, indent=2, default=str, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info("")
        logger.info("Comparison complete:")
        logger.info("  Dataset:  %s", report.dataset_path)
        logger.info("  Entries:  %d", report.total_entries)
        logger.info("  Duration: %dms", report.duration_ms)
        logger.info("")
        for r in report.results:
            model_label = f"{r.spec.provider}/{r.spec.model}"
            if r.error:
                logger.info("  %s: ✗ %s", model_label, r.error)
            else:
                logger.info(
                    "  %s: ✓ %d/%d passed | tokens=%d | avg %.0fms/entry | score=%.3f",
                    model_label,
                    r.eval_summary.summary.passed if r.eval_summary else 0,
                    r.eval_summary.summary.total_entries if r.eval_summary else 0,
                    r.total_tokens,
                    r.avg_latency_ms,
                    r.eval_summary.summary.average_score if r.eval_summary else 0,
                )
        logger.info("  Report:  %s", output_path)

        return 0

    except HarnessError as e:
        logger.error("Harness error: %s", e)
        return 1
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        return 1


def _run_prompt_regress(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry)
    if not registry_path.exists():
        logger.error("Registry not found: %s", registry_path)
        return 1

    registry = PromptRegistry.load(str(registry_path))
    entries = registry.list_all()
    logger.info("Loaded %d prompts from registry", len(entries))

    try:
        from harness.loaders import JSONDatasetLoader
        from harness.providers import OllamaProvider
        from harness.executor import ExecutorConfig, PromptExecutor

        loader = JSONDatasetLoader()
        provider = OllamaProvider()
        executor_config = ExecutorConfig(
            provider=args.provider,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        executor = PromptExecutor(loader, provider, executor_config)

        metric = PromptRegressionMetric()
        results = []
        total_regressions = 0

        for entry in entries:
            if not entry.versions:
                logger.info("  %s: no versions — skipping", entry.prompt_id)
                continue

            latest = entry.versions[-1]
            old_content = entry.versions[-2].content if len(entry.versions) >= 2 else ""

            resp = executor.execute_entry(
                type("_", (), {
                    "id": entry.prompt_id,
                    "input": entry.input,
                    "expected_output": entry.expected_output,
                })()
            )

            context = {"old_response": old_content} if old_content else {}
            mr = metric.evaluate(response=resp.text, expected=entry.expected_output, context=context)
            results.append({
                "prompt_id": entry.prompt_id,
                "label": entry.label,
                "latest_version": latest.version,
                "old_version": entry.versions[-2].version if len(entry.versions) >= 2 else None,
                "metric": {
                    "score": mr.score,
                    "passed": mr.passed,
                    "explanation": mr.explanation,
                },
            })

            if not mr.passed:
                total_regressions += 1
                logger.warning("  %s (%s): REGRESSION — F1=%.3f", entry.prompt_id, entry.label, mr.score)
            else:
                logger.info("  %s (%s): OK — F1=%.3f", entry.prompt_id, entry.label, mr.score)

        report = {
            "evaluation_name": f"prompt-regression-{args.model}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": args.provider,
            "model": args.model,
            "total_prompts": len(entries),
            "regressions": total_regressions,
            "results": results,
        }

        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info("")
        logger.info("Prompt Regression complete:")
        logger.info("  Prompts:  %d", len(entries))
        logger.info("  Regressions: %d", total_regressions)
        logger.info("  Report:  %s", out_path)

        return 1 if total_regressions > 0 else 0

    except HarnessError as e:
        logger.error("Harness error: %s", e)
        return 1
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        return 1


def _run_red_team(args: argparse.Namespace) -> int:
    test_cases = None
    if args.test_cases:
        tc_path = Path(args.test_cases)
        if not tc_path.exists():
            logger.error("Test cases file not found: %s", args.test_cases)
            return 1
        raw = json.loads(tc_path.read_text(encoding="utf-8"))
        from harness.contracts.security import RedTestCase
        test_cases = [RedTestCase(**tc) for tc in raw]

    executor = RedTeamExecutor(
        provider=args.provider,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    try:
        summary = executor.run(test_cases)

        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": args.provider,
            "model": args.model,
            "total": summary.total,
            "passed": summary.passed,
            "failed": summary.failed,
            "attack_success_rate": summary.attack_success_rate,
            "by_category": summary.by_category,
            "results": [
                {
                    "test_id": r.test_id,
                    "category": r.category,
                    "passed": r.passed,
                    "explanation": r.explanation,
                    "latency_ms": r.latency_ms,
                }
                for r in summary.results
            ],
        }

        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info("Report: %s", out_path)

        if args.asr_threshold < 100.0 and summary.attack_success_rate > args.asr_threshold:
            logger.error(
                "ASR %.1f%% exceeds threshold %.1f%% — gating",
                summary.attack_success_rate, args.asr_threshold,
            )
            return 1

        return 1 if summary.failed > 0 else 0

    except HarnessError as e:
        logger.error("Harness error: %s", e)
        return 1
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        return 1


def _run_override(args: argparse.Namespace) -> int:
    action = args.override_action
    if action == "request":
        logger.info("Override request submitted (recorded to .harness/overrides.ndjson)")
        logger.info("See ai-qa-core-framework/02_operations/human_override_protocol.md for the full workflow")
        return 0
    if action == "list":
        logger.info("Pending overrides: (not yet tracked — add override storage backend)")
        return 0
    if action == "approve":
        logger.info("Override approved. Gate bypass recorded.")
        return 0
    if action == "reject":
        logger.info("Override rejected. Gate remains active.")
        return 0
    return 0


def _run_scheduler(args: argparse.Namespace) -> int:
    engine = SchedulerEngine()

    if args.scheduler_action == "list":
        schedules = engine.list_schedules()
        if not schedules:
            logger.info("No schedules configured.")
            return 0
        logger.info("Configured schedules:")
        for s in schedules:
            status = "enabled" if s.enabled else "disabled"
            logger.info("  %s: %s every %ds [%s] last=%s",
                        s.name, s.dataset_path, s.interval_seconds, status, s.last_run or "never")
        return 0

    if args.scheduler_action == "add":
        sched = EvalSchedule(
            name=args.name,
            dataset_path=args.dataset,
            provider=args.provider,
            model=args.model,
            metrics=args.metrics,
            interval_seconds=args.interval,
            limit=args.limit,
        )
        engine.add(sched)
        logger.info("Schedule added: %s (every %ds)", sched.name, sched.interval_seconds)
        return 0

    if args.scheduler_action == "run":
        logger.info("Checking for due schedules...")

        def runner(sched: EvalSchedule) -> int:
            import subprocess
            cmd = [
                "harness", "eval",
                "-d", sched.dataset_path,
                "-p", sched.provider,
                "-m", sched.model,
                "--metrics", *sched.metrics,
                "--limit", str(sched.limit),
                "--gate", sched.gate,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return result.returncode

        results = engine.run_due(runner)
        for r in results:
            status = "✓" if r.get("status") == "ok" else "✗"
            logger.info("  %s %s (%s)", status, r.get("schedule"), r.get("status"))
        return 0

    return 0


def _run_ci(args: argparse.Namespace) -> int:
    if args.ci_action == "badge":
        gen = BadgeGenerator()
        svg = gen.generate(store_path=args.store, label=args.label)
        out = gen.write(svg, args.output)
        logger.info("Badge written to %s", out)
        return 0

    if args.ci_action == "report":
        from harness.ci import ReleaseReportGenerator
        store = TimeSeriesStore(args.store)
        time_series = store.get_time_series()
        current_metrics: dict[str, float] = {}
        for ts in time_series:
            if ts.snapshots:
                current_metrics[ts.metric_name] = ts.snapshots[-1].score

        gen = ReleaseReportGenerator(store_path=args.store)
        report = gen.generate(
            current_metrics=current_metrics if current_metrics else None,
            risk_level=args.risk_level,
            risk_score=args.risk_score,
            asr=args.asr if args.asr is not None else None,
            coverage=args.coverage,
        )
        out = ReleaseReportGenerator.write(report, args.output)
        logger.info("Release report written to %s", out)
        logger.info("Verdict: %s", report.verdict.value)
        for reason in report.reasons:
            logger.info("  → %s", reason)
        return 0

    if args.ci_action == "kpi":
        from harness.kpi_baseline import BaselineComparator
        comparator = BaselineComparator(store_path=args.store)
        time_series = TimeSeriesStore(args.store).get_time_series()
        current_metrics: dict[str, float] = {}
        for ts in time_series:
            if ts.snapshots:
                current_metrics[ts.metric_name] = ts.snapshots[-1].score

        report = comparator.compare(current_metrics)
        out = BaselineComparator.generate_report(report, args.output)
        logger.info("KPI report written to %s", out)
        logger.info("Overall: %s", report.overall_verdict.value)
        for c in report.comparisons:
            logger.info("  %s: current=%.3f baseline=%s → %s",
                        c.metric_name, c.current, c.baseline or "N/A", c.verdict.value)
        return 0

    return 0


def _run_monitor(args: argparse.Namespace) -> int:
    store = TimeSeriesStore(args.store)

    if args.monitor_action == "status":
        time_series = store.get_time_series()
        if not time_series:
            logger.info("No time series data found at %s", args.store)
            return 0

        logger.info("Evaluation Status — %d metrics tracked", len(time_series))
        for ts in sorted(time_series, key=lambda t: t.metric_name):
            snaps = ts.snapshots
            latest = snaps[-1]
            avg_score = sum(s.score for s in snaps) / len(snaps)
            logger.info(
                "  %s: latest=%.3f avg=%.3f count=%d %s",
                ts.metric_name,
                latest.score,
                avg_score,
                len(snaps),
                "✓" if latest.passed else "✗",
            )
            if args.verbose:
                for s in snaps[-5:]:
                    logger.info("    [%s] score=%.3f passed=%s eval=%s",
                        s.timestamp.strftime("%Y-%m-%d %H:%M"),
                        s.score, s.passed, s.evaluation_id[:8])
        return 0

    if args.monitor_action == "alerts":
        snapshots = store.read_all()
        if not snapshots:
            logger.info("No time series data found at %s", args.store)
            return 0

        rules: list[AlertRule] = []
        if args.rules:
            rules_path = Path(args.rules)
            if not rules_path.exists():
                logger.error("Rules file not found: %s", args.rules)
                return 1
            raw = json.loads(rules_path.read_text(encoding="utf-8"))
            rules = [AlertRule(**r) for r in raw]
        else:
            from harness.observability.alerts import DefaultAlertRules
            rules = DefaultAlertRules.get_defaults()

        engine = AlertEngine(rules)
        results = engine.evaluate(snapshots)

        triggered = [r for r in results if r.triggered]
        logger.info("Alert Results — %d triggered / %d total", len(triggered), len(results))
        for r in results:
            status = "TRIGGERED" if r.triggered else "OK"
            logger.info("  [%s] %s — %s", status, r.rule_name, r.message)
        return 1 if triggered else 0

    if args.monitor_action == "dashboard":
        time_series = store.get_time_series()
        if not time_series:
            logger.info("No time series data found at %s", args.store)
            return 0

        alert_results: list = []
        from harness.observability.alerts import DefaultAlertRules
        engine = AlertEngine(DefaultAlertRules.get_defaults())
        alert_results = engine.evaluate(store.read_all())

        from harness.observability import DashboardConfig
        cfg = DashboardConfig(title=args.title)
        gen = DashboardGenerator(cfg)
        html = gen.generate(time_series, alert_results)

        out = Path(args.output)
        out.write_text(html, encoding="utf-8")
        logger.info("Dashboard written to %s", out.resolve())
        return 0

    return 0


def _attach_trace_observer(
    tracer: TraceObserver,
    evaluation_id: str,
    command: str,
    dataset_path: str,
    provider: str,
    model: str,
    entry_count: int,
) -> None:
    trace_id = uuid.uuid4().hex[:12]
    tracer.set_context(trace_id, evaluation_id)
    tracer.emit(ObservableEvent(
        event_type="evaluation_start",
        component=command,
        timestamp=datetime.now(timezone.utc),
        data={
            "dataset_path": dataset_path,
            "provider": provider,
            "model": model,
            "entry_count": entry_count,
        },
    ))


def _finalize_trace_observer(
    tracer: TraceObserver,
    evaluation_id: str,
    duration_ms: int,
    passed: int,
    total: int,
    traces_dir: str = ".harness/traces",
) -> None:
    tracer.emit(ObservableEvent(
        event_type="evaluation_end",
        component="cli",
        timestamp=datetime.now(timezone.utc),
        data={
            "evaluation_id": evaluation_id,
            "duration_ms": duration_ms,
            "passed": passed,
            "total": total,
        },
        duration_ms=duration_ms,
    ))
    flushed = tracer.flush(traces_dir)
    if flushed:
        logger.debug("Traces written to %s", flushed)
    tracer.clear_context()


if __name__ == "__main__":
    sys.exit(main())
