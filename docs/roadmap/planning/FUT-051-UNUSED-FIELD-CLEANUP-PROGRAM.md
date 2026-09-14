# FUT-051 — Unused-field cleanup program

**Status:** Post-launch (continues FUT-002 — plan only; **no deletes in this task**)  
**Mike approval required before implementation:** **Yes** (each deletion batch)  
**Created:** 2026-09-14

## Purpose

Run a staged, table-by-table field ownership program so unused Airtable fields are removed safely without breaking automations, web, Hub, or Interfaces.

## Prior art

- FUT-002 inventory + batch 1/2 UI deletes (2026-08-30 … 2026-09-05).  
- Tools: `tools/airtable/fut_002_field_inventory.py`; docs under `docs/audits/field-inventory/`, `docs/audits/FUT-002-*`.  
- Meta API still cannot reliably DELETE fields — **Mike UI delete** required.

## Method (required for every table)

1. **Inventory** each field (name, id, type, table).  
2. Identify **writer** (automation, Make, web API, formula, manual).  
3. Identify **readers** (automations, formulas, rollups, views, Interfaces, web/`lib/airtable`, Hub).  
4. Classify: `canonical` | `legacy` | `unused` | `uncertain` | `protected`.  
5. **protected** includes: payment, secrets, audit/evidence, Season Sim gate fields while needed, identity keys.  
6. Pipeline: **hide → observe → archive/export → delete**.  
7. Each delete batch needs an **exact field-ID manifest**, ownership proof, and **Mike approval**.

## Staging suggestion

| Stage | Tables (examples) | Goal |
|---|---|---|
| A | Submission Assets, Video Feedback stubs | Finish leftover FUT-002 candidates |
| B | Enrollment / Athlete display clutter | Hide first |
| C | WAS / XP Events debug leftovers | Uncertain → observe |
| D | Config / Levels / Achievements | Highest caution |

## Definition of done (program)

- Living inventory refreshed after each batch.  
- No silent deletes.  
- Uncertain fields never deleted without a reader re-audit.
