from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from harness.contracts.evaluation import EvaluationResult, MetricResult
from harness.contracts.rag import Document, RAGEvaluationInput
from harness.contracts.report import EvaluationSummary
from harness.errors import HarnessError, MetricError
from harness.evaluator import EvaluationConfigInput
from harness.interfaces.context_provider import ContextProvider
from harness.interfaces.metric import Metric

logger = logging.getLogger(__name__)


@dataclass
class RAGSample:
    query: str
    expected_output: str
    context_documents: list[Document]
    response: str | None = None


class RAGEvaluator:
    def __init__(
        self,
        metrics: list[Metric],
        context_provider: ContextProvider | None = None,
        config: EvaluationConfigInput | None = None,
    ):
        if not metrics:
            raise HarnessError("At least one RAG metric is required")
        self._metrics = metrics
        self._context_provider = context_provider
        self._config = config or EvaluationConfigInput()

    @property
    def metric_names(self) -> list[str]:
        return [m.name for m in self._metrics]

    def evaluate(self, samples: list[RAGSample]) -> EvaluationSummary:
        if not samples:
            raise HarnessError("No RAG samples to evaluate")

        evaluation_id = uuid.uuid4().hex[:12]
        start = time.monotonic()

        results: list[EvaluationResult] = []
        for sample in samples:
            result = self._evaluate_sample(sample)
            results.append(result)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        now = datetime.now(timezone.utc)

        total = len(results)
        passed = sum(1 for r in results if r.overall_passed)
        avg_score = sum(r.overall_score for r in results) / total if total else 0.0

        from harness.contracts.report import EnvironmentInfo, EvaluationConfig as EvalCfg, MetricSummary, SummaryStats

        eval_cfg = EvalCfg(
            dataset_path=self._config.dataset_path,
            dataset_format=self._config.dataset_format,
            provider=self._config.provider,
            model=self._config.model,
            metrics=self.metric_names,
        )

        metric_summaries: dict[str, Any] = {}
        if results:
            header_metrics = results[0].metrics
            for hm in header_metrics:
                scores = [r.overall_score for r in results]
                passes = sum(1 for r in results if r.overall_passed)
                metric_summaries[hm.metric_name] = MetricSummary(
                    mean=sum(scores) / len(scores) if scores else 0.0,
                    min=min(scores) if scores else 0.0,
                    max=max(scores) if scores else 0.0,
                    pass_rate=passes / len(results) if results else 0.0,
                )

        env = EnvironmentInfo(
            harness_version="0.1.0",
            python_version="3.12",
            platform="win32",
        )

        summary_stats = SummaryStats(
            total_entries=total,
            passed=passed,
            failed=total - passed,
            skipped=0,
            pass_rate=passed / total if total else 0.0,
            average_score=avg_score,
            metrics=metric_summaries,
        )

        return EvaluationSummary(
            evaluation_name=f"rag-{self._config.provider}-{self._config.model}",
            evaluation_id=evaluation_id,
            timestamp=now,
            duration_ms=elapsed_ms,
            config=eval_cfg,
            environment=env,
            summary=summary_stats,
            results=results,
        )

    def _evaluate_sample(self, sample: RAGSample) -> EvaluationResult:
        entry_start = time.monotonic()
        metric_results: list[MetricResult] = []

        if not sample.response:
            return EvaluationResult(
                entry_id="unknown",
                metrics=[],
                overall_score=0.0,
                overall_passed=False,
                duration_ms=0,
                timestamp=datetime.now(timezone.utc),
            )

        context = {
            "query": sample.query,
            "context_documents": [d.text for d in sample.context_documents],
            "entry_id": sample.query[:40],
        }

        for metric in self._metrics:
            try:
                mr = metric.evaluate(
                    response=sample.response,
                    expected=sample.expected_output,
                    context=context,
                )
            except MetricError as e:
                mr = MetricResult(
                    metric_name=metric.name,
                    score=0.0,
                    passed=False,
                    explanation=str(e),
                    threshold=metric.threshold,
                )
            metric_results.append(mr)

        elapsed_ms = int((time.monotonic() - entry_start) * 1000)
        scores = [m.score for m in metric_results]
        overall_score = sum(scores) / len(scores) if scores else 0.0
        overall_passed = all(m.passed for m in metric_results)

        return EvaluationResult(
            entry_id=context["entry_id"],
            metrics=metric_results,
            overall_score=overall_score,
            overall_passed=overall_passed,
            duration_ms=elapsed_ms,
            timestamp=datetime.now(timezone.utc),
        )
