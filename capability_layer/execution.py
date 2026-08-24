from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

class ExecutionBackend(ABC):
    name: str = "abstract"

    @abstractmethod
    def run_code(self, code: str, *, language: str = "python") -> dict[str, Any]:
        ...

    @abstractmethod
    def run_command(self, command: str) -> dict[str, Any]:
        ...

    def close(self) -> None:
        pass
