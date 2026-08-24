from __future__ import annotations
from typing import Any, Optional
from capability_layer.execution import ExecutionBackend
from capability_layer.ports import DetectionReadPort
from capability_layer.results import CapabilityResult

CAPABILITY_NAME = "generate_detection_brief"

def generate_detection_brief(backend, params, *, detections: DetectionReadPort):
    cell_id = params.get("cell_id")
    if not cell_id or not isinstance(cell_id, str):
        return CapabilityResult(
            capability=CAPABILITY_NAME, status="error",
            message="param 'cell_id' (str) is required",
        )
    cell = detections.get_cell(cell_id)
    if cell is None:
        return CapabilityResult(
            capability=CAPABILITY_NAME, status="error",
            message=f"No detection found for cell_id={cell_id}",
            data={"cell_id": cell_id},
        )
    brief = _build_brief(cell, include_recommendations=bool(params.get("include_recommendations", True)))
    return CapabilityResult(
        capability=CAPABILITY_NAME, status="ok",
        message="Detection brief generated (read-only)",
        data={"brief": brief},
        metadata={"access": "read-only", "port": "DetectionReadPort"},
    )

def _build_brief(cell, *, include_recommendations):
    fused = float(cell.get("fused_probability") or 0)
    scores = {
        "radar": float(cell.get("radar_score") or 0),
        "thermal": float(cell.get("thermal_score") or 0),
        "acoustic": float(cell.get("acoustic_score") or 0),
        "starlink": float(cell.get("starlink_score") or 0),
        "celltower": float(cell.get("celltower_score") or 0),
    }
    active = [n for n, v in scores.items() if v > 0.05]
    band = "high" if fused >= 0.75 else "moderate" if fused >= 0.4 else "low"
    headline = (
        f"Cell {cell.get('cell_id')} @ site {cell.get('site_id', 'unknown')}: "
        f"fused={fused:.3f} ({band}), status={cell.get('status', 'unknown')}"
    )
    recs = []
    if include_recommendations:
        if fused >= 0.75:
            recs.append("Prioritize ground team assessment; high-confidence triage lead only.")
        elif fused >= 0.4:
            recs.append("Consider corroborating pass with an additional sensor modality.")
        else:
            recs.append("Low fused confidence — wait for multi-sensor corroboration.")
        if scores.get("starlink", 0) > 0.3 and scores.get("radar", 0) < 0.2:
            recs.append("Starlink without strong radar — verify observer/site context.")
        if cell.get("status") == "unassigned" and fused >= 0.4:
            recs.append("Cell unassigned — command may set status to searching.")
    return {
        "headline": headline,
        "cell_id": cell.get("cell_id"),
        "site_id": cell.get("site_id"),
        "lat": cell.get("lat"),
        "lon": cell.get("lon"),
        "status": cell.get("status"),
        "fused_probability": fused,
        "confidence_band": band,
        "scores": scores,
        "active_modalities": active,
        "narrative": f"Active modalities: {', '.join(active)}." if active else "No strong modality scores.",
        "recommendations": recs,
        "advisory_only": True,
    }
