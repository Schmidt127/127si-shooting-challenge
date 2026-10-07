# 07 — Old Shooting Challenge vs. new Challenge Platform: what to add, change, or check

**Written:** 2026-10-07
**Who it is for:** Mike, deciding what the new Challenge Platform still needs before the Spring 2027 Shooting Challenge.
**Companion files:** `00`–`06` in this folder describe the old app in detail. This file only talks about the *differences*.

## How to read this

Every item has one of five labels:

| Label | Meaning |
|---|---|
| **ADD** | The old app did this. I found no sign of it in the new platform. |
| **CHANGE** | The new platform has it, but the numbers or rules are different from the old app. You should decide on purpose which one you want. |
| **CHECK** | The new platform seems to have the building blocks, but it is not switched on or filled in for the 2027 Shooting Challenge, or I could not confirm it from the outside. |
| **SAME** | Matches the old app. Nothing to do. |
| **NEW** | The new platform has it and the old app did not. No action; listed so you know what you gained. |

## Where I looked, and one honest limit

- **Old app:** the Airtable base, its 50 automation scripts, the `/shoot` website, and the Make/Lambda/Resend pieces (fully written up in files `00`–`06`).
- **New platform:** the live Supabase database behind `challenge.fairfieldbasketballclub.com` (all 58 tables, the saved rule settings for every challenge, what values are actually allowed in each column, and what has really been written so far), the sibling Communication Platform database (email templates), the Shared Data database (schools), and the public web pages (Overview, Levels, XP Buckets, Leaderboard, FAQs, Parent FAQ, Registration).
- **The limit:** I could not open the new platform's source code (the GitHub repository is not visible to this agent) and I could not sign in to the Parent Portal or admin screens. So when I say "I found no sign of X," it means X is not in the database, the rule settings, or the public pages. An admin screen could exist that I cannot see. Those items are labelled **CHECK**, not **ADD**.

---

## Part A — The short list (fix these first)

These are the items most likely to bite you on day one of the 2027 Shooting Challenge.

1. **The 2027 Shooting Challenge has only four placeholder levels.** The public Levels page shows Starter 0 / Builder 40 / Closer 120 / Finisher 250. The old app had twelve named levels from Beginner (0) to G.O.A.T. (2,200), 200 XP apart, with behaviour gates on the top six. The Dribbling challenge in the new platform already has a proper twelve-level ladder (0 to 2,400) with G.O.A.T. gates, so the engine can do it; the shooting rules were just never filled in. **ADD.**
2. **The grade bands disagree with themselves inside the shooting rules.** Eligibility lists `k-2`, `3-5`, `6-8`, `9-12`. The season goal table lists `prek-2`, `3-4`, `5-6`, `7-8`, `9-12`. A 5th grader is in "3-5" for eligibility but "5-6" for the goal; nothing lines up except 9-12. The old app used K-2 / 3-4 / 5-6 / 7-8 / 9-12 everywhere. **CHANGE** (pick one set and use it in both places).
3. **No meeting (Zoom) XP exists for the 2027 Shooting Challenge.** The public XP Buckets page lists zero meeting buckets. The rules say meetings are "not required" and no meetings are scheduled. In the old app, Zoom was the single biggest bucket (60 per meeting, plus 30 and 40 one-time bonuses, plus half-credit recording makeups). **CHECK / ADD.**
4. **The weekly goal is one flat number (350 shots) for every grade.** The old app scaled the weekly goal by grade band (season goal ÷ 9: roughly 222 for K-2 up to 1,333 for 9-12) and paid three tiers at 100 / 125 / 150 %. Under the new rule, a high-schooler earns the weekly bonus at about a quarter of their real weekly pace, and a kindergartener has to shoot 60 % above theirs. Perfect Week uses the same flat 350. **CHANGE.**
5. **Only three emails exist.** Daily submission confirmation, coach video feedback, homework feedback. The old app also sent a welcome email, a Sunday weekly summary (with awards and momentum), and a Zoom-recording-approval email. The Parent FAQ on the new site promises welcome emails and weekly summaries, but no template exists for either. **ADD.**
6. **The achievements list is a placeholder.** It contains "Achievement – 40 Challenge XP" (+5) and "100 Challenge XP". The old app had a 15-row catalog with rarity, badge icon, and a public Achievements page. **ADD / CHANGE** (decide what an achievement is in the new world).
7. **Most XP amounts are different, some by a lot.** Shooting 10 vs 20. Video 5 vs 25. Homework 39 vs 35. Streaks total 1,115 vs 455 across the nine tiers. None of this is wrong, but it looks like it drifted rather than being decided. **CHANGE** (see the side-by-side table in Part B).

