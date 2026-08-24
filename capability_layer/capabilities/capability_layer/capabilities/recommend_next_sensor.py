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
Capability: recommend_next_sensor

Advisory recommendation for the next sensor most likely to reduce uncertainty.
Does NOT task sensors, fuse scores, write DynamoDB, or publish alerts.
"""

from __future__ import annotations

from typing import Any, Optional

from capability_layer.execution import ExecutionBackend
from capability_layer.ports import DetectionReadPort
from capability_layer.results import CapabilityResult

CAPABILITY_NAME = "recommend_next_sensor"

# Investigative value heuristics (extensible as modules are added)
_SENSOR_META = {
    "radar": {
        "label": "radar",
        "fills": "subsurface / micro-Doppler confirmation",
        "when_weak": "Limited through-rubble or motion-band evidence.",
    },
    "thermal": {
        "label": "thermal",
        "fills": "thermal contrast / hotspot corroboration",
        "when_weak": "Limited thermal delta or hotspot coverage.",
    },
    "acoustic": {
        "label": "acoustic",
        "fills": "tap / voice-pattern corroboration",
        "when_weak": "Limited acoustic confirmation.",
    },
    "starlink": {
        "label": "starlink",
        "fills": "overhead / RF-associated context",
        "when_weak": "Missing or weak overhead observation context.",
    },
    "celltower": {
        "label": "celltower",
        "fills": "coarse infrastructure-associated location context",
        "when_weak": "No cell-tower enrichment on this cell.",
    },
}


def recommend_next_sensor(
    backend: Optional[ExecutionBackend],
    params: dict[str, Any],
    *,
    detections: DetectionReadPort,
) -> CapabilityResult:
    """
    Params:
      cell_id: str (required)
    """
    cell_id = params.get("cell_id")
    if not cell_id or not isinstance(cell_id, str):
        return CapabilityResult(
            capability=CAPABILITY_NAME,
            status="error",
            message="param 'cell_id' (str) is required",
        )

    cell = detections.get_cell(cell_id)
    if cell is None:
        return CapabilityResult(
            capability=CAPABILITY_NAME,
            status="error",
            message=f"No detection found for cell_id={cell_id}",
            data={"cell_id": cell_id},
        )

    recommendation = _recommend(cell)
    return CapabilityResult(
        capability=CAPABILITY_NAME,
        status="ok",
        message="Sensor recommendation generated (advisory only)",
        data={"recommendation": recommendation},
        metadata={
            "access": "read-only",
            "port": "DetectionReadPort",
            "operational_tasking": False,
        },
    )


def _scores(cell: dict[str, Any]) -> dict[str, float]:
    return {
        name: float(cell.get(f"{name}_score") or 0)
        for name in _SENSOR_META
    }


def _recommend(cell: dict[str, Any]) -> dict[str, Any]:
    scores = _scores(cell)
    fused = float(cell.get("fused_probability") or 0)
    active = [k for k, v in scores.items() if v > 0.05]
    strong = [k for k, v in scores.items() if v >= 0.4]
    weak_or_missing = [k for k, v in scores.items() if v < 0.25]

    # Priority rules (explainable, ordered)
    candidates: list[tuple[str, str, str, str]] = []
    # (sensor, priority, expected_value, rationale)

    if len(active) <= 1 and weak_or_missing:
        # Single-source → corroborate with best missing modality
        pick = _prefer_order(weak_or_missing)
        candidates.append(
            (
                pick,
                "high",
                "Corroboration from a second modality",
                f"Only {len(active)} active modality(ies); multi-sensor agreement is weak.",
            )
        )

    if fused >= 0.4 and scores.get("radar", 0) < 0.25:
        candidates.append(
            (
                "radar",
                "high",
                "Subsurface / micro-Doppler confirmation",
                "Fused confidence is elevated but radar contribution is low.",
            )
        )

    if scores.get("thermal", 0) < 0.25 and fused >= 0.3:
        candidates.append(
            (
                "thermal",
                "medium",
                "Thermal contrast corroboration",
                _SENSOR_META["thermal"]["when_weak"],
            )
        )

    if scores.get("acoustic", 0) < 0.25 and fused >= 0.3:
        candidates.append(
            (
                "acoustic",
                "medium",
                "Acoustic pattern corroboration",
                _SENSOR_META["acoustic"]["when_weak"],
            )
        )

    if scores.get("starlink", 0) < 0.25:
        candidates.append(
            (
                "starlink",
                "medium" if fused >= 0.4 else "low",
                "Overhead / RF-associated context",
                _SENSOR_META["starlink"]["when_weak"],
            )
        )

    if scores.get("celltower", 0) < 0.25 and fused < 0.5:
        candidates.append(
            (
                "celltower",
                "low",
                "Coarse location enrichment",
                _SENSOR_META["celltower"]["when_weak"],
            )
        )

    if not candidates:
        # All modalities already contributing — suggest strongest gap still under 0.5
        ordered = sorted(scores.items(), key=lambda kv: kv[1])
        pick = ordered[0][0]
        candidates.append(
            (
                pick,
                "low",
                f"Incremental improvement on weakest modality ({pick})",
                "Evidence coverage is relatively complete; residual value is incremental.",
            )
        )

    # Highest priority first; stable tie-break by prefer order
    priority_rank = {"high": 0, "medium": 1, "low": 2}
    candidates.sort(
        key=lambda c: (priority_rank.get(c[1], 9), _prefer_order_index(c[0]))
    )
    sensor, priority, expected, reason = candidates[0]

    gaps = []
    if len(active) < 2:
        gaps.append("Fewer than two modalities above noise floor.")
    for name, val in scores.items():
        if val < 0.25:
            gaps.append(f"{name} underrepresented (score={val:.2f}).")

    return {
        "recommendation_status": "complete",
        "cell_id": cell.get("cell_id"),
        "site_id": cell.get("site_id"),
        "recommended_sensor": sensor,
        "priority": priority,
        "expected_investigative_value": expected,
        "rationale": reason,
        "why_selected": (
            f"{sensor} was selected because: {reason} "
            f"It addresses: {_SENSOR_META[sensor]['fills']}."
        ),
        "complements_existing": (
            f"Active modalities: {', '.join(active) if active else 'none'}. "
            f"Strong modalities: {', '.join(strong) if strong else 'none'}."
        ),
        "current_fused_probability": fused,
        "current_scores": scores,
        "evidence_gaps": gaps,
        "supporting_observations": {
            "active_count": len(active),
            "strong_count": len(strong),
            "cell_status": cell.get("status"),
        },
        "advisory_only": True,
        "does_not_task_sensors": True,
    }


def _prefer_order(names: list[str]) -> str:
    order = ["radar", "thermal", "acoustic", "starlink", "celltower"]
    for n in order:
        if n in names:
            return n
    return names[0]


def _prefer_order_index(name: str) -> int:
    order = ["radar", "thermal", "acoustic", "starlink", "celltower"]
    try:
        return order.index(name)
    except ValueError:
        return 99