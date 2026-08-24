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
Identity recovery policy & interface contract (Phase 2.5 foundation).

Governing principle:
  Identity recovery restores or re-establishes control of an identity;
  it does not automatically restore credential authority or operational
  authorization.

Phase 2.5 does NOT implement:
  - automated recovery service
  - automatic credential reissuance
  - automatic privilege restoration
  - hidden recovery authority in runtime identity logic

Recovery ≠ credential renewal/revocation.
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Protocol

DEFAULT_AUDIT_PATH = (
    Path(__file__).resolve().parent.parent / "dapp_api" / "recovery_audit.jsonl"
)

TRIGGER_KEYS_LOST = "keys_lost"
TRIGGER_KEYS_COMPROMISED = "keys_compromised"
VALID_TRIGGERS = frozenset({TRIGGER_KEYS_LOST, TRIGGER_KEYS_COMPROMISED})

RECOVERY_APPROVER_SCOPE = "identity_recovery:approver"
RECOVERY_APPROVER_ROLE = "IdentityRecoveryApprover"

STATUS_REQUESTED = "requested"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_COMPLETED = "completed"
STATUS_CANCELLED = "cancelled"


def recovery_boundary_statement() -> str:
    return (
        "Identity recovery re-establishes control of a DID's authentication keys; "
        "it does not renew, reissue, or un-revoke credentials and does not grant "
        "Authorization Matrix scopes."
    )


def trigger_policy() -> dict[str, Any]:
    return {
        TRIGGER_KEYS_LOST: {
            "description": "Holder cannot access the active private key.",
            "prefer_immediate_retire": False,
            "multi_party_approval_recommended": False,
        },
        TRIGGER_KEYS_COMPROMISED: {
            "description": "Active key is believed exposed.",
            "prefer_immediate_retire": True,
            "multi_party_approval_recommended": True,
        },
    }


def evidence_requirements(trigger: str) -> list[str]:
    base = [
        "subject_did",
        "trigger",
        "requester_id",
        "evidence_reference",
    ]
    if trigger == TRIGGER_KEYS_COMPROMISED:
        base.append("compromise_summary")
    return base


def impact_on_verification_methods(trigger: str) -> dict[str, Any]:
    """Policy description only — not an executor."""
    return {
        "retire_prior_authentication_methods": True,
        "activate_new_verification_method": True,
        "preserve_did": True,
        "invalidate_outstanding_nonces": False,
        "reissue_credentials": False,
        "unrevoke_credentials": False,
        "grant_authorization_scopes": False,
        "notes": (
            "Compromise should retire affected methods before or as part of recovery. "
            "Lost-key recovery still retires inaccessible methods so they cannot authenticate."
        ),
        "trigger": trigger,
    }


def required_audit_fields() -> list[str]:
    return [
        "recovery_id",
        "timestamp",
        "subject_did",
        "trigger",
        "requester",
        "approver",
        "status",
        "governance_reference",
        "methods_retired",
        "method_activated",
        "reason",
    ]


def actor_may_approve_recovery(
    actor: str,
    *,
    authz: Optional[dict[str, Any]] = None,
) -> tuple[bool, str]:
    """Approver gate. Prefer dedicated recovery scope/role."""
    if not actor or not str(actor).strip():
        return False, "missing_recovery_actor"
    if authz:
        scopes = authz.get("scopes") or []
        if RECOVERY_APPROVER_SCOPE in scopes:
            return True, "ok_scope"
        if (authz.get("role") or "") == RECOVERY_APPROVER_ROLE:
            return True, "ok_role"
        subject = authz.get("subject_id") or authz.get("email") or ""
        if subject and subject.strip().lower() != actor.strip().lower():
            return False, "actor_authz_subject_mismatch"
    return False, "insufficient_recovery_authority"


def build_recovery_request(
    *,
    subject_did: str,
    trigger: str,
    requester: str,
    evidence_reference: str = "",
    reason: str = "",
    compromise_summary: str = "",
) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    if trigger not in VALID_TRIGGERS:
        return None, "invalid_recovery_trigger"
    if not subject_did:
        return None, "missing_subject_did"
    if not requester:
        return None, "missing_requester"
    rec = {
        "recovery_id": secrets.token_hex(8),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "subject_did": subject_did,
        "trigger": trigger,
        "requester": requester,
        "approver": None,
        "status": STATUS_REQUESTED,
        "governance_reference": "",
        "evidence_reference": evidence_reference,
        "compromise_summary": compromise_summary or None,
        "methods_retired": [],
        "method_activated": None,
        "reason": reason,
        "impact_policy": impact_on_verification_methods(trigger),
        "boundary": recovery_boundary_statement(),
    }
    return rec, None


def append_recovery_audit(
    record: dict[str, Any], *, path: Optional[Path] = None
) -> None:
    """Append metadata-only recovery audit line (no private keys / VCs)."""
    p = path or DEFAULT_AUDIT_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    forbidden = {"private_key", "credential", "envelope", "signature", "proof"}
    safe = {k: v for k, v in record.items() if k not in forbidden}
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(safe, sort_keys=True) + "\n")


class RecoveryService(Protocol):
    def request_recovery(self, **kwargs: Any) -> tuple[dict[str, Any], Optional[str]]:
        ...

    def approve_recovery(
        self, recovery_id: str, *, actor: str, authz: Optional[dict[str, Any]] = None
    ) -> tuple[bool, str]:
        ...


class RecoveryServiceNotImplemented:
    """Explicit stub — prevents accidental silent recovery."""

    def request_recovery(self, **kwargs: Any) -> tuple[dict[str, Any], Optional[str]]:
        raise NotImplementedError(
            "Phase 2.5 ships recovery policy only; automated recovery is deferred"
        )

    def approve_recovery(
        self, recovery_id: str, *, actor: str, authz: Optional[dict[str, Any]] = None
    ) -> tuple[bool, str]:
        raise NotImplementedError(
            "Phase 2.5 ships recovery policy only; automated recovery is deferred"
        )


def get_recovery_service() -> RecoveryService:
    return RecoveryServiceNotImplemented()