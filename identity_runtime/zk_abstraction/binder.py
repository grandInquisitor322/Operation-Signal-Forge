# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""SF-3.5-BIND-1..4 — abstract context/claim binding (no concrete hash mandated)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping


@dataclass(frozen=True)
class BindingTarget:
    """Abstract binding target. Concrete construction is scheme-provided."""

    context_id: str
    revision: int
    eligibility_proposition: str
    public_conditions_fingerprint: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id,
            "revision": self.revision,
            "eligibility_proposition": self.eligibility_proposition,
            "public_conditions_fingerprint": self.public_conditions_fingerprint,
        }


class ContextClaimBinder:
    """
    SF-3.5-BIND-1, BIND-2: covers context_id, revision, proposition, public conditions.
    Changing any element MUST produce a distinct proof target.
    Does NOT select a concrete hash/transcript primitive (scheme-local).
    """

    def compute_target(
        self,
        *,
        context_id: str,
        revision: int,
        eligibility_proposition: str,
        public_conditions: Mapping[str, Any],
    ) -> BindingTarget:
        items = sorted((str(k), repr(v)) for k, v in public_conditions.items())
        fp = "|".join(f"{k}={v}" for k, v in items)
        return BindingTarget(
            context_id=context_id,
            revision=revision,
            eligibility_proposition=eligibility_proposition,
            public_conditions_fingerprint=fp,
        )