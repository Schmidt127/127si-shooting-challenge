# Legacy Shooting Challenge — capability inventory for the new platform

**Why this exists.** The new challenge platform is being built off-Airtable. Before it ships, every module, rule, operator capability, and backlog idea in the legacy app (`127-si-shooting-challenge`, Airtable base `appn84sqPw03zEbTT` + Next.js `/shoot` + Communications Hub) needs to be checked for parity or a deliberate "not carrying forward" decision. This folder is that checklist.

**How it was produced.** Read-only research against this repository on 2026-10-07 (automation scripts, `lib/` contracts, the 2026-09-05 PROD schema snapshot, PROD config exports, docs, and the web app source). No live Airtable, Make, Hub, or Vercel state was consulted. Where the repo says something was "built but not installed" or "designed only," it is recorded that way.

**How to use it.** Walk each file against the new platform's spec. For every row, mark one of: *parity*, *intentionally changed (how)*, *intentionally dropped (why)*, or *gap*. Gaps feed `docs/127-SI-MASTER-FUTURE-WORK-LIST.md`.

## Files

| File | Covers |
|---|---|
| [00-xp-sources.md](./00-xp-sources.md) | Every XP bucket, rule, amount, source key, eligibility, cap, and withdrawal rule; designed-but-inactive XP ideas |
| [01-intake-submissions-assets.md](./01-intake-submissions-assets.md) | Athletes → Enrollments identity model, grade bands, Fillout submission intake, stat modes, `Count This Submission?`, duplicate review, week/enrollment assignment, Submission Assets upload ladder (Make → Lambda → private S3), hash-based file dedupe, Weeks / Program Instance / Config knobs, Testing Scenarios + Season Simulation |
| [02-homework-video-review.md](./02-homework-video-review.md) | Homework library + Program Homework Assignments scheduling, three homework intake paths (file, HW17 reflection quiz, Curriculum Hub), completion lifecycle and timing, coach grading queues, Video Feedback lifecycle, parent feedback emails, S3 rename, public homework/tutorial pages |
| [03-progression-achievements-weekly.md](./03-progression-achievements-weekly.md) | Weekly Athlete Summary fields (goal %, momentum, previous-week chain), 12-level ladder, level gate rules and signature-driven recalculation, Achievements catalog incl. never-automated trigger types, unlock lifecycle, streak model, Perfect Week rules, Shot Milestones / Goal Met / Conquered Goal, Awards catalog + fulfilment, leaderboard ranking and privacy |
| [04-communications-zoom-integrations.md](./04-communications-zoom-integrations.md) | Email Handoff Queue → 079 → Communications Hub → Resend architecture, all six email types with payloads/subjects/gating, copy decisions, Zoom meetings and manual attendance capture, recording-quiz makeup policy, integrations inventory (live vs retired) |
| [05-web-app-brand.md](./05-web-app-brand.md) | Every public and API route, Family Dashboard magic-link auth, Curriculum Hub SSO, data layer and env vars, public-data privacy contract, SEO, brand/design system, QA suites, deployment, media kits |
| [06-operations-ideas-backlog.md](./06-operations-ideas-backlog.md) | All 35 tables with roles, season lifecycle runbooks, audits and safe-backfills, Airtable Interfaces, governance, the complete categorized ideas backlog (planned / deferred / rejected), lessons learned |
| [07-new-platform-gap-comparison.md](./07-new-platform-gap-comparison.md) | Plain-language comparison of the old app (00–06) against the live new Challenge Platform (`challenge.fairfieldbasketballclub.com`, 2026-10-07): every XP bucket and module labelled ADD / CHANGE / CHECK / SAME / NEW, with a short fix-first list and a numbers appendix |

## Cross-domain "must not miss" list

Items that appear in more than one file or that are easy to lose when moving off Airtable.

### Identity and scope
- Three-layer identity: **Athlete** (person) → **Enrollment** (athlete × Program Instance × School Year) → every progress record hangs off Enrollment. Program Instance is the hard isolation boundary for Weeks, goals, homework assignments, gate rules, and leaderboards. Siblings share a parent email but get separate athletes/enrollments; a parent-email change intentionally creates a new athlete (no auto-merge).
- One enrollment per athlete per season is enforced; `Active?` and `Progress Processing Enabled?` are universal guards; a permanent allow-listed test enrollment (Schmidt) coexists with production data and is excluded from comms and leaderboards.
- Grade bands are range-matched from grade (Pre K = −1) and re-assigned on grade change; each band carries a season shot target, a default homework tier, its own shot-milestone ladder, and its own weekly-threshold rule amounts.

