from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ChangeType(str, Enum):
    PROMPT_TEMPLATE = "prompt_template"
    MODEL_CONFIG = "model_config"
    MODEL_SWAP = "model_swap"
    AGENT_TOOL = "agent_tool"
    SAFETY_CONFIG = "safety_config"
    SYSTEM_PROMPT = "system_prompt"
    TRAINING_DATA = "training_data"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SafetyRelevance(str, Enum):
    NON_SAFETY = "non_safety"
    SAFETY_ADJACENT = "safety_adjacent"
    SAFETY_CRITICAL = "safety_critical"


class HistoricalStability(str, Enum):
    STABLE = "stable"
    NORMAL = "normal"
    FLAKY = "flaky"
    HIGH_FAILURE = "high_failure"


CHANGE_TYPE_WEIGHTS: dict[ChangeType, float] = {
    ChangeType.PROMPT_TEMPLATE: 1.0,
    ChangeType.MODEL_CONFIG: 2.0,
    ChangeType.MODEL_SWAP: 3.0,
    ChangeType.AGENT_TOOL: 3.0,
    ChangeType.SAFETY_CONFIG: 3.0,
    ChangeType.SYSTEM_PROMPT: 3.0,
    ChangeType.TRAINING_DATA: 5.0,
}

SAFETY_RELEVANCE_WEIGHTS: dict[SafetyRelevance, float] = {
    SafetyRelevance.NON_SAFETY: 1.0,
    SafetyRelevance.SAFETY_ADJACENT: 2.0,
    SafetyRelevance.SAFETY_CRITICAL: 3.0,
}

HISTORICAL_MULTIPLIERS: dict[HistoricalStability, float] = {
    HistoricalStability.STABLE: 0.5,
    HistoricalStability.NORMAL: 1.0,
    HistoricalStability.FLAKY: 1.5,
    HistoricalStability.HIGH_FAILURE: 2.0,
}

RISK_LEVEL_THRESHOLDS: list[tuple[float, RiskLevel]] = [
    (2.0, RiskLevel.LOW),
    (5.0, RiskLevel.MEDIUM),
    (10.0, RiskLevel.HIGH),
    (float("inf"), RiskLevel.CRITICAL),
]

RISK_LEVEL_GATES: dict[RiskLevel, str] = {
    RiskLevel.LOW: "auto_approve",
    RiskLevel.MEDIUM: "warning",
    RiskLevel.HIGH: "requires_override",
    RiskLevel.CRITICAL: "no_go",
}


def compute_risk_level(score: float) -> RiskLevel:
    for threshold, level in RISK_LEVEL_THRESHOLDS:
        if score <= threshold:
            return level
    return RiskLevel.CRITICAL


@dataclass
class RiskProfile:
    change_type: ChangeType = ChangeType.PROMPT_TEMPLATE
    safety_relevance: SafetyRelevance = SafetyRelevance.NON_SAFETY
    historical_stability: HistoricalStability = HistoricalStability.NORMAL
    custom_weight: float | None = None


@dataclass
class RiskAssessment:
    score: float
    level: RiskLevel
    gate: str
    profile: RiskProfile
    breakdown: dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now())
    rationale: str = ""


@dataclass
class RiskRecord:
    risk_assessment: RiskAssessment
    impact_score: float = 0.0
    affected_evals: list[str] = field(default_factory=list)
    change_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
