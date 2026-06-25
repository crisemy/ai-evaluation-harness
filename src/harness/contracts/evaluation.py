from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MetricResult:
    metric_name: str
    score: float
    passed: bool
    explanation: str
    threshold: float = 0.5
    diagnosis: dict[str, Any] | None = None


@dataclass
class EvaluationResult:
    entry_id: str
    metrics: list[MetricResult]
    overall_score: float
    overall_passed: bool
    duration_ms: int
    timestamp: datetime
