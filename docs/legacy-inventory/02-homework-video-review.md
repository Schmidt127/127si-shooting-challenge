# 02 — Homework system and Video Feedback system (legacy inventory)

Source repo: `Schmidt127/127-si-shooting-challenge` at `/workspace` (read-only research, 2026-10-07).
Production base: `appn84sqPw03zEbTT`. Schema cited from
`airtable/schema/snapshots/prod-20260905-fut002-batch2/schema_doc_appn84sqPw03zEbTT_20260905_062812.md`.
Scripts cited from `airtable/automations/shooting-challenge/`. Web cited from `web/`.

XP point *amounts* are intentionally **not** documented here (covered elsewhere). This file documents
XP *mechanics* only where they gate homework/video workflow.

---

## 0. Executive map

| Domain | Intake | Identity / dedupe | Review | XP prep → event | Parent email | Retired / legacy |
|---|---|---|---|---|---|---|
| Homework (file upload) | Fillout → Submission (`Homework Name 1/2` = PHA IDs, up to 3 files) → 009 creates Submission Assets → **020** creates/links one HC | One HC per **Enrollment + PHA** (fallback Enrollment+Week+Library HW) | Coach in "Homework Grading Queue" Interface: Coach Feedback + Satisfactory? + Review Complete | **064** (Base XP, Award Status Pending) → **065** (`HOMEWORK_XP\|{hcId}`) | **078** (native) sets Parent Feedback Ready? → **071** → Email Handoff Queue → **079** → Communications Hub → Resend; Hub writes Sent?/Delivery Status | 012 deleted, 063 retired, 068 retired (033 owns WAS reconcile) |
| Homework (HW17 reflection quiz) | Fillout → `Final Reflection Quiz Submissions` → **067** | Same HC identity; attachment-less HC (Option B) | Same queue; quiz summary surfaces in HC | Same 064/065 | Same 071 (adds `quizSummary`) | Quiz Result PDF path (Option A) rejected |
| Homework (Structured Curriculum / "Curriculum Hub") | Web `POST /shoot/api/curriculum/homework/submit` creates HC directly (**zero Submissions**), plus immutable `Homework Attempts` + `Homework Responses` | Enrollment + Library (by `Assignment Key`) + PHA resolved by PI + Enrollment Grade Band; idempotency keys | Same queue | Same 064/065 | 071 v4.5+ accepts HC-only topology | Fillout-only path (FUT-029 deferred) |
| Video Feedback | Fillout → Submission (`Video Upload`, up to 3) → 009 assets → **013** creates one Video Feedback per video asset → 070b/070c Make→Lambda→S3 → 022 writes Lambda viewer URL | Video Feedback Key = `VIDEO_FEEDBACK\|{assetId}` | Coach in "Video Feedback Grading" Interface: Coach Feedback + Feedback Posted? (+ optional Custom Video File Name + Confirm S3 Video Rename → **120**) | **113** (Base XP, Ready for XP Automation?) → **114** (`VIDEO_SUBMISSION\|{vfId}`, retires on source loss) | Coach manually sets Parent Feedback Ready? → **073** → Hub → Resend | 111 deleted, 112 OFF (legacy duplicate of 013) |

---

## 1. Homework content model

### 1.1 Homework Library (`tblUuxwYlX4EQ9MKE`, 29 fields in snapshot)

Catalog of assignments (book-based curriculum). Cited: schema snapshot; `web/lib/data/homework.ts` (`FbcCurriculumFields`), `web/lib/data/homework-resources.ts`.

| Field | Type | Notes |
|---|---|---|
| Assignment Full Name | primary text | Internal full name |
| Assignment Full Name - Display | formula | `Book Abbreviation - Topic - Title` |
| Assignment Title | text | **Public name** (FUT-046 precedence: Assignment Title → Full Name - Display → Full Name; `resolvePublicAssignmentName()` in `web/lib/data/homework.ts`) |
| Homework Number | single-select | `HW 1` … `HW 18` (HW 17 = reflection quiz) |
| Assignment Number | number | ordering |
| Book | single-select | Character 33 / Playing in the Box / Mental Toughness for Young Athletes / Stand Alone |
| Book Abbreviation | single-select | Char33 / P.I.B. / MTFYA / SA |
| Assignment Topic | multi-select | 25 values (Growth Mindset, Leadership, Confidence, Play Grounded, …) |
| Age Appropriate | multi-select | `1-3`, `4-6`, `7-8`, `9-12` — descriptive tiers only |
| Cover Images, Docs, Extension Activities | attachments | Resources served via web `app/api/homework/[id]/attachment/[attachmentId]/route.ts` |
| URL, URL Additional | url | External resources; durable link proxy `app/api/homework/[id]/link/route.ts` (SC-162) |
| Full Assignment Description | richText | Long-form instructions |
| Brief Description - Display | aiText | AI-generated teaser shown on web |
| Assignment Rationale, Specific Steps, Assignment Description | long text | Coaching pedagogy content |
| Active?, Published? | checkbox | Web catalog filters on Published |
| Order, Record Id | number / formula | sorting |
| Homework Completions, Weekly Athlete Summary, Program Homework Assignments | links | inverse links |
| Assignment Key | text (post-snapshot) | Stable key used by Curriculum Hub (`web/lib/curriculum/submit-service.ts`; `app/api/curriculum/library/sync/route.ts` "SC Assignment Key Sync") |

