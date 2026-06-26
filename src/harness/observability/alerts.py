from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from harness.observability.models import AlertResult, AlertRule, MetricSnapshot


class AlertEngine:
    def __init__(self, rules: list[AlertRule] | None = None):
        self._rules: list[AlertRule] = rules or []

    @property
    def rules(self) -> list[AlertRule]:
        return list(self._rules)

    def add_rule(self, rule: AlertRule) -> None:
        self._rules.append(rule)

    def remove_rule(self, name: str) -> bool:
        for i, r in enumerate(self._rules):
            if r.name == name:
                self._rules.pop(i)
                return True
        return False

    def evaluate(
        self,
        snapshots: list[MetricSnapshot],
        rules: list[AlertRule] | None = None,
    ) -> list[AlertResult]:
        active_rules = rules if rules is not None else self._rules
        results: list[AlertResult] = []
        now = datetime.now(timezone.utc)

        for rule in active_rules:
            matching = [s for s in snapshots if s.metric_name == rule.metric_name]
            if not matching:
                continue

            latest = max(matching, key=lambda s: s.timestamp)
            triggered = self._check_rule(rule, latest.score)

            results.append(AlertResult(
                rule_name=rule.name,
                metric_name=rule.metric_name,
                triggered=triggered,
                current_value=latest.score,
                threshold=rule.threshold,
                operator=rule.operator,
                timestamp=now,
                evaluation_id=latest.evaluation_id,
                message=self._format_message(rule, triggered, latest.score),
            ))

        return results

    def _check_rule(self, rule: AlertRule, value: float) -> bool:
        ops: dict[str, Any] = {
            "gt": lambda v, t: v > t,
            "lt": lambda v, t: v < t,
            "gte": lambda v, t: v >= t,
            "lte": lambda v, t: v <= t,
            "eq": lambda v, t: v == t,
        }
        check = ops.get(rule.operator)
        if check is None:
            return False
        return check(value, rule.threshold)

    @staticmethod
    def _format_message(rule: AlertRule, triggered: bool, value: float) -> str:
        op_symbols = {"gt": ">", "lt": "<", "gte": ">=", "lte": "<=", "eq": "=="}
        op_str = op_symbols.get(rule.operator, rule.operator)
        status = "TRIGGERED" if triggered else "OK"
        return f"[{status}] {rule.name}: {rule.metric_name} = {value:.3f} {op_str} {rule.threshold}"


@dataclass
class DefaultAlertRules:
    @staticmethod
    def get_defaults() -> list[AlertRule]:
        return [
            AlertRule(
                name="Low Pass Rate",
                metric_name="exact_match",
                operator="lt",
                threshold=0.5,
                description="Exact match pass rate dropped below 50%",
                cooldown_hours=24,
            ),
            AlertRule(
                name="Score Drop",
                metric_name="goal_achievement",
                operator="lt",
                threshold=0.6,
                description="Goal achievement score below 0.6",
                cooldown_hours=24,
            ),
            AlertRule(
                name="Tool Selection Degradation",
                metric_name="tool_selection",
                operator="lt",
                threshold=0.5,
                description="Tool selection F1 score below 0.5",
                cooldown_hours=24,
            ),
        ]
