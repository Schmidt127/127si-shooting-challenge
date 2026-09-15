# Airtable schema — important production surfaces

**Status:** Authoritative inventory snapshot (FUT-058 · 2026-09-15)  
**Base:** Production SC `appn84sqPw03zEbTT`  
**Live MCP count:** **37 tables · 1416 fields**  
**Prior documented snapshot (FUT-002 Batch 2, 2026-09-05):** 35 tables · 1375 fields — **superseded by this live count** (Homework Attempts / Homework Responses and field growth).

`airtable/schema/current/` remains **stale** for full field maps. Prefer this overview + dated snapshots under `airtable/schema/snapshots/` + live Meta export when changing schema.

## Core transactional tables

| Table | ID | Approx fields | Role |
|-------|-----|---------------|------|
| Athletes | `tblTluxBr3DcVrh6h` | 11 | Person identity |
| Enrollments | `tbl3PFmwbRoabu1YV` | 141 | Season participation; Current Level; gates; totals |
| Submissions | `tblEVjVpGGlPTsYSt` | 116 | Daily shooting totals |
| Submission Assets | `tblhMLKxQK77agtME` | 90 | Attachments / upload / reuse |
| Homework Completions | `tblv58ppTFDBXb3nv` | 91 | Graded homework |
| Homework Attempts | `tblaSFVpgXW1e7Qng` | 12 | Curriculum Hub attempt rows |
| Homework Responses | `tblQ1KR8l14e5FyVX` | 9 | Curriculum Hub response rows |
| Video Feedback | `tblOV6pJDxQFBSQ3q` | 50 | Coach video review |
| Weekly Athlete Summary | `tbl9520d72adxlAKQ` | 111 | Weekly rollup + email package |
| XP Events | `tblmGSiNA1akW8KnU` | 55 | **XP ledger** (append-oriented; Active?) |
| Athlete Achievement Unlocks | `tblyT2AQo1JbvmvZS` | 35 | Unlocks → XP via 059 |
| Streak Occurrences | `tbl9VxLdBiNcev4He` | 22 | Streak instances |
| Zoom Meetings | `tblWcSHEm8vNNIxyB` | 94 | Meeting catalog / reconciliation |
| Zoom Attendance | `tblg8DPRu3j0dbuwi` | 53 | Per-athlete attendance |
| Email Handoff Queue | `tblQA3Evz3fNlXvD7` | 23 | SC → Hub outbound queue |
| Final Reflection Quiz Submissions | `tbl6ORxLs192mXEWp` | 55 | Reflection quiz intake |

## Configuration / catalog (do not treat as disposable)

| Table | ID | Role |
|-------|-----|------|
| Weeks | `tblcsKugv1cla36A6` | Challenge calendar (**excluded** from disposable-data deletes) |
| Grade Bands | `tblOhHrIqpjcsk2WG` | Band matching |
| Levels | `tblU6EWmc1jCpgRHe` | Level ladder |
| Level Gate Rules | `tblWIb8JCuQ842HI8` | Gate blocking for 042 |
| Achievements | `tblrADEQbvH9kBfMZ` | Achievement definitions |
| Shot Milestones | `tbl5C4TsQpOigIyRz` | Shot milestone defs |
| XP Reward Rules | `tblnTLz8eDcyi8f3j` | Amounts by event type |
| Config | `tblRB6sh77NxjS568` | Feature flags / Perfect Week mins / Drive roots |
| Target Goal Shots | `tbleCfuAt3rY8unU3` | Weekly shot goals by band + PI |
| Program Homework Assignments | `tblhA3maf7xOa8EUS` | PHA schedule (**20** active incl. Week 9 ×2 as of 2026-09-14) |
| Homework Library | `tblUuxwYlX4EQ9MKE` | Assignment library |
| Program Instance - Sync | `tblMfALZa4YYUy70P` | Multi-year PI |
| School - Synced | `tblyAJ36QvA7Wa2gU` | Schools |
| Tutorials & Assets | `tblDOTgsWfqPm18bw` | Public tutorials catalog |
| Awards / Award Recipients | `tbltlhInAQPtOB8hx` / `tblTyQXl8aEP93ubK` | Awards |
| Payment Transactions | `tblD3kluJLIgPsiFg` | Stripe writeback |
| Countries / State | geo helpers | |
| Testing Scenarios | `tblagI7Q5wXQm2XGS` | ETF (Automation 115 historical) |
| Automations | `tblfpqKqPEbkPnN8E` | **Name / Status / Automation Code labels only** — not script-version authority |

## Cross-base IDs

| Concern | ID / key |
|---------|----------|
| SC Production base | `appn84sqPw03zEbTT` |
| Communications Hub base | `appYG1t5DBRimHBCT` |
| Email Handoff Queue table | `tblQA3Evz3fNlXvD7` |
| Hub ingress identity | `SHOOTING_CHALLENGE\|{eventType}\|{handoffKey}` |

## Deduplication fields (pattern)

| Domain | Field | Owner |
|--------|-------|-------|
| XP | `Source Key` (text) | Creating automation |
| XP | XP Dedupe Key / Normalized | **Formula only — never write** |
| Unlocks | `Milestone Source Key` | 058 / 066 |
| Email | Handoff key on Email Handoff Queue | Producers 071–078A / 076 / 074 / 117 |
| Assets | Source Attachment ID | 009 |

## Schema cleanup program

Field deletion is **FUT-051** (continues FUT-002). This audit does **not** delete production fields. Candidates → **REVIEW BEFORE DELETE** in the Final Audit Report.

## Communications Hub schema (summary)

Programs · Communication Identities · Households · Contact Methods · Suppressions · Test Allowlist · Templates · Integration Events · Messages · Deliveries · Delivery Attempts · Delivery Keys · Audit Events.

Hub has **no Airtable automations** in MCP inventory (2026-09-15) — delivery is application-driven (Next.js + Resend).
