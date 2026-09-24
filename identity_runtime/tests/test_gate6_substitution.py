# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""Gate 6 — scheme substitution evidence (two SchemeVerifier adapters).

Demonstrates mechanism replaceability, not a second production ZK system.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.zk_abstraction.adapters.mock_digest_v2 import (
    PREFIX as M2_PREFIX,
    _view_digest,
)
from identity_runtime.zk_abstraction.bn254 import G1_GENERATOR, encode_g1_proof
from identity_runtime.zk_abstraction.binder import ContextClaimBinder
from identity_runtime.zk_abstraction.identity import IdentityTuple
from identity_runtime.zk_abstraction.registry import (
    CryptographicRegistry,
    install_default_mock_schemes,
)
from identity_runtime.zk_abstraction.scheme_types import BoundStatementTarget
from identity_runtime.zk_abstraction.verifier import IndependentVerifier, VerificationRequest


def _pub():
    return {
        "context_id": "SF-2026-001",
        "revision": "1",
        "lifecycle_state": "ACTIVE",
        "incident_type": "earthquake",
    }


def _claim():
    return "eligible responder for specified context"


class Gate6SubstitutionTests(unittest.TestCase):
    def test_scheme_a_bn254_sfg16a_accepts(self):
        reg = install_default_mock_schemes(CryptographicRegistry())
        pub = _pub()
        claim = _claim()
        fp = ContextClaimBinder().compute_target(
            context_id="SF-2026-001",
            revision=1,
            eligibility_proposition=claim,
            public_conditions=pub,
        ).public_conditions_fingerprint
        proof = encode_g1_proof(
            G1_GENERATOR[0], G1_GENERATOR[1], ("VALID:" + fp).encode()
        )
        r = IndependentVerifier(reg).verify_proof(
            VerificationRequest(
                identity_tuple=IdentityTuple(
                    protocol_id="sf-zk",
                    protocol_version="1.0.0",
                    scheme_id="mock-scheme",
                    scheme_version="1.0.0",
                    policy_version="1.0.0",
                ),
                proof_bytes=proof,
                verifier_visible_inputs=pub,
                context_id="SF-2026-001",
                revision=1,
                claim_proposition=claim,
            )
        )
        self.assertTrue(r.accepted, msg=f"{r.status_code}/{r.reason}")

    def test_scheme_b_digest_v2_accepts_same_semantics(self):
        reg = install_default_mock_schemes(CryptographicRegistry())
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
        tag = _view_digest(bound)
        proof = M2_PREFIX + tag.encode("utf-8")
        r = IndependentVerifier(reg).verify_proof(
            VerificationRequest(
                identity_tuple=IdentityTuple(
                    protocol_id="sf-zk",
                    protocol_version="1.0.0",
                    scheme_id="mock-digest",
                    scheme_version="1.0.0",
                    policy_version="1.0.0",
                ),
                proof_bytes=proof,
                verifier_visible_inputs=pub,
                context_id="SF-2026-001",
                revision=1,
                claim_proposition=claim,
            )
        )
        self.assertTrue(r.accepted, msg=f"{r.status_code}/{r.reason}")

    def test_wrong_scheme_proof_fails_closed(self):
        reg = install_default_mock_schemes(CryptographicRegistry())
        pub = _pub()
        claim = _claim()
        # Digest-v2 wire under mock-scheme (BN254) must not accept
        proof = M2_PREFIX + b"deadbeef"
        r = IndependentVerifier(reg).verify_proof(
            VerificationRequest(
                identity_tuple=IdentityTuple(
                    protocol_id="sf-zk",
                    protocol_version="1.0.0",
                    scheme_id="mock-scheme",
                    scheme_version="1.0.0",
                    policy_version="1.0.0",
                ),
                proof_bytes=proof,
                verifier_visible_inputs=pub,
                context_id="SF-2026-001",
                revision=1,
                claim_proposition=claim,
            )
        )
        self.assertFalse(r.accepted)
        self.assertFalse(r.verified_eligibility_claim)

    def test_bound_statement_immutable_view(self):
        bound = BoundStatementTarget(
            statement_id="x",
            scheme_id="mock-scheme",
            scheme_version="1.0.0",
            materials_ref="mock",
            public_input_view={"revision": "1"},
        )
        with self.assertRaises(TypeError):
            bound.public_input_view["revision"] = "2"


if __name__ == "__main__":
    unittest.main()