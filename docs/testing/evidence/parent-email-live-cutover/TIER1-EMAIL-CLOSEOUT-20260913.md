# Tier-1 email closeout — 2026-09-13

**Production base:** `appn84sqPw03zEbTT`  
**Allowlisted recipient:** `schmidt@fairfieldbasketballclub.com` only  
**GitHub branch:** `cursor/tier1-email-closeout-e05f`

## A. GitHub source-of-truth sync

| Slot | Production (before) | GitHub (before) | After |
|------|--------------------:|----------------:|-------|
| 076 | v8.15 | v8.15 | aligned (no paste) |
| 071 | v4.5 | v4.5 | aligned |
| 072 | v4.9.2 | v4.9.2 | aligned |
| 073 | v4.9 | v4.7 | **backported v4.9 to GitHub** |
| 074 | v3.6 | v3.6 | aligned |
| 117 | v2.2 | v2.2 | aligned |

**073 diff review:** Production v4.9 differs from GitHub v4.7 only by documented v4.8 canonical asset-evidence check + v4.9 verification bump. No recipient, webhook, secret, or routing changes detected.

## B. UI safety attestation

See [`2026-09-13-ui-attestation.json`](./2026-09-13-ui-attestation.json).

**Method:** Production `Automation Code` matches GitHub; script docblocks define trigger tables and test-safe defaults. **Automations table `Trigger table` / `Conditions` columns are stale and were not used as authority** (071 Homework Completions column happens to match; 072/073/074/076/117/079 columns do not).

**API limitation:** Input-variable UI bindings (`testMode`, `dryRun`, `ingressSecret`) are not readable via REST. Attestation relies on unchanged Live automations + script defaults. **079 `ingressSecret` requires Mike UI confirm.**

## C. Disposable proof (`verify-all --skip-welcome --apply`)

Evidence: [`2026-09-13-verify-all-apply.json`](./2026-09-13-verify-all-apply.json)

| Path | Result | Handoff key | Recipient | Test Mode? | Hub | Dupes |
|------|--------|-------------|-----------|------------|-----|-------|
| WEEKLY | **PASS** | `WEEKLY_ATHLETE_SUMMARY\|WEEKLY_ATHLETE_SUMMARY\|recwEXQFyV0IG7240` | schmidt@ only | true | Accepted | 1 |
| ZOOM_RECORDING_APPROVAL | **PASS** | `ZOOM_RECORDING_APPROVAL\|ZOOM_ATTENDANCE\|recjlZvYlzDKDZGas` | schmidt@ only | true | Accepted | 1 |
| DAILY | BLOCKED | — | — | — | — | 0 |
| HOMEWORK | SKIPPED (harness) | — | — | — | — | — |
| VIDEO | SKIPPED (harness) | — | — | — | — | — |

**DAILY blocker:** `Activity Date Is Future?=1` on disposable submission — 2027 challenge dates vs wall-clock gate; `Count This Submission?` stays 0.

**HOMEWORK / VIDEO:** Harness documents required upstream chains (064/065/078 and 013/070b/070c); not armed in this run by design.

**Preflight:** exit 0 — all producer versions match; `realFamilyCount=0`.

**No family email sent.** EHQ rows created for WEEKLY + ZOOM paths only; both `Test Mode?=true` and Hub `Accepted`.

## Remaining for family-email launch

1. Mike UI confirm **079 `ingressSecret`** and producer input variables (`testMode=true`, 118/119 `dryRun=true`).
2. Complete disposable proofs for **DAILY**, **HOMEWORK**, **VIDEO** (manual PKG-007 / sc-multi-asset-homework setup or season-date gate adjustment for DAILY).
3. Explicit approval to flip Live inputs per Phase E runbook — **not done in this closeout**.
