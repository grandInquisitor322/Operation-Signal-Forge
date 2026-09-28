# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""Gate 7 — Protocol versioning & interoperability test suite."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.zk_abstraction.bn254 import G1_GENERATOR, encode_g1_proof
from identity_runtime.zk_abstraction.binder import ContextClaimBinder
from identity_runtime.zk_abstraction.c4_policy_wrapper import evaluate_c4
from identity_runtime.zk_abstraction.identity import IdentityTuple
from identity_runtime.zk_abstraction.protocol_catalog import (
    ProtocolCatalog,
    ProtocolSemanticContract,
    default_sf_zk_v1_contract,
    install_default_protocol_catalog,
)
from identity_runtime.zk_abstraction.registry import (
    CryptographicRegistry,
    OperationType,
    install_default_mock_schemes,
)
from identity_runtime.zk_abstraction.verifier import IndependentVerifier, VerificationRequest


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


def _pub():
    return {
        "context_id": "SF-2026-001",
        "revision": "1",
        "lifecycle_state": "ACTIVE",
        "incident_type": "earthquake",
    }


def _claim():
    return "eligible responder for specified context"


def _valid_proof(pub=None, claim=None):
    pub = pub or _pub()
    claim = claim or _claim()
    fp = ContextClaimBinder().compute_target(
        context_id="SF-2026-001",
        revision=1,
        eligibility_proposition=claim,
        public_conditions=pub,
    ).public_conditions_fingerprint
    return encode_g1_proof(
        G1_GENERATOR[0], G1_GENERATOR[1], ("VALID:" + fp).encode()
    )


def _reg():
    return install_default_mock_schemes(CryptographicRegistry())


class Gate7CatalogTests(unittest.TestCase):
    def test_publish_and_resolve_one_contract(self):
        cat = install_default_protocol_catalog()
        c = cat.require("sf-zk", "1.0.0")
        self.assertEqual(c.protocol_id, "sf-zk")
        self.assertEqual(c.protocol_version, "1.0.0")
        self.assertTrue(c.seal)
        self.assertTrue(c.c1_crypto_validity_required)
        self.assertEqual(c.acceptance_conjunction, "C1&C2&C3&C4")

    def test_immutable_republish_different_semantics_rejected(self):
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

    def test_new_protocol_version_allowed_for_new_semantics(self):
        cat = install_default_protocol_catalog()
        base = default_sf_zk_v1_contract()
        v2 = ProtocolSemanticContract(
            protocol_id="sf-zk",
            protocol_version="1.1.0",
            contract_id="sf-zk-1.1.0",
            stage_3_3_context_semantics="stage-3.3-context-v2",
            stage_3_4_visibility_semantics=base.stage_3_4_visibility_semantics,
            c1_crypto_validity_required=True,
            c2_public_key_profile=base.c2_public_key_profile,
            c3_binding_profile=base.c3_binding_profile,
            c4_admission_profile=base.c4_admission_profile,
            acceptance_conjunction="C1&C2&C3&C4",
        )
        published = cat.publish(v2)
        self.assertEqual(cat.require("sf-zk", "1.1.0").seal, published.seal)
        self.assertEqual(cat.require("sf-zk", "1.0.0").seal, base.seal)


class Gate7IdentityHardeningTests(unittest.TestCase):
    def test_registry_rejects_missing_protocol_version(self):
        reg = _reg()
        ev = reg.validate_operation(
            "mock-scheme",
            "1.0.0",
            OperationType.PROOF_VERIFICATION,
            protocol_version=None,
            policy_version="1.0.0",
        )
        self.assertFalse(ev.allowed)
        self.assertEqual(ev.status_code, "MISSING_PROTOCOL_VERSION")

    def test_registry_rejects_missing_policy_version(self):
        reg = _reg()
        ev = reg.validate_operation(
            "mock-scheme",
            "1.0.0",
            OperationType.PROOF_VERIFICATION,
            protocol_version="1.0.0",
            policy_version=None,
        )
        self.assertFalse(ev.allowed)
        self.assertEqual(ev.status_code, "MISSING_POLICY_VERSION")

    def test_registry_rejects_empty_protocol_version(self):
        reg = _reg()
        ev = reg.validate_operation(
            "mock-scheme",
            "1.0.0",
            OperationType.PROOF_VERIFICATION,
            protocol_version="",
            policy_version="1.0.0",
        )
        self.assertFalse(ev.allowed)

    def test_c4_missing_protocol_version(self):
        ev = evaluate_c4(_reg(), _id(protocol_version=""))
        self.assertFalse(ev.allowed)

    def test_c4_unsupported_protocol_contract(self):
        ev = evaluate_c4(_reg(), _id(protocol_version="9.9.9"))
        self.assertFalse(ev.allowed)
        self.assertIn("UNSUPPORTED", ev.status_code)


