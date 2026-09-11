# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""WP7-CAND-01R1 Workstream A tests (+ F-1..F-5)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import MappingProxyType

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.zk_abstraction.acceptance import (
    AcceptanceControlFlowError,
    AcceptanceDecision,
    ConditionId,
    ConditionOutcome,
    ConditionResult,
    FAILURE_PRECEDENCE,
    evaluate_acceptance,
)


def _all_pass() -> dict:
    return {
        cid: ConditionResult(cid, ConditionOutcome.PASS, "ok")
        for cid in (
            ConditionId.C1,
            ConditionId.C2,
            ConditionId.C3,
            ConditionId.C4,
        )
    }


class WorkstreamAAcceptanceTests(unittest.TestCase):
    def test_all_pass_verified_eligibility(self):
        r = evaluate_acceptance(_all_pass())
        self.assertEqual(r.decision, AcceptanceDecision.VERIFIED_ELIGIBILITY)
        self.assertTrue(r.verified_eligibility_claim)
        self.assertFalse(r.authorization_permitted)
        self.assertEqual(r.status_code, "OK")
        self.assertIsNone(r.primary_failure)

    def test_f1_condition_results_immutable(self):
        r = evaluate_acceptance(_all_pass())
        self.assertIsInstance(r.condition_results, MappingProxyType)
        with self.assertRaises(TypeError):
            r.condition_results[ConditionId.C1] = ConditionResult(  # type: ignore[index]
                ConditionId.C1, ConditionOutcome.FAIL, "x"
            )

    def test_c1_fail(self):
        m = _all_pass()
        m[ConditionId.C1] = ConditionResult(
            ConditionId.C1, ConditionOutcome.FAIL, "bad_proof"
        )
        r = evaluate_acceptance(m)
        self.assertEqual(r.decision, AcceptanceDecision.CLAIM_NOT_SATISFIED)
        self.assertFalse(r.verified_eligibility_claim)
        self.assertFalse(r.authorization_permitted)
        self.assertEqual(r.primary_failure, ConditionId.C1)

    def test_c2_fail(self):
        m = _all_pass()
        m[ConditionId.C2] = ConditionResult(
            ConditionId.C2, ConditionOutcome.FAIL, "missing_field"
        )
        r = evaluate_acceptance(m)
        self.assertEqual(r.decision, AcceptanceDecision.CLAIM_NOT_SATISFIED)
        self.assertEqual(r.primary_failure, ConditionId.C2)

    def test_c3_fail(self):
        m = _all_pass()
        m[ConditionId.C3] = ConditionResult(
            ConditionId.C3, ConditionOutcome.FAIL, "wrong_context"
        )
        r = evaluate_acceptance(m)
        self.assertEqual(r.decision, AcceptanceDecision.CLAIM_NOT_SATISFIED)
        self.assertEqual(r.primary_failure, ConditionId.C3)

    def test_c4_fail(self):
        m = _all_pass()
        m[ConditionId.C4] = ConditionResult(
            ConditionId.C4, ConditionOutcome.FAIL, "scheme_disabled"
        )
        r = evaluate_acceptance(m)
        self.assertEqual(r.decision, AcceptanceDecision.CLAIM_NOT_SATISFIED)
        self.assertEqual(r.primary_failure, ConditionId.C4)

    def test_f2_precedence_c4_before_c1(self):
        m = _all_pass()
        m[ConditionId.C4] = ConditionResult(
            ConditionId.C4, ConditionOutcome.UNSUPPORTED, "unregistered_scheme"
        )
        m[ConditionId.C1] = ConditionResult(
            ConditionId.C1, ConditionOutcome.FAIL, "scheme_proof_check_failed"
        )
        r = evaluate_acceptance(m)
        self.assertEqual(r.primary_failure, ConditionId.C4)
        self.assertEqual(FAILURE_PRECEDENCE[0], ConditionId.C4)

    def test_ambiguous(self):
        m = _all_pass()
        m[ConditionId.C2] = ConditionResult(
            ConditionId.C2, ConditionOutcome.AMBIGUOUS, "dup"
        )
        r = evaluate_acceptance(m)
        self.assertEqual(r.decision, AcceptanceDecision.CLAIM_NOT_SATISFIED)
        self.assertFalse(r.verified_eligibility_claim)

    def test_unsupported(self):
        m = _all_pass()
        m[ConditionId.C4] = ConditionResult(
            ConditionId.C4, ConditionOutcome.UNSUPPORTED, "unknown_scheme"
        )
        r = evaluate_acceptance(m)
        self.assertEqual(r.decision, AcceptanceDecision.CLAIM_NOT_SATISFIED)

    def test_malformed(self):
        m = _all_pass()
        m[ConditionId.C1] = ConditionResult(
            ConditionId.C1, ConditionOutcome.MALFORMED, "empty"
        )
        r = evaluate_acceptance(m)
        self.assertEqual(r.decision, AcceptanceDecision.CLAIM_NOT_SATISFIED)

    def test_unverifiable(self):
        m = _all_pass()
        m[ConditionId.C3] = ConditionResult(
            ConditionId.C3, ConditionOutcome.UNVERIFIABLE, "bad"
        )
        r = evaluate_acceptance(m)
        self.assertEqual(r.decision, AcceptanceDecision.CLAIM_NOT_SATISFIED)

    def test_missing_c1_cannot_accept(self):
        m = _all_pass()
        del m[ConditionId.C1]
        with self.assertRaises(AcceptanceControlFlowError) as ctx:
            evaluate_acceptance(m)
        self.assertIn("missing_condition:C1", str(ctx.exception))

    def test_missing_c4_cannot_accept(self):
        m = _all_pass()
        del m[ConditionId.C4]
        with self.assertRaises(AcceptanceControlFlowError):
            evaluate_acceptance(m)

    def test_mismatched_condition_id_rejected(self):
        m = _all_pass()
        m[ConditionId.C2] = ConditionResult(
            ConditionId.C1, ConditionOutcome.PASS, "wrong_id"
        )
        with self.assertRaises(AcceptanceControlFlowError):
            evaluate_acceptance(m)

    def test_non_success_never_authorizes(self):
        for outcome in (
            ConditionOutcome.FAIL,
            ConditionOutcome.AMBIGUOUS,
            ConditionOutcome.UNSUPPORTED,
            ConditionOutcome.MALFORMED,
            ConditionOutcome.UNVERIFIABLE,
        ):
            m = _all_pass()
            m[ConditionId.C1] = ConditionResult(ConditionId.C1, outcome, "x")
            r = evaluate_acceptance(m)
            self.assertFalse(r.authorization_permitted)
            self.assertFalse(r.verified_eligibility_claim)
            self.assertEqual(r.decision, AcceptanceDecision.CLAIM_NOT_SATISFIED)


if __name__ == "__main__":
    unittest.main()