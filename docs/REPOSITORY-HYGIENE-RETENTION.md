# Repository Hygiene and Evidence Retention

**Status:** Active policy  
**Last updated:** 2026-09-14  
**Applies to:** repository branches, generated operational artifacts, and Season Simulation evidence.  
**Does not authorize:** deletion of Git branches, Git history, Airtable records, Communications Hub records, or production configuration.

## Purpose

Keep the repository useful as an operational record without treating every local probe, temporary registry, or agent work branch as permanent product documentation.

This policy complements [ARCHIVED-AND-SUPERSEDED-FILES.md](./ARCHIVED-AND-SUPERSEDED-FILES.md). Current operational truth remains in [CURRENT-TRUTH.md](./CURRENT-TRUTH.md); this policy does not replace it.

## Evidence classes

| Class | Keep in Git? | Location and handling |
|---|---|---|
| Canonical evidence | Yes | Final pass report, pre-restore acceptance, cleanup manifest/execution/verification, and production-normal formula bundle. Link it from a dated `README.md` or final report. |
| Curated operator artifact | Yes, after review | A reusable runbook, test contract, sanitized sample, or final reconciliation needed to operate or audit the app. Commit with a clear header stating status and date. |
| Historical evidence | Yes, labeled | Prior completed closeouts or meaningful incidents. Label `Historical — do not use for current operations` and link the current authority. |
| One-off probe / raw runtime output | No by default | Keep local while diagnosing; summarize its conclusion in a curated report. Do not commit raw registries, logs, temporary scripts, or ad-hoc API responses. |
| Sensitive or potentially sensitive export | No by default | Redact and place only in the approved archive if the record is genuinely required. Never commit secrets or unnecessary family data. |

## Season Simulation rules

1. Keep: the final pass/fail report, pre-restore acceptance result, exact-ID cleanup manifest/execution/verification, and the production-normal formula source bundle.
2. Archive and label: failed-run investigation reports that explain a later harness or workflow correction.
3. Do not track by default: run registries, process locks, live logs, scratch directories, and `tools/season_simulation/_*.py` session helpers.
4. To add a generated artifact intentionally, first place it in a documented evidence directory, add a one-sentence reason and retention class to its index/README, and explicitly force-add only that reviewed file if an ignore rule applies.
5. Cleanup evidence is immutable historical proof. Do not overwrite it with a later run.

## Branch retention rules

| Branch state | Action | Approval |
|---|---|---|
| `master` / protected release branch | Keep | N/A |
| Open PR or branch with unmerged commits | Keep until the PR is resolved or a maintainer confirms it is superseded | Mike/maintainer review |
| Merged branch | Candidate for deletion after 14 days, once its PR/evidence is linked from `master` | Mike approval |
| Superseded branch with no unique commits | Candidate for deletion after an explicit dry-run review | Mike approval |
| Historical evidence branch | Keep only if its evidence is not represented on `master`; otherwise archive evidence to `master` first | Mike approval |

Never bulk-delete remote branches. A branch-cleanup execution must use a reviewed exact-name manifest and a dry-run comparison against `origin/master`.

## Required dry-run checks before any cleanup

1. `git fetch origin --prune`.
2. Record the `origin/master` SHA and branch inventory date.
3. Classify every candidate as merged, superseded, open/unmerged, or protected.
4. Verify whether the branch has a corresponding open PR and whether it contains commits not reachable from `origin/master`.
5. Produce exact branch names and exact artifact paths; no globs in an execution command.
6. Obtain Mike approval for the proposed manifest. A separate execution task may then delete only approved targets.

## Ownership

- The PR author keeps temporary work local until a PR is merged or closed.
- The integrator adds reusable evidence to a current index.
- Mike approves remote branch deletion, archival moves, and any deletion of tracked material.

