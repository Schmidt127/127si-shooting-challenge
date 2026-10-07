# 04 — Parent/Athlete Communications, External Handoffs, and Zoom Meetings

Legacy repo: `127-si-shooting-challenge` (read-only inventory, repo is the source of truth; no live Airtable queried).
Scope: every parent/athlete email, the Email Handoff Queue / Communications Hub send plane, templates & copy rules, the Zoom meetings/attendance module, all other external integrations, operator controls, and open future work.
XP point *amounts* are intentionally **not** documented here (covered separately); only XP keys, ownership, and semantics appear where needed to explain gating.

Primary sources (cite as you go):

| Area | Files |
|---|---|
| Send-plane architecture | `docs/integrations/email-send-plane.md`, `docs/communications-hub/README.md`, `docs/CURRENT-TRUTH.md` §4–8 |
| Producer scripts | `airtable/automations/shooting-challenge/071-*.js`, `072-*.js`, `073-*.js`, `074-*.js`, `075-*.js` (retired), `076-*.js`, `077-*.js` (deleted in prod), `078A-*.js`, `079-*.js`, `117-*.js`, `118-*.js`, `119-*.js` |
| Zoom | `101-zoom-attendance-xp-award-meeting-xp.js`, `docs/pkg-034-zoom-live-attendance-architecture.md`, `docs/pkg-034-zoom-reconciliation-fields.md`, `docs/deploy-checklists/C-025-zoom-recording-design-stage12.md`, `docs/deploy-checklists/C-025-stage17-manual-airtable-actions.md`, `airtable/automations/shooting-challenge/_design-alternatives/stage17-modular-reference/`, `lib/c025-*.js`, `lib/zoom-live-attendance-lifecycle.js` |
| Schema | `airtable/schema/snapshots/prod-20260905-fut002-batch2/schema_doc_appn84sqPw03zEbTT_20260905_062812.md` (Config ~L6480, Email Handoff Queue ~L6744, Zoom Meetings ~L7665, Zoom Attendance ~L8259) |
| Copy / redesign | `docs/deploy-checklists/*-email-redesign-2026-08-22.md`, `docs/deploy-checklists/sc-parent-athlete-email-redesign-2026-09-01.md`, `docs/deploy-checklists/FUT-046-homework-feedback-subject.md`, `docs/communications-hub/WELCOME-EMAIL-INTEGRATION.md`, `docs/communications-hub/TEMPLATES-REGISTRY-AUDIT-2026-08-17.md`, `docs/roadmap/planning/FUT-056-WELCOME-EMAIL-REACT-EMAIL.md` |
| Make / other integrations | `make/blueprints/README.md`, `make/documentation/README.md`, `docs/roadmap/planning/FUT-052-REPLACE-TREMENDOUS-DECISION.md`, `web/lib/auth/magic-link-email.ts` |
| Future work | `docs/127-SI-MASTER-FUTURE-WORK-LIST.md`, `docs/roadmap/planning/FUT-049…057` |

---

## 1. Architecture overview — how an email leaves the system

### 1.1 Current (frozen baseline, 2026-09-15 / FUT-058)

```
Airtable source record (Enrollment / Submission / Homework Completion / Video Feedback /
Weekly Athlete Summary / Zoom Attendance)
        │  producer automation builds a JSON payload + recipients, creates a row
        ▼
Email Handoff Queue (Airtable table)  — Status Draft → Ready
        │  Automation 079 (the ONLY script that makes an outbound HTTP call for email)
        ▼
Communications Hub  POST https://communications-two-blue.vercel.app/api/events/ingest
   (repo Schmidt127/communications, "127si-communications-hub"; Hub Airtable base appYG1t5DBRimHBCT)
        │  Hub renders subject + HTML + text from React Email templates, dedupes on handoffKey
        ▼
Resend (provider)  ──► Resend webhooks ──► Hub /api/webhooks/resend ──► source-table writeback (Sent? / Sent On / status)
```

Key rules (from `docs/integrations/email-send-plane.md`, `docs/communications-hub/README.md`):

- **Producers never send.** Shooting-Challenge scripts only create queue rows. The Hub owns subject lines, HTML/text, branding, validation, delivery, and delivery-status writeback.
- **079 is the single egress.** Bearer secret comes from an automation input named `ingressSecret`; it is never logged or written to a field.
- **Make.com and Gmail are retired for every Shooting Challenge email** (Mike decision 2026-08-19). Script filenames still say "to Make" / "webhook" — this is historical naming only.
- **Hub `Templates` table is metadata only** — not runtime-authoritative (`TEMPLATES-REGISTRY-AUDIT-2026-08-17.md`). Runtime subject/HTML live in Hub code (`lib/template-candidate-renderer.js`, React Email components).
- **Source `Sent?` is owned by the Hub**, not by producers (FUT-032 Homework Completions, Video Feedback writeback, FUT-006 Weekly Athlete Summary writeback). Producers only set "handed off / Ready" states and clear their arming checkbox.

### 1.2 Published production versions (per `docs/integrations/email-send-plane.md` + `docs/CURRENT-TRUTH.md`)

| # | Script (short) | Version | Role |
|---|---|---|---|
| 071 | Homework feedback → queue | v4.7 | producer |
| 072 | Build weekly summary package | v4.9.4 | builder (writes WAS fields) |
| 073 | Video feedback → queue | v4.11 | producer |
| 074 | Weekly summary → queue | v3.8 | producer |
| 075 | Build welcome email (inline HTML) | — | **retired / absent in prod** (FUT-030) |
| 076 | Build daily submission package → queue | v8.17 | builder + producer |
| 077 | Daily submission → Make | v5.0 | **deleted** (retired Make path) |
| 078A | Enrollment create → welcome handoff | v1.9 | producer |
| 079 | Queue → Hub dispatcher | v2.5 | dispatcher |
| 117 | Zoom recording approval email → queue | v2.4 | producer (email only) |
| 118 | Schedule weekly build (Sun 05:00 Denver) | v2.3 | scheduler |
| 119 | Schedule weekly send (Sun 10:00 Denver) | v1.10 | scheduler |
| 101 | Zoom attendance XP reconciliation | v6.9 | XP writer (not email) |

