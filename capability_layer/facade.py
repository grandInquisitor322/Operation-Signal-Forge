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

"""Capability layer facade — request named capabilities."""

from __future__ import annotations

from typing import Any, Optional

from capability_layer.execution import ExecutionBackend
from capability_layer.ports import DetectionReadPort
from capability_layer.registry import (
    CapabilityRegistry,
    bind_detection_brief,
    bind_investigate_anomaly,
    bind_recommend_next_sensor,
)
from capability_layer.results import CapabilityResult


class CapabilityLayer:
    def __init__(
        self,
        *,
        backend: Optional[ExecutionBackend] = None,
        detections: Optional[DetectionReadPort] = None,
        registry: Optional[CapabilityRegistry] = None,
    ):
        self._backend = backend
        self._detections = detections
        self._registry = registry or CapabilityRegistry()

        if detections is not None:
            self._registry.register(
                "generate_detection_brief",
                bind_detection_brief(detections),
            )
            self._registry.register(
                "investigate_anomaly",
                bind_investigate_anomaly(detections, self.request_capability),
            )
            self._registry.register(
                "recommend_next_sensor",
                bind_recommend_next_sensor(detections),
            )

    def list_capabilities(self) -> list[str]:
        return self._registry.list_capabilities()

    def request_capability(
        self, capability: str, params: Optional[dict[str, Any]] = None
    ) -> CapabilityResult:
        params = params or {}
        handler = self._registry.get(capability)
        if handler is None:
            return CapabilityResult(
                capability=capability,
                status="error",
                message=f"Unknown capability: {capability}",
                data={"available": self.list_capabilities()},
            )
        try:
            return handler(self._backend, params)
        except Exception as e:
            return CapabilityResult(
                capability=capability,
                status="error",
                message=str(e),
                backend=getattr(self._backend, "name", None),
            )

    def run_simple_workflow(self) -> CapabilityResult:
        ping = self.request_capability("ping", {"echo": "phase1"})
        if ping.status != "ok":
            return ping
        return self.request_capability("execute_sandbox_task", {})

    def close(self) -> None:
        if self._backend is not None:
            self._backend.close()