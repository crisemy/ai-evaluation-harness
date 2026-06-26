from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Protocol

from harness.contracts.dataset import Dataset, DatasetEntry
from harness.contracts.execution import ExecutionRequest, ExecutionResponse
from harness.errors import HarnessError
from harness.interfaces.dataset_loader import DatasetLoader
from harness.interfaces.provider import LLMProvider

logger = logging.getLogger(__name__)


class ExecutorObserver(Protocol):
    def on_entry_start(self, entry: DatasetEntry) -> None: ...
    def on_entry_complete(self, entry: DatasetEntry, response: ExecutionResponse) -> None: ...
    def on_entry_error(self, entry: DatasetEntry, error: Exception) -> None: ...


@dataclass
class ExecutorConfig:
    provider: str = "ollama"
    model: str = "phi3"
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 1.0
    stop_sequences: list[str] = field(default_factory=list)
    extra_params: dict = field(default_factory=dict)


class PromptExecutor:
    def __init__(
        self,
        loader: DatasetLoader,
        provider: LLMProvider,
        config: ExecutorConfig | None = None,
    ):
        self._loader = loader
        self._provider = provider
        self._config = config or ExecutorConfig()

    @property
    def config(self) -> ExecutorConfig:
        return self._config

    def execute(self, dataset_path: str) -> list[ExecutionResponse]:
        dataset = self._loader.load(dataset_path)
        return self.execute_dataset(dataset)

    def execute_dataset(self, dataset: Dataset) -> list[ExecutionResponse]:
        responses: list[ExecutionResponse] = []
        for entry in dataset.entries:
            response = self.execute_entry(entry)
            responses.append(response)
        return responses

    def execute_entry(self, entry: DatasetEntry) -> ExecutionResponse:
        request = ExecutionRequest(
            entry_id=entry.id,
            prompt=entry.input,
            provider=self._config.provider,
            model=self._config.model,
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens,
            top_p=self._config.top_p,
            stop_sequences=self._config.stop_sequences,
            extra_params=self._config.extra_params,
        )

        try:
            response = self._provider.generate(request)
            logger.info(
                "Entry %s: %d tokens in %dms",
                entry.id,
                response.token_usage.total_tokens,
                response.latency_ms,
            )
            return response
        except HarnessError:
            raise
        except Exception as e:
            raise HarnessError(f"Unexpected error executing entry {entry.id}: {e}") from e