### 1.3 Historical / retired planes (needed to understand leftover fields)

| Era | Path | Evidence |
|---|---|---|
| Make.com webhooks (2025–mid 2026) | Producer POSTs to Make webhook; Make renders/sends via Gmail; Make writes back `Sent?`, `Make Send Status`, `Sent from Make.com` | 077 v5.0 (`dailySubmission_*` payload, admin BCC/replyTo/testRecipient defaults `mschmidt@fairfield.k12.mt.us`), legacy eventId `WEEKLY_EMAIL|{enrollmentId}|{weekId}`, 117 "f" Make blueprint (sendKey `ZOOM_REC_EMAIL|…`, statuses `sent` / `already_sent`) |
| Inline HTML builders | 072 still contains a full legacy `fullHtml`/`plainText` template; 075 built `Parent Email Subject` / `Parent Email HTML` on the Enrollment | 072 CONFIG + template section; 075 BRAND/CONTACT constants and `programCopy()` |
| Lambda-only URL for video email | 073 version history: moved from Drive/Airtable attachment to Lambda/S3 (CloudFront) URL only, Season Sim gate, custom filename (FUT-008) | 073 docblock |

---

## 2. Email Handoff Queue + Automation 079

### 2.1 Email Handoff Queue table (schema snapshot ~L6744–6883)

| Field (as used by scripts) | Type | Purpose |
|---|---|---|
| Handoff Key | text (primary / unique by convention) | Deterministic dedupe key — see §2.2 |
| Event Type | single select | e.g. `WELCOME`, `DAILY_SUBMISSION`, `HOMEWORK_FEEDBACK`, `VIDEO_FEEDBACK`, `WEEKLY_ATHLETE_SUMMARY`, `ZOOM_RECORDING_APPROVAL` |
| Template Key | text/select | Hub template id (`WELCOME_SHOOTING_CHALLENGE`, `DAILY_SUBMISSION`, `HOMEWORK_FEEDBACK`, `VIDEO_FEEDBACK`, `WEEKLY_ATHLETE_SUMMARY`, `ZOOM_RECORDING_APPROVED`) — note Zoom Event Type ≠ Template Key |
| Source Table / Source Record ID | text | Pointer back to the producing record |
| Enrollment / Program Instance links (or record-id text) | link/text | Carried into envelope as `enrollmentRecordId`, `programInstanceRecordId` |
| Recipients JSON | long text | `[{role:"guardian"|"athlete", email, name}]` |
| Payload JSON | long text | Template data object (varies per type — §3) |
| Status | single select | `Draft` → `Ready` → `Sending` → `Accepted` / `Failed` / `Needs Review` |
| Attempt Count | number | incremented by 079 |
| Last Attempt At / Accepted At | dateTime | set by 079 |
| Hub Event ID | text | `eventId` returned by Hub |
| Last Error / Error | long text | truncated error body |
| Test Mode | checkbox | copied from producer `testMode` input |
| Producer Automation / Producer Version | text | provenance |

### 2.2 Deterministic Handoff Keys

| Email | Key pattern |
|---|---|
| Welcome | `WELCOME|SHOOTING_CHALLENGE|{enrollmentRecordId}` |
| Daily submission | `DAILY_SUBMISSION|SUBMISSIONS|{submissionRecordId}` |
| Homework feedback | `HOMEWORK_FEEDBACK|HOMEWORK_COMPLETIONS|{homeworkCompletionRecordId}` |
| Video feedback | `VIDEO_FEEDBACK|VIDEO_FEEDBACK|{videoFeedbackRecordId}` |
| Weekly summary | `WEEKLY_ATHLETE_SUMMARY|WEEKLY_ATHLETE_SUMMARY|{wasRecordId}` |
| Zoom recording approval | `ZOOM_RECORDING_APPROVAL|ZOOM_ATTENDANCE|{zoomAttendanceRecordId}` |

The Hub treats the key as an idempotency token: re-posting the same key returns `accepted: true` with the same `eventId` (079 reports `accepted_duplicate`).

### 2.3 Producer idempotency pattern (shared by 071 / 073 / 074 / 076 / 078A / 117)

1. Compute key; query queue for existing rows with that key.
2. `>1` existing → set own status to **Needs Review** / skip (duplicate key corruption).
3. `1` existing with identical payload (`stableJson` canonical comparison) → `existing_handoff`, skip.
4. `1` existing with different payload → **Needs Review** (never silently overwrite).
5. Re-check right before create (race guard), create row as **Draft**, then flip to **Ready** (so 079 never sees a half-written row).
6. 076 v8.15 extra: if concurrent duplicates are detected, keep the **oldest Ready** row and mark extras Needs Review.
7. `testMode` is an automation input; default **false / Live**. A strict `parseAutomationBoolean` is used so the Airtable text `"false"` is false (2026-09-14 release fix).

### 2.4 Automation 079 — dispatcher (`079-…send-queue-handoff-to-communications-hub.js` v2.5)

| Aspect | Behavior |
|---|---|
| Trigger | Queue record enters view / Status = Ready (record-triggered), input `recordId` |
| Inputs | `recordId`, `ingressSecret` (Bearer), optional base URL |
| Preconditions | Status must be `Ready`; else `skipped_not_ready` |
| Envelope | `{ schemaVersion:"1.0", sourceSystem:"SHOOTING_CHALLENGE", eventType, templateKey, handoffKey, source:{table, recordId}, enrollmentRecordId, programInstanceRecordId, recipients:[…], data:{…}, testMode }` |
| Success test | HTTP 2xx **and** body `accepted === true` **and** non-empty `eventId` |
| Status flow | Ready → Sending → Accepted (store Hub Event ID, Accepted At) |
| Failure | Failed + Last Error (status + truncated body); Attempt Count++ |
| Retry ceiling | `maxAttemptsBeforeReview: 3` → **Needs Review** after 3 failed attempts (retry = operator flips back to Ready) |
| Outputs | `statusOut`, `errorOut`, `debugStep`, `actionOut` ∈ accepted_new / accepted_duplicate / skipped_not_ready / error |
| Does NOT | mark any source record Sent (Hub does via webhook), log the secret, or re-render content |

