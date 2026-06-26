from __future__ import annotations

from typing import Any

from harness.contracts.evaluation import MetricResult
from harness.interfaces.metric import Metric


class Contains(Metric):
    def __init__(self, threshold: float = 0.5, case_sensitive: bool = False):
        super().__init__(threshold)
        self._case_sensitive = case_sensitive

    @property
    def name(self) -> str:
        return "contains"

    def evaluate(
        self,
        response: str,
        expected: str,
        context: dict[str, Any] | None = None,
    ) -> MetricResult:
        if self._case_sensitive:
            found = expected in response
        else:
            found = expected.lower() in response.lower()

        score = 1.0 if found else 0.0
        passed = score >= self.threshold
        return MetricResult(
            metric_name=self.name,
            score=score,
            passed=passed,
            explanation=(
                "Expected text found in response" if found else "Expected text not found in response"
            ),
            threshold=self.threshold,
            diagnosis={"case_sensitive": self._case_sensitive},
        )
