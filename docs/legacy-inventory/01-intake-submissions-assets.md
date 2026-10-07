# Legacy inventory 01 — Enrollment intake, Submissions, Submission Assets, Weeks/Program Instances, Testing framework

Source repo: `/workspace` (`127-si-shooting-challenge`). Read-only research; no live Airtable access. XP *amounts* intentionally omitted (documented separately).

Primary evidence:

- Scripts: `airtable/automations/shooting-challenge/{001,002,003,005,006,007,009,021,022,023,070a,070b,070c,115,116,120}*.js`
- Schema: `airtable/schema/snapshots/prod-20260905-fut002-batch2/schema_doc_appn84sqPw03zEbTT_20260905_062812.md` (PROD base `appn84sqPw03zEbTT`, 35 tables, 1375 fields)
- Docs: `docs/data-model.md`, `docs/upload-workflow-homework-video.md`, `docs/asset-storage-migration.md`, `docs/testing-and-intake-architecture.md`, `docs/challenge-year/*`, `docs/online-agents/enrollment-season/*`, `docs/automation-index.md`, `make/documentation/*`
- Tools: `tools/program-instance-isolation/`, `tools/season_simulation/`, `tools/enrollment-season/`, `tools/challenge-year/`

---

## 0. Architecture in one picture

```text
Fillout Registration form ──► Enrollments row
   001 find-or-create Athlete, link, Active?=true, block duplicate same-season enrollment
   002 assign Grade Band (initial)  ·  003 re-assign when Grade changes
   078A arm WELCOME handoff (Email Handoff Queue → 079 → Communications Hub → Resend)

Fillout Daily Submission form ──► Submissions row (Enrollment pre-linked when form carries Enrollment id)
   023 assign Enrollment (if missing)        021 Attachment Upload Status (No Files / Processing)
   005 assign Week (Activity Date, PI-scoped; validate Homework Name 1/2 = PHA)
   007 duplicate checker (Duplicate Key → Count It / Needs Review)
   009 one Submission Asset per attachment (HW1 / HW2 / VIDEO slots), Upload Status = Pending Link
         ├─ 020 Homework Completion link/create (homework assets)   ─► 070a → Make → Lambda → S3
         └─ 013 Video Feedback link/create (video assets)           ─► 070b → Make → Lambda → S3
                                                                       070c verifies async writeback, clears trigger
   022 copies Upload Status / URLs from Submission Asset → child (Homework Completion / Video Feedback)
   116 applies Asset Reuse Decision consequences (hash-duplicate review)
   120 FUT-009 S3 rename of a video object on coach request

Identity rule (tools/program-instance-isolation/README.md):
   Athlete = person · Enrollment = Athlete in one Program Instance · all progress scoped through Enrollment → Program Instance
```

Timezone everywhere: **America/Denver**. Activity Date is a date-only field; the scripts treat midnight-UTC values as the calendar day (`dateKeyFromDate` in 005).

---

## 1. Tables in this domain

### 1.1 Athletes (`Athletes`, 11 fields)

| Field | Type | Notes |
|---|---|---|
| Full Name | formula | primary |
| First Name / Last Name | text | identity components |
| Parent Email | email | denormalized; identity component |
| **Athlete Match Key** | formula | `LOWER(parent email)\|LOWER(first)\|LOWER(last)` — read by 001, never written |
| Athlete ID | formula | `"ATH-" & RECORD_ID()` |
| Active? | checkbox | 001 sets true on link |
| Register Date | date | |
| Enrollments | link | one Athlete → many Enrollments (one per season) |

No Parent/Family table exists; family = shared Parent Email (`docs/online-agents/enrollment-season/SIBLING-HANDLING-SPEC.md`).

### 1.2 Enrollments (140 fields) — the per-season athlete record

Grouped by role (full list in schema snapshot):

| Group | Fields |
|---|---|
| Identity / primary | `Full Athlete Name - Backward` (primary), Athlete (link), Athlete First Name, Athlete Last Name, **Enrollment Key** = `AthleteID\|School Year`, Athlete Match Key Lookup |
| Contact | Parent First/Last Name, Parent Email, **Parent Email - Cleaned** (regex formula), Parent Email Submitted, Athlete Email, **Athlete Email - Cleaned**, Parent Cell Number, Athlete Cell Number, Mailing Address Submitted + address parts, Gender, **Welcome Email To** (= parent cleaned, else athlete cleaned) |
| Season scope | **School Year** single-select [`2025-2026`, `2026-2027`, `2027-2028`, `2028-2029`], **Program Instance** (link → Program Instance - Sync), Registered At, Registration Source [`Fillout Registration`], `Registratioin Referrer` (sic) |
| Grade / band | **Grade** single-select [`Pre K`, `K`, `1`…`12`], **Grade Band** (link), Grade Band Label (lookup), **Grade Band (Auto Assign)**, **Last Grade Used for Grade Band**, **Grade Band Status** [Pending, Processing, Assigned, Error], Grade Band Assignment Status (text), **Grade Band Refresh Needed** (formula: Grade ≠ Last Grade Used → 1), Default Homework Tier lookup |
| School | School (link → School - Synced), School Name / Mascot lookups (used in public standings) |
| Status / guards | **Active?** (fail-closed; 001 sets false while processing, true on link), **Progress Processing Enabled?** (PPE; C-010 design), **Athlete Match Status** [Pending, Processing, Linked, Error, Skipped], **Level Recalc Needed?** |
| Files / naming | **Athlete Folder Name** = `Last_First_SchoolYear`, Athlete Headshot (attachment) |
| Payment | Price Paid to Stripe, Payment Transactions (link), Stripe Payment Id, Fillout Submission Id, Waiver (select) |
| Public web | Public Profile Enabled?, Public Profile Slug |
| Goals | Target Goal Shots (lookup via Grade Band), Goal Met?, Perfect Week Video Minimum (lookup from Config) |
| Reconciliation | Reconciliation Source Signature (+ Last Reconciled / Needs?) |
| Progress (owned elsewhere) | XP/Level/Streak/Gate rollups — see XP inventory |