---

## 3. Email catalog

### 3.1 Summary table

| # | Email | Producer(s) | Trigger / timing | Recipients | Template Key | Source lifecycle fields | Live? |
|---|---|---|---|---|---|---|---|
| 1 | Welcome | 078A (075 retired) | Enrollment created / `Welcome Email Status` = Pending Build | Parent (cleaned) — `Welcome Email To` | `WELCOME_SHOOTING_CHALLENGE` | `Welcome Email Status` Pending Build → Ready → Sent | Yes |
| 2 | Daily submission confirmation | 076 (077 deleted) | Submission created / ready (daily, immediate) | Parent **and** athlete (`guardian` + `athlete` roles) | `DAILY_SUBMISSION` | `Daily Email Status`, `Daily Email Handoff Key`, `Daily Email Error` | Yes |
| 3 | Weekly athlete summary | 118 → 072 → 119 → 074 | Sunday 05:00 build, Sunday 10:00 send (America/Denver) | Parent | `WEEKLY_ATHLETE_SUMMARY` | `Weekly Summary Email Status` (Not Ready / Ready for Send / Sent / Error), `Weekly Summary Email Type` (Regular / Preview / Test), `Build Weekly Email Now?`, `Send to Make?`, `Sent?` | Yes |
| 4 | Homework feedback | 071 | Coach sets feedback + arms send on Homework Completion | Parent | `HOMEWORK_FEEDBACK` | `Sent?`, `Sent On` (Hub writeback FUT-032), `Parent Feedback Delivery Status` | Yes |
| 5 | Video feedback | 073 | Coach completes Video Feedback record + arms send | Parent | `VIDEO_FEEDBACK` | `Sent?`, delivery status (Hub writeback) | Yes |
| 6 | Zoom recording approval | 117 | Coach approves a recording-quiz Zoom Attendance row | Parent | `ZOOM_RECORDING_APPROVED` | Zoom Attendance approval-email status fields | Yes (email only; XP in 101) |
| 7 | Magic-link sign-in (web) | `web/lib/auth/magic-link-email.ts` | Parent requests dashboard access | Requested parent email (test-mode redirect) | n/a (inline HTML) | none | Yes (direct Resend from Next.js) |
| 8 | Award / gift-card email | Tremendous (Make) | — | — | — | **Retired/rejected** (FUT-004/FUT-052) |
| 9 | Accomplishment / achievement emails | — | — | — | — | **Not built** (FUT-005 deferred) |
| 10 | SMS | — | — | — | — | **Not built** (Twilio listed as optional) |

### 3.2 Welcome email (078A, formerly 075)

