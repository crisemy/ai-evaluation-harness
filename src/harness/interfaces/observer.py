from __future__ import annotations

from abc import ABC, abstractmethod

from harness.contracts.trace import ObservableEvent, Trace


class Observer(ABC):
    @abstractmethod
    def emit(self, event: ObservableEvent) -> None:
        pass

    @abstractmethod
    def get_trace(self, evaluation_id: str) -> Trace:
        pass
