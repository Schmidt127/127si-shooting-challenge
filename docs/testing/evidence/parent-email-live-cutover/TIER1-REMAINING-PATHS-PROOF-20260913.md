# Tier-1 Remaining Email Paths Proof — 2026-09-13

**Run marker:** `TIER1EP|2026-09-13T2238Z`  
**Base:** Production `appn84sqPw03zEbTT`  
**Enrollment:** gated disposable Testing Schmidt `recn54wbxTjygydqa`  
**Allowlisted recipient only:** `schmidt@fairfieldbasketballclub.com`

## Result: ALL THREE PATHS PASS

| Path | Source Record | Handoff Key | Recipient | Test Mode | Hub Result | Replay Duplicate Check | Cleanup Result |
| ---- | ------------- | ----------- | --------- | --------- | ---------- | ---------------------- | -------------- |
| DAILY (076) | `rec4NkAKkN2aPn1K2` | `DAILY_SUBMISSION\|SUBMISSIONS\|rec4NkAKkN2aPn1K2` | schmidt@fairfieldbasketballclub.com | true | Accepted (`rec2ZbHvssRvWHc0s`) | PASS (1→1 Accepted) | Submission marked cleaned; EHQ retained (DELETE 403) |
| HOMEWORK (071) | `recJnjHx6qMgACa4V` | `HOMEWORK_FEEDBACK\|HOMEWORK_COMPLETIONS\|recJnjHx6qMgACa4V` | schmidt@fairfieldbasketballclub.com | true | Accepted (`recAzmObnh9x3rMxk`) | PASS (1→1 Accepted) | HC disarmed; EHQ retained (DELETE 403) |
| VIDEO (073) | `recKIPPTQPLp1eh9P` | `VIDEO_FEEDBACK\|VIDEO_FEEDBACK\|recKIPPTQPLp1eh9P` | schmidt@fairfieldbasketballclub.com | true | Accepted (`recpx1TJaxsL8FHiL`) | PASS (1→1 Accepted) | VF deactivated; EHQ retained (DELETE 403) |

Evidence JSON: `TIER1EP-2026-09-13T2238Z-proof.json`

## Created record IDs (this run)

| Table | IDs |
| ----- | --- |
| Submissions | `rec4NkAKkN2aPn1K2` (daily), `recM0f7L2GemiSalx` (hw) |
| Weekly Athlete Summary | `recC2qozimwQgFnZe` (031-linked) |
| Submission Assets | `reciwfwNFb3RRPHMB` (hw), `rec8p7tQzVAglinqX` (video) |
| Homework Completions | `recJnjHx6qMgACa4V` |
| Video Feedback | `recKIPPTQPLp1eh9P` |
| XP Events | `recuGlox0BQa7DoWC` (deactivated) |
| Email Handoff Queue | `recy5i0tOK5sIvKKS`, `rec03MMbSjN5yMYXD`, `recIfD34Oyp5bYazo` |

## Safety

- Preflight: 0 real-family active enrollments; hub ready; producer versions match GitHub.
- No live family delivery enabled.
- Producer scripts not pasted or downgraded in this task.

## Cleanup / post-scan

- Run-marker submissions: **0** remaining (`Daily Email Subject` scan).
- PAT lacks DELETE on most transactional tables (403); best-effort deactivate/mark-clean applied.
- Accepted test EHQ rows **retained** as Hub handoff audit (API DELETE 403).
- Mike UI cleanup recommended for deactivated VF, disarmed HC, marked submissions/assets/WAS if desired.

## Live-mode attestation

Preflight `2026-09-13` post-sync: 076 v8.15, 071 v4.5, 072 v4.9.2, 073 v4.9, 074 v3.6, 117 v2.2, 118 v2.1, 119 v1.8 — all match GitHub, all Live.

**Mike UI confirm still required:** automation input `testMode=true` on 071/072/073/076 and `dryRun=true` on 118/119 (not API-readable).
