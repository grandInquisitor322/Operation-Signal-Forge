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
Capability: investigate_anomaly

Workflow capability that coordinates investigation of a completed detection.
Composes supporting capabilities (e.g. generate_detection_brief) and returns
a structured advisory assessment.

Does NOT: fuse scores, write DynamoDB, publish SNS, parse sensor payloads,
          or override Fusion Engine decisions.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from capability_layer.execution import ExecutionBackend
from capability_layer.ports import DetectionReadPort
from capability_layer.results import CapabilityResult

CAPABILITY_NAME = "investigate_anomaly"

# Type for invoking peer capabilities without importing the full facade
CapabilityInvoker = Callable[[str, dict[str, Any]], CapabilityResult]


def investigate_anomaly(
    backend: Optional[ExecutionBackend],
    params: dict[str, Any],
    *,
    detections: DetectionReadPort,
    invoke: CapabilityInvoker,
) -> CapabilityResult:
    """
    Run a read-only investigation workflow for one detection cell.

    Params:
      cell_id: str (required)
      include_recommendations: bool (default True)
    """
    cell_id = params.get("cell_id")
    if not cell_id or not isinstance(cell_id, str):
        return CapabilityResult(
            capability=CAPABILITY_NAME,
            status="error",
            message="param 'cell_id' (str) is required",
        )

    # --- 1. Retrieve detection via port ---
    cell = detections.get_cell(cell_id)
    if cell is None:
        return CapabilityResult(
            capability=CAPABILITY_NAME,
            status="error",
            message=f"No detection found for cell_id={cell_id}",
            data={"cell_id": cell_id},
        )

    supporting: list[dict[str, Any]] = []

    # --- 2. Supporting capability: detection brief ---
    brief_result = invoke(
        "generate_detection_brief",
        {
            "cell_id": cell_id,
            "include_recommendations": bool(params.get("include_recommendations", True)),
        },
    )
    supporting.append(
        {
            "capability": "generate_detection_brief",
            "status": brief_result.status,
            "message": brief_result.message,
        }
    )
    brief = (brief_result.data or {}).get("brief") if brief_result.status == "ok" else None

    # --- 2b. Supporting capability: next sensor (reusable — do not reimplement) ---
    next_sensor_result = invoke(
        "recommend_next_sensor",
        {"cell_id": cell_id},
    )
    supporting.append(
        {
            "capability": "recommend_next_sensor",
            "status": next_sensor_result.status,
            "message": next_sensor_result.message,
        }
    )
    next_sensor = (
        (next_sensor_result.data or {}).get("recommendation")
        if next_sensor_result.status == "ok"
        else None
    )

    # --- 3. Evidence assessment (deterministic, advisory) ---
    evidence = _assess_evidence(cell)

    # --- 4. Aggregate advisory investigation ---
    investigation = {
        "investigation_status": "complete",
        "cell_id": cell_id,
        "site_id": cell.get("site_id"),
        "overall_assessment": _overall_assessment(cell, evidence),
        "confidence_explanation": _confidence_explanation(cell, evidence),
        "evidence_summary": evidence,
        "information_gaps": evidence.get("gaps", []),
        "recommended_actions": _recommended_actions(cell, evidence, brief, next_sensor),
        "next_sensor": next_sensor,
        "detection_brief": brief,
        "supporting_capabilities": supporting,
        "analyst_considerations": _analyst_considerations(cell, evidence),
        "advisory_only": True,
        "does_not_modify_system_state": True,
    }

    return CapabilityResult(
        capability=CAPABILITY_NAME,
        status="ok",
        message="Investigation complete (advisory, read-only)",
        data={"investigation": investigation},
        metadata={
            "access": "read-only",
            "port": "DetectionReadPort",
            "workflow": True,
            "composed": ["generate_detection_brief", "recommend_next_sensor"],
        },
    )


def _scores(cell: dict[str, Any]) -> dict[str, float]:
    keys = ("radar", "thermal", "acoustic", "starlink", "celltower")
    return {k: float(cell.get(f"{k}_score") or 0) for k in keys}


