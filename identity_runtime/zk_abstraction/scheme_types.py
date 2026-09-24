# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""Gate 6 — BoundStatementTarget, CryptoValidityResult, SchemeVerifier port."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Protocol, runtime_checkable


class CryptoOutcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    MALFORMED = "MALFORMED"
    UNVERIFIABLE = "UNVERIFIABLE"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class CryptoValidityResult:
    """Sole normative SchemeVerifier output — C1 crypto only."""

    outcome: CryptoOutcome
    reason_code: str
    scheme_id: str
    scheme_version: str
    reason_detail: str = ""
    materials_ref: str = ""
    adapter_id: str = ""
    statement_id: str = ""


@dataclass(frozen=True)
class BoundStatementTarget:
    """Immutable orchestrator snapshot for one verification attempt."""

    statement_id: str
    scheme_id: str
    scheme_version: str
    materials_ref: str
    public_input_view: Mapping[str, str]
    context_id: str = ""
    revision: str = ""
    eligibility_proposition: str = ""
    relation_hint: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "public_input_view",
            MappingProxyType(dict(self.public_input_view)),
        )


@runtime_checkable
class SchemeVerifier(Protocol):
    """Stable C1 cryptographic mechanism port."""

    adapter_id: str

    def verify_crypto(
        self,
        proof_bytes: bytes,
        bound: BoundStatementTarget,
    ) -> CryptoValidityResult: ...