### 1.2 Program Homework Assignments — PHA (`tblhA3maf7xOa8EUS`)

The **scheduling** object: which library assignment is due in which Week of which Program Instance, in which slot.

| Field | Type | Notes |
|---|---|---|
| (primary) | formula | `PI \| Week \| GradeBand \| Slot \| Homework` |
| Homework Assignment | link (ONE) | Library row |
| Program Instance | link | PI |
| Week | link | **Authoritative week for the HC** (SC-160; 020 v4.1) |
| Grade Band | link (multi) | **Descriptive eligibility metadata only — never used for scheduling or identity** (FUT-049 plans removal). Web uses it for display filtering (`phaMatchesEnrollmentGradeBand` in `web/lib/data/public-athlete-homework.ts`); Curriculum Hub submit resolves PHA by PI + Enrollment Grade Band (SC-CURRICULUM-PHA-001). |
| Homework Slot | single-select | `HW1` / `HW2` — **routing metadata only**, not identity (FUT-001 rejected slot-as-identity) |
| Active? | checkbox | Only active PHAs are assigned/resolved |
| Due Date | date | Timing anchor; fallback = Week End Date (America/Denver) |
| Schedule Key | formula | `PI RID\|Week RID\|Slot\|HW RID` |
| Program Homework Assignment Display | formula | human label |
| Operator Status | formula | "Incomplete — fill…", "Active — will assign via 033 / resolve via 020", "Inactive — ignored by automations" |
| Operator Notes | text | |
| Completions Count | count | |
| Submissions / Submissions 2 | links | inverse of Submission `Homework Name 1` / `Homework Name 2` |
| Homework XP PHA Signature, Assignment Title - Lkp | formula / lookup | XP reconciliation + display |

Web schedule parsing (`web/lib/data/homework.ts`) resolves duplicate-slot PHAs for the same Week deterministically.

### 1.3 Tiers / Grade Bands

- `Grade Bands` table: `Default Homework Tier` single-select — Early Childhood, Primary, Elementary, Upper Elementary, Middle School, Underclassmen, Upperclassmen; plus Min/Max Grade, Target Goal Shots, Active?. (Grade Band linked source of truth: SC-023, 003 v2.0.)
- Library `Age Appropriate` (1-3/4-6/7-8/9-12) is the only per-assignment tier marker.
- Enrollment Grade Band is copied to HC/Video Feedback **by the creating automation** (020 / 013); dedicated copy automations 063 and 111 are retired.
- Deferred future: **FUT-029** grade-band homework player (per-tier assignment variants, attempts, states) — plan only.

### 1.4 Curriculum / tutorial content

- `Tutorials & Assets` (`tblDOTgsWfqPm18bw`): Name, Link to Video, Sort Order, Type of Asset (FBC Article Book / Tutorial / Shout Out / Informational), Associated Program (Shooting / Dribbling Challenge), Detailed/Brief Descriptions, Assignment Rationale, Athlete (shout-out), Athlete Headshot, Thumbnail, Display Image, OK to Publish on Softr, Legacy Tutorials Record ID, Migration Status. Web view `Web - Tutorials Catalog` (`web/lib/airtable/public-tables.ts`); pages `app/(program)/tutorials/page.tsx`, `tutorials/[id]/page.tsx`; presentation helpers `web/lib/data/tutorials.ts`, `tutorial-presentation.ts`; content tooling `tools/tutorials-content/`.
- Structured Curriculum tables (Curriculum Hub): `Homework Attempts` (`tblaSFVpgXW1e7Qng`) and `Homework Responses` (`tblQ1KR8l14e5FyVX`) — immutable per-attempt answer records (`web/lib/curriculum/submit-service.ts`; `web/lib/airtable/public-tables.ts`).
- Learning Activities plan (SC-018/019/020): catalog table + responses table + "counts as homework vs stand-alone" flag — built in repo, not live (`docs/learning-activities/LA-000-current-state-handoff.md`).