---

## Part B — XP buckets, side by side

All "New" figures are from the saved rules for `spring-2027-shoot` (version 17) unless noted. All "Old" figures are from the live Airtable rules on 2026-07-24.

| # | Bucket | Old app | New platform today | Label | What to do |
|---|---|---|---|---|---|
| 1 | **Shooting / daily check-in** | 20 XP for every counted submission. Multiple same-day submissions each earn it. Not per shot. | 10 XP per Daily Check-In that logs shooting. | CHANGE | Decide 10 or 20. Confirm whether two check-ins on the same day both pay or whether the second is treated as a duplicate (the new app has a `duplicate_review` field on each activity, which suggests it flags them, but I could not see the rule). |
| 2 | **Weekly threshold** | Three tiers: 100 / 125 / 150 % of the athlete's *weekly goal* = 10 / 20 / 30 XP (all three stack to 60). Weekly goal = grade-band season goal ÷ 9. Amounts could differ per band. | One tier: 350 total shots in a week = 25 XP, same for every grade. | CHANGE | Switch to percent-of-goal tiers. The Dribbling challenge already uses a `weekly_goal_met` rule with partial-week prorating, so the engine supports it; only the shooting config needs changing. Decide whether to keep three stacking tiers. |
| 3 | **Streaks** | 9 tiers at 3 / 5 / 7 / 10 / 20 / 30 / 40 / 50 / 60 days = 10 / 15 / 20 / 30 / 50 / 60 / 75 / 90 / 105. Stack within one run (a 10-day streak earns 75 total). Can be earned again after a break. Day = Denver calendar day with at least one counted submission. | Same 9 day-counts. Amounts 10 / 15 / 35 / 60 / 90 / 140 / 190 / 250 / 325. Marked "not lifetime eligible." | CHANGE / CHECK | Amounts are 2–3× the old ones at the top end; a single 60-day run is worth 1,115 XP, which is half of the old G.O.A.T. ladder by itself. Decide intentionally. Confirm streaks can be re-earned after a break and that a later-voided check-in breaks the streak and takes the XP back (the ledger supports reversals, so this is probably fine). |
| 4 | **Season-goal milestones** | 8 tiers at 25 / 50 / 75 / 100 / 120 / 150 / 175 / 200 % of the grade-band season goal = 10 / 15 / 20 / 30 / 40 / 50 / 65 / 80. Band goals K-2 2,000 · 3-4 5,000 · 5-6 8,000 · 7-8 10,000 · 9-12 12,000. The 100 % tier stamps Goal Met and drives the Conquered Goal prize. | Same 8 tiers and amounts (the 120 % tier is now 125 %). Same band goals. Per-athlete goal override exists for admins. | SAME (mostly) | Confirm the 125 vs 120 change was intended. Confirm crossing 100 % automatically creates the "Conquered Challenge" award (the award exists; one grant has been made; I could not tell whether it was automatic). |
| 5 | **Perfect Week** | 100 XP. Five gates: (a) counted submission on every day of the week, each day at least 1/7 of the weekly goal; (b) uploaded within a 48-hour grace window (or a manual exception); (c) at least N coach-reviewed videos that week (N from config, 3 in practice); (d) attended that week's Zoom if there was one (recording credit counts only if config says so); (e) 100 % of that week's homework marked satisfactory and turned in by Saturday 11:59 pm Denver. Short final week allowed. | 100 XP. Rules: activity on 7 distinct days, reach weekly goal of 350, each day at least 1/7, 3 videos submitted, attend that week's meeting if one is held. | CHANGE / CHECK | Missing from new: the **homework-on-time gate** and the **48-hour upload grace window**. The video rule now counts videos *submitted* (old counted coach-*reviewed* videos). Video minimum is hard-set to 3 (old was a config setting). Confirm short first/last weeks still qualify. Weekly goal should follow item 2. |
| 6 | **Homework** | 35 XP base + coach-typed extra credit (any number). Earned when a coach marks Satisfactory + Review Complete + writes feedback. Late homework still pays in full (it only loses Perfect Week). Weekly assignments with file uploads, plus an auto-scored 18-question quiz with a family-discussion bonus. | 39 XP per lesson completed in the separate Curriculum Platform. One lesson offered for 2027 shooting ("Final Whistle", optional, 3 attempts). Dribbling has 7 lessons at 33 XP each. | CHANGE / ADD | No **coach extra-credit** bucket. Only one lesson for a nine-week shooting season (old had an assignment most weeks). Decide the 2027 homework plan: how many lessons, whether required, whether late still pays. |
| 7 | **Video / coaching** | 25 XP per coach-feedback record + extra credit; a "Do Not Award XP" switch forces 0. Up to 3 videos per submission, one feedback record per video. | 5 XP when a coach reviews a video + 5 XP when a coach verifies a follow-up video that works on earlier feedback. Up to 2 videos per day. "Improvement" bonus exists in the engine but is empty for shooting. Dribbling pays 15 / 15 and 25 for daily-practice video feedback. | CHANGE / ADD | Amount is one-fifth of the old. No extra-credit bucket. The follow-up/improvement idea is **NEW** and good. Confirm the admin can zero out XP for a specific video (the ledger has reversals; I did not see a per-video "do not award" switch). 2 vs 3 videos per day: decide. |
| 8 | **Meeting attendance (live)** | 60 XP per completed meeting attended; coach links attendees by hand. One-time 30 XP at the 2nd live meeting and 40 XP at the 3rd. | Each meeting carries its own "base attendance XP" and a minimum-minutes threshold; attendance can come from a Zoom CSV import, a recording, or manual entry. No meetings exist for 2027 shooting, meetings are marked "not required," and the XP Buckets page shows none. | CHECK / ADD | Schedule the 2027 meetings and set 60 XP each (or whatever you choose). **ADD** the 2nd/3rd-meeting bonuses if you still want them; nothing like them exists in any challenge's rules. |
| 9 | **Meeting makeup (recording)** | Half of live (30 XP) for a satisfactory recording quiz, with coach approval, a configurable deadline, and "live wins" if both exist. Recording credit never counts toward the 2nd/3rd bonuses. Counts toward level gates; Perfect Week credit is a config switch. | Each meeting has a "makeup XP" number and a makeup deadline. Makeup can be done by watching the recording **or by completing a curriculum lesson** (NEW). Outcomes include attended live / missed / excused / recording-credited. | SAME (capability) / CHECK | Set makeup XP to half of base on each meeting. Decide whether a makeup counts for Perfect Week and level gates. The "excused" outcome is NEW and useful. |
| 10 | **Manual adjustment / coach bonus** | Operator edits a signed number on the athlete, or hand-creates an XP row marked Manual. | The ledger allows an "adjustment" entry with origin "admin manual" and a required reason; it cannot be faked by the system. | CHECK | Confirm there is an admin screen to do this (I only saw the database rule that permits it). |

