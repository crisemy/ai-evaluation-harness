from __future__ import annotations

from typing import Any

from harness.contracts.evaluation import MetricResult
from harness.interfaces.metric import Metric


class ToolSelection(Metric):
    @property
    def name(self) -> str:
        return "tool_selection"

    def evaluate(
        self,
        response: str,
        expected: str,
        context: dict[str, Any] | None = None,
    ) -> MetricResult:
        ctx = context or {}
        steps = ctx.get("trajectory_steps", [])
        expected_tools = ctx.get("expected_tools", [])

        used_tools = list({s.get("tool_name") for s in steps if s.get("tool_name")})

        if not expected_tools:
            return MetricResult(
                metric_name=self.name,
                score=1.0 if used_tools else 0.0,
                passed=True,
                explanation="No expected tools specified — recording used tools only",
                threshold=self.threshold,
                diagnosis={"used_tools": used_tools},
            )

        expected_set = set(expected_tools)
        used_set = set(used_tools)

        if not used_set:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                passed=False,
                explanation="No tools were used",
                threshold=self.threshold,
            )

        correct = used_set & expected_set
        extra = used_set - expected_set
        missing = expected_set - used_set

        if not expected_set:
            score = 1.0
        else:
            precision = len(correct) / len(used_set) if used_set else 0.0
            recall = len(correct) / len(expected_set) if expected_set else 0.0
            score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        passed = score >= self.threshold

        parts = []
        if correct:
            parts.append(f"correct: {sorted(correct)}")
        if extra:
            parts.append(f"unexpected: {sorted(extra)}")
        if missing:
            parts.append(f"missing: {sorted(missing)}")
        explanation = "; ".join(parts) if parts else ("All tools correct" if passed else "No correct tools used")

        return MetricResult(
            metric_name=self.name,
            score=score,
            passed=passed,
            explanation=explanation,
            threshold=self.threshold,
            diagnosis={"used_tools": used_tools, "expected_tools": expected_tools},
        )
