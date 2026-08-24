"""
Dev issuer: mint interim signed envelopes + register credential status.

  python -m identity_runtime.dev_issuer mint
  python -m identity_runtime.dev_issuer revoke --id urn:uuid:... --reason left_org
  python -m identity_runtime.dev_issuer status --id urn:uuid:...
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from identity_runtime.credential_status import (
    get_entry,
    new_credential_id,
    register_active,
    revoke,
)
from identity_runtime.did_key import (
    generate_keypair,
    private_to_pem,
    public_key_to_did_key,
)
from identity_runtime.envelope import sign_envelope

ROOT = Path(__file__).resolve().parent.parent
KEYS_DIR = ROOT / "dapp_api" / "dev_keys"
REG_PATH = ROOT / "dapp_api" / "trust_registry.json"
CREDS_DIR = ROOT / "dapp_api" / "dev_credentials"


def _load_or_create_issuer() -> tuple[Ed25519PrivateKey, str]:
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    pem_path = KEYS_DIR / "issuer_ed25519.pem"
    if pem_path.exists():
        private = serialization.load_pem_private_key(
            pem_path.read_bytes(), password=None
        )
        did = public_key_to_did_key(private.public_key())
        return private, did
    private, did = generate_keypair()
    pem_path.write_bytes(private_to_pem(private))
    (KEYS_DIR / "issuer_did.txt").write_text(did + "\n", encoding="utf-8")
    return private, did


def _ensure_registry(issuer_did: str) -> None:
    REG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if REG_PATH.exists():
        reg = json.loads(REG_PATH.read_text(encoding="utf-8"))
    else:
        reg = []
    found = next((e for e in reg if e.get("issuer_did") == issuer_did), None)
    types = [
        "OrganizationMembership",
        "HumanitarianAnalyst",
        "IncidentCommander",
        "ResearchPartner",
        "SensorOperator",
    ]
    if found:
        found["status"] = "active"
        found["allowed_credential_types"] = types
        found["revocation_method"] = "status_list"
    else:
        reg.append(
            {
                "issuer_did": issuer_did,
                "display_name": "Signal Forge Dev Issuer",
                "status": "active",
                "allowed_credential_types": types,
                "revocation_method": "status_list",
                "effective_from": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            }
        )
    REG_PATH.write_text(json.dumps(reg, indent=2), encoding="utf-8")


def mint(
    private: Ed25519PrivateKey,
    issuer_did: str,
    credential_type: str,
    subject_did: str,
    name: str,
    days_valid: int = 365,
) -> dict:
    now = datetime.now(timezone.utc)
    cred_id = new_credential_id()
    payload = {
        "id": cred_id,
        "type": "SignalForgeCredential",
        "issuer": issuer_did,
        "issuanceDate": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expirationDate": (now + timedelta(days=days_valid)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "credentialSubject": {
            "id": subject_did,
            "credentialType": credential_type,
            "name": name,
            "org": issuer_did,
            "credentialId": cred_id,
        },
    }
    envelope = sign_envelope(payload, private, issuer_did)
    register_active(
        cred_id,
        issuer_did=issuer_did,
        subject_id=subject_did,
        credential_type=credential_type,
    )
    return envelope


def cmd_mint(_: argparse.Namespace) -> None:
    private, issuer_did = _load_or_create_issuer()
    _ensure_registry(issuer_did)
    CREDS_DIR.mkdir(parents=True, exist_ok=True)

    subjects = {
        "analyst": ("HumanitarianAnalyst", "Alex Analyst"),
        "commander": ("IncidentCommander", "Casey Commander"),
        "research": ("ResearchPartner", "Riley Research"),
    }

    print("Issuer DID:", issuer_did)
    print("Trust registry:", REG_PATH)
    print("Credential status: dapp_api/credential_status.json")

    for slug, (ctype, name) in subjects.items():
        sub_priv, sub_did = generate_keypair()
        (KEYS_DIR / f"subject_{slug}.pem").write_bytes(private_to_pem(sub_priv))
        env = mint(private, issuer_did, ctype, sub_did, name)
        out = CREDS_DIR / f"{slug}.vc.json"
        out.write_text(json.dumps(env, indent=2), encoding="utf-8")
        print(
            f"  wrote {out}\n"
            f"    id={env.get('id')}\n"
            f"    subject={sub_did}\n"
            f"    type={ctype}"
        )

    print("Done. Present via POST /auth/present")


def cmd_revoke(args: argparse.Namespace) -> None:
    ok, msg = revoke(args.id, reason=args.reason or "unspecified")
    print(msg if ok else f"FAIL: {msg}")
    entry = get_entry(args.id)
    if entry:
        print(json.dumps(entry, indent=2))
    sys.exit(0 if ok else 1)


def cmd_status(args: argparse.Namespace) -> None:
    entry = get_entry(args.id)
    if not entry:
        print("not_listed")
        sys.exit(1)
    print(json.dumps(entry, indent=2))
    sys.exit(0 if entry.get("status") == "active" else 2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Signal Forge dev credential issuer")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("mint", help="Mint demo VCs (default if no subcommand)")

    p_rev = sub.add_parser("revoke", help="Revoke a credential by id")
    p_rev.add_argument("--id", required=True, help="Credential id (urn:uuid:...)")
    p_rev.add_argument("--reason", default="unspecified")

    p_st = sub.add_parser("status", help="Show credential status entry")
    p_st.add_argument("--id", required=True)

    args = parser.parse_args()
    if args.command == "revoke":
        cmd_revoke(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        cmd_mint(args)


if __name__ == "__main__":
    main()