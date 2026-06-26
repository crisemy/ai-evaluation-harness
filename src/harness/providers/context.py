from __future__ import annotations

from harness.contracts.rag import Document
from harness.interfaces.context_provider import ContextProvider


class DatasetContextProvider(ContextProvider):
    def __init__(self, documents: list[Document]):
        self._documents = documents

    def get_context(self, query: str, top_k: int = 5) -> list[Document]:
        return self._documents[:top_k]
