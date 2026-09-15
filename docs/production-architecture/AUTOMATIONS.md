# Automations — live Production inventory

**Status:** Authoritative presence inventory (FUT-058 · 2026-09-15)  
**Source:** Airtable MCP `list_automations` on `appn84sqPw03zEbTT`  
**Count:** **50** automations · **50 deployed** · **0 undeployed**  
**009 attestation:** Mike manually confirmed production-required and **deployed** using **v1.3 / SC-160** (2026-09-15). MCP re-read same day: `deploymentStatus=deployed`.

Script **body/version** authority remains the Automation editor (and GitHub when pasted). This list proves **presence and deploymentStatus**, not every version string.

Detailed narrative index: [`../automation-index.md`](../automation-index.md) (update overlays when MCP disagrees).

## ACTIVE (deployed)

| Code | Live Airtable name |
|------|--------------------|
| 001 | Enrollment Intake and Setup - Find or Create Athlete and Link Enrollment |
| 002 | Enrollment Intake and Setup - Assign Grade Band - Initial |
| 003 | Enrollment Intake and Setup - Assign Grade Band - If Grade Changes |
| 005 | Submission Intake and Asset Creation - Assign Week to Submission - Homework First |
| **009** | Create Submission Assets from Submission (**v1.3 / SC-160** — production-required) |
| 007a | Submission Intake and Asset Creation - Duplicate Checker for Submissions |
| 010 | Submission Intake and Asset Creation - Create XP Event from Submission |
| 013 | Submission Intake - Create or Link Video Feedback |
| 020 | Link or Create Homework Completion from Submission Asset |
| 021 | Set Attachment Upload Status |
| 022 | Sync Child Upload Writeback from Submission Asset |
| 023 | Assign Enrollment to Submission |
| 030 | Copy Enrollment Grade Band to Weekly Summary |
| 031 | Find or Create Weekly Athlete Summary from Submission |
| 032 | Link Challenge Goal Record to Weekly Athlete Summary |
| 033 | Assign Homework to Weekly Athlete Summary |
| 034 | Set Previous Week Helper Values |
| 035 | Create Weekly Threshold XP Events |
| 041 | Mark Enrollment for Level Recalculation |
| 042 | Assign Current and Next Level |
| 053 | Streak Occurrences - Rebuild and Upsert From Submissions |
| 054 | Streak Occurrences - Create or Repair Streak XP Event |
| 055 | Recalculate Current Shooting Streak from Submission |
| 056 | Refresh Current Shooting Streaks Daily |
| 057 | Calculate Perfect Week Eligibility |
| 058 | Create Perfect Week Unlock |
| 059 | Create XP Event from Achievement Unlock |
| 064 | Assign Base Homework XP |
| 065 | Create or Update Homework XP Event |
| 066 | Create Shot Milestone Unlocks |
| 067 | Link Reflection Quiz to Homework Completion |
| 070a | Send Homework Asset Payload to Make |
| 070b | Send Video Asset Payload to Make |
| 070c | Verify async video asset upload (**live name is the `.js` filename — rename cosmetic**) |
| 071 | Homework Feedback Hub handoff (filename still says Webhook) |
| 072 | Build Weekly Summary Email Package |
| 073 | Video Feedback parent Hub handoff |
| 074 | Create Weekly Summary Hub Handoff |
| 076 | Daily Submission Communications Hub Handoff |
| 078 | Mark Homework Parent Feedback Ready (native update; no script) |
| 078A | Enrollment → Create WELCOME Email Handoff |
| 079 | Send to Communications Hub |
| 101 | Award Meeting XP (live + recording credit) |
| 113 | Assign Base Video XP by Grade Band |
| 114 | Create or Update Video XP Event |
| 116 | Apply Asset Reuse Decision Consequences |
| 117 | Create Zoom Recording Approval Communications Hub Handoff |
| 118 | Schedule Weekly Summary Email Build |
| 119 | Schedule Weekly Summary Email Send |
| 120 | Automatic S3 Video Rename |

## UNDEPLOYED (present, OFF)

**None.** All 50 Production automations are deployed (MCP 2026-09-15 re-read after Mike 009 deploy).

**History:** 2026-09-12 overlay listed **005** and **009** as undeployed. Mid-audit 2026-09-15 MCP showed **005 deployed** / **009 undeployed**. Mike then deployed **009 v1.3 / SC-160** — current truth is **50/50**.

## DISABLED / LEGACY / ABSENT (do not restore)

| Code | Notes |
|------|-------|
| 006 | Retired — Has Video? formula / 057 counts |
| 007 | Replaced by **007a** |
| 008 | Replaced by **116** |
| 012 | Deleted — use **020** |
| 043 | Retired level-gate helper |
| 063 | Retired Grade Band copy on HC |
| 068 | Retired — **033** owns deferred WAS links; keep OFF if present |
| 075 | Retired welcome builder — use **078A** |
| 077 | Deleted — daily Make email retired |
| 111 | Deleted — **013** owns VF Grade Band |
| 112 | Must stay OFF — duplicate of **013** |
| 115 | ETF harness — repo only; not in current live 50 |
| 122 | Superseded by **066** Goal Met Date |
| Make 117f / Gmail weekly | Historical email only |

## REVIEW BEFORE DELETE (repo files / naming)

| Item | Reason |
|------|--------|
| Repo scripts for retired numbers (006, 075, 077, 111, …) | Historical audit archive — keep until FUT-051-style cleanup |
| `_superseded/`, `_design-alternatives/`, `drafts/` | Design history — not production |
| Live name `070c-…js` | Cosmetic rename only |
| Live names still saying “Webhook” / “Make” on Hub producers | Filename/legacy wording; delivery is Hub→Resend |
| Automation **120** deployed | FUT-009 rename — confirm intended ON vs “OFF until disposable test” docs |

## Communications Hub automations

MCP `list_automations` on `appYG1t5DBRimHBCT` returned **[]**. Delivery is via Hub Next.js (`/api/events/ingest`, `/api/deliveries/send`, Resend webhooks) — not Airtable automations.
