from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class CapabilityResult:
    capability: str
    status: str
    message: str = ""
    data: Optional[dict[str, Any]] = None
    backend: Optional[str] = None
    execution_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "status": self.status,
            "message": self.message,
            "data": self.data,
            "backend": self.backend,
            "execution_id": self.execution_id,
            "metadata": self.metadata,
        }
