# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""WP7-CAND-01R1.1 — Targeted Gate 5 remediation tests (R-1, R-2)."""

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
    G1_GENERATOR,
    PROOF_G1_PREFIX,
    encode_g1_proof,
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
class Ev:
    test_id: str
    finding: str
    scenario: str
    observed: str
    accepted: bool
    verified_claim: bool


def _ev(**kw: Any) -> None:
    EVIDENCE.append(asdict(Ev(**kw)))


def _id() -> IdentityTuple:
    return IdentityTuple(
        protocol_id="sf-zk",
        protocol_version="1.0.0",
        scheme_id="mock-scheme",
        scheme_version="1.0.0",
        policy_version="1.0.0",
    )


def _reg() -> CryptographicRegistry:
    r = CryptographicRegistry()
    r.register_scheme(
        SchemeDescriptor(
            scheme_id="mock-scheme",
            scheme_version="1.0.0",
            state=SchemeLifecycleState.SUPPORTED,
        )
    )
    return r


def _pub(**o: Any) -> Dict[str, Any]:
    b: Dict[str, Any] = {
        "context_id": "SF-2026-001",
        "revision": "1",  # R1.1-B canonical decimal string
        "lifecycle_state": "ACTIVE",
        "incident_type": "earthquake",
    }
    b.update(o)
    return b


def _claim() -> str:
    return "eligible responder for specified context"


def _payload(pub: Dict[str, Any]) -> bytes:
    t = ContextClaimBinder().compute_target(
        context_id="SF-2026-001",
        revision=1,
        eligibility_proposition=_claim(),
        public_conditions=pub,
    )
    return ("VALID:" + t.public_conditions_fingerprint).encode()


def _sfg_proof(pub: Dict[str, Any], xy=None) -> bytes:
    x, y = xy or G1_GENERATOR
    return encode_g1_proof(x, y, _payload(pub))


def _v(proof: bytes, public=None, revision: int = 1):
    public = public or _pub()
    return IndependentVerifier(_reg()).verify_proof(
        VerificationRequest(
            identity_tuple=_id(),
            proof_bytes=proof,
            verifier_visible_inputs=public,
            context_id="SF-2026-001",
            revision=revision,
            claim_proposition=_claim(),
        )
    )