**Lifetime XP (across seasons):** the old app summed every season into Lifetime XP and ranked levels by it. The new platform's rules set "lifetime eligible = false" as the default for both challenges, and the website says standings use "Challenge XP earned during this Challenge only — separate from any lifetime recognition shown elsewhere." I could not find where that lifetime recognition lives (it is not in the Shared Data database, which holds schools and geography only). **CHECK** that lifetime recognition is really being built, because right now nothing accrues to it.

---

## Part C — Module by module

### 1. Levels and gates

**Old:** Twelve levels (Beginner, Rookie Shooter, Developing Shooter, Consistent Shooter, Dangerous Shooter, Hot Hand, Deadeye, Sharpshooter, Pro, All-Star, Legend, G.O.A.T.) at 0 to 2,200 in 200-XP steps, based on *lifetime* XP. Levels 7–12 also required minimums: shooting submissions (30 → 58), homework completions (6 → 18), videos (6 → 20), meetings (0 → 2), and a longest streak (0 → 30 days). XP alone could never push past a failing gate; the athlete was "Gate Blocked" and the parent saw "Missing: 2 video review(s), 1 zoom attendance(s)." Each level had cover art and an unlock message.

**New:** Levels are per-challenge ("every athlete starts at zero"). 2027 shooting: four placeholder levels, no gates. Dribbling: twelve levels (Youth Player … G.O.A.T) at 0 to 2,400, with gates only on G.O.A.T (100 % homework, 15 videos, 5 follow-up videos, 50-day streak, 2 meetings, 3 perfect weeks). The engine records level transitions with reasons and emits a "level changed" event.

