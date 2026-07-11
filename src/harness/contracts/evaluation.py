from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from harness.contracts.risk import RiskAssessment, RiskLevel


class FailureCode(str, Enum):
    ACC_ERR = "ACC_ERR"
    SAF_ERR = "SAF_ERR"
    REF_ERR = "REF_ERR"
    LAT_ERR = "LAT_ERR"
    TUL_ERR = "TUL_ERR"
    CON_ERR = "CON_ERR"
    INJ_ERR = "INJ_ERR"
    RET_ERR = "RET_ERR"
    CHK_ERR = "CHK_ERR"
    HAL_ERR = "HAL_ERR"
    BIAS_ERR = "BIAS_ERR"
    CXT_ERR = "CXT_ERR"


FAILURE_CODE_SEVERITY: dict[FailureCode, int] = {
    FailureCode.SAF_ERR: 5,
    FailureCode.INJ_ERR: 5,
    FailureCode.HAL_ERR: 4,
    FailureCode.TUL_ERR: 4,
    FailureCode.CON_ERR: 3,
    FailureCode.ACC_ERR: 3,
    FailureCode.RET_ERR: 3,
    FailureCode.CXT_ERR: 3,
    FailureCode.CHK_ERR: 2,
    FailureCode.BIAS_ERR: 2,
    FailureCode.LAT_ERR: 2,
    FailureCode.REF_ERR: 2,
}


@dataclass
class MetricResult:
    metric_name: str
    score: float
    passed: bool
    explanation: str
    threshold: float = 0.5
    diagnosis: dict[str, Any] | None = None
    failure_code: FailureCode | None = None
    severity: int = 1


@dataclass
class EvaluationResult:
    entry_id: str
    metrics: list[MetricResult]
    overall_score: float
    overall_passed: bool
    duration_ms: int
    timestamp: datetime
    risk_assessment: RiskAssessment | None = None
    max_severity: int = 1
