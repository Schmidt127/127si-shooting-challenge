# 2027 Season Production Configuration

**Status:** Preseason cutover in progress (2026-09-15)  
**Activation date (docs):** 2026-09-15  
**Registration opening date:** **2027-03-01**  
**Registration status target:** **CLOSED** until that date  

## Rollback / pre-cutover reference (do not alter)

| System | Repository | SHA |
|--------|------------|-----|
| Shooting Challenge | `Schmidt127/127-si-shooting-challenge` | `c0a7eba0d62e9582a259eb6ec180745e7d58251c` |
| Communications Hub | `Schmidt127/127-communication-hub` | `4485af3b6d89c80f2166eab09df38cc1c788b87f` |

Freeze date: `2026-09-15` · Prior verdict: `ECOSYSTEM PRODUCTION CLEAN — CURRENT ARCHITECTURE CLOSED`

## Pre-cutover safety (2026-09-15)

| Check | Result |
|-------|--------|
| SC Email Handoff Queue Ready/Draft/Sending | **0** |
| Hub Deliveries Queued/Sending/Needs Review | **0** |
| Unintended emails releasable by cutover | **0** |

## Production email architecture (unchanged)

SC producers → Email Handoff Queue → Automation **079** → Hub `/api/events/ingest` → Messages/Deliveries → **Resend** → `/api/webhooks/resend` → SC Sent? writeback  

Make/Gmail email: **OFF / retired** · Hub scheduler: **off** · No new cron.

## Live vs Test controls

| Control | Pre-cutover | Desired 2027 production | Change |
|---------|-------------|-------------------------|--------|
| Hub Airtable `Send Block Reason` | `LIVE_BLOCKED` for Live | Live allowed; Test still requires allowlist | **Applied 2026-09-15** (formula) |
| Hub Airtable `Ready for Send?` (was Ready for Test Send?) | Test+allowlist only | Test+allowlist **or** Live (no allowlist) | **Applied 2026-09-15** (formula + rename) |
| Hub ingest `testMode` | Must be `true` | `true`=Test, `false`=Live when enabled | Hub PR code |
| `HUB_LIVE_DELIVERY_ENABLED` | unset | `true` on Vercel Production | **Mike sets after Hub deploy** |
| SC producer automation input `testMode` | default **true** | default **false** (Live) | Repo default change + **Mike paste / input clear** |
| Test Allowlist | Active (Schmidt household) | Remains for intentional Test sends | Keep |
| Make email scheduling | OFF | OFF | No change |

## Registration

| Item | Value |
|------|--------|
| Public registration URL | `https://forms.fairfieldbasketballclub.com/shoot-playerregistration` (Fillout) |
| Availability control | **Fillout form open/closed** (Mike UI) — not automatic in this repo |
| Opening date | **2027-03-01** |
| Program Instance | `Shooting Challenge \| 2026-2027` (`rec5mEM0YPqPqq0hZ`) Status **Registering** (required for `/shoot` season scope) |
| PI registration date field | **2027-03-01** (already set) |
| Challenge window | 2027-05-01 → 2027-06-30 |
| Early Bird week | 2027-04-25 → 2027-05-02 |
| Weeks 1–9 | Present on Weeks table |

**Do not** set Program Instance Status away from Registering solely to “close” registration — that breaks `/shoot` public season resolution. Keep **Fillout registration CLOSED** until 2027-03-01.

Prefer Mike manual Fillout open on March 1 over inventing a new scheduler.

## Season readiness snapshot

| Area | Status |
|------|--------|
| Weeks Early Bird + 1–9 + Post-Challenge | Present |
| Config school year 2026-2027 | Present (`rechc1f9f4kVM1tHP`) |
| Program Instance dates | Set (reg 2027-03-01, challenge May–Jun 2027) |
| XP / levels / achievements / Perfect Week rules | Use existing approved Config — no opportunistic rule changes |
| Hub 13 tables / 0 automations | Confirmed |
| SC 50 automations deployed | Confirmed at pre-cutover baseline |

## Mike actions before Live email is real

1. Merge + deploy Hub Live cutover PR; set Vercel `HUB_LIVE_DELIVERY_ENABLED=true`.  
2. Paste updated SC email producers (071/073/074/076/078A/117) **or** set each automation `testMode` input to **false**.  
3. Confirm Fillout **Player Registration** remains **CLOSED** until 2027-03-01.  
4. Controlled allowlist/Live acceptance send to Mike addresses only.  
5. On 2027-03-01: open Fillout registration when ready.

## Intentional Test after Live

Send with `testMode: true` (queue checkbox) + active Test Allowlist. Default production path is Live (`testMode: false`).
