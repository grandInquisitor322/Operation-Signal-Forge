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

"""Phase 2.5 DID method policy tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.did_method_policy import (
    is_method_accepted,
    is_method_locally_managed,
    method_policy_summary,
    parse_did,
    validate_did_for_generation,
    validate_did_for_runtime,
)


class DidMethodPolicyTests(unittest.TestCase):
    def test_parse_did_key(self):
        method, mss, err = parse_did("did:key:z6Mkabcdef")
        self.assertIsNone(err)
        self.assertEqual(method, "key")
        self.assertTrue(mss.startswith("z"))

    def test_invalid_syntax(self):
        _, _, err = parse_did("not-a-did")
        self.assertEqual(err, "invalid_did_syntax")

    def test_accepted_key(self):
        self.assertTrue(is_method_accepted("key"))
        ok, reason = validate_did_for_runtime("did:key:z6Mkabcdef12")
        self.assertTrue(ok, reason)

    def test_unsupported_method(self):
        ok, reason = validate_did_for_runtime("did:example:123")
        self.assertFalse(ok)
        self.assertEqual(reason, "unsupported_did_method")

    def test_managed_subset(self):
        self.assertTrue(is_method_locally_managed("key"))
        ok, _ = validate_did_for_generation("did:key:z6Mkabcdef12")
        self.assertTrue(ok)

    def test_summary_boundaries(self):
        s = method_policy_summary()
        self.assertIn("key", s["accepted_methods"])
        self.assertFalse(s["external_resolver_required"])
        self.assertTrue(s["boundaries"]["resolution_is_not_issuer_trust"])
        self.assertTrue(s["boundaries"]["accepted_is_not_managed"])


if __name__ == "__main__":
    unittest.main()