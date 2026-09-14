# 054 ISO-prefix date helper — known debt (do not paste live code)

**Automation:** 054 — Streak Occurrences create/repair STREAK_XP  
**Status:** Documented debt only — **no live paste in this task**  
**Date:** 2026-09-14

## Debt

`toDateKey` in 054 accepts an **ISO date prefix** (`YYYY-MM-DD…`) by regex and
returns the calendar date characters without converting through
America/Denver. That is sufficient for current perfect-simulation streak end
dates (ISO date or UTC noon ISO datetime), which is protected by the offline
regression in
`tools/season_simulation/tests/test_formula_lifecycle_stage_z.py`
(`Test054IsoPrefixRegression`).

## Why it matters later

If Airtable begins returning offset-local ISO strings near midnight, the
ISO-prefix branch can disagree with the Denver `Intl.DateTimeFormat` path used
for `Date` objects. A future hardening should route string datetimes through the
same Denver formatter (shared helper with 053 / 035) rather than slicing the
prefix alone.

## Out of scope for this remediation

- No GitHub logic change to 054 unless a direct Production defect is proven
- No Airtable paste
