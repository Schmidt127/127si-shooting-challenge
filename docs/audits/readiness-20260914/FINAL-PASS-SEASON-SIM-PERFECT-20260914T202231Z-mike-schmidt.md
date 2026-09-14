# Perfect Mike Schmidt Season Simulation — Final Report

**Run ID:** `SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt`  
**Authorization:** `AUTHORIZED: RUN PERFECT MIKE SCHMIDT SEASON SIMULATION`  
**Verdict: PASS** (pre-restore hard gate)  
**Closeout:** exact-ID cleanup authorized in this session

## Results (pre-restore hard gate — official score)

| Check | Result |
|---|---|
| Active XP | **4980** |
| Active XP Events | **170** |
| Level | **G.O.A.T.** |
| Enrollment | `recrQNLC7wX3oqbmm` |
| Athlete | Mike Schmidt (`recmTBFNWWGtCTsCx`) / `schmidt@fairfieldbasketballclub.com` |
| Submissions | 67 |
| Homework Completions | 20 |
| Video Feedback | 30 |
| Weekly Threshold | **26 events / 480 XP** |
| Perfect Week | 10 / 1000 XP |
| Streak | **9 events / 455 XP** |
| Shot Milestone | 6 / 165 XP |
| Zoom | 2 / 90 XP |
| Submission Base | 67 / 1340 XP |
| Homework XP | 20 / 700 XP |
| Video XP | 30 / 750 XP |

Durable evidence: [`pre-restore-acceptance-evidence-SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt.json`](./pre-restore-acceptance-evidence-SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt.json)

## Formula lifecycle

1. Installed Season Sim temporary gates (Meta API, exact repo text) before writer  
2. Writer + cascade completed under gated formulas  
3. Pre-restore acceptance **PASS** at **4980** (hard gate — this is the official score)  
4. Stage Z restored Production-normal formulas (bundle hash match; no SEASON-SIM branches)  
5. **After restore (EXPECTED — not a failure):** live Active XP fell to **4525** (9 future-dated STREAK_XP rows inactive under Production `NOW()`). Do **not** treat 4525 as a failed season. See [`SC-SEASON-SIM-PERFECT-FORMULA-LIFECYCLE.md`](../../deploy-checklists/SC-SEASON-SIM-PERFECT-FORMULA-LIFECYCLE.md).

## Harness defects found and fixed

Execute initially exited non-zero because reconciliation could not **see** live XP (season data was already correct at 4980):

1. XP loader requested nonexistent `Status` field → 422 swallowed → **0 events**  
2. `ARRAYJOIN({Enrollment})` returns **0 rows** in this Production base; correct filter is `{Enrollment Record ID}='rec…'`  
3. Level read used linked `Current Level` rec ids instead of public display **G.O.A.T.**  
4. Streak settlement matched XP via wrong Source Key shape; map by XP Points / date  
5. EHQ allowlist check treated raw Recipients JSON blobs as addresses  

Fixes: `tools/season_simulation/business_reconciliation.py`, `tools/season_simulation/downstream_settlement.py`  
Regression: `tools/season_simulation/tests/test_xp_enrollment_loader.py`

## Artifacts

- Closeout: [`complete-after-loader-fix-SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt.json`](./complete-after-loader-fix-SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt.json)
- Registry copy: [`SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt__athlete1-perfect.json`](./SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt__athlete1-perfect.json)
- Pre-restore evidence: [`pre-restore-acceptance-evidence-SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt.json`](./pre-restore-acceptance-evidence-SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt.json)

## Cleanup (exact-ID)

- Manifest + ownership: `cleanup-manifest-…202231Z….json` / `cleanup-ownership-…`
- Deleted **580** owned transactional IDs (576 primary + 4 residual XP Events proven via Source Key → registry HC / enrollment)
- Verify: `cleanup-verify-…202231Z….json` → **SIMULATION CLOSED — READY FOR REAL-SEASON OPERATION**
- Preserved: 2 catalog Zoom Meetings, 20 active PHA (Week 9 ×2), Production-normal formulas, Weeks/rules/automations/config
