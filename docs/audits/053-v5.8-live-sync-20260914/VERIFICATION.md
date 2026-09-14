# 053 v5.8 live Production → GitHub sync verification

**Date:** 2026-09-14  
**Automation:** 053 — Streak Occurrences Rebuild and Upsert From Submissions  
**Version:** v5.8  
**Last Updated (script):** 2026-09-13  
**Deployment marker:** SC-SEASON-SIM-001-DEPLOY-20260913B

## Hashes

| Source | SHA-256 |
|--------|---------|
| GitHub master before sync | 42b5fac78d077369b1314b8e795b5867f0a99d2c4baab30ea92286f131f54219 |
| Live Production Automation Code | bded88f5d40fc16213e70b2928dc96747537c6c4bf38002ab151521260e98dfa |
| GitHub after sync (git blob / working tree LF) | bded88f5d40fc16213e70b2928dc96747537c6c4bf38002ab151521260e98dfa |

**Exact byte match (live → GitHub after):** true

## Automations table

- Record: 
ecFpmZOqUaeUtFJQ
- Field updated: **none** — Version Number - AI Agent already 5.8 - 2026-09-13 (isStale: false)
- **Not changed:** Automation Code, trigger, conditions, Status

## Fix

Denver-safe 	oDateKey for ISO datetime strings (no UTC prefix slice) so Week End/Start boundaries do not falsely overlap — unblocks 50- and 60-day streak milestones.

## Tests

- python -m unittest tools.season_simulation.tests.test_reference_data tools.season_simulation.tests.test_sc001_expectations — **PASS (33)**
- 
ode --test tests/streak-milestone/mocked-runtime.test.js — **PASS**
- 
ode --test tests/pipeline/counted-submission-xp-standings-orchestration.test.mjs — **PASS (18)**
- Static 053 	oDateKey Week 6/7 boundary (2027-06-13T05:59Z → 2027-06-12, 2027-06-13T06:00Z → 2027-06-13) — **PASS**

## Scope

Sync only. No Production Airtable code paste, no simulation, no 035/065 changes.
