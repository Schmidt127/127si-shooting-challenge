# System Overview

The **127 Sports Intensity Shooting Challenge** is a youth basketball shooting challenge system. Athletes enroll, submit shooting results, earn XP, advance levels, complete homework, receive video feedback, attend Zoom sessions, and get weekly summaries — with parents notified through automated email.

**Authoritative architecture pack (cold start):** [`docs/production-architecture/README.md`](./docs/production-architecture/README.md)  
**Live ops overlays:** [`docs/CURRENT-TRUTH.md`](./docs/CURRENT-TRUTH.md)  
**Final system audit:** [`docs/audits/FINAL-SYSTEM-AUDIT-REPORT-20260915.md`](./docs/audits/FINAL-SYSTEM-AUDIT-REPORT-20260915.md)

## Four production components

| Component | Identity |
|-----------|----------|
| Shooting Challenge repository | `Schmidt127/127-si-shooting-challenge` |
| Shooting Challenge Airtable | `appn84sqPw03zEbTT` |
| Communications repository | `Schmidt127/communications` |
| Communications Airtable | `appYG1t5DBRimHBCT` |

## Core modules

Enrollment · Submissions · Submission Assets · XP Events · Levels · Achievements / Streaks · Homework · Video Feedback · Zoom Attendance · Weekly Athlete Summary · Email Handoff Queue · Public website (`web/` at **`/shoot`**)

## Main data flow

```
Enrollment → Submission → XP Event → Weekly Athlete Summary
                              ↓
                    Levels / Achievements
                              ↓
              Email Handoff Queue → Automation 079
                              ↓
              Communications Hub → Resend (parent/athlete email)
```

Asset uploads (homework/video) use Make + AWS Lambda/S3 — **not** the email path.

## Development tools

| Tool | Use |
|------|-----|
| **Airtable** | System of record + automations |
| **GitHub** | Source for scripts, web, docs |
| **Cursor / ChatGPT / OMNI** | Implementation / planning / in-base ops |
| **Next.js / Vercel** | Public app at `/shoot` |
| **Communications Hub / Resend** | Parent and athlete transactional email |
| **Make.com** | Upload engine and non-email integrations only |

## Sources of truth

- **GitHub** — what should be deployed (scripts, web)  
- **Airtable Automation editor** — which script body is running  
- **SC Airtable records** — live athlete / XP / summary data  
- **Communications Hub** — delivery records and Resend sends  

Softr is **obsolete**. Make/Gmail parent email is **historical**. DEV base is **retired**.

Start at [`docs/README.md`](./docs/README.md) for the full index.