| Item | Label | Note |
|---|---|---|
| Twelve-level ladder for shooting | ADD | Copy the dribbling ladder shape, rename levels to the shooting names if you want continuity. |
| Gates on levels 7–12 (not just G.O.A.T.) | ADD | The dribbling gate kinds are homework %, videos, follow-up videos, streak, meetings, perfect weeks. The old app also gated on **total shooting submissions**; I did not see that gate kind. CHECK whether it exists. |
| Lifetime vs per-challenge levels | CHANGE | A deliberate design change. Fine, but be aware returning athletes restart at zero. |
| "Missing: …" parent-facing gate explanation | CHECK | Could not see the Parent Portal. |
| Level cover art and unlock message | CHECK | Not in the rule settings I could read. |
| Level-up notification | ADD (optional) | Neither app sends one. The new engine already raises the event; only an email template is missing. |

### 2. Streaks, Perfect Week, milestones

Covered in Part B rows 3–5. Extra notes:

- **Old "Current Streak" display** (days so far, separate from XP tiers) existed on the athlete page. CHECK the Parent Portal shows a live streak count.
- **Old "Longest streak" fed gates** and only counted streaks that were still valid (not voided). The new `calculation_outcomes` table has a status that can be "invalidated," so the same idea exists. SAME.
- **Milestone withdrawal:** old app un-awarded a milestone if shots were corrected downward. New ledger has reversal entries. SAME.

### 3. Achievements and awards

**Old achievements:** 15-row catalog (9 streak tiers, Perfect Week, Shot Milestone, and four never-activated ideas: Goal Achiever, Goal Crusher, Comeback Player, Homework Hero), each with type, category, rarity (Common → Legendary), badge icon, repeatable flag, visible flag. Public `/shoot/achievements` page. Unlocks shown on the athlete profile with the triggering value ("1,500 of 2,000 shots").

**New:** Streaks, Perfect Week, and milestones are "calculations," not achievements. The achievements list has two placeholders tied to raw XP totals. There is a proper `achievement_unlocks` table with dedupe keys and revocation, so the machinery is there.

| Item | Label |
|---|---|
| Real achievement catalog (names, descriptions, rarity, badge) | ADD |
| Public achievements page | ADD (none in the site navigation) |
| Comeback / Homework Hero / Goal Achiever-type triggers | Optional — never built in the old app either |

**Old awards:** award catalog with weekly and overall scope; categories Shots / XP / Homework / Zoom / Consistency / Random drawing / Gift card; Award Recipients with status, delivery method, coach note, Amazon gift-card fulfilment via Tremendous (sandbox), a "Public On Web" switch, and award sections inside the weekly email. The Conquered Goal physical prize was tied to the 100 % milestone, and a post-season audit confirmed every goal-met athlete got one.

**New:** Three awards exist (Conquered Challenge, Grade Band Champion – by Level, Grade Band Runner-Up – by Level) with a grants table that supports revocation.

| Item | Label |
|---|---|
| Weekly awards (not just season-end) | ADD |
| Gift-card / prize fulfilment tracking (or the simple award emailer you planned as FUT-004 / FUT-052) | ADD |
| Public awards list with a per-award "show on web" switch | CHECK |
| Awards appearing in the weekly email | ADD (depends on the weekly email existing) |
| Season-end "every goal-met athlete has a Conquered award" reconciliation | CHECK |

