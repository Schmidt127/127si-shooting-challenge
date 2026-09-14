# Repository Hygiene Dry-Run Manifest — 2026-09-14

**Mode:** Read-only inventory; no branches or files were deleted.  
**Baseline:** `origin/master` at `e00295ad6c62619772e489967efb279d91f98333`  
**Policy:** [REPOSITORY-HYGIENE-RETENTION.md](../REPOSITORY-HYGIENE-RETENTION.md)

## Remote branch inventory

| Inventory result | Count | Meaning |
|---|---:|---|
| Remote refs excluding `origin/HEAD` | 431 | Inventory only; not a deletion list. |
| Refs already merged into `origin/master` | 283 | Potential candidates after PR/evidence review. |
| Refs not merged into `origin/master` | 148 | Preserve until individually resolved. |

### Candidate classes — no deletion authorized

| Candidate class | Examples | Proposed next step |
|---|---|---|
| Merged, dated Cursor work branches | `cursor/fut-039-copy-css-e772`, `cursor/pkg-037-core-certification-5f19`, `cursor/sc-149-family-dashboard-nav` | Verify merged ancestry, associated PR state, and retained evidence; then propose exact names. |
| Merged, dated overnight worker branches | `overnight/2026-07-12/worker-a-T8`, `overnight/v2-run/worker-b-s3-c024-audit-logic-tests`, `overnight/worker-d-docs` | Preserve their final reports on `master`; then propose exact names. |
| Merged audit/coordination branches | `audit/sc-152-153-pw-truth-a1`, `coord/functional-closeout-20260904`, `verify/sc-156-070a-reliability-a3` | Confirm evidence is indexed and no open PR points at the branch. |
| Unmerged/recent branches | `recover/sc-160-stage6-resume`, `docs/fut-029-grade-band-homework-platform`, `docs/sc-160-was-incident-pause` | Not candidates in this dry run. Review their PRs individually. |

Generate the full exact-name candidate manifest only after a maintainer reviews PR states:

```bash
git fetch origin --prune
git branch -r --merged origin/master \
  | sed 's#^ *origin/##' \
  | grep -vE '^(HEAD|master)$' \
  | sort
```

## Generated-artifact inventory

| Class | Examples currently tracked | Proposed retention action |
|---|---|---|
| Canonical Season Sim evidence | `docs/audits/readiness-20260914/FINAL-PASS-*`, `pre-restore-acceptance-evidence-*`, `cleanup-{manifest,execution,verify}-*` | Keep and reference from the readiness index. |
| Canonical formula evidence | production-normal formula bundle and its post-restore hash verification | Keep. |
| Historical failed-run evidence | `failure-evidence-SEASON-SIM-PERFECT-20260914T183404Z-*` | Keep with a historical label because it explains lifecycle hardening. |
| Legacy three-athlete reports | `tools/season_simulation/reports/final-production-run-SEASON-SIM-2027-20260913T010724Z-threeathlete.md`, related cleanup JSON | Preserve as historical; do not use as current run guidance. |
| One-off raw runtime state | `tools/season_simulation/run_registries/*`, process locks, `*-live.log`, `_*.py` helpers | Ignore by default; summarize results in a curated report instead. |
| Unsanitized local probes | `docs/audits/readiness-*/_scratch*/`, temporary testing probes | Ignore by default; never promote without redaction/review. |

## Explicit non-actions

- No remote branches deleted.
- No local branches or worktrees removed.
- No tracked reports moved or deleted.
- No pull requests closed.
- No Airtable, Hub, email, formula, or application changes.

## Approval gate for follow-up

Before any branch or artifact removal, create a separate exact-name manifest with: branch/path, merged/superseded proof, linked PR, evidence location on `master`, and Mike's approval. Do not use recursive deletion or bulk branch commands.

