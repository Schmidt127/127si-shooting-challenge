# Changelog / project status (architecture pack)

**Status:** Snapshot for cold-start readers · **FUT-058 COMPLETE — CLOSED** (2026-09-15)  
**Frozen baselines + work categories:** [`FROZEN_BASELINE_AND_FUTURE_WORK.md`](./FROZEN_BASELINE_AND_FUTURE_WORK.md)  
**Living detail:** [`../CURRENT-TRUTH.md`](../CURRENT-TRUTH.md) · [`../SHOOTING_CHALLENGE_COMPLETION_MASTER.md`](../SHOOTING_CHALLENGE_COMPLETION_MASTER.md) · root [`CHANGELOG.md`](../../CHANGELOG.md)

## Required current production work

`NONE` — ecosystem verdict `ECOSYSTEM PRODUCTION CLEAN — CURRENT ARCHITECTURE CLOSED`.

## Completed / production-ready systems (high level)

- Enrollment intake + grade bands (001–003)  
- Submission XP, homework XP, video XP, Zoom XP (incl. recording credit on 101)  
- Levels + gates (041/042)  
- Streaks, Perfect Week, shot milestones + Goal Met Date (066)  
- Weekly Athlete Summary chain  
- Parent email producers → **079** → Communications Hub → **Resend**  
- Public `/shoot` site: leaderboard, catalogs, game manual, SEO, family dashboard auth  
- Curriculum Hub homework lifecycle (verified)  
- Perfect Mike Schmidt season simulation **PASSED** (2026-09-14)  
- FUT-002 field cleanup Batches 1–2  

## Operational / policy (not architecture defects)

- Broad parent email still **test-mode / allowlist** until Mike authorizes Live cutover  
- Make email scheduling remains **OFF** (sender = Hub → Resend)

## Optional cleanup (NON-BLOCKING — does not reopen FUT-058)

- COM-CC-007 Hub operational views  
- Nested `hub/` duplicate in Communications Hub repo  
- Filenames / Airtable names still saying Make/Webhook (cosmetic)  
- Older docs using Hub slug `Schmidt127/communications` → prefer `127-communication-hub`  
- Stale tip-SHA lines after docs-only merges  
- Schema field count drift vs older snapshots; `airtable/schema/current/` stale  
- `.worktrees/` local checkouts — ignore; do not commit  

**Resolved in FUT-058:** Automation **009** deployed (**v1.3 / SC-160**); SC automations **50/50**; Hub Completion Master refreshed (Hub PR #53 @ `4485af3`); ecosystem baseline frozen.

## Future / deferred product work

- Three-athlete season sim (**SC-SEASON-SIM-001**) ready but **not executed**  
- Tremendous production awards API / FUT-004 / FUT-052  
- Stripe 100% coupon writeback (FUT-053) until Mike activates  
- FUT-029 grade-band homework platform (deferred)  
- FUT-048 CloudFront custom domain (cosmetic deferred)  
- FUT-049+ planning pack (PHA band removal, Dribble decision record, etc.)  
- SMS / Twilio  
- Team Shot Tracker / Junior Ref communications  

## Future data cleanup

- **FUT-051** unused-field program — review before delete; **no deletes from FUT-058**

## Future platform migration

**Not started.** Separate from FUT-058. See [`FROZEN_BASELINE_AND_FUTURE_WORK.md`](./FROZEN_BASELINE_AND_FUTURE_WORK.md) § F (18 planning gates) and shared Shooting + Dribble challenge requirement.

## Intentionally retained legacy

- Repo copies of retired automation scripts (006, 075, 077, 111, …) for audit history  
- Make blueprints for upload / Tremendous (email Make retired)  
- Historical evidence under `docs/prod-completion/`, `docs/testing/evidence/`, `docs/archive/`  
- Softr naming on some publish fields pending rename programs  
- Hub docs with Make→Gmail diagrams labeled **LEGACY**
