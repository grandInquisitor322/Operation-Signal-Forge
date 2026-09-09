# Copyright 2026 Operation Signal Forge contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Gate 5 — fail-closed C1-C4 acceptance control-flow tests."""
from __future__ import annotations

import unittest

from identity_runtime.fail_closed_verifier import (
    CheckResult,
    CheckStatus,
    VerificationStatus,
    verify_fail_closed,
)


def _check(condition: str, status: CheckStatus = CheckStatus.PASS) -> CheckResult:
    return CheckResult(condition=condition, status=status)


class Gate5FailClosedTests(unittest.TestCase):
    def test_all_c1_c4_pass_emits_verified_claim(self):
        result = verify_fail_closed(
            c1=_check("C1"), c2=_check("C2"), c3=_check("C3"), c4=_check("C4")
        )
        self.assertEqual(result.status, VerificationStatus.VERIFIED_ELIGIBILITY)
        self.assertTrue(result.verified_eligibility_claim)
        self.assertTrue(result.authorization_permitted)

    def test_each_condition_failure_blocks_claim_and_authorization(self):
        for condition in ("C1", "C2", "C3", "C4"):
            checks = {name: _check(name) for name in ("C1", "C2", "C3", "C4")}
            checks[condition] = _check(condition, CheckStatus.FAIL)
            result = verify_fail_closed(**{k.lower(): v for k, v in checks.items()})
            self.assertEqual(result.status, VerificationStatus.CLAIM_NOT_SATISFIED)
            self.assertFalse(result.verified_eligibility_claim)
            self.assertFalse(result.authorization_permitted)
            self.assertEqual(result.failed_condition, condition)

    def test_non_pass_states_are_fail_closed(self):
        for status in (
            CheckStatus.AMBIGUOUS,
            CheckStatus.UNSUPPORTED,
            CheckStatus.MALFORMED,
            CheckStatus.UNVERIFIABLE,
        ):
            result = verify_fail_closed(
                c1=_check("C1"),
                c2=_check("C2"),
                c3=_check("C3"),
                c4=_check("C4", status),
            )
            self.assertEqual(result.status, VerificationStatus.CLAIM_NOT_SATISFIED)
            self.assertFalse(result.verified_eligibility_claim)
            self.assertFalse(result.authorization_permitted)

    def test_missing_or_duplicate_condition_cannot_reach_acceptance(self):
        with self.assertRaises(ValueError):
            from identity_runtime.fail_closed_verifier import _validate_checks
            _validate_checks((_check("C1"), _check("C2"), _check("C3")))

        with self.assertRaises(ValueError):
            from identity_runtime.fail_closed_verifier import _validate_checks
            _validate_checks((_check("C1"), _check("C2"), _check("C3"), _check("C3")))


if __name__ == "__main__":
    unittest.main()