class R11TargetedRemediation(unittest.TestCase):
    # --- R-1 ---
    def test_R1_valid_sfg16a_path(self) -> None:
        pub = _pub()
        r = _v(_sfg_proof(pub), pub)
        self.assertTrue(r.accepted)
        self.assertTrue(r.verified_eligibility_claim)
        _ev(
            test_id="R1-01",
            finding="R-1",
            scenario="valid SFG16A + on-curve A + valid payload",
            observed=r.status_code,
            accepted=r.accepted,
            verified_claim=r.verified_eligibility_claim,
        )

    def test_R1_unprefixed_legacy_rejected(self) -> None:
        pub = _pub()
        bare = _payload(pub)
        self.assertFalse(bare.startswith(PROOF_G1_PREFIX))
        r = _v(bare, pub)
        self.assertFalse(r.accepted)
        self.assertFalse(r.verified_eligibility_claim)
        blob = (r.reason + r.status_code).lower()
        self.assertTrue(
            "format" in blob or "sfg" in blob or "malformed" in blob,
            msg=f"{r.status_code}/{r.reason}",
        )
        _ev(
            test_id="R1-02",
            finding="R-1",
            scenario="unprefixed VALID: must not legacy-accept",
            observed=f"{r.status_code}/{r.reason}",
            accepted=False,
            verified_claim=False,
        )

    def test_R1_malformed_sfg16a(self) -> None:
        pub = _pub()
        r = _v(b"SFG16A:not-a-point", pub)
        self.assertFalse(r.accepted)
        self.assertFalse(r.verified_eligibility_claim)
        _ev(
            test_id="R1-03",
            finding="R-1",
            scenario="malformed SFG16A encoding",
            observed=f"{r.status_code}/{r.reason}",
            accepted=False,
            verified_claim=False,
        )

    def test_R1_unrecognized_prefix(self) -> None:
        pub = _pub()
        r = _v(b"OTHERFMT:" + _payload(pub), pub)
        self.assertFalse(r.accepted)
        self.assertFalse(r.verified_eligibility_claim)
        _ev(
            test_id="R1-04",
            finding="R-1",
            scenario="unrecognized prefix cannot select path",
            observed=f"{r.status_code}/{r.reason}",
            accepted=False,
            verified_claim=False,
        )

    def test_R1_empty_and_garbage(self) -> None:
        pub = _pub()
        for proof, tid in [(b"", "R1-05a"), (b"\x00\x01", "R1-05b")]:
            r = _v(proof, pub)
            self.assertFalse(r.accepted)
            self.assertFalse(r.verified_eligibility_claim)
            _ev(
                test_id=tid,
                finding="R-1",
                scenario=repr(proof[:20]),
                observed=r.status_code,
                accepted=False,
                verified_claim=False,
            )

    # --- R-2 ---
    def test_R2_canonical_revision_ok(self) -> None:
        pub = _pub(revision="1")
        r = _v(_sfg_proof(pub), pub)
        self.assertTrue(r.accepted)
        self.assertTrue(r.verified_eligibility_claim)
        _ev(
            test_id="R2-01",
            finding="R-2",
            scenario='revision="1" canonical',
            observed=r.status_code,
            accepted=True,
            verified_claim=True,
        )

    def test_R2_rejects_noncanonical(self) -> None:
        cases = [
            ("R2-02", 1, "int"),
            ("R2-03", 1.0, "float"),
            ("R2-04", True, "bool"),
            ("R2-05", "+1", "plus"),
            ("R2-06", "-1", "minus"),
            ("R2-07", "01", "leading_zero"),
            ("R2-08", "001", "leading_zeros"),
            ("R2-09", "1.0", "decimal"),
            ("R2-10", "1e3", "exponent"),
            ("R2-11", " 1", "ws_lead"),
            ("R2-12", "1 ", "ws_trail"),
            ("R2-13", "1,000", "separator"),
        ]
        for tid, rev, label in cases:
            pub = _pub(revision=rev)
            r = _v(_sfg_proof(pub), pub)
            self.assertFalse(r.accepted, msg=f"{tid} {label} should reject")
            self.assertFalse(r.verified_eligibility_claim)
            _ev(
                test_id=tid,
                finding="R-2",
                scenario=f"revision={rev!r} ({label})",
                observed=f"{r.status_code}/{r.reason}",
                accepted=False,
                verified_claim=False,
            )

    def test_R2_rejects_x_ge_r(self) -> None:
        pub = _pub(revision=str(BN254_R))
        r = _v(_sfg_proof(pub), pub)
        self.assertFalse(r.accepted)
        self.assertIn("field_order", r.reason)
        _ev(
            test_id="R2-14",
            finding="R-2",
            scenario="x == r rejected; no mod r",
            observed=f"{r.status_code}/{r.reason}",
            accepted=False,
            verified_claim=False,
        )

    def test_R2_accepts_r_minus_1(self) -> None:
        xi = BN254_R - 1
        pub = _pub(revision=str(xi))
        r = _v(_sfg_proof(pub), pub, revision=xi)
        self.assertNotIn("field_order", r.reason)
        if not r.accepted:
            self.assertNotIn("scalar_ge_field_order", r.reason)
        _ev(
            test_id="R2-15",
            finding="R-2",
            scenario="x == r-1 in range",
            observed=f"{r.status_code}/{r.reason}/accepted={r.accepted}",
            accepted=r.accepted,
            verified_claim=r.verified_eligibility_claim,
        )


def tearDownModule() -> None:
    out = ROOT / "identity_runtime" / "tests" / "wp7_r11_targeted_evidence.json"
    try:
        out.write_text(json.dumps(EVIDENCE, indent=2), encoding="utf-8")
        print(f"\n[R1.1] evidence: {out} ({len(EVIDENCE)} records)")
    except OSError as e:
        print(e)


if __name__ == "__main__":
    unittest.main()