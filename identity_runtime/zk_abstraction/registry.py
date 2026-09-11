# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""SF-3.5-ABS / SF-3.5-LIFE — Governed cryptographic scheme registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Set, Tuple


class SchemeLifecycleState(Enum):
    SUPPORTED = "SUPPORTED"
    DEPRECATED = "DEPRECATED"
    DISABLED = "DISABLED"
    RETIRED = "RETIRED"


class OperationType(Enum):
    PROOF_GENERATION = "PROOF_GENERATION"
    PROOF_VERIFICATION = "PROOF_VERIFICATION"


@dataclass(frozen=True)
class SchemeDescriptor:
    """Scheme metadata only — no concrete ZK library binding in domain code."""

    scheme_id: str
    scheme_version: str
    state: SchemeLifecycleState
    deprecated_allowed_ops: frozenset = field(default_factory=frozenset)
    scheme_material_ref: str = "mock"


@dataclass(frozen=True)
class EvaluationResult:
    allowed: bool
    reason: str
    status_code: str


class CryptographicRegistry:
    """SF-3.5-ABS-1..10, SF-3.5-LIFE-1..6 — register/resolve/validate fail-closed."""

    def __init__(self) -> None:
        self._schemes: Dict[Tuple[str, str], SchemeDescriptor] = {}
        self._min_scheme_version: Dict[str, str] = {}
        self._allowed_protocol_versions: Set[str] = {"1.0.0"}

    def register_scheme(self, descriptor: SchemeDescriptor) -> None:
        key = (descriptor.scheme_id, descriptor.scheme_version)
        self._schemes[key] = descriptor

    def resolve_scheme(self, scheme_id: str, version: str) -> SchemeDescriptor:
        key = (scheme_id, version)
        if key not in self._schemes:
            raise KeyError(f"UNSUPPORTED_SCHEME:{scheme_id}@{version}")
        return self._schemes[key]

    def set_allowed_protocol_versions(self, versions: Set[str]) -> None:
        self._allowed_protocol_versions = set(versions)

    def set_min_scheme_version(self, scheme_id: str, min_version: str) -> None:
        self._min_scheme_version[scheme_id] = min_version

    def validate_operation(
        self,
        scheme_id: str,
        version: str,
        operation: OperationType,
        *,
        protocol_version: str = "1.0.0",
        policy_version: str = "1.0.0",
    ) -> EvaluationResult:
        try:
            desc = self.resolve_scheme(scheme_id, version)
        except KeyError:
            return EvaluationResult(
                False, "unregistered_scheme", "UNSUPPORTED_SCHEME"
            )

        if protocol_version not in self._allowed_protocol_versions:
            return EvaluationResult(
                False, "unsupported_protocol_version", "UNSUPPORTED_PROTOCOL"
            )

        min_v = self._min_scheme_version.get(scheme_id)
        if min_v is not None and _version_lt(version, min_v):
            return EvaluationResult(
                False, "unauthorized_scheme_downgrade", "SCHEME_DOWNGRADE"
            )

        state = desc.state
        if state in (SchemeLifecycleState.DISABLED, SchemeLifecycleState.RETIRED):
            return EvaluationResult(
                False, f"scheme_{state.value.lower()}", f"SCHEME_{state.value}"
            )
        if state == SchemeLifecycleState.DEPRECATED:
            if operation not in desc.deprecated_allowed_ops:
                return EvaluationResult(
                    False,
                    "deprecated_disallowed_by_policy",
                    "SCHEME_DEPRECATED_DISALLOWED",
                )

        return EvaluationResult(True, "ok", "OK")


def _version_lt(a: str, b: str) -> bool:
    try:
        ta = tuple(int(x) for x in a.split("."))
        tb = tuple(int(x) for x in b.split("."))
        return ta < tb
    except ValueError:
        return True