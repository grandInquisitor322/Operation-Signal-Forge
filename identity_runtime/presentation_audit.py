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
Presentation / binding audit metadata (Phase 2.5 / 2.6).

Governing principle:
  Log evidence that an authentication event occurred,
  not reusable authentication material.

Phase 2.6: records are hash-chained for tamper-evidence (see audit_governance).
"""

from __future__ import annotations

import hashlib
import json
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DEFAULT_PATH = (
    Path(__file__).resolve().parent.parent / "dapp_api" / "presentation_audit.jsonl"
)

_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fingerprint(value: str, *, prefix_len: int = 16) -> str:
    if not value:
        return ""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:prefix_len]


def _last_entry_hash(path: Path) -> str:
    from identity_runtime.audit_governance import GENESIS_HASH

    if not path.exists():
        return GENESIS_HASH
    last = None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            last = line
    if not last:
        return GENESIS_HASH
    try:
        rec = json.loads(last)
        return rec.get("entry_hash") or GENESIS_HASH
    except Exception:
        return GENESIS_HASH


def _append(record: dict[str, Any], path: Optional[Path] = None) -> None:
    from identity_runtime.audit_governance import seal_record

    p = path or DEFAULT_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    forbidden = {
        "signature",
        "proof",
        "private_key",
        "nonce",
        "credential",
        "envelope",
        "did_document",
        "raw_proof",
    }
    safe = {k: v for k, v in record.items() if k not in forbidden}
    with _lock:
        prev = _last_entry_hash(p)
        sealed = seal_record(safe, prev)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(sealed, sort_keys=True) + "\n")


def log_event(
    event: str,
    *,
    path: Optional[Path] = None,
    **fields: Any,
) -> dict[str, Any]:
    rec = {
        "audit_id": secrets.token_hex(8),
        "timestamp": _now(),
        "event": event,
        **fields,
    }
    _append(rec, path)
    return rec


def log_challenge_issued(
    *,
    audience: str,
    expires_at: str = "",
    nonce: str = "",
    path: Optional[Path] = None,
) -> dict[str, Any]:
    return log_event(
        "challenge_issued",
        path=path,
        audience=audience,
        expires_at=expires_at or None,
        nonce_fingerprint=fingerprint(nonce) if nonce else None,
    )


def log_presentation_attempt(
    *,
    credential_id: str = "",
    subject_did: str = "",
    issuer_did: str = "",
    binding_required: bool = False,
    path: Optional[Path] = None,
) -> dict[str, Any]:
    return log_event(
        "presentation_attempt",
        path=path,
        credential_id=credential_id or None,
        subject_did=subject_did or None,
        issuer_did=issuer_did or None,
        binding_required=binding_required,
    )


def log_presentation_result(
    *,
    success: bool,
    reason: str = "",
    credential_id: str = "",
    subject_did: str = "",
    issuer_did: str = "",
    verification_method_id: str = "",
    nonce: str = "",
    path: Optional[Path] = None,
) -> dict[str, Any]:
    event = "presentation_success" if success else "presentation_failure"
    return log_event(
        event,
        path=path,
        success=success,
        reason=reason or None,
        credential_id=credential_id or None,
        subject_did=subject_did or None,
        issuer_did=issuer_did or None,
        verification_method_id=verification_method_id or None,
        nonce_fingerprint=fingerprint(nonce) if nonce else None,
    )


def log_nonce_consumed(
    *,
    audience: str,
    nonce: str = "",
    path: Optional[Path] = None,
) -> dict[str, Any]:
    return log_event(
        "nonce_consumed",
        path=path,
        audience=audience,
        nonce_fingerprint=fingerprint(nonce) if nonce else None,
    )


def log_recovery_event(
    *,
    recovery_id: str,
    subject_did: str,
    trigger: str,
    status: str,
    requester: str = "",
    approver: str = "",
    methods_retired: Optional[list] = None,
    method_activated: str = "",
    reason: str = "",
    path: Optional[Path] = None,
) -> dict[str, Any]:
    return log_event(
        "recovery_event",
        path=path,
        recovery_id=recovery_id,
        subject_did=subject_did,
        trigger=trigger,
        status=status,
        requester=requester or None,
        approver=approver or None,
        methods_retired=methods_retired or [],
        method_activated=method_activated or None,
        reason=reason or None,
    )


def read_audit_log(
    path: Optional[Path] = None, *, limit: int = 100
) -> list[dict[str, Any]]:
    """Low-level read for tests. Production reads should use read_audit_authorized."""
    p = path or DEFAULT_PATH
    if not p.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines()[-limit:]:
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out