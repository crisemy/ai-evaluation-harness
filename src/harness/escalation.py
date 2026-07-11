from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from harness.contracts.evaluation import FAILURE_CODE_SEVERITY, FailureCode
from harness.contracts.report import EvaluationSummary
from harness.contracts.risk import RiskAssessment, RiskLevel

logger = logging.getLogger(__name__)


class GateAction(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    BLOCK = "block"


SEVERITY_GATE_MAP: dict[int, GateAction] = {
    1: GateAction.PASS,
    2: GateAction.PASS,
    3: GateAction.WARNING,
    4: GateAction.BLOCK,
    5: GateAction.BLOCK,
}

RISK_GATE_MAP: dict[RiskLevel, GateAction] = {
    RiskLevel.LOW: GateAction.PASS,
    RiskLevel.MEDIUM: GateAction.WARNING,
    RiskLevel.HIGH: GateAction.WARNING,
    RiskLevel.CRITICAL: GateAction.BLOCK,
}


@dataclass
class EscalationVerdict:
    action: GateAction
    reason: str
    failing_codes: list[FailureCode] = field(default_factory=list)
    max_severity: int = 1
    risk_gate: str = "pass"
    details: dict[str, Any] = field(default_factory=dict)


class EscalationEngine:
    def evaluate(self, summary: EvaluationSummary) -> EscalationVerdict:
        failing_codes: list[FailureCode] = []
        max_severity = 1

        for result in summary.results:
            for metric in result.metrics:
                if not metric.passed and metric.failure_code:
                    failing_codes.append(metric.failure_code)
                    sev = FAILURE_CODE_SEVERITY.get(metric.failure_code, 1)
                    if sev > max_severity:
                        max_severity = sev

        severity_action = SEVERITY_GATE_MAP.get(max_severity, GateAction.PASS)

        risk_action: GateAction = GateAction.PASS
        risk_gate = "pass"
        if summary.risk_assessment:
            risk_gate = summary.risk_assessment.gate
            risk_action = RISK_GATE_MAP.get(summary.risk_assessment.level, GateAction.PASS)

        action = severity_action if severity_action.value != "pass" else risk_action
        if severity_action == GateAction.BLOCK or risk_action == GateAction.BLOCK:
            action = GateAction.BLOCK
        elif severity_action == GateAction.WARNING or risk_action == GateAction.WARNING:
            action = GateAction.WARNING

        reasons = []
        if failing_codes:
            codes_str = ", ".join(c.value for c in set(failing_codes))
            reasons.append(f"Failures: {codes_str} (max severity={max_severity})")
        if summary.risk_assessment and summary.risk_assessment.level != RiskLevel.LOW:
            reasons.append(f"Risk: {summary.risk_assessment.rationale}")

        reason = "; ".join(reasons) if reasons else "All checks passed"

        return EscalationVerdict(
            action=action,
            reason=reason,
            failing_codes=list(set(failing_codes)),
            max_severity=max_severity,
            risk_gate=risk_gate,
        )


__all__ = ["EscalationEngine", "EscalationVerdict", "GateAction"]
