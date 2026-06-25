from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ObservableEvent:
    event_type: str
    component: str
    timestamp: datetime
    data: dict[str, Any]
    duration_ms: int | None = None


@dataclass
class Trace:
    trace_id: str
    evaluation_id: str
    events: list[ObservableEvent] = field(default_factory=list)
