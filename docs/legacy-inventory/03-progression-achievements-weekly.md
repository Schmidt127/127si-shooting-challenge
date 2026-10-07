# 03 — Progression, Achievements, Streaks, Perfect Week, Shot Milestones, Awards, Weekly Summary, Standings

**Scope:** Legacy 127 SI Shooting Challenge (`Schmidt127/127-si-shooting-challenge`, repo at `/workspace`). Read-only inventory of the progression/recognition domain so a new platform can reproduce every module, rule, and non-obvious behavior.
**Sources:** Airtable automation scripts under `airtable/automations/shooting-challenge/`, the Production schema snapshot `airtable/schema/snapshots/prod-20260905-fut002-batch2/schema_doc_appn84sqPw03zEbTT_20260905_062812.md` (+ raw JSON), `docs/overnight/config-xp/CURRENT-CONFIG-BASELINE.md`, `docs/overnight/config-xp/prod-config-analysis.txt`, the Next.js data layer under `web/lib/`, and the backlog docs.
**Out of scope here:** XP point amounts, XP buckets, and Source Key formats (documented separately). Where an automation *awards* XP I only note that it does and which automation owns it.

Conventions used below: **WAS** = Weekly Athlete Summary; **PI** = Program Instance; **Denver** = America/Denver, the only timezone the system reasons in; "fail closed" = the automation sets `statusOut=error` and throws rather than guess.

---

## 0. Domain map (what exists, who owns it)

| Module | Tables | Automations (file prefix) | Web surface |
|---|---|---|---|
| Weekly Athlete Summary + goals + momentum | `Weekly Athlete Summary`, `Target Goal Shots`, `Grade Bands`, `Weeks` | 031 (find/create), 030 (grade band), 032 (goal record), 033 (homework), 034 (previous-week helpers); downstream 035/118/119/076 email | Athlete private profile weekly rows |
| Levels / gates | `Levels`, `Level Gate Rules`, `Enrollments` (progression fields), `Zoom Meetings`, `Zoom Attendance`, `Config` | 041 (queue via signature), 042 (assign + gate block), 043 (retired) | `/shoot/levels`, leaderboard, athlete profile |
| Achievements + unlocks | `Achievements`, `Athlete Achievement Unlocks` | 058 (Perfect Week unlock), 066 (shot-milestone unlocks), 059 (unlock → XP, not in my scope) | `/shoot/achievements`, athlete profile |
| Streaks | `Streak Occurrences`, `Enrollments` current-streak fields | 053 (rebuild occurrences), 054 (occurrence → XP), 055 (current streak on submission), 056 (daily refresh) | athlete profile |
| Perfect Week | WAS helper fields, `Config`, `Video Feedback`, `Zoom Attendance`, `Homework Completions`, `Program Homework Assignments` | 057 (eligibility), 058 (unlock) | Perfect Week panel on athlete profile |
| Shot Milestones / goal met | `Shot Milestones`, `Target Goal Shots`, `Enrollments.Goal Met Date` | 066 (+122 superseded) | athlete profile |
| Awards / physical prizes | `Awards`, `Award Recipients` | none in-repo for fulfillment (Tremendous via Make, slated for replacement) | public awards list, weekly email awards sections |
| Standings | `Enrollments` (via `Web - Leaderboard` view) | none (read-only) | `/shoot/leaderboard`, `/shoot/public-display` |

**Important architectural facts the new platform must preserve:**

1. Everything is keyed by **Enrollment** (athlete × program instance × school year), not by athlete. All summaries, streaks, levels, unlocks, and awards hang off the Enrollment.
2. A **Program Instance** is the isolation boundary. Enrollment and Week must share a PI; Weeks are resolved within the PI; Target Goal Shots and Homework Assignments are PI-scoped. (`031`, `032`, `033`, `053`, `057`)
3. **School Year / Rule Set** selects which gate rules apply (exact year beats shared/blank; never a prior year). (`041`, `042`, `lib/v2-engine-contracts.js: selectYearAwareGateRules`)
4. **Formula/rollup/lookup fields are never written** by scripts; scripts compute into dedicated writable helper fields and formulas derive display values from them.
5. All scripts are **idempotent and append-only** toward XP; they distinguish *skip* (expected no-op) from *error* (fail closed, leave the "needs work" flag set so the record is retried).
6. The old base hit Airtable's **automation count cap** — automation 122 was never installed and its job was folded into 066. Several formula fields carry stale copies of business rules (see §8).

---

## 1. Weekly Athlete Summary (WAS)

Table: `Weekly Athlete Summary` (`tbl9520d72adxlAKQ`, 108 fields). One row per **Enrollment × Week**. It is the hub for the weekly email, Perfect Week, weekly threshold XP, momentum, and parent-facing weekly history.

### 1.1 Identity and links

| Field | Type | Meaning / rule | Source |
|---|---|---|---|
| Display (primary) | formula | `Full Name - From Enrollment - Display - Week - Grade Band` | schema |
| `Enrollment`, `Week` | links | the composite key; both required | 031 |
| `Summary Key` | formula | `EnrollmentKey|WeekKey` (via lookups `Enrollment Key`, `Week Key`). Read-only; 031 uses it to find the canonical row | 031 |
| `Weekly Summary Key`, `Duplicate Prevention Key` | formula | secondary dedupe keys used by email pipeline | schema |
| `Grade Band` | link | copied from Enrollment by 030 when blank | 030 |
| `Goal Record` | link → `Target Goal Shots` | exactly one active target for PI + Grade Band (032) | 032 |
| `Homework` | link → `Homework Library` | the assigned homework for this week (033) | 033 |
| `Submissions` | link | every counted submission for the week; 031 links from the Submission side | 031 |
| `Homework Completions Link` | link | completions reconciled by 033 | 033 |
| `XP Events` | link | repaired by 031 for same Enrollment+Week (excluding Submission Base XP which 010 owns) | 031 |
| `Perfect Week Unlock` | link → Unlocks | set by 058 | 058 |
| `Activity Dates`, `Athlete First/Last Name`, `Grade`, `Program Instance` | lookups | display | schema |

### 1.2 Shooting totals, goal, days

