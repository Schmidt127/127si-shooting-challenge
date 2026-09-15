# 2027 Season Production Configuration

**Status:** **PRODUCTION LIVE** (email plane) — registration CLOSED until **2027-03-01**  
**Activation completed:** 2026-09-15  
**Registration opening date:** **2027-03-01**  
**Registration status:** **CLOSED** (Fillout; do not auto-open)

## Final verdict

`2027 PRODUCTION LIVE — REGISTRATION CLOSED UNTIL MARCH 1`

## Deployed production SHAs (2026-09-15 cutover)

| System | Repository | SHA | Notes |
|--------|------------|-----|-------|
| Shooting Challenge | `Schmidt127/127si-shooting-challenge` | `a9ea96ae6409cb4c36e56aa026697866c2ba579f` | PR #550 + PR #551 merged |
| Communications Hub | `Schmidt127/127-communication-hub` | `20da3d610fa3075ee41cf4c597d3f7d59e0926c8` | PR #54 merged |
| Hub Vercel Production | `communications` / `communications-two-blue.vercel.app` | deploy `dpl_BhjPM3p892emDCvv5yiifKUffoyS` | READY; env `HUB_LIVE_DELIVERY_ENABLED=true` |

## Rollback / pre-cutover reference (do not alter)

| System | Repository | SHA |
|--------|------------|-----|
| Shooting Challenge | `Schmidt127/127si-shooting-challenge` | `c0a7eba0d62e9582a259eb6ec180745e7d58251c` |
| Communications Hub | `Schmidt127/127-communication-hub` | `4485af3b6d89c80f2166eab09df38cc1c788b87f` |

Freeze date: `2026-09-15` · Prior verdict: `ECOSYSTEM PRODUCTION CLEAN — CURRENT ARCHITECTURE CLOSED`

## Pre-activation + post-activation queue safety (2026-09-15)

| Check | Result |
|-------|--------|
| SC Email Handoff Queue Ready/Draft/Sending | **0** |
| Hub Deliveries Queued/Sending/Needs Review | **0** |
| Unintended emails releasable by cutover | **0** |

## Production email architecture (unchanged)

SC producers → Email Handoff Queue → Automation **079** → Hub `/api/events/ingest` → Messages/Deliveries → **Resend** → `/api/webhooks/resend` → SC Sent? writeback  

Make/Gmail email: **OFF / retired** · Hub scheduler: **off** · No new cron.

## Live vs Test controls (final)

| Control | Production value |
|---------|------------------|
| Hub Airtable Live path | Live allowed; Test still requires allowlist |
| `HUB_LIVE_DELIVERY_ENABLED` | **true** (Vercel Production) |
| Hub health | `ready` · provider `RESEND` · scheduler `off` |
| SC producer `testMode` inputs | **false** on 071 / 073 / 074 / 076 / 078A / 117 |
| Weekly 118 | `dryRun=false`, `sendMode=live`, `includeSchmidt=false` |
| Weekly 119 | `dryRun=false`, `includeSchmidt=false` |
| SC `ATHLETE_AUTH_TEST_MODE` | **false** |
| Test Allowlist | **Retained** (3 active Email rows) for intentional Test events |
| Make email scheduling | **OFF** |

GitHub producer script defaults now also default `testMode` to **false** (Live). Production Airtable inputs already force Live; script paste is optional alignment only (requires Airtable UI Update to publish draft pastes).

## Registration

| Item | Value |
|------|--------|
| Public registration URL | `https://forms.fairfieldbasketballclub.com/shoot-playerregistration` (Fillout) |
| Availability control | **Fillout form open/closed** (Mike UI) — not automatic in this repo |
| Opening date | **2027-03-01** |
| Program Instance | `Shooting Challenge \| 2026-2027` (`rec5mEM0YPqPqq0hZ`) Status **Registering** |
| PI registration date field | **2027-03-01** |
| Challenge window | 2027-05-01 → 2027-06-30 |

**Do not** set Program Instance Status away from Registering solely to “close” registration — that breaks `/shoot` public season resolution. Keep **Fillout registration CLOSED** until 2027-03-01.

## Controlled Live smoke (2026-09-15)

**Not executed:** Production Enrollments table currently has **0** records, so no Mike-controlled enrollment exists for the SC → 079 → Hub → Resend path.

When Mike restores an Athlete1 / operator enrollment:

1. Confirm queues still **0** unintended Ready rows.
2. Trigger one producer event with `testMode=false` (or rely on Live input default).
3. Verify queue Accepted → Hub Message/Delivery → Resend → webhook → SC writeback + idempotent replay.

## Intentional Test after Live

Send with `testMode: true` (queue checkbox / producer input) + active Test Allowlist. Default production path is Live (`testMode: false`).
