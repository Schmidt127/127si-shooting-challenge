# Email send plane — current state

**Status:** Current (Production + GitHub aligned 2026-09-13 Tier-1 closeout)  
**Scope:** Shooting Challenge parent / athlete notification emails

This file owns the live **email delivery** question. All Tier-1 parent/athlete **queue producers** match GitHub `master` as of 2026-09-13. Delivery remains **test-safe** until Mike explicitly flips Live inputs per [`deploy-checklists/parent-email-and-auth-live-cutover-2026-09-03.md`](../deploy-checklists/parent-email-and-auth-live-cutover-2026-09-03.md).

---

## Current truth (2026-09-13)

| Item | State |
|------|--------|
| Who sends Shooting Challenge emails | **Resend**, through the Communications Hub |
| Make.com email | **None.** Make.com does not handle any Shooting Challenge emails. |
| Gmail Make scenarios | **Not** the current email sender. Historical only. |
| Daily submission | **076 v8.15** → **079** → Hub → Resend |
| Homework feedback | **071 v4.5** → **079** → Hub → Resend |
| Weekly summary producers | **072 v4.9.2** / **074 v3.6** → **079** → Hub → Resend |
| Video feedback | **073 v4.9** → **079** → Hub → Resend (canonical asset evidence; v4.8 fix) |
| Zoom recording approval | **117 v2.2** → **079** → Hub → Resend |
| Welcome | **078A v1.7** → **079** → Hub → Resend |
| Weekly schedule arms | **118 v2.1** (build) / **119 v1.8** (send) — retain `dryRun=true` until Live flip |
| Hub templates | Communications Hub **PR #52** merged @ **`e79637f`** |
| Automation **077** | **Retired / deleted from Production** |
| Tier 1 operator packet | [`deploy-checklists/TIER-1-LAUNCH-OPS-RUNBOOK-20260911.md`](../deploy-checklists/TIER-1-LAUNCH-OPS-RUNBOOK-20260911.md) |
| Disposable proof recipient | **`schmidt@fairfieldbasketballclub.com` only** |
| Production `Automations` table | **Authority for Name / Status / Automation Code only** — ignore stale condition/trigger columns |

Make may still run **non-email** work (upload engine, Tremendous HTTP). That is not email handling.

---

## Producer version matrix (GitHub = Production)

| Slot | Version | Paste bundle |
|------|---------|--------------|
| **076** | v8.15 | [`076-v8.15-PASTE.txt`](../deploy-checklists/076-v8.15-PASTE.txt) |
| **071** | v4.5 | [`071-v4.5-PASTE.txt`](../deploy-checklists/071-v4.5-PASTE.txt) |
| **072** | v4.9.2 | [`072-v4.9.2-PASTE.txt`](../deploy-checklists/072-v4.9.2-PASTE.txt) |
| **074** | v3.6 | [`074-v3.6-PASTE.txt`](../deploy-checklists/074-v3.6-PASTE.txt) |
| **073** | v4.9 | [`073-v4.9-PASTE.txt`](../deploy-checklists/073-v4.9-PASTE.txt) |
| **117** | v2.2 | [`117-v2.2-PASTE.txt`](../deploy-checklists/117-v2.2-PASTE.txt) |
| **078A** | v1.7 | — |
| **079** | v2.5 | — |
| **118** | v2.1 | — |
| **119** | v1.8 | — |

**073 v4.9 note:** v4.8 replaces obsolete required `Submissions.Video Upload` attachment check with canonical Submission Asset / Video Feedback evidence. v4.9 is a verification bump only; logic unchanged from v4.8.

---

## How to read older documents

| Document class | How to treat Make/Gmail email claims |
|----------------|----------------------------------------|
| This file, `PROJECT_STATE.md` overlay, `communications-hub/README.md` | Current send plane |
| 2026-07-24 weekly email E2E (`118→072→119→074→Make→Gmail`) | **Historical evidence** |
| GitHub Hub queue scripts (`071` / `073` / `074` / `076` / `079`) | Repository contract for Hub handoff |
| **VF + HC Sent?/Sent On owner:** | Communications Hub source writeback after Resend success |

---

## Related

| Doc | Role |
|-----|------|
| This file | Live email delivery authority |
| [`deploy-checklists/TIER-1-LAUNCH-OPS-RUNBOOK-20260911.md`](../deploy-checklists/TIER-1-LAUNCH-OPS-RUNBOOK-20260911.md) | Consolidated Mike operator checklist |
| [`deploy-checklists/parent-email-live-cutover-2026-09-02.md`](../deploy-checklists/parent-email-live-cutover-2026-09-02.md) | Input variables + test-safe defaults |
| [`deploy-checklists/parent-email-and-auth-live-cutover-2026-09-03.md`](../deploy-checklists/parent-email-and-auth-live-cutover-2026-09-03.md) | Live flip checklist (future) |
| [online-agents/homework-assets/HOMEWORK-ASSET-COMPLETION-RUNBOOK.md](../online-agents/homework-assets/HOMEWORK-ASSET-COMPLETION-RUNBOOK.md) | Homework/video Ready? + **071**/**073** ownership |
| [`communications-hub/README.md`](../communications-hub/README.md) | Hub event types and queue producers |
