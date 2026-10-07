# 06 — Operations, Data Integrity, Administration, Season Lifecycle, and the Ideas Backlog

**Scope of this file:** the operational and administrative capability surface of the legacy `127-si-shooting-challenge` platform, plus the full backlog of planned, deferred, and rejected ideas. Companion files in this inventory cover intake/submissions, homework/video, progression/achievements, communications/Zoom, and the web app; those are referenced only where an operational concern touches them. **XP point amounts are intentionally not re-documented here.**

**Source of truth for this research:** the repository at `/workspace` (`Schmidt127/127-si-shooting-challenge`). No live Airtable, Make, Hub, or Vercel state was consulted. Where the repo says a thing was "built but not installed" or "designed only," that is recorded as such.

**Headline state (per `docs/production-architecture/FROZEN_BASELINE_AND_FUTURE_WORK.md` and `docs/production-architecture/2027-SEASON-PRODUCTION-CONFIGURATION.md`):**

| Fact | Value |
|---|---|
| Airtable base (Production, the only environment) | `appn84sqPw03zEbTT` — "127SI - SHOOTING CHALLENGE GAME - NEW 5_1_2026" |
| DEV base | `appTetnuCZlCZdTCT` **retired 2026-08-19**; platform is "Production-only operation" (`docs/ENGINEERING_CONSTITUTION.md` §2) |
| Tables / fields / links (snapshot 2026-09-05) | 35 tables · 1,375 fields · 174 link fields |
| Airtable automations | **50 / 50** — hard per-base cap reached |
| Frozen pre-migration baselines | SC `c0a7eba0d62e9582a259eb6ec180745e7d58251c` · Hub `4485af3b6d89c80f2166eab09df38cc1c788b87f` (freeze 2026-09-15) |
| Current season posture | 2027 Program Instance `Shooting Challenge \| 2026-2027` (`rec5mEM0YPqPqq0hZ`) status **Registering**; registration opens 2027-03-01; challenge window 2027-05-01 → 2027-06-30; Fillout Registration + Daily Submissions **OFF** |
| Email plane | Producers → `Email Handoff Queue` → Automation 079 → Communications Hub (`127-communication-hub`, base `appYG1t5DBRimHBCT`) → Resend; Make/Gmail retired |
| Governance verdict | "ECOSYSTEM PRODUCTION CLEAN — CURRENT ARCHITECTURE CLOSED"; required current production work: **NONE**; migration **not begun** |

---

## 1. Complete Airtable table inventory (35 tables)

Source: `airtable/schema/snapshots/prod-20260905-fut002-batch2/schema_doc_appn84sqPw03zEbTT_20260905_062812.md` (table `description:` lines where present; role classification is mine, informed by `docs/next-wave/data-model/CANONICAL-TABLE-MAP.md` and `docs/next-wave/data-model/FIELD-OWNERSHIP-MATRIX.md`).

Role key: **Transactional** (per-athlete/per-event rows that grow during a season) · **Config** (season-tunable rules) · **Content** (curriculum/media) · **Ops** (operator/engineering support) · **Reference** (slow-changing lookups) · **Legacy** (retained, not authoritative).

