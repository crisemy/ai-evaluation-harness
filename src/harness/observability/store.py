from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from harness.contracts.evaluation import EvaluationResult
from harness.contracts.report import EvaluationSummary
from harness.observability.models import MetricSnapshot, TimeSeriesData


class TimeSeriesStore:
    def __init__(self, store_path: str):
        self._path = Path(store_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, summary: EvaluationSummary) -> int:
        count = 0
        with self._path.open("a", encoding="utf-8") as f:
            for result in summary.results:
                for mr in result.metrics:
                    snapshot = MetricSnapshot(
                        metric_name=mr.metric_name,
                        score=mr.score,
                        passed=mr.passed,
                        threshold=mr.threshold,
                        timestamp=result.timestamp or summary.timestamp,
                        evaluation_id=summary.evaluation_id,
                        entry_id=result.entry_id,
                        config_snapshot={
                            "provider": summary.config.provider,
                            "model": summary.config.model,
                            "dataset_path": summary.config.dataset_path,
                        },
                    )
                    f.write(
                        json.dumps(self._snapshot_to_dict(snapshot), default=str, ensure_ascii=False)
                        + "\n"
                    )
                    count += 1
        return count

    def read_all(self) -> list[MetricSnapshot]:
        if not self._path.exists():
            return []

        snapshots: list[MetricSnapshot] = []
        for line in self._path.read_text(encoding="utf-8").strip().splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            snapshots.append(self._dict_to_snapshot(raw))
        return snapshots

    def get_time_series(self, metric_name: str | None = None) -> list[TimeSeriesData]:
        all_snapshots = self.read_all()
        grouped: dict[str, list[MetricSnapshot]] = {}
        for snap in all_snapshots:
            if metric_name and snap.metric_name != metric_name:
                continue
            grouped.setdefault(snap.metric_name, []).append(snap)

        return [
            TimeSeriesData(metric_name=name, snapshots=sorted(snaps, key=lambda s: s.timestamp))
            for name, snaps in grouped.items()
        ]

    def clear(self) -> None:
        if self._path.exists():
            self._path.write_text("", encoding="utf-8")

    @staticmethod
    def _snapshot_to_dict(snapshot: MetricSnapshot) -> dict[str, Any]:
        return {
            "metric_name": snapshot.metric_name,
            "score": snapshot.score,
            "passed": snapshot.passed,
            "threshold": snapshot.threshold,
            "timestamp": snapshot.timestamp.isoformat(),
            "evaluation_id": snapshot.evaluation_id,
            "entry_id": snapshot.entry_id,
            "config_snapshot": snapshot.config_snapshot,
        }

    @staticmethod
    def _dict_to_snapshot(raw: dict[str, Any]) -> MetricSnapshot:
        return MetricSnapshot(
            metric_name=raw["metric_name"],
            score=raw["score"],
            passed=raw["passed"],
            threshold=raw["threshold"],
            timestamp=datetime.fromisoformat(raw["timestamp"]),
            evaluation_id=raw["evaluation_id"],
            entry_id=raw.get("entry_id"),
            config_snapshot=raw.get("config_snapshot", {}),
        )