### 4. Registration, identity, grade bands

**Old:** Fillout form → Stripe → Airtable; an automation found-or-created the athlete by parent email and blocked a second enrollment in the same season; grade bands were linked records matched by min/max grade; parent email was the identity.

**New:** Self-serve registration on the site, Stripe checkout with early-bird / regular / late pricing, waiver versions and acceptances, households with people and memberships, magic-link login for parents, required headshot, "how did you hear about us" referral tracking, platform roles (admin / athlete / coach / parent), a grade snapshot frozen at enrollment, invite codes for private test challenges.

| Item | Label | Note |
|---|---|---|
| Registration, pricing tiers, waivers, households, headshots, referrals | NEW | Clear upgrade. |
| Grade-band key mismatch (eligibility vs season goal) | CHANGE | Part A item 2. |
| Same-season duplicate enrollment guard | CHECK | Old had one; could not confirm. |
| School on the athlete | CHECK | The leaderboard page says it shows schools, and the Shared Data database has a full schools table, but I saw no school column on `people` or `challenge_enrollments`. Confirm where it is stored. |
| Changing a parent email without creating a duplicate athlete | CHECK | Was a known weakness in the old app; households should fix it. |

### 5. Daily logging (submissions)

**Old:** one form for everything: activity date, optional hour, either a simple shot total or 2PT/3PT/FT made and attempted, homework files, up to 3 videos, a video focus note. Submissions dated in the future did not count; a duplicate checker compared date + time + stats and held suspected duplicates out of scoring until a human decided; 48-hour "same day" grace for Perfect Week; file-hash detection flagged re-uploaded video files. A test harness could create submissions without the form, and a "season simulation clock" let you test a future season.

**New:** Parent Portal Daily Check-In; activities with date and time, metrics for two/three/free-throw made and attempted plus total shots; a `duplicate_review` field; "supersedes" and "void" fields (a correction replaces the old row instead of editing it); up to 2 videos per day; internal test challenges exist.

| Item | Label |
|---|---|
| Date/time/shot entry, correction-by-supersede, voiding with reason | SAME / NEW |
| Future-dated entries blocked | CHECK |
| Duplicate rule (same day + time + stats → hold for review) | CHECK |
| Re-uploaded video file detection (file hash) | CHECK |
| Max videos per day: 3 (old) vs 2 (new) | CHANGE |
| Simple-total vs detailed-stats toggle per season | CHECK |
| Backdating limit (how many days back a parent can log) | CHECK |
| Season simulation / future-date testing | CHECK (internal test challenges exist; a clock override probably does not) |

### 6. Homework / curriculum

**Old:** homework lived in the same base: weekly assignment records, up to 2 assignments per submission with up to 3 files each, parent notes, coach feedback text, Satisfactory / Review Complete gating, late detection vs due date, an auto-scored 18-question quiz, and a structured "Curriculum Hub" with attempts and token-gated submission. Homework feedback email.

**New:** homework is done in a separate Curriculum Platform; the challenge platform sends assignment requests, receives result receipts, and pays XP. Seven lessons exist; shooting 2027 is assigned one. Homework-feedback email exists.

| Item | Label |
|---|---|
| Lesson plan for 2027 shooting (how many, which weeks, required or not) | CHECK / decide |
| Coach extra credit | ADD (or drop deliberately) |
| Late homework: pays XP but not Perfect Week | CHECK |
| Parent note on homework; coach feedback text visible to parent | CHECK |
| File-upload homework (drawings, photos) vs quiz-only lessons | CHECK — old had both; new appears quiz/lesson based |

### 7. Video coaching

**Old:** videos went through Make → Lambda → private S3, with a viewer link; one coach feedback record per video file; "Parent Feedback Ready" was a manual tick; a "Do Not Award XP" switch; a coach could rename the file; feedback email.

**New:** coaching threads with videos, feedback, and verifications; "daily practice video attached" event; follow-up verification pays XP; feedback email; Parent FAQ says videos are private.