class Gate7InteropVerifierTests(unittest.TestCase):
    def test_positive_path_same_contract(self):
        reg = _reg()
        pub = _pub()
        claim = _claim()
        r = IndependentVerifier(reg).verify_proof(
            VerificationRequest(
                identity_tuple=_id(),
                proof_bytes=_valid_proof(pub, claim),
                verifier_visible_inputs=pub,
                context_id="SF-2026-001",
                revision=1,
                claim_proposition=claim,
            )
        )
        self.assertTrue(r.accepted, msg=f"{r.status_code}/{r.reason}")

    def test_unsupported_protocol_version_fail_closed(self):
        reg = _reg()
        pub = _pub()
        claim = _claim()
        r = IndependentVerifier(reg).verify_proof(
            VerificationRequest(
                identity_tuple=_id(protocol_version="9.9.9"),
                proof_bytes=_valid_proof(pub, claim),
                verifier_visible_inputs=pub,
                context_id="SF-2026-001",
                revision=1,
                claim_proposition=claim,
            )
        )
        self.assertFalse(r.accepted)
        self.assertFalse(r.verified_eligibility_claim)

    def test_scheme_downgrade_fail_closed(self):
        reg = _reg()
        reg.set_min_scheme_version("mock-scheme", "2.0.0")
        pub = _pub()
        claim = _claim()
        r = IndependentVerifier(reg).verify_proof(
            VerificationRequest(
                identity_tuple=_id(scheme_version="1.0.0"),
                proof_bytes=_valid_proof(pub, claim),
                verifier_visible_inputs=pub,
                context_id="SF-2026-001",
                revision=1,
                claim_proposition=claim,
            )
        )
        self.assertFalse(r.accepted)

    def test_gate6_substitution_same_protocol_contract(self):
        from identity_runtime.zk_abstraction.adapters.mock_digest_v2 import (
            PREFIX as M2_PREFIX,
            _view_digest,
        )
        from identity_runtime.zk_abstraction.scheme_types import BoundStatementTarget

        reg = _reg()
        pub = _pub()
        claim = _claim()
        fp = ContextClaimBinder().compute_target(
            context_id="SF-2026-001",
            revision=1,
            eligibility_proposition=claim,
            public_conditions=pub,
        ).public_conditions_fingerprint
        bound = BoundStatementTarget(
            statement_id="t",
            scheme_id="mock-digest",
            scheme_version="1.0.0",
            materials_ref="mock-digest-materials",
            public_input_view={k: str(v) for k, v in pub.items()},
            relation_hint=fp,
        )
        proof = M2_PREFIX + _view_digest(bound).encode("utf-8")
        r = IndependentVerifier(reg).verify_proof(
            VerificationRequest(
                identity_tuple=_id(scheme_id="mock-digest", scheme_version="1.0.0"),
                proof_bytes=proof,
                verifier_visible_inputs=pub,
                context_id="SF-2026-001",
                revision=1,
                claim_proposition=claim,
            )
        )
        self.assertTrue(r.accepted, msg=f"{r.status_code}/{r.reason}")
        self.assertEqual(r.identity_tuple.protocol_id, "sf-zk")
        self.assertEqual(r.identity_tuple.protocol_version, "1.0.0")

    def test_policy_version_not_in_public_inputs(self):
        from identity_runtime.zk_abstraction.verifier import ALLOWED_PUBLIC_KEYS

        self.assertNotIn("policy_version", ALLOWED_PUBLIC_KEYS)
        self.assertNotIn("protocol_id", ALLOWED_PUBLIC_KEYS)
        self.assertNotIn("protocol_version", ALLOWED_PUBLIC_KEYS)

    def test_c4_returns_bound_contract_on_success(self):
        ev = evaluate_c4(_reg(), _id())
        self.assertTrue(ev.allowed)
        self.assertIsNotNone(ev.contract)
        self.assertEqual(ev.contract.protocol_version, "1.0.0")
        self.assertTrue(ev.contract.seal)


class Gate7CompatibleVsIncompatible(unittest.TestCase):
    def test_compatible_republish_same_seal_ok(self):
        cat = install_default_protocol_catalog()
        again = default_sf_zk_v1_contract()
        cat.publish(again)
        self.assertEqual(cat.require("sf-zk", "1.0.0").seal, again.seal)

    def test_incompatible_under_old_version_rejected_at_catalog(self):
        cat = ProtocolCatalog()
        v1 = default_sf_zk_v1_contract()
        cat.publish(v1)
        bad = ProtocolSemanticContract(
            protocol_id="sf-zk",
            protocol_version="1.0.0",
            contract_id="sf-zk-1.0.0-baseline",
            stage_3_3_context_semantics="DIFFERENT",
            stage_3_4_visibility_semantics=v1.stage_3_4_visibility_semantics,
            c1_crypto_validity_required=True,
            c2_public_key_profile=v1.c2_public_key_profile,
            c3_binding_profile=v1.c3_binding_profile,
            c4_admission_profile=v1.c4_admission_profile,
            acceptance_conjunction="C1&C2&C3&C4",
        )
        with self.assertRaises(ValueError):
            cat.publish(bad)


if __name__ == "__main__":
    unittest.main()