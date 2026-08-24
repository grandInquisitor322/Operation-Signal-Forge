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
Audit log governance (Phase 2.6 G4 / Phase 2.7 H2).

Retention, least-privilege read access, integrity verification,
and privileged-admin meta-audit.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

TAMPER_EVIDENCE_DESIGN = {
    "mechanism": "hash_chained_jsonl",
    "algorithm": "SHA-256",
    "deployment_fit": "single_host_file_audit",
    "external_service_required": False,
    "retains_reusable_auth_material": False,
    "status": "approved_for_implementation",
}

AUDIT_READER_SCOPE = "identity_audit:read"
AUDIT_ADMIN_SCOPE = "identity_audit:admin"

_DEFAULT_RETENTION = {
    "challenge_issued": int(os.environ.get("SF_AUDIT_RETENTION_CHALLENGE", str(30 * 86400))),
    "presentation_success": int(os.environ.get("SF_AUDIT_RETENTION_SUCCESS", str(90 * 86400))),
    "presentation_failure": int(os.environ.get("SF_AUDIT_RETENTION_FAILURE", str(180 * 86400))),
    "nonce_consumed": int(os.environ.get("SF_AUDIT_RETENTION_NONCE", str(30 * 86400))),
    "recovery_event": int(os.environ.get("SF_AUDIT_RETENTION_RECOVERY", str(365 * 86400))),
    "privileged_audit_action": int(os.environ.get("SF_AUDIT_RETENTION_PRIV", str(365 * 86400))),
    "audit_integrity_failure": int(os.environ.get("SF_AUDIT_RETENTION_INTEGRITY", str(365 * 86400))),
    "default": int(os.environ.get("SF_AUDIT_RETENTION_DEFAULT", str(90 * 86400))),
}

GENESIS_HASH = "0" * 64


def retention_policy() -> dict[str, int]:
    return dict(_DEFAULT_RETENTION)


def retention_seconds_for_event(event: str) -> int:
    return _DEFAULT_RETENTION.get(event, _DEFAULT_RETENTION["default"])


def actor_may_read_audit(
    actor: str,
    *,
    authz: Optional[dict[str, Any]] = None,
) -> tuple[bool, str]:
    if not actor or not str(actor).strip():
        return False, "missing_audit_actor"
    if not authz:
        return False, "insufficient_audit_authority"
    scopes = authz.get("scopes") or []
    if AUDIT_READER_SCOPE in scopes or AUDIT_ADMIN_SCOPE in scopes:
        return True, "ok"
    if (authz.get("role") or "") in ("IdentityAuditReader", "IdentityAuditAdmin"):
        return True, "ok"
    return False, "insufficient_audit_authority"


def actor_may_admin_audit(
    actor: str,
    *,
    authz: Optional[dict[str, Any]] = None,
) -> tuple[bool, str]:
    if not actor or not str(actor).strip():
        return False, "missing_audit_actor"
    if not authz:
        return False, "insufficient_audit_admin_authority"
    scopes = authz.get("scopes") or []
    if AUDIT_ADMIN_SCOPE in scopes:
        return True, "ok"
    if (authz.get("role") or "") == "IdentityAuditAdmin":
        return True, "ok"
    return False, "insufficient_audit_admin_authority"


def _parse_ts(iso: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except Exception:
        return None


def _integrity_payload(rec: dict[str, Any], prev_hash: str) -> bytes:
    body = {k: v for k, v in rec.items() if k not in ("entry_hash", "prev_hash")}
    body["_prev"] = prev_hash
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode(
        "utf-8"
    )


def compute_entry_hash(rec: dict[str, Any], prev_hash: str) -> str:
    return hashlib.sha256(_integrity_payload(rec, prev_hash)).hexdigest()


def seal_record(rec: dict[str, Any], prev_hash: str) -> dict[str, Any]:
    out = dict(rec)
    out["prev_hash"] = prev_hash
    out["entry_hash"] = compute_entry_hash(out, prev_hash)
    return out


def verify_chain(records: list[dict[str, Any]]) -> tuple[bool, str]:
    prev = GENESIS_HASH
    for i, rec in enumerate(records):
        if rec.get("prev_hash") != prev:
            return False, f"chain_break_at_{i}_prev_mismatch"
        expected = compute_entry_hash(rec, prev)
        if rec.get("entry_hash") != expected:
            return False, f"chain_break_at_{i}_hash_mismatch"
        prev = rec["entry_hash"]
    return True, "ok"


def filter_expired(
    records: list[dict[str, Any]], *, now: Optional[datetime] = None
) -> tuple[list[dict[str, Any]], int]:
    now = now or datetime.now(timezone.utc)
    kept: list[dict[str, Any]] = []
    purged = 0
    for rec in records:
        event = rec.get("event") or "default"
        ts = _parse_ts(rec.get("timestamp") or "")
        if ts is None:
            kept.append(rec)
            continue
        max_age = retention_seconds_for_event(str(event))
        if ts + timedelta(seconds=max_age) < now:
            purged += 1
            continue
        kept.append(rec)
    return kept, purged


def log_privileged_audit_action(
    *,
    actor: str,
    operation: str,
    detail: str = "",
    path: Optional[Path] = None,
) -> None:
    """H2 — Meta-audit of identity_audit:admin. Metadata only."""
    try:
        from identity_runtime.presentation_audit import log_event

        log_event(
            "privileged_audit_action",
            path=path,
            actor=actor,
            operation=operation,
            detail=detail or None,
        )
    except Exception:
        pass


def read_audit_authorized(
    path: Path,
    *,
    actor: str,
    authz: Optional[dict[str, Any]] = None,
    limit: int = 200,
) -> tuple[Optional[list[dict[str, Any]]], Optional[str]]:
    ok, reason = actor_may_read_audit(actor, authz=authz)
    if not ok:
        return None, reason
    scopes = (authz or {}).get("scopes") or []
    if AUDIT_ADMIN_SCOPE in scopes or (authz or {}).get("role") == "IdentityAuditAdmin":
        log_privileged_audit_action(
            actor=actor,
            operation="admin_read_audit",
            detail=str(path),
            path=path,
        )
    if not path.exists():
        return [], None
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records[-limit:], None


def purge_expired_file(
    path: Path,
    *,
    actor: str,
    authz: Optional[dict[str, Any]] = None,
) -> tuple[int, Optional[str]]:
    """Admin-only rewrite keeping non-expired records; reseals chain from genesis."""
    ok, reason = actor_may_admin_audit(actor, authz=authz)
    if not ok:
        return 0, reason
    log_privileged_audit_action(
        actor=actor,
        operation="purge_expired_audit",
        detail=str(path),
        path=path,
    )
    if not path.exists():
        return 0, None
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    kept, purged = filter_expired(records)
    prev = GENESIS_HASH
    sealed: list[dict[str, Any]] = []
    for rec in kept:
        base = {k: v for k, v in rec.items() if k not in ("prev_hash", "entry_hash")}
        s = seal_record(base, prev)
        sealed.append(s)
        prev = s["entry_hash"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in sealed:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
    return purged, None