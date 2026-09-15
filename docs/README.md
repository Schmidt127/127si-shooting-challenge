# Documentation index

This is the navigation entry point for the 127 SI Shooting Challenge repository.

## Start with current authority

| Need | Open |
|---|---|
| **Cold-start architecture pack** | [production-architecture/README.md](./production-architecture/README.md) |
| **Frozen production baselines + future-work categories** | [production-architecture/FROZEN_BASELINE_AND_FUTURE_WORK.md](./production-architecture/FROZEN_BASELINE_AND_FUTURE_WORK.md) |
| FUT-058 final system audit (closed) | [audits/FINAL-SYSTEM-AUDIT-REPORT-20260915.md](./audits/FINAL-SYSTEM-AUDIT-REPORT-20260915.md) |
| Current verified project state | [CURRENT-TRUTH.md](./CURRENT-TRUTH.md) |
| Active implementation roadmap | [MASTER_REMAINING_WORK_LIST.md](../MASTER_REMAINING_WORK_LIST.md) |
| Engineering and operating rules | [ENGINEERING_CONSTITUTION.md](./ENGINEERING_CONSTITUTION.md) |
| System and ownership authority | [AUTHORITY-MAP.md](./AUTHORITY-MAP.md) |
| Current operational snapshot | [PROJECT_STATE.md](./PROJECT_STATE.md) |
| Current email delivery plane | [integrations/email-send-plane.md](./integrations/email-send-plane.md) |
| Automation lookup | [automation-index.md](./automation-index.md) |
| Active-document routing | [ACTIVE-DOCS-INDEX.md](./ACTIVE-DOCS-INDEX.md) |

### Documentation hierarchy (do not confuse)

| Layer | Meaning |
|---|---|
| Current production truth | What is running now — CURRENT-TRUTH + architecture pack |
| Frozen production baseline | Exact SC + Hub SHAs in FROZEN_BASELINE_AND_FUTURE_WORK |
| Operations | How to operate current prod — OPERATIONS / DEPLOYMENT / email-send-plane |
| Optional cleanup | Non-blocking hygiene — does **not** reopen FUT-058 |
| Future product work | MASTER_REMAINING_WORK_LIST + Master Future Work List |
| Future migration | Separate; **not started** — FROZEN_BASELINE § F |
| Legacy / historical | Make/Gmail diagrams and retired scripts — labeled only |

## Important authority rules

- The **Airtable Automation editor** is the authority for published automation code and its version header. The Automations tracking table is operational metadata only.
- The passed Perfect Mike Schmidt simulation is historical evidence: pre-restore acceptance was **4,980 active XP / 170 events**; post-restore future-date deactivation is expected and does not change that result.
- Historical plans, probes, prior runbooks, Foundation Reset material, `next-wave/`, and `chatgpt-sources/` are reference material unless the Active Docs Index explicitly routes to them.

## Working in this repository

Read [AGENTS.md](../AGENTS.md) before making changes. For implementation work, keep the Master Remaining Work List and Current Truth aligned; do not use historical plans as a current instruction source.

## Historical reference

Historical evidence is intentionally retained. Use [ARCHIVED-AND-SUPERSEDED-FILES.md](./ARCHIVED-AND-SUPERSEDED-FILES.md) to determine whether an older document is evidence, superseded guidance, or a retired path.