Payment Transactions table (9 fields): Stripe Payment ID, Fillout Submission ID, Amount, Coupon, Payment Status, Enrollment link.

### 1.3 Grade Bands (17 fields)

| Field | Notes |
|---|---|
| Name (formula) | renders `K-2`, `3-4`, `5-6`, `7-8`, `9-12`, `PreK–K`, `Kindergarten`, `Grade N`, `Grades a–b` from Min/Max |
| **Min Grade / Max Grade** (number) | Pre K = -1, K = 0 |
| Sort Order | tie-break |
| **Default Homework Tier** select | Early Childhood, Primary, Elementary, Upper Elementary, Middle School, Underclassmen, Upperclassmen |
| Active? | inactive bands ignored by 002/003 |
| Total Shot Target (lookup from Target Goal Shots) | per-band season goal |
| Links | Enrollments, Target Goal Shots, Program Homework Assignments, XP Reward Rules, etc. |

Rule (SC-023): Grade Bands are the **linked source of truth**; scripts match by Min/Max range, never hard-coded band IDs.

### 1.4 Target Goal Shots (9 fields)

Target Label, **Total Shot Target**, Grade Band (link), Active?, **Goal Key** = `SHOT_GOAL|BAND|target`, Program Instance (link). Production example: 9–12 band = 12,000 shots/season (`tools/season_simulation/constants.py`). Downstream: WAS "Weekly Goal Shots Target" and Perfect Week daily minimum = `ceil(weeklyGoal/7)`.

### 1.5 Submissions (116 fields) — one row per daily log

| Group | Fields / formulas |
|---|---|
| Who | **Enrollment** (link), Athlete (link), Program Instance - Synced (link), Submission School Year, `Fillout Enrollment Id` / `Enrollment Record ID` (text bridge from the form) |
| When | **Activity Date** (date), **Activity Date - Time** single-select hourly `12:00 am`…`11:00 pm`, Submitted At (`CREATED_TIME()`), **Activity Date Is Future?** = `IF({Activity Date}, IF({Activity Date} > NOW(),1,0), BLANK())`, Activity Date Key (UTC `YYYY-MM-DD`), **Submitted Same Day?** (Denver day of Submitted At vs Activity Date; has a gated Perfect-Week test path), **Perfect Week Grace Eligible?** (Activity Date ≤ TODAY() and within 48 h grace, or `Perfect Week Manual Exception?`) |
| Shots — simple | **Shot Total** |
| Shots — detailed | 2PT Made/Attempted, 3PT Made/Attempted, FT Made/Attempted; **Submission Stat Mode** formula = `Detailed Shooting` if any detailed field filled, else `Simple Total`; **Detailed Stats Valid?** (non-negative, made ≤ attempted); **Total Shots Canonical**, **Total Makes Canonical** |
| Week | **Week** (link), Week Assignment Status formula (`No Activity Date` / `Activity Date in Future` / `Assigned` / `Needs Assignment`), Needs Week Assignment?, **Week Counts Toward Challenge?** (lookup from Weeks) |
| Homework | **Homework Name 1 / Homework Name 2** (link → **Program Homework Assignments**, not the library), **HW Sub 1 / HW Sub 2** (attachments), HW 1 / HW 2 - Parent Note, Has HW1? / Has HW2? |
| Video | **Video Upload** (attachments), Video Upload Note, **Video Feedback Focus**, **Video Feedback Note**, Has Video? (formula; replaced retired 006), Video Count (orphaned), Has Review Assets? |
| Duplicates | **Duplicate Key** formula = `Enrollment\|YYYY-MM-DD\|time-or-NO_TIME\|mode\|stats…`; **Duplicate Review Status** [Needs Review, Count It, Exclude It, OK, Pending Review, Duplicate, Not Reviewed] |
| Counting gate | **Count This Submission?** = 0 if Activity Date Is Future, no Week, no Enrollment, Duplicate Review Status ∈ {Exclude It, Needs Review}; else Simple Total needs Shot Total ≥ 0, Detailed needs Detailed Stats Valid?; Counted shot/make fields; Counted Activity Date Key; Perfect Week Countable Submission? |
| Assets | **Attachment Upload Status** [Processing, Sent, Error, No Files], Attachment Upload Error, **Ready for 009 Asset Creation?** (Enrollment linked, no existing Submission Assets, at least one attachment), Why Not Ready for 009?, Submission Assets Ready?, Ready to Send Attachments to Make?, Submission Assets (link) |
| Reconciliation | **Current Reconciliation Signature** = `RECORD_ID\|COUNT\|MODE\|DUP\|VALID\|FUTURE\|SHOTS\|DATE\|ENR\|WEEK\|WAS\|XP_SIG\|XP_KEYS\|XP_SUBS\|XP_ENRS`, Last Reconciled Signature, Reconciliation Needed? |
| Daily email (owned by comms) | Daily Email To/Subject/Version/HTML, Sent to Make.com Status, Build Daily Email Now?, Send Daily Email to Make Now? |
| Parent edit link | **Edit Submission - Parent** = `"https://form.fillout.com/t/vNgeHardYcus?id=" & RECORD_ID()` |
| Test gates | **Season Sim Test Record?**, **Season Sim Clock Now**, **Season Sim Test Submitted At** (SC-SEASON-SIM-002); Perfect Week Test Record? / Test Submitted At; Testing Scenarios (link) |
| XP (elsewhere) | XP Award Status [Pending, Processing, Awarded, Error, Completed, No Shots Submitted], XP Events links |

