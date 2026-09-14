# Email producer Airtable boolean input parsing

**Status:** PENDING Production paste (GitHub PR first)  
**Date:** 2026-09-14  
**Scope:** Strict parsing of automation inputs `testMode`, `sendMode`, `dryRun`, `includeSchmidt`  
**Does not change:** automation triggers, recipient routing, Hub templates, Make webhooks  

**Rule:** Production changes are not official until this document exists in GitHub. See [v2/04 § Official promotion documentation](../v2/04-ai-development-standards.md#official-promotion-documentation-required).

---

## Root cause

Airtable Automation script inputs often deliver the visible value `false` as the **text** `"false"`. JavaScript `Boolean("false")` is `true`, so producers using:

```js
cfg.testMode === undefined ? true : Boolean(cfg.testMode)
```

armed Test Mode even when the Airtable UI showed `false`.

## Fix

Shared `parseAutomationBoolean` / `parseAutomationSendMode` (canonical body in  
`airtable/automations/shooting-challenge/lib/automation-input-booleans.js`, **inlined** into each producer — Airtable cannot `require()` the lib).

| Input | Documented safe default when missing |
|---|---|
| `testMode` | `true` (safe / test) |
| `dryRun` | `true` |
| `includeSchmidt` | `false` |
| `sendMode` / `sendModeInput` | `test` |

Text `"false"` / `"0"` / `0` → false; `"true"` / `"1"` / `1` → true; `"Live"` → live.

## Promotion order

| # | Step | Owner | Done |
|---|------|-------|------|
| 1 | Merge GitHub PR for this change | Mike | [ ] |
| 2 | Paste each script below (docblock → end; skip GitHub header) | Mike | [ ] |
| 3 | Confirm automation **inputs and triggers unchanged** in UI | Mike | [ ] |
| 4 | Spot-check one producer with UI `testMode = false` (allowlisted only) | Mike | [ ] |

## Airtable paste sources

| Automation | GitHub file | Version |
|---|---|---|
| 071 | `071-email-notifications-and-external-handoffs-send-homework-feedback-email-webhook.js` | v4.6 |
| 072 | `072-email-notifications-and-external-handoffs-build-weekly-summary-email-package.js` | v4.9.3 |
| 073 | `073-email-notifications-and-external-handoffs-send-video-feedback-parent-email-webhook.js` | v4.10 |
| 074 | `074-email-notifications-and-external-handoffs-send-weekly-summary-email-package-to-make.js` | v3.7 |
| 076 | `076-email-notifications-and-external-handoffs-build-daily-submission-email-package.js` | v8.16 |
| 078A | `078A-email-notifications-and-external-handoffs-enrollment-create-welcome-email-handoff.js` | v1.8 |
| 117 | `117-zoom-send-recording-approval-email-to-make.js` | v2.3 |
| 118 | `118-email-notifications-and-external-handoffs-schedule-weekly-summary-email-build.js` | v2.2 |
| 119 | `119-email-notifications-and-external-handoffs-schedule-weekly-summary-email-send.js` | v1.9 |

Paste path: `airtable/automations/shooting-challenge/` in the repo tip after merge.

## Explicit non-goals

- Do **not** change triggers, filters, or recipient allowlists.
- Do **not** re-run season simulation as part of this paste.
- Do **not** alter Communications Hub or Make scenarios for this fix.