| # | Table | Fields / links | One-line purpose | Role | Notes for new platform |
|---|---|---|---|---|---|
| 1 | **Automations** | 15 / 0 | Inventory of Airtable automations: Name, Status (Live/Off/Legacy), Automation Code, Sections 01–11/90/99, trigger type/table/view, action summary. | Ops / **Legacy** | Authority for `Name`/`Status`/`Automation Code` **only** (Mike refresh 2026-08-20). **Not** a version authority — the published Automation editor is (`docs/AUTOMATION_VERSION_INVENTORY.md` banner). |
| 2 | **Enrollments** | 140 / 23 | "Primary operating table for athlete participation records" — one athlete × one Program Instance / school year. Hub for level, gates, XP totals, grade band, parent emails, `Active?`. | Transactional (hub) | 75+ computed fields; `Enrollment Key = {Athlete ID}\|{School Year}` formula. `Active?` is the sandbox/visibility gate (see §7). |
| 3 | **Athletes** | 11 / 2 | "Core athlete/person table" — identity across seasons. | Transactional (identity) | Athlete = person; Enrollment = Athlete in one Program Instance (isolation rule, `tools/program-instance-isolation/README.md`). |
| 4 | **Submissions** | 116 / 12 | "Stores individual athlete shooting activity submissions" (daily shot logs from Fillout). | Transactional | `Count This Submission?`, `Duplicate Key`, week/enrollment assignment, reconciliation signature. |
| 5 | **Submission Assets** | 90 / 8 | "Operational asset table tied to submission records" — per-file rows (homework/video/headshot), upload pipeline state, S3 writeback, reviewer tokens. | Transactional | Asset Purpose / Slot; Upload Destination; `Reviewer Access Token`. |
| 6 | **XP Events** | 55 / 10 | "Event log table for XP-related activity" — append-only XP ledger with `Source Key`, `Active?`, `Duplicate - Remove`. | Transactional (ledger) | One source record → one XP Event. Never edit; adjust by new rows. |
| 7 | **Athlete Achievement Unlocks** | 35 / 6 | "Transaction table for earned achievement unlocks" (Perfect Week, Shot Milestones; legacy streak rows archived). | Transactional | `Milestone Source Key`; Pending→Awarded lifecycle (059). |
| 8 | **Streak Occurrences** | 22 / 4 | "Tracks each individual streak milestone earned" — one row per block × threshold. | Transactional | Rebuilt by 053; XP by 054. |
| 9 | **Weekly Athlete Summary** (WAS) | 108 / 9 | "Summary table for one athlete enrollment in one challenge week" — weekly rollups, goal, homework links, weekly email package + send state. | Transactional (summary) | `Summary Key = {Enrollment Key}\|{Week Key}`; no atomic uniqueness → duplicate WAS risk (see §7). |
| 10 | **Target Goal Shots** | 9 / 4 | "Reference table for target shot-goal definitions" by grade band / season. | Config | Linked to WAS by 032; Goal Met Date backfill (SC-163). |
| 11 | **Grade Bands** | 17 / 7 | "Reference table for grade-band definitions" (min/max grade, label, `Active?`). | Config | Rename-safety problem (C-021). |
| 12 | **Achievements** | 23 / 3 | "Reference table for achievement definitions" (streak lengths, Perfect Week, milestones) linked to XP Reward Rules. | Config | |
| 13 | **Homework Completions** | 86 / 11 | "Stores completion records for athlete homework assignments" — one row per athlete × assignment; review state, feedback email state, XP reconciliation signature. | Transactional | HC identity audited in `docs/next-wave/data-model/HC-IDENTITY-AUDIT.md`. |
| 14 | **Weeks** | 21 / 12 | "Calendar anchor table for weekly challenge periods" — Sunday–Saturday, `America/Denver` Start/End dateTime, `Week Key = RECORD_ID()`, `Counts Toward Challenge?`, reconciliation signatures. | Config (calendar) | **Excluded from disposable-data mode.** Three identities: Week Key (RID), Week Code (`YYYY-YYYY\|Week N`), Week Name (label). |
| 15 | **Program Instance - Sync** | 39 / 6 | "Synced source table for program instance records" — one row per season/program (e.g. `Shooting Challenge \| 2026-2027`), Status (Registering/…), challenge window, Active School Year → Config. | Config (season) | Synced from an upstream base. Isolation scope for all progress. |
| 16 | **School - Synced** | 31 / 1 | "Synced source table for school records." | Reference | Synced. |
| 17 | **Level Gate Rules** | 16 / 3 | "Define and manage customizable progression requirements for each Level by year or rule set" — minimum submissions/homework/videos/zoom/streak days, `Gate Enabled?`, `Version Active?`. | Config | Layer-2 tuning target for 2026–27 (`docs/v2/season-configuration-design.md`). |
| 18 | **Levels** | 19 / 5 | "Reference table for level definitions and progression order" — names, cumulative XP thresholds, `Active?`. | Config | |
| 19 | **Shot Milestones** | 16 / 3 | "Reference table for shot milestone definitions." | Config | |
| 20 | **Homework Library** (a.k.a. `FBC Curriculum - SYNC`) | 29 / 3 | "Active homework / curriculum source table." | Content | Synced curriculum; presentation-name problem (C-022). |
| 21 | **Program Homework Assignments** (PHA) | 25 / 8 | "MVP junction: reusable … assignment scheduled for one Program Instance + Week + Grade Band + Slot." | Config / Content | 20 active PHA rows in 2027 sim incl. Week 9 × 2; FUT-049 removes PHA Grade Band. |
| 22 | **Video Feedback** | 50 / 5 | "Coach review tracks video asset feedback, approval, and XP awards." | Transactional | Coach work queue Interface (SC-166). |
| 23 | **Tutorials & Assets** | 15 / 0 | Canonical content catalog for tutorial videos/assets (migrated from legacy `Tutorials`, C-026). | Content | No description in base (schema health INFO). |
| 24 | **XP Reward Rules** | 9 / 1 | "Central hub to flexibly configure all XP award values and logic." | Config | Amounts documented elsewhere. |
| 25 | **Config** | 40 / 6 | "Configuration table for app-wide settings and control values" — one row per `Active School Year`; toggles: `HW Review Enabled?`, `Video Review Enabled?`, `Submission XP Active?`, `Detailed Stat Tracking Enabled?`, `Require Detailed Stats?`, `Challenge Week Count`, `Active XP Rule Set`, `Max Videos Per Submission`, `Perfect Week Video Minimum`, full **Zoom recording-makeup policy** (`Recording Path Enabled?`, `Recording Makeup Enabled?`, `Recording Makeup Counts for Perfect Week?`, `Recording Gives Full Zoom Gate Credit?`, `Recording Quiz Requires Coach Approval?`, `Zoom Recording Deadline Mode`, `Zoom Recording Makeup Window Days`, `Zoom Recording XP Percent of Live`, `Recording Approval Email Enabled?/Template Key/Timing`), Google Drive root, `File Naming Pattern`. | Config (global) | Several toggles have **no automation consumers** (`docs/next-wave/config-selection/CONFIG-CONSUMER-INVENTORY.md`). Season-launch fields proposed but not added (§2). |
| 26 | **Email Handoff Queue** | 23 / 0 | "Single outbound Communications Hub queue for all Shooting Challenge email types. Only Automation 079 may send these records to the Communications Hub." Handoff Key, Status, Event Type, Template Key, Payload/Recipients JSON, Hub Event ID, attempt/retry counters, `Test Mode?`. | Ops (outbox) | Transactional outbox pattern; **the** integration boundary to the Hub. |
| 27 | **Awards** | 29 / 1 | "Defines all reusable awards … including rules, categories, and settings." | Config / Content | `Public On Web` gate. |
| 28 | **Award Recipients** | 41 / 3 | "Tracks every actual award given to an athlete for each challenge." | Transactional (season close) | Close-out audits + gift-card cart summary. |
| 29 | **Final Reflection Quiz Submissions** | 55 / 2 | "Captures, auto-scores, and links athlete submissions for the Shooting Challenge quiz" (HW17 path via 067). | Transactional | Separate Fillout quiz path. |
| 30 | **Zoom Meetings** | 94 / 6 | "Centralize and manage all online video meetings with seamless participant tracking." | Transactional / Content | Recording URLs, week signature. |
| 31 | **Zoom Attendance** | 49 / 3 | Per-enrollment attendance / recording-credit rows (no base description). | Transactional | Live vs recording credit (101 / 117). |
| 32 | **Testing Scenarios** | 25 / 4 | "Engineering Test Framework (SC-001). Orchestration only — not a second XP/homework/email path." Run Test?, Dry Run?, Scenario Type, Expected/Actual Result, Pass/Fail Notes, links to Enrollment/Submission/HC/PHA. | Ops (QA) | Production-only by design (automation 115). |
| 33 | **Payment Transactions** | 9 / 1 | "Track Stripe payment writebacks linked to enrollments" — Stripe Payment ID, Fillout Submission ID, Actual Amount Paid, Coupon Code, Payment Status, Make Processed At. | Transactional (finance) | Writeback path validated, Make scenario **inactive** (FUT-003/FUT-053). |
| 34 | **Countries** | 7 / 1 | Address lookup (no description). | Reference | |
| 35 | **State** | 6 / 1 | Address lookup (no description). | Reference | |

**Legacy / retired tables not in the 2026-09-05 snapshot but referenced in docs:** `Tutorials` (migrated into Tutorials & Assets, C-026), a proposed `Tutorial Migration Review` table (preview only), and the never-built `Learning Activities` / `Program Category Settings` tables (ideas, §6).

**Schema health warnings worth carrying forward** (snapshot header): tables without descriptions (Tutorials & Assets, Zoom Attendance, Countries, State); heavy formula/lookup density on Enrollments/WAS/Submissions; duplicate "gate summary" formulas; Weeks text stubs that are "fake relationships" (`docs/next-wave/data-model/SAFE-MIGRATION-PLAN.md` M-03, M-05).

---

## 2. Season lifecycle operations

### 2.1 Lifecycle phases as the legacy platform ran them

| Phase | What happens | Key artifacts |
|---|---|---|
| **Pre-season / rollover** | Tag prior season; create new Program Instance; seed Weeks (Sunday–Saturday, Denver); create Config row for the school year; duplicate `Version Active?` Level Gate Rules set; tune Levels / XP Reward Rules / Achievements; publish Game Manual + web rules **before Day 1**; open Fillout registration; run readiness validators. | `docs/challenge-year/ANNUAL-ROLLOVER.md`, `docs/challenge-year/GO-LIVE-CHECKLIST.md`, `docs/shooting-challenge-v2-config-vs-code.md` §"2026–27 tuning workflow", `docs/v2/season-configuration-design.md`, `docs/v2/level-gate-rules-config-template.csv` |
| **Registration window** | Fillout registration → Enrollment intake automations (001–003) → optional Stripe/Fillout/Make payment writeback → Welcome email (078A). Early-bird week decision (MRW-L04). | `docs/production-architecture/2027-SEASON-PRODUCTION-CONFIGURATION.md`, `docs/next-wave/fillout/FILLOUT-FORM-INVENTORY.md` |
| **In-season weekly cadence** | Daily submissions → XP → WAS; Sunday-evening weekly maintenance checklist; weekly summary chain (118 → 072 → 119 → 074 historically; Hub path now); homework grading queue; video feedback queue; Zoom attendance; dry-run audit subset (Stages B/F/G/H). | `docs/checklists/weekly-maintenance-checklist.md`, `docs/next-wave/was-email/WEEKLY-EMAIL-RETRY-SOP.md`, `docs/production-architecture/OPERATIONS.md` |
| **Season close-out** | Final 090A–090G audit sweep; Award Recipients closeout; goal-conquer reconciliation; awards catalog quick check; gift-card cart summary (2025–26: **70 cards / $595**); final challenge summary email build; post-close hygiene list; field cleanup (Stage J). | `airtable/extension-scripts/audits/README.md` §"Season close-out order", `docs/close-out-considerations.md`, `docs/post-close-hygiene-2025-26.md`, `docs/airtable/stage-j-legacy-cleanup.md` |
| **Between seasons** | Platform modernization waves; schema snapshots; retire duplicate automations; docs reconciliation; frozen baseline. | `docs/v2-014-automation-modernization-roadmap.md`, `docs/production-architecture/FROZEN_BASELINE_AND_FUTURE_WORK.md` |

