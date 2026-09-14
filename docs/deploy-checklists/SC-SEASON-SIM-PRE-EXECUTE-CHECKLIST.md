# Season simulation — pre-execute Email / Hub / process checklist

**Purpose:** Fail-closed checks before any email-enabled or Perfect execute.  
**Does not** read/write Airtable UI-only input variables via API.

## Required checks

| # | Check | Pass condition |
|---|--------|----------------|
| 1 | Single simulation process | No competing execute lock / only one process |
| 2 | Allowlist | Sole recipient `schmidt@fairfieldbasketballclub.com` |
| 3 | EHQ backlog | Email Handoff Queue transactional count = **0** |
| 4 | Hub backlog | Communications Hub transactional count = **0** |
| 5 | 079 `ingressSecret` | Operator **visually** attests in Airtable UI immediately before email-enabled execute (`--attest-079-ingress-secret`) |
| 6 | Producer input modes | Operator **visually** attests immediately before email-enabled execute (`--attest-producer-input-modes`) |

## Formula lifecycle (related)

| Flag | Meaning |
|------|---------|
| `gates_applied` | Season Sim gated formulas are active for the run |
| `settlement_complete` | Cascade/downstream settlement finished (900s timeout enforced) |
| `formula_restore_pending` | Production-normal restore still required |
| `production_formulas_restored` | Post-write hash verify passed (never set on dry-run alone) |
| `formula_restore_failed` | Restore attempted and verification failed |

**Restore source:** `tools/season_simulation/production_normal_formulas.json` only.  
**Recovery:** `python -m season_simulation recover-formula-restore --run-id …`

## Repo implementation

- `tools/season_simulation/pre_execute_checklist.py`
- `tools/season_simulation/simulation_process_lock.py`
- `tools/season_simulation/formula_lifecycle.py`
- `tools/season_simulation/execute_perfect.py`
