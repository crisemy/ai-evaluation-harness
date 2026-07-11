from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from harness.contracts.evaluation import MetricResult
from harness.interfaces.metric import Metric

logger = logging.getLogger(__name__)


@dataclass
class PromptVersion:
    version: str
    content: str
    changelog: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now())


@dataclass
class PromptEntry:
    prompt_id: str
    label: str
    input: str
    expected_output: str
    versions: list[PromptVersion] = field(default_factory=list)


class PromptRegistry:
    def __init__(self, registry_path: str | None = None):
        self._entries: dict[str, PromptEntry] = {}
        self._registry_path = registry_path

    def register(self, entry: PromptEntry) -> None:
        self._entries[entry.prompt_id] = entry

    def get(self, prompt_id: str) -> PromptEntry | None:
        return self._entries.get(prompt_id)

    def list_all(self) -> list[PromptEntry]:
        return list(self._entries.values())

    def add_version(self, prompt_id: str, version: PromptVersion) -> None:
        entry = self._entries.get(prompt_id)
        if entry:
            entry.versions.append(version)

    def save(self, path: str | None = None) -> str:
        out = path or self._registry_path or "prompt_registry.json"
        data = []
        for entry in self._entries.values():
            data.append({
                "prompt_id": entry.prompt_id,
                "label": entry.label,
                "input": entry.input,
                "expected_output": entry.expected_output,
                "versions": [
                    {"version": v.version, "content": v.content, "changelog": v.changelog, "timestamp": v.timestamp.isoformat()}
                    for v in entry.versions
                ],
            })
        Path(out).write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return out

    @classmethod
    def load(cls, path: str) -> PromptRegistry:
        registry = cls(path)
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        for item in raw:
            entry = PromptEntry(
                prompt_id=item["prompt_id"],
                label=item.get("label", ""),
                input=item["input"],
                expected_output=item.get("expected_output", ""),
                versions=[
                    PromptVersion(**v) for v in item.get("versions", [])
                ],
            )
            registry.register(entry)
        return registry


class PromptRegressionMetric(Metric):
    def __init__(self, threshold: float = 0.8):
        super().__init__(threshold)

    @property
    def name(self) -> str:
        return "prompt_regression"

    def evaluate(
        self,
        response: str,
        expected: str,
        context: dict[str, Any] | None = None,
    ) -> MetricResult:
        old_response = (context or {}).get("old_response", "")
        if not old_response:
            return MetricResult(
                metric_name=self.name,
                score=1.0,
                passed=True,
                explanation="No baseline response to compare — skipping regression check",
                threshold=self.threshold,
            )

        new_words = set(response.strip().lower().split())
        old_words = set(old_response.strip().lower().split())
        if not old_words and not new_words:
            score = 1.0
        elif not old_words or not new_words:
            score = 0.0
        else:
            intersection = new_words & old_words
            precision = len(intersection) / len(new_words) if new_words else 0.0
            recall = len(intersection) / len(old_words) if old_words else 0.0
            score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        passed = score >= self.threshold
        return MetricResult(
            metric_name=self.name,
            score=round(score, 4),
            passed=passed,
            explanation=(
                f"Regression F1={score:.3f} (threshold={self.threshold})"
                if passed
                else f"REGRESSION DETECTED: F1={score:.3f} below threshold={self.threshold}"
            ),
            threshold=self.threshold,
        )
