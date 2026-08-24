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

"""Phase 2.8 — verification level assignment and record tests."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.independent_verification import record_verification
from identity_runtime.verification_levels import (
    LEVEL_1,
    LEVEL_2,
    LEVEL_3,
    confirm_or_escalate,
    expected_evidence_for_level,
    propose_level,
    recommend_level,
    validate_evidence_for_level,
    validate_level_record,
)


class Phase28Tests(unittest.TestCase):
    def test_low_consequence_level_1(self):
        lvl, _ = recommend_level(domains=["documentation"])
        self.assertEqual(lvl, LEVEL_1)

    def test_high_consequence_level_3(self):
        lvl, _ = recommend_level(domains=["identity_recovery", "audit_governance"])
        self.assertEqual(lvl, LEVEL_3)

    def test_ambiguous_escalates(self):
        lvl, reason = recommend_level(domains=["documentation"], ambiguous=True)
        self.assertEqual(lvl, LEVEL_2)
        self.assertIn("escalat", reason)

    def test_verifier_cannot_de_escalate(self):
        prop = propose_level(
            domains=["identity"], proposed_by="author", proposed_level=3
        )
        out, err = confirm_or_escalate(
            prop, verifier="rev", confirmed_level=1
        )
        self.assertIsNone(out)
        self.assertEqual(err, "verifier_cannot_de_escalate")

    def test_verifier_can_escalate(self):
        prop = propose_level(
            domains=["api_behavior"], proposed_by="author", proposed_level=2
        )
        out, err = confirm_or_escalate(
            prop, verifier="rev", escalate_to=3, verifier_rationale="authz risk"
        )
        self.assertIsNone(err)
        self.assertEqual(out["final_level"], 3)
        self.assertEqual(out["status"], "escalated")

    def test_level2_rejects_console_only_pass(self):
        ok, reason = validate_evidence_for_level(
            2, implementer_console_only=True, verifier_run_results={"x": "ok"}
        )
        self.assertFalse(ok)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "iv.jsonl"
            with self.assertRaises(ValueError):
                record_verification(
                    verifier="r",
                    implementer="a",
                    scope="t",
                    suites=["s"],
                    result="PASS",
                    verification_level=2,
                    domains=["api_behavior"],
                    implementer_console_only=True,
                    verifier_run_results={"s": "PASS"},
                    path=path,
                )

    def test_level2_pass_with_verifier_results(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "iv.jsonl"
            rec = record_verification(
                verifier="r",
                implementer="a",
                scope="t",
                suites=["test_phase28_verification_levels"],
                result="PASS",
                verification_level=2,
                domains=["api_behavior"],
                risk_rationale="behavioral",
                verifier_run_results={
                    "test_phase28_verification_levels": "PASS",
                    "runner": "verifier",
                },
                path=path,
            )
            self.assertEqual(rec["verification_level"], 2)
            self.assertTrue(rec["verifier_run_results"])

    def test_level3_requires_context(self):
        ok, reason = validate_evidence_for_level(
            3,
            verifier_run_results={"s": "PASS"},
            execution_context="",
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "missing_execution_context_for_level3")

    def test_h1_does_not_touch_audit_admin(self):
        import inspect
        from identity_runtime import independent_verification as iv

        src = inspect.getsource(iv)
        self.assertNotIn("purge_expired_file", src)
        self.assertNotIn("identity_audit:admin", src)

    def test_validate_level_record(self):
        ok, _ = validate_level_record(
            {
                "verification_level": 2,
                "risk_rationale": "behavioral",
                "domains": ["api_behavior"],
                "expected_evidence": expected_evidence_for_level(2),
                "verifier": "r1",
            }
        )
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()