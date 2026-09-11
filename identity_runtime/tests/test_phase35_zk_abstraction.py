# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""Stage 3.5 — cryptographic abstraction tests (mock scheme only)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.zk_abstraction.audit import CryptographicAuditLogger
from identity_runtime.zk_abstraction.binder import ContextClaimBinder
from identity_runtime.zk_abstraction.identity import IdentityTuple
from identity_runtime.zk_abstraction.registry import (
    CryptographicRegistry,
    OperationType,
    SchemeDescriptor,
    SchemeLifecycleState,
)
from identity_runtime.zk_abstraction.verifier import (
    IndependentVerifier,
    VerificationRequest,
)


def _id(
    scheme: str = "mock-scheme",
    scheme_ver: str = "1.0.0",
    proto_ver: str = "1.0.0",
) -> IdentityTuple:
    return IdentityTuple(
        protocol_id="sf-zk",
        protocol_version=proto_ver,
        scheme_id=scheme,
        scheme_version=scheme_ver,
        policy_version="1.0.0",
    )


def _registry_with_mock(
    state: SchemeLifecycleState = SchemeLifecycleState.SUPPORTED,
    deprecated_ops=frozenset(),
) -> CryptographicRegistry:
    reg = CryptographicRegistry()
    reg.register_scheme(
        SchemeDescriptor(
            scheme_id="mock-scheme",
            scheme_version="1.0.0",
            state=state,
            deprecated_allowed_ops=frozenset(deprecated_ops),
        )
    )
    return reg


def _public(**over) -> dict:
    base = {
        "context_id": "SF-2026-001",
        "revision": 1,
        "lifecycle_state": "ACTIVE",
        "incident_type": "earthquake",
    }
    base.update(over)
    return base


def _req(reg_state=SchemeLifecycleState.SUPPORTED, proof=None, public=None, **kw):
    reg = _registry_with_mock(reg_state)
    binder = ContextClaimBinder()
    pub = public if public is not None else _public()
    binding = binder.compute_target(
        context_id=kw.get("context_id", "SF-2026-001"),
        revision=kw.get("revision", 1),
        eligibility_proposition=kw.get(
            "claim",
            "eligible responder for specified context",
        ),
        public_conditions=pub,
    )
    if proof is None:
        proof = ("VALID:" + binding.public_conditions_fingerprint).encode("utf-8")
    v = IndependentVerifier(reg, binder=binder, audit=CryptographicAuditLogger())
    request = VerificationRequest(
        identity_tuple=_id(),
        proof_bytes=proof,
        verifier_visible_inputs=pub,
        context_id=kw.get("context_id", "SF-2026-001"),
        revision=kw.get("revision", 1),
        claim_proposition=kw.get("claim", "eligible responder for specified context"),
        required_public_keys=kw.get(
            "required", {"context_id", "revision", "lifecycle_state"}
        ),
    )
    return v, request, binding


class Phase35PositiveTests(unittest.TestCase):
    def test_happy_path(self):
        v, req, _ = _req()
        r = v.verify_proof(req)
        self.assertTrue(r.accepted)
        self.assertEqual(r.status_code, "OK")

    def test_binding_distinct_on_revision(self):
        b = ContextClaimBinder()
        t1 = b.compute_target(
            context_id="A", revision=1, eligibility_proposition="p", public_conditions={}
        )
        t2 = b.compute_target(
            context_id="A", revision=2, eligibility_proposition="p", public_conditions={}
        )
        self.assertNotEqual(t1, t2)

    def test_audit_has_no_witness(self):
        audit = CryptographicAuditLogger()
        v, req, _ = _req()
        v.audit = audit
        v.verify_proof(req)
        self.assertTrue(len(audit.entries) >= 1)
        blob = str(audit.entries)
        self.assertNotIn("private_witness", blob)


