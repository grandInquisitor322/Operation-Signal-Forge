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

"""Phase 3.0 — definition artifact completeness tests (no cryptography)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.phase30_definitions import (
    DEFERRED_STAGES,
    INVARIANTS,
    SUCCESS_DOES_NOT_ESTABLISH,
    USE_CASE,
    definition_complete,
)


class Phase30DefinitionTests(unittest.TestCase):
    def test_definition_complete(self):
        self.assertTrue(definition_complete())

    def test_use_case_mentions_responder_and_context(self):
        u = USE_CASE.lower()
        self.assertIn("emergency responder", u)
        self.assertIn("disaster", u)

    def test_stage_32_deferred_not_resolved(self):
        self.assertIn("3.2_disaster_context_authority", DEFERRED_STAGES)

    def test_proof_not_authorization_invariant(self):
        self.assertIn("zkp_proof_validity_is_not_authorization", INVARIANTS)
        self.assertIn("authorization", SUCCESS_DOES_NOT_ESTABLISH)

    def test_no_zkp_runtime_modules_required(self):
        # Phase 3.0 must not introduce a zkp package
        zkp = ROOT / "identity_runtime" / "zkp"
        self.assertFalse(zkp.exists())


if __name__ == "__main__":
    unittest.main()