### 1.6 Submission Assets (90 fields) — one row per uploaded file

| Group | Fields |
|---|---|
| Identity | Submission Assets Full Name (primary), **Asset Key** (= RECORD_ID after FUT-002), Submission (link), Enrollment (link), Program Instance (link), Week (link), Homework Completion (link), Video Feedback (link) |
| Slot / purpose | **Asset Purpose** [Homework 1, Homework 2, Video For Feedback, Registration Headshot, Other]; **Asset Slot** [HW1, HW2, VIDEO, VIDEO-1…VIDEO-4]; Asset Slot Base; **Asset Label** (`HW1-1`, `VID-2` …); **Asset Type** [Homework PDF, Homework Image, Homework Document, Video Feedback, Submission Photo, Submission Video, Athlete Headshot, Other, Image, Video]; Asset Sequence; Is True Video Feedback Asset?, Is Homework Upload Asset? |
| Source file | Airtable Attachment (copy), **Source Attachment ID** (idempotency key), Original File Name, File Size Bytes, File MIME Type |
| Routing | **Upload Destination** formula = SWITCH(Asset Purpose: Homework 1/2 → `Homework Completions`; Video For Feedback → `Video Feedback`; Registration Headshot/Other → `Ignore`); Ready to Send to Make?; Why Not Ready for Make?; Workflow Next Step; Ready for Homework Completion Script? / Ready for Video Feedback Script?; **Send to Make Trigger** (checkbox) |
| Upload lifecycle | **Upload Status** [Pending Link, Processing, Uploaded, Error, Ready, No File]; Upload Error; Uploaded At; **Upload Claim Run ID**, **Processing Started At** (Lambda-owned claim); **Writeback Complete?** = Uploaded + Canonical + Storage Key + hash + Uploaded At; Upload Ready? |
| Storage | **Storage Key** (S3 object key), **Canonical File URL** (private S3 HTTPS — never public), **Reviewer File URL** formula = `https://qzfaiyaq7a2cugh6alpov7iyfu0nrwbf.lambda-url.us-east-2.on.aws/file/{RECORD_ID}?token={Reviewer Access Token}`, Reviewer Access Token, legacy Google Drive File ID/URL, Formatted Upload Name |
| Naming helpers | Program Instance - Convert to File Name, Date - Convert YYYY_MM_DD, Asset Type - Convert, **Upload Naming Status** [Pending Metadata, Ready, Blocked, Error] |
| Content hash dedup | **File Content Hash**, **File Hash Algorithm** [SHA-256], **File is Duplicate?**, **Duplicate File Status** [Not Checked, Unique, Exact Duplicate, Possible Duplicate, Allowed Reuse, Needs Review, Error], **Duplicate Match Strength** [Exact SHA-256 Hash, Same Source Attachment ID, Same Size and Filename, Filename Only Weak Match, Manual Review], Duplicate Match Record(s) (self-link), Duplicate Match Notes, Duplicate Checked At, Duplicate Check Error, Exact Hash Match Found?, Same Enrollment Match Found?, Potential Asset Reuse? |
| Reuse review | **Duplicate Review Status** [Not Reviewed, Needs Review, Confirmed Duplicate, Not Duplicate, Allowed Reuse]; **Asset Reuse Decision** [Not Reviewed, Approved Reuse, Allowed — Legitimate Reuse, Allowed — Correction/Resubmission, Confirmed Duplicate, False Positive, Unable to Determine, Resolved — Duplicate Record Error]; Asset Reuse Review Summary / Reviewed By / Reviewed At / Primary Reason / Reasons / Review Notes; Duplicate Resolution Applied? / Applied At / Error / Last Applied Decision |
| Video review | Video Feedback Focus [Shooting, Layups / Finishing, Ball Handling, Free Throws, Footwork / Defense, Strength / Movement, General Basketball, Other] |

### 1.7 Weeks (21 fields)

Week Name, **Start Date / End Date** (dateTime, Denver), **Week Key** = `ARRAYJOIN(Program Instance) & "|" & Week Name`, **Program Instance** (link), Config - Lnk, **Counts Toward Challenge?** (checkbox → Submissions lookup "Week Counts Toward Challenge?"), Active Week? / Active?, Reconciliation Source Signature, FBC Curriculum - SYNC (link), Program Homework Assignments (link), Submissions / WAS inverse links.

### 1.8 Program Homework Assignments (PHA, 25 fields)

Junction: **Homework Assignment** (link → Homework Library, exactly one) + **Program Instance** + **Week** + **Grade Band** + **Homework Slot** [HW1, HW2] + Active? + Due Date. `Schedule Key` = `PI|Week|GradeBand|Slot|Homework` (dedupe fingerprint). Operator Status formula (Incomplete / Active / Inactive). `Homework XP PHA Signature`. Submissions.Homework Name 1/2 link **here**, not to the library; 005/020 dereference library content.

### 1.9 Program Instance - Sync (39 fields)

Name (e.g. `Shooting Challenge | 2026-2027`), Program / Event / **School Year - Linked**, Start / End, **Registration Open / Registration Closes**, **Status** [Closed, Completed, In Progress, Inactive, Planning, Registering, Up Next], Cost + pricing tiers, Season, **Program Code** [character, dribble, freethrow, shooting], **Registration URL**, **Daily Submission URL**, Welcome - Website URL / Subject Line / Intro Note, Why This Matters, Minimum Video (lookup), links to Enrollments/Weeks/Config/PHA/Target Goal Shots.

### 1.10 Config (40 fields; single row per season)

