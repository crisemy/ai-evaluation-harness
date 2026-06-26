from __future__ import annotations

from abc import ABC, abstractmethod

from harness.contracts.rag import Document


class ContextProvider(ABC):
    @abstractmethod
    def get_context(self, query: str, top_k: int = 5) -> list[Document]:
        pass
