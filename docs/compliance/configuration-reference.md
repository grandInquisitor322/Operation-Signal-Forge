# Configuration Reference — Operation Signal Forge

**Version:** 0.2 (Architecture Baseline)  
**Status:** Active  
**Related:** `docs/architecture/security-assumptions.md`, `docs/compliance/privacy-and-data-handling.md`, `docs/engineering/deployment-prerequisites.md` (forthcoming)

This document lists **runtime configuration** used by Signal Forge components: environment variables, sensible defaults, and where each setting applies. Secrets must never be committed to git.

---

## 1. Principles

1. **Configuration over code** for environment-specific values (table names, thresholds, topic ARNs).
2. **Secrets** (API keys) live in environment variables or a secrets manager — not in source.
3. **Defaults** exist for local/dev convenience; production must set explicit values.
4. Changing fusion weights or thresholds is an **operational** decision; document overrides in the deploy runbook.

---

## 2. Fusion Engine (`fusion_engine.py`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DETECTIONS_TABLE` | Recommended | `signal-forge-detections-prod` | DynamoDB table for per-cell detection records |
| `ALERT_TOPIC_ARN` | Optional | unset / empty | SNS topic ARN for high-confidence alerts; if unset, alerts are skipped |
| `HIGH_CONFIDENCE_THRESHOLD` | Optional | `0.75` | Fused probability at or above which SNS alert may fire |

### Behavior notes

- Scores are stored as DynamoDB `Decimal` values via internal helpers — not configured by env.
- Starlink handling uses `lambda_sensors_starlink.process`; no Starlink-specific env vars in Fusion at v0.2.
- Grid cell id is derived from lat/lon truncation (code constant); changing resolution requires a code change, not an env var.

### Example (Lambda console / SAM)

```bash
DETECTIONS_TABLE=signal-forge-detections-prod
ALERT_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:signal-forge-alerts
HIGH_CONFIDENCE_THRESHOLD=0.75
```