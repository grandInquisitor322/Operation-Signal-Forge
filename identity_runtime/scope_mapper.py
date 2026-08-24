"""Map interim credential types → Authorization Matrix scopes."""

from __future__ import annotations

TYPE_SCOPES: dict[str, list[str]] = {
    "OrganizationMembership": [],
    "HumanitarianAnalyst": [
        "detections:read",
        "detections:list",
        "capabilities:invoke",
        "capabilities:invoke:investigate",
    ],
    "IncidentCommander": [
        "detections:read",
        "detections:list",
        "capabilities:invoke",
        "capabilities:invoke:investigate",
        "cells:status:write",
        "alerts:subscribe",
    ],
    "ResearchPartner": [
        "detections:read",
        "detections:list",
    ],
    "SensorOperator": [
        "sensors:submit",
        "detections:read",
    ],
}


def scopes_for_credential_type(credential_type: str) -> list[str]:
    return list(TYPE_SCOPES.get(credential_type, []))