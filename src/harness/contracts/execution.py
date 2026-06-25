from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float | None = None


@dataclass
class StreamChunk:
    token: str
    finish_reason: str | None = None


@dataclass
class ExecutionRequest:
    entry_id: str
    prompt: str
    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 1.0
    stop_sequences: list[str] = field(default_factory=list)
    extra_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResponse:
    entry_id: str
    text: str
    provider: str
    model: str
    latency_ms: int
    token_usage: TokenUsage
    timestamp: datetime
    finish_reason: str = "stop"
    raw_response: dict[str, Any] | None = None
