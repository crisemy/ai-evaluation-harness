from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from harness.contracts.evaluation import EvaluationResult
from harness.contracts.risk import RiskAssessment


@dataclass
class EnvironmentInfo:
    harness_version: str
    python_version: str
    platform: str
    provider_versions: dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSummary:
    mean: float
    min: float
    max: float
    pass_rate: float


@dataclass
class EvaluationConfig:
    dataset_path: str
    dataset_format: str
    provider: str
    model: str
    metrics: list[str]
    environment: str = "local"
    release_id: str = ""
    execution_id: str = ""
    owner: str = ""


@dataclass
class SummaryStats:
    total_entries: int
    passed: int
    failed: int
    skipped: int
    pass_rate: float
    average_score: float
    metrics: dict[str, MetricSummary]


@dataclass
class EvaluationSummary:
    evaluation_name: str
    evaluation_id: str
    timestamp: datetime
    duration_ms: int
    config: EvaluationConfig
    environment: EnvironmentInfo
    summary: SummaryStats
    results: list[EvaluationResult]
    risk_assessment: RiskAssessment | None = None
    max_severity: int = 1


@dataclass
class ReportMetadata:
    format: str
    generated_at: datetime


@dataclass
class Report:
    format: str
    content: str
    metadata: ReportMetadata
