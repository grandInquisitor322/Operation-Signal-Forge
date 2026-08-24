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
Identity recovery executor (Phase 2.6 G2).

Workflow: request → approve → retire methods → activate new key → audit.

Does NOT reissue credentials, un-revoke, or grant Authorization Matrix scopes.
Uses holder_keys.rotate_holder_key for key material transition.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from identity_runtime.did_resolver import LocalDidResolver, get_resolver
from identity_runtime.holder_keys import rotate_holder_key
from identity_runtime.presentation_audit import log_recovery_event
from identity_runtime.recovery_policy import (
    STATUS_COMPLETED,
    STATUS_REJECTED,
    STATUS_REQUESTED,
    VALID_TRIGGERS,
    actor_may_approve_recovery,
    append_recovery_audit,
    build_recovery_request,
    recovery_boundary_statement,
)

DEFAULT_REQUESTS_PATH = (
    Path(__file__).resolve().parent.parent / "dapp_api" / "recovery_requests.json"
)


def _load_requests(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"requests": {}}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _save_requests(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


class RecoveryExecutor:
    def __init__(
        self,
        *,
        requests_path: Optional[Path] = None,
        resolver: Optional[LocalDidResolver] = None,
    ) -> None:
        self.requests_path = Path(requests_path or DEFAULT_REQUESTS_PATH)
        self.resolver = resolver

    def request_recovery(
        self,
        *,
        subject_did: str,
        trigger: str,
        requester: str,
        evidence_reference: str = "",
        reason: str = "",
        compromise_summary: str = "",
    ) -> tuple[Optional[dict[str, Any]], Optional[str]]:
        rec, err = build_recovery_request(
            subject_did=subject_did,
            trigger=trigger,
            requester=requester,
            evidence_reference=evidence_reference,
            reason=reason,
            compromise_summary=compromise_summary,
        )
        if err or not rec:
            return None, err
        data = _load_requests(self.requests_path)
        data.setdefault("requests", {})[rec["recovery_id"]] = rec
        _save_requests(self.requests_path, data)
        append_recovery_audit(rec)
        log_recovery_event(
            recovery_id=rec["recovery_id"],
            subject_did=subject_did,
            trigger=trigger,
            status=STATUS_REQUESTED,
            requester=requester,
            reason=reason,
        )
        return rec, None

    def approve_and_execute(
        self,
        recovery_id: str,
        *,
        actor: str,
        authz: Optional[dict[str, Any]] = None,
        governance_reference: str = "",
    ) -> tuple[Optional[dict[str, Any]], Optional[str]]:
        """
        Authorize then execute key retirement + replacement.
        Does not modify credentials or Authorization Matrix scopes.
        """
        ok, reason = actor_may_approve_recovery(actor, authz=authz)
        if not ok:
            log_recovery_event(
                recovery_id=recovery_id,
                subject_did="",
                trigger="",
                status=STATUS_REJECTED,
                approver=actor,
                reason=reason,
            )
            return None, reason

        data = _load_requests(self.requests_path)
        rec = data.get("requests", {}).get(recovery_id)
        if not rec:
            return None, "recovery_request_not_found"
        if rec.get("status") != STATUS_REQUESTED:
            return None, f"recovery_status_{rec.get('status')}"

        subject_did = rec["subject_did"]
        trigger = rec["trigger"]
        if trigger not in VALID_TRIGGERS:
            return None, "invalid_recovery_trigger"

        try:
            resolver = self.resolver or get_resolver()
            updated, _priv, new_mid, retired_id = rotate_holder_key(
                subject_did, resolver=resolver  # type: ignore[arg-type]
            )
        except Exception as e:
            rec["status"] = STATUS_REJECTED
            rec["reason"] = f"execution_failed:{e}"
            data["requests"][recovery_id] = rec
            _save_requests(self.requests_path, data)
            log_recovery_event(
                recovery_id=recovery_id,
                subject_did=subject_did,
                trigger=trigger,
                status=STATUS_REJECTED,
                approver=actor,
                reason=str(e),
            )
            return None, f"execution_failed:{e}"

        rec["status"] = STATUS_COMPLETED
        rec["approver"] = actor
        rec["governance_reference"] = governance_reference
        rec["methods_retired"] = [retired_id]
        rec["method_activated"] = new_mid
        rec["boundary"] = recovery_boundary_statement()
        rec["credentials_modified"] = False
        rec["authorization_scopes_granted"] = False
        data["requests"][recovery_id] = rec
        _save_requests(self.requests_path, data)
        append_recovery_audit(rec)
        log_recovery_event(
            recovery_id=recovery_id,
            subject_did=subject_did,
            trigger=trigger,
            status=STATUS_COMPLETED,
            requester=rec.get("requester") or "",
            approver=actor,
            methods_retired=[retired_id],
            method_activated=new_mid,
            reason=governance_reference or "approved",
        )
        return {
            "recovery": rec,
            "did_document_id": updated.get("id"),
            "method_activated": new_mid,
            "methods_retired": [retired_id],
        }, None


def get_recovery_executor(**kwargs: Any) -> RecoveryExecutor:
    return RecoveryExecutor(**kwargs)