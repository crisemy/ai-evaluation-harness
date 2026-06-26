from __future__ import annotations

from typing import Any

from harness.contracts.evaluation import MetricResult
from harness.interfaces.metric import Metric


class GoalAchievement(Metric):
    @property
    def name(self) -> str:
        return "goal_achievement"

    def evaluate(
        self,
        response: str,
        expected: str,
        context: dict[str, Any] | None = None,
    ) -> MetricResult:
        if not response:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                passed=False,
                explanation="Agent produced no final answer",
                threshold=self.threshold,
            )

        if not expected:
            return MetricResult(
                metric_name=self.name,
                score=1.0,
                passed=True,
                explanation="No expected output provided — skipping goal achievement",
                threshold=self.threshold,
            )

        score = 1.0 if response.strip() == expected.strip() else 0.0
        passed = score >= self.threshold

        return MetricResult(
            metric_name=self.name,
            score=score,
            passed=passed,
            explanation=(
                "Agent achieved the expected goal"
                if passed
                else f"Expected '{expected[:120]}', got '{response[:120]}'"
            ),
            threshold=self.threshold,
        )
