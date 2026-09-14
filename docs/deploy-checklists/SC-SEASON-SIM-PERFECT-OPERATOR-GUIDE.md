# Perfect Mike Schmidt season simulation — current operator guide

**Status:** historical Perfect-path acceptance is complete and cleaned. This guide is the **only current operator entrypoint** for a future authorized Perfect Mike Schmidt run.

**Current evidence:** [`FINAL-PASS-SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt.md`](../audits/readiness-20260914/FINAL-PASS-SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt.md) records a passing pre-restore acceptance of **4,980 active XP / 170 events**, followed by exact-ID cleanup. It is evidence, not a run template or an authorization to execute.

## Scope and safety

- One disposable athlete/enrollment only: **Mike Schmidt**.
- The only permitted simulation recipient is `schmidt@fairfieldbasketballclub.com`.
- Do not run a simulation, alter formula gates, or clean records without a new explicit Mike authorization.
- Production-normal formulas are the normal resting state. The exact restore source is `tools/season_simulation/production_normal_formulas.json`.
- Never use an old Stage-0 formula snapshot as a restore source.

## Lifecycle that must be followed

1. Run read-only preflight and confirm an empty transactional test plane, no execution lock, 20 active PHA (including Week 9 ×2), two catalog Zoom meetings, and no `SEASON-SIM` branch in Production-normal formulas.
2. Obtain the current explicit authorization for a new run. Use a new `SEASON-SIM-PERFECT-<UTC>-mike-schmidt` ID; never reuse a cleaned run ID.
3. Apply the row-scoped simulation gates only for the authorized run. Normal records must stay on their Production `NOW()` / `TODAY()` paths.
4. Write the run and wait for downstream settlement. The gates remain active through all reconciliation and any authorized requeue repair.
5. **Pre-restore hard acceptance:** require all of the following before Stage Z:

   | Check | Required result |
   |---|---|
   | Active XP | 4,980 |
   | Active XP events | 170 |
   | Weekly Threshold | 26 events / 480 XP |
   | Streak | 9 active events / 455 XP |
   | Source keys | No blank, whitespace, duplicate, or dual-homework active keys |
   | Recipient safety | Only `schmidt@fairfieldbasketballclub.com` |
   | Linkage | All expected records link to the simulation enrollment |

6. If any acceptance check fails, stop. Preserve formulas and records for investigation; do **not** restore formulas or clean automatically.
7. Only after a pass, Stage Z restores the exact Production-normal bundle and verifies hashes/no `SEASON-SIM` branches. Future-dated simulation rows will then become non-countable; the post-restore XP rollup is not the official result.
8. Cleanup requires separate explicit approval and an exact-ID, dependency-first manifest. Never automatically clean a failed, paused, or passing run.

## Expected post-restore behavior

For the historical 2027-dated Perfect run, the post-restore active rollup became **4,525** after the nine future-dated Streak XP events became inactive under the normal `NOW()` path. This is expected and does **not** supersede the official pre-restore pass of 4,980 / 170.

## Commands

Run from `tools/`. These examples are not authorization.

```powershell
# Read-only readiness check
python -m season_simulation preflight

# Read-only planner
python -m season_simulation execute-perfect --offline-fixture `
  --simulation-id "SEASON-SIM-PERFECT-<UTC>-mike-schmidt"

# Authorized write path — run only after a new explicit approval
python -m season_simulation execute-perfect `
  --execute `
  --confirm "SEASON-SIMULATION-2027" `
  --confirm-disposable "CONFIRM-DISPOSABLE-SEASON-SIM" `
  --acknowledge-clock-override `
  --simulation-id "SEASON-SIM-PERFECT-<UTC>-mike-schmidt"
```

Add `--enable-email-delivery` only when a new authorization includes email. Before an email-enabled run, complete the visual UI attestations described in [`SC-SEASON-SIM-PRE-EXECUTE-CHECKLIST.md`](./SC-SEASON-SIM-PRE-EXECUTE-CHECKLIST.md).

## Related documents

- Formula lifecycle detail: [`SC-SEASON-SIM-PERFECT-FORMULA-LIFECYCLE.md`](./SC-SEASON-SIM-PERFECT-FORMULA-LIFECYCLE.md)
- Email/process preflight: [`SC-SEASON-SIM-PRE-EXECUTE-CHECKLIST.md`](./SC-SEASON-SIM-PRE-EXECUTE-CHECKLIST.md)
- Historical SC-002 operator/manifest documents: retained for evidence only; each is marked historical.
- Three-athlete scenario: separate future work. It is not an alternative entrypoint for the Perfect Mike path.
