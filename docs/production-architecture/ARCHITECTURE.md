# Architecture — data flows

**Status:** Authoritative (FUT-058 · 2026-09-15)

## Primary forward path

```
Athlete / Parent
    │  (Fillout enrollment · site magic-link · daily form / curriculum hub)
    ▼
Shooting Challenge App (`web/` @ /shoot)
    │  server-side Airtable reads/writes only
    ▼
Shooting Challenge Airtable (`appn84sqPw03zEbTT`)
    │  Automations 001–120 (deployed inventory)
    │  XP Events · WAS · Unlocks · Email Handoff Queue
    ▼
Automation 079 → HTTP POST Hub `/api/events/ingest`
    ▼
Communications Hub (Vercel + Airtable `appYG1t5DBRimHBCT`)
    │  Messages · Deliveries · allowlist / suppression gates
    ▼
Resend → Parent / athlete email
    │
    └──► Hub writeback → SC source Sent?/Sent On (VF / HC / WAS as configured)
```

## Reverse / supporting flows

| Flow | Direction |
|------|-----------|
| Magic-link auth email | SC `web/` → Resend directly (auth path; not Hub queue) |
| Homework / video asset upload | SC Submission Assets → **070a/070b** → Make → Lambda/S3 → writeback → **022** / **070c** |
| Curriculum structured homework | Curriculum Hub ↔ SC APIs (`CURRICULUM_*` secrets) → Homework Attempts/Responses + assets |
| Leaderboard / public profiles | SC Airtable → `web/` SSR |
| Tremendous awards | Award Recipients → Make (sandbox; keep OFF for prod API until approved) |

## Major workflow map

### Enrollment

**Trigger:** Fillout creates Enrollment → **001** find/create Athlete → **002** Grade Band → (optional) **003** grade-change refresh → Program Instance / school sync → **078A** WELCOME handoff → **079** → Hub → Resend.

### Daily submission

**Trigger:** Submission created/updated → **023** Enrollment · **005** Week · **007a** duplicate check · **021** attachment status · **009** asset create (v1.3 / SC-160, deployed) → **010** `SUBMISSION_XP` → **031** WAS · **041/042** levels · streaks **053–056** · **076** daily email handoff → **079** → Hub.

### Homework

Asset ready → **020** Homework Completion (+ WAS) → coach review → **064** prepare XP · **065** `HOMEWORK_XP` → **078** ready flag · **071** handoff → **079** → Hub → writeback Sent?.

Upload path: **070a** → Make/Lambda → **022** child writeback.

### Video feedback

Asset → **013** Video Feedback → coach grade → **113** base XP · **114** `VIDEO_SUBMISSION` XP → **073** handoff → **079** → Hub.

Upload: **070b** → Make/Lambda → **070c** verify · **022** writeback. Reuse decisions: **116**.

### Zoom

Attendance / meeting reconciliation → **101** `ZOOM_ATTEND_*` / `ZOOM_RECORDING_CREDIT` XP → levels. Recording approval email: **117** → **079** → Hub.

### Achievements / Perfect Week / milestones

Streaks **053→054→059**. Perfect Week **057→058→059**. Shot milestones + Goal Met Date **066→059**.

### Weekly summary email

Sunday **118** arms build → **072** package → **119** arms send → **074** handoff → **079** → Hub → Resend. Threshold XP: **035**.

## Deduplication pattern (universal)

One source record → one XP Event via **Source Key** text field. Formulas may expose normalized dedupe keys — scripts never write formula fields. Email: Email Handoff Queue key → Hub Message `Dedupe Key` / Delivery peer key → Resend once.

Detail: [`XP_AND_PROGRESSION.md`](./XP_AND_PROGRESSION.md) · [`COMMUNICATIONS.md`](./COMMUNICATIONS.md).
