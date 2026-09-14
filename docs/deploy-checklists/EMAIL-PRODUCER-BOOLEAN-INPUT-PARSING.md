# Email producer input parsing — deployed contract

**Status:** Deployed and verified in published Automation-editor code on 2026-09-14.
**Scope:** `testMode`, `sendMode` / `sendModeInput`, `dryRun`, and `includeSchmidt` parsing in Tier-1 producers.

## Why this exists

Airtable can pass an input visibly set to `false` as the text value `"false"`. JavaScript treats that text as truthy if code calls `Boolean("false")`. The producers now use the shared parsing contract below instead.

| Value supplied by Airtable | Parsed boolean |
|---|---:|
| missing `testMode` / `dryRun` | safe default `true` |
| `false`, `"false"`, `0`, `"0"` | false |
| `true`, `"true"`, `1`, `"1"` | true |
| missing `includeSchmidt` | false |
| `Live` / `live` send mode | live |
| missing send mode | test |

The canonical helper lives in `airtable/automations/shooting-challenge/lib/automation-input-booleans.js` and is inlined into each Airtable script because Automation scripts cannot import repository modules at runtime.

## Deployed version set

| Automation | Version |
|---|---:|
| 071 | v4.7 |
| 072 | v4.9.4 |
| 073 | v4.11 |
| 074 | v3.8 |
| 076 | v8.17 |
| 078A | v1.9 |
| 117 | v2.4 |
| 118 | v2.3 |
| 119 | v1.10 |

## Operator rules

- Published Automation-editor code, compared to GitHub by normalized body hash, is the authority for a future drift check.
- Do not use the `Automations` tracking-table mirror to initiate a paste.
- Inputs, triggers, and secrets are UI configuration. Verify them visually, save, and re-open to confirm persistence.
- The `ingressSecret` for 079 must be present but must never be copied into repository files or evidence.
- A code or version change must include a bumped header version and an updated paste bundle before it is pasted to Production.

For current operating steps, see [`TIER-1-LAUNCH-OPS-RUNBOOK-20260911.md`](./TIER-1-LAUNCH-OPS-RUNBOOK-20260911.md). Dated cutover and proof documents are historical evidence, not promotion instructions.
