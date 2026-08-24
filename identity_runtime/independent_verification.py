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
H1 — Independent verification records (Phase 2.7 / 2.8 levels / 2.9 limitations gate).

Standing control inside Step 4 (Tests & Validation).
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DEFAULT_PATH = (
    Path(__file__).resolve().parent.parent
    / "dapp_api"
    / "independent_verification.jsonl"
)

ASSIGNMENT_MODEL = {
    "model": "rotating_reviewer",
    "description": (
        "A human reviewer functionally separate from the implementation author "
        "re-runs or spot-checks material regression and repository evidence. "
        "No dedicated QA org required."
    ),
    "automation": "optional_scripted_suite_re_run_with_human_signoff",
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_verification(
    *,
    verifier: str,
    implementer: str,
    scope: str,
    suites: list[str],
    result: str,
    evidence_type: str = "independently_verified",
    notes: str = "",
    limitations: str = "",
    disagreements: str = "",
    verification_level: Optional[int] = None,
    risk_rationale: str = "",
    domains: Optional[list[str]] = None,
    expected_evidence: Optional[list[str]] = None,
    execution_context: str = "",
    verifier_run_results: Optional[dict[str, Any]] = None,
    implementer_console_only: bool = False,
    path: Optional[Path] = None,
) -> dict[str, Any]:
    if not verifier or not str(verifier).strip():
        raise ValueError("missing_verifier")
    notes_out = notes
    if verifier.strip().lower() == (implementer or "").strip().lower():
        notes_out = (notes + " | WARN: verifier_equals_implementer").strip(" |")

    from identity_runtime.verification_levels import (
        expected_evidence_for_level,
        level_name,
        recommend_level,
        validate_evidence_for_level,
    )

    domains_list = list(domains or [])
    if verification_level is None:
        verification_level, auto_reason = recommend_level(domains=domains_list)
        risk_rationale = risk_rationale or auto_reason
    else:
        verification_level = int(verification_level)
        if not risk_rationale:
            _, auto_reason = recommend_level(
                domains=domains_list, explicit_level=verification_level
            )
            risk_rationale = auto_reason

    if str(result).upper() == "PASS":
        ok_ev, ev_reason = validate_evidence_for_level(
            verification_level,
            verifier_run_results=verifier_run_results,
            execution_context=execution_context,
            implementer_console_only=implementer_console_only,
        )
        if not ok_ev:
            raise ValueError(f"insufficient_evidence_for_pass:{ev_reason}")
        if int(verification_level) >= 3:
            from identity_runtime.level3_environment_policy import limitations_acceptable

            ok_lim, lim_reason = limitations_acceptable(limitations)
            if not ok_lim:
                raise ValueError(f"insufficient_evidence_for_pass:{lim_reason}")

    exp = list(expected_evidence or expected_evidence_for_level(verification_level))

    rec = {
        "verification_id": secrets.token_hex(8),
        "timestamp": _now(),
        "verifier": verifier,
        "implementer": implementer,
        "scope": scope,
        "suites": list(suites),
        "result": result,
        "evidence_type": evidence_type,
        "notes": notes_out or None,
        "limitations": limitations or None,
        "disagreements": disagreements or None,
        "assignment_model": ASSIGNMENT_MODEL["model"],
        "verification_level": verification_level,
        "verification_level_name": level_name(verification_level),
        "risk_rationale": risk_rationale or None,
        "domains": domains_list,
        "expected_evidence": exp,
        "execution_context": execution_context or None,
        "verifier_run_results": verifier_run_results,
    }
    p = path or DEFAULT_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def list_verifications(
    path: Optional[Path] = None, *, limit: int = 50
) -> list[dict[str, Any]]:
    p = path or DEFAULT_PATH
    if not p.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines()[-limit:]:
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out