from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from harness.comparison import CompareConfig, ComparisonEngine, ModelSpec
from harness.errors import HarnessError
from harness.evaluator import EvalSample, EvaluationConfigInput, EvaluationEngine
from harness.evaluator_rag import RAGEvaluator, RAGSample
from harness.executor import ExecutorConfig, PromptExecutor
from harness.loaders import JSONDatasetLoader
from harness.metrics import Contains, ExactMatch
from harness.metrics.rag import Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall
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
}


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
    rag_.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

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
    if args.command == "compare":
        return _run_compare(args)

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
        entries = dataset.entries
        if args.limit > 0:
            entries = entries[: args.limit]

        logger.info("Loaded %d entries from %s", len(entries), dataset_path)

        responses = []
        for entry in entries:
            logger.info("Executing entry %s...", entry.id)
            resp = executor.execute_entry(entry)
            responses.append(EvalSample(response=resp, expected_output=entry.expected_output))
            logger.info(
                "  → %d tokens in %dms",
                resp.token_usage.total_tokens,
                resp.latency_ms,
            )

        eval_config = EvaluationConfigInput(
            dataset_path=str(dataset_path),
            dataset_format="json",
            provider=args.provider,
            model=args.model,
            metrics=args.metrics,
        )
        engine = EvaluationEngine(metrics, eval_config)
        summary = engine.evaluate(responses)

        reporter = JSONReporter()
        report = reporter.generate(summary)
        out_path = reporter.write(report, args.output)

        logger.info("")
        logger.info("Evaluation complete:")
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
        entries = dataset.entries
        if args.limit > 0:
            entries = entries[: args.limit]

        logger.info("Loaded %d RAG entries from %s", len(entries), dataset_path)

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

            resp = executor.execute_entry(
                type("_", (), {
                    "id": entry_id,
                    "input": prompt,
                    "expected_output": sample["expected_output"],
                })()
            )

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
        )
        rag_evaluator = RAGEvaluator(metrics, config=eval_cfg)
        summary = rag_evaluator.evaluate(executed_samples)

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


if __name__ == "__main__":
    sys.exit(main())