| Field | Rule |
|---|---|
| `Total Shots This Week` | rollup `Submissions.Total Shots Counted` |
| `Total Makes This Week` | rollup of makes |
| `Goal Shots Target` | lookup `Goal Record.Total Shot Target` (the *whole-challenge* target for the grade band, e.g. K‑2 = 2000) |
| `Weekly Goal Shots Target` | formula `Goal Shots Target / 9` — **the challenge is 9 weeks long and the weekly goal is 1/9 of the band target** (Config also carries `Challenge Week Count`; the formula hardcodes 9) |
| `Goal Completion %` | `Total Shots This Week / Weekly Goal Shots Target` (ratio, 1.0 = 100%) |
| `Days Logged This Week` | rollup of distinct `Counted Activity Date Key` on submissions |
| `Met Minimum Days Requirement?` | `Days Logged >= 3` (legacy consistency rule; still surfaced) |
| `Threshold XP Ready?` | links present AND `Goal Completion % >= 1` AND (`Requeue Threshold XP` OR status ≠ Processed) — gate for weekly-threshold XP automation |
| `Threshold XP Status` / `Processed At` / `Error Message` / `Requeue Threshold XP` | state for weekly threshold XP (100 / 125 / 150 % tiers per `lib/v2-engine-contracts.js`) |

### 1.3 Momentum (parent-facing)

| Field | Rule |
|---|---|
| `Previous Week Shots` | written by 034 = previous WAS `Total Shots This Week` (0 if no previous) |
| `Previous Total XP` | written by 034 = previous WAS `Total XP After Week` |
| `Weekly Improvement Value` | `IF(Previous Week Shots, Total - Previous, BLANK())` |
| `Momentum Status` | blank prev → **First Week**; improvement > 50 → **On Fire**; > 0 → **Rising**; = 0 → **Steady**; < −50 → **Needs Push**; otherwise negative → **Drop** |
| `XP Earned This Week` | rollup of linked `XP Events.Active XP Points` |
| `Total XP After Week` | `Previous Total XP + XP Earned This Week` (running total, computed by chaining weeks) |
| `Level Number` | **STALE formula** (≥4500→8, 3000→7, 2000→6, 1400→5, 900→4, 500→3, 200→2, else 1). Does not match the live 12-level ladder. Do not port. |

"Previous week" in 034 = same Enrollment, Week Start Date (Denver) strictly earlier, most recent. Week ordering is by **Week Start Date**, not week number.

### 1.4 Homework summary fields

`Homework Assigned Count` (rollup), `Homework Satisfactory Count`, `Homework Completed?`, `Homework Completion %`, `Homework Display` (shows "🚫 No Homework" when none), `Homework Requirement Status` (Not Calculated / Not Required – No Homework This Week / Complete – 100% / Incomplete – N%).

### 1.5 Perfect Week helper fields on WAS

Written by 057, read by 058 and the profile. `Perfect Week Daily Check Status` (Pending/Pass/Fail/Needs Review), `Perfect Week Daily Check Detail` (text), `Perfect Week Daily Requirement Met?` (checkbox), `Perfect Week Video Count`, `Perfect Week Zoom Meeting Count`, `Perfect Week Zoom Attendance Count`, `Perfect Week Homework Assigned Count`, `Perfect Week Homework Satisfactory Count`, `Perfect Week Homework Requirement Met?` (number 0/1), `Perfect Week Automation Status` (Pending/Ready/Created/Skipped/Error), `Perfect Week Automation Error`, `Perfect Week Recalc Needed?` (checkbox), `Perfect Week Video Minimum` (lookup from Config via Enrollment → PI), formulas `Perfect Week Video Requirement Met?` (**hardcoded ≥3**, stale), `Perfect Week Daily Requirement Met? Calculated` (**misnamed**: actually `Video Count >= Video Minimum`), `Perfect Week Zoom Requirement Met?`, `Perfect Week Zoom Requirement Status` (Not Calculated / No Zoom This Week / Attended / Missed), `Perfect Week Eligible?` (Ready & daily & HW=1 & video=1 & zoom=1), `Perfect Week Calculation Queue?` (Enr+Week+Goal linked & (Status=Pending OR Recalc Needed?)). Details in §5.

### 1.6 Email/package fields (for completeness; email itself is another inventory)

`Build Weekly Email Now?`, `Weekly Summary Email Status` (Not Ready / Ready for Send / Sent / Error), `Email Type` (Regular/Preview/Test), `Email Subject` = "Weekly Shooting Challenge Summary for {First}", cleaned parent/athlete emails, `Combined Recipient Emails`, `Weekly Awards Placeholder/Display`, `Overall Awards Placeholder` (AI text) / `Display`, `Weekly Summary Overall Section`, `Zoom Meetings Summary` (AI text), `Upcoming Zoom Display/Link`, `Weekly Email Payload JSON/HTML/Text/Subject/Week Label/Revision/Ready?/Sent?/Sent At/Recipients/Record ID`, `sendMode` (Test/Live), `Send to Make?`, `Make Send Status`, `Hub Event ID/Accepted At`, `Package Build Error`, `Last Package Build Attempt`. The weekly email is built from the WAS row and includes awards sections, Zoom summary, momentum and achievements.

### 1.7 Lifecycle (creation → helpers → Perfect Week)

| Step | Automation | Trigger | Behavior | Skip / error rules |
|---|---|---|---|---|
| 1 | **031** Find-or-create WAS from Submission (v4.1) | Submissions view: Activity Date, Week, Enrollment non-empty; `Count This Submission? = 1`; WAS link empty | Computes expected Summary Key; finds **exactly one** fully valid canonical WAS (Enrollment + Week + Summary Key + same PI); creates one when none, then **re-queries** to detect a race; links Submission ↔ WAS; removes the submission from any stale WAS; repairs XP Event → WAS links for same Enrollment+Week (except Submission Base XP, owned by 010); arms `Submissions.Build Daily Email Now?` (consumed by 076); sets `Summary Calculation Status = Complete`. Actions: `created_canonical_summary`, `found_existing_summary`, `repaired_stale_summary_link` | Skips uncounted submissions, inactive enrollments, unsupported `Submission Stat Mode` (must be "simple total" or "detailed shooting"). Errors on multiple candidate summaries or PI mismatch |
| 2 | **030** Copy grade band (v3.0) | WAS view: Enrollment & Week set, Grade Band empty | Copies `Enrollment.Grade Band` → `WAS.Grade Band` | skip if already set |
| 3 | **032** Link goal record (v3.4) | WAS with Enrollment but no/invalid Goal Record | Finds exactly one `Target Goal Shots` with PI (from Enrollment) + Grade Band + `Active?` + explicit numeric `Total Shot Target` (0 allowed). **Week is not a factor** (the goal is challenge-wide). Validates an existing link | duplicates → error; no match → skip |
| 4 | **033** Assign homework (v4.4) | WAS without Homework (or needing reconcile) | `Program Homework Assignments` is the **sole schedule authority** (PI + Week + Active?). Slots `HW1`/`HW2` sorted; duplicate slot fails closed; PHA Grade Band is metadata only. Writes `WAS.Homework`; reconciles deferred `Homework Completions` (same Enrollment+Week+assigned homework with blank `Weekly Athlete Summary Link`). Absorbed retired 068 | conflict with existing different Homework → error |
| 5 | **034** Previous-week helpers (v3.4) | WAS needing helpers | Finds previous WAS (see §1.3), writes `Previous Week Shots`, `Previous Total XP` (0 when none), `Summary Calculation Status = Complete`, and **arms Perfect Week** (`Perfect Week Automation Status = Pending`) | errors set status Error |
| 6 | 057 / 058 | queue formula | see §5 | |
| 7 | 118 / 119 / 035 | Sunday 5:00 AM Denver | weekly email build targets the latest active non-Post-Challenge week that has **ended** in Denver (partial terminal week 9 included — SC-121) | email inventory |

