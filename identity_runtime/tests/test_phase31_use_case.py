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

"""Phase 3.1 — use-case confirmation tests (no cryptography)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.phase31_use_case import (
    DEFERRED,
    DESIGN_PRINCIPLES,
    INVARIANTS,
    USE_CASE,
    use_case_confirmed,
)


class Phase31UseCaseTests(unittest.TestCase):
    def test_use_case_confirmed(self):
        self.assertTrue(use_case_confirmed())

    def test_singular_use_case_text(self):
        self.assertIn("eligible emergency responder", USE_CASE.lower())
        self.assertIn("specified active", USE_CASE.lower())

    def test_three_design_principles_named(self):
        self.assertEqual(len(DESIGN_PRINCIPLES), 3)

    def test_proof_not_authorization(self):
        self.assertIn(
            "zkp_proof_validity_is_not_authorization", INVARIANTS
        )

    def test_stage_32_still_deferred(self):
        self.assertIn("3.2_disaster_context_authority", DEFERRED)

    def test_no_zkp_runtime_package(self):
        self.assertFalse((ROOT / "identity_runtime" / "zkp").exists())


if __name__ == "__main__":
    unittest.main()