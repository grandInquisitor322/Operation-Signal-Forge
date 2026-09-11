# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""WP7-CAND-01R1 Workstream C — C4 protocol/scheme/policy wrapper tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.zk_abstraction.acceptance import ConditionOutcome
from identity_runtime.zk_abstraction.binder import ContextClaimBinder
from identity_runtime.zk_abstraction.c4_policy_wrapper import (
    VerifierPolicyContext,
    evaluate_c4,
)
from identity_runtime.zk_abstraction.identity import IdentityTuple
from identity_runtime.zk_abstraction.registry import (
    CryptographicRegistry,
    SchemeDescriptor,
    SchemeLifecycleState,
)
from identity_runtime.zk_abstraction.result_taxonomy import VerificationOutcomeClass
from identity_runtime.zk_abstraction.verifier import (
    IndependentVerifier,
    VerificationRequest,
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


def _reg(state=SchemeLifecycleState.SUPPORTED, version="1.0.0"):
    reg = CryptographicRegistry()
    reg.register_scheme(
        SchemeDescriptor(
            scheme_id="mock-scheme",
            scheme_version=version,
            state=state,
        )
    )
    return reg


def _public():
    return {
        "context_id": "SF-2026-001",
        "revision": 1,
        "lifecycle_state": "ACTIVE",
        "incident_type": "earthquake",
    }


def _valid_proof(pub, claim="eligible responder for specified context"):
    binder = ContextClaimBinder()
    binding = binder.compute_target(
        context_id="SF-2026-001",
        revision=1,
        eligibility_proposition=claim,
        public_conditions=pub,
    )
    return ("VALID:" + binding.public_conditions_fingerprint).encode()


class WorkstreamCC4Tests(unittest.TestCase):
    def test_supported_c4_pass(self):
        ev = evaluate_c4(_reg(), _id())
        self.assertTrue(ev.allowed)
        self.assertEqual(ev.outcome, ConditionOutcome.PASS)

    def test_disabled_scheme(self):
        ev = evaluate_c4(_reg(SchemeLifecycleState.DISABLED), _id())
        self.assertFalse(ev.allowed)

    def test_retired_scheme(self):
        ev = evaluate_c4(_reg(SchemeLifecycleState.RETIRED), _id())
        self.assertFalse(ev.allowed)

    def test_unsupported_protocol_version(self):
        ev = evaluate_c4(_reg(), _id(protocol_version="9.9.9"))
        self.assertFalse(ev.allowed)

    def test_unauthorized_downgrade(self):
        reg = _reg(version="2.0.0")
        reg.register_scheme(
            SchemeDescriptor(
                scheme_id="mock-scheme",
                scheme_version="1.0.0",
                state=SchemeLifecycleState.SUPPORTED,
            )
        )
        reg.set_min_scheme_version("mock-scheme", "2.0.0")
        ev = evaluate_c4(reg, _id(scheme_version="1.0.0"))
        self.assertFalse(ev.allowed)
        self.assertIn("downgrade", ev.reason)

    def test_policy_mismatch(self):
        ctx = VerifierPolicyContext(active_policy_version="2.0.0")
        ev = evaluate_c4(_reg(), _id(policy_version="1.0.0"), policy_context=ctx)
        self.assertFalse(ev.allowed)
        self.assertIn("policy_mismatch", ev.reason)

    def test_missing_scheme_version(self):
        ev = evaluate_c4(_reg(), _id(scheme_version=""))
        self.assertFalse(ev.allowed)
        self.assertEqual(ev.outcome, ConditionOutcome.MALFORMED)

    def test_ambiguous_c4(self):
        ev = evaluate_c4(_reg(), _id(protocol_id="__ambiguous__"))
        self.assertFalse(ev.allowed)
        self.assertEqual(ev.outcome, ConditionOutcome.AMBIGUOUS)

    def test_malformed_missing_protocol(self):
        ev = evaluate_c4(_reg(), _id(protocol_id=""))
        self.assertFalse(ev.allowed)
        self.assertEqual(ev.outcome, ConditionOutcome.MALFORMED)

    def test_valid_proof_but_c4_fails_no_verified(self):
        reg = _reg(SchemeLifecycleState.DISABLED)
        pub = _public()
        v = IndependentVerifier(reg)
        r = v.verify_proof(
            VerificationRequest(
                identity_tuple=_id(),
                proof_bytes=_valid_proof(pub),
                verifier_visible_inputs=pub,
                context_id="SF-2026-001",
                revision=1,
                claim_proposition="eligible responder for specified context",
            )
        )
        self.assertFalse(r.accepted)
        self.assertFalse(r.verified_eligibility_claim)
        if r.taxonomy is not None:
            self.assertNotEqual(
                r.taxonomy.outcome, VerificationOutcomeClass.VERIFIED_ELIGIBILITY
            )


if __name__ == "__main__":
    unittest.main()