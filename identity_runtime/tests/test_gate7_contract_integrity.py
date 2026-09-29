# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""Gate 7 G7-CI — Contract integrity and seal binding tests (ADR-G7)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.zk_abstraction.c4_policy_wrapper import evaluate_c4
from identity_runtime.zk_abstraction.identity import IdentityTuple
from identity_runtime.zk_abstraction.protocol_catalog import (
    ProtocolCatalog,
    ProtocolSemanticContract,
    default_sf_zk_v1_contract,
    install_default_protocol_catalog,
    verify_contract_integrity,
)
from identity_runtime.zk_abstraction.registry import (
    CryptographicRegistry,
    install_default_mock_schemes,
)


def _id(**kw) -> IdentityTuple:
    base = dict(
        protocol_id="sf-zk",
        protocol_version="1.0.0",
        scheme_id="mock-scheme",
        scheme_version="1.0.0",
        policy_version="1.0.0",
    )
    base.update(kw)
    return IdentityTuple(**base)


class Gate7ContractIntegrityTests(unittest.TestCase):
    """Workstreams A–C / E — publication, immutability, runtime integrity."""

    def test_publish_valid_computed_seal_accepted(self):
        cat = ProtocolCatalog()
        c = default_sf_zk_v1_contract()
        published = cat.publish(c)
        self.assertEqual(published.seal, c.compute_seal())
        self.assertEqual(cat.require("sf-zk", "1.0.0").seal, published.seal)

    def test_publish_supplied_seal_matches_recomputed(self):
        cat = ProtocolCatalog()
        base = default_sf_zk_v1_contract()
        published = cat.publish(base)
        self.assertEqual(published.seal, base.seal)

    def test_publish_incorrect_supplied_seal_rejected(self):
        cat = ProtocolCatalog()
        base = default_sf_zk_v1_contract()
        bad = ProtocolSemanticContract(
            protocol_id=base.protocol_id,
            protocol_version=base.protocol_version,
            contract_id=base.contract_id,
            stage_3_3_context_semantics=base.stage_3_3_context_semantics,
            stage_3_4_visibility_semantics=base.stage_3_4_visibility_semantics,
            c1_crypto_validity_required=base.c1_crypto_validity_required,
            c2_public_key_profile=base.c2_public_key_profile,
            c3_binding_profile=base.c3_binding_profile,
            c4_admission_profile=base.c4_admission_profile,
            acceptance_conjunction=base.acceptance_conjunction,
            seal="0" * 32,
        )
        with self.assertRaises(ValueError) as cm:
            cat.publish(bad)
        self.assertIn("PROTOCOL_CONTRACT_SEAL_MISMATCH", str(cm.exception))

    def test_modified_content_with_copied_seal_rejected(self):
        cat = install_default_protocol_catalog()
        base = default_sf_zk_v1_contract()
        mutated = ProtocolSemanticContract(
            protocol_id=base.protocol_id,
            protocol_version=base.protocol_version,
            contract_id=base.contract_id,
            stage_3_3_context_semantics="stage-3.3-context-v2-TAMPERED",
            stage_3_4_visibility_semantics=base.stage_3_4_visibility_semantics,
            c1_crypto_validity_required=base.c1_crypto_validity_required,
            c2_public_key_profile=base.c2_public_key_profile,
            c3_binding_profile=base.c3_binding_profile,
            c4_admission_profile=base.c4_admission_profile,
            acceptance_conjunction=base.acceptance_conjunction,
            seal=base.seal,
        )
        with self.assertRaises(ValueError) as cm:
            cat.publish(mutated)
        self.assertIn("PROTOCOL_CONTRACT_SEAL_MISMATCH", str(cm.exception))

    def test_modified_content_new_seal_same_identity_immutable(self):
        cat = install_default_protocol_catalog()
        base = default_sf_zk_v1_contract()
        mutated = ProtocolSemanticContract(
            protocol_id=base.protocol_id,
            protocol_version=base.protocol_version,
            contract_id=base.contract_id,
            stage_3_3_context_semantics="stage-3.3-context-v2-CHANGED",
            stage_3_4_visibility_semantics=base.stage_3_4_visibility_semantics,
            c1_crypto_validity_required=base.c1_crypto_validity_required,
            c2_public_key_profile=base.c2_public_key_profile,
            c3_binding_profile=base.c3_binding_profile,
            c4_admission_profile=base.c4_admission_profile,
            acceptance_conjunction=base.acceptance_conjunction,
        )
        with self.assertRaises(ValueError) as cm:
            cat.publish(mutated)
        self.assertIn("PROTOCOL_CONTRACT_IMMUTABLE", str(cm.exception))

    def test_identical_republish_idempotent(self):
        cat = install_default_protocol_catalog()
        again = default_sf_zk_v1_contract()
        out = cat.publish(again)
        self.assertEqual(out.seal, again.seal)
        self.assertEqual(cat.require("sf-zk", "1.0.0").seal, again.seal)

    def test_runtime_require_verifies_intact_contract(self):
        cat = install_default_protocol_catalog()
        c = cat.require("sf-zk", "1.0.0")
        self.assertEqual(c.seal, c.compute_seal())
        verify_contract_integrity(c)

    def test_runtime_require_rejects_tampered_content(self):
        cat = install_default_protocol_catalog()
        base = cat.require("sf-zk", "1.0.0")
        tampered = ProtocolSemanticContract(
            protocol_id=base.protocol_id,
            protocol_version=base.protocol_version,
            contract_id=base.contract_id,
            stage_3_3_context_semantics="TAMPERED-CONTENT",
            stage_3_4_visibility_semantics=base.stage_3_4_visibility_semantics,
            c1_crypto_validity_required=base.c1_crypto_validity_required,
            c2_public_key_profile=base.c2_public_key_profile,
            c3_binding_profile=base.c3_binding_profile,
            c4_admission_profile=base.c4_admission_profile,
            acceptance_conjunction=base.acceptance_conjunction,
            seal=base.seal,
        )
        cat._entries[("sf-zk", "1.0.0")] = tampered
        with self.assertRaises(ValueError) as cm:
            cat.require("sf-zk", "1.0.0")
        self.assertIn("PROTOCOL_CONTRACT_SEAL_MISMATCH", str(cm.exception))

    def test_runtime_require_rejects_tampered_seal(self):
        cat = install_default_protocol_catalog()
        base = cat.require("sf-zk", "1.0.0")
        bad_seal = ProtocolSemanticContract(
            protocol_id=base.protocol_id,
            protocol_version=base.protocol_version,
            contract_id=base.contract_id,
            stage_3_3_context_semantics=base.stage_3_3_context_semantics,
            stage_3_4_visibility_semantics=base.stage_3_4_visibility_semantics,
            c1_crypto_validity_required=base.c1_crypto_validity_required,
            c2_public_key_profile=base.c2_public_key_profile,
            c3_binding_profile=base.c3_binding_profile,
            c4_admission_profile=base.c4_admission_profile,
            acceptance_conjunction=base.acceptance_conjunction,
            seal="deadbeef" * 4,
        )
        cat._entries[("sf-zk", "1.0.0")] = bad_seal
        with self.assertRaises(ValueError) as cm:
            cat.require("sf-zk", "1.0.0")
        self.assertIn("PROTOCOL_CONTRACT_SEAL_MISMATCH", str(cm.exception))

    def test_c4_fail_closed_on_tampered_catalog_contract(self):
        cat = install_default_protocol_catalog()
        base = cat.require("sf-zk", "1.0.0")
        tampered = ProtocolSemanticContract(
            protocol_id=base.protocol_id,
            protocol_version=base.protocol_version,
            contract_id=base.contract_id,
            stage_3_3_context_semantics="TAMPERED",
            stage_3_4_visibility_semantics=base.stage_3_4_visibility_semantics,
            c1_crypto_validity_required=True,
            c2_public_key_profile=base.c2_public_key_profile,
            c3_binding_profile=base.c3_binding_profile,
            c4_admission_profile=base.c4_admission_profile,
            acceptance_conjunction=base.acceptance_conjunction,
            seal=base.seal,
        )
        cat._entries[("sf-zk", "1.0.0")] = tampered
        reg = CryptographicRegistry()
        install_default_mock_schemes(reg)
        ev = evaluate_c4(reg, _id(), protocol_catalog=cat)
        self.assertFalse(ev.allowed)
        self.assertEqual(ev.status_code, "PROTOCOL_CONTRACT_SEAL_MISMATCH")


if __name__ == "__main__":
    unittest.main()