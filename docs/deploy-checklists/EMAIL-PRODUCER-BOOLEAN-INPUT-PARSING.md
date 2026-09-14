# Email producer Airtable boolean input parsing

**Status:** PENDING Mike approval → merge → Production paste  
**Date:** 2026-09-14  
**Merged baseline:** PR #542 (`1ac4cea7`) introduced the parser; this follow-up bumps paste versions.  
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
| 1 | Mike approves version bump list | Mike | [ ] |
| 2 | Merge follow-up PR to `master` | Mike / Cursor | [ ] |
| 3 | Paste each script below (docblock → end; skip GitHub header) | Cursor (authorized) | [ ] |
| 4 | Confirm automation **inputs and triggers unchanged** in UI | Cursor / Mike | [ ] |
| 5 | Retain UI values: producers `testMode=false`; 072 `sendModeInput=live`; 118/119 season Live + dryRun=false | Cursor / Mike | [ ] |

## Airtable paste sources (this deploy)

| Automation | Live today (Automations table) | New GitHub / paste | Paste bundle |
|---|---:|---:|---|
| 071 | v4.5 | **v4.7** | [`071-v4.7-PASTE.txt`](./071-v4.7-PASTE.txt) |
| 072 | v4.9.2 | **v4.9.4** | [`072-v4.9.4-PASTE.txt`](./072-v4.9.4-PASTE.txt) |
| 073 | v4.9 | **v4.11** | [`073-v4.11-PASTE.txt`](./073-v4.11-PASTE.txt) |
| 074 | v3.6 | **v3.8** | [`074-v3.8-PASTE.txt`](./074-v3.8-PASTE.txt) |
| 076 | v8.15 | **v8.17** | [`076-v8.17-PASTE.txt`](./076-v8.17-PASTE.txt) |
| 078A | v1.7 | **v1.9** | [`078A-v1.9-PASTE.txt`](./078A-v1.9-PASTE.txt) |
| 117 | v2.2 | **v2.4** | [`117-v2.4-PASTE.txt`](./117-v2.4-PASTE.txt) |
| 118 | v2.1 | **v2.3** | [`118-v2.3-PASTE.txt`](./118-v2.3-PASTE.txt) |
| 119 | v1.8 | **v1.10** | [`119-v1.10-PASTE.txt`](./119-v1.10-PASTE.txt) |

Source path: `airtable/automations/shooting-challenge/` on `master` after merge.

## Explicit non-goals

- Do **not** change triggers, filters, or recipient allowlists.
- Do **not** re-run season simulation as part of this paste.
- Do **not** alter Communications Hub or Make scenarios for this fix.
- Do **not** run producers or create EHQ/Hub rows during paste verification.
