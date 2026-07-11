from __future__ import annotations

import logging

from harness.contracts.risk import (
    CHANGE_TYPE_WEIGHTS,
    HISTORICAL_MULTIPLIERS,
    RISK_LEVEL_GATES,
    SAFETY_RELEVANCE_WEIGHTS,
    ChangeType,
    HistoricalStability,
    RiskAssessment,
    RiskLevel,
    RiskProfile,
    RiskRecord,
    SafetyRelevance,
    compute_risk_level,
)

logger = logging.getLogger(__name__)


class RiskClassifier:
    def classify(self, profile: RiskProfile) -> RiskAssessment:
        change_weight = profile.custom_weight or CHANGE_TYPE_WEIGHTS.get(profile.change_type, 1.0)
        safety_weight = SAFETY_RELEVANCE_WEIGHTS.get(profile.safety_relevance, 1.0)
        historical_multiplier = HISTORICAL_MULTIPLIERS.get(profile.historical_stability, 1.0)

        score = change_weight * safety_weight * historical_multiplier
        level = compute_risk_level(score)
        gate = RISK_LEVEL_GATES[level]

        breakdown = {
            "change_weight": change_weight,
            "safety_weight": safety_weight,
            "historical_multiplier": historical_multiplier,
        }

        rationale = (
            f"Risk={change_weight}×{safety_weight}×{historical_multiplier}={score:.1f} "
            f"({profile.change_type.value}, {profile.safety_relevance.value}, "
            f"{profile.historical_stability.value}) → {level.value} gate: {gate}"
        )

        return RiskAssessment(
            score=score,
            level=level,
            gate=gate,
            profile=profile,
            breakdown=breakdown,
            rationale=rationale,
        )


__all__ = ["RiskClassifier", "RiskAssessment", "RiskProfile", "RiskRecord", "RiskLevel", "ChangeType"]