| Item | Label |
|---|---|
| Private storage, feedback per video, feedback email | SAME |
| Follow-up / improvement verification XP | NEW |
| "Do not award" per video | CHECK |
| Extra credit per video | ADD (or drop) |
| Amounts (25 vs 5 + 5) | CHANGE |

### 8. Meetings (Zoom)

Covered in Part B rows 8–9. The new platform adds scheduling, reschedule counts, cancellation, attendance windows, minimum-minutes threshold, Zoom CSV import with per-row import records, roster entries, and makeup via curriculum lesson. All NEW. Still missing: the 2nd/3rd-meeting bonuses, and any 2027 shooting meetings at all.

### 9. Emails

**Old (six types):** welcome (with per-program copy overrides), daily submission confirmation, homework feedback, video feedback, Sunday weekly summary (built 5:00 am, sent 10:00 am; momentum status, goal %, days logged, XP this week, perfect-week status, weekly and overall awards sections, empty-week variant), Zoom recording approval. Plus parent magic-link sign-in. A handoff queue gave every email an idempotency key, a Draft → Ready → Sent / Failed / Needs Review state, a three-attempt limit, test-mode allowlists, and provider webhooks writing "Sent" back.

**New:** the Communication Platform holds **three** published templates — `daily_submission_confirmation`, `coach_video_feedback`, `homework_feedback` — plus one internal test template. The challenge platform has a weekly-summary job and a "weekly summary ready" event, but no template and no challenge has it switched on. Preferences, suppressions, kill switches, and delivery tracking exist (NEW and better than the old queue).

| Email | Label |
|---|---|
| Daily submission confirmation | SAME |
| Video feedback | SAME |
| Homework feedback | SAME |
| Welcome email (promised in the new Parent FAQ) | ADD |
| Weekly summary (promised in the new Parent FAQ) | ADD — job exists, template and switch-on missing |
| Meeting makeup approved / credited | ADD |
| Level-up, achievement unlocked, award granted | ADD (optional; events already fire) |
| Season-end recap | ADD (was on the old backlog, never built) |
| Parent magic-link sign-in | SAME (Supabase) |

### 10. Public website and leaderboard

**Old `/shoot`:** home, leaderboard (sorted level → lifetime XP → shots → name; grade-band filter K-5 / 6-8 / 9-12; only nine presentation fields, no contact data, enforced by tests), kiosk "public display" with a top-3 podium, opt-in public athlete profile pages (`/athletes/first-last`) with weekly rows and unlocks, levels page, achievements page, awards page, homework and video pages, media kit.

**New:** `/challenges`, per-challenge Overview / Levels / XP Buckets, `/leaderboard` (names, schools, rank, Challenge XP; past seasons browsable), About, FAQs, Parent FAQ, Programs, Registration, Parent Portal sign-in. Light theme, same brand voice.

| Item | Label |
|---|---|
| Levels page, XP buckets page, leaderboard, FAQs | SAME or better |
| Public athlete profile pages (opt-in) | ADD (your backlog called the next version a "family private profile," FUT-057; the Parent Portal may already cover it — CHECK) |
| Kiosk / public display with podium | ADD |
| Achievements page, awards page | ADD |
| Leaderboard tie-break order and grade-band filter | CHECK |
| `robots.txt` and `sitemap.xml` | ADD — both return 404 today |
| Media / publicity kit pages | CHECK (optional) |

### 11. Admin, operations, testing

**Old:** no admin console. Everything ran through Airtable views, 50 automations, a set of dry-run audit scripts (Stages A–J), controlled backfills, a Testing Scenarios table, a season-simulation clock, a Config table with four conflicting rows, and a CHANGELOG.

**New:** versioned rule settings per challenge (83 versions saved so far — every rule change is kept), an audit log of admin actions (363 so far: enrollment goal override, challenge duplicate, pricing publish, group and meeting management, coaching actions, guardian actions), background jobs with retries and execution history, an outbox so nothing is lost between steps, internal/test challenges with invite codes, challenge duplication.

