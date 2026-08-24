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
Trust Registry — authoritative issuer trust + Phase 2.3 governance.

Answers: Is this issuer trusted to issue this credential type *right now*?

Does NOT answer holder authorization (Authorization Matrix).
Does NOT track per-credential status (credential_status.py).

Governance mutations require TrustRegistryAdmin authority
(see require_governance_authority).

Lifecycle:
  proposed → under_review → active ⇄ suspended
                         ↘ revoked (terminal for this registration)
"""

from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "dapp_api" / "trust_registry.json"
AUDIT_PATH = Path(__file__).resolve().parent.parent / "dapp_api" / "trust_registry_audit.jsonl"
ADMINS_PATH = (
    Path(__file__).resolve().parent.parent / "dapp_api" / "trust_governance_admins.json"
)

VALID_STATUSES = frozenset(
    {"proposed", "under_review", "active", "suspended", "revoked"}
)

UNTRUSTED_STATUSES = frozenset({"proposed", "under_review", "suspended", "revoked"})

TRUST_REGISTRY_ADMIN_SCOPE = "trust_registry:admin"
TRUST_REGISTRY_ADMIN_ROLE = "TrustRegistryAdmin"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Governance authorization
# ---------------------------------------------------------------------------


def load_governance_admins(path: Optional[Path] = None) -> list[dict[str, Any]]:
    p = path or ADMINS_PATH
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        return data
    return list(data.get("admins") or [])


def save_governance_admins(
    admins: list[dict[str, Any]], path: Optional[Path] = None
) -> None:
    p = path or ADMINS_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"admins": admins}, indent=2), encoding="utf-8")


def _actor_in_admin_list(actor: str, path: Optional[Path] = None) -> bool:
    if not actor:
        return False
    actor_l = actor.strip().lower()
    for row in load_governance_admins(path):
        rid = (row.get("id") or row.get("did") or row.get("email") or "").strip().lower()
        if rid and rid == actor_l:
            return True
    return False


def _authz_has_admin(authz: Optional[dict[str, Any]]) -> bool:
    if not authz:
        return False
    scopes = authz.get("scopes") or []
    if TRUST_REGISTRY_ADMIN_SCOPE in scopes:
        return True
    role = authz.get("role") or ""
    if role == TRUST_REGISTRY_ADMIN_ROLE:
        return True
    return False


def require_governance_authority(
    actor: str,
    *,
    authz: Optional[dict[str, Any]] = None,
    admins_path: Optional[Path] = None,
    action: str = "govern",
) -> tuple[bool, str]:
    """
    Allow if ANY of:
      1. authz has trust_registry:admin scope or TrustRegistryAdmin role
      2. actor is listed in trust_governance_admins.json
      3. Bootstrap: no admins configured AND actor == SF_TRUST_BOOTSTRAP_ACTOR
    """
    if not actor or not str(actor).strip():
        return False, "missing_governance_actor"

    if _authz_has_admin(authz):
        subject = (authz or {}).get("subject_id") or (authz or {}).get("email") or ""
        if subject and subject.strip().lower() != actor.strip().lower():
            return False, "actor_authz_subject_mismatch"
        return True, "ok_authz"

    if _actor_in_admin_list(actor, admins_path):
        return True, "ok_admin_list"

    admins = load_governance_admins(admins_path)
    bootstrap = (os.environ.get("SF_TRUST_BOOTSTRAP_ACTOR") or "").strip()
    if not admins and bootstrap and bootstrap.lower() == actor.strip().lower():
        return True, "ok_bootstrap"

    return False, "insufficient_governance_authority"


def _enforce_gov(
    actor: str,
    *,
    authz: Optional[dict[str, Any]],
    admins_path: Optional[Path],
    action: str,
) -> Optional[str]:
    ok, reason = require_governance_authority(
        actor, authz=authz, admins_path=admins_path, action=action
    )
    if not ok:
        return reason
    return None


def register_governance_admin(
    *,
    admin_id: str,
    name: str = "",
    actor: str,
    authz: Optional[dict[str, Any]] = None,
    admins_path: Optional[Path] = None,
) -> tuple[bool, str]:
    err = _enforce_gov(
        actor, authz=authz, admins_path=admins_path, action="register_admin"
    )
    if err:
        return False, err
    if not admin_id:
        return False, "missing_admin_id"
    admins = load_governance_admins(admins_path)
    if any((a.get("id") or "").lower() == admin_id.strip().lower() for a in admins):
        return False, "admin_already_registered"
    admins.append(
        {
            "id": admin_id.strip(),
            "name": name or admin_id,
            "registered_at": _now_iso(),
            "registered_by": actor,
        }
    )
    save_governance_admins(admins, admins_path)
    return True, "admin_registered"


# ---------------------------------------------------------------------------
# Registry load / save / query
# ---------------------------------------------------------------------------


def load_registry(path: Optional[Path] = None) -> list[dict[str, Any]]:
    p = path or DEFAULT_PATH
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8-sig"))


def save_registry(entries: list[dict[str, Any]], path: Optional[Path] = None) -> None:
    p = path or DEFAULT_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def find_issuer(
    issuer_did: str, path: Optional[Path] = None
) -> Optional[dict[str, Any]]:
    for entry in load_registry(path):
        if entry.get("issuer_did") == issuer_did:
            return entry
    return None


def issuer_allows_type(
    issuer_did: str, credential_type: str, path: Optional[Path] = None
) -> tuple[bool, str]:
    """Read-only runtime check — no governance actor required."""
    entry = find_issuer(issuer_did, path)
    if entry is None:
        return False, "issuer_not_trusted"
    status = (entry.get("status") or "").lower()
    if status != "active":
        return False, f"issuer_{status or 'unknown'}"
    allowed = entry.get("allowed_credential_types") or []
    if credential_type not in allowed:
        return False, "issuer_type_not_allowed"
    return True, "ok"


def _append_audit(
    record: dict[str, Any], audit_path: Optional[Path] = None
) -> None:
    p = audit_path or AUDIT_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def _audit(
    *,
    action: str,
    actor: str,
    issuer_did: str,
    previous_state: Optional[str],
    resulting_state: str,
    reason: str = "",
    allowed_credential_types: Optional[list[str]] = None,
    governance_reference: str = "",
    emergency: bool = False,
    audit_path: Optional[Path] = None,
    authority: str = "",
) -> dict[str, Any]:
    rec = {
        "audit_id": secrets.token_hex(8),
        "timestamp": _now_iso(),
        "action": action,
        "actor": actor,
        "authority": authority,
        "issuer_did": issuer_did,
        "previous_state": previous_state,
        "resulting_state": resulting_state,
        "reason": reason,
        "allowed_credential_types": allowed_credential_types,
        "governance_reference": governance_reference,
        "emergency": emergency,
    }
    _append_audit(rec, audit_path)
    return rec


# ---------------------------------------------------------------------------
# Governance mutations
# ---------------------------------------------------------------------------


def propose_issuer(
    *,
    issuer_did: str,
    display_name: str,
    requested_credential_types: list[str],
    actor: str,
    authz: Optional[dict[str, Any]] = None,
    organization: str = "",
    governance_reference: str = "",
    reason: str = "onboarding_request",
    path: Optional[Path] = None,
    audit_path: Optional[Path] = None,
    admins_path: Optional[Path] = None,
) -> tuple[bool, str, Optional[dict[str, Any]]]:
    auth_err = _enforce_gov(actor, authz=authz, admins_path=admins_path, action="propose")
    if auth_err:
        return False, auth_err, None
    if not issuer_did:
        return False, "missing_issuer_did", None
    if find_issuer(issuer_did, path) is not None:
        return False, "issuer_already_registered", None
    if not requested_credential_types:
        return False, "missing_requested_types", None

    _, authority = require_governance_authority(actor, authz=authz, admins_path=admins_path)
    entry = {
        "issuer_did": issuer_did,
        "display_name": display_name or issuer_did,
        "organization": organization,
        "status": "proposed",
        "allowed_credential_types": [],
        "requested_credential_types": list(requested_credential_types),
        "revocation_method": "status_list",
        "proposed_at": _now_iso(),
        "proposed_by": actor,
        "approved_at": None,
        "approved_by": None,
        "governance_reference": governance_reference,
        "effective_from": None,
        "last_reviewed_at": _now_iso(),
        "notes": reason,
    }
    reg = load_registry(path)
    reg.append(entry)
    save_registry(reg, path)
    _audit(
        action="propose",
        actor=actor,
        issuer_did=issuer_did,
        previous_state=None,
        resulting_state="proposed",
        reason=reason,
        allowed_credential_types=[],
        governance_reference=governance_reference,
        audit_path=audit_path,
        authority=authority,
    )
    return True, "proposed", entry


def mark_under_review(
    issuer_did: str,
    *,
    actor: str,
    authz: Optional[dict[str, Any]] = None,
    reason: str = "governance_review",
    governance_reference: str = "",
    path: Optional[Path] = None,
    audit_path: Optional[Path] = None,
    admins_path: Optional[Path] = None,
) -> tuple[bool, str]:
    auth_err = _enforce_gov(
        actor, authz=authz, admins_path=admins_path, action="mark_under_review"
    )
    if auth_err:
        return False, auth_err
    return _transition(
        issuer_did,
        allowed_from={"proposed", "under_review", "suspended"},
        new_status="under_review",
        action="mark_under_review",
        actor=actor,
        authz=authz,
        reason=reason,
        governance_reference=governance_reference,
        path=path,
        audit_path=audit_path,
        admins_path=admins_path,
    )


def approve_issuer(
    issuer_did: str,
    *,
    actor: str,
    allowed_credential_types: list[str],
    authz: Optional[dict[str, Any]] = None,
    reason: str = "approved",
    governance_reference: str = "",
    path: Optional[Path] = None,
    audit_path: Optional[Path] = None,
    admins_path: Optional[Path] = None,
) -> tuple[bool, str]:
    auth_err = _enforce_gov(actor, authz=authz, admins_path=admins_path, action="approve")
    if auth_err:
        return False, auth_err
    if not allowed_credential_types:
        return False, "approval_requires_credential_types"
    entry = find_issuer(issuer_did, path)
    if entry is None:
        return False, "issuer_not_found"
    prev = entry.get("status")
    if prev not in ("proposed", "under_review", "suspended", "active"):
        if prev == "revoked":
            return False, "cannot_approve_revoked_use_new_registration"
        return False, f"cannot_approve_from_{prev}"

    _, authority = require_governance_authority(actor, authz=authz, admins_path=admins_path)
    reg = load_registry(path)
    for e in reg:
        if e.get("issuer_did") == issuer_did:
            e["status"] = "active"
            e["allowed_credential_types"] = list(allowed_credential_types)
            e["approved_at"] = _now_iso()
            e["approved_by"] = actor
            e["effective_from"] = e.get("effective_from") or _now_iso()[:10]
            e["last_reviewed_at"] = _now_iso()
            if governance_reference:
                e["governance_reference"] = governance_reference
            e["notes"] = reason
            break
    save_registry(reg, path)
    _audit(
        action="approve",
        actor=actor,
        issuer_did=issuer_did,
        previous_state=prev,
        resulting_state="active",
        reason=reason,
        allowed_credential_types=list(allowed_credential_types),
        governance_reference=governance_reference,
        audit_path=audit_path,
        authority=authority,
    )
    return True, "active"


def suspend_issuer(
    issuer_did: str,
    *,
    actor: str,
    authz: Optional[dict[str, Any]] = None,
    reason: str = "suspended",
    governance_reference: str = "",
    emergency: bool = False,
    path: Optional[Path] = None,
    audit_path: Optional[Path] = None,
    admins_path: Optional[Path] = None,
) -> tuple[bool, str]:
    auth_err = _enforce_gov(actor, authz=authz, admins_path=admins_path, action="suspend")
    if auth_err:
        return False, auth_err
    return _transition(
        issuer_did,
        allowed_from={"active", "under_review", "proposed"},
        new_status="suspended",
        action="emergency_suspend" if emergency else "suspend",
        actor=actor,
        authz=authz,
        reason=reason,
        governance_reference=governance_reference,
        emergency=emergency,
        path=path,
        audit_path=audit_path,
        admins_path=admins_path,
    )


def restore_issuer(
    issuer_did: str,
    *,
    actor: str,
    authz: Optional[dict[str, Any]] = None,
    reason: str = "restored_after_review",
    governance_reference: str = "",
    path: Optional[Path] = None,
    audit_path: Optional[Path] = None,
    admins_path: Optional[Path] = None,
) -> tuple[bool, str]:
    auth_err = _enforce_gov(actor, authz=authz, admins_path=admins_path, action="restore")
    if auth_err:
        return False, auth_err
    entry = find_issuer(issuer_did, path)
    if entry is None:
        return False, "issuer_not_found"
    if entry.get("status") != "suspended":
        return False, f"cannot_restore_from_{entry.get('status')}"
    if not entry.get("allowed_credential_types"):
        return False, "restore_requires_existing_allowed_types"
    return _transition(
        issuer_did,
        allowed_from={"suspended"},
        new_status="active",
        action="restore",
        actor=actor,
        authz=authz,
        reason=reason,
        governance_reference=governance_reference,
        path=path,
        audit_path=audit_path,
        admins_path=admins_path,
    )


def revoke_issuer(
    issuer_did: str,
    *,
    actor: str,
    authz: Optional[dict[str, Any]] = None,
    reason: str = "revoked",
    governance_reference: str = "",
    emergency: bool = False,
    path: Optional[Path] = None,
    audit_path: Optional[Path] = None,
    admins_path: Optional[Path] = None,
) -> tuple[bool, str]:
    auth_err = _enforce_gov(
        actor, authz=authz, admins_path=admins_path, action="revoke_issuer"
    )
    if auth_err:
        return False, auth_err
    return _transition(
        issuer_did,
        allowed_from={"active", "suspended", "under_review", "proposed"},
        new_status="revoked",
        action="emergency_revoke" if emergency else "revoke_issuer",
        actor=actor,
        authz=authz,
        reason=reason,
        governance_reference=governance_reference,
        emergency=emergency,
        path=path,
        audit_path=audit_path,
        admins_path=admins_path,
    )


def set_allowed_types(
    issuer_did: str,
    *,
    actor: str,
    allowed_credential_types: list[str],
    authz: Optional[dict[str, Any]] = None,
    reason: str = "update_types",
    governance_reference: str = "",
    path: Optional[Path] = None,
    audit_path: Optional[Path] = None,
    admins_path: Optional[Path] = None,
) -> tuple[bool, str]:
    auth_err = _enforce_gov(
        actor, authz=authz, admins_path=admins_path, action="set_allowed_types"
    )
    if auth_err:
        return False, auth_err
    entry = find_issuer(issuer_did, path)
    if entry is None:
        return False, "issuer_not_found"
    if entry.get("status") == "revoked":
        return False, "cannot_update_revoked_issuer"
    prev = entry.get("status")
    prev_types = list(entry.get("allowed_credential_types") or [])
    _, authority = require_governance_authority(actor, authz=authz, admins_path=admins_path)
    reg = load_registry(path)
    for e in reg:
        if e.get("issuer_did") == issuer_did:
            e["allowed_credential_types"] = list(allowed_credential_types)
            e["last_reviewed_at"] = _now_iso()
            break
    save_registry(reg, path)
    _audit(
        action="set_allowed_types",
        actor=actor,
        issuer_did=issuer_did,
        previous_state=prev,
        resulting_state=prev,
        reason=f"{reason}; was={prev_types}",
        allowed_credential_types=list(allowed_credential_types),
        governance_reference=governance_reference,
        audit_path=audit_path,
        authority=authority,
    )
    return True, "updated"


def _transition(
    issuer_did: str,
    *,
    allowed_from: set[str],
    new_status: str,
    action: str,
    actor: str,
    authz: Optional[dict[str, Any]] = None,
    reason: str,
    governance_reference: str = "",
    emergency: bool = False,
    path: Optional[Path] = None,
    audit_path: Optional[Path] = None,
    admins_path: Optional[Path] = None,
) -> tuple[bool, str]:
    entry = find_issuer(issuer_did, path)
    if entry is None:
        return False, "issuer_not_found"
    prev = entry.get("status")
    if prev not in allowed_from:
        return False, f"cannot_{action}_from_{prev}"
    if prev == "revoked" and new_status != "revoked":
        return False, "revoked_is_terminal"
    _, authority = require_governance_authority(actor, authz=authz, admins_path=admins_path)
    reg = load_registry(path)
    for e in reg:
        if e.get("issuer_did") == issuer_did:
            e["status"] = new_status
            e["last_reviewed_at"] = _now_iso()
            e["notes"] = reason
            if governance_reference:
                e["governance_reference"] = governance_reference
            break
    save_registry(reg, path)
    types = list(
        (find_issuer(issuer_did, path) or {}).get("allowed_credential_types") or []
    )
    _audit(
        action=action,
        actor=actor,
        issuer_did=issuer_did,
        previous_state=prev,
        resulting_state=new_status,
        reason=reason,
        allowed_credential_types=types,
        governance_reference=governance_reference,
        emergency=emergency,
        audit_path=audit_path,
        authority=authority,
    )
    return True, new_status


def load_audit(audit_path: Optional[Path] = None) -> list[dict[str, Any]]:
    p = audit_path or AUDIT_PATH
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out