| Field | Purpose |
|---|---|
| **Active School Year** | selects the live season (`YYYY-YYYY`) |
| Root Google Drive Folder ID / Link | legacy Drive root (`1e4ymb1M4IlAMBgjAhSMiuYdaSiUtYM80`) |
| **Max Videos Per Submission** | cap for VIDEO slots (asset slots VIDEO-1..4 exist) |
| File / **File Naming Pattern** | upload naming template |
| **Detailed Stat Tracking Enabled?** / **Require Detailed Stats?** | simple vs detailed shooting intake |
| **HW Review Enabled?** / **Video Review Enabled?** | gate review pipelines |
| Submission Base XP, Shot XP Per Shot, Submission XP Active?, Submission XP Notes, Active XP Rule Set | XP (see other doc) |
| **Challenge Week Count** | number of counted weeks |
| **Perfect Week Video Minimum** (= 3 in PROD) | Perfect Week rule; looked up on Enrollments |
| C-025 recording fields | Recording Approval Email Enabled? / Template Key / Timing; Recording Gives Full Zoom Gate Credit?; Recording Makeup Counts for Perfect Week?; Recording Makeup Enabled?; Recording Path Enabled?; Recording Quiz Requires Coach Approval?; Zoom Recording Deadline Mode; Makeup Window Days; XP Percent of Live; YN helper formulas |
| Links | Zoom Attendance, Zoom Meetings, Weeks, Level Gate Rules, Program Instance - Sync, FBC Curriculum - SYNC |

### 1.11 School - Synced (31 fields)

School name, State, Level, Classification, Division, District, Colors, Song, Nickname, **Mascot**, etc. Synced from another base; Enrollments link to it for standings display.

### 1.12 Testing Scenarios (25 fields)

**Scenario Type** [Daily Submission, Homework, Homework + Video, Three Video Upload, Milestone Crossing, Perfect Week, Backdated Submission, Parent Feedback, Weekly Summary, Award Generation, Other, Video]; Test Status; **Last Run Status** [Pass, Fail, Blocked, Error, Not Run]; **Run Test?**; **Dry Run?**; Submission Date; Shot Total; Video Feedback Focus [Form, Footwork, Release, Follow Through, Other]; Video Feedback Question; **Intake Attachments**; Related Enrollment; Linked Submission; Homework Assignment (→ PHA); Last Run At / Notes / Output.

---

## 2. Enrollment lifecycle

### 2.1 Intake (Fillout → Enrollments)

Contract: `docs/online-agents/enrollment-season/FILLOUT-ENROLLMENT-CONTRACT.md` + `fillout-enrollment-contract.schema.json`; validator `tools/enrollment-season/enrollment_validator.py`.

| External label | Airtable field | Required | Notes |
|---|---|---|---|
| Athlete First / Last Name | same | yes | trim, collapse spaces; validator warns on ALL CAPS |
| Parent First / Last Name | same | yes | welcome copy |
| Parent Email | Parent Email | yes | lowercased; Fillout blocks bad format |
| Athlete Email | Athlete Email | no | not part of identity |
| Grade | Grade | yes | `Pre-K` → `Pre K`; must fall in a Grade Band |
| School | School (link) | season-dependent | |
| Parent / Athlete Cell | Parent Cell Number / Athlete Cell Number | no | SMS future (SC-044) |
| School Year | School Year | yes | current season option |
| Program / Challenge | Program Instance | yes for welcome | |
| Gender, Mailing Address, Registration Source, Consent | various | | |
| Payment | Price Paid to Stripe, Stripe Payment Id, Fillout Submission Id, Payment Transactions | | Fillout + Stripe |

Retired (do not rebuild): Parent Email Subject/HTML, Welcome Email Status/Sent At/Error/Ready? (legacy 075). Live welcome path: **078A → Email Handoff Queue (WELCOME) → 079 → Communications Hub → Resend**; requires Athlete linked + Parent Email - Cleaned + Program Instance.

### 2.2 Automation 001 — find-or-create Athlete (v5.4)

File: `001-enrollment-intake-and-setup-find-or-create-athlete-and-link-enrollment.js`

1. Validate `recordId`; load Enrollment; require First, Last, Parent Email (Cleaned → Parent Email → Submitted); validate `School Year` is consecutive `YYYY-YYYY` (`isValidSchoolYear`).
2. Set `Athlete Match Status = Processing`, **`Active? = false`** (fail-closed while processing).
3. If already linked → `already-linked` (or `already-linked-and-activated`).
4. Match key `normalizeEmail(parent)|normalizeText(first)|normalizeText(last)`; `normalizeEmail` strips angle brackets, quotes, trailing `,;`, whitespace. Match order: formula `Athlete Match Key` exact → normalized first+last+parent email → last-chance re-query → create Athlete (First, Last, Parent Email, Active?=true).
5. **Duplicate season guard** (`findExistingEnrollmentForSeason`): if the Athlete already has another Enrollment with same School Year → clear Athlete link, `Active?=false`, status `Error`, `actionTaken=duplicate-enrollment-blocked`.
6. Otherwise link Athlete, `Active?=true`, status `Linked`, `Level Recalc Needed?=true`.

Outputs: `athleteId`, `athleteMatchKey`, `actionTaken` (already-linked / matched-existing-and-linked / created-and-linked / duplicate-enrollment-blocked), `matchMethod`, `parentEmailUsed`, `statusOut`, `errorOut`, `debugStep`.

Design rules (`NEW-RETURNING-ATHLETE-SPEC.md`, `SIBLING-HANDLING-SPEC.md`): no auto-merge of Athletes; a parent-email change creates a *new* Athlete (known risk); same name under different parent = distinct athlete; siblings share parent email, get separate Athletes/Enrollments/email packages; School and Grade are Enrollment-scoped (season), identity is Athlete-scoped.

### 2.3 Automations 002 / 003 — Grade Band

