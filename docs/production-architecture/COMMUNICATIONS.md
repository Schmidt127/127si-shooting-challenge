# Communications — SC ↔ Hub boundary

**Status:** Authoritative (FUT-058 · 2026-09-15)  
**Email plane:** [`../integrations/email-send-plane.md`](../integrations/email-send-plane.md)  
**Hub repo:** `Schmidt127/communications` (local: `127si-communication-hub`)  
**Hub base:** `appYG1t5DBRimHBCT`  
**Provider:** **Resend** (Make/Gmail not the sender)

## System of record by responsibility

| Responsibility | Owner |
|----------------|-------|
| Source athlete/parent activity | SC Airtable |
| Queue row before send | SC **Email Handoff Queue** |
| Only SC script that POSTs to Hub | Automation **079** |
| Message / Delivery records | Communications Hub Airtable |
| HTML templates (React Email) | Communications Hub repo `emails/` |
| Template catalog metadata | Hub **Templates** table |
| Test allowlist / suppressions | Hub **Test Allowlist** / **Suppressions** |
| Delivery success writeback to SC Sent? | Hub after Resend (VF / HC / WAS as configured) |
| Magic-link auth emails | SC `web/` Resend path (not Hub queue) |

## Active SC → Hub event types

| Producer | Event type | Template key | Dedupe / handoff key shape |
|----------|------------|--------------|----------------------------|
| **078A** | `WELCOME` | `WELCOME` | `WELCOME\|SHOOTING_CHALLENGE\|…` |
| **076** | `DAILY_SUBMISSION` | `DAILY_SUBMISSION` | `DAILY_SUBMISSION\|SUBMISSIONS\|{Submission}` |
| **071** | `HOMEWORK_FEEDBACK` | `HOMEWORK_FEEDBACK` | `HOMEWORK_FEEDBACK\|HOMEWORK_COMPLETIONS\|{HC}` |
| **073** | `VIDEO_FEEDBACK` | `VIDEO_FEEDBACK` | `VIDEO_FEEDBACK\|VIDEO_FEEDBACK\|{VF}` |
| **074** | `WEEKLY_ATHLETE_SUMMARY` | `WEEKLY_ATHLETE_SUMMARY` | `WEEKLY_ATHLETE_SUMMARY\|WEEKLY_ATHLETE_SUMMARY\|{WAS}` |
| **117** | `ZOOM_RECORDING_APPROVAL` | `ZOOM_RECORDING_APPROVED` | `ZOOM_RECORDING_APPROVAL\|ZOOM_ATTENDANCE\|{ZA}` |

Shared dispatcher: **079** → `POST /api/events/ingest` with `SHOOTING_CHALLENGE_INGRESS_SECRET`.

Weekly schedule arms (do not send alone): **118** (build) · **119** (send) · package builder **072**.

## Hub processing

1. Validate ingress + idempotency `SHOOTING_CHALLENGE|{eventType}|{handoffKey}`
2. Create/reuse Message + Delivery
3. Gate: Test mode · allowlist · suppression · opt-out · approval formulas
4. Send via Resend
5. Webhook `/api/webhooks/resend` updates provider status
6. Writeback to SC source Sent?/Sent On when configured
7. Retry: max **2** attempts → Needs Review (`RETRY_POLICY` in Hub docs)

## Recipient resolution

- Parent/guardian emails originate from SC Enrollment / Athlete contact fields in the producer payload.
- Hub may sync Communication Identities; **program bases remain authoritative** for people (Hub DEC-008).
- Disposable proof recipient: `schmidt@fairfieldbasketballclub.com` only until Live cutover.

## Dual implementation warning

| Do not confuse | Why |
|----------------|-----|
| Make “Ready for Make?” fields on Hub Messages | Legacy Make orchestration — Resend path is current |
| SC filenames saying “Webhook” / “Make” | Historical naming; producers create Hub queue rows |
| Hub Completion Master “MVP not complete” | May lag live Resend path — verify against SC email-send-plane + Hub evidence |

## Live cutover

Broad participant email remains gated by Test mode / allowlist until Mike flips Live inputs per:

- [`../deploy-checklists/parent-email-and-auth-live-cutover-2026-09-03.md`](../deploy-checklists/parent-email-and-auth-live-cutover-2026-09-03.md)
- [`../deploy-checklists/TIER-1-LAUNCH-OPS-RUNBOOK-20260911.md`](../deploy-checklists/TIER-1-LAUNCH-OPS-RUNBOOK-20260911.md)
