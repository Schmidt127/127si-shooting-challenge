# SC-SEASON-SIM-001 — Closeout `010724Z` three-athlete run

**Run ID:** `SEASON-SIM-2027-20260913T010724Z-threeathlete`  
**Status:** `SIMULATION CLOSED` (2026-09-13)  
**Base:** `appn84sqPw03zEbTT`

## Scope

Disposable cleanup only for the three simulation athletes:

- `recFcH7qLPzzso9s3` (Perfect)
- `recyH8DPUKi07rkcg` (Recovery)
- `reclW1BQ9UDd6yl0z` (Edge)

## Never deleted (verified preserved)

- Separate run `114448Z` (enrollment `recNJaTAevEGQrbg9`, 19 EHQ)
- Canonical Zoom Meetings `recMFP2x5LDqea9ax`, `recb9EjQIJVzaRpZa`
- Weeks, PHA, Homework Library, Achievements, Levels, Gate Rules, automations, formulas

## Manifest

- **Total deleted:** 1,051 records
- **Manifest:** `tools/season_simulation/reports/cleanup-manifest-010724Z-final.json`
- **Execute log:** `tools/season_simulation/reports/cleanup-execute-010724Z-final.json`
- **Verify log:** `tools/season_simulation/reports/cleanup-verify-010724Z-final.json`

## Post-closeout checks (completed)

- [x] All manifest IDs deleted
- [x] Sim athletes/enrollments gone
- [x] Paginated marker rescan — 0 `010724Z` / `SEASON-SIM|` hits across 11 transactional tables (2026-09-13T18:37:17Z)
- [x] Submissions formulas Production-normal (no Season Sim branches)
- [x] No email dispatched during cleanup
- [x] `114448Z` and ordinary Production records intact

## Closeout report

`tools/season_simulation/reports/final-production-run-SEASON-SIM-2027-20260913T010724Z-threeathlete.md`
