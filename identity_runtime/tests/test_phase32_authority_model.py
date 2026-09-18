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

"""Phase 3.2 — authority model package tests (no crypto, no schemas)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.phase32_authority_model import (
    AUTHORITY_ROLES,
    CLAIM_TYPES,
    GATE_3_2_TO_3_3,
    INVARIANTS,
    LIFECYCLE_SEMANTICS,
    REJECTED_ALTERNATIVES,
    package_complete,
)


class Phase32AuthorityModelTests(unittest.TestCase):
    def test_package_complete(self):
        self.assertTrue(package_complete())

    def test_five_authority_roles(self):
        self.assertEqual(len(AUTHORITY_ROLES), 5)
        self.assertIn("authorized_incident_authority", AUTHORITY_ROLES)
        self.assertIn("zkp_verifier", AUTHORITY_ROLES)

    def test_three_claim_types_separated(self):
        self.assertIn("qualification_claim", CLAIM_TYPES)
        self.assertIn("assignment_claim", CLAIM_TYPES)
        self.assertIn("authorization_decision", CLAIM_TYPES)

    def test_six_lifecycle_semantics(self):
        self.assertEqual(len(LIFECYCLE_SEMANTICS), 6)

    def test_zkp_cannot_determine_disaster_status(self):
        self.assertIn(
            "zkp_layer_determines_disaster_status", REJECTED_ALTERNATIVES
        )
        self.assertIn(
            "active_context_established_by_authority_not_zkp", INVARIANTS
        )

    def test_gate_flags(self):
        self.assertTrue(GATE_3_2_TO_3_3["lifecycle_semantics_documented"])
        self.assertTrue(GATE_3_2_TO_3_3["zkp_boundary_preserved"])

    def test_no_zkp_runtime_package(self):
        self.assertFalse((ROOT / "identity_runtime" / "zkp").exists())


if __name__ == "__main__":
    unittest.main()