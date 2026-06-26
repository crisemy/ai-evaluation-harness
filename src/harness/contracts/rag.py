from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    id: str
    text: str
    source: str | None = None
    metadata: dict[str, Any] | None = None
    score: float | None = None


@dataclass
class DocumentChunk:
    id: str
    text: str
    source: str | None = None
    chunk_index: int = 0
    metadata: dict[str, Any] | None = None


@dataclass
class RAGEvaluationInput:
    query: str
    expected_output: str
    context_documents: list[Document]
    response: str | None = None