class Phase35NegativeMatrix(unittest.TestCase):
    def test_unsupported_scheme(self):
        reg = CryptographicRegistry()
        v = IndependentVerifier(reg)
        r = v.verify_proof(
            VerificationRequest(
                identity_tuple=_id(scheme="unknown"),
                proof_bytes=b"x",
                verifier_visible_inputs=_public(),
                context_id="SF-2026-001",
                revision=1,
                claim_proposition="p",
            )
        )
        self.assertFalse(r.accepted)
        self.assertEqual(r.status_code, "UNSUPPORTED_SCHEME")

    def test_disabled_scheme(self):
        v, req, _ = _req(SchemeLifecycleState.DISABLED)
        r = v.verify_proof(req)
        self.assertFalse(r.accepted)
        self.assertIn("DISABLED", r.status_code)

    def test_retired_scheme(self):
        v, req, _ = _req(SchemeLifecycleState.RETIRED)
        r = v.verify_proof(req)
        self.assertFalse(r.accepted)
        self.assertIn("RETIRED", r.status_code)

    def test_deprecated_disallowed(self):
        v, req, _ = _req(SchemeLifecycleState.DEPRECATED)
        r = v.verify_proof(req)
        self.assertFalse(r.accepted)
        self.assertEqual(r.status_code, "SCHEME_DEPRECATED_DISALLOWED")

    def test_deprecated_allowed_when_policy_permits(self):
        reg = _registry_with_mock(
            SchemeLifecycleState.DEPRECATED,
            deprecated_ops={OperationType.PROOF_VERIFICATION},
        )
        binder = ContextClaimBinder()
        pub = _public()
        binding = binder.compute_target(
            context_id="SF-2026-001",
            revision=1,
            eligibility_proposition="p",
            public_conditions=pub,
        )
        proof = ("VALID:" + binding.public_conditions_fingerprint).encode()
        v = IndependentVerifier(reg, binder=binder)
        r = v.verify_proof(
            VerificationRequest(
                identity_tuple=_id(),
                proof_bytes=proof,
                verifier_visible_inputs=pub,
                context_id="SF-2026-001",
                revision=1,
                claim_proposition="p",
            )
        )
        self.assertTrue(r.accepted)

    def test_unsupported_protocol_version(self):
        reg = _registry_with_mock()
        v = IndependentVerifier(reg)
        r = v.verify_proof(
            VerificationRequest(
                identity_tuple=_id(proto_ver="9.9.9"),
                proof_bytes=b"x",
                verifier_visible_inputs=_public(),
                context_id="SF-2026-001",
                revision=1,
                claim_proposition="p",
            )
        )
        self.assertFalse(r.accepted)
        self.assertEqual(r.status_code, "UNSUPPORTED_PROTOCOL")

    def test_unauthorized_downgrade(self):
        reg = _registry_with_mock()
        reg.register_scheme(
            SchemeDescriptor(
                scheme_id="mock-scheme",
                scheme_version="0.9.0",
                state=SchemeLifecycleState.SUPPORTED,
            )
        )
        reg.set_min_scheme_version("mock-scheme", "1.0.0")
        v = IndependentVerifier(reg)
        r = v.verify_proof(
            VerificationRequest(
                identity_tuple=_id(scheme_ver="0.9.0"),
                proof_bytes=b"x",
                verifier_visible_inputs=_public(),
                context_id="SF-2026-001",
                revision=1,
                claim_proposition="p",
            )
        )
        self.assertFalse(r.accepted)
        self.assertEqual(r.status_code, "SCHEME_DOWNGRADE")

    def test_malformed_proof(self):
        v, req, _ = _req(proof=b"")
        r = v.verify_proof(req)
        self.assertFalse(r.accepted)
        self.assertEqual(r.status_code, "MALFORMED_PROOF")

    def test_invalid_proof(self):
        v, req, _ = _req(proof=b"INVALID")
        r = v.verify_proof(req)
        self.assertFalse(r.accepted)
        self.assertEqual(r.status_code, "INVALID_PROOF")

    def test_wrong_context(self):
        pub = _public(context_id="OTHER")
        v, req, _ = _req(public=pub)
        r = v.verify_proof(req)
        self.assertFalse(r.accepted)
        self.assertEqual(r.status_code, "WRONG_CONTEXT")

    def test_wrong_revision(self):
        pub = _public(revision=99)
        v, req, _ = _req(public=pub)
        r = v.verify_proof(req)
        self.assertFalse(r.accepted)
        self.assertEqual(r.status_code, "WRONG_REVISION")

    def test_wrong_claim(self):
        pub = _public(eligibility_proposition="other claim")
        v, req, _ = _req(public=pub)
        r = v.verify_proof(req)
        self.assertFalse(r.accepted)
        self.assertEqual(r.status_code, "WRONG_CLAIM")

    def test_missing_required(self):
        pub = {"context_id": "SF-2026-001", "revision": 1}
        v, req, _ = _req(public=pub)
        r = v.verify_proof(req)
        self.assertFalse(r.accepted)
        self.assertEqual(r.status_code, "MISSING_CONDITION")

    def test_ambiguous(self):
        pub = _public(_ambiguous=True)
        v, req, _ = _req(public=pub)
        r = v.verify_proof(req)
        self.assertFalse(r.accepted)
        self.assertEqual(r.status_code, "AMBIGUOUS_CONDITION")

    def test_stale(self):
        pub = _public(_stale=True)
        v, req, _ = _req(public=pub)
        r = v.verify_proof(req)
        self.assertFalse(r.accepted)
        self.assertEqual(r.status_code, "STALE_CONDITION")

    def test_revoked_lifecycle(self):
        pub = _public(lifecycle_state="REVOKED")
        v, req, _ = _req(public=pub)
        r = v.verify_proof(req)
        self.assertFalse(r.accepted)
        self.assertEqual(r.status_code, "REVOKED_CONDITION")

    def test_superseded(self):
        pub = _public(lifecycle_state="SUPERSEDED")
        v, req, _ = _req(public=pub)
        r = v.verify_proof(req)
        self.assertFalse(r.accepted)
        self.assertEqual(r.status_code, "SUPERSEDED_CONDITION")

    def test_conflicted(self):
        pub = _public(_conflicted=True)
        v, req, _ = _req(public=pub)
        r = v.verify_proof(req)
        self.assertFalse(r.accepted)
        self.assertEqual(r.status_code, "CONFLICTED_CONDITION")

    def test_unverifiable(self):
        pub = _public(_unverifiable=True)
        v, req, _ = _req(public=pub)
        r = v.verify_proof(req)
        self.assertFalse(r.accepted)
        self.assertEqual(r.status_code, "UNVERIFIABLE_CONDITION")

    def test_outside_boundary_leak(self):
        pub = _public(casualty_lists=["x"])
        v, req, _ = _req(public=pub)
        r = v.verify_proof(req)
        self.assertFalse(r.accepted)
        self.assertEqual(r.status_code, "OUTSIDE_BOUNDARY_LEAK")

    def test_failure_does_not_authorize(self):
        v, req, _ = _req(proof=b"bad")
        r = v.verify_proof(req)
        self.assertFalse(r.accepted)
        self.assertFalse(getattr(r, "authorized", False))


class Phase35AuditGuard(unittest.TestCase):
    def test_audit_rejects_secret_keys(self):
        audit = CryptographicAuditLogger()
        with self.assertRaises(ValueError):
            audit.log_verification(
                context_id="c",
                revision=1,
                claim_id="c",
                identity_tuple=_id(),
                verification_outcome="OK",
                extra={"private_witness": "leak"},
            )


if __name__ == "__main__":
    unittest.main()