# Email send plane — current state

**Status:** Current — published Automation-editor code and GitHub are aligned as of 2026-09-14.
**Scope:** Shooting Challenge parent and athlete notification delivery.

## Architecture

```text
Airtable producer → Email Handoff Queue → Automation 079 → Communications Hub → Resend
```

Resend through the Communications Hub is the only Shooting Challenge parent-email delivery plane. Make/Gmail parent-email routes are retired. Legacy `Send to Make?` fields are workflow arm flags; they are not a Make email send.

## Authority and drift checks

Published Airtable Automation-editor code is the Production authority. Compare it with GitHub `master` using the script version and normalized body hash. The `Automations` tracking table is a convenience mirror for names and status; stale code/version cells there must not initiate a paste.

## Published producer versions

| Slot | Version | Route |
|---|---:|---|
| 071 | v4.7 | Homework feedback → 079 → Hub → Resend |
| 072 | v4.9.4 | Weekly package builder |
| 073 | v4.11 | Video feedback → 079 → Hub → Resend |
| 074 | v3.8 | Weekly handoff → 079 → Hub → Resend |
| 076 | v8.17 | Daily submission → 079 → Hub → Resend |
| 078A | v1.9 | Welcome → 079 → Hub → Resend |
| 079 | v2.5 | Dispatcher; `ingressSecret` is UI-only |
| 117 | v2.4 | Zoom recording approval → 079 → Hub → Resend |
| 118 | v2.3 | Scheduled weekly build arm |
| 119 | v1.10 | Scheduled weekly send arm |

Current producers include strict input parsing, so Airtable's text value `"false"` is correctly interpreted as false. See [`EMAIL-PRODUCER-BOOLEAN-INPUT-PARSING.md`](../deploy-checklists/EMAIL-PRODUCER-BOOLEAN-INPUT-PARSING.md).

## Operational evidence

- Email Handoff Queue records establish producer acceptance and handoff state.
- Communications Hub messages, deliveries, attempts, and audit events establish downstream delivery state.
- Input variables, triggers, and the 079 secret are Automation-editor settings. They must be visually verified, saved, and re-opened; they are not repository configuration.
- Do not paste a producer merely because an old checklist or table mirror reports an older version.

## Safety rules

- Use a deliberate disposable proof before a broad email-mode change.
- During a simulation, the only approved recipient is `schmidt@fairfieldbasketballclub.com`.
- For normal family operation, producers must use cleaned enrollment contact fields. Do not use a simulation allowlist in place of contact validation.
- Preserve queue and Hub audit evidence during incidents; do not bulk-delete delivery records.

## Related documents

| Document | Role |
|---|---|
| [`TIER-1-LAUNCH-OPS-RUNBOOK-20260911.md`](../deploy-checklists/TIER-1-LAUNCH-OPS-RUNBOOK-20260911.md) | Current operator instructions |
| [`EMAIL-PRODUCER-BOOLEAN-INPUT-PARSING.md`](../deploy-checklists/EMAIL-PRODUCER-BOOLEAN-INPUT-PARSING.md) | Current input-parsing contract |
| `docs/testing/evidence/parent-email-live-cutover/` | Historical proof artifacts; not current promotion instructions |
| Dated parent-email cutover packets | Historical context; do not use their version tables or paste queues |