- `normalizeGradeToNumber`: `pre k|pk|preschool` → -1; `k|kindergarten` → 0; ordinals (`1st`, `2nd`…) and numerics.
- `findMatchingGradeBands`: Active? and `Min ≤ g ≤ Max`, sorted by Sort Order/min/max/name. 0 matches → Error; >1 → Error (ambiguous).
- Writes: Grade Band link, Grade Band (Auto Assign) text, Last Grade Used for Grade Band, Grade Band Status (Pending → Processing → Assigned/Error), Grade Band Assignment Status.
- 002 trigger view: Grade and Athlete not empty, Grade Band empty, `Ready for Grade Band Assignment? = 1`.
- 003 (v2.0, production-verified 2026-09-03) trigger view `Automation - 003 - Grade Band Refresh Needed` (`Grade Band Refresh Needed = 1`, i.e. Grade ≠ Last Grade Used). Grade Band history of prior seasons untouched; downstream copies (030 WAS, 063/111 homework/video band copies) re-derive.

### 2.4 Active? and Progress Processing Enabled? guards

`tools/enrollment-season/active_guard_contract.py` catalogs consumers: 023 (Active? → may auto-link), 010/031/053/065 (spec: PPE; historically Active? gap), 056/066/101/114 (Active?), 072/118/119 (Active? + **hard-coded Schmidt exclude** — documented conflict with "Schmidt visible, Active?=true" Foundation Reset), 076 (gap), web leaderboard (Active? view/fallback). Rule: missing field → treat as enabled (`missing_fallback=True`).

### 2.5 Folder/file naming

`Athlete Folder Name = Last_First_SchoolYear` (Enrollments formula) — original Drive folder convention; S3 era uses Submission Assets naming helpers + Config `File Naming Pattern`. Headshot: `Athlete Headshot` attachment on Enrollments; `Registration Headshot` asset purpose routes to `Ignore` (not uploaded by engine).

### 2.6 Season/intake calendar for enrollment

`tools/enrollment-season/season_date_boundaries.py` models: enrollment open/close, challenge start/end, early-bird window (SC-066 decision: use early-bird registration), preseason access, late enrollment, backdate limits, intake statuses `before_intake / intake_open / late_enrollment / intake_closed`. C-018 / SC-064: **intake-open dates are separate from challenge-run dates** (Program Instance `Registration Open/Closes` vs `Start/End`).

---

## 3. Submission intake

### 3.1 Form and record shape

Fillout Daily Submission form (OFF since C-008; reopen gated by SC-135/SC-146). Form carries Enrollment identity (`Fillout Enrollment Id` / Enrollment pre-link) and never chooses a Week (`docs/challenge-year/FILLOUT-SEASON-ACTIVATION.md`). Parents get an edit link `Edit Submission - Parent` (Fillout `vNgeHardYcus?id=rec…`). Program Instance exposes `Daily Submission URL` and `Registration URL` per season.

Fields written by form: Activity Date, Activity Date - Time (optional hourly), Shot Total **or** 2PT/3PT/FT made/attempted, Homework Name 1/2 (PHA), HW Sub 1/2 (1–3 files each), HW 1/2 - Parent Note, Video Upload (1–`Max Videos Per Submission`), Video Upload Note, Video Feedback Focus, Video Feedback Note.

Config switches: `Detailed Stat Tracking Enabled?`, `Require Detailed Stats?`, `HW Review Enabled?`, `Video Review Enabled?`, `Max Videos Per Submission`.

### 3.2 Simple vs detailed stats

`Submission Stat Mode` = `Detailed Shooting` if any of the six detailed fields is filled, else `Simple Total`. `Detailed Stats Valid?` requires non-negative and made ≤ attempted. `Total Shots Canonical` / `Total Makes Canonical` unify both modes for downstream (XP, WAS, milestones).

### 3.3 Activity-date rules

- `Activity Date Is Future?` compares to `NOW()`; future → not counted, not assigned a Week (Week Assignment Status `Activity Date in Future`), 009 blocked (`Activity Date Is Future? = 0` in trigger).
- `Submitted At = CREATED_TIME()` cannot be backdated (relevant to same-day / Perfect Week rules).
- `Submitted Same Day?` (Denver) and `Perfect Week Grace Eligible?` (48-hour grace or `Perfect Week Manual Exception?`) feed Perfect Week.
- Backdated submissions are allowed as long as a PI-scoped Week covers the date (`season_date_boundaries.evaluate_submission_eligibility`).

### 3.4 Automation 023 — assign Enrollment (v3.1)

Priority: (1) existing valid link (athlete matches, Active?, PI matches); (2) `Fillout Enrollment Id` / `Enrollment Record ID`; (3) Submission.Program Instance; (4) Week → Weeks.Program Instance; (5) Submission School Year; (6) single-active-enrollment fallback **only when no other context**. Ambiguity → skip and clear bad links; never guesses.

### 3.5 Automation 005 — assign Week, homework-first (v5.5)

- Week = the one PI-scoped Weeks row (Program Instance match; Active) whose `[Start, End]` date keys contain Activity Date. 0 → clear Week (`clearWeekWhenNoMatch: true`), >1 → error.
- Homework Name 1/2 hold **PHA record IDs**; `validateSelectedPha`: Active?, PI match, Week match, Homework Slot HW1/HW2, exactly one Homework Assignment link. `normalizeHomeworkPlacement` auto-corrects slot placement; duplicate slot → fail closed. Homework with no resolvable week → error. **Grade Band is never used for scheduling.**
- Key behavior: homework validity is checked *before* committing the week so a submission cannot land on a week whose homework doesn't match.

### 3.6 Automation 021 — Attachment Upload Status (v2.0)

`No Files` vs `Processing` from HW Sub 1/2 + Video Upload; runs when status empty or `No Files` (so late-added attachments re-arm). Terminal `Sent`/`Error` set by asset pipeline.