### 1.5 HW17 Final Reflection Quiz (`Final Reflection Quiz Submissions`)

Fillout quiz → Airtable. Fields: Enrollment, Homework Completion, Submitted At, Processing Status (Pending/Processed/Error/Needs Review), Processing Error, Coach/Admin Notes, "How did the athlete complete…" (3 options), **Q1–Q18** full question text + 4 options each, `Q# Correct?` formulas, **Score** (sum /18), **Target Score Met?** (≥10), **Quiz Result Summary** ("Score: X/18 | Target 10+ | Homework Credit | Family Discussion Bonus"), Homework 17 Credit Earned?, **Family Discussion Bonus?** (= "Worked with parent/family and discussed"), Correct Answer Distribution, Quiz Version, Homework Credit Rule, Coach Feedback lookup.
Automation **067** (`067-homework-link-or-create-completion-from-reflection-quiz.js`, v3.5) resolves the single active HW1-slot PHA whose library `Homework Number = "HW 17"` for the enrollment's PI (`resolveHw17PhaForEnrollment`), then find-or-creates an **attachment-less** HC (SC-014 Option B approved; no Quiz Result PDF). Optional attachment bridge code (`findOrCreateParentSubmission`/`ensureAssets`) retained but unused. Decision record: `docs/next-wave/homework-pipeline/QUIZ-PATH-DECISION.md`.

---

## 2. Homework completion lifecycle

### 2.1 Homework Completions table (`tblv58ppTFDBXb3nv`) — key fields

| Group | Fields |
|---|---|
| Identity | Enrollment, Homework (library), **Program Homework Assignment**, Week, Homework Completion Key (`Enrollment\|Week\|Homework`), Item Slot (HW1/HW2/Video-1/2/3), Asset Slot (HW1/HW2), Item Type (Homework / Video Review), Grade Band, Curriculum Idempotency Key, Assignment Key |
| Intake | Submission Date, Submissions - Linked, Submission Assets, Airtable Attachment (legacy), Asset Label/Type/Purpose, Source System (Fillout/Airtable/Make/Manual Upload/Other), Upload Status (Pending/Processing/Uploaded/Writeback Complete/Error), Upload Ready? (formula), Uploaded At, All Submitted Files Uploaded?, Writeback Complete?, Upload Error, Final Reflection Quiz Submissions, Notes |
| Status | **Completion Status** (Not Submitted / Submitted / Under Review / Satisfactory / Needs Revision / Not Accepted), **Review Status** (Archived / In Review / Needs Attention / New / Ready for Review / Reviewed), Review Status - Calculated, Completion Summary (formula: "Satisfactory + Extra Credit" / "Satisfactory" / Completion Status) |
| Review | Coach Feedback, Satisfactory?, Review Complete, Extra Credit?, Extra Credit XP Awarded, Reviewed By, Reviewed At, Automation Error |
| XP | Base XP Awarded, Total Homework XP Awarded (formula base+extra), Award Status (Pending/Processing/Awarded/Error/Do Not Award), XP Events, XP signature / Homework XP Reconciliation Needed? fields |
| Weekly summary | Weekly Athlete Summary Link (canonical), Weekly Athlete Summary (LEGACY text) |
| Parent email | Parent Feedback Ready?, Parent Feedback Subject, Parent Feedback Sent?, Sent On, Send Error, **Parent Feedback Delivery Status** (Pending/Sent/Delivered/Bounced/Failed/Complained/Cancelled/Unknown/Needs Review), Delivery Error, Resend Message ID, Hub Event ID |

### 2.2 Creation from uploaded assets — Automation 020 (v4.1, 2026-09-05)

File: `020-homework-link-or-create-homework-completion.js`. Trigger: Submission Assets when homework asset ready (upstream 009).

