from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EvalSchedule:
    name: str
    dataset_path: str
    provider: str = "ollama"
    model: str = "phi3"
    metrics: list[str] = field(default_factory=lambda: ["exact_match", "contains"])
    interval_seconds: int = 3600
    limit: int = 5
    gate: str = "warning"
    enabled: bool = True
    last_run: str = ""


class SchedulerEngine:
    def __init__(self, config_path: str = ".harness/schedules.json"):
        self._config_path = config_path
        self._schedules: list[EvalSchedule] = []
        self._load()

    def _load(self) -> None:
        path = Path(self._config_path)
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            self._schedules = [EvalSchedule(**s) for s in raw]

    def save(self) -> None:
        path = Path(self._config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "name": s.name,
                "dataset_path": s.dataset_path,
                "provider": s.provider,
                "model": s.model,
                "metrics": s.metrics,
                "interval_seconds": s.interval_seconds,
                "limit": s.limit,
                "gate": s.gate,
                "enabled": s.enabled,
                "last_run": s.last_run,
            }
            for s in self._schedules
        ]
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add(self, schedule: EvalSchedule) -> None:
        self._schedules.append(schedule)
        self.save()

    def list_schedules(self) -> list[EvalSchedule]:
        return self._schedules

    def run_due(self, runner) -> list[dict[str, Any]]:
        results = []
        now = datetime.now(timezone.utc)
        for sched in self._schedules:
            if not sched.enabled:
                continue
            if sched.last_run:
                last = datetime.fromisoformat(sched.last_run)
                elapsed = (now - last).total_seconds()
                if elapsed < sched.interval_seconds:
                    continue

            logger.info("Running scheduled eval: %s", sched.name)
            try:
                exit_code = runner(sched)
                sched.last_run = now.isoformat()
                results.append({"schedule": sched.name, "exit_code": exit_code, "status": "ok"})
            except Exception as e:
                logger.error("Scheduled eval %s failed: %s", sched.name, e)
                results.append({"schedule": sched.name, "error": str(e), "status": "error"})

        self.save()
        return results
