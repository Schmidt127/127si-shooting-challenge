# Tier 1 email operations — current operator runbook

**Current as of:** 2026-09-14
**Production base:** `appn84sqPw03zEbTT`
**Delivery plane:** Airtable producer → Email Handoff Queue → Automation 079 → Communications Hub → Resend

This is the current operator guide for Shooting Challenge email. Published Airtable Automation-editor code is the production authority. GitHub `master` is the source used to compare that published code. The `Automations` tracking table is a convenience mirror only; do not use it to decide whether code must be pasted.

## Current published producer versions

| Automation | Version |
|---|---:|
| 071 — Homework feedback | v4.7 |
| 072 — Weekly package | v4.9.4 |
| 073 — Video feedback | v4.11 |
| 074 — Weekly send | v3.8 |
| 076 — Daily submission | v8.17 |
| 078A — Welcome | v1.9 |
| 079 — Hub dispatcher | v2.5 |
| 117 — Zoom recording approval | v2.4 |
| 118 — Weekly build schedule | v2.3 |
| 119 — Weekly send schedule | v1.10 |

## Standard preflight

Before changing email modes, running a disposable proof, or pasting a producer:

1. Check Communications Hub health and confirm its transactional backlog is understood.
2. Confirm no unintended Email Handoff Queue backlog is eligible for delivery.
3. Compare **published editor code** against GitHub by version and normalized body hash. Do not rely on the tracking-table version field.
4. In Airtable's Automation editor, confirm the trigger and dynamic `recordId` mapping are unchanged. Never hard-code a record ID or recipient.
5. Confirm Automation 079 is ON and its `ingressSecret` is present. The secret is UI-only; do not copy it into GitHub or reports.

## Boolean and send-mode inputs

Producer scripts now parse Airtable values safely: the visible string `"false"` is treated as false, rather than JavaScript's truthy `Boolean("false")` behavior.

| Input | Missing-value default | Live value | Safe rollback value |
|---|---|---|---|
| `testMode` | `true` | `false` | `true` |
| `sendModeInput` / `sendMode` | `test` | `live` / `Live` | `test` |
| `dryRun` | `true` | `false` | `true` |
| `includeSchmidt` | `false` | `false` unless deliberately approved | `false` |

When changing an input, save, re-open the Automation editor, and confirm the value persisted. Do not manually run a producer merely to test a setting.

## When a paste is actually needed

Do not paste because an older checklist says a paste is pending. Paste only when the published editor body/version is behind the matching GitHub body/version, after a reviewed PR is merged.

For an approved paste:

1. Use the matching current `*-PASTE.txt` bundle generated from `master`.
2. Preserve the existing trigger, conditions, input variables, and ON/OFF state.
3. Paste the Automation body exactly as directed by the bundle; do not edit it in the browser.
4. Save, re-open, and record published version plus normalized hash verification.
5. Run the repository paste-integrity check. A paste alone is not a reason to send email.

## Delivery safety

- Resend through the Communications Hub is the only Shooting Challenge parent-email delivery plane.
- Make/Gmail parent-email routes are retired; legacy `Send to Make?` fields are arm flags, not evidence of a Make email send.
- Email Handoff Queue status and Hub delivery/audit rows are the operational evidence for a delivery.
- Use a deliberate disposable proof before a broad live change. During a simulation, the approved recipient is `schmidt@fairfieldbasketballclub.com` only.
- For normal family operation, recipient selection must come from the cleaned enrollment contact fields; do not use an allowlist as a substitute for family-contact validation.

## Emergency rollback

Set affected producers back to `testMode=true`; set 072 to test send mode; set 118/119 `dryRun=true`; and disable scheduled arms only if a full weekly-email pause is necessary. Leave 079 ON unless the dispatcher itself is the confirmed fault. Preserve queue and Hub audit evidence; do not bulk-delete delivery records in an incident.

## Historical material

The dated cutover packets and proof reports remain as evidence only. Start with this document and [`EMAIL-PRODUCER-BOOLEAN-INPUT-PARSING.md`](./EMAIL-PRODUCER-BOOLEAN-INPUT-PARSING.md) for current operation.
