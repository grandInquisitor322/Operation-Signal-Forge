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

"""
DID method policy (Phase 2.5).

Accepted methods  ≠  locally managed methods
DID resolution    ≠  issuer trust
DID resolution    ≠  authorization

Policy only — does not call Trust Registry or Authorization Matrix.
"""

from __future__ import annotations

import re
from typing import Any, Optional

# Methods the Identity Runtime may validate / resolve under local policy.
ACCEPTED_DID_METHODS: dict[str, dict[str, Any]] = {
    "key": {
        "name": "did:key",
        "syntax_prefix": "did:key:",
        "key_types": ["Ed25519"],
        "verification_relationships": ["authentication", "assertionMethod"],
        "resolution": "local_or_deterministic",
        "notes": "Interim default; multibase embedded in identifier.",
    },
}

# Methods Signal Forge is willing to generate / manage (narrower set).
LOCALLY_MANAGED_DID_METHODS: dict[str, dict[str, Any]] = {
    "key": {
        "generate": True,
        "rotate_verification_material": True,
        "notes": "Document-centric key rotation may keep DID string stable.",
    },
}

_DID_PATTERN = re.compile(r"^did:([a-z0-9]+):(.+)$", re.IGNORECASE)


def parse_did(did: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Returns (method, method_specific_id, error).
    error is None on success.
    """
    if not did or not isinstance(did, str):
        return None, None, "invalid_did"
    m = _DID_PATTERN.match(did.strip())
    if not m:
        return None, None, "invalid_did_syntax"
    method = m.group(1).lower()
    mss = m.group(2)
    if not mss:
        return None, None, "invalid_did_syntax"
    return method, mss, None


def is_method_accepted(method: str) -> bool:
    return method.lower() in ACCEPTED_DID_METHODS


def is_method_locally_managed(method: str) -> bool:
    return method.lower() in LOCALLY_MANAGED_DID_METHODS


def validate_did_for_runtime(did: str) -> tuple[bool, str]:
    """
    Fail-safe gate before resolution/binding.
    Reject unknown methods; do not degrade to anonymous.
    """
    method, mss, err = parse_did(did)
    if err:
        return False, err
    assert method is not None
    if not is_method_accepted(method):
        return False, "unsupported_did_method"
    if method == "key":
        if not mss or len(mss) < 8:
            return False, "invalid_did_key_identifier"
    return True, "ok"


def validate_did_for_generation(did: str) -> tuple[bool, str]:
    """True only if method is both accepted and locally managed."""
    method, _, err = parse_did(did)
    if err:
        return False, err
    assert method is not None
    if not is_method_accepted(method):
        return False, "unsupported_did_method"
    if not is_method_locally_managed(method):
        return False, "did_method_not_locally_managed"
    return True, "ok"


def method_policy_summary() -> dict[str, Any]:
    """Introspection for docs / admin UI — not trust decisions."""
    return {
        "accepted_methods": sorted(ACCEPTED_DID_METHODS.keys()),
        "locally_managed_methods": sorted(LOCALLY_MANAGED_DID_METHODS.keys()),
        "resolution_baseline": "local",
        "external_resolver_required": False,
        "boundaries": {
            "resolution_is_not_issuer_trust": True,
            "resolution_is_not_authorization": True,
            "accepted_is_not_managed": True,
        },
    }


def future_expansion_criteria() -> list[str]:
    """Criteria doc — not a commitment to any network."""
    return [
        "Security review of method and key types",
        "Resolution strategy without mandatory single-vendor dependency",
        "No Trust Registry or Authorization Matrix schema break",
        "Automated tests for parse, validate, resolve, and fail-safe reject",
        "Clear accept vs manage policy update with governance approval",
    ]