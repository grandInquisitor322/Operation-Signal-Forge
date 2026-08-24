from __future__ import annotations
import base64
import subprocess
import textwrap
import uuid
from typing import Any, Optional
from capability_layer.execution import ExecutionBackend

class KubernetesBackend(ExecutionBackend):
    name = "kubernetes"

    def __init__(self, *, namespace: str = "default", python_image: str = "python:3.12-slim",
                 timeout_seconds: int = 120, kubectl: str = "kubectl"):
        self.namespace = namespace
        self.python_image = python_image
        self.timeout_seconds = timeout_seconds
        self.kubectl = kubectl

    def _run_kubectl(self, args, *, input_text: Optional[str] = None):
        return subprocess.run([self.kubectl, *args], input=input_text, text=True,
                              capture_output=True, check=False)

    def run_code(self, code: str, *, language: str = "python") -> dict[str, Any]:
        if language != "python":
            return {"status": "error", "result": f"Unsupported language: {language}",
                    "exit_code": None, "execution_id": None, "raw": None}
        job_name = f"sf-cap-{uuid.uuid4().hex[:10]}"
        script_b64 = base64.b64encode(code.encode("utf-8")).decode("ascii")
        manifest = textwrap.dedent(f"""
            apiVersion: batch/v1
            kind: Job
            metadata:
              name: {job_name}
              namespace: {self.namespace}
              labels:
                app: signal-forge-capability
            spec:
              ttlSecondsAfterFinished: 60
              backoffLimit: 0
              template:
                spec:
                  restartPolicy: Never
                  containers:
                    - name: runner
                      image: {self.python_image}
                      command: ["/bin/sh", "-c", "echo {script_b64} | base64 -d > /tmp/task.py && python /tmp/task.py"]
            """).strip()
        apply = self._run_kubectl(["apply", "-f", "-"], input_text=manifest)
        if apply.returncode != 0:
            return {"status": "error", "result": apply.stderr or apply.stdout,
                    "exit_code": apply.returncode, "execution_id": job_name, "raw": None}
        wait = self._run_kubectl(["wait", "--for=condition=complete", f"job/{job_name}",
                                  "-n", self.namespace, f"--timeout={self.timeout_seconds}s"])
        logs = self._run_kubectl(["logs", "-n", self.namespace, f"job/{job_name}"])
        log_text = ((logs.stdout or "") + (logs.stderr or "")).strip()
        ok = wait.returncode == 0
        self._run_kubectl(["delete", "job", job_name, "-n", self.namespace, "--wait=false"])
        return {"status": "ok" if ok else "error", "result": log_text,
                "exit_code": 0 if ok else 1, "execution_id": job_name,
                "raw": {"wait_stderr": wait.stderr}}

    def run_command(self, command: str) -> dict[str, Any]:
        job_name = f"sf-cmd-{uuid.uuid4().hex[:10]}"
        manifest = textwrap.dedent(f"""
            apiVersion: batch/v1
            kind: Job
            metadata:
              name: {job_name}
              namespace: {self.namespace}
            spec:
              ttlSecondsAfterFinished: 60
              backoffLimit: 0
              template:
                spec:
                  restartPolicy: Never
                  containers:
                    - name: runner
                      image: {self.python_image}
                      command: ["/bin/sh", "-c", {repr(command)}]
            """).strip()
        apply = self._run_kubectl(["apply", "-f", "-"], input_text=manifest)
        if apply.returncode != 0:
            return {"status": "error", "result": apply.stderr or apply.stdout,
                    "exit_code": apply.returncode, "execution_id": job_name, "raw": None}
        wait = self._run_kubectl(["wait", "--for=condition=complete", f"job/{job_name}",
                                  "-n", self.namespace, f"--timeout={self.timeout_seconds}s"])
        logs = self._run_kubectl(["logs", "-n", self.namespace, f"job/{job_name}"])
        ok = wait.returncode == 0
        self._run_kubectl(["delete", "job", job_name, "-n", self.namespace, "--wait=false"])
        return {"status": "ok" if ok else "error", "result": (logs.stdout or "").strip(),
                "exit_code": 0 if ok else 1, "execution_id": job_name, "raw": None}

    def close(self) -> None:
        pass
