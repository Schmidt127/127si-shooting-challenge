# Perfect season simulation — formula lifecycle (pre-restore acceptance)

Authority for Perfect Mike Schmidt execute (`execute-perfect`).

## Rule

Season-sim row-scoped formulas stay active through:

1. Writer execution
2. Downstream automation settlement
3. All reconciliation checks
4. Any authorized requeue repair
5. Final **active XP** verification

Production-normal formulas are restored **only after** a hard pre-restore acceptance pass.

## Pre-restore acceptance (hard gate)

Must all pass before Stage Z:

| Check | Target |
|---|---|
| Active XP | **4,980** (not raw / historical totals) |
| Weekly Threshold | **26** events / **480** XP |
| Streak | **9** active events / **455** XP |
| Source Keys | No blank, whitespace, duplicate, or dual homework keys among **active** XP Events (shared `validate_active_xp_source_keys`) |
| EHQ recipients | Allowlist only (`schmidt@fairfieldbasketballclub.com`) |
| Linkage | Expected simulation records tied to the correct enrollment |

On any failure: **preserve** Season Sim formulas and records. Do **not** restore formulas automatically.

## After restore (separate safety verification)

When Mike-authorized restore proceeds after a passing gate:

- Formulas match the committed Production-normal bundle (hash check)
- No `SEASON-SIM` branch remains
- Restoration created no new records / EHQ / emails / Hub dispatches
- Future-dated simulation rows are expected to become non-countable under Production `NOW()` and **must not** be used for the final active-XP acceptance calculation (that calculation is pre-restore only)

## Cleanup

Cleanup never runs automatically after execute. Failed / incomplete / paused registries require an extra force token:

`CONFIRM-FORCE-CLEANUP-INCOMPLETE-SEASON-SIM`

Mike must explicitly authorize cleanup after reviewing evidence.

## Code

- `tools/season_simulation/perfect_pre_restore_acceptance.py`
- `tools/season_simulation/execute_perfect.py` (Stage Z gated by acceptance)
- `tools/season_simulation/confirmation.py` (`require_incomplete_cleanup_force`)
- Tests: `tools/season_simulation/tests/test_perfect_pre_restore_acceptance.py`
