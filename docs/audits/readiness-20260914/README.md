# Multi-Agent Readiness Package — 2026-09-14

**Branch:** `audit/multi-agent-readiness-cleanup-20260914`  
**Coordinator tip (SC):** `47fe2205` (`origin/master` at audit start)  
**Simulation execute:** **NOT performed** (out of scope)  
**PR #530:** **SUPERSEDED** — do not merge, copy, or deploy

---

## 1. Current-state report

### Repositories

| System | Repo | Branch / tip at audit | Notes |
|--------|------|------------------------|-------|
| Shooting Challenge | `Schmidt127/127si-shooting-challenge` | `master` / `47fe2205` | Fast-forwarded local from `7557d099`; readiness work on feature branch |
| Curriculum Hub | `Schmidt127/127si-curriculum-hub` | local `main` was behind; **origin/main `76db1a3`** | Hub tip advanced past local `33a7d38` |

### Airtable bases (verified)

| Role | Base ID | Evidence |
|------|---------|----------|
| Shooting Challenge Production | `appn84sqPw03zEbTT` | `docs/CURRENT-TRUTH.md`, live Meta API |
| Curriculum Hub Production | `appnrW8pPpzq8Nhov` | Hub `docs/HOMEWORK_HUB_INTEGRATION_CONTRACT.md`, `docs/DATA_MODEL.md`, `src/lib/data/airtable/airtable-http.ts` |
| Communications Hub (email allowlist context) | `appYG1t5DBRimHBCT` | referenced in SC-SEASON-SIM manifests (not wiped) |

### Post-cleanup transactional truth (live re-read)

**SC Production — transactional empty except catalog Zoom Meetings:**

| Table | Count |
|-------|------:|
| Athletes | 0 |
| Enrollments | 0 |
| Submissions | 0 |
| Submission Assets | 0 |
| Homework Completions | 0 |
| Video Feedback | 0 |
| XP Events | 0 |
| Athlete Achievement Unlocks | 0 |
| Streak Occurrences | 0 |
| Weekly Athlete Summary | 0 |
| Zoom Attendance | 0 |
| Email Handoff Queue | 0 |
| Homework Attempts / Responses | 0 |
| Zoom Meetings | **2** (catalog preserved) |

Preserved Zoom Meetings: `recMFP2x5LDqea9ax` Introduction · `recb9EjQIJVzaRpZa` Motivation for a Strong Finish.

**Reference preserved (sample):** Weeks 12 · PHA 20 · Homework Library 132 · XP Reward Rules 31 · Levels 12 · Achievements 15 · Countries 194 · Automations 50.

**Curriculum Hub transactional:** Submission Outbox 0 · Homework Draft Attempts 0 · Homework Draft Responses 0. Lessons reference count 132 preserved.

**Formulas:** Meta scan found **0** `SEASON-SIM` / simulation-clock formula branches. Live formulas use normal `NOW()`/`TODAY()` samples.

Artifacts: [`live-transaction-audit.json`](./live-transaction-audit.json)

---

## 2. Production-versus-GitHub version matrix

Full matrix: [`prod-vs-github-version-matrix.json`](./prod-vs-github-version-matrix.json) · GitHub extract: [`github-automation-versions.json`](./github-automation-versions.json)

### Key scripts

| Code | GitHub | Production Automations table | Match |
|------|--------|------------------------------|-------|
| 010 | v10.14 | v10.14 Live | MATCH |
| 020 | v4.1 | v4.1 Live | MATCH |
| 034 | v3.4 | v3.4 Live | MATCH |
| **035** | **v1.3** | **v1.5 Live** | **MISMATCH (Prod ahead)** |
| **053** | **5.6** | **5.8 Live** | **MISMATCH (Prod ahead)** |
| 057 | 2.7 | 2.7 Live | MATCH |
| **065** | **v10.9** | **v10.11 Live** | **MISMATCH (Prod ahead)** |
| 066 | v4.1 | v4.1 Live | MATCH |
| 071–074, 076, 101, 114, 117 | aligned | aligned | MATCH |
| **022** | v2.2 | v2.0 Live | MISMATCH (GitHub ahead) |
| **064** | parse noise (`2026`) | v12.2 Live | review metadata parse |

**Do not paste older GitHub over Production for 035 / 053 / 065.** Sync GitHub forward from Production paste bundles before next execute.

### Open / merged PRs (SC)

| PR | State | Disposition |
|----|-------|-------------|
| **#530** | OPEN draft | **SUPERSEDED — unsafe; do not merge** |
| #531–#534 | MERGED | Season-sim 010724Z closeout + Tier-1 email paths |
| #528–#529 | MERGED | 67-day window + Perfect Week Week-End timing |

### Season-sim run IDs (historical; cleaned)

