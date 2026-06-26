from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentStep:
    step_index: int
    thought: str | None = None
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_output: str | None = None
    duration_ms: int | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class AgentTrajectory:
    entry_id: str
    task: str
    steps: list[AgentStep]
    final_answer: str | None = None
    total_duration_ms: int = 0
    total_tokens: int = 0
    metadata: dict[str, Any] | None = None


@dataclass
class AgentEvaluationInput:
    task: str
    expected_output: str
    trajectory: AgentTrajectory
    expected_trajectory: list[AgentStep] | None = None
    expected_tools: list[str] | None = None
