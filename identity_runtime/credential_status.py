"""
Credential status / revocation store (interim file-backed).

Checked during present_credential BEFORE Authorization Matrix mapping.
Does not touch Fusion Engine or Capability Layer.

Status values: active | revoked
"""

from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DEFAULT_PATH = (
    Path(__file__).resolve().parent.parent / "dapp_api" / "credential_status.json"
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_credential_id() -> str:
    return f"urn:uuid:{secrets.token_hex(16)}"


def load_status_db(path: Optional[Path] = None) -> dict[str, Any]:
    p = path or DEFAULT_PATH
    if not p.exists():
        return {"credentials": {}}
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    if "credentials" not in data:
        data = {"credentials": data if isinstance(data, dict) else {}}
    return data


def save_status_db(data: dict[str, Any], path: Optional[Path] = None) -> None:
    p = path or DEFAULT_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8-sig")


def register_active(
    credential_id: str,
    *,
    issuer_did: str,
    subject_id: str,
    credential_type: str,
    path: Optional[Path] = None,
    replaces: Optional[str] = None,
) -> None:
    db = load_status_db(path)
    db["credentials"][credential_id] = {
        "status": "active",
        "issuer_did": issuer_did,
        "subject_id": subject_id,
        "credential_type": credential_type,
        "issued_at": _now_iso(),
        "revoked_at": None,
        "revocation_reason": None,
    }
    save_status_db(db, path)


def revoke(
    credential_id: str,
    *,
    reason: str = "unspecified",
    path: Optional[Path] = None,
) -> tuple[bool, str]:
    """Mark credential revoked. Idempotent if already revoked."""
    if not credential_id:
        return False, "missing_credential_id"
    db = load_status_db(path)
    entry = db["credentials"].get(credential_id)
    if entry is None:
        db["credentials"][credential_id] = {
            "status": "revoked",
            "issuer_did": None,
            "subject_id": None,
            "credential_type": None,
            "issued_at": None,
            "revoked_at": _now_iso(),
            "revocation_reason": reason,
        }
        save_status_db(db, path)
        return True, "revoked_untracked"
    if entry.get("status") == "revoked":
        return True, "already_revoked"
    entry["status"] = "revoked"
    entry["revoked_at"] = _now_iso()
    entry["revocation_reason"] = reason
    save_status_db(db, path)
    return True, "revoked"


def check_status(
    credential_id: Optional[str], path: Optional[Path] = None
) -> tuple[bool, str]:
    """
    Returns (allowed, reason).
    - No id → deny
    - Unknown id → allow unless SF_STRICT_CREDENTIAL_STATUS=1
    - active → allow
    - revoked → deny
    """
    if not credential_id:
        return False, "missing_credential_id"
    db = load_status_db(path)
    entry = db["credentials"].get(credential_id)
    if entry is None:
        if os.environ.get("SF_STRICT_CREDENTIAL_STATUS", "").lower() in (
            "1",
            "true",
            "yes",
        ):
            return False, "credential_status_unknown"
        return True, "unknown_not_listed"
    status = entry.get("status") or "active"
    if status == "revoked":
        return False, "credential_revoked"
    if status != "active":
        return False, f"credential_status_{status}"
    return True, "active"


def get_entry(
    credential_id: str, path: Optional[Path] = None
) -> Optional[dict[str, Any]]:
    return load_status_db(path)["credentials"].get(credential_id)