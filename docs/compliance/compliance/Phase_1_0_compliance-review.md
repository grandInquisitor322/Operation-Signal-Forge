# Compliance Review

**Date of record** 07-29-2026
**Time of record:** 6:19 AM 

## Checklist

- Does every sensor module have documented responsibilities?
- Are data sources documented (OpenCellID, Starlink, etc.)?
- Are external APIs and licenses recorded?
- Are configuration variables documented?
- Are security assumptions written down?
- Is there a basic privacy and data-handling policy?
- Are deployment prerequisites documented?

## Status by item

| **#** | **Item** | **Status** | **Primary artifact** |
| --- | --- | --- | --- |
| 1 | Sensor module responsibilities | **Done** | docs/engineering/sensor-responsibilities.md (+ module guide, ADRs) |
| 2 | Data sources documented | **Done** | docs/compliance/data-sources.md |
| 3 | External APIs & licenses | **Done** | docs/compliance/third-party-apis-and-licenses.md (fields filled) |
| 4 | Configuration variables | **Done** | docs/engineering/configuration-reference.md |
| 5 | Security assumptions | **Done** | docs/architecture/security-assumptions.md |
| 6 | Privacy / data-handling | **Done** | docs/compliance/privacy-and-data-handling.md |
| 7 | Deployment prerequisites | **Done** | docs/engineering/deployment-prerequisites.md |

## Polish items

| **Polish item** | **Status** | **Notes** |
| --- | --- | --- |
| Merge filled license tables (no _TBD_ for public terms) | **Done** (draft ready) | Keep per-deploy blanks: keys, account ID, tier, Leaflet pin |
| First-party LICENSE = Apache-2.0 | **Done** | Root file; referenced by licenses register |
| Honest v0.2 gaps (radar/thermal/acoustic still in Fusion) | **Documented** | In sensor-responsibilities |
| Privacy contact + numeric retention | **Still deployer TBD** | Placeholders by design |
| README links to docs/compliance/ | **Optional** | Improves discoverability |
| Commit all new docs to git | **Confirm locally** | Ensure they’re on main / tagged if desired |