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
Phase 2.2 — Credential renewal & rotation.

Renewal = issue a NEW credential (B). Never mutate credential A.
B must pass the normal present_credential pipeline independently.
Revocation of A is never reversed by issuing B.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from identity_runtime.credential_status import (
    check_status,
    get_entry,
    new_credential_id,
    register_active,
    revoke,
)
from identity_runtime.envelope import sign_envelope, verify_envelope
from identity_runtime.trust_registry import issuer_allows_type

# Default: renew when within this many days of expiration (or already past if allow_expired)
DEFAULT_RENEWAL_WINDOW_DAYS = 30


def _parse_exp(exp: Optional[str]) -> Optional[datetime]:
    if not exp:
        return None
    try:
        return datetime.fromisoformat(exp.replace("Z", "+00:00"))
    except ValueError:
        return None


def check_renewal_eligibility(
    envelope: dict[str, Any],
    *,
    renewal_window_days: int = DEFAULT_RENEWAL_WINDOW_DAYS,
    allow_expired: bool = False,
    force: bool = False,
) -> tuple[bool, str, dict[str, Any]]:
    """
    Eligibility for renewal (not full authorization).
    Does not grant scopes; only decides if issuer may mint a replacement.

    Returns (ok, reason, meta).
    """
    ok, reason = verify_envelope(envelope)
    if not ok:
        return False, reason, {}

    subject = envelope.get("credentialSubject") or {}
    cred_type = subject.get("credentialType") or envelope.get("credentialType")
    if not cred_type:
        return False, "missing_credential_type", {}

    issuer = envelope.get("issuer")
    allowed, reg_reason = issuer_allows_type(issuer, cred_type)
    if not allowed:
        return False, reg_reason, {}

    credential_id = envelope.get("id") or subject.get("credentialId")
    status_ok, status_reason = check_status(credential_id)
    if not status_ok:
        # Revoked original cannot be "renewed" — use rotate / explicit re-issue
        return False, status_reason, {"credential_id": credential_id}

    subject_id = subject.get("id") or subject.get("did")
    if not subject_id:
        return False, "missing_subject_id", {}

    exp_dt = _parse_exp(envelope.get("expirationDate"))
    now = datetime.now(timezone.utc)
    meta = {
        "credential_id": credential_id,
        "subject_id": subject_id,
        "credential_type": cred_type,
        "issuer": issuer,
        "expirationDate": envelope.get("expirationDate"),
    }

    if exp_dt is None:
        if not force:
            return False, "missing_expirationDate", meta
    else:
        if exp_dt < now and not allow_expired:
            return False, "credential_expired_renew_requires_allow_expired", meta
        window_start = exp_dt - timedelta(days=renewal_window_days)
        if not force and exp_dt >= now and now < window_start:
            return False, "not_in_renewal_window", {
                **meta,
                "renewal_window_starts": window_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

    return True, "eligible", meta


def issue_replacement(
    *,
    issuer_private: Ed25519PrivateKey,
    issuer_did: str,
    subject_id: str,
    credential_type: str,
    name: str = "",
    org: Optional[str] = None,
    days_valid: int = 365,
    replaces_id: Optional[str] = None,
    extra_subject: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Mint a brand-new credential B. Registers B as active.
    Does not modify credential A.
    """
    allowed, reg_reason = issuer_allows_type(issuer_did, credential_type)
    if not allowed:
        raise ValueError(reg_reason)

    now = datetime.now(timezone.utc)
    cred_id = new_credential_id()
    subject: dict[str, Any] = {
        "id": subject_id,
        "credentialType": credential_type,
        "name": name or credential_type,
        "org": org or issuer_did,
        "credentialId": cred_id,
    }
    if replaces_id:
        subject["replaces"] = replaces_id
    if extra_subject:
        subject.update(extra_subject)

    payload = {
        "id": cred_id,
        "type": "SignalForgeCredential",
        "issuer": issuer_did,
        "issuanceDate": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expirationDate": (now + timedelta(days=days_valid)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "credentialSubject": subject,
    }
    if replaces_id:
        payload["replaces"] = replaces_id

    envelope = sign_envelope(payload, issuer_private, issuer_did)
    register_active(
        cred_id,
        issuer_did=issuer_did,
        subject_id=subject_id,
        credential_type=credential_type,
        replaces=replaces_id,
    )
    return envelope


def renew_credential(
    old_envelope: dict[str, Any],
    *,
    issuer_private: Ed25519PrivateKey,
    issuer_did: str,
    days_valid: int = 365,
    renewal_window_days: int = DEFAULT_RENEWAL_WINDOW_DAYS,
    allow_expired: bool = False,
    force: bool = False,
    revoke_old: bool = False,
    revoke_reason: str = "superseded_by_renewal",
) -> tuple[Optional[dict[str, Any]], Optional[str], dict[str, Any]]:
    """
    Renewal: eligibility on A, issue independent B (same type + subject by default).

    If revoke_old=True, revoke A after B is issued.
    Default revoke_old=False so A remains valid until its own expiry.
    """
    ok, reason, meta = check_renewal_eligibility(
        old_envelope,
        renewal_window_days=renewal_window_days,
        allow_expired=allow_expired,
        force=force,
    )
    if not ok:
        return None, reason, meta

    if issuer_did != meta["issuer"]:
        allowed, reg_reason = issuer_allows_type(issuer_did, meta["credential_type"])
        if not allowed:
            return None, reg_reason, meta

    subject = old_envelope.get("credentialSubject") or {}
    try:
        new_env = issue_replacement(
            issuer_private=issuer_private,
            issuer_did=issuer_did,
            subject_id=meta["subject_id"],
            credential_type=meta["credential_type"],
            name=subject.get("name") or meta["credential_type"],
            org=subject.get("org") or issuer_did,
            days_valid=days_valid,
            replaces_id=meta.get("credential_id"),
        )
    except ValueError as e:
        return None, str(e), meta

    info = {
        **meta,
        "new_credential_id": new_env.get("id"),
        "operation": "renew",
    }

    if revoke_old and meta.get("credential_id"):
        rok, rmsg = revoke(meta["credential_id"], reason=revoke_reason)
        info["old_revocation"] = rmsg
        if not rok:
            info["old_revocation_failed"] = True

    return new_env, None, info


def rotate_credential(
    old_envelope: dict[str, Any],
    *,
    issuer_private: Ed25519PrivateKey,
    issuer_did: str,
    new_subject_id: Optional[str] = None,
    days_valid: int = 365,
    revoke_old: bool = True,
    revoke_reason: str = "rotated",
    force: bool = True,
) -> tuple[Optional[dict[str, Any]], Optional[str], dict[str, Any]]:
    """
    Rotation: replace credential and/or holder key material.
    By default revokes A and issues B.
    B is still verified independently on present.
    """
    ok, reason = verify_envelope(old_envelope)
    if not ok:
        return None, reason, {}

    subject = old_envelope.get("credentialSubject") or {}
    cred_type = subject.get("credentialType") or old_envelope.get("credentialType")
    if not cred_type:
        return None, "missing_credential_type", {}

    allowed, reg_reason = issuer_allows_type(issuer_did, cred_type)
    if not allowed:
        return None, reg_reason, {}

    old_id = old_envelope.get("id") or subject.get("credentialId")
    # Rotation after compromise: old may already be revoked — still allow issuing B
    status_ok, status_reason = check_status(old_id)
    if not status_ok and status_reason != "credential_revoked" and not force:
        return None, status_reason, {"credential_id": old_id}

    subject_id = new_subject_id or subject.get("id") or subject.get("did")
    if not subject_id:
        return None, "missing_subject_id", {}

    try:
        new_env = issue_replacement(
            issuer_private=issuer_private,
            issuer_did=issuer_did,
            subject_id=subject_id,
            credential_type=cred_type,
            name=subject.get("name") or cred_type,
            org=subject.get("org") or issuer_did,
            days_valid=days_valid,
            replaces_id=old_id,
            extra_subject={"rotationOf": old_id} if old_id else None,
        )
    except ValueError as e:
        return None, str(e), {}

    info = {
        "credential_id": old_id,
        "new_credential_id": new_env.get("id"),
        "subject_id": subject_id,
        "credential_type": cred_type,
        "operation": "rotate",
        "old_status_before": status_reason,
    }

    if revoke_old and old_id:
        entry = get_entry(old_id) if old_id else None
        if not entry or entry.get("status") != "revoked":
            rok, rmsg = revoke(old_id, reason=revoke_reason)
            info["old_revocation"] = rmsg
        else:
            info["old_revocation"] = "already_revoked"

    return new_env, None, info