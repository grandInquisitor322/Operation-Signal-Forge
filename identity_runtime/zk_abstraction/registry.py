# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""SF-3.5-ABS / SF-3.5-LIFE — Governed cryptographic scheme registry.
Gate 6: scheme → SchemeVerifier binding (resolve_verifier).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Set, Tuple


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
    """Scheme metadata — adapter binding via registry, not domain code."""

    scheme_id: str
    scheme_version: str
    state: SchemeLifecycleState
    deprecated_allowed_ops: frozenset = field(default_factory=frozenset)
    scheme_material_ref: str = "mock"
    public_scalar_modulus: int | None = None
    adapter_id: str = ""


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
        self._verifiers: Dict[Tuple[str, str], object] = {}

    def register_scheme(self, descriptor: SchemeDescriptor) -> None:
        key = (descriptor.scheme_id, descriptor.scheme_version)
        # Back-compat: mock-scheme gets BN254 Fr modulus if unset
        if (
            descriptor.scheme_id == "mock-scheme"
            and descriptor.public_scalar_modulus is None
        ):
            from identity_runtime.zk_abstraction.bn254 import BN254_R

            descriptor = SchemeDescriptor(
                scheme_id=descriptor.scheme_id,
                scheme_version=descriptor.scheme_version,
                state=descriptor.state,
                deprecated_allowed_ops=descriptor.deprecated_allowed_ops,
                scheme_material_ref=descriptor.scheme_material_ref,
                public_scalar_modulus=BN254_R,
                adapter_id=descriptor.adapter_id or "mock-bn254-sfg16a",
            )
        self._schemes[key] = descriptor

    def register_verifier(self, scheme_id: str, version: str, verifier: object) -> None:
        self._verifiers[(scheme_id, version)] = verifier

    def resolve_verifier(self, scheme_id: str, version: str) -> object:
        key = (scheme_id, version)
        if key in self._verifiers:
            return self._verifiers[key]
        verifier = _default_verifier_for(scheme_id, version)
        if verifier is None:
            raise KeyError(f"UNSUPPORTED_SCHEME_VERIFIER:{scheme_id}@{version}")
        self._verifiers[key] = verifier
        return verifier

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


def _default_verifier_for(scheme_id: str, version: str) -> Optional[object]:
    if scheme_id == "mock-scheme" and version == "1.0.0":
        from identity_runtime.zk_abstraction.adapters.mock_bn254_sfg16a import (
            MockBn254Sfg16aVerifier,
        )

        return MockBn254Sfg16aVerifier()
    if scheme_id == "mock-digest" and version == "1.0.0":
        from identity_runtime.zk_abstraction.adapters.mock_digest_v2 import (
            MockDigestV2Verifier,
        )

        return MockDigestV2Verifier()
    return None


def install_default_mock_schemes(
    registry: CryptographicRegistry,
) -> CryptographicRegistry:
    """Register Gate 6 mock schemes A (BN254 SFG16A) and B (digest v2)."""
    from identity_runtime.zk_abstraction.adapters.mock_bn254_sfg16a import (
        MATERIALS_REF as M1,
        MockBn254Sfg16aVerifier,
        SCHEME_ID as S1,
        SCHEME_VERSION as V1,
    )
    from identity_runtime.zk_abstraction.adapters.mock_digest_v2 import (
        MATERIALS_REF as M2,
        MockDigestV2Verifier,
        SCHEME_ID as S2,
        SCHEME_VERSION as V2,
    )
    from identity_runtime.zk_abstraction.bn254 import BN254_R

    registry.register_scheme(
        SchemeDescriptor(
            scheme_id=S1,
            scheme_version=V1,
            state=SchemeLifecycleState.SUPPORTED,
            scheme_material_ref=M1,
            public_scalar_modulus=BN254_R,
            adapter_id="mock-bn254-sfg16a",
        )
    )
    registry.register_verifier(S1, V1, MockBn254Sfg16aVerifier())
    registry.register_scheme(
        SchemeDescriptor(
            scheme_id=S2,
            scheme_version=V2,
            state=SchemeLifecycleState.SUPPORTED,
            scheme_material_ref=M2,
            public_scalar_modulus=None,
            adapter_id="mock-digest-v2",
        )
    )
    registry.register_verifier(S2, V2, MockDigestV2Verifier())
    return registry