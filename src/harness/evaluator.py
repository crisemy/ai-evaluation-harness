from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
import sys as _sys
from typing import Any

from harness.contracts.evaluation import EvaluationResult, MetricResult
from harness.contracts.report import EvaluationSummary
from harness.contracts.execution import ExecutionResponse
from harness.contracts.report import (
    EnvironmentInfo,
    EvaluationConfig,
    MetricSummary,
    SummaryStats,
)
from harness.contracts.risk import (
    ChangeType,
    HistoricalStability,
    RiskAssessment,
    RiskProfile,
    SafetyRelevance,
)
from harness.errors import HarnessError
from harness.interfaces.metric import Metric
from harness.risk import RiskClassifier

logger = logging.getLogger(__name__)


@dataclass
class EvalSample:
    response: ExecutionResponse
    expected_output: str


@dataclass
class EvaluationConfigInput:
    dataset_path: str = ""
    dataset_format: str = "json"
    provider: str = "ollama"
    model: str = "phi3"
    metrics: list[str] = field(default_factory=lambda: ["exact_match", "contains"])
    risk_profile: RiskProfile | None = None


class EvaluationEngine:
    def __init__(self, metrics: list[Metric], config: EvaluationConfigInput | None = None):
        if not metrics:
            raise HarnessError("At least one metric is required")
        self._metrics = metrics
        self._config = config or EvaluationConfigInput()
        self._risk_classifier = RiskClassifier()

    @property
    def metric_names(self) -> list[str]:
        return [m.name for m in self._metrics]

    def evaluate(self, samples: list[EvalSample]) -> EvaluationSummary:
        if not samples:
            raise HarnessError("No execution responses to evaluate")

        evaluation_id = uuid.uuid4().hex[:12]
        start = time.monotonic()

        risk_assessment: RiskAssessment | None = None
        if self._config.risk_profile:
            risk_assessment = self._risk_classifier.classify(self._config.risk_profile)
            logger.info("Risk assessment: %s", risk_assessment.rationale)

        results: list[EvaluationResult] = []
        for sample in samples:
            result = self._evaluate_entry(sample, risk_assessment)
            results.append(result)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        now = datetime.now(timezone.utc)

        header = results[0]
        metric_names = [m.metric_name for m in header.metrics]

        metric_summaries: dict[str, MetricSummary] = {}
        for name in metric_names:
            scores = [r.overall_score for r in results]
            passes = sum(1 for r in results if r.overall_passed)
            metric_summaries[name] = MetricSummary(
                mean=sum(scores) / len(scores) if scores else 0.0,
                min=min(scores) if scores else 0.0,
                max=max(scores) if scores else 0.0,
                pass_rate=passes / len(results) if results else 0.0,
            )

        total = len(results)
        passed = sum(1 for r in results if r.overall_passed)
        max_severity = max((r.max_severity for r in results), default=1)
        avg_score = (
            sum(r.overall_score for r in results) / total if total else 0.0
        )

        eval_config = EvaluationConfig(
            dataset_path=self._config.dataset_path,
            dataset_format=self._config.dataset_format,
            provider=self._config.provider,
            model=self._config.model,
            metrics=self.metric_names,
        )

        env = EnvironmentInfo(
            harness_version="0.1.0",
            python_version=f"{_sys.version_info.major}.{_sys.version_info.minor}.{_sys.version_info.micro}",
            platform=_sys.platform,
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
            evaluation_name=f"{self._config.provider}-{self._config.model}-eval",
            evaluation_id=evaluation_id,
            timestamp=now,
            duration_ms=elapsed_ms,
            config=eval_config,
            environment=env,
            summary=summary_stats,
            results=results,
            risk_assessment=risk_assessment,
            max_severity=max_severity,
        )

    def _evaluate_entry(self, sample: EvalSample, risk_assessment: RiskAssessment | None = None) -> EvaluationResult:
        entry_start = time.monotonic()
        metric_results: list[MetricResult] = []

        for metric in self._metrics:
            context = {"entry_id": sample.response.entry_id, "model": sample.response.model}
            if sample.response.raw_response:
                context["raw_response"] = sample.response.raw_response

            try:
                mr = metric.evaluate(
                    response=sample.response.text,
                    expected=sample.expected_output,
                    context=context,
                )
            except Exception as e:
                mr = MetricResult(
                    metric_name=metric.name,
                    score=0.0,
                    passed=False,
                    explanation=f"Metric error: {e}",
                    threshold=metric.threshold,
                )
            metric_results.append(mr)

        elapsed_ms = int((time.monotonic() - entry_start) * 1000)
        scores = [m.score for m in metric_results]
        overall_score = sum(scores) / len(scores) if scores else 0.0
        overall_passed = all(m.passed for m in metric_results)
        max_severity = max((m.severity for m in metric_results), default=1)

        return EvaluationResult(
            entry_id=sample.response.entry_id,
            metrics=metric_results,
            overall_score=overall_score,
            overall_passed=overall_passed,
            duration_ms=elapsed_ms,
            timestamp=datetime.now(timezone.utc),
            risk_assessment=risk_assessment,
            max_severity=max_severity,
        )
