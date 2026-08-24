"""DApp API with server-side AuthZ. Capability Layer gets AuthZContext only."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from capability_layer import CapabilityLayer
from capability_layer.adapters import InMemoryDetectionReader
from dapp_api.authz import (
    authorize_capability,
    login as auth_login,
    logout as auth_logout,
    resolve_token,
)

SAMPLE = {
    "cell_id": "10.4806_-66.9036",
    "site_id": "caracas-site-7",
    "lat": 10.4806,
    "lon": -66.9036,
    "radar_score": 0.72,
    "thermal_score": 0.55,
    "acoustic_score": 0.4,
    "starlink_score": 0.63,
    "celltower_score": 0.0,
    "fused_probability": 0.81,
    "status": "unassigned",
}

_layer = CapabilityLayer(detections=InMemoryDetectionReader([SAMPLE]))

CAPABILITY_ROUTES = {
    "/capabilities/generate_detection_brief": "generate_detection_brief",
    "/capabilities/recommend_next_sensor": "recommend_next_sensor",
    "/capabilities/investigate_anomaly": "investigate_anomaly",
}


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers", "Content-Type, Authorization"
        )

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read_json()
        if path == "/auth/login":
            return self._handle_login(body)
        if path == "/auth/logout":
            return self._handle_logout()
        cap = CAPABILITY_ROUTES.get(path)
        if cap:
            return self._handle_capability(cap, body)
        return self._json(404, {"error": "not found"})

    def _handle_login(self, body):
        token, ctx, err = auth_login(
            body.get("email", ""), body.get("password", "")
        )
        if err:
            return self._json(401, {"error": err})
        return self._json(200, {"token": token, "authz": ctx.to_dict()})

    def _handle_logout(self):
        token = self._bearer_token()
        if token:
            auth_logout(token)
        return self._json(200, {"ok": True})

    def _handle_capability(self, capability, body):
        ctx, err = resolve_token(self._bearer_token())
        if err:
            return self._json(401, {"error": err})
        allowed, reason = authorize_capability(ctx, capability)
        if not allowed:
            return self._json(
                403,
                {
                    "error": reason,
                    "capability": capability,
                    "role": ctx.role,
                    "scopes": ctx.scopes,
                },
            )
        cell_id = body.get("cell_id") or SAMPLE["cell_id"]
        params = {
            "cell_id": cell_id,
            "authz": {
                "subject_id": ctx.subject_id,
                "org_id": ctx.org_id,
                "role": ctx.role,
                "scopes": ctx.scopes,
                "assurance": ctx.assurance,
                "presentation_id": ctx.presentation_id,
            },
        }
        result = _layer.request_capability(capability, params)
        payload = result.to_dict()
        payload["authz_receipt"] = {
            "subject_id": ctx.subject_id,
            "role": ctx.role,
            "capability": capability,
            "decision": "allow",
        }
        return self._json(200, payload)

    def _bearer_token(self):
        hdr = self.headers.get("Authorization") or ""
        if hdr.lower().startswith("bearer "):
            return hdr[7:].strip()
        return None

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}

    def _json(self, code, obj):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


def main():
    host, port = "127.0.0.1", 8787
    print("DApp API (AuthZ enforced) http://%s:%s" % (host, port))
    HTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()