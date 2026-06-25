from __future__ import annotations

from abc import ABC, abstractmethod

from harness.contracts.dataset import Dataset


class DatasetLoader(ABC):
    @abstractmethod
    def load(self, path: str, format: str) -> Dataset:
        pass

    @abstractmethod
    def validate(self, entry: dict) -> None:
        pass