`Summary Calculation Status` values: Pending / Calculating / Complete / Error.

### 1.8 Supporting tables

**Target Goal Shots** (`tbleCfuAt3rY8unU3`): `Target Label` ("{Band} - {N} shots"), `Total Shot Target`, `Grade Band`, `Active?`, `Goal Key` ("SHOT_GOAL|BAND|N"), `Program Instance`, `Band Sort Order`, links to WAS and Shot Milestones. Baseline notes only **1 record** in PROD; **`Grade Bands.Total Shot Target` is the de-facto source** of the band target used by `Enrollments.Target Goal Shots` and `Goal Met?`. The new platform should have one authoritative band target per program instance.

**Grade Bands**: name formula from Min/Max Grade (PreK–K, K‑2, 3‑4, 5‑6, 7‑8, 9‑12), `Sort Order`, `Default Homework Tier`, `Active?`, `Total Shot Target`. 7 rows (5 active + 2 mojibake legacy).

Live band targets (`CURRENT-CONFIG-BASELINE.md`): K‑2 **2,000**; 3‑4 **5,000**; 5‑6 **8,000**; 7‑8 **10,000**; 9‑12 **12,000** shots for the challenge.

---

## 2. Levels, Level Gate Rules, progression

### 2.1 Levels table (`tblU6EWmc1jCpgRHe`)

| Field | Notes |
|---|---|
| `Level Name`, `Level Name with Color` (single select) | 12 names: Beginner, Rookie Shooter, Developing Shooter, Consistent Shooter, Dangerous Shooter, Hot Hand, Deadeye, Sharpshooter, Pro, All-Star, Legend, G.O.A.T. |
| `Cover Image` | attachment art per level (web shows it) |
| `XP Required (Cumulative)` | lifetime XP threshold; exactly one level must be 0 |
| `XP From Previous Level` | formula delta |
| `Previous Level` / `Next Level` | self links |
| `Active?`, `Sort Order`, `Rank` | ladder order |
| `Unlock Message` | rich text shown on level-up |
| `Public Gate Criteria` | rollup of the active gate rule's `Public Gate Rules - Active Only` text |
| `Level Gate Rules`, `Enrollments - Current Level`, `Enrollments - Next Level` | reverse links |

**Live ladder (12 active, 200 XP apart):** Beginner 0 · Rookie Shooter 200 · Developing Shooter 400 · Consistent Shooter 600 · Dangerous Shooter 800 · Hot Hand 1000 · Deadeye 1200 · Sharpshooter 1400 · Pro 1600 · All-Star 1800 · Legend 2000 · G.O.A.T. 2200.

### 2.2 Level Gate Rules (`tblWIb8JCuQ842HI8`)

A gate is a **behavioral prerequisite to enter a level** in addition to XP. Fields: `Name`, `Level` (exactly one), `School Year / Rule Set`, `Version Active?`, `Gate Enabled?`, `Minimum Submissions`, `Minimum Homework Completions`, `Minimum Video Submissions`, `Minimum Zoom Meetings`, `Minimum Streak Days`, `Level Rank (Lookup)`, `Enrollments Checked by This Gate`, `Global Config` link, `Public Gate Criteria` formula:

> "To unlock this level, athletes must complete:\n• N shooting submissions\n• N homework completions\n• N video submissions\n• N Zoom meeting(s)\n• A N-day shooting streak" (blank when disabled)

and `Public Gate Rules - Active Only`.

**Live gates** (ranks 1–6 are pass-through rows with zeros/disabled):

| Level | Subs | HW | Videos | Zoom | Streak days |
|---|---|---|---|---|---|
| 7 Deadeye | 30 | 6 | 6 | 0 | 0 |
| 8 Sharpshooter | 34 | 8 | 8 | 1 | 0 |
| 9 Pro | 38 | 10 | 10 | 1 | 10 |
| 10 All-Star | 42 | 12 | 12 | 1 | 20 |
| 11 Legend | 50 | 13 | 16 | 2 | 20 |
| 12 G.O.A.T. | 58 | 18 | 20 | 2 | 30 |

Gate inputs on Enrollment are **lifetime counts**: `Total Submissions`, `Total Homework Completions`, `Total Video Submissions`, `Total Zoom Attendances` (count fields) and `Longest Streak Days` (rollup of `Streak Occurrences.Gate Eligible Streak Days`, i.e. only *active* occurrences count).

### 2.3 Enrollment progression fields

