from __future__ import annotations

from typing import Any

from harness.contracts.evaluation import MetricResult
from harness.errors import MetricError
from harness.interfaces.metric import Metric

try:
    from deepeval.metrics import AnswerRelevancyMetric as _AnswerRelevancyMetric

    HAS_DEEPEVAL = True
except ImportError:
    HAS_DEEPEVAL = False


class AnswerRelevancy(Metric):
    def __init__(self, threshold: float = 0.5):
        super().__init__(threshold)
        self._wrapped: Any = None

    @property
    def name(self) -> str:
        return "answer_relevancy"

    def evaluate(
        self,
        response: str,
        expected: str,
        context: dict[str, Any] | None = None,
    ) -> MetricResult:
        if not HAS_DEEPEVAL:
            raise MetricError("deepeval is not installed. Run: pip install deepeval")

        if self._wrapped is None:
            try:
                self._wrapped = _AnswerRelevancyMetric(threshold=self.threshold)
            except Exception as e:
                return MetricResult(
                    metric_name=self.name,
                    score=0.0,
                    passed=False,
                    explanation=f"Failed to initialize DeepEval metric: {e}",
                    threshold=self.threshold,
                )

        ctx = context or {}
        query = ctx.get("query", expected)

        try:
            result = self._wrapped.measure(query, response)
            score = result.score if hasattr(result, "score") else getattr(self._wrapped, "score", 0.0)
            reason = result.reason if hasattr(result, "reason") else getattr(self._wrapped, "reason", "")
            return MetricResult(
                metric_name=self.name,
                score=score,
                passed=score >= self.threshold,
                explanation=reason or f"Answer relevancy score: {score:.3f}",
                threshold=self.threshold,
            )
        except Exception as e:
            raise MetricError(f"AnswerRelevancy evaluation failed: {e}") from e