### Scoring integrity
- A single formula gate (`Count This Submission?`) decides whether a submission scores; duplicates are only flagged by automation and resolved by a human (Count It / Needs Review / Exclude It).
- Every derived record (XP Event, Weekly Athlete Summary, Homework Completion, Video Feedback, unlock, streak occurrence) has a deterministic key and is append-only with soft `Active?` withdrawal. The new platform should turn these conventions into database constraints: unique keys, transactions, no formula-lag races.
- Reconciliation is signature-driven (current vs last-reconciled hash) rather than event-triggered; levels recalc on a 15-minute cadence; streaks refresh nightly so they visibly break without new input.
- All dates are America/Denver calendar keys; date-only values must never be timezone-shifted (documented regressions in 066 v4.0 and 053).

### Program calendar and config
- Season = Program Instance with Registration Open/Close separate from Start/End; 9 challenge Weeks, Sunday–Saturday, partial terminal week allowed, `Counts Toward Challenge?` per week.
- Config knobs that must exist somewhere: active school year, max videos per submission, detailed stat tracking on/off and required, HW / video review enabled, challenge week count, Perfect Week video minimum, Zoom recording policy (enabled, deadline days and basis, XP %, coach approval, full gate credit, counts for Perfect Week), file-naming pattern. Per-category on/off for a program instance (FUT-038) was planned, never built.

### Content and review
- Homework is scheduled per Program Instance + Week + Slot through Program Homework Assignments; completions are identified by Enrollment + assignment, allow many files → one completion, and three intake paths (file upload, auto-scored 18-question reflection quiz, Curriculum Hub with zero files). Late = full credit but not Perfect Week; early counts for the assigned week.
- Video review: one Video Feedback row per uploaded video (up to 3 per submission), coach feedback as a quotation in the parent email, `Do Not Award XP?` override, coach-driven S3 rename, files always served through a tokenized Lambda viewer (never raw S3 or Airtable CDN URLs).
- Coach grading queues are Interfaces driven by composite Active/Completed rules because single-select "status" fields went stale.

### Gamification beyond XP
- 12 levels with cover image, color, and unlock message; gates at ranks 7–12 across five dimensions (submissions, homework, videos, Zoom meetings, longest streak) with parent-facing "Missing: …" strings and On Track / Paused status.
- Achievements catalog defines trigger types never automated (Goal %, Comeback, Homework Hero, Days Logged, Improvement, Engagement, Manual, Secret, Rarity, Badge icon) — treat as first-class rule types in the new engine.
- Awards catalog (Weekly / Overall scope, section groups, Gift Card / Physical / Recognition / Badge, manual fulfilment) with recipient status pipeline and `Public On Web` publication gate; Conquered Goal keeps activity truth (`Goal Met Date`) separate from fulfilment date.
- Leaderboard ranks Level → Lifetime XP → Total Shots → name, with strict eligibility, a 9-field privacy allowlist, grade-band filter, and a kiosk display; athlete profiles are opt-in by slug.

### Communications
- One outbox plane: producers build JSON → Email Handoff Queue (deterministic handoff keys, Draft → Ready → Sending → Accepted/Failed → Needs Review after 3 attempts) → Hub owns templates/branding/Resend → delivery status written back from webhooks. Six live email types: welcome, daily submission (parent + athlete), weekly summary (scheduled Sunday build/send with empty-week "short" policy), homework feedback, video feedback, Zoom recording approval.
- Only cleaned parent email is ever used; test-mode recipient redirect and strict boolean parsing exist because of a real incident.
- Planned, unbuilt: level-up / achievement / award notifications, React Email welcome redesign, family profile email, SMS.

### Operations
- No admin console existed: operators used grid views as triggers, two grading Interfaces, ~50 read-only audits and ~45 safe backfills (dry-run default, typed confirmation phrases), CLIs for season rollover, and 261 deploy checklists. Season Launch Control and the Reliability Command Center were built but never installed.
- Airtable's 50-automation cap and production-only operation (DEV base retired) shaped many compromises; the new platform needs a real staging environment and a season-simulation harness (SC-SEASON-SIM-001).
- Explicitly rejected ideas to keep rejected: public S3 bucket, Tremendous API, dual-track progression (until post-2026-27 review), one base per season, mid-season config edits.

### Biggest planned-but-unbuilt ideas
- Shared multi-challenge platform (SC-143 / FUT-050): identity, enrollment, XP + buckets, levels, achievements, rewards, comms, reporting, admin shared across Shooting and Dribble challenges.
- Learning Activities / interactive Curriculum Hub replacing fixed HW1/HW2 slots (SC-018/019/020, FUT-029, FUT-055).
- Family/household private profile with visibility matrix and sibling handling (FUT-057, SC-062).
- S3 migration orchestrator and deterministic media naming (FUT-040, FUT-009, FUT-010).
- Config-generated Player and Game Manuals with a rules acknowledgement before first submission (FUT-054).
- One-click media-kit generation from award data (V2-028).