| Step | Behavior |
|---|---|
| Identity | `resolveHomeworkAssignmentIdentity`: Submission `Homework Name 1/2` hold **PHA record IDs**; slot → PHA; HC.Homework = library, HC.PHA = PHA. `validateSelectedPha` checks Active, PI ownership, library link. |
| Week | `resolveHomeworkAssignedWeekId`: **PHA.Week authoritative**; Submission.Week optional (weekless intake SC-160). |
| Match | `findHomeworkCompletionMatch`: Enrollment + PHA; fallback Enrollment + Week + Library HW. `pickPreferredHomeworkCompletion` prefers Satisfactory, then more assets. Multiple ambiguous candidates → **fail closed** (error, no create). |
| Multi-file | N assets (max 3 per Fillout form) → **one** HC; assets appended (SC-015/SC-016). |
| Timing | `resolveQualifyingSubmissionDateKey` = latest asset `Uploaded At` else Activity Date; `evaluateHomeworkSubmissionDeadline` vs PHA Due Date (fallback Week End Date; America/Denver) → `early` / `on_time` / `late` / `no_due_date` / `unknown_submission_date`. |
| Timing notes | `buildTimingSubmissionNote` writes "Late submission: …" / "Early submission: …" to HC `Notes`. Placeholder-early-then-late replacement records late. |
| Policy | **Late = full XP credit but excluded from Perfect Week** (FUT-001 late-credit, 057 v2.4+). **Early counts toward the assigned (PHA) week**, not the upload week. |
| WAS | `ensureCanonicalWasForPhaWeek`: find-or-create Weekly Athlete Summary for Enrollment + PHA.Week and link; if deferred, 033 v4.2 reconciles (068 retired). |
| Writes on create | Completion Status "Submitted", Review Status "Ready for Review", Asset Purpose "Homework Turn-In", Source System "Fillout", Item Type "Homework", Asset/Item Slot = PHA slot, Grade Band from Enrollment; asset → Pending Link + `Send to Make Trigger` (070a upload). |
| Outputs | `statusOut`, `actionOut`, `timingStatus`, `dueDateKey`, `creditEligible`, `debugStep`. |

### 2.3 Creation from reflection quiz — Automation 067 (v3.5)

Trigger: quiz row with Enrollment set, HC empty, Processing Status empty. Exact-identity validation; `markQuizReview` sets Processing Status (Processed / Error / Needs Review). Creates attachment-less HC with Item Type Homework, Source System Fillout, Completion Status Submitted, Review Status Ready for Review; links quiz row ↔ HC. WAS link deferred if none exists.

### 2.4 Creation from Structured Curriculum (Curriculum Hub) — web

- Route `web/app/api/curriculum/homework/submit/route.ts` → `web/lib/curriculum/submit-service.ts` + `submit-validation.ts`.
- Flow: `start` issues a **submit authorization token** (Redis, 4h TTL; `docs/interfaces/curriculum-hub-submit-authorization.md`) → `redeem` → `assignments` lists → `upload-staging` for file answers → `submit`.
- Resolves Enrollment and Library by `Assignment Key`; PHA by PI + Enrollment Grade Band (422 when none, 409 when multiple library rows / PHA ambiguity).
- Creates HC directly with **zero Submissions** (`buildHomeworkCompletionFields`: Completion Status "Submitted", Review Status "Ready for Review", Notes). `FORBIDDEN_HC_WRITE_FIELDS` guards review/XP fields.
- Idempotency: `Homework Attempts.Idempotency Key` and HC `Curriculum Idempotency Key`; `expectedAttemptNumber` enforced; **Needs Revision** HC permits a new attempt (new Attempt row, same HC).
- File-upload answers map to Submission Assets with Label/Slot = question key.
- 071 v4.5+ accepts HC-only topology for parent email. Audit: `docs/audits/SC-CURRICULUM-PHA-001-20260907.md`.

### 2.5 Review and XP preparation — Automation 064 (v12.2)

Gate: Coach Feedback non-blank AND Satisfactory? AND Review Complete AND Enrollment/Homework/Week/Submission Date present. Writes Base XP from XP Reward Rule `HOMEWORK_COMPLETION`, Award Status Pending, Reviewed By "Mike Schmidt" (if blank), Reviewed At; `rearmShotMilestoneCheck` re-arms Enrollment `Run Shot Milestone Check?`; `markError` → Award Status Error + Automation Error. **Does not create XP Event.**

### 2.6 XP event — Automation 065 (live v10.11)

Trigger `Homework XP Reconciliation Needed? = 1` AND `Total Homework XP Awarded > 0`. One XP Event with Source Key `HOMEWORK_XP|{hcId}`; soft-skip if total not yet positive so 064→065 re-entry works; remaps when assets merge (SC-015).

### 2.7 Weekly summary linking

020 v4.1 finds/creates canonical WAS for Enrollment + PHA.Week. **068 is retired** (file throws at runtime); 033 v4.2 owns deferred reconciliation. Perfect Week logic (057) consumes HC timing: late HCs do not satisfy Perfect Week homework requirement (`docs/audits/PERFECT-WEEK-HOMEWORK-TIMING-AUDIT-20260912.md`).

