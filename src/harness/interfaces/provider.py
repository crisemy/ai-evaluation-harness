from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from harness.contracts.execution import ExecutionRequest, ExecutionResponse, StreamChunk


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, request: ExecutionRequest) -> ExecutionResponse:
        pass

    @abstractmethod
    def stream(self, request: ExecutionRequest) -> AsyncIterator[StreamChunk]:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def available_models(self) -> list[str]:
        pass