### 2.2 Challenge-Year Engine + Season Launch Control (built in repo; **not live-installed**)

Library `lib/challenge-year/` with CLI `tools/challenge-year/cli.js` (`tools/challenge-year/README.md`). Docs pack `docs/challenge-year/*`.

| Command / capability | Purpose |
|---|---|
| `generate-weeks` | Produce the Sunday–Saturday week set for a window in `America/Denver`; canonical label `YYYY-YYYY\|Week N`. |
| `validate-weeks` | Contract checks: contiguity, no overlap, Denver boundaries, `Counts Toward Challenge?` coherence. |
| `validate-enrollments` | Enrollment ↔ Program Instance ↔ Config coherence. |
| `validate-was` | WAS duplicate / orphan detection against Week + Enrollment. |
| `resolve-config` | Resolve which Config row applies for a Program Instance / year (also `lib/config-selection/`, `docs/next-wave/config-selection/CONFIG-SELECTION-CONTRACT.md`). |
| `preflight` | Rollover preflight bundle. |
| `manifest` + `launch-*` | Season Launch Control: build an activation manifest and drive lifecycle states **Draft → Validated → Staged → Activating → Live / Rolled Back**, with transition checks and a rollback checklist. |

Supporting read-only Scripting-extension previews (`airtable/extension-scripts/audits/preview-*.js`): `preview-challenge-year-config-relationships`, `-mismatches`, `-old-config-links`, `-was-duplicates`, `-weeks-missing`, `preview-cross-season-xp-risks`, `preview-season-launch-activation`, `preview-season-launch-rollback`, `preview-stale-email-flags`, `preview-submission-week-mismatches`.

Proposed (not added) Config fields for season control (`docs/challenge-year/SEASON-LAUNCH-CONTROL.md`, `docs/challenge-year/FIELD-OWNERSHIP.md`): `Challenge Year Status`, `Enrollment Open/Close`, `Test Mode?`, `Email Schedule Enabled?`, `XP Enabled?`, `Achievements Enabled?`, `Rollover State`. Dashboard view specs 1–6 in `docs/challenge-year/SEASON-LAUNCH-DASHBOARD-VIEWS.md`. Season-sensitive automation inventory and the "no hard-coded year/PI/record IDs" policy in `docs/challenge-year/AUTOMATION-SEASON-AUDIT.md`; offline enforcement by `tools/docs/audit-automation-hardcodes.mjs` (SC-034: flags "first Config record" selection and `new Date().getFullYear()` inference as unsafe business-rule hardcodes).

### 2.3 Enrollment-season validators (Python)

`tools/enrollment-season/`: `active_guard_contract.py`, `enrollment_validator.py`, `identity_matching.py`, `season_date_boundaries.py`, `weeks_seed_validator.py` (+ tests). Encodes the `Active?` guard contract, athlete identity matching rules used by 001, and week-seed validation.

### 2.4 Program Instance isolation

`tools/program-instance-isolation/README.md` — 8 warning categories ensuring all progress (Submissions, WAS, XP, HC, VF, Zoom, unlocks) is scoped via Enrollment → Program Instance, never via Athlete directly. This is the multi-year rule the new platform must keep (V2-013 "one base + Program Instance per program year").

### 2.5 Reliability Command Center (RCC) — built, views not installed

`lib/reliability-command-center/`, CLI `tools/reliability-command-center/cli.js`, docs `docs/reliability-command-center/{README,ARCHITECTURE,WORKFLOW-CHECKS,HEALTH-STATUS-CONTRACT,AIRTABLE-VIEW-SPEC,RETRY-POLICY,ROLLBACK}.md`.

| Element | Content |
|---|---|
| Operator questions | "Is this week's email safe to send?", "Which enrollments have XP without WAS?", "What is stuck?" |
| Workflow checkers | Enrollment, Submissions, XP, Homework, Levels, WAS/Weekly email — each emits coded `WorkflowIssue` records |
| Health status contract | 13 normalized statuses (e.g. healthy, degraded, blocked, stale, unknown…) |
| Retry classes | `automatically_retryable`, `retryable_after_correcting_data`, `manual_review_required`, `never_retry_already_completed` |
| MVP Airtable views (spec only) | Weekly Email Health; P0 Ready-but-incomplete; P0 Send-armed-not-Ready; P0 Sent/Make mismatch; XP by Source Key |
| Rollback | Never-dos: don't uncheck `Sent?` to retest, never delete XP/S3, never re-arm blindly |

Status: SC-147 "RCC views not installed (Built in Repository)" — accepted residual at launch (`docs/launch-certification/LAUNCH-DECISION.md`).

### 2.6 Season simulation harness

`tools/season_simulation/` (Python; `README.md`): writer-record simulation of a full season for a disposable enrollment. "Perfect Mike" run (SC-SEASON-SIM-PERFECT-202231Z) completed: **4,980 XP / 170 XP events** over the 2027-04-25 → 2027-06-30 window, 20 active PHA, gated formulas settled. Three-athlete run **SC-SEASON-SIM-001** is READY but not executed; requires exact authorization phrase `RUN 3-ATHLETE SEASON SIMULATION`. Late-homework policy and SC-168 note recorded in README.

### 2.7 Readiness validators and release tooling

| Tool | Purpose |
|---|---|
| `tools/validate-v2-release-readiness.js` | Offline docs/automation consistency validator (SCRIPT headers, CHANGELOG, index). |
| `tools/readiness/final_readiness_audit.py` | Three-base readiness audit (SC, Hub, upstream sync). |
| `tools/readiness/compare_live_vs_github_automations.py`, `extract_github_automation_versions.py` | Live-vs-repo version reconciliation. |
| `tools/readiness/live_transaction_audit.py` | Transactional record audit. |
| `tools/readiness/build_cleanup_manifest.py`, `execute_cleanup.py`, `*_comms_hub_cleanup*.py` | Manifest-driven cleanup with explicit execution step. |
| `tools/readiness/normalize_035_ascii_v17.py`, `proof_035_v17_executable_unchanged.py` | Script-body hygiene proofs (ASCII normalization without behavior change). |
| `tools/testing/` | Agent-4 QA suite, autonomous QA, SC-003 testing-views verifier (`verify_testing_views.mjs`), identity contract, E2E matrix, expected-vs-actual, production probe, orphan cleanup, weekly settlement checks. |
| `tools/airtable/` | Python schema exporter (`export_airtable_schema.py`), close-out award scripts, final email staging, `v2_prod_runbook/` safe operator CLI. |
| `tools/docs/` | `generate-work-list-section-g.mjs`, `reconcile-future-work-list.mjs`, `extract-automation-triggers.mjs`, `audit-automation-hardcodes.mjs`, `sync-chatgpt-sources.ps1`. |
| `tools/make/` | Blueprint patchers for the upload engine (hash lookup). |
| `tools/tutorials-content/` | Tutorials content build. |

