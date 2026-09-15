# Changelog / project status (architecture pack)

**Status:** Snapshot for cold-start readers (FUT-058 · 2026-09-15)  
**Living detail:** [`../CURRENT-TRUTH.md`](../CURRENT-TRUTH.md) · [`../SHOOTING_CHALLENGE_COMPLETION_MASTER.md`](../SHOOTING_CHALLENGE_COMPLETION_MASTER.md) · root [`CHANGELOG.md`](../../CHANGELOG.md)

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

## Known limitations

- Broad parent email still **test-mode / allowlist** until Live cutover  
- Three-athlete season sim (**SC-SEASON-SIM-001**) ready but **not executed**  
- Tremendous production awards API pending  
- Stripe 100% coupon writeback plan-only until activation  
- Schema field count drift vs older snapshots; `airtable/schema/current/` stale  
- Hub Completion Master / some Hub docs may lag Resend-live reality  

**Resolved this audit:** Automation **009** Mike-confirmed deployed (**v1.3 / SC-160**); Production automations **50/50**.  

## Deferred improvements

- FUT-029 grade-band homework platform  
- FUT-048 CloudFront custom domain (cosmetic)  
- FUT-049+ planning pack (PHA band removal, Dribble decision, unused-field program, etc.)  
- SMS / Twilio  

## Intentionally retained legacy

- Repo copies of retired automation scripts (006, 075, 077, 111, …) for audit history  
- Make blueprints for upload / Tremendous (email Make retired)  
- Historical evidence under `docs/prod-completion/`, `docs/testing/evidence/`, `docs/archive/`  
- Softr naming on some publish fields pending rename programs  

## Technical debt (non-blocking unless noted)

| Item | Class |
|------|-------|
| Filenames / Airtable names still saying Make/Webhook | COSMETIC |
| Nested `hub/` duplicate in communications repo | OPTIONAL cleanup |
| Root SYSTEM_OVERVIEW historically claimed Make email | Fixed in this pack |
| `.worktrees/` local checkouts | Ignore — do not commit |