### 2.8 Parent feedback email — 078 → 071 → Hub

- **078** (native Update Record, no script): Satisfactory? + Coach Feedback → `Parent Feedback Ready?`.
- **071** (`071-…-send-homework-feedback-email-webhook.js`, v4.7): creates Email Handoff Queue row with key `HOMEWORK_FEEDBACK|HOMEWORK_COMPLETIONS|{hcId}`. Gates: Ready, not Sent, Satisfactory, Award Status **Awarded**, Coach Feedback, XP evidence (active XP Event owned by HC), PHA ownership (PI+Week+Homework+Slot), submission topology check (Submission-backed or HC-only). Asset URLs = `Reviewer File URL` only (Lambda-served).
- Payload: athleteName/First/Last, parentFirstName, assignmentTitle (public precedence), coachFeedback, totalHomeworkXpAwarded, quizSummary, submittedFiles[{id,url,label}], homeworkSlot, programName, weekName, reviewStatus "Satisfactory", submittedDate, reviewedDate, athleteProfileUrl (`/shoot/athletes/{slug}` if Public Profile Enabled), landing/shoot/homework URLs. Recipient = Enrollment `Parent Email - Cleaned` (role guardian). `testMode` strict parse, default false. Writes `Parent Feedback Subject` prep note, clears/sets `Parent Feedback Send Error`.
- **079** delivers queue → Communications Hub (separate repo) → Resend. Hub writes back `Parent Feedback Sent?`, `Sent On`, `Delivery Status`, `Resend Message ID`, `Hub Event ID` (FUT-032 complete).
- Runbook: `docs/online-agents/homework-assets/HOMEWORK-ASSET-COMPLETION-RUNBOOK.md`; flow: `docs/data-flow/homework-flow.md`.

---

## 3. Video Feedback lifecycle

### 3.1 Video Feedback table (`tblOV6pJDxQFBSQ3q`) — key fields

| Group | Fields |
|---|---|
| Identity | Video Feedback Name (`Enrollment - Week - Video Feedback`), **Video Feedback Key** (`VIDEO_FEEDBACK\|{assetId}`), Submission Asset, Submission, Enrollment, Week (lookup), Grade Band, Asset Type (Submission Video / Other) |
| Video | Video Asset File Name, **Video URL or Drive Link** (Lambda viewer URL), Video File - AWS (lookup), **Custom Video File Name**, **Confirm S3 Video Rename**, Video Asset Uploaded At, Upload Status (Pending/Processing/Uploaded/Error/Ready/No File), Writeback Complete? (Upload Status="Uploaded" AND Uploaded At set), Upload Error, Activity Date - Lkp, Auto-link Eligible? |
| Review | Coach Feedback, **Feedback Posted?**, Active?, **Do Not Award XP?**, Reviewed By, Reviewed At, **Video Feedback Workflow Status** (Needs Review / Feedback Given / Ready for XP / Completed / Review Complete) |
| XP | Base XP Awarded, Extra Credit XP Awarded, Total Video XP Awarded (0 if Do Not Award), Award Status (Pending/Awarded/Do Not Award), Ready for XP Automation?, XP Events |
| Parent email | Parent Feedback Ready?, Subject, Sent?, Sent On, Send Error, Delivery Status, Delivery Error, Hub Event ID, Resend Message ID |

### 3.2 Creation — Automation 013 (v3.2.0; sole writer)

File: `013-submission-intake-create-or-link-video-feedback.js`. Trigger: Submission Asset with Asset Slot = VIDEO and Source Attachment ID in Submission `Video Upload`.
- One Video Feedback per video asset (**up to 3 videos per Submission → 3 VF rows**). `findCandidates` by key; `assertOwnership` (asset ↔ submission ↔ enrollment); `decideGradeBandRepair` copies Enrollment Grade Band (replaces 111).
- Creates with Asset Type, Workflow Status = first available of ["Pending Upload","Pending","Ready","Processing"], Upload Status, Active?; asset → Pending Link + `Send to Make Trigger`. Outputs `readyToSendToMake` / `whyNotReadyForMake`.
- **112** (`112-…create-video-feedback-from-submission-asset.js`, v2.1) is a legacy duplicate keyed by asset record ID, routed by Upload Destination "video feedback" / Asset Purpose "video for feedback"; **must stay OFF**.

### 3.3 Upload and URL