- `SEASON-SIM-2027-20260913T010724Z-threeathlete` (closeout package in `tools/season_simulation/reports/`)
- Prior SC-002 / T122531Z and 20260902\* athlete1 runs (archived reports)
- Formula rollback / lifecycle: `tools/season_simulation/formula_lifecycle.py` (snapshot + restore; read-only verify hooks)

---

## 3. Transaction classification and cleanup manifest

- Pre-delete audit + classification: [`live-transaction-audit.json`](./live-transaction-audit.json) (pre-clean snapshot overwritten by final verify — counts also in execution reports)
- Manifest: [`cleanup-manifest.json`](./cleanup-manifest.json)
- Primary delete: **926** exact IDs ([`cleanup-execution.json`](./cleanup-execution.json))
- Residual race recreations: **16** IDs ([`cleanup-execution-residual.json`](./cleanup-execution-residual.json))
- **Total deleted:** **942**
- Preserved exceptions: 2 catalog Zoom Meetings
- Mike-approved hard-stop deletes: 4 EHQ rows with `mschmidt@fairfield.k12.mt.us` (Testing Schmidt / VERIFY / FAMTEST) — approval recorded in manifest

Tools: `tools/readiness/live_transaction_audit.py`, `build_cleanup_manifest.py`, `execute_cleanup.py`

---

## 4. Cleanup execution and post-cleanup verification

| Pass | Deleted | Errors |
|------|--------:|-------:|
| Primary | 926 | 0 |
| Residual (automation race orphans) | 16 | 0 |

**Post-verify:** all disposable SC + Hub transactional tables **0**; Hub outbox/drafts **0**; EHQ **0**; formulas normal; catalog Zoom Meetings retained; Weeks/PHA/Library/Lessons intact.

---

## 5. Email-recipient safety report

| Control | Status |
|---------|--------|
| Simulation allowlist | `schmidt@fairfieldbasketballclub.com` (`tools/season_simulation/constants.py` `SAFE_EMAIL_RECIPIENT`) |
| Recipient gate | `tools/season_simulation/recipient_safety.py` |
| Live EHQ after cleanup | **0** rows (no stale send backlog) |
| Non-allowlist remnants | Removed after Mike approval (4 k12 test queue rows) |
| Normal live email producer settings | **Not changed** this task (identified only) |

Future simulation emails must continue to force the allowlist; execute remains gated.

---

## 6. XP-oracle and reconciliation-readiness report

| Capability | Status |
|------------|--------|
| Active vs raw XP | Supported via `Active?` / status filters in `business_reconciliation.actual_xp_buckets_from_events` + new checker |
| Lifetime XP vs active sum | Checker row + business gate |
| Daily / HW / Video / Threshold / PW / Zoom / Milestone buckets | `business_reconciliation` + STREAK map includes **50→90, 60→105** |
| Streak segments after missed days | Oracle uses contiguous blocks (`expectations_matrix._streaks_from_submit_days` mirrors 053) — do not assume one season-long segment |
| Duplicate Source Key | Counted in business gate + checker |
| Level/gates | `level_for` ladder; checker refuses lowering gates |
| Read-only table output | **NEW** `tools/season_simulation/reconciliation_checker.py` → Expected \| Actual \| Pass/Fail \| Evidence |
| Perfect-season oracle | Rebuilt **4980** (20 HW × 35; 10 Perfect Weeks; Zoom 90 = 1 live + 1 recording) — prior 4910 retired with 18-PHA model |

**Go for dry-run validation tooling:** YES  
**Go for claiming execute success:** NO until authorized execute + checker PASS on all enrollments

Tests: `tools/season_simulation/tests/test_reconciliation_checker.py`

---

## 7. Go / No-Go

| Area | Status | Blocking Issue | Required Action |
|------|--------|----------------|-----------------|
| Shooting Challenge data cleanup | **GO** | None | None |
| Curriculum data cleanup | **GO** | None | None |
| Formulas and automation versions | **CONDITIONAL GO** | Prod ahead of GitHub on **035 / 053 / 065**; **022** GitHub ahead of Prod | Sync GitHub←Prod for 035/053/065; decide 022 paste; do not paste older GitHub over Prod |
| Email safety | **GO** | None for queue backlog | Keep allowlist; do not change live Hub settings without separate approval |
| XP reconciliation/oracle | **GO (tooling)** | Execute not run | Use `reconciliation_checker` on next sim; require exact PASS |
| Dry-run readiness | **GO** | None | `python -m season_simulation dry-run-three` (read-only default) |
| Execute readiness | **NO-GO** | Explicit Mike phrase + confirm tokens + fresh run ID + paste sync for 035/053/065 recommended | Wait for `RUN 3-ATHLETE SEASON SIMULATION` + gates; **do not** merge PR #530 |

---

## Explicit non-actions this task

- No season simulation dry-run or execute was started as a campaign write
- No Weeks / PHA / Lessons / question banks deleted
- No merge to `master`
- PR #530 untouched (superseded)