- **Script:** `078A-…enrollment-create-welcome-email-handoff.js` v1.9. Legacy builder `075-…build-challenge-welcome-email.js` is "HISTORICAL ONLY" and is absent from production (FUT-030 reset).
- **Trigger:** Enrollment record created (or `Welcome Email Status` = Pending Build). Skips Schmidt test enrollments (`recCyFEPeATOVNlr9`, `recgP9qZYjAhE7NXm`) unless explicitly included.
- **Gating:** active enrollment; `Parent Email - Cleaned` non-empty; status not already Ready/Sent; idempotent key `WELCOME|SHOOTING_CHALLENGE|{enr}` (#126 key cutover documented in `docs/communications-hub/WELCOME-EMAIL-INTEGRATION.md`).
- **Recipients:** `buildRecipientsJson` → guardian from `Parent Email - Cleaned` (`Welcome Email To` on the Enrollment mirrors it). Parent name from `Parent First Name`/`Parent Name`.
- **Payload (`buildPayloadJson`):** athlete first/full name, parent first name, program name & instance label, start/end dates, weekly goal, daily submission URL, XP page / dashboard URL, homework URL, program-instance overrides (`Welcome - Subject Line`, `Welcome - Intro Note`, `Why This Matters`, `Welcome - Website URL`, `Daily Submission URL`), pricing fields where present, contact (coach) info.
- **Subject (Hub):** `Welcome, {Athlete Name}! — {Program Name}` (`welcome-email-redesign-2026-08-22.md`); Program Instance `Welcome - Subject Line` can override.
- **Legacy 075 behaviors worth re-implementing:** per-program copy blocks via `programCopy()` for program codes `shooting` / `dribble` / `freethrow` / `character`; info table rows (dates, goal, Zoom nights, contact); CTA buttons; TEST MODE banner when test; build blocked if `Parent Email Subject` or `Parent Email HTML` already filled (no overwrite).
- **Source lifecycle:** `Welcome Email Status` Pending Build → Ready → Sent (Sent set by Hub writeback); proof checklist in `WELCOME-EMAIL-INTEGRATION.md`.
- **Future:** FUT-056 React Email visual redesign (brief only; "do not change live producers").

### 3.3 Daily submission confirmation (076; 077 retired)

- **Script:** `076-…build-daily-submission-email-package.js` v8.17 (builder + producer in one). `077-…send-daily-submission-email-package-to-make.js` v5.0 is the retired Make sender (deleted in prod).
- **Trigger:** Submission record created / enters "ready" view (immediately after a daily submission).
- **Gating:** linked Enrollment active; parent cleaned email present; `Daily Email Status` not Sent; week resolvable; Schmidt test enrollments excluded unless simulation allowlist (`schmidt@fairfieldbasketballclub.com`).
- **Recipients:** **both** guardian and athlete roles (athlete email if present; Hub dedupes identical addresses).
- **Payload (lines ~1037–1068):** athleteName / athleteFirstName, parentFirstName, submissionDate/display, shots, makes, shootingPercentage, weeklyGoal, goal progress to date, daysLoggedThisWeek, perfectWeek daily minimum met?, streak (computed in-script), weekXp so far, level, XP earned for this submission (**with FUT-041 "XP Earned | Extra Credit" line, 076 v8.12**), homework section (assignments due / completed), game-log extra-credit tagline (FUT-031), coach-feedback quote (FUT-042), CTA URLs from `CANONICAL_URLS` (`https://www.fairfieldbasketballclub.com`, `/shoot`, `/shoot/homework`, `https://forms.fairfieldbasketballclub.com/shoot-dailysubmissions`), `buildXpPageUrl(enrollment)`.
- **Subject (Hub):** `Daily Submission for {Athlete Name} – Check Your Progress`; HTML includes logo, `Great Job, {Athlete Name}!`, scoreboard cards, homework section, `View My XP Page`, footer links, **no weekly totals block** (`daily-submission-email-redesign-2026-08-22.md`).
- **Writeback:** `Daily Email Status` (option set: Error / Ready / Sending / Sent / Sent from Make.com / Sent to Make.com — last two legacy), `Daily Email Handoff Key`, `Daily Email Error`; 076 v8.15 oldest-Ready-wins dedupe.
- **Retry:** re-arm by clearing status / flipping queue row back to Ready.

### 3.4 Weekly athlete summary (118 → 072 → 119 → 074)

| Step | Script | Schedule / trigger | What it does |
|---|---|---|---|
| Arm build | `118-…schedule-weekly-summary-email-build.js` v2.3 | Scheduled **Sunday 05:00 America/Denver** | Finds the just-ended week's WAS rows for active enrollments, sets `Build Weekly Email Now?`; inputs `dryRun`, `excludedEnrollmentIds`, `includeSchmidt`, `emptyWeekPolicy`; outputs `armedCountOut`, skipped lists. Handles SC-121 partial terminal week. |
| Build | `072-…build-weekly-summary-email-package.js` v4.9.4 | WAS `Build Weekly Email Now?` checked | Reads WAS + Enrollment + Video Feedback + Homework Completions + PHA; writes `Weekly Email Subject/HTML/Text/Payload/Recipients`, diagnostics JSON, sets `Weekly Summary Email Status` = Ready for Send, clears the arm checkbox; `skipBuild` / `suppressEmptyWeek` paths; error → Status Error + error text. |
| Arm send | `119-…schedule-weekly-summary-email-send.js` v1.10 | Scheduled **Sunday 10:00 America/Denver** | Sets `Send to Make?` on WAS rows with Status Ready for Send & not Sent; inputs `dryRun`, `sendMode`, exclusions, `includeSchmidt`. |
| Queue | `074-…send-weekly-summary-email-package-to-make.js` v3.8 | WAS `Send to Make?` checked | Gates: Ready ✓, Sent ✗, Send to Make ✓, active enrollment, parent cleaned. Creates queue row; clears `Send to Make?` and error field. |

- **Payload (074 → Hub):** athleteName, athleteFirstName, parentFirstName, weekLabel/weekName, weekDateRange, shootingDaysLogged(+Display), perfectWeekDaysLogged(+Display), daysLogged, shots, makes, weeklyGoal, goalCompletionRatio/Percent/Display, shootingPercentage, weeklyXp, currentLevel, nextLevel, streak, streakStatus, homeworkLines, packageKind (`regular` | `short_no_activity`), videoSubmissions, videosSubmittedThisWeek, weeklyVideoCount, weeklyVideoTarget, videoFeedbackStatus, zoomAttendanceStatus, perfectWeekCriteria (daily minimum, video progress, homework status, eligible flag), programName.
- **072 packageData extras (legacy inline template, still written to WAS):** xpLines, videoLines, zoomSummary (from `Zoom Meetings Summary` aiText / attendance), perfectWeekXpAmount (amount — see XP doc), level, streak.
- **Subjects:** `Weekly Shooting Challenge Summary - {Athlete Name} - {Week Label}`; empty week → `Shooting Challenge Weekly Reminder - …` (`weekly-athlete-summary-email-redesign-2026-08-22.md`). HTML: logo, `Your weekly progress is in!`, scoreboard, shooting progress, XP/level, homework when present, `View My XP Page`, Sunday-morning schedule copy, condensed footer.
- **Empty-week policy (SC-035):** `send_short` (default) | `send_normal` | `suppress` → `packageKind: short_no_activity` renders quiet-week encouragement without XP CTA.
- **Writeback:** `Weekly Summary Email Status` Not Ready / Ready for Send / Sent / Error; `Weekly Summary Email Type` Regular / Preview / Test; `Sent?` set by Hub (FUT-006 writeback contract `WEEKLY_SUMMARY_SOURCE_WRITEBACK_v1.md`, Hub `source-writeback-weekly-summary.js`; deploy checklist `FUT-006-weekly-was-hub-writeback.md`); legacy `Make Send Status` Ready / Sent.
- **Order dependency:** 034 chain builds WAS by Week Start Date order; 072 must run after weekly totals exist (it never writes rollup/formula totals).

### 3.5 Homework feedback (071)

- **Script:** `071-…send-homework-feedback-email-webhook.js` v4.7 (name is historical; it creates a queue row).
- **Trigger:** Homework Completion where coach feedback is present and the send checkbox is armed (conditions in docblock); `Sent?` unchecked.
- **Recipients:** parent only (cleaned).
- **Payload (lines ~597–625):** athleteFirstName, athleteLastName, athleteName, parentFirstName, assignmentTitle (FUT-045 precedence: **Assignment Title → Assignment Full Name - Display → Assignment Full Name**), homeworkTitle/homeworkLabel, coachFeedback (verbatim, rendered as quote FUT-042), grade/score if present, completion date, XP line, submitted-homework link (FUT-044 "View Submitted Homework" CTA), monitored contact (FUT-047), XP page URL.
- **Subject (Hub, FUT-046):** `Homework Feedback – {First Last} – {Assignment Name}`; test mode prefixes `[TEST] `; en-dash separators. Hub owns the subject; 071 must not duplicate subject logic.
- **Writeback:** Hub → `Sent?`, `Sent On` via Resend webhooks (FUT-032, Hub PR #42); `Parent Feedback Delivery Status` option set: Pending / Sent / Delivered / Bounced / Failed / Complained / Cancelled / Unknown / Needs Review.

### 3.6 Video feedback (073)

- **Script:** `073-…send-video-feedback-parent-email-webhook.js` v4.11.
- **Trigger:** Video Feedback record with coach feedback complete and send armed; Season Simulation gate (no sends for sim data unless allowlisted).
- **Recipients:** parent only.
- **Payload (lines ~709–740):** athlete names, parentFirstName, submission date / week, coachFeedback, videoUrl (**Lambda/S3 CloudFront URL only** — no Drive / attachment URLs), `Custom Video File Name` (FUT-008) as display name, corrected-video URL when present (FUT-009 rename workflow), XP line, XP page URL.
- **Subject (Hub):** `Video Feedback for {Athlete Name}` (unchanged in redesign).
- **Writeback:** Hub → `Sent?` / delivery status (`VIDEO-FEEDBACK-HUB-RESEND-WRITEBACK.md`).

### 3.7 Zoom recording approval (117)

- **Script:** `117-zoom-send-recording-approval-email-to-make.js` v2.4 — **email only**; recording XP moved into 101 v6.8 (SC-147). Earlier Make blueprint "117f" used sendKey `ZOOM_REC_EMAIL|…` with `sent` / `already_sent` statuses (`docs/deploy-checklists/117-zoom-recording-approval-email.md`).
- **Trigger:** Zoom Attendance row where `Attendance Type` = Recording, coach approval granted, approval-email arm checked, not already sent.
- **Recipients:** parent only.
- **Payload (lines ~330–380):** athlete names, parentFirstName, meeting title/date, recording-quiz submitted date, approval date, credit note (half-credit semantics text), counts toward gate note, XP page URL.
- **Handoff:** Event Type `ZOOM_RECORDING_APPROVAL`, Template Key `ZOOM_RECORDING_APPROVED`, key `ZOOM_RECORDING_APPROVAL|ZOOM_ATTENDANCE|{za}`.
- **Writeback:** approval-email status/sent fields on Zoom Attendance; XP untouched.

### 3.8 Web magic-link email (Next.js)

- `web/lib/auth/magic-link-email.ts`: posts directly to `https://api.resend.com/emails` (not via Hub). Subject `Your Shooting Challenge dashboard sign-in link`; inline HTML with orange `#FF8B00` button and `#262626` text; transports `resend` | `dev_bypass` | `test_stub`; test mode redirects every recipient to `getAthleteAuthTestRecipient()`. `web/lib/auth/parent-email.ts` provides `normalizeParentEmail` / `validateParentEmailInput` (same cleaning intent as `Parent Email - Cleaned`).

---

## 4. Recipient, safety, and test-mode rules (all producers)

| Rule | Detail |
|---|---|
| Authoritative address | `Parent Email - Cleaned` formula on Enrollments: lowercases, strips `"Name <addr>"` wrapper, quotes, trailing `,;`, whitespace. Raw `Parent Email` is **never** used for sending. `Combined Recipient Emails` and `Welcome Email To` are derived display/convenience fields. |
| Roles | `guardian` (parent) on all types; `athlete` added only by 076 (daily). 078A sends PARENT + ATHLETE roles to the same address; Hub dedupes. |
| Test enrollments | Schmidt test enrollments `recCyFEPeATOVNlr9`, `recgP9qZYjAhE7NXm` excluded by default (118/119 `includeSchmidt` input to override). |
| Simulation allowlist | Season-simulation / test sends only to `schmidt@fairfieldbasketballclub.com`. |
| testMode | Producer input, default false; strict boolean parse; copied to queue `Test Mode` and envelope; Hub prefixes `[TEST]` and may reroute. |
| Live base note | Per operating-mode rules the production base currently holds only Mike's addresses, so live sends were allowed during development. |
| Secrets | Hub ingress secret only as 079 input; Resend API key only in Hub / Vercel env; never in Airtable fields or logs. |

---

## 5. Templates, copy locations, brand rules, approved copy decisions

| Item | Where |
|---|---|
| Runtime templates (subject/HTML/text) | Communications Hub repo (`Schmidt127/communications`): `lib/template-candidate-renderer.js`, React Email components `SectionCard`, `StatPairRow`, `Badge`, `EmailHeader`, `EmailFooter`, `CoachFeedbackQuote`, `VideosSubmittedThisWeekSection` |
| Template metadata | Hub Airtable base `appYG1t5DBRimHBCT` → `Templates` (metadata only, audited `TEMPLATES-REGISTRY-AUDIT-2026-08-17.md`) |
| Legacy inline templates (reference only) | 072 `fullHtml`/`plainText`; 075 `programCopy()`, info table, buttons |
| Redesign specs (2026-08-22, consolidated 2026-09-01) | `docs/deploy-checklists/{welcome,daily-submission,weekly-athlete-summary,homework-feedback,video-feedback}-email-redesign-2026-08-22.md`, `sc-parent-athlete-email-redesign-2026-09-01.md` |
| Brand | `BRAND_STANDARDS.md`, `.cursor/rules/web-ui-brand.mdc`: blue `#0034B7`, orange `#FF8B00`, text `#262626`, surface `#F2F2F2`; **no navy** (FUT-035); logo header; condensed footer links; primarily light theme |
| Public URLs used in copy | `https://www.fairfieldbasketballclub.com/shoot` (XP page / dashboard), `/shoot/homework`, daily form `https://forms.fairfieldbasketballclub.com/shoot-dailysubmissions` |
| Copy review | `docs/copy-reviews/2026-08-30-phase4-public-pages.md` (public pages; email copy approved via redesign checklists) |

Approved copy decisions to carry forward:

- Subject formats in §3 (en-dash segments for homework; "Check Your Progress" daily; week label in weekly; empty-week "Weekly Reminder").
- Daily email has **no weekly totals**; weekly email carries Sunday-morning schedule copy.
- Coach feedback is rendered as a quotation block (FUT-042) in homework/video/daily where present.
- Assignment names use the public **Assignment Title** (FUT-045), never internal keys.
- Game Log Extra Credit tagline (FUT-031) and "XP Earned | Extra Credit" line (FUT-041) appear in daily email.
- Monitored contact line in homework email (FUT-047).
- Welcome email: per-program intro/why-this-matters overrides live on Program Instance; test banner when test mode.
- Anti-AI writing rules from `AGENTS.md` apply to all parent-facing copy.

---

## 6. Zoom meetings module

### 6.1 Tables and key fields (schema snapshot L7665–8599; Config L6480–6744)

**Zoom Meetings**

| Field | Notes |
|---|---|
| Zoom Meeting Key (primary) | deterministic id used in XP keys |
| Meeting Title / Date-Time (America/Denver) / Join Link / Passcode | display + `Upcoming Zoom Display`, `Upcoming Zoom Link` formulas consumed by web & emails |
| Program Instance (link) | scoping |
| Week (link) | ties meeting to Perfect Week calculations |
| **Attendees** (link → Enrollments) | **the live-attendance roster; linked manually by coach** (no Zoom API / CSV import exists in repo) |
| Recording URL / Recording Available? / Recording Quiz Link | recording-makeup path |
| Meeting-level overrides | `Recording Deadline Override`, `Recording Credit Percent Override`, `Requires Coach Approval Override`, etc. (C-025 Stage 17 "Meeting Override" layer) |
| Effective formulas C1–C11 | `Effective Recording Deadline`, `Effective Recording Credit %`, `Effective Requires Approval`, `Effective Counts for Gate`, `Effective Counts for Perfect Week`, … resolve Config → Program Config → Meeting Override |
| Zoom Meetings Summary (aiText) | narrative used in weekly email `zoomSummary` |
| Rollups | attendee count; `ARRAYJOIN(ARRAYUNIQUE(values), "\n")` lists |

**Zoom Attendance** (one row per enrollment × meeting credit; recording path primarily)

| Field | Notes |
|---|---|
| Primary formula | `ZOOM-ATTENDANCE-PRIMARY-FIELD-FORMULA.md` — `{Enrollment} | {Meeting} | {Type}` style key |
| Enrollment (link), Zoom Meeting (link) | identity |
| Attendance Type | `Live` / `Recording` |
| Recording Quiz Submitted At / Quiz Score / Quiz Passed? | recording intake evidence |
| Deadline fields | `Recording Deadline (Effective)`, `Past Deadline?` → view `Zoom Recording Quiz - Past Deadline` |
| Coach Approval | `Approved?` checkbox, `Approved At`, `Approved By`, `Rejected Reason` |
| Approval email | arm checkbox, status, handoff key, error (117) |
| Credit outputs | `Credit Percent (Effective)`, `Counts Toward Gate?`, `Counts Toward Perfect Week?` |

**Enrollments (Zoom-related)**

| Field | Notes |
|---|---|
| `Total Zoom Attendances` | **count of `Zoom Meetings.Attendees` backlinks — live only** |
| `Meets Gate: Zoom Meetings` | level-gate check against required Zoom count |
| `Perfect Week Zoom Requirement Status` | formula → Not Calculated / No Zoom This Week / Attended / Missed |
| `Public Missing Zoom` | parent/athlete-facing message when requirement missed |
| Nine PKG-034 reconciliation fields | `Zoom Attendance Current Signature`, `Zoom Attendance Last Reconciled Signature`, `Zoom XP Reconciliation Needed?` = `IF(AND({Current Signature},{Current}!={Last Reconciled}),1,0)`, last-reconciled timestamp, counts, error, etc. (`docs/pkg-034-zoom-reconciliation-fields.md` has prod field IDs) |

**Config** (single-row program defaults, C-025 Stage 17)

| Config key | Default |
|---|---|
| Recording makeup enabled? | on |
| Recording deadline days | **7** |
| Deadline basis | **"Later of Both"** (meeting date + N days vs recording-posted + N days) |
| Recording credit percent | **50%** |
| Requires coach approval? | on |
| Recording counts toward level gate? | on |
| Recording counts toward Perfect Week? | on (see discrepancy §6.5) |

### 6.2 Live attendance capture

1. Coach hosts the Zoom; afterward links present enrollments in `Zoom Meetings.Attendees`.
2. Linking changes the enrollment's `Zoom Attendance Current Signature`; `Zoom XP Reconciliation Needed?` flips to 1.
3. **Automation 101** (`101-zoom-attendance-xp-award-meeting-xp.js` v6.9) runs on that trigger formula and is the **sole XP writer** for Zoom:
   - live base key `ZOOM_ATTEND_BASE|{Zoom Meeting Key}|{enrollmentId}`;
   - cumulative bonus keys `ZOOM_ATTEND_BONUS_2|{enr}`, `ZOOM_ATTEND_BONUS_3|{enr}`;
   - recording key `ZOOM_RECORDING_CREDIT|{enr}|{meetingId}` (since v6.8 / SC-147);
   - idempotent: append-only XP Events, recheck before create, stores last-reconciled signature; unlink → documented lifecycle in `lib/zoom-live-attendance-lifecycle.js` (no deletion of XP; flagged for review).
4. Downstream: `Total Zoom Attendances` (live count) feeds `Meets Gate: Zoom Meetings`; 057 Perfect Week reads live Attendees; 042 re-applies gate via `Level Recalc Needed?`.

There is **no automated Zoom attendance import** (no Zoom API, no CSV parser, no Zoom MCP usage in scripts). The `Zoom` MCP namespace exists in the agent toolset but is unused by the app.

### 6.3 Recording makeup (C-025, "Stage 12 design → Stage 17 install")

Owner-approved rules (`docs/deploy-checklists/C-025-zoom-recording-design-stage12.md`, 10 rules):

1. A missed live meeting may be made up by watching the recording and submitting the recording quiz.
2. Deadline = configurable days (default 7) using "Later of Both" basis; past-deadline rows are visible in `Zoom Recording Quiz - Past Deadline` view and are not credited.
3. Coach approval required by default (per-meeting override possible).
4. Credit percent default 50% of the live credit (amount in XP doc).
5. One credit per (Enrollment, Zoom Meeting): **live wins**; a recording credit for a meeting already attended live is blocked (`lib/c025-stage17-combined-zoom-credit.js` qualifying rules).
6. Recording credit **never writes to `Attendees`** (keeps the live roster clean).
7. Recording approval triggers parent email (117) once, idempotent.
8. Gate credit: recording counts toward the Zoom level gate (042 re-applies via `Level Recalc Needed?`), but `Total Zoom Attendances` remains live-only — gate logic must union live ∪ recording.
9. Perfect Week: see §6.5 discrepancy.
10. Config precedence: Config → Program Config → Meeting Override → Effective (formulas C1–C11).

Deadline algorithm (Stage 12): `deadline = max(meetingDate, recordingPostedDate) + deadlineDays` when basis = Later of Both; alternatives: meeting-date only / recording-posted only.

Install steps: `docs/deploy-checklists/C-025-stage17-manual-airtable-actions.md` (84 manual steps: Config values, fields, views, rollups). Stage 17 modular design (`_design-alternatives/stage17-modular-reference/`, 117a normalize / 117b deadline / 117c approve / 117d credit / 117e email / orchestrator) was **never deployed** because of the Airtable automation-slot limit; production collapsed it into 101 (XP) + 117 (email) + formulas.

Recording-quiz intake path (Fillout vs Airtable form) is **not confirmed in repo** ("Mike chooses intake path").

### 6.4 Live vs recording exclusivity and gate/PW semantics

| Dimension | Live | Recording |
|---|---|---|
| Source of truth | `Zoom Meetings.Attendees` link | `Zoom Attendance` row (Type = Recording, Approved) |
| XP key | `ZOOM_ATTEND_BASE|{mtgKey}|{enr}` (+ cumulative bonuses) | `ZOOM_RECORDING_CREDIT|{enr}|{mtg}` |
| Credit | full | configurable % (default half) |
| Counts in `Total Zoom Attendances` | yes | **no** |
| Level gate | yes | yes (via gate union logic) |
| Perfect Week | yes | **policy conflict — see 6.5** |
| Parent email | none dedicated (appears in weekly summary `zoomAttendanceStatus`) | 117 approval email |
| Both for same meeting | live wins; recording credit refused / flagged |

### 6.5 Documented discrepancy to resolve in the rebuild

- `docs/127-SI-MASTER-FUTURE-WORK-LIST.md` ("Recorded Zoom meetings" section, ~L76–80) and the 101 docblock say recorded meetings **do not** count toward Perfect Week but **do** count toward level-gate advancement at half credit.
- Config default `Recording Makeup Counts for Perfect Week?` and the Stage 17 design (`lib/c025-stage17-zoom-attendance.js` DOWNSTREAM_GAPS: 057 v1.3 / 042 v3.1 to count live ∪ recording) assume recording **can** count toward Perfect Week.
- Production 057 reads only live `Attendees`, so **actual behavior = Master list policy** (no PW credit for recordings). The new platform should make this a single explicit config switch and document the chosen default.

### 6.6 Zoom in parent/athlete-facing surfaces

- Weekly email: `zoomAttendanceStatus` / `zoomSummary`; `Public Missing Zoom` message when the week's requirement is missed.
- Web: Zoom Meeting page redesign complete (FUT-017) using `Upcoming Zoom Display/Link`.
- Welcome email (legacy 075): Zoom night listed in info table from Program Instance.

---

## 7. Other integrations inventory

| Integration | Purpose | Status (as of freeze 2026-09-15) | Evidence |
|---|---|---|---|
| **Communications Hub** (Vercel, `Schmidt127/communications`) | Render + send all SC parent emails; Resend webhooks → source writeback | **Live** (Hub SHA `4485af3` at freeze) | `docs/communications-hub/README.md`, `email-send-plane.md` |
| **Resend** | Email provider for Hub and web magic links | Live | Hub; `web/lib/auth/magic-link-email.ts` |
| **Gmail (via Make)** | Former sender for weekly/daily/feedback emails | **Retired** 2026-08-19 | `CURRENT-TRUTH.md` §4 |
| **Make.com — Upload Engine** | Video/homework upload orchestration to S3 via Lambda | **Keep / live** | `make/blueprints/README.md` |
| Make — Weekly / Parent email scenarios | Old email senders | Retired | `make/documentation/README.md` |
| Make — Tremendous v1 / v2 | Gift-card award fulfillment | v1 historical, v2 **OFF**; Tremendous **rejected** as end-state (FUT-004, FUT-052, C-028 sandbox) | `docs/roadmap/planning/FUT-052-REPLACE-TREMENDOUS-DECISION.md`, `docs/integrations/tremendous-award-fulfillment.md` |
| Make — FUT-003 Fillout→Stripe stub | Registration payment | Inactive stub | `make/blueprints/README.md` |
| **AWS Lambda `upload-asset` + S3 + CloudFront** (`d21ixrrrqpqz29.cloudfront.net`) | Video & homework asset storage; FUT-009 rename worker `POST /fut009/rename`; Automation **120** triggers rename on `Confirm S3 Video Rename` | Live (FUT-009 activated 2026-09-04) | Master list FUT-009; `lambda/upload-asset/upload_core/` |
| **Fillout** | Registration form, daily submission form (`forms.fairfieldbasketballclub.com/shoot-dailysubmissions`), edit submission; CSS theme (FUT-039) | Registration live; **Fillout daily OFF** per CURRENT-TRUTH (web form primary) — verify | `CURRENT-TRUTH.md` §5, Master list ~L1707–1727 |
| **Softr** | Former parent portal | **Obsolete** | `CURRENT-TRUTH.md` |
| **Google Drive / Airtable attachments** | Former video storage | Retired in favor of S3 (SC-100 retirement strategy deferred) | 073 history, Master list ~L670 |
| **Stripe** | Registration payments, 100% coupon writeback | Live via Fillout; FUT-053 planning | `docs/roadmap/planning/FUT-053-STRIPE-COUPON-100-PERCENT-WRITEBACK.md` |
| **Zoom API** | — | **Not integrated** (manual roster) | §6.2 |
| **SMS / Twilio** | — | Not built; optional/deferred | Master list "Optional / deferred" |
| **Vercel** (web `/shoot`) | Next.js app; Resend magic links | Live | `web/` |

---

## 8. Operator (coach/admin) capabilities

| Capability | Mechanism | Script/field |
|---|---|---|
| Arm welcome email | Enrollment `Welcome Email Status` = Pending Build (auto on create) | 078A |
| Arm/resend daily email | Clear `Daily Email Status` / fix `Daily Email Error`; queue row Ready | 076, 079 |
| Build weekly email now (ad hoc / preview) | Check `Build Weekly Email Now?`; set `Weekly Summary Email Type` = Preview/Test | 072 |
| Send weekly email | Check `Send to Make?` (name legacy) | 074 |
| Scheduler dry run / exclusions | 118/119 inputs `dryRun`, `sendMode`, `excludedEnrollmentIds`, `includeSchmidt`, `emptyWeekPolicy` | 118, 119 |
| Send homework / video feedback | Coach fills feedback, checks send arm; `Sent?` prevents double send | 071, 073 |
| Approve Zoom recording + email parent | Zoom Attendance `Approved?` + approval-email arm | 117 (+101 for XP) |
| Retry a failed Hub handoff | Flip queue Status Failed/Needs Review → Ready; 079 re-posts (3 attempts then Needs Review) | 079 |
| Inspect failures | Queue `Last Error`, `Attempt Count`; source `*Email Error` fields; `Parent Feedback Delivery Status` | all |
| Test mode | Producer `testMode` input; queue `Test Mode`; Hub `[TEST]` prefix / reroute | all producers |
| Delivery audit | Hub base `appYG1t5DBRimHBCT` events + Resend logs; source `Sent On` | Hub |
| Confirm S3 video rename | Enrollment/VF `Confirm S3 Video Rename` → Automation 120 → Lambda | FUT-009 |
| Manual Zoom roster | Link enrollments in `Zoom Meetings.Attendees`; 101 reconciles | PKG-034 |

---

## 9. Known gaps and future ideas (IDs from `docs/127-SI-MASTER-FUTURE-WORK-LIST.md` and `docs/roadmap/planning/`)

| ID | Status | One line |
|---|---|---|
| FUT-004 | Deferred (P3) | Automated award emailer to replace Tremendous (define award types, recipients, dedupe, delivery status). |
| FUT-005 | Deferred (P3) | Automated accomplishment / achievement emails. |
| FUT-006 | Complete | Parent-facing email workflows for the season (Daily, Welcome, Weekly, Zoom, Video/Homework); remaining WAS writeback closed in repo, paste pending. |
| FUT-008 | Complete | `Custom Video File Name` used in parent emails/web. |
| FUT-009 | Complete | AWS storage structure + corrected-video rename (Automation 120, Lambda). |
| FUT-017 | Complete | Zoom Meeting page redesign. |
| FUT-027 | Complete | Program-wide gift-card award commitment messaging (parent FAQ). |
| FUT-029 | Deferred — do not implement | Grade-band homework platform / intake adapter. |
| FUT-032 | Complete | Homework Hub → Resend source writeback (Sent?/Sent On). |
| FUT-038 | Brief needed | Global category on/off toggle (would gate email categories). |
| FUT-040 | Brief needed | Automatic S3 migration orchestration + headshots. |
| FUT-041 / 042 / 044–047 | Complete | Daily XP Extra Credit line; coach-feedback quote; View Submitted Homework CTA; Assignment Title; homework subject; monitored contact. |
| FUT-048 | Deferred | CloudFront custom domain `homework.fairfieldbasketballclub.com`. |
| FUT-052 | Decision only | Replace Tremendous: options A–D, B = Hub/Resend "award issued" email + staff fulfillment favored. |
| FUT-053 | Planning | Stripe 100% coupon writeback. |
| FUT-056 | Post-launch brief | Welcome email visual redesign in React Email (do not change live producers). |
| FUT-057 | Planning | Family private profile (affects magic-link / parent auth emails). |
| SC-035 | Done | Empty-week weekly email policy (`send_short` default). |
| SC-121 | Done | Partial terminal week handling in 118. |
| SC-147 | Complete | Zoom recording half-XP moved into 101 v6.8; 117 email-only. |
| C-025 Stage 17 | Partially deployed | Config-driven recording makeup; modular 117a–e never deployed (slot limit). |
| Optional / deferred | — | SMS / Twilio; cosmetic polish; orchestration improvements. |
| Open (this inventory) | — | Zoom recording vs Perfect Week policy conflict (§6.5); no automated Zoom attendance import; recording-quiz intake path unconfirmed; 072 still carries dead inline template; "to Make" naming debt. |

---

## 10. Checklist for the rebuild (must-not-miss)

1. Single outbound email egress with bearer secret, idempotency keys, Draft→Ready→Sending→Accepted/Failed/Needs Review, 3-attempt ceiling, no secret logging.
2. Deterministic Handoff Keys per source record; payload-diff → Needs Review rather than overwrite.
3. Provider-webhook-driven `Sent?`/`Sent On`/delivery-status writeback to source rows (not producer-set).
4. Cleaned-parent-email formula as the only recipient source; guardian + athlete roles; test-enrollment exclusions; allowlisted simulation sends; strict testMode parsing.
5. Six live email types with the exact subjects/payload fields in §3; Hub-owned templates with shared brand components; empty-week weekly variant.
6. Sunday 05:00 build / 10:00 send schedulers with dry-run, exclusion, includeSchmidt, emptyWeekPolicy inputs and partial-terminal-week handling.
7. Zoom: manual live roster link → signature-based reconciliation → single XP writer; recording makeup with configurable deadline ("Later of Both"), credit %, coach approval, one-credit-per-meeting with live-wins, approval email; explicit Perfect Week / gate switches.
8. Program-instance-level welcome overrides (subject, intro, why-this-matters, URLs) and per-program copy variants.
9. Web magic-link email via Resend with dev-bypass / test-stub transports.
10. Retire Make/Gmail/Softr/Drive/Tremendous; keep Make Upload Engine + Lambda/S3/CloudFront + Fillout registration + Stripe.