070b sends asset payload to Make → Lambda → S3 (program-owned bucket); 070c verifies writeback and clears trigger; 022 writes `Video URL or Drive Link` = Lambda viewer URL (`*.lambda-url.us-east-2.on.aws/file/{recId}?token=`). Locked upload model: `docs/upload-workflow-homework-video.md` (max 3 files, `Video Feedback Focus/Question` on the form, `Formatted Upload Name`, `Coach Video Title`).

### 3.4 Coach rename — Automation 120 (v1.0; FUT-009)

File: `120-video-review-and-xp-apply-fut009-s3-video-rename.js`. Trigger: `Confirm S3 Video Rename` checked + valid `Custom Video File Name` + Submission Asset linked. Calls Lambda `POST /fut009/rename` (inputs recordId, lambdaRenameUrl, uploadWebhookSecret, includeAuditFields); S3 CopyObject retains original; writes back verified key; actions `renamed` / `airtable_only_recovery` / `skipped_already_named` / …; clears checkbox on success. CLI recovery `tools/airtable/fut_009_video_rename.py`.

### 3.5 XP preparation — Automation 113 (v6.5)

Skips: `video_not_active`, `feedback_not_posted`, `do_not_award_xp` (sets Award Status "Do Not Award" + disarms), `coach_feedback_missing`, invalid links (`markSourceInvalid` disarms Ready for XP Automation?). Uses exactly one canonical rule `VIDEO_SUBMISSION`. Writes Base XP, Award Status Pending, Ready for XP Automation? true, Workflow Status "Ready for XP", Reviewed By/At if blank. Re-arms only when canonical event exists but is inactive.

### 3.6 XP event — Automation 114 (v6.3)

One VF → one XP Event `VIDEO_SUBMISSION|{vfId}`; XP Source "Video Submission", XP Bucket "Video Feedback", Reason Public "Video feedback XP earned." **Retires (deactivates) the exact event when source becomes ineligible** (Active? off, Do Not Award, Feedback Posted cleared, source non-countable) and reactivates the same event on recovery; queues Enrollment `Level Recalc Needed?`. **Must trigger on both positive and withdrawal updates.** Tests: `tests/video-feedback/video-feedback-xp-mocked-runtime.test.js`.

### 3.7 Parent email — Automation 073 (v4.11)

- **No automation marks video `Parent Feedback Ready?`** — coach sets it manually (`docs/audits/video-parent-feedback-ready-workflow-audit-2026-08-17.md`), unlike homework (078).
- Handoff key `VIDEO_FEEDBACK|VIDEO_FEEDBACK|{vfId}`. Gates: Active, Feedback Posted, Ready, not Sent, Coach Feedback, canonical chain (VF key = `VIDEO_FEEDBACK|{assetId}`, asset `Is True Video Feedback Asset?`, Submission `Count This Submission?`, Week lookup), **Lambda-viewer-only URL** (`classifySecureVideoUrl` rejects Google Drive, direct/presigned S3), Activity Date not in future with **Season Sim dual gate** (`Season Sim Test Record?` + Video Upload Note contains `SEASON-SIM|` vs `Season Sim Clock Now`), XP evidence (active XP Event sum).
- Payload: athleteName, athleteFirstName, parentFirstName, coachFeedback, reviewedAt, weekName, customVideoFileName, originalFileName, displayFileName (custom → original → "Video submission"), videoUrl, videoSubmissionNote, totalVideoXpAwarded, baseXpAwarded, uploadStatus, videoAssetUploadedAt, programName, reviewStatus "Review complete", URLs, canonical IDs.
- Hub writes back Sent?/Sent On/Delivery Status/Resend Message ID/Hub Event ID.

### 3.8 Retirement / multiplicity rules

- Source ineligibility (Submission un-counted, asset no longer true video asset, VF deactivated) → 114 retires XP; 073 refuses handoff.
- Multiple videos per Submission are first-class: each file → own asset → own VF → own XP Event → own parent email.
- Video **as homework** (SC-011) is a separate purpose routing; Item Type "Video Review" exists on HC but canonical video review lives in Video Feedback.

---

## 4. Operator / coach workflows