### 3.7 Automation 007 — duplicate checker (v2.0)

Reads formula `Duplicate Key` (Enrollment|date|time-or-NO_TIME|mode|stats). Scans other Submissions: 0 matches → `Count It`; ≥1 → `Needs Review`; preserves manual `Exclude It` (`overwriteExcludeIt:false`). `Count This Submission?` excludes `Needs Review` and `Exclude It`, so a flagged duplicate is held out of scoring until a human resolves it.

### 3.8 Automation 006 — retired

Video Count (SF-07 / SC-158, 2026-09-04): presence now via `Has Video?` formula; Perfect Week counts videos in 057. Do not rebuild a counter automation.

### 3.9 Reconciliation signature

`Current Reconciliation Signature` concatenates count/mode/dup/validity/future/shots/date/enrollment/week/WAS/XP keys; compared to `Last Reconciled Signature` to flag `Reconciliation Needed?` — a cheap change-detection mechanism for audits/backfills (`airtable/extension-scripts/audits/`, `tools/season_simulation/reconciliation_checker.py`).

### 3.10 Season-simulation gates on Submissions

`Season Sim Test Record?` + `Video Upload Note` containing `SEASON-SIM|…` + `Season Sim Clock Now` + `Season Sim Test Submitted At` allow a temporary gated formula variant of `Activity Date Is Future?` and `Submitted Same Day?` so disposable 2027 rows can count before wall-clock reaches the season (`tools/season_simulation/clock_override.py`). Production formulas restored to plain NOW()/TODAY() after SC-SEASON-SIM-002.

---

## 4. Submission Assets pipeline

### 4.1 Automation 009 — create assets (v1.3, SC-160)

| Source field | Slot | Purpose | Label prefix | Gate |
|---|---|---|---|---|
| HW Sub 1 | HW1 | Homework 1 | `HW1-n` | exactly one Homework Name 1 (PHA) link |
| HW Sub 2 | HW2 | Homework 2 | `HW2-n` | exactly one Homework Name 2 link |
| Video Upload | VIDEO | Video For Feedback | `VID-n` | none |

- Exactly one Enrollment required; Week optional (0 → note "week-dependent scoring on hold"; >1 → fail).
- Idempotency: exact `Source Attachment ID` → skip; **compatible restoration** (same filename+label+size+type) → repair existing asset; ambiguous → `needs_review`.
- `inferAssetType`: purpose Video For Feedback → `Video Feedback`; image → `Homework Image`; video → `Video Feedback`; pdf → `Homework PDF`; doc/docx/pages → `Homework Document`; else `Other`.
- Creates asset: Upload Status `Pending Link`, Send to Make Trigger false, Original File Name, Purpose/Type/Slot/Label, attachment copy, Submission/Enrollment/Week/PI links. Parent Submission: Attachment Upload Status `Processing`/`No Files` + Attachment Upload Error.
- Trigger: `Ready for 009 Asset Creation? = 1` AND `Activity Date Is Future? = 0`.

### 4.2 Child linking (020 / 013)

020 links/creates **Homework Completion** per (Enrollment, PHA) — N assets → one HC (SC-015/016); HC Week = PHA.Week. 013 links/creates **Video Feedback** per video asset. Both keep `Pending Link` and check `Send to Make Trigger`. (Owned by other inventories; included for pipeline continuity.)

### 4.3 Upload Status ladder (`make/documentation/upload-asset-engine.md`)

| Status | Meaning | Set by |
|---|---|---|
| Pending Link | prep complete, eligible for send | 009, 013, 020 |
| Processing | claimed by Lambda (`Upload Claim Run ID`, `Processing Started At`) | **Lambda** (070a/b never write Processing in v4.8) |
| Uploaded | object in S3; writeback done | Lambda/Make |
| Error | upload or validation failed; `Upload Error` text | Lambda/Make/070 |
| Ready / No File | legacy/homework-only states — do not introduce alternate gates |

Audit `airtable/extension-scripts/audits/audit-stuck-upload-processing.js` expects 0 stuck Processing rows.

### 4.4 Automations 070a / 070b — send payload (v4.8 shared body)

Inputs `recordId`, `makeWebhookUrl`, `automationNumber`. Payload (no attachment URLs, no season slug, no secrets):

```json
{ "sourceName": "Airtable Upload Engine", "automationNumber": "070b", "sentAtIso": "...",
  "routeKey": "homework_completion | video_feedback", "uploadDestination": "Homework Completions | Video Feedback",
  "sourceTable": "Submission Assets", "submissionAssetRecordId": "rec…",
  "targetTable": "Homework Completions | Video Feedback", "targetRecordId": "rec…",
  "enrollmentId": "rec…", "programInstanceId": "rec…" }
```

Guards: already uploaded (Canonical URL or Uploaded+Storage Key) → `skipped_already_uploaded`; blank Submission allowed if HC-linked + Enrollment (v4.8); exactly one Enrollment and one PI; missing target → `skipped_pending_link`; missing attachment → Error. Response handling: plain-text `Accepted` → `lambda_upload_accepted_async` (070c verifies); Lambda JSON must be `uploaded` + `writebackVerification.allPass` or `skipped_already_uploaded`; failures keep trigger + write Upload Error. Triggers: `Send to Make Trigger` checked AND Upload Status `Pending Link` AND Upload Destination matches route.

### 4.5 Make → Lambda → S3 (`make/documentation/C-013-prod-upload-engine-lambda-runbook.md`)

