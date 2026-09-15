# System Overview — 127 SI Shooting Challenge

**Status:** Authoritative (FUT-058 · 2026-09-15)  
**Product:** 127 Sports Intensity Shooting Challenge  
**Public app:** https://www.fairfieldbasketballclub.com/shoot

## What it is

A youth basketball shooting challenge: athletes enroll, submit daily shooting totals, complete homework, receive video feedback, attend Zoom sessions, earn XP, advance levels, unlock achievements, and receive parent emails — all driven by Airtable as the operational system of record plus a Next.js participant site.

## Four production components

| Component | Location | Role |
|-----------|----------|------|
| **Shooting Challenge repository** | GitHub `Schmidt127/127-si-shooting-challenge` | Automations source, Next.js `/shoot` app, tools, Make blueprints (non-email), docs |
| **Shooting Challenge Airtable** | Base `appn84sqPw03zEbTT` (`127SI - SHOOTING CHALLENGE GAME - NEW 5_1_2026`) | Athlete data, XP ledger, queues, automations |
| **Communications repository** | GitHub `Schmidt127/communications` (local folder often `127si-communication-hub`) | Hub ingest API, React Email templates, Resend delivery, SC source writeback |
| **Communications Airtable** | Base `appYG1t5DBRimHBCT` | Messages, Deliveries, Templates, Test Allowlist, Integration Events |

Related but **out of this audit’s “four components” core:** Curriculum Hub (`127si-curriculum-hub`, base `appnrW8pPpzq8Nhov`) for structured homework lessons; Landing (`127si-fairfield-basketball-club` / historical `hoopchallenges-landing`).

## Hosting and integrations

| Surface | Host / service |
|---------|----------------|
| Public website | Vercel project root `web/` → `/shoot` on fairfieldbasketballclub.com |
| Communications Hub API | Vercel `communications` → `https://communications-two-blue.vercel.app` |
| Asset upload | Make upload engine + AWS Lambda `127si-upload-asset` + S3 / CloudFront |
| Email | **Resend** via Communications Hub (not Make/Gmail) |
| Enrollment form | Fillout → Airtable Enrollments |
| Payments | Stripe → Make writeback (plan / activation gated — FUT-003 / FUT-053) |
| Awards | Tremendous sandbox path exists; production API pending (C-028 / FUT-004 / FUT-052) |

## Core modules (SC base)

Enrollment · Submissions · Submission Assets · Homework Completions · Video Feedback · Zoom Attendance · XP Events · Levels / Gates · Achievements / Streaks / Perfect Week / Shot Milestones · Weekly Athlete Summary · Email Handoff Queue · Config / XP Reward Rules / Program Instance · Awards

## Documentation entry

Start here: [`README.md`](./README.md) in this folder. Live ops overlays: [`../CURRENT-TRUTH.md`](../CURRENT-TRUTH.md).

## Explicitly obsolete claims (do not revive)

| Claim | Current truth |
|-------|---------------|
| Softr is the front end | **Obsolete** — Next.js `/shoot` is the public app |
| Make.com / Gmail send parent emails | **Obsolete** — Hub → Resend |
| DEV Airtable base is active | **Retired** 2026-08-19 (`appTetnuCZlCZdTCT`) |
| Production Automations table owns script versions | **False** — Automation **editor** owns versions; table owns Name/Status/Code labels only |