| Surface | Detail | Cite |
|---|---|---|
| Interface "Homework Grading Queue" | `pbdR1bQlyAiRrKNJq` / page `pag1ohNraczU0PgjM`; view `HOMEWORK GRADING QUEUE - FINAL`; coach enters Coach Feedback, Satisfactory?, Extra Credit?, Review Complete | `docs/audits/SC-166-COACH-WORK-QUEUE-RULES-20260905.md`, `docs/deploy-checklists/SC-166-coach-work-queue-filters.md` |
| Interface "Video Feedback Grading" | `pbdAqKBx1VQWt4TSu` / `pagK6dWwNon0Vv6MQ`; view `Grading Video. In Order of Checkboxes`; coach watches Lambda viewer, enters Coach Feedback, Feedback Posted?, optional Custom Video File Name + Confirm S3 Video Rename, then Parent Feedback Ready? | same |
| SC-166 composite queue rules | Because `Workflow Status`/`Review Status` go stale, ACTIVE = composite of (not Sent, not Reviewed/Review Complete, Active?, has asset) and COMPLETED = (Sent? or Awarded + Review Complete). Interface fine-tuning Mike-owned/manual. | same |
| PHA setup | Operator fills PHA per PI+Week+Slot; `Operator Status` formula tells whether 033 will assign / 020 will resolve. 033 weekly assignment writes HW to WAS. | schema; `docs/automation-index.md` §Homework |
| Quiz triage | Quiz `Processing Status` = Needs Review / Error for coach intervention; Coach/Admin Notes | schema |
| Error surfaces | HC `Automation Error`, `Upload Error`, `Parent Feedback Send Error`, `Parent Feedback Delivery Status`; VF `Upload Error`, `Send Error`, duplicate-key lookups | schema |
| Asset reuse review | Automation 116 (asset reuse review) flags reused files | `docs/automation-index.md` |
| Audits / backfills | `airtable/extension-scripts/audits/` Stages A–J dry-run pipeline audits; `safe-backfills/` (e.g. `fut-009-video-rename.js`) | `airtable/extension-scripts/*/README.md` |
| Testing | Universal Testing Scenarios (SC-001, automation 115), Season Sim packages, permanent Schmidt enrollment (SC-004) | `docs/127-SI-MASTER-FUTURE-WORK-LIST.md` |

---

## 5. Public web surfaces (`/shoot`)

| Route | Purpose | Cite |
|---|---|---|
| `/shoot/homework` | Compact homework catalog by week/slot, public assignment names, durable links (SC-162) | `web/app/(program)/homework/page.tsx`, `web/lib/data/homework.ts` |
| `/shoot/homework/[id]` | Assignment detail: description, rationale, steps, resources, cover images | `web/app/(program)/homework/[id]/page.tsx`, `web/lib/data/homework-resources.ts` |
| `/shoot/api/homework/[id]/attachment/[attachmentId]` | Proxies Airtable attachments (expiring URLs) durably | route file |
| `/shoot/api/homework/[id]/link` | Durable redirect to library URL / URL Additional | route file |
| `/shoot/tutorials`, `/shoot/tutorials/[id]` | Tutorials, shout-outs, FBC articles catalog | `web/app/(program)/tutorials/*`, `web/lib/airtable/queries.ts` |
| `/shoot/athletes/[slug]` | Public athlete profile: Homework Completions, Public Missing Homework/Videos, Perfect Week Video Count, Perfect Week Homework Requirement Status, Coach Feedback (when public) | `web/lib/airtable/queries.ts`, `web/lib/data/public-athlete-homework.ts` |
| Curriculum Hub API (`/shoot/api/curriculum/{start,redeem,assignments,upload-staging,homework/submit,library/sync}`) | Token-gated structured homework submission (52 structured-enabled lessons, lesson hero, private SEO) | `web/app/api/curriculum/*`, `web/lib/curriculum/*` |

Server-side Airtable reads only (`web/lib/airtable/`); token never exposed to browser.

---

## 6. Known gaps and future ideas (from Master Future Work List + roadmap)

