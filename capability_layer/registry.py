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

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from capability_layer.execution import ExecutionBackend
from capability_layer.ports import DetectionReadPort
from capability_layer.results import CapabilityResult

Handler = Callable[[Optional[ExecutionBackend], dict[str, Any]], CapabilityResult]
CapabilityInvoker = Callable[[str, dict[str, Any]], CapabilityResult]


class CapabilityRegistry:
    def __init__(self) -> None:
        self._handlers: Dict[str, Handler] = {}
        self.register("ping", _ping)
        self.register("execute_sandbox_task", _execute_sandbox_task)

    def register(self, name: str, handler: Handler) -> None:
        self._handlers[name] = handler

    def list_capabilities(self) -> list[str]:
        return sorted(self._handlers)

    def get(self, name: str) -> Optional[Handler]:
        return self._handlers.get(name)


def _ping(backend: Optional[ExecutionBackend], params: dict[str, Any]) -> CapabilityResult:
    try:
        import agentforge  # noqa: F401
        af = True
    except Exception:
        af = False
    return CapabilityResult(
        capability="ping",
        status="ok",
        message="Capability layer available",
        data={"echo": params.get("echo", "pong"), "agentforge_importable": af},
    )


def _execute_sandbox_task(
    backend: Optional[ExecutionBackend], params: dict[str, Any]
) -> CapabilityResult:
    if backend is None:
        return CapabilityResult(
            capability="execute_sandbox_task",
            status="error",
            message="No execution backend configured",
        )
    code = params.get("code") or "print('Phase 1')\nprint(2+2)\n"
    out = backend.run_code(code)
    ok = out.get("status") == "ok"
    return CapabilityResult(
        capability="execute_sandbox_task",
        status="ok" if ok else "error",
        message="K8s job finished" if ok else "K8s job failed",
        data={"output": out.get("result"), "exit_code": out.get("exit_code")},
        backend=backend.name,
        execution_id=out.get("execution_id"),
    )


def bind_detection_brief(detections: DetectionReadPort) -> Handler:
    from capability_layer.capabilities.detection_brief import generate_detection_brief

    def _handler(
        backend: Optional[ExecutionBackend], params: dict[str, Any]
    ) -> CapabilityResult:
        return generate_detection_brief(backend, params, detections=detections)

    return _handler


def bind_investigate_anomaly(
    detections: DetectionReadPort,
    invoke: CapabilityInvoker,
) -> Handler:
    from capability_layer.capabilities.investigate_anomaly import investigate_anomaly

    def _handler(
        backend: Optional[ExecutionBackend], params: dict[str, Any]
    ) -> CapabilityResult:
        return investigate_anomaly(
            backend, params, detections=detections, invoke=invoke
        )

    return _handler

def bind_recommend_next_sensor(detections: DetectionReadPort) -> Handler:
    from capability_layer.capabilities.recommend_next_sensor import recommend_next_sensor

    def _handler(
        backend: Optional[ExecutionBackend], params: dict[str, Any]
    ) -> CapabilityResult:
        return recommend_next_sensor(backend, params, detections=detections)

    return _handler