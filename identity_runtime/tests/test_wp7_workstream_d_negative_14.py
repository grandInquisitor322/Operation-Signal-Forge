# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""WP7-CAND-01R1 Workstream D — SF-3.5-CONF-3 14-case negative suite.

NEG-C1-03 / NEG-C2-02 use the BN254 affine G1 + Fr kernel on the verifier path.
Pairing evaluation remains mock.
"""

from __future__ import annotations

import json
import sys
import unittest
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.zk_abstraction.bn254 import (
    BN254_R,
    encode_g1_proof,
)
from identity_runtime.zk_abstraction.binder import ContextClaimBinder
from identity_runtime.zk_abstraction.c4_policy_wrapper import VerifierPolicyContext
from identity_runtime.zk_abstraction.identity import IdentityTuple
from identity_runtime.zk_abstraction.registry import (
    CryptographicRegistry,
    SchemeDescriptor,
    SchemeLifecycleState,
)
from identity_runtime.zk_abstraction.result_taxonomy import (
    SubjectIneligibilityStatus,
    VerificationOutcomeClass,
)
from identity_runtime.zk_abstraction.verifier import IndependentVerifier, VerificationRequest

EVIDENCE: List[Dict[str, Any]] = []


@dataclass
class EvidenceRecord:
    test_id: str
    failure_condition: str
    setup: str
    exact_input_mutation: str
    command: str
    observed_result: str
    status_code: str
    verified_eligibility_claim: bool
    authorization_outcome: str
    crypto_boundary: str = "mock"


def _rec(**kw):
    EVIDENCE.append(asdict(EvidenceRecord(**kw)))


def _id(**kw):
    b = dict(
        protocol_id="sf-zk",
        protocol_version="1.0.0",
        scheme_id="mock-scheme",
        scheme_version="1.0.0",
        policy_version="1.0.0",
    )
    b.update(kw)
    return IdentityTuple(**b)


def _reg(state=SchemeLifecycleState.SUPPORTED, version="1.0.0"):
    r = CryptographicRegistry()
    r.register_scheme(
        SchemeDescriptor(scheme_id="mock-scheme", scheme_version=version, state=state)
    )
    return r


def _pub(**o):
    b = {
        "context_id": "SF-2026-001",
        "revision": 1,
        "lifecycle_state": "ACTIVE",
        "incident_type": "earthquake",
    }
    b.update(o)
    return b


def _claim():
    return "eligible responder for specified context"


def _proof(pub, claim=None):
    claim = claim or _claim()
    t = ContextClaimBinder().compute_target(
        context_id=pub.get("context_id", "SF-2026-001"),
        revision=pub.get("revision", 1),
        eligibility_proposition=claim,
        public_conditions=pub,
    )
    return ("VALID:" + t.public_conditions_fingerprint).encode()


def _v(reg=None, proof=None, public=None, identity=None, claim=None, policy_context=None, context_id="SF-2026-001", revision=1):
    reg = reg or _reg()
    public = public if public is not None else _pub()
    claim = claim or _claim()
    identity = identity or _id()
    if proof is None:
        proof = _proof(public, claim)
    return IndependentVerifier(reg, policy_context=policy_context).verify_proof(
        VerificationRequest(
            identity_tuple=identity,
            proof_bytes=proof,
            verifier_visible_inputs=public,
            context_id=context_id,
            revision=revision,
            claim_proposition=claim,
        )
    )


def _rej(r, tid):
    assert r.accepted is False, tid
    assert r.verified_eligibility_claim is False, tid
    assert r.authorization_permitted is False, tid
    if r.taxonomy is not None:
        assert r.taxonomy.outcome != VerificationOutcomeClass.VERIFIED_ELIGIBILITY, tid
        assert r.taxonomy.subject_ineligibility == SubjectIneligibilityStatus.NOT_ASSERTED, tid


class WorkstreamDNegative14(unittest.TestCase):
    def test_NEG_C1_01(self):
        pub = _pub()
        good = _proof(pub)
        mut = b"MUTATED_A:" + good[6:]
        r = _v(proof=mut, public=pub)
        _rej(r, "NEG-C1-01")
        _rec(
            test_id="NEG-C1-01",
            failure_condition="Mutated scalar bytes in Groth16 group element A",
            setup="corrupt mock proof A material",
            exact_input_mutation=repr(mut[:24]),
            command="verify_proof(mutated A)",
            observed_result="REJECT",
            status_code=r.status_code,
            verified_eligibility_claim=False,
            authorization_outcome="denied",
            crypto_boundary="mock — not production Groth16",
        )

    def test_NEG_C1_02(self):
        p1, p2 = _pub(incident_type="earthquake"), _pub(incident_type="flood")
        r = _v(proof=_proof(p1), public=p2)
        _rej(r, "NEG-C1-02")
        _rec(
            test_id="NEG-C1-02",
            failure_condition="Circuit mismatch: proof for R1 supplied for R2",
            setup="proof for earthquake pub; verify flood pub",
            exact_input_mutation="incident_type earthquake→flood",
            command="verify_proof(circuit mismatch)",
            observed_result="REJECT",
            status_code=r.status_code,
            verified_eligibility_claim=False,
            authorization_outcome="denied",
            crypto_boundary="mock fingerprint as relation id",
        )

    def test_NEG_C1_03(self):
        pub = _pub()
        # A = (1, 1) is in Fp×Fp but y^2 ≠ x^3+3 (1 ≠ 4). Payload is otherwise valid
        # so rejection cannot be empty-proof or mock fingerprint mismatch.
        mut = encode_g1_proof(1, 1, _proof(pub))
        r = _v(proof=mut, public=pub)
        _rej(r, "NEG-C1-03")
        self.assertEqual(r.status_code, "MALFORMED_PROOF")
        self.assertEqual(r.reason, "g1_a_off_curve")
        _rec(
            test_id="NEG-C1-03",
            failure_condition="Point off-curve / subgroup validation failure on A",
            setup="BN254 G1 A=(1,1) off y^2=x^3+3; VALID payload retained",
            exact_input_mutation=repr(mut[:48]),
            command="verify_proof(off-curve A)",
            observed_result="REJECT",
            status_code=r.status_code,
            verified_eligibility_claim=False,
            authorization_outcome="denied",
            crypto_boundary="BN254 G1 affine on-curve + [r]P; no pairing",
        )

    def test_NEG_C2_01(self):
        r = _v(public=_pub(casualty_lists=["secret"]))
        _rej(r, "NEG-C2-01")
        _rec(
            test_id="NEG-C2-01",
            failure_condition="Unadmitted input outside Stage 3.4 boundary",
            setup="inject casualty_lists",
            exact_input_mutation="casualty_lists",
            command="verify_proof(unadmitted)",
            observed_result="REJECT",
            status_code=r.status_code,
            verified_eligibility_claim=False,
            authorization_outcome="denied",
        )

    def test_NEG_C2_02(self):
        # x_i = r (Fr order). Must reject; must not reduce to 0.
        pub = _pub(incident_type=BN254_R)
        r = _v(public=pub)
        _rej(r, "NEG-C2-02")
        self.assertEqual(r.status_code, "MALFORMED_CONDITION")
        self.assertTrue(r.reason.startswith("scalar_ge_field_order:incident_type:"))
        _rec(
            test_id="NEG-C2-02",
            failure_condition="Malformed field scalar x_i >= p",
            setup="allowlisted incident_type set to BN254 Fr order r (no reduction)",
            exact_input_mutation=f"incident_type={BN254_R} (>= r)",
            command="verify_proof(x_i>=p)",
            observed_result="REJECT",
            status_code=r.status_code,
            verified_eligibility_claim=False,
            authorization_outcome="denied",
            crypto_boundary="BN254 Fr; reject x_i>=r with no mod-r",
        )

    def test_NEG_C2_03(self):
        r = _v(public={"context_id": "SF-2026-001", "revision": 1})
        _rej(r, "NEG-C2-03")
        _rec(
            test_id="NEG-C2-03",
            failure_condition="Required verifier-visible input omitted",
            setup="omit lifecycle_state",
            exact_input_mutation="no lifecycle_state",
            command="verify_proof(missing required)",
            observed_result="REJECT",
            status_code=r.status_code,
            verified_eligibility_claim=False,
            authorization_outcome="denied",
        )

    def test_NEG_C3_01(self):
        r = _v(public=_pub(context_id="SF-2026-OTHER"), context_id="SF-2026-001")
        _rej(r, "NEG-C3-01")
        _rec(
            test_id="NEG-C3-01",
            failure_condition="Mutated context_id binding",
            setup="public vs request context mismatch",
            exact_input_mutation="SF-2026-OTHER vs SF-2026-001",
            command="verify_proof(context)",
            observed_result="REJECT",
            status_code=r.status_code,
            verified_eligibility_claim=False,
            authorization_outcome="denied",
        )

    def test_NEG_C3_02(self):
        r = _v(public=_pub(revision=99), revision=1)
        _rej(r, "NEG-C3-02")
        _rec(
            test_id="NEG-C3-02",
            failure_condition="Mutated revision binding",
            setup="revision 99 vs 1",
            exact_input_mutation="99 vs 1",
            command="verify_proof(revision)",
            observed_result="REJECT",
            status_code=r.status_code,
            verified_eligibility_claim=False,
            authorization_outcome="denied",
        )

    def test_NEG_C3_03(self):
        r = _v(
            public=_pub(eligibility_proposition="qualification:eligible_responder"),
            claim="assignment:dispatch_team_alpha",
        )
        _rej(r, "NEG-C3-03")
        _rec(
            test_id="NEG-C3-03",
            failure_condition="Proposition re-binding Qualification vs Assignment",
            setup="public qualification; claim assignment",
            exact_input_mutation="qualification→assignment",
            command="verify_proof(proposition)",
            observed_result="REJECT",
            status_code=r.status_code,
            verified_eligibility_claim=False,
            authorization_outcome="denied",
        )

    def test_NEG_C4_01(self):
        pub = _pub()
        r = _v(reg=_reg(SchemeLifecycleState.DISABLED), public=pub, proof=_proof(pub))
        _rej(r, "NEG-C4-01")
        _rec(
            test_id="NEG-C4-01",
            failure_condition="scheme DISABLED/RETIRED",
            setup="DISABLED scheme + valid mock proof",
            exact_input_mutation="DISABLED",
            command="verify_proof(disabled)",
            observed_result="REJECT",
            status_code=r.status_code,
            verified_eligibility_claim=False,
            authorization_outcome="denied",
        )

    def test_NEG_C4_02(self):
        reg = _reg(version="2.0.0")
        reg.register_scheme(
            SchemeDescriptor(
                scheme_id="mock-scheme",
                scheme_version="1.0.0",
                state=SchemeLifecycleState.SUPPORTED,
            )
        )
        reg.set_min_scheme_version("mock-scheme", "2.0.0")
        pub = _pub()
        r = _v(reg=reg, public=pub, proof=_proof(pub), identity=_id(scheme_version="1.0.0"))
        _rej(r, "NEG-C4-02")
        _rec(
            test_id="NEG-C4-02",
            failure_condition="Unauthorized version downgrade",
            setup="min 2.0.0; request 1.0.0",
            exact_input_mutation="1.0.0 < 2.0.0",
            command="verify_proof(downgrade)",
            observed_result="REJECT",
            status_code=r.status_code,
            verified_eligibility_claim=False,
            authorization_outcome="denied",
        )

    def test_NEG_C4_03(self):
        pub = _pub()
        r = _v(
            public=pub,
            proof=_proof(pub),
            identity=_id(policy_version="1.0.0"),
            policy_context=VerifierPolicyContext(active_policy_version="2.0.0"),
        )
        _rej(r, "NEG-C4-03")
        _rec(
            test_id="NEG-C4-03",
            failure_condition="Mismatched policy_version",
            setup="active 2.0.0; identity 1.0.0",
            exact_input_mutation="1.0.0 vs 2.0.0",
            command="verify_proof(policy)",
            observed_result="REJECT",
            status_code=r.status_code,
            verified_eligibility_claim=False,
            authorization_outcome="denied",
        )

    def test_NEG_FLB_01(self):
        r = _v(proof=b"", public=_pub())
        _rej(r, "NEG-FLB-01")
        _rec(
            test_id="NEG-FLB-01",
            failure_condition="Absent proof payload",
            setup="empty proof",
            exact_input_mutation="proof_bytes=b''",
            command="verify_proof(no proof)",
            observed_result="REJECT; no verified claim; authz denied",
            status_code=r.status_code,
            verified_eligibility_claim=False,
            authorization_outcome="denied",
        )

    def test_NEG_FLB_02(self):
        r = _v(proof=b"NOT_A_PROOF", public=_pub())
        _rej(r, "NEG-FLB-02")
        self.assertFalse(getattr(r, "raw_credential_accepted", False))
        _rec(
            test_id="NEG-FLB-02",
            failure_condition="No raw credential fallback",
            setup="invalid proof; no fallback attr",
            exact_input_mutation="NOT_A_PROOF",
            command="verify_proof(invalid)",
            observed_result="REJECT; no credential fallback",
            status_code=r.status_code,
            verified_eligibility_claim=False,
            authorization_outcome="denied",
        )


def tearDownModule():
    out = ROOT / "identity_runtime" / "tests" / "wp7_workstream_d_evidence.json"
    try:
        out.write_text(json.dumps(EVIDENCE, indent=2), encoding="utf-8")
        print(f"\n[Workstream D] evidence: {out} ({len(EVIDENCE)} records)")
    except OSError as e:
        print(f"[Workstream D] evidence write failed: {e}")


if __name__ == "__main__":
    unittest.main()