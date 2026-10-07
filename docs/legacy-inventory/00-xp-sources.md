# 00 — XP sources: every way an athlete earns XP in the legacy app

**Purpose:** a complete list of XP "buckets" in the legacy Airtable Shooting Challenge so the new platform can be checked for parity. Companion files `01`–`06` cover every other module.

**Source of truth for this research:** repository automation scripts (`airtable/automations/shooting-challenge/*.js`), `lib/v2-engine-contracts.js` (`SOURCE_KEY_PREFIXES`), the 2026-09-05 PROD schema snapshot, and the PROD config export in `docs/overnight/config-xp/` (2026-07-24). Amounts are read live from `XP Reward Rules` by the automations, so the Airtable table remains the final authority on numbers.

## How XP is stored and totalled

- Every point is a row in **XP Events**. Writers never edit amounts in place except to reconcile the same owned event; events are append-only and never deleted.
- `XP Events.Active XP Points` = `XP Points` when `Active?` is checked and `Duplicate Status ≠ "Duplicate - Remove"`, else 0.
- `Enrollments.Lifetime XP Earned` = rollup of `Active XP Points`.
- `Enrollments.Lifetime XP Total` = `Lifetime XP Earned` + `Lifetime XP Manual Adjustments` (a plain signed number).
- `Weekly Athlete Summary.XP Earned This Week` = rollup of linked `Active XP Points`.
- Each event carries `XP Bucket` (single select), `XP Source` (single select), `Source Key` (idempotency), `XP Activity Date` + `XP Activity Date Source`, `XP Reason Public`, `XP Reason Debug`, `Award Mode` (Automatic / Manual), `Awarded By`.
- Levels (12, 0 → 2,200 XP in 200-XP steps) and Level Gate Rules consume XP; they never produce it.

## The ten XP paths

