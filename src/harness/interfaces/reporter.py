from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from harness.contracts.report import EvaluationSummary, Report


class Reporter(ABC):
    @abstractmethod
    def generate(
        self,
        summary: EvaluationSummary,
        format: str,
        options: dict[str, Any] | None = None,
    ) -> Report:
        pass
