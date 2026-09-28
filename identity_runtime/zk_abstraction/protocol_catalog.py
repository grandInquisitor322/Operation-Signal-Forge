# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""Gate 7 — Protocol semantic contract catalog (SF-3.5-PROTO).

Maps (protocol_id, protocol_version) → immutable ProtocolSemanticContract.
Runtime selects and evaluates; does not redefine the contract.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class ProtocolSemanticContract:
    """Immutable semantic identity for one (protocol_id, protocol_version)."""

    protocol_id: str
    protocol_version: str
    contract_id: str
    # Explicit surfaces (ADR); values are opaque labels/ids, not ZK mechanisms
    stage_3_3_context_semantics: str
    stage_3_4_visibility_semantics: str
    c1_crypto_validity_required: bool
    c2_public_key_profile: str
    c3_binding_profile: str
    c4_admission_profile: str
    acceptance_conjunction: str  # e.g. "C1&C2&C3&C4"
    seal: str = ""  # content hash; set at publish

    def compute_seal(self) -> str:
        payload = {
            "protocol_id": self.protocol_id,
            "protocol_version": self.protocol_version,
            "contract_id": self.contract_id,
            "stage_3_3_context_semantics": self.stage_3_3_context_semantics,
            "stage_3_4_visibility_semantics": self.stage_3_4_visibility_semantics,
            "c1_crypto_validity_required": self.c1_crypto_validity_required,
            "c2_public_key_profile": self.c2_public_key_profile,
            "c3_binding_profile": self.c3_binding_profile,
            "c4_admission_profile": self.c4_admission_profile,
            "acceptance_conjunction": self.acceptance_conjunction,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:32]


@dataclass
class ProtocolCatalog:
    """Governed catalog: published contracts are immutable under their version key."""

    _entries: Dict[Tuple[str, str], ProtocolSemanticContract] = field(default_factory=dict)

    def publish(self, contract: ProtocolSemanticContract) -> ProtocolSemanticContract:
        """Publish or re-assert a contract. Same key + different seal is rejected."""
        key = (contract.protocol_id, contract.protocol_version)
        sealed = contract
        if not sealed.seal:
            sealed = ProtocolSemanticContract(
                protocol_id=contract.protocol_id,
                protocol_version=contract.protocol_version,
                contract_id=contract.contract_id,
                stage_3_3_context_semantics=contract.stage_3_3_context_semantics,
                stage_3_4_visibility_semantics=contract.stage_3_4_visibility_semantics,
                c1_crypto_validity_required=contract.c1_crypto_validity_required,
                c2_public_key_profile=contract.c2_public_key_profile,
                c3_binding_profile=contract.c3_binding_profile,
                c4_admission_profile=contract.c4_admission_profile,
                acceptance_conjunction=contract.acceptance_conjunction,
                seal=contract.compute_seal(),
            )
        existing = self._entries.get(key)
        if existing is not None and existing.seal != sealed.seal:
            raise ValueError(
                f"PROTOCOL_CONTRACT_IMMUTABLE:{key[0]}@{key[1]}:"
                f"existing_seal={existing.seal}:new_seal={sealed.seal}"
            )
        self._entries[key] = sealed
        return sealed

    def resolve(
        self, protocol_id: str, protocol_version: str
    ) -> Optional[ProtocolSemanticContract]:
        return self._entries.get((protocol_id, protocol_version))

    def require(
        self, protocol_id: str, protocol_version: str
    ) -> ProtocolSemanticContract:
        c = self.resolve(protocol_id, protocol_version)
        if c is None:
            raise KeyError(
                f"UNSUPPORTED_PROTOCOL_CONTRACT:{protocol_id}@{protocol_version}"
            )
        return c

    def keys(self) -> Tuple[Tuple[str, str], ...]:
        return tuple(self._entries.keys())


def default_sf_zk_v1_contract() -> ProtocolSemanticContract:
    """Baseline contract for sf-zk@1.0.0 (does not select a concrete ZK mechanism)."""
    c = ProtocolSemanticContract(
        protocol_id="sf-zk",
        protocol_version="1.0.0",
        contract_id="sf-zk-1.0.0-baseline",
        stage_3_3_context_semantics="stage-3.3-context-v1",
        stage_3_4_visibility_semantics="stage-3.4-visibility-v1",
        c1_crypto_validity_required=True,
        c2_public_key_profile="canonical-public-v1",
        c3_binding_profile="context-claim-binder-v1",
        c4_admission_profile="identity-tuple-v1",
        acceptance_conjunction="C1&C2&C3&C4",
    )
    return ProtocolSemanticContract(
        protocol_id=c.protocol_id,
        protocol_version=c.protocol_version,
        contract_id=c.contract_id,
        stage_3_3_context_semantics=c.stage_3_3_context_semantics,
        stage_3_4_visibility_semantics=c.stage_3_4_visibility_semantics,
        c1_crypto_validity_required=c.c1_crypto_validity_required,
        c2_public_key_profile=c.c2_public_key_profile,
        c3_binding_profile=c.c3_binding_profile,
        c4_admission_profile=c.c4_admission_profile,
        acceptance_conjunction=c.acceptance_conjunction,
        seal=c.compute_seal(),
    )


def install_default_protocol_catalog(
    catalog: Optional[ProtocolCatalog] = None,
) -> ProtocolCatalog:
    cat = catalog or ProtocolCatalog()
    cat.publish(default_sf_zk_v1_contract())
    return cat