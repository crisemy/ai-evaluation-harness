from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from harness.contracts.evaluation import MetricResult


class Metric(ABC):
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def evaluate(
        self,
        response: str,
        expected: str,
        context: dict[str, Any] | None = None,
    ) -> MetricResult:
        pass
