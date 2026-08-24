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
H7 — Retention governance (Phase 2.7).

Formal ownership over identity audit retention defaults without redesigning
the existing per-event retention mechanism in audit_governance.py.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from identity_runtime.audit_governance import (
    AUDIT_ADMIN_SCOPE,
    actor_may_admin_audit,
    retention_policy,
)

DEFAULT_PATH = (
    Path(__file__).resolve().parent.parent / "dapp_api" / "retention_governance.json"
)

# Named owner/authority for changing retention defaults (independent-review observation)
RETENTION_POLICY_OWNER = "IdentityAuditAdmin"
RETENTION_CHANGE_SCOPE = AUDIT_ADMIN_SCOPE  # identity_audit:admin
PURGE_AUTHORITY_SCOPE = AUDIT_ADMIN_SCOPE

GOVERNANCE = {
    "policy_owner_role": RETENTION_POLICY_OWNER,
    "change_scope": RETENTION_CHANGE_SCOPE,
    "purge_authority_scope": PURGE_AUTHORITY_SCOPE,
    "policy_basis": (
        "Minimum-necessary retention for identity assurance and security reconstruction; "
        "defaults live in audit_governance retention_policy() with env overrides."
    ),
    "mechanism_preserved": "per_event_retention_in_audit_governance",
}


def retention_governance_summary() -> dict[str, Any]:
    return {
        **GOVERNANCE,
        "current_defaults_seconds": retention_policy(),
    }


def record_retention_change(
    *,
    actor: str,
    authz: Optional[dict[str, Any]] = None,
    change_description: str,
    policy_basis: str = "",
    path: Optional[Path] = None,
) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    """Authorize and record a retention configuration change (audit of policy change)."""
    ok, reason = actor_may_admin_audit(actor, authz=authz)
    if not ok:
        return None, reason
    rec = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor": actor,
        "operation": "retention_config_change",
        "change_description": change_description,
        "policy_basis": policy_basis or GOVERNANCE["policy_basis"],
        "owner_role": RETENTION_POLICY_OWNER,
    }
    p = path or DEFAULT_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec, None