| Group | Fields |
|---|---|
| XP | `Lifetime XP Earned` (rollup Active XP Points), `Lifetime XP Manual Adjustments`, `Lifetime XP Total = Earned + Adjustments` |
| Assignment | `Current Level`, `Next Level`, `Level Gate Rule`, `Level Status` (Pending / Processing / Assigned / Gate Blocked / Error), `Level Recalc Needed?`, `Progression Last Queued Signature`, `Progression Last Reconciled Signature` |
| Display | `Current Level - Public Facing Display`, `Level Sort Order - For Softr` (lookup `Levels.Sort Order`, used as primary leaderboard sort), `Current Level XP Required`, `Current Level XP Ceiling` (= next − 1), `Next Level XP Required`, `XP Progress in Current Level`, `XP Needed for Next Level` |
| Gate debug | `Gate Minimum: Submissions/Homework/Videos/Zoom Meetings/Streak Days` (lookups), `Meets Gate: *` formulas (forced 1 when `Gate Enabled Status = Disabled`), `Gate Enabled?`, `Gate Enabled Status`, `Gate Debug Summary`, `Gate Failure Summary - Formula`, `Gate Summary`, `Gate Passes`, **`Gate-Test Eligible Level`** (lookup of the Level attached to the Enrollment's `Level Gate Rule`; i.e. the level the athlete is currently being tested against — the blocked one when Gate Blocked, otherwise the next one) |
| Parent-facing | `Public Progression Status` ("On Track" / "Paused"), `Public Missing Submissions/Homework/Videos/Zoom/Streak` ("N submission(s)", "N homework completion(s)", "N video review(s)", "N zoom attendance(s)", "N more streak day(s)"), `Public Gate Missing Reason` ("Missing: …") |
| Zoom credit | `Effective Zoom Gate Meetings` (written by 042; live ∪ approved recording credit) |

### 2.4 Assignment algorithm (041 → 042)

**041 — Mark Enrollment for Level Recalculation (v5.1), scheduled every 15 min.** Builds a **signature** JSON (`version: 2`) of everything that can change the outcome: enrollment inputs (Lifetime XP Total, manual adjustments, the 4 lifetime counts, Longest Streak Days, School Year, Active?), current outputs (currentLevel, nextLevel, levelGateRule, levelStatus), PI, the relevant levels (current/next/reachable + first unreached), and the matching/shared-year gate rules for those levels. If signature ≠ `Progression Last Reconciled Signature` → set `Level Recalc Needed?` and `Progression Last Queued Signature`. Already-pending → skip. Inactive enrollment → advance signature only (no queue). This replaces per-event triggers and makes level recalculation cheap and self-healing.

**042 — Assign Current and Next Level with Gate Blocking (v4.1.3).** Trigger view "042 - Needs Level Assignment" (`Level Recalc Needed?` & `Active?`).

1. `buildLevelList`: active, named, finite non-negative **unique** thresholds, exactly one 0-XP level; otherwise error.
2. `buildGateRuleMap`: `Version Active?`, exactly one Level link; exact School Year match beats shared/blank; two exact matches or zero usable → error; **never fall back to a prior year**; the five minimums must be non-negative numbers.
3. `computeEffectiveZoomAttendanceCount`: live attendance (`Zoom Meetings.Attendees`) ∪ **Recording Quiz** attendance (`Zoom Attendance` rows that are approved, no conflict, `Zoom Gate Credit Earned?`, review ≠ Needs Correction); prefer live when both; marks `Gate Credit Applied?` on the recording row; persists `Effective Zoom Gate Meetings`.
4. `evaluateGate`: no rule or `Gate Enabled? = false` → pass; otherwise compare each minimum; failures recorded as `Submissions a/b; Homework a/b; Videos a/b; Zoom a/b; Streak a/b`.
5. `determineAllowedLevelWithGateBlocking`: walk the ladder while `XP ≥ threshold`; **the first level whose gate fails stops the walk** → `Current Level` = last allowed, `Next Level` = blocked level, `Level Gate Rule` = blocked rule, `Level Status = Gate Blocked`. If no block → Current = highest XP-qualified level, Next = following level, `Level Gate Rule` = next level's gate, `Status = Assigned`.
6. Writes, re-reads to verify, then writes `Progression Last Reconciled Signature` = queued signature and clears `Level Recalc Needed?`. On error keeps the flag set and `Level Status = Error`.

Key behaviors: XP alone never promotes past a failing gate; gates can also be *re-failed* only via inputs decreasing (counts are lifetime so this is rare); a disabled gate is a pass; Level Status "Processing" is transient.

**043 (v2.1) retired** — used to set `Level Gate Rule` from `Next Level` separately; 042 now owns that field.

### 2.5 What parents/athletes see

- `/shoot/levels` (`web/lib/data/levels.ts`, `web/lib/release/public-surface.ts`): ascending ladder with name, color label, cover image, cumulative XP, delta from previous, rank, and "Advance requirements" from `Public Gate Criteria`; fallback copy "No extra gates for this tier — reach the lifetime XP threshold…".
- Athlete profile: current level, XP progress in level, XP needed for next, `Public Progression Status`, `Public Gate Missing Reason` and the five `Public Missing *` strings (so a parent sees "Missing: 2 video review(s), 1 zoom attendance(s)").
- Leaderboard sorts by level first (§7).
- Level-up notification (C-027 / FUT-005) was never built — levels change silently today.

---

## 3. Achievements catalog and unlocks

### 3.1 Achievements (`tblrADEQbvH9kBfMZ`)

| Field | Values / notes |
|---|---|
| `Achievement Name`, `Achievement Key` (lower snake), `Description`, `Internal Notes` | |
| `Achievement Type` | Behavior / Progress / Milestone / Challenge / Secret |
| `Category` | Streak / Consistency / Volume / Homework / Improvement / Comeback / Engagement / Special |
| `Trigger Type` | Goal % / Shots Total / Days Logged / Streak Length / Homework Completed / Weekly Challenge Completed / Improvement / Comeback / Engagement Score / Manual |
| `Trigger Threshold`, `Trigger Operator` (>=, =, <=), `Threshold Value` | numeric trigger |
| `Repeatable?`, `One-Time Unlock?`, `Week-Specific?`, `Week` | repeat semantics |
| `Active?`, `Visible?`, `Sort Order`, `Badge Icon Name`, `Rarity` (Common/Uncommon/Rare/Epic/Legendary) | catalog/display |
| `Reward Rule Key` | joins to XP Reward Rules (e.g. `PERFECT_WEEK`, `SHOT_MILESTONE`, `STREAK_nDAY`) |
| `Submission Grace Period Hours` | used by 057 for Perfect Week grace (default 48) |

**Live catalog (15 rows):**

| Achievement | Trigger | Threshold | Active | Repeatable |
|---|---|---|---|---|
| 3 / 5 / 7 / 10 / 20 / 30 / 40 / 50 / 60-Day Streak | Streak Length | 3…60 | yes | yes (re-earnable after a break) |
| Perfect Week | Weekly Challenge Completed | 7 | yes | per week |
| Shot Milestone | Shots Total | 100 (nominal; real tiers live in Shot Milestones) | yes | per milestone |
| Goal Achiever | Goal % | 1.0 | **inactive** | |
| Goal Crusher | Goal % | 1.2 | **inactive** | |
| Comeback Player | Comeback | — | **inactive** | |
| Homework Hero | Homework Completed | 1 | **inactive** | |

Only three *mechanisms* are automated (streak, perfect week, shot milestone). Goal %/Comeback/Homework/Days Logged/Improvement/Engagement/Manual trigger types exist as catalog ideas and should be first-class rule types in the new engine.

### 3.2 Athlete Achievement Unlocks (`tblyT2AQo1JbvmvZS`)

| Field | Notes |
|---|---|
| `Enrollment`, `Athlete`, `Achievement`, `Week`, `Weekly Athlete Summary`, `Shot Milestone` | links |
| `Unlock Key` formula | `Enr|Ach|WEEK:w[|SHOT_MILESTONE:m][|STREAK_RUN_START:date]` |
| `Milestone Source Key` | writable dedupe key owned by the creator (058, 066) |
| `Date Unlocked`, `Milestone Activity Date`, `Unlock Source Date` (= Milestone Activity Date else Date Unlocked) | the activity date the unlock is credited to |
| `Active?` | soft delete / withdrawal (e.g. shots fell below a milestone) |
| `Source Status` (Pending / Ready for XP / Awarded / Skipped / Error), `XP Award Status` (Pending / Awarded / Skipped / Error), `XP Awarded`, `XP Events` | 059 awards XP from unlocks |
| `Ready for 059 XP?` formula | Enr+Ach+Pending+no XP Events |
| `059 Lifecycle Trigger?` formula | Pending+Active, **or** Awarded+Inactive (withdrawal) |
| `First Time Unlock?`, `Repeat Unlock Count` | repeat tracking |
| `Display in Weekly Email?`, `Display in Dashboard?`, `Included in Summary?`, `Week Summary` | surfacing flags |
| `Trigger Value`, `Trigger Context`, `Coach Note` | explanation shown to parents ("1,500 of 2,000 shots") |
| `Streak Instance Key`, `Streak Start Date` | legacy streak-unlock fields (streaks now use Streak Occurrences instead) |
| Lookups: Achievement Type, Category, Visible?, Rarity | |

Lifecycle: creator writes unlock with `Source Status = Pending` (or `Ready for XP`) → 059 creates one XP Event per unlock and marks Awarded → if the creator later deactivates the unlock (`Active? = false`), 059 deactivates the XP Event; reactivation restores it. Unlocks are **never deleted**.

Web: `/shoot/achievements` (`web/lib/data/achievements.ts`) renders the catalog (name, description, type, category, rarity default Common, trigger type/threshold, sort, badge icon, repeat flags) for `Active? && Visible?`. Athlete profile lists unlocks with `Date Unlocked`, `XP Awarded`, `Trigger Value`, `Shot Milestone`.

---

## 4. Streaks

### 4.1 Model

A **streak** = consecutive Denver calendar days with at least one *counted* submission (`Count This Submission? = 1`, `Total Shots Counted > 0`, `Activity Date` present). Multiple submissions on the same day collapse to one day. Streaks are **derived entirely from submission Activity Dates**; nothing is incremented.

Two representations:

1. **`Streak Occurrences`** (`tbl9VxLdBiNcev4He`) — one row per (Enrollment, streak-length Achievement, Streak End Date). Fields: `Name` ("Enr - Ach - M/D/YYYY"), `Active?`, `Enrollment`, `Achievement`, `Achievement Key`, `Streak Days` (= threshold), `Streak Start Date`, `Streak End Date`, `Week`, `Awarded At` (created time), `XP Events`, `Source Status` (Pending / Ready for XP / Awarded / Duplicate / Error), `Notes`, `Streak Date Key`, `Streak Occurrence Key` ("streak|enr|achkey|date"), `Source Submission Date`, `Trigger Submission Date`, `Last Evaluated At`, `Gate Eligible Streak Days` (= Streak Days when Active; feeds `Enrollments.Longest Streak Days`).
2. **Enrollment current-streak fields** — `Current Shooting Streak` (int), `Current Shooting Streak As Of` (date), `Current Shooting Streak Status` (Active / Broken / No Submissions), `Current Shooting Streak Last Checked At`.

### 4.2 Rebuild and award (053 / 054)

**053 — Streak Occurrences rebuild/upsert (v5.8).** For an enrollment: gather valid dates → `buildStreakBlocks` (runs of consecutive days). For each active Achievement with `Trigger Type = Streak Length` (threshold > 0, ascending) and each block with length ≥ threshold → one occurrence whose `Streak End Date = block[threshold-1]` (the day the threshold was *first reached*), `Streak Start Date = block[0]`, `Streak Days = threshold`, `Week` resolved by PI-scoped Week date ranges. Identity = Enrollment + Achievement + End Date. New rows are created **without** Ready status and then updated to "Ready for XP" so 054's update trigger fires. Rows no longer supported by the dates are **deactivated** (not deleted); restored dates reactivate them; duplicate identities keep the oldest Active/Ready row and mark the others `Duplicate` + inactive.

Consequences the new platform must keep:
- A 10-day block yields 3-, 5-, 7-, 10-day occurrences (all nested thresholds), each with its own end date.
- The **same achievement is re-earnable after a break** (a second 3-day block → second 3-Day Streak occurrence). Policy line in the work list confirms streak rewards repeat automatically after a break (SC-081 resolved).
- Deleting/uncounting a submission can retroactively dissolve a streak → occurrence deactivated → its XP withdrawn by 054.
- Future-dated submissions make occurrences "inactive under Production NOW()" (frozen baseline note), so evaluation is date-relative.

**054 — Create or repair Streak XP Event (v5.8).** One XP Event per occurrence (XP Activity Date = Streak End Date, Award Mode Automatic), links the WAS by Enrollment+Week, sets `Source Status = Awarded`; lifecycle trigger watches `Active?` / `Source Status` to deactivate/restore; more than one active XP Event for an occurrence → error.

### 4.3 Current streak (055 / 056)

**055 (v3.2)** runs on a submission: from counted Activity Dates, if the most recent date is **today or yesterday** (Denver) → `Status = Active`, count backward through consecutive days; otherwise `Broken` with 0; no counted submissions → `No Submissions`. Writes the four Enrollment fields.

**056 (v1.2)** daily at **3:15 AM Denver** for all active enrollments: recomputes the streak *through yesterday*; no submission yesterday → 0/Broken. This is what makes a streak visibly "break" without any new submission.

Longest streak: not a stored max; it is `Longest Streak Days` = rollup max of active occurrences' `Gate Eligible Streak Days` (so "longest" is quantized to the achievement thresholds 3/5/7/10/20/30/40/50/60, not the true run length). The new platform should store the true longest run and also the threshold-based value for gates.

Grace: streaks have **no grace period** — the day is the Activity Date (the day the shooting happened), which is itself allowed to be back-dated by the submitter; submission timing grace only matters for Perfect Week.

---

## 5. Perfect Week

### 5.1 Rules (057 v2.7 — `057-...calculate-perfect-week-eligibility.js`)

A WAS is a Perfect Week when, for the official week, **all** of the following hold:

| Component | Rule | Data |
|---|---|---|
| **Daily shooting** | A qualifying submission on **every official day of the Week** (`Week Start Date`..`Week End Date`, 1–7 days; terminal partial week 9 is allowed to be short), **and** each day's counted shots ≥ `dailyMinimum = ceil(Weekly Goal Shots Target / 7)` | Submissions; WAS `Weekly Goal Shots Target` |
| Submission timing | `classifySubmissionTiming` → `on_time` (submitted the same Denver day as Activity Date), `grace_period` (submitted ≤ end of activity day + grace hours; grace from `Achievements.Submission Grace Period Hours` on the PERFECT_WEEK achievement, default **48 h**), `late`, `manual_exception` (`Submissions.Perfect Week Manual Exception?` checkbox), `ineligible`. on_time, grace_period, and manual_exception qualify. Submission formulas `Perfect Week Grace Eligible?` / `Perfect Week Countable Submission?` mirror this | Submissions |
| **Videos** | count of `Video Feedback` rows linked to the week's submissions ≥ `Config.Perfect Week Video Minimum` (year-aware Config lookup, fail closed if missing) | Video Feedback, Config |
| **Zoom** | if any `Zoom Meetings` exist for the Week: attended live **or** approved Recording Quiz attendance (`Zoom Attendance` approved, no conflict, `Effective Recording Counts for Perfect Week?`, review ≠ Needs Correction) for ≥1 meeting; marks `Perfect Week Credit Applied?`. No meetings that week → pass ("No Zoom This Week"). Config flag `Recording Makeup Counts for Perfect Week?` governs whether recordings count (policy note in work list says recorded Zoom does *not* count for Perfect Week by default but *does* count for level gates at half XP) | Zoom Meetings, Zoom Attendance, Config |
| **Homework** | 100 % of homework assigned for the Week (from `Program Homework Assignments`, PI+Week+Active) has a **Satisfactory** `Homework Completion` with `Submission Date ≤ Week End Saturday` (early completion counts; PHA Due Date ignored). No homework assigned → pass. Fallback derives the assigned set from completions when PHA is empty | PHA, Homework Completions |
| Preconditions | Enrollment active; WAS goal settled (`Goal Shots Target` equals `Goal Record.Total Shot Target`); evaluation only **after Week End** (helper counts may be written early but Pass/Fail waits) | |

Outputs on WAS: `Perfect Week Daily Check Status` Pass/Fail/Needs Review, `Daily Check Detail` text (per-day table of shots/timing), `Daily Requirement Met?`, the Video/Zoom/Homework counts and `Homework Requirement Met?`, `Perfect Week Automation Status = Ready`, clears `Perfect Week Recalc Needed?`. Inactive enrollment or unsettled goal → Needs Review / Error.

### 5.2 Unlock (058 v1.7)

Trigger: WAS lifecycle (recordUpdated on status/helper fields, not on the unlock link). When `Perfect Week Eligible?` is true, upsert an `Athlete Achievement Unlock` with `Milestone Source Key = PERFECT_WEEK|{enrollmentId}|{weekId}`, Achievement = `Reward Rule Key = PERFECT_WEEK`, Week, WAS link, `Coach Note`, `Source Status = Pending`; links `WAS.Perfect Week Unlock`. If eligibility later flips false → deactivate the unlock (restore if it flips back). XP comes from 059.

### 5.3 Recalculation queue

`Perfect Week Calculation Queue?` (formula) = Enrollment+Week+Goal Record linked AND (`Automation Status = Pending` OR `Recalc Needed?`). 034 arms Pending when it finishes helpers; any later change (new submission, video review approved, Zoom attendance approved, homework graded) must set `Perfect Week Recalc Needed?` to re-run 057. Statuses: Automation Status Pending → Ready → Created (unlock made) / Skipped / Error; Daily Check Status Pending → Pass/Fail/Needs Review.

### 5.4 Display

Athlete profile Perfect Week panel (`web/.../perfect-week-panel.tsx`): "Perfect Week" / "In Progress" / "Not Perfect", with video count, `Homework Requirement Status`, `Zoom Requirement Status`. FUT-013 plans a richer day-by-day activity panel.

### 5.5 Divergences to note

- `lib/v2-engine-contracts.js: evaluatePerfectWeekEligibility` defaults `requiredDailyCount = 5` — stale vs. 057's "every official week day". Trust 057.
- WAS `Perfect Week Video Requirement Met?` formula hardcodes ≥3; 057 uses Config. Config also has **4 conflicting records** per the baseline doc; the new platform needs one config per program instance/year.

---

## 6. Shot Milestones, Goal Met, Conquered Goal, Award Recipients

### 6.1 Shot Milestones (`tbl5C4TsQpOigIyRz`)

| Field | Rule |
|---|---|
| `Milestone Label` | "{TargetGoal} - {pct}%" |
| `Target Goal Shot` (link), `Grade Band` / `Band Sort Order` lookups, `Target Shots Lookup` | |
| `Milestone Percent` | 25 / 50 / 75 / 100 / 120 / 150 / 175 / 200 |
| `Milestone Shot Count` | `ROUND(target × pct / 100)` |
| `Milestone Tier` | 25 Starter · 50 Building · 75 Strong · 100 **Conquered** · 120 Beyond Target · 150 High Achievement · 175 Elite Achievement · 200 Premier Achievement |
| `Points Awarded` | SWITCH by percent (amounts documented elsewhere) |
| `Active`, `Notes`, `Milestone Unique Key` ("TargetGoal|pct"), `Sort Order`, XP Events / Unlocks links | |

Live: 5 active bands × 8 tiers = 40 active rows (+16 legacy inactive). Examples: K‑2 (2000) → 500 / 1000 / 1500 / 2000 / 2400 / 3000 / 3500 / 4000; 9‑12 (12000) → 3000 … 24000.

### 6.2 Automation 066 (v4.1) — milestone unlocks + Goal Met Date

Trigger: `Enrollments.Run Shot Milestone Check?` (armed by 010 after each successful submission reconciliation). Steps:

1. Sum counted shots for **this** enrollment only.
2. Load active Shot Milestones for the enrollment's Grade Band (link-ID match, label fallback).
3. For every milestone with `Milestone Shot Count ≤ total` ensure one Unlock (`Milestone Source Key = SHOT_MILESTONE|{enrollmentId}|{shotMilestoneId}`, `Milestone Activity Date` = Activity Date of the counted submission that crossed it, `Week`, `XP Award Status = Pending`; 059 awards). `detectShotMilestoneCrossings` (contracts) = `prev < threshold ≤ curr`.
4. Unlocks whose threshold is no longer met (shots removed) → `Active? = false`; restored → reactivate.
5. **SC-163:** stamp `Enrollments.Goal Met Date` = the first counted Activity Date on which cumulative counted shots ≥ `Target Goal Shots`. Date-only; never overwrite once set; fail closed if unprovable. Must **not** TZ-convert a date-only value (v4.0 double-shift bug: UTC-midnight → Denver → previous day, then dateTime field → another day).
6. Clear `Run Shot Milestone Check?` except on error.

Docblock: "THIS IS NOT: Conquered Goal award fulfillment / Award Recipients.Date Awarded."

Enrollment fields: `Total Shots Counted`, `Total Shots Submitted` (rollups), `Target Goal Shots` (via Grade Band), `Goal Met?` formula = "🟢 🏆 GOAL MET!" when counted ≥ target, `Goal Met Date` (writable date-only per SC-163 — note the 2026‑09‑05 snapshot still shows it as a lookup of `Award Recipients.Date Awarded`; the deploy checklist `docs/deploy-checklists/SC-163-goal-met-date.md` records the schema fix), `Run Shot Milestone Check?`, `Award Recipients` link. `122-...stamp-goal-met-date.js` is a superseded stub (throws) because the base was out of automation slots.

### 6.3 Awards catalog (`tbltlhInAQPtOB8hx`)

| Field | Values |
|---|---|
| `Award Name`, `Award Code`, `Award Description`, `Email Display Name`, `Email Short Name`, `Default Email Description/Label`, `Default Winner Text`, `Default No-Winner Text` | copy |
| `Award Scope` | Weekly / Overall / Both |
| `Summary Section Group` | Weekly Awards · Entire Challenge Awards · Both · Hidden · Overall Shot Champion · Overall XP Champion · Overall Homework Champion · Overall Zoom Champion · Overall Amazon Gift Card Winner · Overall Consistency Award |
| `Award Category` | Shots / XP / Homework / Zoom / Milestone / Achievement / Gift Card / Participation / Other / Video / Motivation / Random |
| `Award Type` | Performance / Participation / Prize / Recognition / Bonus |
| `Prize Type` | Amazon Gift Card / Physical Prize / Recognition Only / Badge / Other |
| `Prize Value` (currency), `Gift Card Award?`, `Requires Manual Fulfillment?`, `Recurring Award?` | fulfillment |
| `Include in Weekly/Overall Awards Section?`, `Eligible for Weekly/Overall Summary?`, `Challenge Active?`, `Current Challenge Eligible?`, `Active?`, `Sort Order` | email/visibility |

Historical award names seen in hygiene docs: Conquered Goal, Random Drawing Incentive, Dedication, Grade Band mid-season awards, Overall Shot/XP/Homework/Zoom Champion, Consistency Award, Amazon Gift Card Winner.

### 6.4 Award Recipients (`tblTyQXl8aEP93ubK`)

| Field | Notes |
|---|---|
| `Enrollment`, `Award`, `Week` (blank = OVERALL), `Award Scope` (Weekly/Overall), `Award Amount`, `Date Awarded`, `Delivery Method` (Email / In Person / Manual / Other) | core |
| `Award Status` | Approved / Cancelled / Delivered / Failed / In Amazon Cart / Pending / Sending / Sent |
| `Gift Card Needed?`, `Award Recipient Unique Key`, `Ready to Send?` formula, Parent Email/Send formulas | |
| Tremendous fields | `Environment` (Sandbox/Production), `External ID` (`AWARD|{key}`), `Reward ID`, `Order ID`, `Delivery Status` (Not Sent/Pending/Scheduled/Succeeded/Failed/Canceled/Flagged), `Sent At`, `Delivered At`, `Error Message`, `Response`, `Test Record?`, `Send to Tremendous?` |
| `Coach Feedback - Awards` (rich text) | personal note per award |
| **`Public On Web`** (checkbox) | **sole** publication gate for the public awards list (`web/lib/data/public-awards.ts`); `Award Status` must never gate visibility |

**Conquered Goal** = the 100 % Shot Milestone tier *as a physical/gift-card award*: when an athlete's `Goal Met?` is true, staff create an Award Recipient (Award = Conquered Goal) and fulfil it (gift card or prize). `Goal Met Date` (activity truth, 066) and `Date Awarded` (fulfilment) are deliberately separate. A post-close audit (`audit-final-goal-conquer-reconciliation.js`) checks every Goal Met enrollment has a Conquered Goal recipient (14/14 in 2025‑26). Hygiene items: recipient scope "Weekly" on rows whose Award is Overall/Both (H‑0xx), optional `Conquered Goal Date` lookup filter (SC‑129/H‑006).

Fulfilment path today: Make.com → Tremendous (sandbox tested, C‑028); FUT‑004 / FUT‑052 replace this with a simple automated award emailer. Weekly and overall awards are also rendered into the weekly summary email sections (`Weekly Awards Display`, `Overall Awards Display`).

---

## 7. Standings, leaderboards, public display, privacy

| Aspect | Rule | Source |
|---|---|---|
| Source | `Enrollments` through the Airtable view **`Web - Leaderboard`** (Mike-controlled filter); fallback formula `AND({Active?}, {Lifetime XP Total} >= 0)`. No Standings/Leaderboard/Badge tables exist; the board is computed at read time | `web/lib/airtable/queries.ts`, `web/docs/airtable-views.md` |
| Ranking | `Level Sort Order - For Softr` desc → `Lifetime XP Total` desc → `Total Shots Counted` desc → name → record id (deterministic ties) | `web/lib/data/leaderboard.ts` |
| Eligibility (SC‑161) | `Active?`; exactly one Athlete link; PI + School Year scope; `Level Status ∈ {Assigned, Gate Blocked}`; `Current Level - Public Facing Display` matches linked active level; XP ≥ that level's threshold; dedupe Athlete+PI+Year keeping the higher-ranked row | same |
| Fields exposed | display name, school, grade, grade band label, level name, headshot, lifetime XP, total shots, public profile slug (only when `Public Profile Enabled`) — **9 presentation fields, no contact data**, enforced by unit tests | `web/lib/release/public-standings.test.ts` |
| Grade-band filter | client-side K–5 / 6–8 / 9–12 / other re-rank within band | `grade-bands.ts` |
| Public display | `/shoot/public-display` kiosk: top 10 + podium for top 3, same query | `public-surface.ts` |
| Caching | 120 s ISR | |
| Schmidt test athlete | Code is name-blind; exclusion only via view filter (SC‑004 decided: keep visible) | `PUBLIC-STANDINGS-AUDIT.md` |
| Public athlete profile | `/shoot/athletes/{slug}`; slug = lowercase `first-last`; enabled by `Public Profile Enabled`; strict field allowlist (level/XP progress, streak fields, target & Goal Met?, Public Progression/Missing *, WAS rows: Week Label, Total Shots, Days Logged, XP Earned, Goal Completion %, Momentum Status, Homework Completed?, Perfect Week fields; unlocks; XP Events); privacy tests assert no record ids/emails leak, opaque keys, weeks newest-first excluding future weeks | `web/lib/data/public-athlete-profile.ts` |
| Public awards | Award Recipients with `Public On Web` only; fail closed when field missing | `public-awards.ts` |
| Weekly email standings | none — the email shows the athlete's own summary + awards sections, not a ranked table | WAS fields |

Not built but planned: per-grade-band leaderboards as separate pages, weekly (not lifetime) leaderboards, streak leaderboards, family private profile (FUT‑057).

---

## 8. Known gaps, inconsistencies, and future ideas

### 8.1 Inconsistencies found in the legacy data model (fix in the new platform)

| # | Issue | Where |
|---|---|---|
| G1 | WAS `Level Number` formula uses an 8-level ladder; live ladder is 12 levels at 200 XP | schema |
| G2 | WAS `Perfect Week Video Requirement Met?` hardcodes 3; 057 reads Config | schema vs 057 |
| G3 | `Perfect Week Daily Requirement Met? Calculated` is actually the video check | schema |
| G4 | `Weekly Goal Shots Target = /9` hardcoded while Config has `Challenge Week Count` | schema |
| G5 | `Goal Met Date` snapshot = Award lookup; SC‑163 made it writable date-only | snapshot vs deploy checklist |
| G6 | `Target Goal Shots` has 1 record; `Grade Bands.Total Shot Target` is used in practice | baseline |
| G7 | Config has 4 conflicting records; year-aware lookup needed | baseline |
| G8 | `Level Gate Rules` has no Program Instance link — gates scoped by School Year only; same-year multi-program isolation unproven | PKG‑036 preflight |
| G9 | `Longest Streak Days` is quantized to achievement thresholds, not the true run | schema/053 |
| G10 | Contracts lib default `requiredDailyCount = 5` vs 057 all-week-days | `lib/v2-engine-contracts.js` |
| G11 | Automation slot cap forced 122 into 066; 043 retired; 032/033/063/111 deleted/re-versioned over time | automation-index |
| G12 | Level changes, milestone unlocks, streak awards produce no notification | C‑027 / FUT‑005 |
| G13 | Award Recipients scope mismatches vs Awards catalog on historical rows | post-close hygiene |

### 8.2 Backlog items (IDs from `docs/127-SI-MASTER-FUTURE-WORK-LIST.md`, `docs/roadmap/`, `docs/production-architecture/FROZEN_BASELINE_AND_FUTURE_WORK.md`)

| ID | One line |
|---|---|
| FUT-004 / FUT-052 | Replace Tremendous with a simple automated award emailer / provider; decision locked, activation separate |
| FUT-005 | Major-event notifications: streak occurrence, shot milestone, challenge goal met |
| FUT-011 | Athlete page level graphic (cover image / progress ring) |
| FUT-013 | Perfect Week activity panel (day-by-day) on athlete page |
| FUT-015 | Levels page redesign |
| FUT-025 | Sitemap + public profiles SEO |
| FUT-027 | Gift-card commitment FAQ for parents |
| FUT-038 | Global category on/off (e.g. disable Zoom or Homework for a season) — disabled categories must auto-pass/zero gate dimensions so G.O.A.T. stays reachable |
| FUT-049 | Remove Grade Band from Program Homework Assignments (metadata only) |
| FUT-050 | Dribble Challenge decision — shared platform must share identity, enrollment, XP, levels, achievements, progression, rewards; primary metric shots vs dribble minutes |
| FUT-051 | Unused-field cleanup program (many WAS/email helper fields) |
| FUT-054 | Player Manual + game addendum (rules explained to families) |
| FUT-057 | Family private profile redesign |
| SC-034 | Perfect Week config closeout (video minimum / grace from Config) |
| SC-081 | Streak rewards repeat after a break — resolved policy |
| SC-082 | Early-level gate tuning (gates only start at rank 7 today) |
| SC-085 | Recorded Zoom meetings count for gates at half XP; not for Perfect Week by default |
| SC-090/091/092 | Zoom integration (attendance import, recording quiz) |
| SC-121 | Weekly email targets latest ended week including partial terminal week |
| SC-127/128/129 | Awards cleanup; Conquered Goal Date lookup filter |
| SC-144 | Rename `Level Sort Order - For Softr` (legacy Softr naming) |
| SC-161 | Leaderboard eligibility/dedupe repair (complete) |
| SC-163 | Goal Met Date reliability (complete, 066 v4.1) |
| SC-168 | Weekly email handoffs |
| SC-169 | Missing achievement unlocks audit |
| C-021 / C-022 | Public display fields must not be primary/formula fields |
| C-027 | Level-up / milestone notifications |
| C-028 | Tremendous sandbox send test |
| V2-005 / V2-007 | Tune Level Gate Rules / Levels for next season |
| PKG-036 / 038 / 039 / 040 | Production proof packets: progression, streak+milestone XP, WAS/weekly goal, standings |

### 8.3 Ideas present only as catalog rows or formulas (never automated)

- Goal Achiever (100 % of weekly goal) and Goal Crusher (120 %) achievements; weekly threshold XP at 100/125/150 % exists in contracts (`WEEKLY_THRESHOLD_{pct}_{band}`).
- Comeback Player, Homework Hero, Days Logged, Improvement, Engagement Score, Manual achievements.
- `Met Minimum Days Requirement? (≥3 days)` weekly consistency rule.
- Achievement `Rarity`, `Badge Icon Name`, `Secret` type, `Week-Specific?` achievements.
- Award categories Video / Motivation / Random (random drawing incentive) and Recognition-only / Badge prize types.
- AI-generated text fields on WAS (`Overall Awards Placeholder`, `Zoom Meetings Summary`) for email copy.
