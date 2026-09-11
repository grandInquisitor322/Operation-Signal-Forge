# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""WP7-CAND-01R1 Workstream B — SF-3.5-VER-5 result taxonomy tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.zk_abstraction.acceptance import (
    ConditionId,
    ConditionOutcome,
    ConditionResult,
    evaluate_acceptance,
)
from identity_runtime.zk_abstraction.result_taxonomy import (
    FORBIDDEN_OUTCOME,
    SubjectIneligibilityStatus,
    VerificationOutcomeClass,
    classify_acceptance,
    classify_from_status_reason,
)
from identity_runtime.zk_abstraction.identity import IdentityTuple
from identity_runtime.zk_abstraction.registry import (
    CryptographicRegistry,
    SchemeDescriptor,
    SchemeLifecycleState,
)
from identity_runtime.zk_abstraction.binder import ContextClaimBinder
from identity_runtime.zk_abstraction.verifier import (
    IndependentVerifier,
    VerificationRequest,
)


def _all_pass():
    return {
        cid: ConditionResult(cid, ConditionOutcome.PASS, "ok")
        for cid in (ConditionId.C1, ConditionId.C2, ConditionId.C3, ConditionId.C4)
    }


def _id():
    return IdentityTuple(
        protocol_id="sf-zk",
        protocol_version="1.0.0",
        scheme_id="mock-scheme",
        scheme_version="1.0.0",
        policy_version="1.0.0",
    )


def _reg():
    reg = CryptographicRegistry()
    reg.register_scheme(
        SchemeDescriptor(
            scheme_id="mock-scheme",
            scheme_version="1.0.0",
            state=SchemeLifecycleState.SUPPORTED,
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


class WorkstreamBTaxonomyTests(unittest.TestCase):
    def test_verified_eligibility(self):
        t = classify_acceptance(evaluate_acceptance(_all_pass()))
        self.assertEqual(t.outcome, VerificationOutcomeClass.VERIFIED_ELIGIBILITY)
        self.assertTrue(t.verified_eligibility_claim)
        self.assertFalse(t.authorization_permitted)
        self.assertFalse(t.asserts_subject_ineligible)

    def test_missing_proof_not_ineligible(self):
        m = _all_pass()
        m[ConditionId.C1] = ConditionResult(
            ConditionId.C1, ConditionOutcome.MALFORMED, "empty_proof"
        )
        t = classify_acceptance(evaluate_acceptance(m))
        self.assertEqual(t.outcome, VerificationOutcomeClass.MALFORMED)
        self.assertEqual(
            t.subject_ineligibility, SubjectIneligibilityStatus.NOT_ASSERTED
        )

    def test_invalid_proof_claim_not_satisfied(self):
        m = _all_pass()
        m[ConditionId.C1] = ConditionResult(
            ConditionId.C1, ConditionOutcome.FAIL, "scheme_proof_check_failed"
        )
        t = classify_acceptance(evaluate_acceptance(m))
        self.assertEqual(t.outcome, VerificationOutcomeClass.CLAIM_NOT_SATISFIED)
        self.assertFalse(t.asserts_subject_ineligible)

    def test_malformed(self):
        m = _all_pass()
        m[ConditionId.C2] = ConditionResult(
            ConditionId.C2, ConditionOutcome.MALFORMED, "malformed"
        )
        t = classify_acceptance(evaluate_acceptance(m))
        self.assertEqual(t.outcome, VerificationOutcomeClass.MALFORMED)

    def test_unsupported(self):
        m = _all_pass()
        m[ConditionId.C4] = ConditionResult(
            ConditionId.C4, ConditionOutcome.UNSUPPORTED, "unregistered_scheme"
        )
        t = classify_acceptance(evaluate_acceptance(m))
        self.assertEqual(t.outcome, VerificationOutcomeClass.UNSUPPORTED)

    def test_ambiguous(self):
        m = _all_pass()
        m[ConditionId.C2] = ConditionResult(
            ConditionId.C2, ConditionOutcome.AMBIGUOUS, "dup"
        )
        t = classify_acceptance(evaluate_acceptance(m))
        self.assertEqual(t.outcome, VerificationOutcomeClass.AMBIGUOUS)

    def test_unverifiable(self):
        m = _all_pass()
        m[ConditionId.C3] = ConditionResult(
            ConditionId.C3, ConditionOutcome.UNVERIFIABLE, "bad"
        )
        t = classify_acceptance(evaluate_acceptance(m))
        self.assertEqual(t.outcome, VerificationOutcomeClass.UNVERIFIABLE)

    def test_failed_proof_not_asserted_ineligible(self):
        m = _all_pass()
        m[ConditionId.C1] = ConditionResult(
            ConditionId.C1, ConditionOutcome.FAIL, "bad"
        )
        t = classify_acceptance(evaluate_acceptance(m))
        self.assertNotEqual(t.outcome.value, FORBIDDEN_OUTCOME)
        self.assertEqual(
            t.subject_ineligibility, SubjectIneligibilityStatus.NOT_ASSERTED
        )

    def test_outcomes_distinct(self):
        classes = {
            VerificationOutcomeClass.VERIFIED_ELIGIBILITY,
            VerificationOutcomeClass.CLAIM_NOT_SATISFIED,
            VerificationOutcomeClass.NOT_ESTABLISHED,
        }
        self.assertEqual(len(classes), 3)
        self.assertNotIn(FORBIDDEN_OUTCOME, [c.value for c in VerificationOutcomeClass])

    def test_verifier_attaches_taxonomy_success(self):
        binder = ContextClaimBinder()
        pub = _public()
        binding = binder.compute_target(
            context_id="SF-2026-001",
            revision=1,
            eligibility_proposition="eligible responder for specified context",
            public_conditions=pub,
        )
        proof = ("VALID:" + binding.public_conditions_fingerprint).encode()
        v = IndependentVerifier(_reg(), binder=binder)
        r = v.verify_proof(
            VerificationRequest(
                identity_tuple=_id(),
                proof_bytes=proof,
                verifier_visible_inputs=pub,
                context_id="SF-2026-001",
                revision=1,
                claim_proposition="eligible responder for specified context",
            )
        )
        self.assertTrue(r.accepted)
        self.assertIsNotNone(r.taxonomy)
        self.assertEqual(
            r.taxonomy.outcome, VerificationOutcomeClass.VERIFIED_ELIGIBILITY
        )
        self.assertFalse(r.authorization_permitted)

    def test_verifier_invalid_proof_taxonomy(self):
        v = IndependentVerifier(_reg())
        r = v.verify_proof(
            VerificationRequest(
                identity_tuple=_id(),
                proof_bytes=b"INVALID",
                verifier_visible_inputs=_public(),
                context_id="SF-2026-001",
                revision=1,
                claim_proposition="p",
            )
        )
        self.assertFalse(r.accepted)
        self.assertIsNotNone(r.taxonomy)
        self.assertEqual(
            r.taxonomy.subject_ineligibility,
            SubjectIneligibilityStatus.NOT_ASSERTED,
        )
        self.assertFalse(r.taxonomy.asserts_subject_ineligible)

    def test_structural_fallback_taxonomy(self):
        t = classify_from_status_reason(
            accepted=False,
            status_code="STRUCTURAL_MISSING_CONDITION",
            reason="missing_condition:C1",
        )
        self.assertEqual(t.outcome, VerificationOutcomeClass.UNVERIFIABLE)
        self.assertFalse(t.asserts_subject_ineligible)


if __name__ == "__main__":
    unittest.main()