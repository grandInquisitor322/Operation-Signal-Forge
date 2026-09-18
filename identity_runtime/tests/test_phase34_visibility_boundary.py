# Copyright 2026 Operation Signal Forge contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Stage 3.4 — visibility boundary tests (no cryptography)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.phase34_visibility_boundary import (
    AUTHORITY_VISIBLE_CONDITIONS,
    CLAIM_KINDS,
    CLASSIFICATIONS,
    CONTEXT_FIELDS,
    ELIGIBILITY_PROPOSITION,
    FAIL_CLOSED_TRIGGERS,
    GATE_3_4_TO_3_5,
    INVARIANTS,
    OUTSIDE_PROOF,
    assignment_satisfies_qualification,
    bindings_distinct,
    classify_attribute,
    eligibility_satisfied,
    minimum_verifier_knowledge_contract,
    package_complete,
    qualification_satisfies_assignment,
)


class Phase34VisibilityBoundaryTests(unittest.TestCase):
    def test_package_complete(self):
        self.assertTrue(package_complete())

    def test_claim_kinds_not_collapsed(self):
        for k in ("qualification", "assignment", "eligibility", "authorization"):
            self.assertIn(k, CLAIM_KINDS)

    def test_three_classifications(self):
        self.assertEqual(len(CLASSIFICATIONS), 3)

    def test_classify_unnecessary_is_outside(self):
        c = classify_attribute(
            "extra_field",
            required_for_proposition=False,
            is_evidence_not_condition=False,
        )
        self.assertEqual(c, "outside_proof_boundary")

    def test_classify_required_condition_visible(self):
        c = classify_attribute(
            "lifecycle_state",
            required_for_proposition=True,
            is_evidence_not_condition=False,
        )
        self.assertEqual(c, "verifier_visible")

    def test_classify_required_evidence_private(self):
        c = classify_attribute(
            "qualification_credential",
            required_for_proposition=True,
            is_evidence_not_condition=True,
        )
        self.assertEqual(c, "private_witness")

    def test_classify_exclusion_list(self):
        c = classify_attribute(
            "casualty_lists",
            required_for_proposition=True,
            is_evidence_not_condition=True,
            outside_list=True,
        )
        self.assertEqual(c, "outside_proof_boundary")
        self.assertIn("dispatch_history", OUTSIDE_PROOF)

    def test_context_binding_distinct(self):
        self.assertTrue(bindings_distinct("SF-2026-001", 1, "SF-2026-001", 2))
        self.assertTrue(bindings_distinct("SF-2026-001", 1, "SF-2026-002", 1))
        self.assertFalse(bindings_distinct("SF-2026-001", 1, "SF-2026-001", 1))

    def test_qual_does_not_satisfy_assignment(self):
        self.assertFalse(
            qualification_satisfies_assignment(
                has_qualification=True, requires_assignment=True
            )
        )

    def test_assign_does_not_satisfy_qualification(self):
        self.assertFalse(
            assignment_satisfies_qualification(
                has_assignment=True, requires_qualification=True
            )
        )

    def test_fail_closed(self):
        self.assertFalse(
            eligibility_satisfied(
                required_conditions_ok=True, any_fail_closed_trigger=True
            )
        )
        self.assertTrue(
            eligibility_satisfied(
                required_conditions_ok=True, any_fail_closed_trigger=False
            )
        )
        self.assertIn("revoked", FAIL_CLOSED_TRIGGERS)

    def test_authority_visible_conditions(self):
        self.assertIn("authority_reference", AUTHORITY_VISIBLE_CONDITIONS)

    def test_context_fields_preserved(self):
        for f in (
            "context_id",
            "revision",
            "incident_type",
            "geographic_applicability",
            "operational_period",
            "lifecycle_state",
        ):
            self.assertIn(f, CONTEXT_FIELDS)

    def test_min_verifier_knowledge_contract(self):
        c = minimum_verifier_knowledge_contract()
        self.assertEqual(c["proposition"], ELIGIBILITY_PROPOSITION)
        self.assertIn("private_witness_evidence_classes", c)
        self.assertIn("minimization_rule", c)

    def test_gate_and_invariants(self):
        self.assertTrue(GATE_3_4_TO_3_5["sufficient_for_stage_3_5"])
        self.assertTrue(GATE_3_4_TO_3_5["no_stage_3_5_crypto"])
        self.assertIn("proof_validity_not_authorization", INVARIANTS)

    def test_no_zkp_runtime_package(self):
        self.assertFalse((ROOT / "identity_runtime" / "zkp").exists())


if __name__ == "__main__":
    unittest.main()