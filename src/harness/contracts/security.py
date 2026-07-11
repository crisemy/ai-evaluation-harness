from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class RedTestCase:
    id: str
    category: str
    subcategory: str
    description: str
    input: str
    expected_behavior: str
    success_criteria: str


@dataclass
class RedTestResult:
    test_id: str
    category: str
    subcategory: str
    input: str
    response: str
    passed: bool
    explanation: str
    latency_ms: int = 0


@dataclass
class RedTestSummary:
    total: int
    passed: int
    failed: int
    attack_success_rate: float
    by_category: dict[str, dict[str, int]]
    results: list[RedTestResult]
    timestamp: datetime = field(default_factory=lambda: datetime.now())