| Item | Label |
|---|---|
| Config as versioned rules, audit log, job retries, outbox | NEW |
| Health dashboard (stuck jobs, failed emails, unreviewed duplicates) | CHECK |
| Season close-out checklist (awards, goal-conquer reconciliation, final recap, archive) | CHECK |
| Grading work queues for coaches (homework / video) | CHECK |
| Integrity audits ("every goal-met athlete has an award", "every XP row has a valid source") | CHECK |
| Disposable test identities and a true staging environment | NEW (internal challenges) — but confirm a real staging environment exists, since the old app lost its DEV base |

### 12. Groups and coaches

**Old:** none. **New:** challenge groups (team / class / cohort / camp) with memberships and assigned coaches. NEW.

---

## Part D — What the new platform has that the old one never did

No action needed; this is the credit column.

- Self-serve registration with Stripe, tiered pricing, waivers, households, headshots, referral tracking.
- Per-challenge versioned rules, so each season's numbers are frozen and auditable.
- One XP ledger with award / reversal / adjustment entries, reasons, and idempotency enforced by the database (the old app enforced this with scripts and "recheck before create").
- Follow-up and improvement video XP.
- Meeting scheduling, Zoom CSV attendance import, minimum-minutes thresholds, excused outcomes, makeup by curriculum lesson.
- Groups and coaches.
- Communication preferences, suppressions, kill switches, delivery tracking.
- Admin audit log and background-job history.
- Internal test challenges with invite codes; challenge duplication.
- Multiple challenge types (Shooting, Dribbling, Reading coming) on one platform — the old SC-143 "shared challenge platform" idea, realised.

---

## Part E — Old-app ideas that were never built and are still absent

Listed so you can decide whether they belong on the new backlog. None are parity gaps.

- Level-up / achievement / milestone notifications (old G12, C-027, FUT-005).
- Per-grade-band leaderboard pages, weekly (not season) leaderboards, streak leaderboards.
- Goal Achiever, Goal Crusher, Comeback Player, Homework Hero achievements.
- Per-shot or accuracy-based XP (the old "5 base + 0.02 per shot" test design that was never switched on).
- Season-end recap email and automated award emailer (FUT-004 / FUT-052).
- Season simulation clock for testing a future season before it starts.

---

## Appendix — Numbers at a glance

| Setting | Old (2025-26) | New shooting 2027 | New dribbling 2027 (for reference) |
|---|---|---|---|
| Per check-in XP | 20 | 10 | 20 |
| Video XP | 25 (+ extra credit) | 5 initial + 5 follow-up | 15 follow-up + 15 improvement + 25 daily-practice feedback |
| Homework XP | 35 (+ extra credit) | 39 (1 lesson) | 33 (7 lessons) |
| Meeting live / makeup | 60 / 30; +30 at 2nd, +40 at 3rd | not set | per meeting |
| Streak 3/5/7/10/20/30/40/50/60 | 10/15/20/30/50/60/75/90/105 (= 455) | 10/15/35/60/90/140/190/250/325 (= 1,115) | 10/15/25/40/60/90/120/200/275 (= 835) |
| Weekly threshold | 100/125/150 % of (goal ÷ 9) = 10/20/30 | 350 shots flat = 25 | goal-met = 25, prorated partial weeks |
| Perfect Week | 100; 5 gates incl. homework and 48 h grace | 100; 7 days + 350 + 3 videos + meeting | — |
| Milestones 25…200 % | 10/15/20/30/40/50/65/80 (120 % tier) | same (125 % tier) | 20/30/40/60/78/100/120/140 |
| Season goals | K-2 2,000 · 3-4 5,000 · 5-6 8,000 · 7-8 10,000 · 9-12 12,000 | same (keys `prek-2`, `3-4`, `5-6`, `7-8`, `9-12`) | — |
| Eligibility bands | same as goals | `k-2`, `3-5`, `6-8`, `9-12` (mismatch) | — |
| Levels | 12, 0–2,200, gates on 7–12 | 4 placeholders, no gates | 12, 0–2,400, gates on G.O.A.T |
| Lifetime XP | yes, across seasons | off by default | off by default |
| Achievements | 15-row catalog | 2 placeholders | 2 placeholders |
| Emails | 6 types + magic link | 3 templates + magic link | same 3 |