| ID | One-liner | Status |
|---|---|---|
| FUT-001 | HC identity by assignment (PHA), not slot; late-credit policy (full XP, no Perfect Week) | Complete |
| FUT-009 | AWS storage structure + corrected-video naming (Custom Video File Name → 120 rename) | Activated; optional secret rotation, audit fields |
| FUT-010 | Intake Submission-Asset attachment cleanup after verified S3 upload | Dry-run complete; supervised apply pending |
| FUT-014 / FUT-046 | Public assignment naming precedence (Assignment Title first) incl. Hub emails | Web shipped; Hub email pending |
| FUT-029 | Grade-band homework platform + homework intake adapter (per-tier assignment variants, attempts, states, in-app player) | **Deferred — plan only** (`docs/next-wave/homework-pipeline/FUT-029-GRADE-BAND-HOMEWORK-PLATFORM-PLAN.md`) |
| FUT-032 | HC Hub→Resend writeback (Sent?/Sent On/Delivery Status) | Complete |
| FUT-045 / SC-171 | Daily submission + homework feedback parent email presentation (071 v4.5+, athleteFirstName) | GitHub ready; paste + Hub deploy pending |
| FUT-049 | Remove PHA Grade Band (descriptive only; never scheduling) and migrate | Planning |
| FUT-051 | Unused-field cleanup (many legacy HC/VF fields) | Planning |
| FUT-054 | Player Manual + Game Manual Addendum | Outline only |
| FUT-055 | Interactive Curriculum Hub modernization (post-launch) | Plan only; Mike approval required |
| FUT-057 | Family private-profile redesign | Planning |
| SC-010 / SC-012 | PDF/document homework; written/reflection responses end-to-end | Installed; re-test |
| SC-011 | Video as homework/learning asset vs daily video purpose routing | Installed; re-test |
| SC-013 / SC-014 | Online quizzes → reviewable completion; HW17 Option B attachment-less | Live / Monitoring (do not reopen PDF path) |
| SC-015 / SC-016 | Multi-file → one HC; exactly one HC per assignment per enrollment | Complete |
| SC-018 / SC-019 / SC-020 | Learning Activities catalog + responses + "counts as homework" flag | Built in repo / Planned |
| SC-022 | XP Reward Rules cleanup (Video XP 1-vs-25 discrepancy to resolve) | Installed |
| SC-160 | Weekless asset intake + early/on-time/late timing spine (009/020/065/057) | Complete |
| SC-162 | Homework compact list + durable links | Complete |
| SC-166 | Coach active work queues (composite rules) | Mike-owned manual Interface tuning |
| Video Parent Feedback Ready | No automation sets VF `Parent Feedback Ready?`; manual coach step | Gap (audit 2026-08-17) |
| 112 / 111 / 063 / 068 / 012 | Legacy automations: OFF or deleted; files retained historically | Do not restore |

---

## 7. Non-obvious rules the new platform must preserve

1. Submission `Homework Name 1/2` store **PHA record IDs**, not library IDs; HC links both PHA and Library.
2. **PHA.Week is authoritative** for the HC week; Submission.Week is optional (weekless intake).
3. Grade Band on PHA is descriptive only; HW1/HW2 slot is routing only; **identity = Enrollment + PHA**.
4. Many files → **one** HC; ambiguous matches **fail closed**.
5. Late homework earns **full XP** but is **excluded from Perfect Week**; early homework counts toward the **assigned** week; timing is from the latest asset `Uploaded At` vs PHA Due Date (fallback Week End Date, America/Denver), written as a Notes prefix.
6. 020 find-or-creates the canonical WAS; a separate reconciler (033) handles deferred links.
7. HW17 quiz is auto-scored (18 MC, target 10+, Family Discussion Bonus) and produces an **attachment-less** HC.
8. Structured Curriculum creates HCs with **zero Submissions**, with immutable attempts/responses, idempotency keys, token-gated submit, and Needs Revision re-attempts.
9. Homework review gate = Coach Feedback + Satisfactory? + Review Complete; 064 prepares, 065 creates `HOMEWORK_XP|{hcId}`; 078 (native) marks parent-ready; 071 requires Award Status **Awarded** + XP evidence before email handoff; Hub owns Sent?/delivery writeback.
10. One Video Feedback per video file (up to 3 per Submission); key `VIDEO_FEEDBACK|{assetId}`; 013 is the sole writer.
11. Parent video links must be **Lambda viewer URLs** only (Drive/S3 rejected by 073).
12. 114 **retires/reactivates the same XP Event** when source eligibility toggles and must fire on withdrawal updates; it queues level recalc.
13. Video `Do Not Award XP?` overrides everything (Total = 0, Award Status Do Not Award).
14. Coach can rename S3 video via `Custom Video File Name` + `Confirm S3 Video Rename` (120; original retained).
15. No automation sets video `Parent Feedback Ready?` — manual step; homework has 078.
16. Coach queues use composite Active/Completed rules because status single-selects go stale.
17. Season Sim records are dual-gated (`Season Sim Test Record?` + `SEASON-SIM|` note) with a simulated clock for future-date checks.
18. Public assignment name precedence: Assignment Title → Full Name - Display → Full Name.
19. Web proxies attachments and external links through durable `/shoot/api/homework/[id]/…` routes.
20. Retired automations (012, 063, 068, 111, 112) must not be recreated; their behaviors moved into 020/013/033.
