"""Ports between Capability Layer and the rest of Signal Forge."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional

class DetectionReadPort(ABC):
    @abstractmethod
    def get_cell(self, cell_id: str) -> Optional[dict[str, Any]]:
        ...

    @abstractmethod
    def list_cells(self, *, site_id: Optional[str] = None,
                   min_fused_probability: Optional[float] = None,
                   limit: int = 20) -> list[dict[str, Any]]:
        ...
