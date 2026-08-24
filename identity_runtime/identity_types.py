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
Person / Organization / Role data model (Phase 2.4).

Does not implement HR workflows — structural distinctions only.
"""

from __future__ import annotations

from typing import Any, Optional

IDENTITY_KINDS = frozenset({"Person", "Organization", "Role"})


def person(
    *, did: str, name: str = "", also_known_as: Optional[list[str]] = None
) -> dict[str, Any]:
    return {
        "kind": "Person",
        "did": did,
        "name": name,
        "alsoKnownAs": list(also_known_as or []),
    }


def organization(
    *, did: str, name: str = "", also_known_as: Optional[list[str]] = None
) -> dict[str, Any]:
    return {
        "kind": "Organization",
        "did": did,
        "name": name,
        "alsoKnownAs": list(also_known_as or []),
    }


def role(
    *,
    role_id: str,
    name: str,
    organization_did: str,
    description: str = "",
) -> dict[str, Any]:
    return {
        "kind": "Role",
        "roleId": role_id,
        "name": name,
        "organizationDid": organization_did,
        "description": description,
    }


def membership(
    *,
    person_did: str,
    organization_did: str,
    role_id: Optional[str] = None,
    status: str = "active",
) -> dict[str, Any]:
    """Person ↔ Organization (+ optional Role). Not a credential."""
    return {
        "kind": "Membership",
        "personDid": person_did,
        "organizationDid": organization_did,
        "roleId": role_id,
        "status": status,
    }


def validate_identity_record(rec: dict[str, Any]) -> tuple[bool, str]:
    kind = rec.get("kind")
    if kind not in IDENTITY_KINDS and kind != "Membership":
        return False, "unknown_identity_kind"
    if kind in ("Person", "Organization"):
        if not rec.get("did"):
            return False, "missing_did"
    if kind == "Role":
        if not rec.get("roleId") or not rec.get("organizationDid"):
            return False, "incomplete_role"
    if kind == "Membership":
        if not rec.get("personDid") or not rec.get("organizationDid"):
            return False, "incomplete_membership"
        if rec.get("personDid") == rec.get("organizationDid"):
            return False, "person_org_must_differ"
    return True, "ok"