### 2.8 Emergency recovery runbook

`docs/recovery/emergency-recovery.md`: severity S1–S3; immediate steps Pause → Scope → Communicate → Preserve evidence; recovery workflow `Pause → Diagnose (audit dry-run) → Fix root cause (GitHub → deploy) → Backfill (CONFIRM_WRITE) → Re-run audit → Re-enable → CHANGELOG + incident note`. Notes that Airtable has **no full base rollback** — schema rollback is manual from snapshot notes.

---

## 3. Data-integrity tooling

### 3.1 Conventions (apply to every script)

Sources: `airtable/extension-scripts/audits/README.md`, `airtable/extension-scripts/safe-backfills/README.md`, `docs/v2/08-testing-standards.md`.

| Convention | Rule |
|---|---|
| Audit vs backfill | Audits are **read-only**, emit JSON summary with counts + sample record IDs, never delete. Backfills create/update only. |
| Dry-run default | Every backfill defaults to `DRY_RUN = true` / `previewOnly=true`. |
| Explicit confirm | `CONFIRM_WRITE = true` for writes; `CONFIRM_DELETE = true` (or `--confirm-delete`) for the few deleters; typed phrases for high-impact ops (`CONFIRM MERGE`, `APPROVE TRANSACTIONAL PURGE`, `RUN 3-ATHLETE SEASON SIMULATION`). |
| Batch limits | Typically 50 (25 for deletes); re-run until `remainingCount = 0`. |
| Dedupe keys | Same Source Key patterns as production automations. |
| Logging | Record IDs and before/after in output; CHANGELOG entry with date/scope/counts. |
| "Fix the audit, not the data" | If an audit flags valid rows under an evolved rule, update the audit (H-001 lesson: 090F false positives on multiple legitimate same-week milestones). |
| When **not** to backfill | Widespread live-automation logic bugs (fix automation first); suspected duplicate emails (fix scenario idempotency first); orphan completions with no file anywhere (manual). |

### 3.2 Idempotency and reconciliation primitives

| Primitive | Where | Behavior |
|---|---|---|
| **Source Key** on XP Events | `SUBMISSION_XP\|{subId}`, `HOMEWORK_XP\|{hcId}` (legacy `HOMEWORK_COMPLETION\|`), `STREAK_XP\|…` (legacy `STREAK_OCC*` migrated), `ZOOM_RECORDING_CREDIT\|…`, Milestone Source Key on unlocks; registry `docs/next-wave/automation-ownership/xp-source-key-registry.json` | One source record → one XP Event; "guard against stealing"; recheck before create (010 v10.14 closed a TOCTOU race, SC-167, with create+retry). |
| **Reconciliation signatures** | `Current Reconciliation Signature` on Submissions/HC; `Progression Last Queued/Reconciled Signature` on Enrollments; `Reconciliation Source Signature` and `Zoom XP Week Signature` on Weeks | Formula-computed hash of inputs; automations compare stored vs current to decide re-run; `initialize-homework-xp-reconciliation-signatures.js` seeds them. |
| **Duplicate - Remove** status | XP Events | Soft-exclude duplicates from rollups; `repair-final-090e-xp-rollup-duplicate-status.js` clears false positives. |
| **Single-writer ownership** | `docs/next-wave/automation-ownership/SINGLE-WRITER-OWNERSHIP-MATRIX.md`, `WAS-UNIQUENESS-CONTRACT.md`, `AUTOMATION-WRITER-INVENTORY.md` | Each field has one writer (e.g. Make owned `Weekly Email Sent?`; 074 only clears `Send to Make?`). |
| **Append-only XP** | engine contract `docs/v2/03-business-rules.md` §6.2 | Corrections are new rows (negative adjustments), never edits. |
| **Active?** on XP Events / unlocks / enrollments | | Soft deactivation instead of deletion. |

### 3.3 Audit catalog (`airtable/extension-scripts/audits/`)

Pipeline Stages A–J (stage → automations → audit → backfill):

| Stage | Focus | Audit script(s) |
|---|---|---|
| A | Submission intake | `audit-submission-pipeline-integrity.js` |
| B | Submission XP (010) | `audit-xp-vs-submissions.js` |
| C | WAS / orphan XP | `audit-orphan-xp-events.js`, `audit-xp-linkage-coverage.js` |
| D | Assets created (009) | `audit-submission-pipeline-integrity.js` |
| E | Homework upload | `audit-homework-completion-upload-edge-cases.js`, `audit-stuck-upload-processing.js` |
| F | Homework XP (065) | `audit-homework-pipeline-integrity.js`, `audit-homework-xp-pipeline-integrity.js` |
| G | Video upload | `audit-video-pipeline-integrity.js`, `audit-video-and-homework-attachment-linkage.js` |
| H | Video XP (114) | `audit-video-xp-pipeline-integrity.js` (+ `.test.js`) |
| I | Achievements / streaks | `audit-achievement-xp-pipeline-integrity.js`, `audit-pending-shot-milestone-unlocks.js` |
| J | Legacy cleanup | `audit-legacy-cleanup-candidates.js`, `audit-field-coverage-report.js` |

Final pre-close sweep (run in order): `audit-final-090a-submission-base-xp.js`, `090b-homework-xp`, `090c-streaks-milestones-perfect-week-xp`, `090d-video-zoom-xp`, `090e-xp-events-enrollment-totals`, `090f-athlete-achievement-unlocks-workflow`, `090g-weekly-summary-email-workflow`.

Season close-out: `audit-final-award-recipients-closeout.js` (+ `.source.js`), `audit-final-goal-conquer-reconciliation.js`, `audit-final-awards-catalog-quick.js`, `audit-final-awards-cart-summary.js`, `june29-award-recipients-snapshot-data.js`.

Package / targeted audits: `audit-pkg-036-progression-integrity.js` (error / warning / `formula_unsettled` / inaccessible classes), `audit-pkg-040-standings-integrity.js` (+ test; notes `Web - Leaderboard` view unobservable from scripting), `audit-c023-stage5-duplicate-consequences.js`, `audit-target-enrollment-full-integrity.js` (business rules for multiple same-day submissions, Duplicate Key, 007 flags), `audit-zoom-live-attendance-xp-lifecycle.js` (+ test), `audit-homework071-trigger-readiness.js`, `audit-homework17-reflection-quiz-pipeline.js`, `audit-counted-submission-xp-standings-reliability.js`, `audit-submission-asset-pipeline-duplicate-xp.js`, `audit-orphan-asset-homework-submission-repair-planner.js`, `audit-make-upload-engine-test-submission.js`.

### 3.4 Backfill / repair catalog (`airtable/extension-scripts/safe-backfills/`)

