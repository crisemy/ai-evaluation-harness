from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from harness.contracts.trace import ObservableEvent, Trace
from harness.interfaces.observer import Observer


class TraceObserver(Observer):
    def __init__(self, traces_dir: str | None = None):
        self._traces: dict[str, Trace] = {}
        self._current_trace_id: str | None = None
        self._current_evaluation_id: str | None = None
        self._traces_dir = traces_dir

    def set_context(self, trace_id: str, evaluation_id: str) -> None:
        self._current_trace_id = trace_id
        self._current_evaluation_id = evaluation_id

    def clear_context(self) -> None:
        self._current_trace_id = None
        self._current_evaluation_id = None

    def emit(self, event: ObservableEvent) -> None:
        if self._current_trace_id is None or self._current_evaluation_id is None:
            return

        if self._current_trace_id not in self._traces:
            self._traces[self._current_trace_id] = Trace(
                trace_id=self._current_trace_id,
                evaluation_id=self._current_evaluation_id,
                events=[],
            )
        self._traces[self._current_trace_id].events.append(event)

    def get_trace(self, evaluation_id: str) -> Trace | None:
        for t in self._traces.values():
            if t.evaluation_id == evaluation_id:
                return t
        return None

    def get_all_traces(self) -> list[Trace]:
        return list(self._traces.values())

    def flush(self, path: str | None = None) -> str | None:
        target = path or self._traces_dir
        if not target:
            return None

        p = Path(target)
        p.parent.mkdir(parents=True, exist_ok=True)

        records: list[dict[str, Any]] = []
        for trace in self._traces.values():
            records.append({
                "trace_id": trace.trace_id,
                "evaluation_id": trace.evaluation_id,
                "events": [
                    {
                        "event_type": e.event_type,
                        "component": e.component,
                        "timestamp": e.timestamp.isoformat(),
                        "data": e.data,
                        "duration_ms": e.duration_ms,
                    }
                    for e in trace.events
                ],
            })

        p.write_text(
            "\n".join(json.dumps(r, default=str, ensure_ascii=False) for r in records),
            encoding="utf-8",
        )
        return str(p)

    @classmethod
    def load_ndjson(cls, path: str) -> list[Trace]:
        p = Path(path)
        if not p.exists():
            return []

        traces: list[Trace] = []
        for line in p.read_text(encoding="utf-8").strip().splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            events = [
                ObservableEvent(
                    event_type=e["event_type"],
                    component=e["component"],
                    timestamp=datetime.fromisoformat(e["timestamp"]),
                    data=e.get("data", {}),
                    duration_ms=e.get("duration_ms"),
                )
                for e in raw.get("events", [])
            ]
            traces.append(Trace(
                trace_id=raw["trace_id"],
                evaluation_id=raw["evaluation_id"],
                events=events,
            ))
        return traces
