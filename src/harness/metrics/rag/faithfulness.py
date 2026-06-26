from __future__ import annotations

from typing import Any

from harness.contracts.evaluation import MetricResult
from harness.errors import MetricError
from harness.interfaces.metric import Metric

try:
    from deepeval.metrics import FaithfulnessMetric as _FaithfulnessMetric
    from deepeval.models import DeepEvalBaseLLM

    HAS_DEEPEVAL = True
except ImportError:
    HAS_DEEPEVAL = False


class Faithfulness(Metric):
    def __init__(self, threshold: float = 0.5, model: Any = None):
        super().__init__(threshold)
        self._model = model
        self._wrapped: Any = None

    @property
    def name(self) -> str:
        return "faithfulness"

    def evaluate(
        self,
        response: str,
        expected: str,
        context: dict[str, Any] | None = None,
    ) -> MetricResult:
        if not HAS_DEEPEVAL:
            raise MetricError("deepeval is not installed. Run: pip install deepeval")

        ctx = context or {}
        context_docs = ctx.get("context_documents", [])

        if not context_docs:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                passed=False,
                explanation="No context documents provided for faithfulness evaluation",
                threshold=self.threshold,
            )

        if self._wrapped is None:
            try:
                kwargs = {"threshold": self.threshold}
                if self._model is not None:
                    kwargs["model"] = self._model
                self._wrapped = _FaithfulnessMetric(**kwargs)
            except Exception as e:
                return MetricResult(
                    metric_name=self.name,
                    score=0.0,
                    passed=False,
                    explanation=f"Failed to initialize DeepEval metric: {e}",
                    threshold=self.threshold,
                )

        try:
            result = self._wrapped.measure(response, context_docs)
            score = result.score if hasattr(result, "score") else getattr(self._wrapped, "score", 0.0)
            reason = result.reason if hasattr(result, "reason") else getattr(self._wrapped, "reason", "")
            return MetricResult(
                metric_name=self.name,
                score=score,
                passed=score >= self.threshold,
                explanation=reason or f"Faithfulness score: {score:.3f}",
                threshold=self.threshold,
                diagnosis={"raw_result": str(result)},
            )
        except Exception as e:
            raise MetricError(f"Faithfulness evaluation failed: {e}") from e
