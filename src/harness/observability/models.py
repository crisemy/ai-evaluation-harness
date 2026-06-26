from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MetricSnapshot:
    metric_name: str
    score: float
    passed: bool
    threshold: float
    timestamp: datetime
    evaluation_id: str
    entry_id: str | None = None
    config_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass
class TimeSeriesData:
    metric_name: str
    snapshots: list[MetricSnapshot] = field(default_factory=list)


@dataclass
class AlertRule:
    name: str
    metric_name: str
    operator: str
    threshold: float
    description: str = ""
    cooldown_hours: int = 24


@dataclass
class AlertResult:
    rule_name: str
    metric_name: str
    triggered: bool
    current_value: float
    threshold: float
    operator: str
    timestamp: datetime
    evaluation_id: str | None = None
    message: str = ""


@dataclass
class DashboardConfig:
    title: str = "AI Evaluation Harness Dashboard"
    refresh_interval_seconds: int = 300
    max_snapshots_per_metric: int = 100
    show_alert_history: bool = True
