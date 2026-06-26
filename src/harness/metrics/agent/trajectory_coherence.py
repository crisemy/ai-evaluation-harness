from __future__ import annotations

from typing import Any

from harness.contracts.evaluation import MetricResult
from harness.interfaces.metric import Metric


class TrajectoryCoherence(Metric):
    @property
    def name(self) -> str:
        return "trajectory_coherence"

    def evaluate(
        self,
        response: str,
        expected: str,
        context: dict[str, Any] | None = None,
    ) -> MetricResult:
        ctx = context or {}
        steps = ctx.get("trajectory_steps", [])

        if not steps:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                passed=False,
                explanation="No trajectory steps to evaluate coherence",
                threshold=self.threshold,
            )

        issues = []
        total_steps = len(steps)

        thought_count = sum(1 for s in steps if s.get("thought"))
        tool_count = sum(1 for s in steps if s.get("tool_name"))

        if total_steps > 1:
            for i in range(1, total_steps):
                prev = steps[i - 1]
                curr = steps[i]
                if prev.get("tool_name") and not prev.get("tool_output") and curr.get("thought"):
                    issues.append(f"Step {i}: tool had no output before next thought")

        has_final_answer = bool(response and response.strip())

        # score components:
        # - 40%: has steps with thoughts
        # - 30%: no ordering issues detected
        # - 30%: has final answer
        thought_score = min(thought_count / max(total_steps, 1), 1.0) * 0.4
        ordering_score = (1.0 - min(len(issues) * 0.2, 1.0)) * 0.3
        answer_score = (1.0 if has_final_answer else 0.0) * 0.3

        score = thought_score + ordering_score + answer_score
        passed = score >= self.threshold

        parts = [f"{total_steps} steps ({thought_count} thoughts, {tool_count} tool calls)"]
        if issues:
            parts.extend(issues[:3])
        if not has_final_answer:
            parts.append("no final answer produced")
        explanation = "; ".join(parts)

        return MetricResult(
            metric_name=self.name,
            score=round(score, 4),
            passed=passed,
            explanation=explanation,
            threshold=self.threshold,
            diagnosis={
                "step_count": total_steps,
                "thought_count": thought_count,
                "tool_count": tool_count,
                "issues": issues,
            },
        )