| # | XP Bucket | XP Source label(s) | Writer automation(s) | Amount (PROD 2026-07-24) | Earned when | Source Key | Frequency / caps |
|---|---|---|---|---|---|---|---|
| 1 | **Shooting Base** | Submission Base | 010 | Rule `SHOOTING_BASE` = 20 | Submission has `Count This Submission? = 1` (not future-dated, Week counts toward challenge, not duplicate Exclude/Needs Review, valid shot total), `Total Shots Counted > 0`, Enrollment/Week/Weekly Athlete Summary linked, Enrollment active / progress-enabled | `SUBMISSION_XP\|{submissionId}` | Flat per counted submission regardless of shot count; multiple same-day submissions each earn it. |
| 2 | **Weekly Threshold** | Weekly Threshold 100 / 125 / 150 | 035 | Rules `WEEKLY_THRESHOLD_{100\|125\|150}_{K2\|34\|56\|78\|912}` = 10 / 20 / 30 (per-band configurable; identical across bands today) | `Goal Completion %` on Weekly Athlete Summary ≥ 1.00 / 1.25 / 1.50, where `Goal Completion % = Total Shots This Week ÷ (Season Goal Shots Target ÷ 9)` | `WEEKLY_THRESHOLD\|{enrollmentId}\|{weekId}\|{percent}` | Up to 3 events per athlete per week, cumulative (150% earns all three = 60). Progressive: re-fires as % rises during the week (`Threshold Settled Through %`). |
| 3 | **Streak** | 3-Day … 60-Day Streak | 053 (Streak Occurrences) → 054 (XP) | Rules `STREAK_{n}DAY`: 3d 10, 5d 15, 7d 20, 10d 30, 20d 50, 30d 60, 40d 75, 50d 90, 60d 105 | Consecutive America/Denver calendar days with ≥1 counted submission; thresholds come from `Achievements` rows with `Trigger Type = "Streak Length"` | `STREAK_XP\|{enrollmentId}\|{achievementId}\|{streakEndDate}` | Cumulative within one streak block (a 10-day streak earns 3+5+7+10 = 75). Repeatable after a break. Occurrences deactivate if submissions are later excluded. |
| 4 | **Shot Milestone** | Shot Milestone | 066 (unlock) → 059 (XP) | `Shot Milestones.Points Awarded` per record (fallback rule `SHOT_MILESTONE`). 8 active tiers per Grade Band at 25 / 50 / 75 / 100 / 120 / 150 / 175 / 200 % of the band's season goal = 10 / 15 / 20 / 30 / 40 / 50 / 65 / 80 | Enrollment lifetime `Total Shots Counted` crosses the tier threshold. Band season goals: K-2 2,000 · 3-4 5,000 · 5-6 8,000 · 7-8 10,000 · 9-12 12,000 | `SHOT_MILESTONE\|{enrollmentId}\|{shotMilestoneId}` | Once per tier per enrollment (max 310 XP). Deactivated if total falls back below. 100% tier also stamps `Enrollments.Goal Met Date` and feeds the Conquered Goal physical award. |
| 5 | **Perfect Week** | Perfect Week | 057 (eligibility helpers) → 058 (unlock) → 059 (XP) | Rule `PERFECT_WEEK` = 100 | All of: counted submission on every official day of the Week (Sun–Sat; partial terminal week allowed), each day ≥ 1/7 of weekly goal, uploaded within grace window (default 48 h after activity date, or manual exception), ≥ Config `Perfect Week Video Minimum` Video Feedback records that week, attended Zoom if a meeting existed that week (live, or approved recording credit when Config allows), 100% of assigned homework satisfactory and submitted by Week End Saturday 11:59:59 pm Denver | `PERFECT_WEEK\|{enrollmentId}\|{weekId}` | Once per athlete per week; evaluated only after the week ends; re-queued via `Perfect Week Recalc Needed?`. |
| 6 | **Homework Completion** | Homework Completion | 064 (prepare) → 065 (XP) | Rule `HOMEWORK_COMPLETION` = 35 base + coach-entered `Extra Credit XP Awarded` (free number) | Coach sets `Satisfactory?` + `Review Complete` + non-blank `Coach Feedback`; Enrollment / Homework (PHA) / Week / Submission Date present | `HOMEWORK_XP\|{homeworkCompletionId}` | One per Homework Completion. Late homework still earns full XP (only Perfect Week excludes it). Unsatisfactory = 0. Same event is updated if extra credit changes. |
| 7 | **Video Feedback** | Video Submission | 113 (prepare) → 114 (XP) | Rule `VIDEO_SUBMISSION` = 25 base + `Extra Credit XP Awarded`; forced to 0 by `Do Not Award XP?` | Coach posts feedback (`Feedback Posted?`), linked Submission countable, non-future, same Enrollment, exactly one Week | `VIDEO_SUBMISSION\|{videoFeedbackId}` | One per Video Feedback record (several per submission/week allowed; up to 3 videos per submission). No grade-band variation. Retired/reactivated when source eligibility toggles. |
| 8 | **Zoom Attendance** (live) | Zoom Meeting Attendance Base / Bonus 2 / Bonus 3 | 101 | Rules `ZOOM_ATTEND_BASE` = 60 per meeting; `ZOOM_ATTEND_BONUS_2` = 30; `ZOOM_ATTEND_BONUS_3` = 40 | Enrollment is in `Zoom Meetings.Attendees` (manually linked by coach) and Meeting Status = Completed, same school year / program instance | Base `ZOOM_ATTEND_BASE\|{meetingKey}\|{enrollmentId}`; bonuses `ZOOM_ATTEND_BONUS_2\|{enrollmentId}`, `ZOOM_ATTEND_BONUS_3\|{enrollmentId}` | Base per meeting attended. Bonus 2 once per season at the 2nd live meeting, Bonus 3 once at the 3rd. Recording credits do not count toward bonuses. |
| 9 | **Zoom Attendance** (recording makeup) | Zoom Meeting Recording Quiz | 101 (SC-147, v6.8+) | Rule `ZOOM_RECORDING` if present → else Config `Zoom Recording XP Percent of Live` (year-aware) → else `floor(live ÷ 2)` → 30 today | `Zoom Attendance` row with `Attendance Method = Recording Quiz`, `Recording Quiz Satisfactory?`, no `Zoom Credit Conflict?`, meeting Completed, coach approval per Config | `ZOOM_RECORDING_CREDIT\|{enrollmentId}\|{meetingId}` | One per meeting per athlete; mutually exclusive with live credit for the same meeting (live wins). Counts for the level-gate Zoom dimension; Perfect Week credit is Config-dependent. Never counts toward Bonus 2/3. |
| 10 | **Manual Bonus** / Manual Adjustment | Manual Adjustment, Coach Bonus | None (human) | Any | Operator edits `Enrollments.Lifetime XP Manual Adjustments` (±) or hand-creates an XP Event with `Award Mode = Manual` | n/a | Ad hoc; no rule record. |

