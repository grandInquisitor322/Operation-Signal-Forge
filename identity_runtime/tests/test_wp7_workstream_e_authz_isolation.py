# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""WP7-CAND-01R1 Workstream E — Authorization isolation tests."""

from __future__ import annotations

import json
import sys
import unittest
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.zk_abstraction.authorization_isolation import (
    AuthorizationRequest,
    VerifiedEligibilityClaim,
    authorize,
    authorize_from_verification,
    claim_from_verification,
)
from identity_runtime.zk_abstraction.binder import ContextClaimBinder
from identity_runtime.zk_abstraction.identity import IdentityTuple
from identity_runtime.zk_abstraction.registry import (
    CryptographicRegistry,
    SchemeDescriptor,
    SchemeLifecycleState,
)
from identity_runtime.zk_abstraction.verifier import IndependentVerifier, VerificationRequest

EVIDENCE: List[Dict[str, Any]] = []


@dataclass
class EvidenceRecord:
    test_id: str
    scenario: str
    expected_result: str
    observed_result: str
    authorization_decision: bool
    had_positive_verified_claim: bool
    denial_or_grant_reason: str


def _ev(**kw):
    EVIDENCE.append(asdict(EvidenceRecord(**kw)))


def _id():
    return IdentityTuple(
        protocol_id="sf-zk",
        protocol_version="1.0.0",
        scheme_id="mock-scheme",
        scheme_version="1.0.0",
        policy_version="1.0.0",
    )


def _reg():
    r = CryptographicRegistry()
    r.register_scheme(
        SchemeDescriptor(
            scheme_id="mock-scheme",
            scheme_version="1.0.0",
            state=SchemeLifecycleState.SUPPORTED,
        )
    )
    return r


def _pub():
    return {
        "context_id": "SF-2026-001",
        "revision": 1,
        "lifecycle_state": "ACTIVE",
        "incident_type": "earthquake",
    }


def _claim_text():
    return "eligible responder for specified context"


def _valid_proof(pub):
    t = ContextClaimBinder().compute_target(
        context_id="SF-2026-001",
        revision=1,
        eligibility_proposition=_claim_text(),
        public_conditions=pub,
    )
    return ("VALID:" + t.public_conditions_fingerprint).encode()


def _verify(proof, public=None):
    public = public or _pub()
    return IndependentVerifier(_reg()).verify_proof(
        VerificationRequest(
            identity_tuple=_id(),
            proof_bytes=proof,
            verifier_visible_inputs=public,
            context_id="SF-2026-001",
            revision=1,
            claim_proposition=_claim_text(),
        )
    )