| Group | Scripts |
|---|---|
| Submission → XP → WAS linkage | `backfill-submission-pipeline-links.js`, `backfill-submission-xp-events.js`, `backfill-missing-weekly-summaries-and-xp-links.js`, `backfill-xp-event-weekly-summary-links.js` |
| Homework | `backfill-homework-completion-upload-status.js`, `-upload-edge-cases.js`, `-was-links.js`, `-orphan-resolve.js`, `backfill-homework17-completions-from-reflection-quiz.js`, `backfill-homework-xp-from-reviewed.js`, `dedupe-homework-xp-events.js`, `initialize-homework-xp-reconciliation-signatures.js`, `repair-homework17-retrigger-parent-email.js` |
| Video | `backfill-video-pipeline-links.js`, `backfill-video-xp-from-posted-feedback.js`, `repair-video-feedback-xp-link.js`, `repair-missing-reviewer-access-tokens.js`, `intake-manual-email-video-feedback-submission.js`, `fut-009-video-rename.js` |
| Zoom | `dedupe-zoom-meeting-xp-events.js` |
| Streaks / milestones | `backfill-legacy-streak-xp-week-and-was.js`, `backfill-legacy-streak-xp-source-keys.js`, `backfill-shot-milestone-xp-week-and-was.js`, `backfill-shot-milestone-unlock-mark-awarded.js`, `archive-legacy-streak-unlock-records.js` (one of the few deleters; 156 orphan rows removed 2026-06-24) |
| Linkage repairs (named incidents) | `repair-audit-linkage-full.js`, `repair-orphan-asset-submission-links.js`, `repair-audit-001…010-*.js` (per-athlete multi-asset writeback, stale upload error, shot-tracker credit), `repair-kimm-lyle-restore-excluded-submissions.js` |
| Final close | `repair-final-090e-xp-rollup-duplicate-status.js`, `repair-final-090f-unlock-week-from-source.js` (stub), `repair-final-090g-build-final-challenge-summary-email.js`, `backfill-goal-met-date.js` (SC-163) |
| Content | `migrate-tutorials-into-tutorials-and-assets.js` (+ tests), `merge-three-tutorials-possible-matches.js` |
| Storage | `fut-010-clear-intake-attachments.js` (delete-after-verify cleanup worker; Production dry-run 2026-08-30 → 0 eligible) |

Run order 1–16 and "Ready / DRY_RUN / Stub" status per script: `airtable/extension-scripts/safe-backfills/README.md` lines 55–87.

### 3.5 Automation inventory and version control

| Artifact | Role |
|---|---|
| `airtable/automations/shooting-challenge/*.js` | GitHub source of truth; SCRIPT + CONFIG header blocks; `AUTOMATION_SCRIPT_STANDARD.md`. |
| `docs/AUTOMATION_VERSION_INVENTORY.md` | Living inventory: script version, trigger, PROD evidence per automation; "Unknowns are intentional — do not invent live versions." |
| `docs/automation-index.md`, `airtable/schema/current/automation-trigger-map.md` | Lookup and trigger maps. |
| `docs/v2-014-automation-modernization-roadmap.md`, `docs/v2-014-wave-2a-classification.md` | Category A–F taxonomy (leave alone / V2 rewrite / merge / extension / external / retire), complexity scores, 46 scripts classified, ~12 slots recoverable. |
| `docs/audits/VERSION-AUDIT-CORRECTION-*.md` | Three-way (live / GitHub / inventory) alignment records. |
| Testing Scenarios table + automation 115 | Production-only Engineering Test Framework; orchestration only. |
| `docs/testing/views/TESTING-VIEWS-SPEC.json` + `tools/testing/verify_testing_views.mjs` | SC-003: eleven "Schmidt-only" testing views (Testing Scenarios, Submissions, XP Events, WAS, Assets, HC, VF, Unlocks, Enrollment, Seeded Weeks, Zoom Attendance). Rule: do **not** hide Schmidt from public standings. |

### 3.6 Rollback posture

- Scripts: redeploy last known-good commit (GitHub is authoritative).
- Data: never delete XP/S3; soft-deactivate; adjust via new rows; `docs/reliability-command-center/ROLLBACK.md` never-dos.
- Season: `docs/challenge-year/ROLLBACK-CHECKLIST.md` + `preview-season-launch-rollback.js`; pre-cutover baseline SHAs recorded.
- Schema: no base-level rollback in Airtable; snapshot-driven manual revert (`docs/recovery/emergency-recovery.md`).
- Weekly email: `docs/next-wave/was-email/WEEKLY-EMAIL-RETRY-SOP.md` response classes (success / timeout / malformed / retryable_http / client_error) and "never uncheck Sent? to retest."

---

## 4. Airtable Interfaces for coaches and admins

The repo documents Interfaces thinly (OMNI-first policy kept most in-base work out of GitHub). What is evidenced:

| Interface / page | Evidence | Purpose |
|---|---|---|
| **Homework Grading Queue** (`pag1ohNraczU0PgjM`) | `docs/deploy-checklists/SC-166-coach-work-queue-filters.md`, `docs/audits/SC-166-COACH-WORK-QUEUE-RULES-20260905.md` | Coach work queue; composite ACTIVE/COMPLETED filter rules over Homework Completion fields (field IDs recorded). |
| **Video Feedback Grading** (`pagK6dWwNon0Vv6MQ`) | same | Coach queue for Video Feedback review with equivalent ACTIVE/COMPLETED rules. |
| **Curriculum Hub submit authorization** | `docs/interfaces/curriculum-hub-submit-authorization.md` | `submitAuthorizationToken` contract between web Curriculum Hub and Airtable (athlete-facing, admin-governed). |
| **Season Launch dashboard views 1–6** | `docs/challenge-year/SEASON-LAUNCH-DASHBOARD-VIEWS.md` | Designed, not installed. |
| **RCC MVP views** | `docs/reliability-command-center/AIRTABLE-VIEW-SPEC.md` | Designed, not installed (SC-147). |
| **Testing views (section `02 TESTING`)** | `docs/testing/views/*` | Installed/verified via OMNI prompt; operator checklist. |
| **Automation trigger views** | e.g. `Automation - 003 - Grade Band Refresh Needed`, `042 - Needs Level Assignment`, `Web - Leaderboard` | Views double as automation triggers and web data sources (`web/docs/airtable-views.md`). |
| **SC-116 admin roadmap** | MFWL Section F | Admin console roadmap item (status in list). |

Takeaway: the legacy platform never had a unified admin console; "administration" was Airtable grid views + two grading Interfaces + Scripting-extension audits + CLI tools + Markdown runbooks.

---

## 5. Governance artifacts

