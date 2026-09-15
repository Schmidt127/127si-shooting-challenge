# XP and progression

**Status:** Authoritative (FUT-058 · 2026-09-15)  
**Registry file:** [`../next-wave/automation-ownership/xp-source-key-registry.json`](../next-wave/automation-ownership/xp-source-key-registry.json)

## Ledger model

| Concern | Authority |
|---------|-----------|
| XP amounts | **XP Reward Rules** table |
| XP ledger | **XP Events** (Active? lifecycle; one Source Key per logical award) |
| Current level | **Enrollment.Current Level** (written by **042**) |
| Level gates | **Level Gate Rules** + **042** |
| Unlocks | **Athlete Achievement Unlocks** → **059** XP |

**Rule:** one source record → at most one Active XP Event for that Source Key. Scripts recheck before create; deactivate/reactivate the same row on lifecycle (do not mint duplicates).

## XP Source Key prefixes (production)

| Prefix | Format | Writer |
|--------|--------|--------|
| `SUBMISSION_XP\|` | `SUBMISSION_XP\|{submissionId}` | **010** |
| `HOMEWORK_XP\|` | `HOMEWORK_XP\|{homeworkCompletionId}` | **065** (064 prepares only) |
| `VIDEO_SUBMISSION\|` | `VIDEO_SUBMISSION\|{videoFeedbackId}` | **114** (113 assigns base) |
| `STREAK_XP\|` | `STREAK_XP\|{enrollmentId}\|{achievementId}\|{streakEndDate}` | **054** |
| `SHOT_MILESTONE\|` / Milestone Source Key | unlock then **059** | **066** → **059** |
| `PERFECT_WEEK\|` | `PERFECT_WEEK\|{enrollmentId}\|{weekId}` | **058** → **059** |
| `WEEKLY_THRESHOLD\|` | `WEEKLY_THRESHOLD\|{enrollmentId}\|{weekId}\|{percent}` | **035** |
| `ZOOM_ATTEND_BASE\|` | `ZOOM_ATTEND_BASE\|{meetingId}\|{enrollmentId}` | **101** |
| `ZOOM_ATTEND_BONUS_2\|` / `_3\|` | enrollment-scoped bonuses | **101** |
| `ZOOM_RECORDING_CREDIT\|` | `ZOOM_RECORDING_CREDIT\|{enrollmentId}\|{meetingId}` | **101** (SC-147) |

### Not live / do not mint

`ZOOM_CREDIT|`, `ZOOM_RECORDING|`, `ZOOM_LIVE|` — historical Stage 17 / design only.

## Domain pipeline

| Domain | Pipeline |
|--------|----------|
| Submission Base | Count It / ready → **010** |
| Homework | **064** prepare → **065** create/reconcile |
| Video | **113** → **114** |
| Zoom live + recording | **101** |
| Streak | **053** occurrences → **054** XP → (**059** if unlock path) |
| Perfect Week | **057** eligibility → **058** unlock → **059** XP |
| Shot milestone | **066** unlock (+ Goal Met Date) → **059** |
| Weekly threshold | WAS ready → **035** |
| Levels | XP change → **041** mark → **042** assign Current/Next with gates |

## XP date resolution

Use Denver-safe date keys (America/Denver) for week boundaries and streak ends — see **053** `toDateKey` (no naive UTC ISO-prefix slice). Submission / homework activity dates follow script helpers in 005 / 020 / 010 families.

## Perfect Week notes

- Config-driven video minimum (SC-034).
- Late homework excluded from Perfect Week credit (FUT-001 / SC-160 policy).
- Early homework can count for assigned-week Perfect Week when policy says so.

## Manual bonus

Manual / admin XP, if used, must still set a unique Source Key and follow Active? lifecycle — prefer documented XP Reward Rules event types; do not invent ad-hoc duplicates.
