# Final readiness report — Perfect run `SEASON-SIM-PERFECT-20260914T183404Z-mike-schmidt`

**Verdict: READY FOR NEW PERFECT SIMULATION**

Do **not** execute the next simulation until Mike reviews this report and issues the exact command below.

## Task Classification (session)

| Field | Value |
|---|---|
| Type | Production simulation failure remediation + harness hardening + exact-ID cleanup |
| Phase | 3 Implementation / 5 Close |
| Repo | `127si-shooting-challenge` |
| Scope | One failed Mike Schmidt simulation only |

## PR #541

- **Merged:** yes — https://github.com/Schmidt127/127si-shooting-challenge/pull/541
- **Merge commit:** `cefbbecb869a3c755058dde7da735449f9a8e8ef`
- **CI:** automation-contracts, python-contracts, Vercel — all SUCCESS before merge
- **Scope note:** Included WeekInfo compatibility, `run_id` contract propagation, `SEASON-SIM-PERFECT-*` Stage H support, regression tests, plus related Perfect-run readiness artifacts (T161924Z cleanup evidence, email producer UI mode docs). No Production formula/automation edits.

### Post-merge verification

- Targeted tests: `test_execute_perfect_weekinfo` (5), `test_perfect_run_harness`, `test_formula_lifecycle_stage_z`, `test_active_xp_source_key_integrity`, new `test_perfect_pre_restore_acceptance` (9) — OK

## Root cause (plain language)

The Perfect run settled far enough to look almost complete (**4,950 active XP** under Season Sim formulas) but was missing one **150% Weekly Threshold** award (30 XP). Stage Z still restored Production-normal `NOW()` formulas after settlement without requiring the **4,980 active-XP** hard gate. After restore, future-dated streak eligibility collapsed (**9 STREAK_XP → inactive**, −455), live active XP fell to **4,495**, and Week 2 WAS Goal Completion % went to **0**. That is a failed acceptance test — not a season to repair by fabricating XP or requeueing under restored formulas.

## Phase 1 — before-cleanup XP evidence

Source: `docs/audits/readiness-20260914/failure-evidence-SEASON-SIM-PERFECT-20260914T183404Z-mike-schmidt.json`

| Metric | Value |
|---|---|
| Enrollment | `rec2r1VgYEEWJBeKG` |
| Athlete | `recRrd9nLKwK4vspy` |
| Pre-restore snapshot (documented) | **4,950** |
| Live active XP after restore | **4,495** |
| Lifetime XP Earned (live) | **4,495** |
| Active events / inactive | 160 / 9 |
| Weekly Threshold active | 25 events / **450** XP (need 26 / 480) |
| Missing 150 Source Key | `WEEKLY_THRESHOLD\|rec2r1VgYEEWJBeKG\|rec7RpUMVLbcrmn4h\|150` — **absent** |
| Week 2 WAS `recYhbzze2Xc75lDa` | Goal Completion % = **0**; Threshold XP Status = Processed; Requeue = empty; present keys 100 + 125 only |
| Inactive STREAK_XP | **9** events (Source Keys + IDs in evidence JSON) |
| Formulas | Production-normal; **no SEASON-SIM branches** |
| EHQ | 94 rows; recipients **only** `schmidt@fairfieldbasketballclub.com` |

**Explicit statement:** 4,950 was the pre-restore simulation snapshot (missing 30 XP vs 4,980). Live 4,495 is post-restore ineligibility/deactivation (nine inactive streak awards). Do not fabricate the missing 30-XP event; do not requeue under restored formulas.

## Phase 3 — lifecycle hardening (this PR)

- `perfect_pre_restore_acceptance.py` — hard gate: active XP 4980, WT 26/480, Streak 9/455, shared Source Key validator, allowlist
- `execute_perfect.py` — Stage Z blocked unless settlement + business pass + pre-restore acceptance
- Cleanup of paused/failed registries requires `CONFIRM-FORCE-CLEANUP-INCOMPLETE-SEASON-SIM` (never automatic)
- Docs: `docs/deploy-checklists/SC-SEASON-SIM-PERFECT-FORMULA-LIFECYCLE.md`
- Shared `validate_active_xp_source_keys` retained in business reconciliation + reconciliation checker

## Phase 4 — exact-ID cleanup

| Artifact | Path |
|---|---|
| Manifest | `docs/audits/readiness-20260914/cleanup-manifest-SEASON-SIM-PERFECT-20260914T183404Z-mike-schmidt.json` |
| Ownership | `docs/audits/readiness-20260914/cleanup-ownership-…json` (pass; allowlist only) |
| Execution | `docs/audits/readiness-20260914/cleanup-execution-…json` |
| Verify | `docs/audits/readiness-20260914/cleanup-verify-…json` |

### Deleted counts (primary + residuals)

| Table / base | Count |
|---|---|
| Email Handoff Queue (SC) | 94 + 2 residual = **96** |
| XP Events (SC) | 169 + 3 residual = **172** |
| Athlete Achievement Unlocks | **16** |
| Streak Occurrences | **9** |
| Video Feedback | **30** |
| Homework Completions | **20** |
| Submission Assets | **55** |
| Zoom Attendance | **2** |
| Zoom Meetings (disposable only) | **2** |
| Weekly Athlete Summary | **10** |
| Submissions | **67** |
| Enrollments | **1** |
| Athletes | **1** |
| Comms Integration Events | **93** |
| Curriculum Hub transactional | **0** (already empty) |
| **Total deleted** | **574** |

### Preserved (non-simulation)

- Catalog Zoom: `recMFP2x5LDqea9ax` (Introduction), `recb9EjQIJVzaRpZa` (Motivation)
- Active PHA: **20** (including Week 9 assignments)
- Weeks / XP rules / Levels / templates / Programs / Test Allowlist / automations — untouched
- Production-normal formula hashes — match committed bundle; no SEASON-SIM text
- No active simulation lock

### Final three-base zero-state

| Base | Transactional | Status |
|---|---|---|
| Shooting Challenge `appn84sqPw03zEbTT` | Athletes…EHQ | **0** |
| Curriculum Hub `appnrW8pPpzq8Nhov` | Outbox / Drafts | **0** |
| Communications Hub `appYG1t5DBRimHBCT` | Attempts…Integration Events / Contact Methods / Identities | **0** |

Email/Hub safety: allowlist-only throughout; no producer/email sends performed in this task.

## Next simulation (Mike only — after review)

Exact single command and approval phrase:

```text
python -m season_simulation execute-perfect --execute --confirm "SEASON-SIMULATION-2027" --confirm-disposable "CONFIRM-DISPOSABLE-SEASON-SIM" --acknowledge-clock-override --enable-email-delivery --simulation-id "SEASON-SIM-PERFECT-<UTC>-mike-schmidt"
```

Approval phrase Mike should say after reviewing this report:

```text
AUTHORIZED: RUN PERFECT MIKE SCHMIDT SEASON SIMULATION
```

Do not start until formulas are confirmed Season-Sim-gated for the new run’s writer window, and producer UI modes are verified per `docs/deploy-checklists/SC-SEASON-SIM-EMAIL-PRODUCER-UI-MODES.md`.