| Artifact | Path | Essence |
|---|---|---|
| Engineering Constitution | `docs/ENGINEERING_CONSTITUTION.md` | GitHub is source of truth; Airtable is the *running* copy; production-only; 7-step promotion; docs are part of the deliverable. |
| AI development standards | `docs/v2/04-ai-development-standards.md` | Mike / ChatGPT / Cursor / OMNI role split; Task Classification + Workspace Check on every task; OMNI-first for in-Airtable work; "official promotion documentation required." |
| Operating mode | `docs/CHATGPT-PROJECT-OPERATING-MODE.md`, `.cursor/rules/project-operating-mode.mdc` | High autonomy; disposable-data mode (transactional test records only; **Weeks excluded**); Mike approval for schema/paste/deletion of tables, config, evidence, payments, secrets, S3. |
| Deploy checklists | `docs/deploy-checklists/` (**261 files**) + `_PROMOTION-STEPS-TEMPLATE.md` | Every production paste/activation has a promotion doc with rollback; PKG-/SC-/FUT- packets. |
| Operator worksheets | `docs/operator-worksheets/PKG-007/034/037/039/040-*.md` | Mike-only evidence capture (SHAs, run IDs, record values); "repository source is not installed-version proof." |
| CHANGELOG | `CHANGELOG.md` (`### Airtable` / `### Web` / `### Make`) | Production-impacting changes. |
| Four-agent workflow | `docs/agent-runs/00-START-HERE.md`, `CONTROL.json`, `.cursor/rules/four-agent-workflow.mdc` | Lead / Implementation / Testing / Research roles; workers never merge; Mike approves `master`; no destructive git; CONTROL.json over chat history. |
| Launch certification pack (historical) | `docs/launch-certification/*` | 2026-07-25 "READY WITH NON-BLOCKING FOLLOW-UPS"; certified release commit vs verified tip vs current tip distinction. |
| Production architecture pack | `docs/production-architecture/*` (`SOURCE_OF_TRUTH`, `AUTHORITY-MAP` link, `OPERATIONS`, `DEPLOYMENT`, `COMMUNICATIONS`, `FROZEN_BASELINE_AND_FUTURE_WORK`) | Post-FUT-058 authoritative pack; documentation hierarchy (current truth → frozen baseline → ops → optional cleanup → future product → future migration → legacy). |
| Known issues | `docs/KNOWN_ISSUES.md` (K-H1…K-L6 + accepted exceptions), `docs/known-issues.md` pointer | See §7. |
| PROD operating mode (historical) | `docs/SHOOTING_CHALLENGE_PROD_OPERATING_MODE.md` | Earlier PROD-first rules superseded by constitution. |
| Decisions | `docs/decisions/MRW-B05-xp-activity-wip-resolution.md` | Example ADR (ABANDON PR #240). |
| Security | `docs/SECURITY-AND-SENSITIVE-FILES.md`, `docs/REPOSITORY-INTEGRITY-AUDIT.md`, SC-145 | Never commit tokens/webhooks; S3 private; secure video URL (`lib/secure-video-url.js`). |

The 18-point migration planning checklist the old repo demands before any new platform build is in `docs/production-architecture/FROZEN_BASELINE_AND_FUTURE_WORK.md` §F (discovery, architecture, source-of-truth, data model, dev workflow, repo strategy, environments, authN/Z, secrets, integration inventory, AI-agent access, testing, deployment, observability, backup/recovery, migration, rollback, docs).

---

## 6. IDEAS BACKLOG — planned, deferred, and rejected

Primary sources: `docs/127-SI-MASTER-FUTURE-WORK-LIST.md` (MFWL; Sections A–G), `MASTER_REMAINING_WORK_LIST.md` (MRW-L items), `docs/roadmap/_archive/MASTER_REMAINING_WORK_LIST-pre-20260914.md` (MRW-A…I), `docs/roadmap/planning/FUT-049…057*.md`, `docs/next-wave/**`, `docs/close-out-considerations.md` (C-items), `docs/xp-motivation-analysis-2025-26.md`, `docs/platform-config-improvements.md`, `docs/_generated-work-list-section-g.md`.

Section G snapshot (MFWL): **77 tracked items — 63 complete, 3 in progress, 1 ready, 10 deferred.** Status words below are as recorded in the repo.

### 6.1 Platform architecture and multi-program

| ID | Title | Status | One-liner |
|---|---|---|---|
| SC-143 | Multi-challenge platform | Deferred / planning constraint | Shared infra (identity, enrollment, challenge/session model, XP Events + buckets, levels, achievements, rewards, comms, reporting, admin) for Shooting **and** Dribble; primary metric differs (shots vs dribble minutes); not simultaneous. |
| FUT-050 | Dribble Challenge product options | Decision only | Option B (own base) recommended near-term; shared-platform requirement governs the future. |
| V2-013 | Program Instance multi-year model | Adopted direction (one base + PI per year) | Replaced "archive + clone base per season." |
| FUT-058 | Ecosystem production-clean closeout | COMPLETE — CLOSED | Produced frozen baseline + migration checklist; forbids reopening. |
| V2-014 | Automation modernization (waves 2b+) | Planning complete; implementation not started | Rewrite/merge/retire by Category A–F; recover ~12 slots; Lambda deferred. |
| SC-034 / V2-002 | Config-over-code hardcode elimination | Audit built | Remove first-Config-record and calendar-year inference from scripts. |
| C-021 | Grade bands propagate from Configuration | Open | Match by Grade Band **link**, not string parsing (072's `normalizeGradeBandForRule()` hardcodes `K2/34/56/78/912`). |
| C-022 | Presentation fields | Open | Explicit public labels (`Public Assignment Name`, `Week Label - Public`) instead of primary/formula strings in emails. |
| C-018 | Intake vs run calendars | Open | Separate registration calendar from challenge run calendar. |
| C-019 / C-023 | Content hash / dedupe | Open | Content hash on assets; duplicate consequence audit. |
| C-024 | Dedupe keys hardening | Open | Harden HC key (M-06 additive RID-based formula). |
| FUT-051 | Unused-field cleanup program | Deferred (future data cleanup) | hide → observe → archive → delete; Meta API cannot delete fields. |
| FUT-049 | Remove PHA Grade Band | Planned (9-step migration) | Enrollment.Grade Band becomes sole authority. |
| SC-100 | Attachment / Google Drive retirement | Deferred | Retire Drive paths after S3. |
| FUT-040 | Automatic S3 migration orchestrator | Brief ready | discover → copy → verify → writeback → delete attachment for homework, video, registration headshots; never delete S3; never public bucket. |
| FUT-009 / FUT-007 | AWS storage structure + naming contract; corrected-video workflow | Brief ready / partially built (`lib/aws-media-naming`, `fut-009-video-rename.js`) | Deterministic S3 keys; HEADSHOT naming. |
| FUT-010 | Intake attachment cleanup worker | Built; 0 eligible in dry-run | Delete-after-verify stage only. |
| SC-144 | Softr flag rename | Complete/obsolete | Softr retired. |
| SC-145 | Repo security hardening | Complete | |
| MRW-I11 | Branch protection | Open (archive) | |

### 6.2 Season operations and admin tooling

| ID | Title | Status | One-liner |
|---|---|---|---|
| SC-032 | Season Launch Control | Built in repo; not live-installed | Lifecycle states + manifest + dashboard views. |
| SC-147 | Reliability Command Center views | Built in repo; views not installed | Weekly email health + P0 views + XP by Source Key. |
| SC-116 | Admin roadmap | Listed | Unified admin tooling. |
| SC-033 | Feature switches | Listed | Global on/off switches (precursor to FUT-038). |
| FUT-038 | Global category on/off per program instance | Brief ready; Mike decision pending (Options A Config / B Program Instance / C new table) | Disable submissions/homework/video/zoom/streaks/achievements/milestones per season without breaking gates or G.O.A.T. reachability. |
| C-010 | `Active?` guard on all automations | Partially done (C010 install doc) | Every script checks enrollment `Active?`. |
| C-011 | Automatic weekly email schedule | Done via 118/119 | |
| C-012 | Stage K audit | Open | Next audit stage after J. |
| V2-011 | Audit pack | Open | Season audit package. |
| V2-012 / SC-SEASON-SIM-001 | Dry-run season / three-athlete simulation | READY, not executed | Run-gated by exact phrase. |
| C-020 / SC-001 | Engineering Test Framework (Testing Scenarios) | Script paused; table live | "Testing Scenario Library" explicitly **do not build now**. |
| SC-003 | Testing views | Complete | |
| SC-062 | Siblings / household | Listed | Household modeling (feeds FUT-057). |
| FUT-057 | Family private profile | Planned | Accordion household profile, household authZ, field visibility matrix, view-only contacts v1. |
| C-017 | (ops watchlist item) | Open | See `docs/close-out-considerations.md`. |
| MRW-L01 | Tier-1 paste/verify queue | Active | Remaining automation pastes + verification. |
| MRW-L04 | Early-bird activation decision | Mike decision | 2026–27 early-bird week (decided "yes" 2026-08-27 in principle). |
| H-001…H-006 | Post-close hygiene 2025–26 | Mixed | 090F false positives, 066 template, award scope mismatch (49 rows), thanks-for-playing duplicate bucket, weekly-email stats 92/293/48/23/1, Conquered Goal Date lookup. |
| K-… | Known issues list | Accepted exceptions | See §7. |

### 6.3 Payments and registration

| ID | Title | Status | One-liner |
|---|---|---|---|
| FUT-003 / MRW-L02 | Stripe/Fillout/Make payment writeback | Paid path validated; Make scenario inactive | Payment Transactions table in place. |
| FUT-053 | Stripe coupons / 100% discounts | Deferred | Idempotency on `event.id` / `payment_intent`; staff reporting. |
| SC-146 | Reopen Fillout intake | Mike UI action | Registration opens 2027-03-01. |
| FUT-039 | Fillout branding + copy pack | Delivered (theme CSS, selectors, copy) | |
| FUT-029 | Hybrid Fillout homework / grade-band homework platform | Deferred | Typed responses, multiple choice, photo/doc/video uploads per grade band. |
| FUT-048 | (deferred item) | Deferred | Listed in MRW deferred bucket with FUT-029. |

### 6.4 Progression, motivation, and game design (ideas — amounts excluded)

| ID / source | Idea | Status | One-liner |
|---|---|---|---|
| V2 locked decision 2026-07-03 | **One ladder, spread gates early, communicate before Day 1** | Adopted | No dual-track for 2026–27; gates tuned in Level Gate Rules; "numbers later." |
| xp-motivation Option A | Parallel ranks (Shooter Level + Program Honors) | **Not adopted** (historical brainstorm) | Two progress stories; no gate blocking on shooter level. |
| Option B | Single ladder with gated "★" prestige suffix | Not adopted | Levels XP-only; star when program checklist met. |
| Option C | XP multiplier lane | Not adopted | Small persistent multiplier for breadth. |
| Option D | Season quests / Quest Board | Not adopted | Optional weekly quests with separate leaderboard. |
| C-014 / SC-082 | Streak economics + gate tuning | Decision recorded | Streak rewards re-earnable (Mike 2026-08-27); break-vs-hold incentive review. |
| V2-005/006/007 | Gate / XP / level tuning passes | Open | Q1 2027 config tuning. |
| xp-motivation §"Weekly email additions" | Level progress block + next gate item + manual link in every weekly email | Idea | Low production cost. |
| xp-motivation §"July tasks" | "I read the rules" acknowledgement before first submission | Idea | Registration/Week 0 automation. |
| Priority 4 | Within-day marginal shooting incentive / weekly thresholds promotion | Idea | Weekly threshold XP barely fired in 2025–26. |
| Mike decision 2026-08-27 | Recorded Zoom = no Perfect Week, counts for gates, partial XP | Adopted | Encoded in Config recording-makeup toggles. |
| SC-018/019/020 | Learning Activities catalog | Deferred (PKG-005) | Generalize homework into typed learning activities; schema + routing contract in `docs/next-wave/homework-pipeline/LEARNING-ACTIVITIES-SCHEMA.md`, `LEARNING-ACTIVITY-ROUTING-CONTRACT.md`. |
| FUT-055 | Interactive Curriculum Hub | Planned | One XP path; shadow → dual-run → cutover. |
| C-009 | HW17 quiz as normal file path | Partial (067) | |
| MRW-I02 / I03 | Recording XP architecture; Video XP 1-vs-25 question | Decided / open | |

### 6.5 Communications and content (operational angle only)

| ID | Title | Status | One-liner |
|---|---|---|---|
| V2-008 / SC-109 | Game Manual generated from config | Complete (SC-109) | |
| FUT-054 / MRW-L03 / FUT-026 | Player Manual + Game Manual Addendum | Planned | Outlines + change control. |
| V2-009 | Rules hub on web | Open | |
| V2-010 | Pre-season comms plan | Open | |
| C-027 / MRW-H08 | Major-event notifications | Open | Level-up / achievement notifications. |
| MRW-H02 / H03 | Award emailer; accomplishment emails | Open | |
| FUT-056 | Welcome email in React Email | Planned | |
| C-025-EMAIL / 117 | Zoom recording approval email | Live v2.1 (117f deferred) | |
| V2-014b / EMC | Email migration to Hub | Done (Hub live) | |
| SC-131/132 | Media kits | Complete | `media/`, `docs/media-kits.md`. |
| Optional/deferred | SMS / Twilio | Deferred | |
| Optional/deferred | Extra Curriculum lessons; cosmetic; orchestration | Deferred | |
| Naming decisions (Mike 2026-08-27) | "Jr. Referee Clinic", "Youth Programs" / "Coach Tools", "State Rankings" | Adopted | Cross-program nav naming. |
| FUT-041/042/043/044/046 | Email/card styling items | COMPLETE | |

### 6.6 Awards and recognition

| ID | Title | Status | One-liner |
|---|---|---|---|
| FUT-004 / FUT-052 | Replace Tremendous | Option B chosen in planning | Hub/Resend award email + staff fulfillment. |
| C-028 | Tremendous production API | **Rejected** | Section E. |
| SC-127/128/129 | Awards cleanup | Complete | Catalog + recipients + public-on-web gate. |
| SC-163 | Goal Met Date backfill | Ready | |
| H-003 | Award scope mismatch (49 rows) | Hygiene | |
| Close-out tooling | Gift-card cart summary, conquered-goal reconciliation, catalog quick check | Built | |

### 6.7 Testing and quality

| ID | Title | Status |
|---|---|---|
| SC-004 Schmidt identity contract; SC-005 E2E matrix; SC-006 expected-vs-actual; SC-ATHLETE-WF-001 athlete workflow QA; SC-PW-E2E Perfect Week E2E; weekly settlement checks | Complete | `tools/testing/README.md`, `docs/testing/*` |
| SC-007/008 reliability runbook; TEST-RELIABILITY-PROGRAM-20260908 | Complete | |
| Agent-4 QC coverage matrix, Live/Test email regression | Complete | `docs/testing/agent4-qc/` |

### 6.8 Rejected directions (MFWL Section E) and why

| Rejected idea | Reason recorded |
|---|---|
| Public S3 bucket | Security policy — assets stay private behind authorized links (`lib/secure-video-url.js`). |
| Tremendous production API (C-028) | Replaced by Hub/Resend award email + staff fulfillment (FUT-052). |
| Duplicate SEO pages | Content duplication harms SEO; single canonical pages. |
| One large redesign prompt | Design work must be incremental and reviewable. |
| HW1/HW2 slot identity as homework identity | Slots are positions, not assignment identity (`docs/next-wave/homework-pipeline/FLEXIBLE-HW1-HW2-SLOT-FOLLOWUP.md`). |
| Dual-track progression for 2026–27 | Communication + spread gates first; revisit only if friction remains. |
| Separate Airtable base per season (archive + clone) | Superseded by V2-013 one base + Program Instance. |
| GitHub fork per season | Tag `season-2025-26-final`; continue on `master`. |
| Lambda now (V2-014) | Deferred until a need the current stack cannot meet. |
| Testing Scenario Library | "Do not build now." |
| Deleting Airtable fields during closeout (FUT-058) | No field deletes from governance tasks; FUT-051 owns cleanup later. |
| Changing live config mid-season | 2025–26 lesson; requires documented migration + family notice. |

---

## 7. Known issues and lessons learned (operational)

| Theme | Detail | Where documented |
|---|---|---|
| **Automation cap (50/50)** | Base hit Airtable's hard cap; every new behavior required retiring or merging something (012 deleted; 112 OFF; 043 retire candidate; 006 retired). V2-014 estimates ~12 slots recoverable. New platform should not inherit a slot economy. | `docs/v2-014-automation-modernization-roadmap.md`, `docs/AUTOMATION_VERSION_INVENTORY.md` |
| **Formula lag / settlement** | Rollups and formulas settle asynchronously; audits had to add `formula_unsettled` classes and "settlement" waits; season simulation gated on formula settlement. | `audit-pkg-036-progression-integrity.js` header, `tools/season_simulation/README.md`, `docs/testing/weekly-settlement/` |
| **No atomic uniqueness** | Airtable cannot enforce unique keys → duplicate XP Events (TOCTOU in 010, fixed v10.14 with create+retry), duplicate WAS (bounded-concurrency residual; `WAS-UNIQUENESS-CONTRACT.md`), duplicate unlocks. Mitigated by Source Keys, recheck-before-create, `Duplicate - Remove`, dedupe backfills. | `docs/next-wave/automation-ownership/WAS-UNIQUENESS-CONTRACT.md`, `docs/next-wave/data-model/UNIQUE-KEY-AUDIT.md` |
| **Trigger re-entry / loops** | Scripts that write fields matching their own trigger condition re-fire; "no script writing fields that re-trigger same condition"; `Send to Make Trigger` transient flags; 059 trigger rework (SC-159). | `docs/recovery/emergency-recovery.md`, `docs/v2/AUTOMATION_059_TRIGGER_RESOLUTION.md` |
| **Timezone pitfalls** | Weeks are `America/Denver` dateTime; raw `new Date("M/D/YYYY")` is wrong; use date-key helpers (005/034); submission week mismatches audited. | `.cursor/rules/airtable-automation-scripts.mdc`, `preview-submission-week-mismatches.js`, `docs/challenge-year/WEEK-CONTRACT.md` |
| **Automations table is not truth** | Obsolete ops inventory; only Name/Status/Code trusted; versions come from the published editor + GitHub headers. | `docs/AUTOMATION_VERSION_INVENTORY.md` banner |
| **Repo ≠ installed** | "Repository source is not installed-version proof"; operator worksheets capture live versions; three-way alignment audits. | `docs/operator-worksheets/*`, `docs/audits/VERSION-AUDIT-CORRECTION-*` |
| **Schema API limits** | Meta API returned 403 for schema export at times (fallback in-extension exporter); Meta API cannot delete fields; no base rollback. | `airtable/extension-scripts/schema/README.md`, `docs/roadmap/planning/FUT-051*.md`, `docs/recovery/emergency-recovery.md` |
| **Dual status fields** | Weekly email had `Weekly Email Sent?` + `Make Send Status` + `Weekly Summary Email Status` + two timestamps; single-writer attestation needed. | `docs/next-wave/data-model/SAFE-MIGRATION-PLAN.md` M-02 |
| **`Active?` gaps** | Several automations (010/031/065/053/072/076 historically) did not honor enrollment `Active?`, leaking test/sandbox rows into production paths. | `docs/close-out-considerations.md` `Active?` table, C-010 |
| **Mid-season rule introduction** | Gates/levels not fully configured in weeks 1–2 of 2025–26; homework requirement surfaced ~week 8; 61.5% zero homework; 16 of 21 athletes ≥1,000 XP gate-blocked. Lesson: config + manual live on Day 1. | `docs/xp-motivation-analysis-2025-26.md`, `docs/shooting-challenge-v2-master-direction.md` |
| **Hardcoded season context** | Scripts selecting the first Config record or inferring year from `Date.now()` break at rollover. | `tools/docs/audit-automation-hardcodes.mjs`, `docs/challenge-year/AUTOMATION-SEASON-AUDIT.md` |
| **Grade-band string matching** | Renaming bands breaks 072 and rule lookups. | `docs/platform-config-improvements.md` C-021 |
| **Email safety** | Allowlist / `testMode` discipline; "never blast real parents"; participant protection via Fillout OFF rather than testMode in 2027 posture. | `docs/production-architecture/OPERATIONS.md`, `2027-SEASON-PRODUCTION-CONFIGURATION.md` |
| **Leaderboard view unobservable** | Scripting extension cannot read a view's rendered state → standings audit approximates. | `audit-pkg-040-standings-integrity.js` |
| **Make/Gmail legacy** | Historical Make chain retained only as labeled legacy; keep Make email scheduling OFF. | `docs/production-architecture/FROZEN_BASELINE_AND_FUTURE_WORK.md` §B |
| **Accepted exceptions** | K-H1…K-L6 in `docs/KNOWN_ISSUES.md` (e.g. 066/054 installed-not-live-tested for latest versions; 117f deferred; Fillout daily OFF intentional). | `docs/KNOWN_ISSUES.md`, `docs/launch-certification/LAUNCH-DECISION.md` |

---

## 8. What the new platform should take from this domain (synthesis)

1. **First-class season/program-instance model with explicit lifecycle states** (Draft → Validated → Staged → Live → Closed → Archived) and a calendar contract (Sunday–Saturday, single timezone, canonical week codes) — the legacy platform designed this (SC-032) but never installed it.
2. **Database-enforced uniqueness and an append-only ledger** for XP/unlocks/WAS so Source Keys, recheck-before-create, `Duplicate - Remove`, and dedupe backfills become unnecessary.
3. **Config-over-code as a schema**: Levels, Level Gate Rules, XP Reward Rules, Achievements, Grade Bands, Target Goals, Config toggles — all versioned per season with "no mid-season edits without migration + notice." Add FUT-038 category on/off per program instance.
4. **An admin console** (the legacy system had none): work queues (homework/video grading), RCC-style health dashboards, weekly email health, stuck-item views, retry classes, and typed-phrase guards for destructive ops.
5. **Audit-first operations**: keep the Stages A–J mental model and 090 pre-close sweep as built-in integrity checks, with "fix the audit, not the data."
6. **Transactional outbox for all communications** (Email Handoff Queue → Hub) with single-writer send state and test-mode/allowlist posture.
7. **Close-out automation**: award recipients, goal-conquer reconciliation, gift-card cart, final season recap email, post-close hygiene list.
8. **Disposable test identities and production-only QA harness** (Testing Scenarios, Schmidt views) — but with a real staging environment this time, since the legacy platform lost its DEV base.
9. **Backlog carry-forward**: FUT-038, FUT-040/009, FUT-049, FUT-051, FUT-053, FUT-054, FUT-055, FUT-057, SC-143 shared challenge platform, Learning Activities, C-021/C-022 presentation and rename-safety, SC-SEASON-SIM-001.
