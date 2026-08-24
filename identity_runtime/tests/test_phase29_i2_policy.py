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

"""Phase 2.9 — I2 Level 3 environment policy tests."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.independent_verification import record_verification
from identity_runtime.level3_environment_policy import (
    H6_DISPOSITION,
    I2_DECISION,
    REASSESSMENT_TRIGGERS,
    level3_local_path_sufficient,
    limitations_acceptable,
    separate_provisioning_required,
)
from identity_runtime.verification_levels import validate_evidence_for_level


class Phase29Tests(unittest.TestCase):
    def test_i2_no_separate_provisioning(self):
        self.assertFalse(separate_provisioning_required())
        self.assertFalse(I2_DECISION["separate_provisioning_required"])
        self.assertEqual(I2_DECISION["baseline"], "verifier_controlled_local_level3")

    def test_reassessment_triggers_named(self):
        self.assertGreaterEqual(len(REASSESSMENT_TRIGGERS), 6)

    def test_h6_deferred(self):
        self.assertEqual(H6_DISPOSITION["status"], "deferred")

    def test_limitations_empty_rejected(self):
        ok, reason = limitations_acceptable("")
        self.assertFalse(ok)
        ok2, _ = limitations_acceptable("none material")
        self.assertTrue(ok2)

    def test_local_level3_sufficient_without_ci(self):
        ok, reason = level3_local_path_sufficient(
            verifier="rev",
            implementer="auth",
            verifier_run_results={"suite": "PASS"},
            execution_context="verifier-controlled local venv",
            limitations="Local venv, not separate CI",
        )
        self.assertTrue(ok, reason)

    def test_level3_validate_still_works_without_ci_infra(self):
        ok, _ = validate_evidence_for_level(
            3,
            verifier_run_results={"s": "PASS"},
            execution_context="local verifier checkout",
        )
        self.assertTrue(ok)

    def test_level3_pass_requires_nonempty_limitations(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "iv.jsonl"
            with self.assertRaises(ValueError) as ctx:
                record_verification(
                    verifier="r",
                    implementer="a",
                    scope="phase-2.9",
                    suites=["s"],
                    result="PASS",
                    verification_level=3,
                    domains=["audit_compliance"],
                    execution_context="local",
                    verifier_run_results={"s": "PASS"},
                    limitations="",
                    path=path,
                )
            self.assertIn("limitations", str(ctx.exception))

    def test_h1_still_separate_from_g4(self):
        import inspect
        from identity_runtime import independent_verification as iv

        src = inspect.getsource(iv)
        self.assertNotIn("purge_expired_file", src)
        self.assertNotIn("identity_audit:admin", src)


if __name__ == "__main__":
    unittest.main()