Make scenario `Upload Engine - Lambda - v1`: webhook → router (`automationNumber`+`routeKey`) → HTTP POST Lambda Function URL with `X-Upload-Secret` (120 s timeout) → webhook response (200 Lambda JSON or 502 error JSON; often `Accepted` async). Lambda re-fetches the asset from Airtable (fresh attachment URL — avoids expired URLs), downloads, hashes (SHA-256), stores in **private program-owned S3**, resolves season via Enrollment → Program Instance → School Year - Linked, writes back Storage Key, Canonical File URL, File Content Hash/Algorithm/Size/MIME, Uploaded At, Upload Status, claim fields. Reviewer access is via Lambda viewer URL + per-record token (`Reviewer File URL`), never a public bucket URL. Homework resources also served via CloudFront `d21ixrrrqpqz29.cloudfront.net` (FUT-048 custom domain deferred). Legacy v1/v2 Make scenarios uploaded to Google Drive (athlete folder search/create under root) — superseded (SC-100 Drive retirement deferred).

### 4.6 Hash duplicate detection (`upload-asset-engine-v2-hash-duplicate-check.md`, C-023)

Hash helper → Airtable REST lookup `{File Content Hash} = sha AND RECORD_ID() != self` → write File is Duplicate?, Duplicate File Status (Unique / Exact Duplicate / Error), Duplicate Match Strength, Duplicate Match Record, Notes, Checked At, Check Error. **Flag only; never blocks upload.** Human review fields: Duplicate Review Status, Asset Reuse Decision. Rule: never auto-reuse another athlete's object (SC-098).

### 4.7 Automation 070c — verify async upload (v1.1)

Trigger `Writeback Complete? > 0`. Verifies Upload Status Uploaded, Canonical URL, Storage Key, hash + `SHA-256`, Uploaded At, blank Upload Error → clears `Send to Make Trigger`. Actions `async_upload_verified_trigger_cleared`, `async_upload_already_verified`, `async_writeback_verification_failed`. Idempotent; does not upload.

### 4.8 Automation 022 — child writeback (v2.2)

Copies from asset → Homework Completions {Upload Status, Upload Error, Uploaded At, Writeback Complete?} or Video Feedback {Upload Status, Upload Error, **Video URL or Drive Link**, Video Asset File Name, Video Asset Uploaded At, Writeback Complete?}. Skips `Pending Link`. `classifySecureVideoUrl` accepts only `https://*.lambda-url.us-east-2.on.aws/file/rec…?token=…`; rejects Google Drive, direct/presigned S3; writes repair note when Reviewer File URL missing.

### 4.9 Automation 116 — Asset Reuse Decision consequences (v1.0.1, C-023 S5)

Decision groups: notReviewed [`Not Reviewed`]; approved [`Approved Reuse`, `Allowed — Legitimate Reuse`, `Allowed — Correction/Resubmission`]; confirmed [`Confirmed Duplicate`]; falsePositive [`False Positive`, `Unable to Determine`, `Resolved — Duplicate Record Error`]. Confirmed duplicate → Video Feedback `Do Not Award XP?` / Award Status adjusted, XP source keys `VIDEO_SUBMISSION|vfId` / `HOMEWORK_XP|hcId` referenced; writes Duplicate Resolution Applied?/At/Error/Last Applied Decision + `[C-023-S5]` audit note. Never deletes assets or S3 objects; reversible.

### 4.10 Automation 120 — FUT-009 S3 video rename (v1.0, OFF pending test)

Video Feedback trigger: `Confirm S3 Video Rename` checked, `Custom Video File Name` valid (not blank/`—`), Submission Asset linked. Calls Lambda `POST /fut009/rename` with `X-Upload-Secret`; Lambda CopyObject + HeadObject, keeps original object; patches Storage Key, Canonical File URL, Formatted Upload Name. Actions renamed / airtable_only_recovery / skipped_already_named / ready_for_lambda / error_*.

### 4.11 Locked upload models (`docs/upload-workflow-homework-video.md`)

- Homework: 1–3 files per slot; naming decided **before** upload from metadata (PI, date `YYYY_MM_DD`, asset type, athlete); `Upload Naming Status` gates send.
- Video: 1–N (Config max) per submission; one Video Feedback child per asset; Video Feedback Focus/Note carried from Submission.
- Metadata ownership: Airtable owns purpose/slot/labels; Lambda owns claim/storage/hash fields; Make owns nothing durable (transport).

---

## 5. Weeks, Program Instances, Config, Target Goal Shots

### 5.1 Week contract (`docs/challenge-year/WEEK-CONTRACT.md`, `CHALLENGE-YEAR-CONTRACT.md`)

- Weeks are **Sunday–Saturday**, America/Denver; `Week 0` (Early Bird, countable in 2026-27: Apr 25–May 1), `Week 1..N`, `Post-Challenge`. `Counts Toward Challenge?` per week; Config `Challenge Week Count`.
- Identity = Week record ID / `Week Key` (`PI|Week Name`), never Week Name alone (multi-year).
- Generator CLI `tools/challenge-year/` builds the season calendar from Program Instance Start/End; resolver statuses for unresolved dates; `tools/enrollment-season/weeks_seed_validator.py` checks seed CSV (required Week Name/Start/End/Sequence; overlap FAIL, gap WARNING, duplicate sequence FAIL; optional Week Type Early Bird/Regular/Final/Preseason, Intake Open?, Counts for XP?, Counts for Leaderboard?, Program Instance required for multi-year).
- Annual rollover (`ANNUAL-ROLLOVER.md`): new Program Instance → new School Year option → seed Weeks + PHA (20 live PHA rows for 2026-27; Week 9 ×2) + Target Goal Shots → flip Config `Active School Year` → Fillout season routing (`fillout-season-routing.contract.json`, attestations F-ATT-01..05).

### 5.2 Program Instance isolation (V2-013 / SC-067)

