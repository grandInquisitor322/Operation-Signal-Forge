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
Trust Registry governance CLI (Phase 2.3).

Actor must have TrustRegistryAdmin authority (admin list, authz scope, or bootstrap).

  python -m identity_runtime.trust_gov propose --did ... --name "Org" --types HumanitarianAnalyst --actor gov-admin
  python -m identity_runtime.trust_gov approve --did ... --types HumanitarianAnalyst --actor gov-admin --ref GOV-001
  python -m identity_runtime.trust_gov suspend --did ... --actor gov-admin --reason review
  python -m identity_runtime.trust_gov restore --did ... --actor gov-admin
  python -m identity_runtime.trust_gov revoke --did ... --actor gov-admin
  python -m identity_runtime.trust_gov emergency-suspend --did ... --actor gov-admin
  python -m identity_runtime.trust_gov list
  python -m identity_runtime.trust_gov audit
"""

from __future__ import annotations

import argparse
import json
import sys

from identity_runtime.trust_registry import (
    approve_issuer,
    load_audit,
    load_registry,
    mark_under_review,
    propose_issuer,
    restore_issuer,
    revoke_issuer,
    set_allowed_types,
    suspend_issuer,
)


def _types(s: str) -> list[str]:
    return [t.strip() for t in s.split(",") if t.strip()]


def main() -> None:
    p = argparse.ArgumentParser(
        description="Trust Registry governance (requires TrustRegistryAdmin actor)"
    )
    sub = p.add_subparsers(dest="cmd")

    pr = sub.add_parser("propose")
    pr.add_argument("--did", required=True)
    pr.add_argument("--name", required=True)
    pr.add_argument("--types", required=True, help="comma-separated requested types")
    pr.add_argument("--actor", required=True)
    pr.add_argument("--org", default="")
    pr.add_argument("--ref", default="")

    ur = sub.add_parser("under-review")
    ur.add_argument("--did", required=True)
    ur.add_argument("--actor", required=True)
    ur.add_argument("--reason", default="governance_review")

    ap = sub.add_parser("approve")
    ap.add_argument("--did", required=True)
    ap.add_argument("--types", required=True, help="authorized types")
    ap.add_argument("--actor", required=True)
    ap.add_argument("--ref", default="")
    ap.add_argument("--reason", default="approved")

    su = sub.add_parser("suspend")
    su.add_argument("--did", required=True)
    su.add_argument("--actor", required=True)
    su.add_argument("--reason", default="suspended")

    es = sub.add_parser("emergency-suspend")
    es.add_argument("--did", required=True)
    es.add_argument("--actor", required=True)
    es.add_argument("--reason", default="emergency_suspected_compromise")

    rs = sub.add_parser("restore")
    rs.add_argument("--did", required=True)
    rs.add_argument("--actor", required=True)
    rs.add_argument("--reason", default="restored_after_review")
    rs.add_argument("--ref", default="")

    rv = sub.add_parser("revoke")
    rv.add_argument("--did", required=True)
    rv.add_argument("--actor", required=True)
    rv.add_argument("--reason", default="revoked")
    rv.add_argument("--ref", default="")

    er = sub.add_parser("emergency-revoke")
    er.add_argument("--did", required=True)
    er.add_argument("--actor", required=True)
    er.add_argument("--reason", default="emergency_revoke")

    st = sub.add_parser("set-types")
    st.add_argument("--did", required=True)
    st.add_argument("--types", required=True)
    st.add_argument("--actor", required=True)

    sub.add_parser("list")
    sub.add_parser("audit")

    args = p.parse_args()

    if args.cmd == "propose":
        ok, msg, entry = propose_issuer(
            issuer_did=args.did,
            display_name=args.name,
            requested_credential_types=_types(args.types),
            actor=args.actor,
            organization=args.org,
            governance_reference=args.ref,
        )
        print(msg if ok else f"FAIL: {msg}")
        if entry:
            print(json.dumps(entry, indent=2))
        sys.exit(0 if ok else 1)

    if args.cmd == "under-review":
        ok, msg = mark_under_review(
            args.did, actor=args.actor, reason=args.reason
        )
        print(msg if ok else f"FAIL: {msg}")
        sys.exit(0 if ok else 1)

    if args.cmd == "approve":
        ok, msg = approve_issuer(
            args.did,
            actor=args.actor,
            allowed_credential_types=_types(args.types),
            reason=args.reason,
            governance_reference=args.ref,
        )
        print(msg if ok else f"FAIL: {msg}")
        sys.exit(0 if ok else 1)

    if args.cmd == "suspend":
        ok, msg = suspend_issuer(
            args.did, actor=args.actor, reason=args.reason
        )
        print(msg if ok else f"FAIL: {msg}")
        sys.exit(0 if ok else 1)

    if args.cmd == "emergency-suspend":
        ok, msg = suspend_issuer(
            args.did,
            actor=args.actor,
            reason=args.reason,
            emergency=True,
        )
        print(msg if ok else f"FAIL: {msg}")
        sys.exit(0 if ok else 1)

    if args.cmd == "restore":
        ok, msg = restore_issuer(
            args.did,
            actor=args.actor,
            reason=args.reason,
            governance_reference=args.ref,
        )
        print(msg if ok else f"FAIL: {msg}")
        sys.exit(0 if ok else 1)

    if args.cmd == "revoke":
        ok, msg = revoke_issuer(
            args.did,
            actor=args.actor,
            reason=args.reason,
            governance_reference=args.ref,
        )
        print(msg if ok else f"FAIL: {msg}")
        sys.exit(0 if ok else 1)

    if args.cmd == "emergency-revoke":
        ok, msg = revoke_issuer(
            args.did,
            actor=args.actor,
            reason=args.reason,
            emergency=True,
        )
        print(msg if ok else f"FAIL: {msg}")
        sys.exit(0 if ok else 1)

    if args.cmd == "set-types":
        ok, msg = set_allowed_types(
            args.did,
            actor=args.actor,
            allowed_credential_types=_types(args.types),
        )
        print(msg if ok else f"FAIL: {msg}")
        sys.exit(0 if ok else 1)

    if args.cmd == "list":
        print(json.dumps(load_registry(), indent=2))
        return

    if args.cmd == "audit":
        print(json.dumps(load_audit(), indent=2))
        return

    p.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()