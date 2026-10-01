# Deployment Prerequisites — Operation Signal Forge

**Version:** 0.2 (Architecture Baseline)  
**Status:** Active  
**Related:**`docs/engineering/configuration-reference.md`, `README.md`, `infra/` SAM templates, `docs/compliance/third-party-apis-and-licenses.md`

This document lists **what must be in place before** `sam build` / `sam deploy` and before wiring the dashboard or field ingest. It is a gate checklist, not a full runbook.

---

## 1. Purpose

Confirm people, accounts, tools, and secrets exist **before** deploying Fusion, dashboard API, alerts, or sensor ingest. Skipping these steps is a common cause of partial stacks and misconfigured production.

---

## 2. People and ownership

| Role | Needed for |
|------|------------|
| AWS account admin (or sufficient IAM) | Create stack, IAM roles, SNS subscriptions |
| SAR / ops owner | Alert email/SMS targets, dashboard access policy |
| Privacy / compliance contact (recommended) | SMS consent, retention, data-subject requests |
| Developer with repo access | Build, deploy, run simulators |

---

## 3. Accounts and external services

| Account / service | Required? | Purpose |
|-------------------|-----------|---------|
| AWS account | **Yes** | Lambda, DynamoDB, API Gateway, SNS, S3, CloudFront, IoT (as designed) |
| AWS region chosen | **Yes** | All resources in one primary region unless multi-region is designed |
| OpenCellID (or cell DB) account | If celltower enabled | API key for lookups |
| Daytona account | **No** for prod | Local/module tests only |
| GitHub (or source host) | Recommended | Source control; not required on the AWS box itself |
| SMS/email endpoints | If alerts enabled | SNS subscriptions; SMS may need extra telecom setup |

---

## 4. Local toolchain

Install and verify on the deploy workstation:

| Tool | Purpose | Check |
|------|---------|--------|
| AWS CLI v2 | Credentials, S3 sync, debugging | `aws sts get-caller-identity` |
| AWS SAM CLI | `sam build`, `sam deploy` | `sam --version` |
| Python 3.10+ (match Lambda runtime) | Local tests, simulators | `python --version` |
| pip | Dependencies | `pip --version` |
| Git | Checkout release tag | `git --version` |
| Docker (if SAM requires it for builds) | Consistent Lambda builds | `docker --version` |

**Recommended:** Deploy from a clean checkout of a known tag (e.g. `v0.2.0-architecture-baseline` or later).

---

## 5. AWS credentials and IAM

Before deploy:

1. Configure credentials with permission to create the stack’s resources (Lambda, DynamoDB, IAM roles, API Gateway, SNS, S3, etc.).
2. Prefer a dedicated deploy role or profile over long-lived root keys.
3. Confirm account ID and region:

```bash
aws sts get-caller-identity
aws configure get region
```