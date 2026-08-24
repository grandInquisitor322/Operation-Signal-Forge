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
H4 — Minimal tamper-detection response (Phase 2.7).

Not SIEM. Scheduled/triggered verify_chain; on failure, write alert file +
governed audit event. Notification path: local alert JSONL under dapp_api/
(simplest reliable path present in this deployment model).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from identity_runtime.audit_governance import verify_chain
from identity_runtime.presentation_audit import DEFAULT_PATH as AUDIT_PATH
from identity_runtime.presentation_audit import log_event, read_audit_log

ALERT_PATH = (
    Path(__file__).resolve().parent.parent / "dapp_api" / "tamper_alerts.jsonl"
)

NOTIFICATION_PATH_SELECTED = {
    "path": "dapp_api/tamper_alerts.jsonl",
    "rationale": (
        "Single-host identity deployment has no existing pager/email bus in-repo; "
        "local alert JSONL is the minimal reliable notification sink without new infra."
    ),
}


def check_audit_integrity(
    *,
    audit_path: Optional[Path] = None,
    alert_path: Optional[Path] = None,
) -> dict[str, Any]:
    path = audit_path or AUDIT_PATH
    records = read_audit_log(path, limit=100_000)
    ok, reason = verify_chain(records)
    result = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ok": ok,
        "reason": reason,
        "record_count": len(records),
        "audit_path": str(path),
    }
    if not ok:
        ap = alert_path or ALERT_PATH
        ap.parent.mkdir(parents=True, exist_ok=True)
        with ap.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result, sort_keys=True) + "\n")
        try:
            log_event(
                "audit_integrity_failure",
                reason=reason,
                record_count=len(records),
            )
        except Exception:
            pass
    return result