def _assess_evidence(cell: dict[str, Any]) -> dict[str, Any]:
    scores = _scores(cell)
    active = {k: v for k, v in scores.items() if v > 0.05}
    strong = {k: v for k, v in scores.items() if v >= 0.4}
    fused = float(cell.get("fused_probability") or 0)

    gaps: list[str] = []
    if len(active) < 2:
        gaps.append("Fewer than two modalities above noise floor.")
    if not strong and fused < 0.75:
        gaps.append("No single modality at strong confidence (>= 0.4).")
    if scores.get("radar", 0) < 0.2 and fused >= 0.4:
        gaps.append("Limited radar contribution relative to fused confidence.")
    if cell.get("status") == "unassigned" and fused >= 0.4:
        gaps.append("Operational status still unassigned despite elevated fused score.")
    if scores.get("starlink", 0) > 0.3 and scores.get("radar", 0) < 0.2:
        gaps.append("Starlink evidence without corroborating radar.")

    agreement = (
        "multi-sensor"
        if len(strong) >= 2
        else ("single-sensor" if len(active) == 1 else "weak / sparse")
    )

    return {
        "contributing_sensor_count": len(active),
        "active_modalities": list(active.keys()),
        "strong_modalities": list(strong.keys()),
        "scores": scores,
        "fused_probability": fused,
        "sensor_agreement": agreement,
        "cell_status": cell.get("status"),
        "gaps": gaps,
        "completeness": (
            "good" if len(strong) >= 2 else "partial" if len(active) >= 2 else "limited"
        ),
    }


def _overall_assessment(cell: dict[str, Any], evidence: dict[str, Any]) -> str:
    fused = evidence["fused_probability"]
    completeness = evidence["completeness"]
    if fused >= 0.75 and completeness in ("good", "partial"):
        return (
            "Elevated fused confidence with usable multi-sensor context. "
            "Treat as a triage priority for human review, not a confirmed find."
        )
    if fused >= 0.4:
        return (
            "Moderate fused confidence. Evidence may be incomplete; "
            "corroboration recommended before heavy resource commitment."
        )
    return (
        "Low fused confidence or sparse evidence. "
        "Suitable for monitoring rather than immediate tasking."
    )


def _confidence_explanation(cell: dict[str, Any], evidence: dict[str, Any]) -> str:
    fused = evidence["fused_probability"]
    n = evidence["contributing_sensor_count"]
    agreement = evidence["sensor_agreement"]
    return (
        f"Fused probability is {fused:.3f} from the Fusion Engine (deterministic). "
        f"This investigation sees {n} active modalit(y/ies) with {agreement} agreement. "
        f"Evidence completeness rated '{evidence['completeness']}'. "
        f"Capability Layer does not recompute fusion."
    )


def _recommended_actions(
    cell: dict[str, Any],
    evidence: dict[str, Any],
    brief: Optional[dict[str, Any]],
    next_sensor: Optional[dict[str, Any]] = None,
) -> list[str]:
    actions: list[str] = []
    fused = evidence["fused_probability"]

    if fused >= 0.75:
        actions.append("Queue for analyst review and possible ground-team tasking.")
    elif fused >= 0.4:
        actions.append("Request additional sensor pass on the same cell if available.")
    else:
        actions.append("Continue monitoring; deprioritize versus higher-fused cells.")

    # From reusable recommend_next_sensor capability (not reimplemented here)
    if next_sensor and next_sensor.get("recommended_sensor"):
        sensor = next_sensor["recommended_sensor"]
        priority = next_sensor.get("priority", "medium")
        actions.append(
            f"Next sensor suggestion ({priority}): {sensor} — "
            f"{next_sensor.get('expected_investigative_value', 'see rationale')}."
        )

    for gap in evidence.get("gaps", []):
        if "radar" in gap.lower():
            actions.append("If safe/feasible, prioritize radar revisit on this grid cell.")
        if "unassigned" in gap.lower():
            actions.append("Command may update cell status to searching when assigned.")

    if brief and brief.get("recommendations"):
        for rec in brief["recommendations"][:2]:
            if rec not in actions:
                actions.append(rec)

    seen = set()
    unique = []
    for a in actions:
        if a not in seen:
            seen.add(a)
            unique.append(a)
    return unique


def _analyst_considerations(cell: dict[str, Any], evidence: dict[str, Any]) -> list[str]:
    notes = [
        "This output is advisory decision support only.",
        "Fused probability was produced by the Fusion Engine; this workflow does not alter it.",
        "Do not clear or confirm a cell solely on this investigation result.",
    ]
    if evidence["completeness"] == "limited":
        notes.append("Sparse modality coverage increases uncertainty.")
    if evidence.get("gaps"):
        notes.append("Address listed information gaps before high-cost deployment.")
    return notes