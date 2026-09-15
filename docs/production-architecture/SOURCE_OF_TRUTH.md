# Source of Truth matrix

**Status:** Verified against production behavior (FUT-058 · 2026-09-15)

| Domain | Source of Truth |
|--------|-----------------|
| Athlete enrollment / identity | SC Airtable **Enrollments** + **Athletes** |
| Daily submissions | SC **Submissions** |
| Submission media / upload state | SC **Submission Assets** (+ S3 canonical after upload) |
| Homework completion / grade | SC **Homework Completions** |
| Curriculum attempt/response detail | SC **Homework Attempts** / **Homework Responses** (+ Curriculum Hub) |
| Video feedback | SC **Video Feedback** |
| Zoom attendance | SC **Zoom Attendance** / **Zoom Meetings** |
| XP ledger | SC **XP Events** |
| XP amounts / event types | SC **XP Reward Rules** |
| Current level / next level | SC **Enrollment** fields written by **042** |
| Level gate definitions | SC **Level Gate Rules** + **Levels** |
| Achievement unlocks | SC **Athlete Achievement Unlocks** |
| Streak instances | SC **Streak Occurrences** |
| Perfect Week eligibility flags | SC **Weekly Athlete Summary** (+ **057**) |
| Weekly calculations / email package | SC **Weekly Athlete Summary** |
| Season calendar | SC **Weeks** (manual; not disposable) |
| PHA schedule | SC **Program Homework Assignments** |
| Feature flags / Perfect Week mins | SC **Config** |
| Automation script **code version** | Airtable **Automation editor** (+ GitHub when aligned) |
| Automation Name / Status / Code **labels** | SC **Automations** table (those three columns only) |
| Email handoff queue (pre-send) | SC **Email Handoff Queue** |
| Communication delivery records | Hub **Messages** / **Deliveries** |
| Communication HTML templates | Hub repo React Email (`emails/`) |
| Template catalog metadata | Hub **Templates** |
| Test allowlist / suppressions | Hub **Test Allowlist** / **Suppressions** |
| Sent?/Sent On on SC sources | Hub writeback after successful send (configured types) |
| Public website content/UI | SC repo `web/` on Vercel |
| Upload orchestration | Make upload scenarios + Lambda (not email) |
| Live ops overlays / pending pastes | `docs/CURRENT-TRUTH.md` |
| Release status narrative | `docs/SHOOTING_CHALLENGE_COMPLETION_MASTER.md` |
| Future work IDs | `docs/127-SI-MASTER-FUTURE-WORK-LIST.md` + `MASTER_REMAINING_WORK_LIST.md` |

When documents disagree with live Airtable/Vercel/Resend evidence, **live systems win** and documentation must be updated.
