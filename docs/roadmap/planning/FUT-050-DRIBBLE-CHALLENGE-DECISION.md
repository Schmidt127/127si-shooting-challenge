# FUT-050 — Dribble Challenge product decision

**Status:** Future (decision record only — do not build)  
**Mike approval required before implementation:** **Yes** (architecture choice)  
**Created:** 2026-09-14

## Purpose

Decide whether Dribble Challenge is:

1. a **module inside** the Shooting Challenge base/app, or  
2. a **separate base/application**.

Constraint: track **dribbling minutes**, not shooting XP.

## Option A — Module inside Shooting Challenge

**Reuse:** enrollment/family auth patterns, household dashboard shell, email/Hub/Resend, homework/Zoom patterns, reporting chrome, brand.

**Keep independent:** dribble metrics table(s), rules, leaderboards, progression (minutes-based), possibly separate WAS-like summaries.

**Pros:** One login surface for families; shared ops; faster MVP.  
**Cons:** Risk of XP/minutes confusion; schema pollution; harder to price/market separately; coupled release risk.

## Option B — Own base / application

**Reuse (patterns, not shared tables):** enrollment UX, email Hub allowlist model, auth approach, brand components (copy into `127-si-dribble` or similar).

**Independent:** full data model, minutes ledger, leaderboards, reporting, progression.

**Pros:** Clean domain boundary; separate launch/pricing; lower blast radius.  
**Cons:** Duplicate ops; two dashboards unless a landing hub stitches them; more build cost.

## Recommendation

**Prefer Option B (own base/app) for the product of record**, with a thin shared **family portal shell** later if needed.

**Why:** Minutes ≠ XP is a core domain split. Keeping both in one XP-centric base invites accidental coupling (thresholds, Perfect Week metaphors, leaderboard math). Shooting Challenge has just proven a long automation/XP surface via Perfect sim — adding a second currency increases regression cost.

**Near-term:** Keep Dribble as landing “Youth Programs” marketing only until ADR locked (FUT-033–037 live in landing repo).

## Definition of done (this planning item)

- Mike accepts A or B (or hybrid portal + separate base).  
- No schema/app build until a separate implementation ID is opened.

## Future platform migration constraint (not this item)

Independent of near-term packaging (A vs B), **future platform migration** planning must support **both** Shooting Challenge and Dribble Challenge on shared challenge infrastructure (athlete identity, enrollment, challenge/session model, XP events/buckets, levels, achievements, progression, rewards, communications, reporting, administration), with primary metrics **shots** vs **dribble minutes**. See [`../../production-architecture/FROZEN_BASELINE_AND_FUTURE_WORK.md`](../../production-architecture/FROZEN_BASELINE_AND_FUTURE_WORK.md). Do not implement from FUT-050 or FUT-058.
