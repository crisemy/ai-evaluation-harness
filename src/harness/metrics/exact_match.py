from __future__ import annotations

from typing import Any

from harness.contracts.evaluation import MetricResult
from harness.interfaces.metric import Metric


class ExactMatch(Metric):
    @property
    def name(self) -> str:
        return "exact_match"

    def evaluate(
        self,
        response: str,
        expected: str,
        context: dict[str, Any] | None = None,
    ) -> MetricResult:
        score = 1.0 if response.strip() == expected.strip() else 0.0
        passed = score >= self.threshold
        return MetricResult(
            metric_name=self.name,
            score=score,
            passed=passed,
            explanation=(
                "Output exactly matches expected"
                if passed
                else f"Expected '{expected[:80]}', got '{response[:80]}'"
            ),
            threshold=self.threshold,
        )
