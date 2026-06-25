from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class DatasetEntry:
    id: str
    input: str
    expected_output: str
    category: str | None = None
    difficulty: Difficulty | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class DatasetMetadata:
    name: str
    description: str | None = None
    created: datetime | None = None
    format_version: str = "1.0"


@dataclass
class Dataset:
    metadata: DatasetMetadata
    entries: list[DatasetEntry]
