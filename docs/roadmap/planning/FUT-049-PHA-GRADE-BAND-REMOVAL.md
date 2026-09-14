# FUT-049 — PHA Grade Band removal and migration

**Status:** Post-launch (planning only)  
**Mike approval required before implementation:** **Yes** (especially field delete)  
**Created:** 2026-09-14

## Purpose

Remove athlete grade classification ownership from Program Homework Assignments (PHA). PHA remains the **assignment schedule row** (Program Instance + Week + Slot + library link + Active). Athlete grade comes from **Enrollment.Grade Band**. Curriculum/lesson differentiation belongs in the **Curriculum Hub** content model, not on PHA.

## Target design

| Concern | Owner after migration |
|---|---|
| Which week/slot/library is scheduled | PHA (unchanged identity) |
| Which athlete grade band applies | Enrollment.Grade Band |
| Lesson variant / interactive content by grade | Curriculum Hub assignment/content |
| Operator display of “who this row is for” | Temporary compatibility labels → then Hub |

## Dependency inventory (repo-backed, 2026-09-14)

### Runtime scheduling identity (do **not** use PHA Grade Band)

Automations **005, 020, 033, 067, 071, 065, 115** — PI + Week + Slot + Active (+ PHA RID at intake). Contracts: `tests/homework/pha-grade-band-metadata-contract.test.js`.

### Eligibility / filter readers (must be migrated or retired)

| System | Path / note |
|---|---|
| Web public athlete homework | `web/lib/data/public-athlete-homework.ts` — `phaMatchesEnrollmentGradeBand` |
| Private dashboard | `web/lib/data/private-dashboard-loader.ts` |
| Curriculum assignments / submit | `web/lib/curriculum/assignments-service.ts`, `submit-service.ts` |
| Weekly email homework block | Automation **072** filters PHA Grade Band vs enrollment |
| Season sim reference | `tools/season_simulation/reference_data.py` — `homework_covers_grade_band` |

### Operator / formula surfaces

PHA **Schedule Key** / **Operator Status** formulas historically include Grade Band RID (`docs/deploy-checklists/program-homework-assignments-mvp.md`, harden scripts). Plan replacement keys without Grade Band.

### Writers (non-production automations)

Seed/restore/backfill only (`tools/testing/seed_pha_from_curriculum.mjs`, `tools/airtable/restore_pha_18.py`, etc.). No production automation writes PHA Grade Band today.

### Make

No PHA Grade Band reads/writes (HC Grade Band only).

Full research inventory: captured in roadmap reconcile session (explore agent 2026-09-14).

## Migration sequence

1. **Freeze inventory** — dated export of every reader/writer above; add any live Interfaces/views Mike uses.  
2. **Compatibility period** — keep PHA Grade Band populated; switch web eligibility to “Enrollment Grade Band only” with optional PHA overlap as soft warning (log, do not hard-fail).  
3. **072 / email** — stop filtering by PHA Grade Band; list PHAs by PI + Week schedule only (Enrollment already scopes athlete).  
4. **Curriculum Hub** — ensure lesson differentiation uses Enrollment Grade Band + Hub content, not PHA.  
5. **Operator formulas** — rewrite Schedule Key / Operator Status without Grade Band RID; dual-run observe.  
6. **Validation** — for each active Enrollment Grade Band, confirm expected PHA set (20-row season including Week 9 ×2) still resolves; no cross-family leakage.  
7. **Hide field** in Interfaces; observe ≥1 week (or Mike-agreed window).  
8. **Archive/export** field values.  
9. **Deletion gate** — exact field-ID manifest + Mike approval → UI delete.

## Compatibility / rollback

- Keep field during compatibility; feature-flag web to old overlap filter if regressions appear.  
- Do not delete until audit proves zero hard readers.  
- Rollback = re-enable overlap filter + unhide field (values restored from export if deleted prematurely — prefer never delete until export verified).

## Data validation plan

- Count active PHA = **20** (Week 9 ×2).  
- For sample enrollments in each Grade Band, private homework list matches expected slots.  
- 072 package dry-run (allowlist) shows correct HW names.  
- No automation starts using Grade Band for scheduling identity.

## Deletion gate (Mike)

Stop. Require: production audit PASS + export stored + written approval. Meta API cannot delete fields reliably — **Mike UI delete**.

## Definition of done

- No runtime reader depends on PHA Grade Band.  
- Enrollment Grade Band is sole athlete grade authority.  
- Field deleted only after Mike gate.  
- Docs/contracts updated; conflicting “PHA owns schedule by grade” docs marked superseded.
