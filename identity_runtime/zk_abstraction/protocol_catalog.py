# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""Gate 7 — Protocol semantic contract catalog (SF-3.5-PROTO).

Maps (protocol_id, protocol_version) → immutable ProtocolSemanticContract.
Runtime selects and evaluates; does not redefine the contract.

G7-CI (ADR-G7-Contract-Integrity-and-Seal-Binding):
  - publish() always recomputes seal; supplied seal must match
  - identity immutability is content-based (via verified seals)
  - require() verifies integrity before returning a contract
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
        """Authoritative content-derived seal. The seal field is excluded."""
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

    def with_verified_seal(self) -> "ProtocolSemanticContract":
        """Return a copy whose seal is the independently computed content seal."""
        computed = self.compute_seal()
        return ProtocolSemanticContract(
            protocol_id=self.protocol_id,
            protocol_version=self.protocol_version,
            contract_id=self.contract_id,
            stage_3_3_context_semantics=self.stage_3_3_context_semantics,
            stage_3_4_visibility_semantics=self.stage_3_4_visibility_semantics,
            c1_crypto_validity_required=self.c1_crypto_validity_required,
            c2_public_key_profile=self.c2_public_key_profile,
            c3_binding_profile=self.c3_binding_profile,
            c4_admission_profile=self.c4_admission_profile,
            acceptance_conjunction=self.acceptance_conjunction,
            seal=computed,
        )


def verify_contract_integrity(contract: ProtocolSemanticContract) -> ProtocolSemanticContract:
    """Fail closed if stored seal does not match independently recomputed seal."""
    computed = contract.compute_seal()
    if not contract.seal or contract.seal != computed:
        raise ValueError(
            f"PROTOCOL_CONTRACT_SEAL_MISMATCH:"
            f"{contract.protocol_id}@{contract.protocol_version}:"
            f"stored={contract.seal}:computed={computed}"
        )
    return contract


@dataclass
class ProtocolCatalog:
    """Governed catalog: published contracts are immutable under their version key."""

    _entries: Dict[Tuple[str, str], ProtocolSemanticContract] = field(default_factory=dict)

    def publish(self, contract: ProtocolSemanticContract) -> ProtocolSemanticContract:
        """Publish or re-assert a contract with verified content/seal binding.

        - Always recomputes seal via compute_seal() (authoritative).
        - Non-empty caller seal must match the recomputed seal or publication fails.
        - Same (protocol_id, protocol_version) + different content → PROTOCOL_CONTRACT_IMMUTABLE.
        - Same identity + identical content → idempotent (returns existing).
        """
        key = (contract.protocol_id, contract.protocol_version)
        computed = contract.compute_seal()
        if contract.seal and contract.seal != computed:
            raise ValueError(
                f"PROTOCOL_CONTRACT_SEAL_MISMATCH:{key[0]}@{key[1]}:"
                f"supplied={contract.seal}:computed={computed}"
            )
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
            seal=computed,
        )

        existing = self._entries.get(key)
        if existing is not None:
            existing_computed lim = existing.compute_seal()
            if not existing.seal or existing.seal != existing_computed:
                raise ValueError(
                    f"PROTOCOL_CONTRACT_SEAL_MISMATCH:{key[0]}@{key[1]}:"
                    f"stored={existing.seal}:computed={existing_computed}"
                )
            if existing_computed != computed:
                raise ValueError(
                    f"PROTOCOL_CONTRACT_IMMUTABLE:{key[0]}@{key[1]}:"
                    f"existing_seal={existing.seal}:new_seal={computed}"
                )
            return existing

        self._entries[key] = sealed
        return sealed

    def resolve(
        self, protocol_id: str, protocol_version: str
    ) -> Optional[ProtocolSemanticContract]:
        """Lookup only — does not establish integrity. Prefer require() for trust."""
        return self._entries.get((protocol_id, protocol_version))

    def require(
        self, protocol_id: str, protocol_version: str
    ) -> ProtocolSemanticContract:
        """Resolve and verify content/seal integrity before returning."""
        c = self.resolve(protocol_id, protocol_version)
        if c is None:
            raise KeyError(
                f"UNSUPPORTED_PROTOCOL_CONTRACT:{protocol_id}@{protocol_version}"
            )
        return verify_contract_integrity(c)

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
    return c.with_verified_seal()


def install_default_protocol_catalog(
    catalog: Optional[ProtocolCatalog] = None,
) -> ProtocolCatalog:
    cat = catalog or ProtocolCatalog()
    cat.publish(default_sf_zk_v1_contract())
    return cat