Every scoped lookup must filter by Enrollment or Program Instance: `tools/program-instance-isolation/audit-program-instance-isolation.mjs` flags `athlete-without-enrollment-filter`, `week-date-without-program-instance`, `week-name-as-identity`, `summary-athlete-week-name`, `xp-rule-type-only`, `zoom-meeting-date-only`, `select-all-records-broad-scan`, `dedupe-key-uses-display-name`. Multiple seasons coexist in one base; Status select [Planning, Registering, Up Next, In Progress, Completed, Closed, Inactive].

### 5.3 Per-band goals

Target Goal Shots: one Active row per Grade Band per Program Instance (`Goal Key = SHOT_GOAL|BAND|target`). Weekly goal = season goal / counted weeks (e.g. 12,000 → 1,334/week → 191/day Perfect Week minimum for 9–12).

### 5.4 Config-over-code (SC-021)

No hard-coded season numbers in scripts; all season knobs in Config / Program Instance / Weeks / Grade Bands / Target Goal Shots / XP Reward Rules.

---

## 6. Testing framework, season simulation, disposable data

### 6.1 Engineering Test Framework (`docs/testing-and-intake-architecture.md`, C-017–C-020, SC-001/002)

- **Testing Scenarios** table drives Fillout-shaped tests without Fillout. Automation **115 (v2.1)** runs on `Run Test?`: enrollment **allowlist** `recgP9qZYjAhE7NXm` (Schmidt) and `recCyFEPeATOVNlr9`; scenario types Daily Submission / Homework / Video / Three Video Upload (+ Other / Perfect Week downstream with `C025_STAGE17_DOWNSTREAM`); `Dry Run?` returns a preview payload without writes; maxHomeworkFiles 3, maxVideoFiles 3; homework scenarios must point at a **PHA** (library-only links rejected); writes Submission {Enrollment, Athlete, Activity Date, Shot Total, Homework Name 1, HW Sub 1, Video Feedback Focus/Note, Video Upload, Duplicate Review Status=Count It}; records Last Run Status Pass/Fail/Blocked/Error/Not Run; actions created / dry_run / blocked_* / skipped_* / c025_*. Not idempotent per run — each check creates a new Submission.
- Principle: **no test flags on pipeline tables**; tests are real records on the permanent Schmidt enrollment (SC-004; Active?=true, publicly visible, emails Schmidt-only). Two calendars (intake vs challenge) honored.

### 6.2 Season Simulation (`tools/season_simulation/`, SC-SEASON-SIM-001/002)

Python harness (preflight → execute → settlement → reconciliation → cleanup) simulating a full 67-day season (Apr 25–Jun 30 2027) with disposable athletes (`Sim Perfect` g12 / `Sim Recovery` g10 / `Sim Edge` g8). Hard gates: confirmation tokens (`SEASON-SIMULATION-2027`, `CONFIRM-DISPOSABLE-SEASON-SIM`, `CONFIRM-CLEANUP-SEASON-SIM`, `RUN 3-ATHLETE SEASON SIMULATION`), safe email recipient only, run registry + `SEASON-SIM|run` markers in Notes fields, transactional vs reference table lists (Weeks/Config/PHA/Library/Grade Bands/Target Goal Shots never deleted), gated clock-override formulas (see §3.10), zero-remnant audit after cleanup. SC-SEASON-SIM-002 complete; three-athlete run READY, not executed.

### 6.3 Disposable test records (FUT-030, operating mode)

Transactional tables (Enrollments, Submissions, Submission Assets, Homework Completions, Video Feedback, XP Events, unlocks, WAS, Zoom attendance, Email Handoff Queue) may be reset; Weeks/Config/PHA/schema/S3 objects never. Full reset 2026-08-31 deleted 959 records and restored 18 PHA.

---

## 7. Known gaps and future ideas (IDs from `docs/127-SI-MASTER-FUTURE-WORK-LIST.md`)

| ID | Item | Status |
|---|---|---|
| C-010 / SC-068 | Harden `Active?` + PPE guards across 010/031/053/065/076; resolve 072/118/119 Schmidt hard-exclude conflict | queued |
| C-017 / SC-060 | Fillout → Athletes validation trustworthy; tighten live form at reopen | queued / live-tested |
| C-018 / SC-064 | Intake-open vs challenge-run calendars wired into Fillout/web gate | queued |
| C-021 | Grade bands propagate automatically downstream | queued |
| C-023 / SC-097 / SC-098 | Content-hash dedup + manual reuse decision | in progress |
| C-009 | Redo HW17 Fillout quiz intake (no attachment) | queued |
| SC-019 | Learning Activity Responses table + response → asset routing | built in repo |
| SC-032 / SC-065 | Season settings; Weeks rebuilt (complete for 2026-27) | built / complete |
| SC-066 | Early-bird registration periods | decided: yes |
| SC-067 / V2-013 | Program Instance multi-year redesign | deferred architecture wave |
| SC-100 | Attachment / Google Drive retirement | deferred |
| SC-146 | Re-open Fillout daily intake when season ready (after SC-135 dry run) | deferred |
| SC-135 / V2-012 | Dry-run full season on Schmidt before public intake | queued |
| FUT-009 | S3 video rename (Automation 120) | repo v1.0, OFF |
| FUT-029 | Grade-band homework platform + intake adapter | deferred — do not implement |
| FUT-040 | Automatic S3 migration of legacy attachments | brief needed |
| FUT-048 | CloudFront custom domain for homework resources | deferred |
| SC-144 | Schema typo renames (e.g. `Registratioin Referrer`) | deferred |
| SC-SEASON-SIM-001 | Three-athlete season simulation execute | ready, not executed |
| — | Known identity gaps: parent-email change → new Athlete; duplicate Enrollment possible from form resubmit (001 v5.4 now blocks same-season duplicates at link time) | documented |
| — | Video Count field orphaned after 006 retirement | cleanup candidate |
