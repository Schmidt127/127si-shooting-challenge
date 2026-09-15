# Production architecture pack — Shooting Challenge

**Status:** Authoritative cold-start documentation (FUT-058)  
**Audit date:** 2026-09-15  
**Live evidence:** Airtable MCP against Production SC `appn84sqPw03zEbTT` and Communications Hub `appYG1t5DBRimHBCT`  
**Git tip at audit:** `origin/master` @ `4c3074a7`  
**Automation presence (closeout):** **50/50 deployed** — **009 v1.3 / SC-160** Mike-confirmed production-required

This folder is the **single entry point** for a developer or AI agent with no prior conversation history. Prefer these files over older root/overview drafts when they disagree.

| Document | Purpose |
|----------|---------|
| [SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md) | What the product is; repos; bases; hosting |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | End-to-end data flows |
| [AIRTABLE_SCHEMA.md](./AIRTABLE_SCHEMA.md) | Important tables, IDs, relationships |
| [AUTOMATIONS.md](./AUTOMATIONS.md) | Live automation inventory (ACTIVE / UNDEPLOYED / LEGACY) |
| [XP_AND_PROGRESSION.md](./XP_AND_PROGRESSION.md) | XP Sources, Source Keys, levels, achievements |
| [COMMUNICATIONS.md](./COMMUNICATIONS.md) | SC ↔ Communications Hub boundary |
| [OPERATIONS.md](./OPERATIONS.md) | Troubleshooting first-looks |
| [ENVIRONMENT.md](./ENVIRONMENT.md) | Env var names and purpose (no secrets) |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | How each surface ships |
| [SOURCE_OF_TRUTH.md](./SOURCE_OF_TRUTH.md) | Ownership matrix |
| [CHANGELOG_AND_STATUS.md](./CHANGELOG_AND_STATUS.md) | Completed systems, debt, intentional legacy |

**Full audit report:** [`../audits/FINAL-SYSTEM-AUDIT-REPORT-20260915.md`](../audits/FINAL-SYSTEM-AUDIT-REPORT-20260915.md)

## Companion live ops docs (still required)

| Doc | Role |
|-----|------|
| [`../CURRENT-TRUTH.md`](../CURRENT-TRUTH.md) | Dated live overlays (versions, sims, pending pastes) |
| [`../AUTHORITY-MAP.md`](../AUTHORITY-MAP.md) | Who overrides whom |
| [`../automation-index.md`](../automation-index.md) | Detailed per-script index (may lag MCP overlay) |
| [`../integrations/email-send-plane.md`](../integrations/email-send-plane.md) | Email delivery authority |
| [`../../SYSTEM_OVERVIEW.md`](../../SYSTEM_OVERVIEW.md) | Root overview (kept in sync with this pack) |

## Production constraints

- Do not delete fields, automations, or historical XP without dependency review + Mike approval.
- Script version authority = **Airtable Automation editor**, not the Automations tracking table.
- Parent email delivery = Communications Hub → **Resend** (Make.com is not the email sender).