## Mechanics that change totals without being a bucket

- **Withdrawal and restoration.** Every writer (010, 035, 054, 059, 065, 101, 114) flips `Active?` off on its own event when the source becomes ineligible (submission excluded as duplicate, future-dated, homework un-marked, Zoom roster removal, milestone total drops below threshold) and reactivates the same event on restore. No deletes.
- **`Duplicate Status = "Duplicate - Remove"`** zeroes an event in the rollups even if `Active?` is on.
- **Enrollment guards.** `Active?` false or `Progress Processing Enabled?` false suppresses new XP for that enrollment.
- **Dates.** `XP Activity Date` is per bucket (submission activity date, week end date, streak end date, meeting start, milestone activity date); weekly totals and emails key off it.

## Designed in the base but not awarding XP today

Decide deliberately for the new platform rather than inherit by accident.

- **Inactive Achievements** with reward keys but no writer: `Goal Achiever` (GOAL_ACHIEVER, goal % ≥ 100), `Goal Crusher` (GOAL_CRUSHER, goal % ≥ 120), `Comeback Player` (COMEBACK_PLAYER), `Homework Hero` (HOMEWORK_HERO). Shot Milestone tiers at 100% and 120% effectively cover the first two.
- **Orphan `XP Source` options** no script writes: `Coach Bonus`, `Homework Bonus`, `Shot Volume Bonus`, `Streak Bonus`, `Video Bonus`, `Achievement Unlock`, `Video Submissions for Feedback`.
- **Submission-level formula XP** (`XP Base Points` = 5 per counted submission, `XP Volume Bonus` = min(20, floor(shots ÷ 25)), `XP Accuracy Bonus`, `XP Detailed Stats Bonus`, `XP Total Points`). This was the "GOAT starting test setup: 5 base XP + 0.02 XP per counted shot" design noted in the Config table. It does **not** feed `Lifetime XP`; the XP Events pipeline (flat 20 per submission) is the operative one. Per-shot or accuracy XP in the new platform is a new decision, not parity.
- **Current Shooting Streak** (055/056) is display only; streak XP comes solely from Streak Occurrence tiers.

## Parity checklist for the new platform

1. Per-submission flat XP (not per-shot) — and whether multiple same-day submissions each count.
2. Weekly goal tiers at 100 / 125 / 150 % with per-grade-band amounts; weekly goal = season goal ÷ 9.
3. Nine streak tiers, cumulative within a streak, repeatable after a break, derived from activity dates.
4. Eight shot-milestone tiers at % of grade-band season goal, including tiers above 100%.
5. Perfect Week with its five gates (daily shooting with 1/7 pace, grace window, video minimum from config, conditional Zoom, on-time homework).
6. Homework base + coach extra credit; late still pays.
7. Video feedback base + extra credit + "Do Not Award" override.
8. Zoom live base per meeting + one-time 2nd / 3rd meeting bonuses.
9. Zoom recording-quiz credit at a configurable % with live-vs-recording exclusivity.
10. Manual adjustment path (signed number on the athlete, or a manual event).
11. Withdrawal semantics — XP must be reversible (soft-deactivated, never deleted) when the source becomes ineligible.
12. Public and debug reason strings on every event; activity date distinct from created time.
