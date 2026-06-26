from __future__ import annotations

from typing import Any

from harness.contracts.evaluation import MetricResult
from harness.interfaces.metric import Metric


class StepCorrectness(Metric):
    @property
    def name(self) -> str:
        return "step_correctness"

    def evaluate(
        self,
        response: str,
        expected: str,
        context: dict[str, Any] | None = None,
    ) -> MetricResult:
        ctx = context or {}
        steps = ctx.get("trajectory_steps", [])
        expected_steps = ctx.get("expected_trajectory", [])

        if not steps:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                passed=False,
                explanation="No trajectory steps recorded",
                threshold=self.threshold,
            )

        if not expected_steps:
            return MetricResult(
                metric_name=self.name,
                score=1.0,
                passed=True,
                explanation="No expected trajectory provided — skipping step correctness",
                threshold=self.threshold,
            )

        matches = 0
        details = []
        for i, (actual, exp) in enumerate(zip(steps, expected_steps)):
            step_ok = True
            exp_tool = exp.get("tool_name")
            if exp_tool and actual.get("tool_name") != exp_tool:
                step_ok = False
            exp_thought = exp.get("thought")
            if exp_thought and actual.get("thought") != exp_thought:
                step_ok = False

            if step_ok:
                matches += 1
                details.append(f"Step {i}: correct")
            else:
                exp_label = exp_tool or exp_thought or "unknown"
                act_label = actual.get("tool_name") or actual.get("thought") or "unknown"
                details.append(f"Step {i}: expected '{exp_label}', got '{act_label}'")

        score = matches / len(expected_steps) if expected_steps else 1.0
        passed = score >= self.threshold
        explanation = "; ".join(details) if details else "All steps correct"

        return MetricResult(
            metric_name=self.name,
            score=score,
            passed=passed,
            explanation=explanation,
            threshold=self.threshold,
        )
