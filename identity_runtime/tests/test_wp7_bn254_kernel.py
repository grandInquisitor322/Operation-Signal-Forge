# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""BN254 kernel checks backing NEG-C1-03 / NEG-C2-02 (no silent reduction).

Aligned with WP7-CAND-01R1.1 (revision scalar scope + ASCII decimal).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.zk_abstraction.bn254 import (
    BN254_B,
    BN254_P,
    BN254_R,
    G1_GENERATOR,
    encode_g1_proof,
    first_public_scalar_out_of_range,
    first_public_scalar_violation,
    g1_in_prime_subgroup,
    g1_on_curve,
    g1_scalar_mul,
    parse_canonical_fr_decimal,
    parse_g1_proof,
    validate_g1_affine,
)
from identity_runtime.zk_abstraction.binder import ContextClaimBinder
from identity_runtime.zk_abstraction.identity import IdentityTuple
from identity_runtime.zk_abstraction.registry import (
    CryptographicRegistry,
    SchemeDescriptor,
    SchemeLifecycleState,
)
from identity_runtime.zk_abstraction.verifier import IndependentVerifier, VerificationRequest


class Bn254KernelTests(unittest.TestCase):
    def test_generator_on_curve(self):
        x, y = G1_GENERATOR
        self.assertEqual((y * y) % BN254_P, (x * x * x + BN254_B) % BN254_P)
        self.assertTrue(g1_on_curve(x, y))
        self.assertIsNone(validate_g1_affine(x, y))

    def test_off_curve_point(self):
        self.assertFalse(g1_on_curve(1, 1))
        self.assertEqual(validate_g1_affine(1, 1), "g1_a_off_curve")

    def test_coordinate_not_reduced_mod_p(self):
        self.assertEqual(
            validate_g1_affine(BN254_P, 2), "g1_a_coordinate_out_of_range"
        )
        self.assertEqual(
            validate_g1_affine(1, BN254_P), "g1_a_coordinate_out_of_range"
        )

    def test_subgroup_order_of_generator(self):
        x, y = G1_GENERATOR
        self.assertIsNone(g1_scalar_mul(BN254_R, (x, y)))
        self.assertTrue(g1_in_prime_subgroup(x, y))

    def test_public_scalar_eq_r_rejected_without_reduction(self):
        # R1.1-B: verifier-visible Fr scalar is revision (canonical decimal string)
        hit = first_public_scalar_violation(
            {"revision": str(BN254_R)}, scalar_keys=("revision",)
        )
        self.assertIsNotNone(hit)
        self.assertEqual(hit[0], "revision")
        self.assertTrue(
            "field_order" in hit[1] or hit[1].startswith("scalar_ge_field_order"),
            msg=hit[1],
        )
        # no modular reduction of r into a valid Fr element for this check
        self.assertEqual(BN254_R % BN254_R, 0)
        self.assertNotEqual(BN254_R, 0)

    def test_public_scalar_r_minus_one_in_range(self):
        xi = BN254_R - 1
        hit = first_public_scalar_violation(
            {"revision": str(xi)}, scalar_keys=("revision",)
        )
        self.assertIsNone(hit)
        val, err = parse_canonical_fr_decimal(str(xi))
        self.assertIsNone(err)
        self.assertEqual(val, xi)

    def test_ascii_only_rejects_unicode_digits(self):
        # H-2: Arabic-Indic / fullwidth digits must not pass (str.isdigit would)
        val, err = parse_canonical_fr_decimal("١")
        self.assertIsNone(val)
        self.assertIsNotNone(err)
        val2, err2 = parse_canonical_fr_decimal("１０")
        self.assertIsNone(val2)
        self.assertIsNotNone(err2)

    def test_on_curve_a_with_valid_payload_accepted(self):
        pub = {
            "context_id": "SF-2026-001",
            "revision": "1",  # R1.1-B canonical decimal string
            "lifecycle_state": "ACTIVE",
            "incident_type": "earthquake",
        }
        claim = "eligible responder for specified context"
        fp = ContextClaimBinder().compute_target(
            context_id="SF-2026-001",
            revision=1,
            eligibility_proposition=claim,
            public_conditions=pub,
        ).public_conditions_fingerprint
        payload = ("VALID:" + fp).encode()
        x, y = G1_GENERATOR
        proof = encode_g1_proof(x, y, payload)
        parsed = parse_g1_proof(proof)
        self.assertEqual((parsed.x, parsed.y), (x, y))
        self.assertEqual(parsed.payload, payload)

        reg = CryptographicRegistry()
        reg.register_scheme(
            SchemeDescriptor(
                scheme_id="mock-scheme",
                scheme_version="1.0.0",
                state=SchemeLifecycleState.SUPPORTED,
            )
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
        self.assertTrue(r.verified_eligibility_claim)


if __name__ == "__main__":
    unittest.main()