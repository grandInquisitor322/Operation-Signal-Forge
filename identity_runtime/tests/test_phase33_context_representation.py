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

"""Stage 3.3 — context representation package tests (no crypto)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.phase33_context_representation import (
    EXCLUSIONS,
    GATE_3_3_TO_3_4,
    GOVERNING,
    INVARIANTS,
    LIFECYCLE_STATES,
    REPRESENTATION_MODEL,
    SCOPE_FIELDS,
    package_complete,
)


class Phase33ContextRepresentationTests(unittest.TestCase):
    def test_package_complete(self):
        self.assertTrue(package_complete())

    def test_four_scope_fields(self):
        self.assertEqual(len(SCOPE_FIELDS), 4)

    def test_four_lifecycle_states(self):
        self.assertEqual(
            set(LIFECYCLE_STATES),
            {"ACTIVE", "EXPIRED", "REVOKED", "SUPERSEDED"},
        )

    def test_hybrid_model_named(self):
        self.assertIn("canonical_context_envelope", REPRESENTATION_MODEL)

    def test_fail_closed_and_not_authz_engine(self):
        self.assertIn("representation_is_not_authorization_engine", INVARIANTS)
        self.assertIn("proof_validity_not_authorization", INVARIANTS)

    def test_exclusions_include_rosters_and_dispatch(self):
        self.assertIn("responder_rosters", EXCLUSIONS)
        self.assertIn("dispatch_data", EXCLUSIONS)

    def test_gate_flags(self):
        self.assertTrue(GATE_3_3_TO_3_4["sufficient_for_stage_3_4"])
        self.assertTrue(GATE_3_3_TO_3_4["no_public_private_split"])
        self.assertTrue(GATE_3_3_TO_3_4["no_zk_runtime"])

    def test_governing_principles_present(self):
        self.assertIn("minimum authoritative context", GOVERNING["scope"])
        self.assertIn("consumes context", GOVERNING["external_boundary"])

    def test_no_zkp_runtime_package(self):
        self.assertFalse((ROOT / "identity_runtime" / "zkp").exists())


if __name__ == "__main__":
    unittest.main()