class WorkstreamEAuthzIsolation(unittest.TestCase):
    def test_E01_valid_positive_path(self):
        pub = _pub()
        r = _verify(_valid_proof(pub), pub)
        self.assertTrue(r.accepted)
        d = authorize_from_verification(r)
        self.assertTrue(d.permitted)
        self.assertTrue(d.had_positive_verified_claim)
        _ev(
            test_id="E-01",
            scenario="valid positive verified claim",
            expected_result="AUTHZ_PERMITTED",
            observed_result=d.status_code,
            authorization_decision=d.permitted,
            had_positive_verified_claim=True,
            denial_or_grant_reason=d.reason,
        )

    def test_E02_missing_proof(self):
        r = _verify(b"", _pub())
        self.assertFalse(r.accepted)
        d = authorize_from_verification(r)
        self.assertFalse(d.permitted)
        self.assertFalse(d.had_positive_verified_claim)
        _ev(
            test_id="E-02",
            scenario="missing proof",
            expected_result="denied",
            observed_result=d.status_code,
            authorization_decision=False,
            had_positive_verified_claim=False,
            denial_or_grant_reason=d.reason,
        )

    def test_E03_invalid_proof(self):
        r = _verify(b"INVALID_PROOF", _pub())
        self.assertFalse(r.accepted)
        d = authorize_from_verification(r, role="commander", scopes=("all",))
        self.assertFalse(d.permitted)
        _ev(
            test_id="E-03",
            scenario="invalid proof; favorable role/scopes",
            expected_result="denied",
            observed_result=d.status_code,
            authorization_decision=False,
            had_positive_verified_claim=False,
            denial_or_grant_reason=d.reason,
        )

    def test_E04_failure_plus_raw_credential(self):
        r = _verify(b"NOT_A_PROOF", _pub())
        d = authorize_from_verification(
            r, raw_credential={"type": "HumanitarianAnalyst", "token": "steal"}
        )
        self.assertFalse(d.permitted)
        self.assertTrue(d.used_raw_credential)
        _ev(
            test_id="E-04",
            scenario="failed verification + raw credential",
            expected_result="denied",
            observed_result=d.status_code,
            authorization_decision=False,
            had_positive_verified_claim=False,
            denial_or_grant_reason=d.reason,
        )

    def test_E05_malformed_untrusted_result(self):
        claim = claim_from_verification(_verify(b"", _pub()))
        self.assertIsNone(claim)
        d = authorize(AuthorizationRequest(verified_claim=None))
        self.assertFalse(d.permitted)
        _ev(
            test_id="E-05",
            scenario="no valid positive claim from unsuccessful result",
            expected_result="AUTHZ_DENIED_NO_CLAIM",
            observed_result=d.status_code,
            authorization_decision=False,
            had_positive_verified_claim=False,
            denial_or_grant_reason=d.reason,
        )

    def test_E06_permissive_default_attempt(self):
        r = _verify(b"BAD", _pub())
        d = authorize_from_verification(r, force_authorize=True, default_allow=True)
        self.assertFalse(d.permitted)
        self.assertTrue(d.used_force_or_default)
        _ev(
            test_id="E-06",
            scenario="unsuccessful verification + force/default allow",
            expected_result="denied",
            observed_result=d.status_code,
            authorization_decision=False,
            had_positive_verified_claim=False,
            denial_or_grant_reason=d.reason,
        )

    def test_E07_direct_matrix_bypass(self):
        d = authorize(
            AuthorizationRequest(
                verified_claim=None,
                role="IncidentCommander",
                scopes=("capabilities:invoke",),
                raw_credential={"vc": "present"},
            )
        )
        self.assertFalse(d.permitted)
        self.assertEqual(d.status_code, "AUTHZ_DENIED_NO_CLAIM")
        _ev(
            test_id="E-07",
            scenario="direct matrix request without verified claim",
            expected_result="AUTHZ_DENIED_NO_CLAIM",
            observed_result=d.status_code,
            authorization_decision=False,
            had_positive_verified_claim=False,
            denial_or_grant_reason=d.reason,
        )

    def test_E08_false_and_none_claim(self):
        d_false = authorize(
            AuthorizationRequest(
                verified_claim=VerifiedEligibilityClaim(
                    positive=False,
                    context_id="SF-2026-001",
                    revision=1,
                    scheme_id="mock-scheme",
                    scheme_version="1.0.0",
                )
            )
        )
        self.assertFalse(d_false.permitted)
        d_none = authorize(AuthorizationRequest(verified_claim=None))
        self.assertFalse(d_none.permitted)
        _ev(
            test_id="E-08",
            scenario="explicit false claim and null claim",
            expected_result="denied",
            observed_result=f"{d_false.status_code}/{d_none.status_code}",
            authorization_decision=False,
            had_positive_verified_claim=False,
            denial_or_grant_reason=d_false.reason,
        )

    def test_E09_claim_proof_mismatch_wrong_source(self):
        bad = VerifiedEligibilityClaim(
            positive=True,
            context_id="SF-2026-001",
            revision=1,
            scheme_id="mock-scheme",
            scheme_version="1.0.0",
            source="raw_credential",
        )
        d = authorize(AuthorizationRequest(verified_claim=bad))
        self.assertFalse(d.permitted)
        self.assertEqual(d.status_code, "AUTHZ_DENIED_CLAIM_MALFORMED")
        _ev(
            test_id="E-09",
            scenario="positive-looking claim with wrong source",
            expected_result="AUTHZ_DENIED_CLAIM_MALFORMED",
            observed_result=d.status_code,
            authorization_decision=False,
            had_positive_verified_claim=False,
            denial_or_grant_reason=d.reason,
        )

    def test_E10_failure_not_asserted_ineligible(self):
        r = _verify(b"INVALID", _pub())
        self.assertFalse(r.accepted)
        if r.taxonomy is not None:
            self.assertFalse(r.taxonomy.asserts_subject_ineligible)
        d = authorize_from_verification(r)
        self.assertFalse(d.permitted)
        _ev(
            test_id="E-10",
            scenario="failed verification does not assert ineligibility; denies authz",
            expected_result="denied; NOT_ASSERTED ineligibility",
            observed_result=d.status_code,
            authorization_decision=False,
            had_positive_verified_claim=False,
            denial_or_grant_reason=d.reason,
        )


def tearDownModule():
    out = ROOT / "identity_runtime" / "tests" / "wp7_workstream_e_evidence.json"
    try:
        out.write_text(json.dumps(EVIDENCE, indent=2), encoding="utf-8")
        print(f"\n[Workstream E] evidence: {out} ({len(EVIDENCE)} records)")
    except OSError as e:
        print(f"[Workstream E] evidence write failed: {e}")


if __name__ == "__main__":
    unittest.main()