# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""Scheme material placeholders — mock only; no concrete ZK library."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SchemeMaterial:
    """Opaque material reference for a scheme version (never logged as secret)."""

    scheme_id: str
    scheme_version: str
    material_ref: str
    status: str  # ACTIVE | REVOKED | SUPERSEDED