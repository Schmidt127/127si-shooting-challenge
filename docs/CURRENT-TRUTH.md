# CURRENT TRUTH — 127 SI Shooting Challenge

**Status:** Active — primary current-state document for this repository  
**Last verification (repo):** 2026-09-15 — **FUT-058 COMPLETE — CLOSED**. Ecosystem verdict: `ECOSYSTEM PRODUCTION CLEAN — CURRENT ARCHITECTURE CLOSED`. Required production work: **NONE**. Frozen baselines: SC `c0a7eba0d62e9582a259eb6ec180745e7d58251c` · Hub `4485af3b6d89c80f2166eab09df38cc1c788b87f` — [`production-architecture/FROZEN_BASELINE_AND_FUTURE_WORK.md`](./production-architecture/FROZEN_BASELINE_AND_FUTURE_WORK.md). Architecture pack: [`production-architecture/`](./production-architecture/README.md) · audit [`audits/FINAL-SYSTEM-AUDIT-REPORT-20260915.md`](./audits/FINAL-SYSTEM-AUDIT-REPORT-20260915.md). Live MCP (closeout): **37 tables / 1416 fields**; **50** automations (**50 deployed**, incl. **009 v1.3 / SC-160**). Prior 2026-09-14: **Master roadmap reconciled** ([`MASTER_REMAINING_WORK_LIST.md`](../MASTER_REMAINING_WORK_LIST.md) · [`roadmap/README.md`](./roadmap/README.md)). **Perfect Mike Schmidt season sim PASSED** — run `SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt` — pre-restore **4,980 active XP / 170 events**; formulas restored Production-normal after acceptance; exact-ID cleanup closed (transactional zero). Evidence: [`audits/readiness-20260914/FINAL-PASS-SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt.md`](./audits/readiness-20260914/FINAL-PASS-SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt.md). Post-restore **4,525** is **expected** (future-dated streaks inactive under Production `NOW()`) — **not** a failed season. Active **PHA = 20** (incl. Week 9 ×2). **Automation version authority = Airtable Automation editor** (tracking table Name/Status/Code only — not script-version authority). **Three-athlete SC-SEASON-SIM-001 still NOT EXECUTED.** **SC-SEASON-SIM-002** CLOSED. **FUT-048** deferred. Email allowlist: **`schmidt@fairfieldbasketballclub.com`** (Live cutover = Mike policy, not an architecture defect). Prior “Perfect / three-athlete both NOT EXECUTED” and “18 PHA” launch claims are **superseded** (18 PHA = historical restore era).
**Companion release status:** [`SHOOTING_CHALLENGE_COMPLETION_MASTER.md`](./SHOOTING_CHALLENGE_COMPLETION_MASTER.md)  
**Active roadmap:** [`MASTER_REMAINING_WORK_LIST.md`](../MASTER_REMAINING_WORK_LIST.md)  
**Authority map:** [`AUTHORITY-MAP.md`](./AUTHORITY-MAP.md)  
**Integrity audit:** [`REPOSITORY-INTEGRITY-AUDIT.md`](./REPOSITORY-INTEGRITY-AUDIT.md)

> **Evidence boundary:** This file records the best repository-backed truth plus Mike-dated overlays already committed in-repo. It does **not** invent live Airtable / Make / Vercel / Tremendous UI state. Claims that need a live re-read are labeled `UNVERIFIED`, `PENDING`, or `REQUIRES LIVE CONFIRMATION`.

### Evening handoff for remote Cursor agents (2026-09-05 EOD)

| Start here | Why |
|---|---|
| [audits/EOD-BASELINE-20260905.md](./audits/EOD-BASELINE-20260905.md) | Authoritative end-of-day live-verification baseline |
| This file | Live bases, automation versions, pending queue |
| [127-SI-MASTER-FUTURE-WORK-LIST.md](./127-SI-MASTER-FUTURE-WORK-LIST.md) | Canonical future work; FUT-029/FUT-048 deferred |
| master tip | Confirm with git fetch + git rev-parse origin/master |
| Landing hub FUT-033-037 | Implement in hoopchallenges-landing, not this repo web/ |
---

## Authority rule — Automation versions (updated 2026-09-14)

> **Script / version authority:** The live, **published Airtable Automation editor / workflow deployment** (published script body + `SCRIPT` header, with UI configuration Mike attests) is the authority for the automation code actually running. The Production `Automations` **tracking table is not authoritative for script versions**.

> **Tracking-table scoped authority (historical refresh 2026-08-20):** When using the Production `Automations` data table at all, treat **only** these three columns as identity/ops metadata — never as version truth:
>
> 1. `Name`  
> 2. `Status` (Live / Off)  
> 3. `Automation Code` (label only — may lag the editor)  
>
> Do **not** use other columns on that table (trigger type, trigger table, conditions, sections, action summary, script location, external systems, etc.) as audit authority — they may still be stale.

**Prior rule (pre-refresh):** The old, unmaintained `Automations` table was non-authority. Any audit conclusion that depended on the **pre-refresh** table alone is still retracted for that era (including false Live claims for retired **077**).

### Allowed current-truth sources (only)

1. Actual, published Airtable **Automations editor / workflow deployment** (script version and code authority)  
2. Production `Automations` table columns **`Name` / `Status` / `Automation Code`** as **identity/ops labels only** (not script-version authority)  
3. Dated live-test evidence supplied by Mike  
4. Current Version 2 repository source files  
5. Current Make.com scenario configuration and blueprint (non-email planes)  
6. Current Communications Hub configuration  
7. Current website and deployment evidence  
8. Mike’s direct confirmation of what is working in Production  

Repository docs (`automation-index.md`, inventories, Completion Master) are **documentation references**. They must not override current live evidence when Mike or the Automation editor contradicts them.

**Audit artifact:** [`audits/2026-08-20-automation-49-code-audit.md`](./audits/2026-08-20-automation-49-code-audit.md)

---

## 1. Repository identity

| Item | Value |
|------|--------|
| GitHub | `Schmidt127/127-si-shooting-challenge` |
| Product | 127 Sports Intensity Shooting Challenge |
| Public app | https://www.fairfieldbasketballclub.com/shoot |
| Vercel root | `web/` |
| Production Git branch | `master` |
| Not this repo | Landing hub, JR Ref (`127-si-jr-ref`), Team Shot Tracker |

---

## 2. Git identity (verified this audit)

| Check | Result |
|-------|--------|
| **Frozen SC production baseline (FUT-058)** | `c0a7eba0d62e9582a259eb6ec180745e7d58251c` — do not treat older tips as freeze |
| **Frozen Hub production baseline (FUT-058)** | `4485af3b6d89c80f2166eab09df38cc1c788b87f` (`Schmidt127/127-communication-hub`) |
| Branch | Re-verify with `git fetch` + `git rev-parse` (docs branch may differ from `master`) |
| HEAD SHA | Re-verify after fetch — may be ahead of freeze only for approved post-freeze commits |
| `origin/master` | Re-verify after fetch |
| Ahead / behind | Re-verify after fetch |
| Recent merges (2026-09-15) | **#549** FUT-058 architecture pack / audit (`c0a7eba0`). Hub **#53** Completion Master refresh (`4485af3`). |
| Recent merges (2026-09-14) | **#545** Perfect formula lifecycle / accept gate (`4f960814`). Roadmap reconcile + Perfect pass evidence in [`MASTER_REMAINING_WORK_LIST.md`](../MASTER_REMAINING_WORK_LIST.md). Perfect closeout code/docs may also land via open Perfect cleanup PR. |
| Recent merges (2026-09-12 + 2026-09-11) | **#521** SEO footer (`94429042`) · **#520** homework attempt/response links · **#519** curriculum question-set submit auth · **#517** Tier 1 runbook (`8590c9ec`) · **#516** FUT-043 (`3703ffdc`). Email producer pastes still **pending Mike** — [`deploy-checklists/TIER-1-LAUNCH-OPS-RUNBOOK-20260911.md`](./deploy-checklists/TIER-1-LAUNCH-OPS-RUNBOOK-20260911.md). |
| Recent merges (2026-09-06 presim web + email) | **#473** email name/Zoom payloads (`4a81c0cf`) · **#472** Grade Bands / leaderboard hero / MT / FAQ (`75632e88`). Hub communications **PR #52** merged (`e79637f`). |
| Recent merges (2026-09-05 purge + SC-167 complete) | **#457** transactional purge (`ba969433`) · **#456** SC-167 complete docs (`57831fe7`) · **#455** SC-167/168/169 live-status |
| Recent merges (2026-09-05 discrepancy wave) | **#450** backlog intake · **#451** SC-168 (`fba62be0`) · **#453** SC-167 010 v10.14 (`08da8b03`) · **#452** SC-169 (`caad5ba9`). Wave: [`audits/SC-167-168-169-DISCREPANCY-WAVE-CLOSEOUT-20260905.md`](./audits/SC-167-168-169-DISCREPANCY-WAVE-CLOSEOUT-20260905.md) |
| Recent merges (2026-09-05 completion wave) | **#435** A1 truth (`7c63dd00`) · **#440** SC-161 (`0eb1ed28`) · **#438** SC-163 repo (`43d353a4`) · **#437** SC-162 (`f8a1c9ee`) · **#439** SC-164/165 (`9869a2eb`) · **#436** SC-166 (`bd0198a4`) · **#444** SC-163 066 v4.1 live closeout (`480771fc`) · **#446** dual-enrollment cleanup (`58663cfd`) · **#447** Season Sim preflight (`2131f7d5`) · **#448** Master List reconciliation (`3cf3b568`). Evidence: [`audits/SC-163-LIVE-VERIFICATION-CLOSEOUT-20260905.md`](./audits/SC-163-LIVE-VERIFICATION-CLOSEOUT-20260905.md) · [`audits/SC-WAVE-20260905-CLOSEOUT.md`](./audits/SC-WAVE-20260905-CLOSEOUT.md) · [`audits/MASTER-LIST-RECONCILIATION-20260905.md`](./audits/MASTER-LIST-RECONCILIATION-20260905.md) |
| Recent merges (2026-09-04 SF + reliability) | **#411** SC-156 · **#410/#409/#408** SC-153 · **#407** SF closeout · **#406** SC-152/153 · **#404** SC-154/155/156 · **#401** SC-157 closes **#340** · **#398** SC-147 · **#399** SEO · **#397** FUT-025 · **#396** SC-148 · **#395** SC-057/058 |
| Open PRs | Re-verify with `gh pr list` — do not assume none. |
| Recent merges (2026-08-31) | **#312** multi-asset HW / 065 XP closeout |
| Recent merges (2026-08-30) | **#311** gift-card/coach · **#308** public-app readiness · **#298** public copy · **#276** ATHWF · **#297** paste audit |
| Prior integrity ship | `0b1d634…` (2026-08-20); XP activity ledger merge follows |
| True merge markers (`<<<<<<<`) | None found |
| Nested clone (ignored) | Local folder `127-si-shooting-challenge/` — gitignored; **do not treat as source of truth** |

Re-verify before relying on SHA:

```powershell
git fetch origin
git rev-parse HEAD origin/master
git status -sb
```

---

## 3. Airtable bases

> **Production-only (2026-08-19):** The separate DEV base (`appTetnuCZlCZdTCT`) is **retired**. Do not recreate, re-enable, or paste automations to it. Historical DEV install docs remain read-only with banners. Controlled testing uses Production with Schmidt enrollments per Mike authorization.

| Environment | Base UI name | Base ID | Role |
|-------------|--------------|---------|------|
| **Production** | `127SI - SHOOTING CHALLENGE GAME - NEW 5_1_2026` | `appn84sqPw03zEbTT` | **Only active** system of record |
| ~~Development~~ | ~~`127SI - SHOOTING CHALLENGE - DEV`~~ | ~~`appTetnuCZlCZdTCT`~~ | **Retired 2026-08-19** — historical snapshots only |

Schema snapshots under `airtable/schema/snapshots/prod-20260706/` and `dev-20260706/` are dated exports in-repo (DEV snapshot is historical). **Post–FUT-002 batch-1 live export:** `airtable/schema/snapshots/prod-20260831-fut002-batch1/` (33 tables / **1350** fields, 2026-08-31; **historical**). **After SA XP text stubs delete (2026-08-31):** Meta **1363** fields / **35** tables. **Post–FUT-002 Batch 2 delete (2026-09-05):** Meta **1375** fields / **35** tables — `airtable/schema/snapshots/prod-20260905-fut002-batch2/` · [`testing/evidence/fut-002/batch2-live-verify-20260905.json`](./testing/evidence/fut-002/batch2-live-verify-20260905.json). `airtable/schema/current/` remains **stale** — prefer dated snapshot + latest FUT-002 evidence for live field truth.

---

## 4. Website / deployment

| Item | State |
|------|--------|
| Public URL | https://www.fairfieldbasketballclub.com/shoot |
| Local | http://localhost:3001/shoot |
| Health | `GET /shoot/api/health` → public `{ "status": "ok" }` (SC-172). Legacy: `GET /shoot/api/airtable` → token validity check |
| Softr | **Obsolete / Not Used** — historical reference only |
| SEO | **COMPLETE** — program pages indexable (`NEXT_PUBLIC_ALLOW_SEARCH_INDEXING=true`); structured data + mobile meta from PR **#399** (supersedes draft **#310**). Status: [`audits/SEO-STATUS-20260904.md`](./audits/SEO-STATUS-20260904.md). Private/auth routes remain `noindex`. |
| Production deploy | **Live** — Vercel Production **`dpl_6h8wT3nFtuxGveW8DaoN34CWCVyA`** matches `master` tip **`94429042`**. Post-purge transactional athlete tables empty; FUT-043 + homework compact list + Levels + SC-149 branding live; FUT-025 athlete indexing env on |
| SC-172 Health + admin diagnostics | **LIVE / token pending** (2026-09-10) — PR **#505** merged; Production health **200**; diagnostics **403** until `ADMIN_DIAGNOSTICS_TOKEN` set. Evidence [`audits/SC-172-PRODUCTION-VERIFY-20260910.md`](./audits/SC-172-PRODUCTION-VERIFY-20260910.md) · checklist [`deploy-checklists/SC-172-health-admin-diagnostics.md`](./deploy-checklists/SC-172-health-admin-diagnostics.md) |
| Structured Curriculum Hub | **COMPLETE / PRODUCTION VERIFIED** (2026-09-12) — Hub Homework lifecycle verified; 52 structured-enabled; private SEO; SC Assignment Key Sync 52/52; lesson hero deployed. Active Hub feature work closed unless Production defect. Checklist history: [`deploy-checklists/structured-curriculum-hub-production-cutover.md`](./deploy-checklists/structured-curriculum-hub-production-cutover.md) |
| Presim web UX (2026-09-06) | **Merged** PR **#472** (`75632e88`) — dynamic **Grade Bands** leaderboard filters; leaderboard hero; public datetimes **America/Denver** with fixed **MT** label; FAQ accordion (hash deep-links) |
| Vitest / smoke | **483/483** Vitest pass (2026-08-30 release QA) · typecheck/lint/build PASS · prior smoke **50/50** (MRW-E04) |
| FUT-016 Tutorials | **Complete** — portfolio catalog at `/shoot/tutorials` (PR **#284**, 2026-08-30) |
| FUT-017 Zoom Meetings | **Complete** — portfolio catalog at `/shoot/zoom-meetings` (PR **#285**, 2026-08-30) |
| FUT-025 athlete profiles | **COMPLETE / Live Tested** — Production `NEXT_PUBLIC_ATHLETE_PROFILE_INDEXING=true`; cutover redeploy `dpl_4tbg25UzYPFruga1PzQthewWswNP`; public slug `athlete1-schmidt` → `index, follow`; `robots.txt` no longer Disallows `/shoot/athletes/`; sitemap still omits athlete URLs. Evidence [`audits/FUT-025-indexing-cutover-20260904.md`](./audits/FUT-025-indexing-cutover-20260904.md) |
| SC-149 branding URLs | **COMPLETE / Live Tested in PROD** (2026-09-04) — Vercel Production env MATCH for `NEXT_PUBLIC_LANDING_URL` / `SITE_URL` / `BASE_PATH`; live HTML Fairfield; zero hoop hosts; no redeploy required. Evidence [`testing/evidence/SC-149-FAIRFIELD-ATTESTATION-2026-09-04.json`](./testing/evidence/SC-149-FAIRFIELD-ATTESTATION-2026-09-04.json) · checklist [`deploy-checklists/SC-149-fairfield-branding-url-verification.md`](./deploy-checklists/SC-149-fairfield-branding-url-verification.md) |
| SC-149 Family Dashboard navigation | **COMPLETE / Live Tested in PROD** (2026-09-04) — PR **#358** (`29904b45`); header/mobile/footer/parent/FAQ CTAs → `/shoot/dashboard/sign-in`; private `/shoot/dashboard` remains auth-gated. Evidence [`audits/SC-149-family-dashboard-nav-prod-verification-20260904.md`](./audits/SC-149-family-dashboard-nav-prod-verification-20260904.md) · independent verify [`audits/SC-149-INDEPENDENT-VERIFY-20260904.md`](./audits/SC-149-INDEPENDENT-VERIFY-20260904.md) |
| SC-149 residual (FD under More) | **COMPLETE** (2026-09-05 with SC-164/165) — PR **#439** (`9869a2eb`); `MORE_NAV_HREFS` includes Family Dashboard → `/shoot/dashboard/sign-in`. Evidence [`audits/SC-149-MORE-FAMILY-DASHBOARD-20260905.md`](./audits/SC-149-MORE-FAMILY-DASHBOARD-20260905.md) |
| SC-161 Leaderboard | **COMPLETE / Live Tested** (2026-09-05) — PR **#440**; repair proven with athletes present; after OPS-PURGE Production board is legitimate **empty** (0 athletes). Evidence [`audits/SC-161-LEADERBOARD-REPAIR-20260905.md`](./audits/SC-161-LEADERBOARD-REPAIR-20260905.md) · [`audits/EOD-BASELINE-20260905.md`](./audits/EOD-BASELINE-20260905.md) |
| SC-162 Homework UX | **COMPLETE / Live Tested** (2026-09-05) — PR **#437** (`f8a1c9ee`); compact catalog + durable attachment/link delivery; **not FUT-029**. Evidence [`audits/SC-162-HOMEWORK-COMPACT-DURABLE-LINKS.md`](./audits/SC-162-HOMEWORK-COMPACT-DURABLE-LINKS.md) |
| SC-163 Goal Met Date | **COMPLETE / Live Tested** (2026-09-05) — PR **#444**; live **066 v4.1** = GitHub; Goal Met Date **date-only**; Athlete1 stamped **8/30/2026**, retry preserved, no duplicate milestones; 066 may remain ON. Evidence [`audits/SC-163-LIVE-VERIFICATION-CLOSEOUT-20260905.md`](./audits/SC-163-LIVE-VERIFICATION-CLOSEOUT-20260905.md) · checklist [`deploy-checklists/SC-163-goal-met-date.md`](./deploy-checklists/SC-163-goal-met-date.md). |
| SC-164 Levels UX | **COMPLETE / Live Tested** (2026-09-05) — PR **#439**; single **Your Level Progress** section; on-card gates. Evidence [`audits/SC-164-LEVELS-PROGRESS-UX-20260905.md`](./audits/SC-164-LEVELS-PROGRESS-UX-20260905.md) |
| SC-165 Awards / coaching messaging | **COMPLETE / Live Tested** (2026-09-05) — PR **#439**; Overview + What’s Included. Evidence [`audits/SC-165-AWARDS-COACHING-MESSAGING-20260905.md`](./audits/SC-165-AWARDS-COACHING-MESSAGING-20260905.md) |
| SC-166 Coach work queues | **Mike-owned/manual** (2026-09-05) — Interfaces published; filter/layout fine-tuning is Mike UI only; **not a core application blocker**. Checklist [`deploy-checklists/SC-166-coach-work-queue-filters.md`](./deploy-checklists/SC-166-coach-work-queue-filters.md). |
| FUT-029 Grade-band homework | **Deferred — DO NOT IMPLEMENT** — not part of current app completion; out of scope for wave 2026-09-05 / SC-162 |
| FUT-048 CloudFront custom domain (homework resources) | **DEFERRED** (Optional / low) — branded domain such as `homework.fairfieldbasketballclub.com` for `resources-homework` / `resources-homework-cf`; current permanent domain **`d21ixrrrqpqz29.cloudfront.net` remains acceptable**; **not a launch blocker**; **not FUT-029**; do **not** change CloudFront/DNS/S3/Airtable/Production for this now; do **not** delay homework-resource migration for this cosmetic improvement |
| SC-112 Athlete auth + private dashboard | **COMPLETE — PRODUCTION VERIFIED BY MIKE** (2026-09-04) — magic-link + multi-child three-athlete select/switch/sign-out verified on Production deploy `dpl_8TLH6uQAvLXUoQGDrGQ4NrFnWcVG` (merge `78208ffc` / PR **#388**). **No further SC-112 action.** Checklist: [`deploy-checklists/SC-112-athlete-auth-preview-and-production.md`](./deploy-checklists/SC-112-athlete-auth-preview-and-production.md). Ledger: [`audits/SC-112-multi-child-select-404-fix-20260904.md`](./audits/SC-112-multi-child-select-404-fix-20260904.md) |
| SC-151 Family Dashboard Gmail access | **MERGED/DEPLOYED** — PR **#389** merge `a00ef7a5`; Production `dpl_2mch4scL3c6bgHZgizDbsqPTywbW`; docs closeout PR **#391** (`0479db22`). Sign-in shows registration-email instruction; Gmail prohibition gone. **SC-112 remains closed.** Audit: [`audits/SC-151-family-dashboard-gmail-access-20260904.md`](./audits/SC-151-family-dashboard-gmail-access-20260904.md) |
| Public awards (`Public On Web`) | **MERGED** PR **#378** (`a0e84533`) — `AWARD_RECIPIENT_PUBLICATION_FIELD = "Public On Web"`. PR **#376** closed superseded. |
| Transactional enrollments | **Empty** after OPS-PURGE-20260905 — Athletes/Enrollments = **0**. Prior 2026-09-03 MCP note (2/3 Schmidt VERIFY) is historical.
| Season Simulation | **Perfect Mike Schmidt PASSED** (`SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt`) — pre-restore **4980 / 170**; formulas restored; cleanup closed — [`audits/readiness-20260914/FINAL-PASS-SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt.md`](./audits/readiness-20260914/FINAL-PASS-SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt.md). Post-restore **4525** = expected under Production `NOW()`, not a failed season. **Three-athlete SC-SEASON-SIM-001 READY — NOT EXECUTED.** **SC-002 T122531Z COMPLETE / cleaned.** Discrepancy wave **SC-167/168/169 COMPLETE**. Live formulas Production-normal — do not change until authorized execute. SC-001 requires **`RUN 3-ATHLETE SEASON SIMULATION`**. |
| Zoom Attendance primary (2026-09-06) | Lookups + **Attendance Label** formula **created live** (`fldVILeOyW1jepScv`, isValid). Primary still **Id** `fldXHFpB3MrOVevYL` autoNumber — Mike UI convert pending. Checklist: [`deploy-checklists/ZOOM-ATTENDANCE-PRIMARY-FIELD-FORMULA.md`](./deploy-checklists/ZOOM-ATTENDANCE-PRIMARY-FIELD-FORMULA.md). |
| SC-109 Game Manual PDF | **COMPLETE / Live Tested in PROD (2026-09-04)** — `/shoot/game-manual` shows **Open game manual** → Adobe Publish Online (`GAME_MANUAL_PUBLISH_URL` repo default; env override optional); How you earn XP + Level ladder render; no env-name leak — evidence [`testing/evidence/SC-109-PROD-ATTESTATION-2026-09-04.json`](./testing/evidence/SC-109-PROD-ATTESTATION-2026-09-04.json) · checklist [`deploy-checklists/SC-109-game-manual-url-verification.md`](./deploy-checklists/SC-109-game-manual-url-verification.md) |
| FUT-002 field inventory | **Batch 1 COMPLETE** + **SA XP stubs deleted** + **Batch 2 COMPLETE (2026-09-05)** — five Batch 2 text-stub IDs absent; live Meta **1375** fields / **35** tables; schema `airtable/schema/snapshots/prod-20260905-fut002-batch2/`; evidence [`testing/evidence/fut-002/batch2-live-verify-20260905.json`](./testing/evidence/fut-002/batch2-live-verify-20260905.json) · closeout [`audits/FUT-002-BATCH2-POST-DELETE-CLOSEOUT-20260905.md`](./audits/FUT-002-BATCH2-POST-DELETE-CLOSEOUT-20260905.md). Later: Config Drive roots + `unknown` interface review remain FUTURE |
| FUT-010 intake attachment cleanup | **Dry-run complete (R3 2026-08-30)** — **0 eligible**; no deletion request — [`testing/evidence/FUT-010-DRY-RUN-2026-08-30-R3.md`](./testing/evidence/FUT-010-DRY-RUN-2026-08-30-R3.md) |
| Weeks 2026–27 | **Finalized** — Early Bird **Apr 25–May 1, 2027** countable; May 1 ∈ Early Bird; Week 1 starts May 2 — [`testing/evidence/WEEKS-2026-27-AUDIT-2026-08-30.md`](./testing/evidence/WEEKS-2026-27-AUDIT-2026-08-30.md) |
| Homework PHA 2026–27 | **Current: 20 active PHA** including **Week 9 × 2** (supersedes “18 PHA” launch claims). Historical: **18 active restored** after FUT-030 (2026-08-31) — evidence [`testing/evidence/transactional-reset-2026-08-31/11-pha-restore-created-20260831_133022.json`](./testing/evidence/transactional-reset-2026-08-31/11-pha-restore-created-20260831_133022.json); prior audit [`testing/evidence/HOMEWORK-PHA-18-AUDIT-2026-08-30.md`](./testing/evidence/HOMEWORK-PHA-18-AUDIT-2026-08-30.md) = **historical**. |
| Transactional data | **Empty** after Perfect-sim cleanup (2026-09-14) and prior 2026-09-05 purge — Athletes/Enrollments/Submissions/Assets/HC/XP/WAS/VF/Unlocks/Streaks/Zoom Attendance/Award Recipients/Payments/Email Handoff Queue = **0**. Zoom Meetings **2** catalog (Introduction, Motivation). PHA **20** / Weeks preserved / Homework Library / Countries / State preserved. Evidence: [`audits/readiness-20260914/cleanup-verify-SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt.json`](./audits/readiness-20260914/cleanup-verify-SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt.json) · historical purge [`testing/evidence/transactional-purge-2026-09-05/CLOSEOUT.md`](./testing/evidence/transactional-purge-2026-09-05/CLOSEOUT.md). |
| Phase 4 public copy | **Shipped** PR **#298** — CR-13/CR-17/CR-18 parent copy implemented 2026-09-01; optional Dashboard relabel complete (CR-12) |
| SC-147 Recorded Zoom half-XP | **COMPLETE / Live Tested in PROD** — Automation **101 v6.8** Live; GitHub synced (PR **#398**); recording `ZOOM_RECORDING_CREDIT|*` @ 30 + live @ 60 on disposable VERIFY; **no 121**; **117** email-only. Optional residual: GitHub year-aware Config percent hardening may still need Airtable UI paste for byte-match. Evidence [`audits/SC-147-101-V68-PRODUCTION-CLOSEOUT-20260904.md`](./audits/SC-147-101-V68-PRODUCTION-CLOSEOUT-20260904.md) |
| SC-148 mobile a11y | **COMPLETE / Live Tested in PROD** — interactive + Playwright attestation 2026-09-04. Evidence [`audits/SC-148-mobile-a11y-prod-attestation-20260904.md`](./audits/SC-148-mobile-a11y-prod-attestation-20260904.md) |
| SC-057 / SC-058 | **Complete / Live Tested** — 50 Production automations MCP-attested; inventory [`audits/WORKFLOW-RELIABILITY-INVENTORY-20260904.md`](./audits/WORKFLOW-RELIABILITY-INVENTORY-20260904.md); silent-failure remediation [`audits/WORKFLOW-SILENT-FAILURE-REMEDIATION-20260904.md`](./audits/WORKFLOW-SILENT-FAILURE-REMEDIATION-20260904.md) |
| MRW-F07 weekly email harness | **Complete (PR #289)** — disposable E2E tooling for `118→072→119→074→079`; live `--apply` on Mike disposable WAS still operator-only |
| Production smoke athlete slug | `perfect-week-testing` (`testing-schmidt` is DEV-only) |
| PHA Due Date | Public homework catalog + athlete homework assignments display PHA Due Date (fallback Week End Date); verified prod 2026-08-25 |
| Homework catalog (FUT-014) | **Complete** — `/shoot/homework` PHA + Homework Library live catalog; Brief Description = **`Homework Library.Brief Description - Display`** (`fldAnHr3uTuDN5bs9`); 4 published cards verified prod 2026-08-26 |
| XP Event Log (website) | **Complete** — two-row layout, ISO dates, linked headline details, same-date % sort; display-only (no XP calculation changes). Commits `6625559`, `f225f04`, `68c3a45`, `3306379` |
| FUT-003 paid Make route | **Validated — ready for Mike Make activation** (scenario **inactive** by design; A5 audit 2026-09-04); free-payment **deferred Nov/Dec 2026**; not a non-registration launch blocker — [`audits/FUT-003-STRIPE-STATUS-20260904.md`](./audits/FUT-003-STRIPE-STATUS-20260904.md) |
| FUT-009 S3 video rename | **COMPLETE / Live Tested** — Lambda `/fut009/rename` + Automation **120** Live; disposable Schmidt rename + idempotent re-run 2026-09-04 — [`audits/FUT-009-LAMBDA-STATUS-20260904.md`](./audits/FUT-009-LAMBDA-STATUS-20260904.md) |
| Live Vercel settings | Production env names verified via CLI 2026-08-25 (`NEXT_PUBLIC_ALLOW_SEARCH_INDEXING`, `NEXT_PUBLIC_SITE_URL`); do not log values |

Evidence pointer: [`PROJECT_STATE.md`](./PROJECT_STATE.md) § Vercel / web app.

---

## 5. Email path (current)

| Item | State |
|------|--------|
| Sender | **Resend** via Communications Hub |
| Make.com email | **None** — Make does not send SC parent/athlete notification email |
| Gmail Make scenarios | **Historical only** |
| Daily submission path | **076 v8.16** (GitHub; paste pending) → **079** → Hub → Resend |
| Homework feedback path | **071 v4.5** → **079** → Hub → Resend (Production = GitHub 2026-09-13) |
| Tier 1 operator packet | [`deploy-checklists/TIER-1-LAUNCH-OPS-RUNBOOK-20260911.md`](./deploy-checklists/TIER-1-LAUNCH-OPS-RUNBOOK-20260911.md) — producers aligned; disposable delivery proof + Live testMode flip remain |
| Automation **077** | **Retired / deleted from Production** (Mike-dated docs: 2026-08-13). Do not restore Make daily email. GitHub source retained as archive only. **Do not** trust obsolete `Automations` table rows that once showed 077 as Live. |
| Queue producers (repo) | Include Hub handoff scripts; **079** dispatches Ready queue → Hub → Resend |
| Automation **117** | **v2.2 Live** — Hub queue create + `athleteFirstName` / meeting display / proof timestamps. Not XP; not Make 117f. |
| Hub templates (comms) | Communications Hub **PR #52** **MERGED** to `main` @ **`e79637f`**. Tier-1 producers aligned with GitHub (2026-09-13). Version matrix: [`deploy-checklists/parent-email-live-cutover-2026-09-02.md`](./deploy-checklists/parent-email-live-cutover-2026-09-02.md) · [`integrations/email-send-plane.md`](./integrations/email-send-plane.md). |
| Parent-email + auth Live cutover (2026-09-03) | Operator checklist **MERGED** PR **#377** — [`deploy-checklists/parent-email-and-auth-live-cutover-2026-09-03.md`](./deploy-checklists/parent-email-and-auth-live-cutover-2026-09-03.md). Target Live: producer `testMode=false` (071/073/074/076/078A/117); 118 `dryRun=false` + `sendMode=Live`; 119 `dryRun=false`; Vercel `ATHLETE_AUTH_TEST_MODE=false`. Magic-link **works**. Mike UI attestation remains authority if settings drift. |

Authority: [`integrations/email-send-plane.md`](./integrations/email-send-plane.md) · Completion Master · [`automation-index.md`](./automation-index.md). Live Automations UI attestation still preferred if Mike re-confirms.

---

## 6. Make.com (current inventory)

| Scenario / blueprint | Status |
|----------------------|--------|
| Upload Engine → Lambda (070b/070c path) | **Active** upload path (non-email) |
| Homework upload (070a) | **PROD Live v4.7** (SC-156 Complete — script-only graph) |
| Weekly / parent notification email | **Retired for email** — Hub → Resend |
| Make **117f** Zoom Gmail | **Historical** |
| Tremendous awards v2 | **Implementation snapshot**; sandbox validated; scenario **OFF**; production API **PENDING** |
| Tremendous awards v1 | **Historical** |

Authority: [`integrations/tremendous-award-fulfillment.md`](./integrations/tremendous-award-fulfillment.md) · [`make/blueprints/README.md`](../make/blueprints/README.md).

---

## 7. Communications Hub

| Item | State |
|------|--------|
| Role | Queue + Resend delivery for SC notification email |
| Zoom recording approval | **117 v2.2** → Email Handoff Queue → **079** → Hub → Resend (Production = GitHub 2026-09-13). |
| Welcome / participant activation | Hub path documented; full participant activation still **PENDING** live proof |
| Template registry | See `docs/communications-hub/` — treat audit dated 2026-08-17 as evidence, not invent live template IDs |

---

## 8. Airtable automation versions (repo source + Mike overlays)

### Confirmed Production versions (Automations Code MCP 2026-08-29 + reconfirm 2026-08-30)

Authority precedence for this reconciliation:

1. **Live Automation script body / run-history `version` output** (Mike-attested)
2. Production `Automations` columns **Name / Status / Automation Code** (post-2026-08-20 refresh only)
3. Repository SCRIPT headers

Do **not** treat other Automations-table columns (trigger/conditions) as authority — they are often stale.

| # | Production (Automations Code) | GitHub | Status | Notes |
|---|-------------------------------|--------|--------|-------|
| **003** | **v2.0** | v2.0 | **Live / COMPLETE / PRODUCTION-VERIFIED / DO-NOT-TOUCH** | Grade-change Grade Band refresh; keep active; disposable VERIFY Enrollment 2026-09-03 — [`prod-completion/2026-09-03/AUTOMATION-003-GRADE-CHANGE-VERIFIED.md`](./prod-completion/2026-09-03/AUTOMATION-003-GRADE-CHANGE-VERIFIED.md). Initial assign remains **002**. |
| **010** | **v10.14** | v10.14 | Live / **SC-167 COMPLETE / Live Tested** | Option A create+retry proof 2026-09-05; one Active `SUBMISSION_XP`; formulas restored — [`audits/SC-167-010-V1014-OPTION-A-LIVE-PROOF-20260905.md`](./audits/SC-167-010-V1014-OPTION-A-LIVE-PROOF-20260905.md). Prior dual-enrollment fixture cleanup historical — [`audits/010-DUAL-ENROLLMENT-FIXTURE-CLEANUP-20260905.md`](./audits/010-DUAL-ENROLLMENT-FIXTURE-CLEANUP-20260905.md). |
| **020** | **v4.1** | v4.1 | Live / **PASTE-ALIGNED** (SC-160 COMPLETE 2026-09-05) | HC Week = PHA.Week; Submission.Week optional; Early/On Time/Late Notes; WAS find-or-create for Enrollment+PHA.Week. Evidence [`audits/SC-160-STAGE6-FINAL-CLOSEOUT-20260905.md`](./audits/SC-160-STAGE6-FINAL-CLOSEOUT-20260905.md) |
| **022** | **v2.2** | v2.2 | Live / **aligned** | Lambda-only parent URL — [`022-v2.2-operator-packet.md`](./deploy-checklists/022-v2.2-operator-packet.md) |
| **033** | **v4.4** | v4.4 | Live | |
| **035** | **v1.7** | v1.6 live (Unicode comment drift) | **GitHub v1.7 ready — paste pending Mike approval** | Marker `SC-SEASON-SIM-001-DEPLOY-20260914D`; ASCII/comment hash consistency; executable unchanged from v1.6. Evidence [`audits/readiness-20260914/035-V1.7-ASCII-HASH-CONSISTENCY-20260914.md`](./audits/readiness-20260914/035-V1.7-ASCII-HASH-CONSISTENCY-20260914.md) · paste [`deploy-checklists/035-v1.7-PASTE.txt`](./deploy-checklists/035-v1.7-PASTE.txt) |
| **041** | **v5.1** | v5.1 | Live | Optional inputs only |
| **053** | **5.8** | 5.8 | Live / **GitHub synced** (2026-09-14) | Marker `SC-SEASON-SIM-001-DEPLOY-20260913B`; Denver-safe `toDateKey`; unblocks 50/60-day streaks. Evidence [`audits/053-v5.8-live-sync-20260914/VERIFICATION.md`](./audits/053-v5.8-live-sync-20260914/VERIFICATION.md) |
| **057** | **2.7** | **2.7 Live** | Queue?=1; formula Pending OR Recalc | Perfect Week homework = Week End Saturday only (v2.7). Live header+SHA match GitHub 2026-09-14 — paste not required. |
| **058** | **1.7** | **1.7 Live** | Lifecycle `recordUpdated` + nine fields | SC-153 **COMPLETE / Live Tested** — withdraw/restore/idempotency PASS ([`SC-153-058-V17-LIVE-VERIFICATION-20260904.md`](./audits/SC-153-058-V17-LIVE-VERIFICATION-20260904.md)) |
| **059** | **v3.8** | v3.8 | Live / **SC-159 COMPLETE / Live Tested** | Formula `059 Lifecycle Trigger?` = 1 only; withdraw/restore/idempotency/PW PASS — [`audits/SC-159-LIVE-VERIFICATION-CLOSEOUT-20260904.md`](./audits/SC-159-LIVE-VERIFICATION-CLOSEOUT-20260904.md) · checklist [`deploy-checklists/059-sc159-lifecycle-formula-trigger.md`](./deploy-checklists/059-sc159-lifecycle-formula-trigger.md) (nested OR checklist superseded) |
| **064** | **Production-verified current live** | v12.2 in repo | Live | Do not invent a new version string |
| **065** | **v10.11** | v10.11 | Live / **GitHub synced from live Automation Code** (2026-09-14) | Soft-skip when `Total Homework XP Awarded` not yet positive (`SC-SEASON-SIM-001-DEPLOY-20260913B`); required trigger Needed?=1 AND Total XP > 0. Evidence [`audits/readiness-20260914/065-V10.11-LIVE-SYNC-VERIFY-20260914.md`](./audits/readiness-20260914/065-V10.11-LIVE-SYNC-VERIFY-20260914.md). Prior SC-160 Stage 6 path remains valid. |
| **067** | **v3.5** | v3.5 | Live / **aligned** (no paste needed) | Reflection quiz → Homework Completion. Live body matches GitHub **v3.5** (Agent 3 MCP 2026-09-05). Prior decline note historical — [`audits/VERSION-AUDIT-CORRECTION-021-013-067-20260905.md`](./audits/VERSION-AUDIT-CORRECTION-021-013-067-20260905.md) |
| **066** | **v4.1** | v4.1 | Live / **SC-163 COMPLETE / Live Tested** | Goal Met Date date-only + milestones; Athlete1 stamped **8/30/2026**; may remain ON — [`audits/SC-163-LIVE-VERIFICATION-CLOSEOUT-20260905.md`](./audits/SC-163-LIVE-VERIFICATION-CLOSEOUT-20260905.md) |
| **013** | **v3.2.0** | v3.2.0 | Live / **aligned** (no paste needed) | VF create path. Live body matches GitHub **v3.2.0** (Agent 3 MCP 2026-09-05). Prior decline note historical — [`audits/VERSION-AUDIT-CORRECTION-021-013-067-20260905.md`](./audits/VERSION-AUDIT-CORRECTION-021-013-067-20260905.md) |
| **021** | **v2.0** | v2.0 | **Live / ALIGNED** | Attachment Upload Status only; exact byte match GitHub; Phase A combined paste never installed — same correction audit |
| **072** | **v4.9.4** | v4.9.2 | **GitHub ahead / paste pending** | Boolean/send-mode parse paste deploy; checklist [`deploy-checklists/EMAIL-PRODUCER-BOOLEAN-INPUT-PARSING.md`](./deploy-checklists/EMAIL-PRODUCER-BOOLEAN-INPUT-PARSING.md) |
| **073** | **v4.11** | v4.9 | **GitHub ahead / paste pending** | Strict `parseAutomationBoolean` for `testMode` text `"false"` |
| **071** | **v4.7** | v4.5 | **GitHub ahead / paste pending** | Strict `parseAutomationBoolean` for `testMode` text `"false"` |
| **076** | **v8.17** | v8.15 | **GitHub ahead / paste pending** | Strict `parseAutomationBoolean` for `testMode` text `"false"` |
| **074** | **v3.8** | v3.6 | **GitHub ahead / paste pending** | Strict `parseAutomationBoolean` for `testMode` text `"false"` |
| **070a** | **v4.7** | **v4.7 Live** | Script-only graph (SC-156); trigger clears via script | Homework upload Make path |
| **070b** | **v4.7** | v4.7 | Live | |
| **070c** | **current live (repo v1.1)** | v1.1 | Live/enabled | Do not invent a new version |
| **101** | **v6.8** | v6.8 | Live / **SC-147 COMPLETE** | Recording half-XP Live Tested; GitHub synced PR **#398**. Optional: re-paste GitHub year-aware Config percent hardening for byte-match |
| **117** | **v2.4** | v2.2 | **GitHub ahead / paste pending** | Strict `parseAutomationBoolean` for `testMode` text `"false"` |
| **078A** | **v1.9** | v1.7 | **GitHub ahead / paste pending** | Strict `parseAutomationBoolean` for `testMode` text `"false"` |
| **118** | **v2.3** | v2.1 | **GitHub ahead / paste pending** | Strict boolean/sendMode input parse for schedule arming |
| **119** | **v1.10** | v1.8 | **GitHub ahead / paste pending** | Strict `parseAutomationBoolean` for `dryRun` / `includeSchmidt` |

**Record-ID classification (Mike final):** Dynamic for all record-based automations; optional on **041** only; intentionally blank on **056 / 078 / 118 / 119**. **065** and **066** use triggering-record `recordId` in Production. Closeout: [`deploy-checklists/2026-08-24-065-066-dynamic-trigger-closeout.md`](./deploy-checklists/2026-08-24-065-066-dynamic-trigger-closeout.md).

**Config-over-code audit (SC-034 / V2-002):** Repo + **live** automation **057 v2.2** use Config field **`Perfect Week Video Minimum`**. Schema field renamed. Automations Code **tracker** may lag with typo — not a paste blocker. WAS lookup + formula live. **No** `legacyRequiredVideoCount: 3`. Audit: [`audits/2026-08-27-SC-034-config-hardcode-audit.md`](./audits/2026-08-27-SC-034-config-hardcode-audit.md).

**Historical:** Midday 2026-08-21 Code snapshots (010 v10.10 / 101 v6.6) and “010/022/072 paste pending” rows are **superseded**.

### Repository source (GitHub) — other notable scripts

Live ON/OFF for rows without Mike UI confirmation = `UNVERIFIED`. Full table: [`AUTOMATION_VERSION_INVENTORY.md`](./AUTOMATION_VERSION_INVENTORY.md).

| # | GitHub version (header) | Notes |
|---|-------------------------|--------|
| 070a | v4.7 | **Live** during Perfect Week controlled window (historically intentional OFF) |
| 070c | v1.1 | **Enabled in PROD** — async video writeback verify after **070b**; do not invent a new version |
| 076 | **v8.14** (GitHub) / **v8.12** (Live) | Daily Hub queue create — streak + `athleteFirstName` pending paste |
| 077 | v5.0 archive | **Deleted from Production** (2026-08-13 docs) — not live Make send |
| 079 | v2.5 (GitHub + prod) | Ready queue → Hub → Resend; E2E weekly send 2026-08-24 |
| 112 | legacy | Expected **OFF** |
| 115 | v2.1 ETF | **Production-only ETF** — never paste as normal season automation |
| 005 | v5.5 (GitHub) | PHA slot normalize (see CHANGELOG) |
| 117a / 117b | design / historical S16 | **Not** current PROD 117 |

**Contradiction resolved:** Older Completion Master paste-queue rows that still say “010 v10.8 pending,” “020 v3.5,” or “070b v4.6 paste pending” are **historical**. Prefer this file’s final 2026-08-21 verification table.

---

## 9. XP / levels / achievements

| Domain | Owner (repo contract) | Live proof |
|--------|----------------------|------------|
| Submission XP | **010** — Source Key `SUBMISSION_XP\|{submissionId}` | GitHub + Live **v10.14** (SC-167 COMPLETE / Live Tested) |
| Homework XP | **064** prepares (`HOMEWORK_COMPLETION` rule); **065** creates/reconciles `HOMEWORK_XP|{hcId}` (**020** HC create; **078** marks Parent Feedback Ready?) | **065 Production v10.11** (soft-skip / 064→065 re-entry); late-credit + weekless WAS paths Live Tested |
| Video XP | **113 / 114** (+ **013** VF create) | **Live v6.4 / v6.2**; **PKG-007 lifecycle proof PASS 2026-08-23** (`AUTONOMOUS_VIDEO_QA_20260823_164549`, Testing3). Native trigger + 073 OFF UI attestation open |
| Shot milestones | **066** | Production **v4.1** Live Tested (SC-163 Goal Met Date + milestones) |
| Levels | **041 / 042** | **041 Production v5.1**; broader progression proof still open |
| Perfect Week | **057 → 058 → 059** | **COMPLETE** for WAS `recl3DmBh22ADPWWe`: unlock `recJ5umer4J4FHTOz`, key `PERFECT_WEEK\|rec93mAfo5jKqP3g5\|recNzl4dNOtDmJqnV`, XP `reczehlzkA8fjiQh0`, Awarded, 100 XP, no duplicate unlock. Evidence: `docs/testing/evidence/sc-pw-e2e/award-was-recl3DmBh22ADPWWe-2026-08-29-mcp.json`. Do **not** re-`--apply` for this fixture. |
| Zoom live attendance XP | **101** | Production **v6.8** Live (SC-147 recording half-XP). GitHub synced PR **#398**. |
| Zoom recording XP under slot 117 | Not live | Slot **117** is email Hub handoff (**v2.1 Live**) |

---

## 10. Homework / video / Zoom

| Path | State |
|------|--------|
| Homework assets → HC → XP → parent | **009** → **020 v4.1** → **070a v4.7 Live** → **064** prepare / **065 v10.11** → **078** Ready → **071** Hub (SC-160 Live Tested; v10.10 soft-skip protects 064→065 timing) |
| Homework completion (**020**) | Production Automations Code **v4.1** (SC-160). **012** / **063** deleted — do not restore |
| Homework upload Make (**070a**) | Production **v4.7 Live** during Perfect Week controlled window (historically intentional OFF). Formula Ready alone does not send; **Send to Make Trigger** required |
| Video upload (**070b** + Lambda + **070c**) | Production **070b v4.7** → Make → Lambda → **070c current live (repo v1.1)** verify. Optional retry proof + secret rotation **PENDING** |
| Child upload writeback (**022**) | Production **v2.2** Live — Lambda viewer URL only; no Canonical S3 fallback |
| Homework parent email | **078** Ready → **071** → **079** → Hub → Resend |
| Video parent email | Video `Parent Feedback Ready?` **manual** → **073 v4.4** Live → Hub → Resend — parent URL must be Lambda viewer only |
| Zoom live attendance | **101 v6.8** (SC-147 recording half-XP Live Tested) |
| Zoom recording approval email | **117 v2.1 Live** → Hub → Resend; GitHub **v2.2** paste pending (Hub `main` **e79637f**) |
| Fillout daily submission | **OFF** (contest intake closed) |

---

## 11. Perfect Week

| Item | State |
|------|--------|
| Controlled path through WAS / homework | Path evidence 2026-08-16 |
| Perfect Week 48-hour grace period | **Live-tested** — **057 v2.0** + Airtable formulas; disposable weekly email showed **4/7** PW qualifying days vs **7/7** general shooting days |
| Full Perfect Week award proof | **COMPLETE** — WAS `recl3DmBh22ADPWWe`; unlock Awarded + 100 XP; see MCP evidence JSON. Do not create another test week for this requirement. |
| Required order | **057 → 058 → 059** only after Eligible?=1 and Days Logged=7 |
| Weekly XP disagreement (`reczxTIpVI8ZJLex0`) | **Historical artifact:** old weekly email sent **before v4.7 corrections** — preserved evidence only. Resolved by **072 v4.7** + disposable E2E **2026-08-24** on `recdj8MD0szplMW5r`. Queue proof `recoikFrli3m0xDRa` **must remain unchanged** — not reused |
| Authority | Completion Master + Perfect Week prep report + Perfect Week testing docs under `docs/testing/perfect-week/` |

---

## 12. Tremendous (C-028)

| Item | State |
|------|--------|
| Sandbox send | **Validated** (Mike 2026-08-19) |
| Production API | **PENDING** Tremendous approval |
| Make scenario | **OFF** |
| Keys | Make credentials only — **never commit** |
| v2 blueprint | Implementation snapshot, not production-live |
| v1 blueprint | Historical |

---

## 13. Work ledger (summary)

### Completed (selected, evidence-backed)

- Wave 0 2025–26 close-out; H-001; many PKG merges on `master`
- Email plane migrated to Hub → Resend (Mike 2026-08-19)
- Confirmed Production pastes aligned: **010 v10.14**, **020 v4.1**, **022 v2.2**, **065 v10.11**, **071 v4.3**, **076 v8.12**, **072 v4.9.1**, **073 v4.6**, **066 v4.1**, **013 v3.2.0**, **067 v3.5**, **070b**, **117**
- Tremendous sandbox validation
- Lambda season CodeOnly deploy (optional follow-ups open)
- Repository integrity + PII redaction pass
- Secure video URL pipeline **Live** (022/072/073) — Lambda viewer only; direct S3 AccessDenied expected
- **2026-08-24:** **066 v3.9** dynamic `recordId` verified; historical audit artifacts documented
- **2026-09-06:** SC-SEASON-SIM-001 three-athlete prep READY (not executed); five-enrollment superseded
- **2026-09-05:** SC-167/168/169 COMPLETE; OPS-PURGE COMPLETE; SC-SEASON-SIM-002 closed; formulas `NOW()`/`TODAY()`

### Open Mike UI actions (Tier 1 launch ops — 2026-09-11)

- **Tier 1 launch ops runbook:** [`deploy-checklists/TIER-1-LAUNCH-OPS-RUNBOOK-20260911.md`](./deploy-checklists/TIER-1-LAUNCH-OPS-RUNBOOK-20260911.md) — Phase A email pastes (**076→071→072→074→073→117**); Phase B SC-172 `ADMIN_DIAGNOSTICS_TOKEN`; Phase C Structured Curriculum Hub cutover; Phase D Zoom Attendance primary formula; Phase E Live testMode flip.
- **SC-166 (Mike-owned/manual; not core blocker):** Optional Interface Active/History filter fine-tuning — [`deploy-checklists/SC-166-coach-work-queue-filters.md`](./deploy-checklists/SC-166-coach-work-queue-filters.md).

### Pending / needs live proof

- Optional Automations Code **tracker** text refresh for 057 (live script already correct — do not repaste)
- Optional disposable fixture cleanup: `recdj8MD0szplMW5r`, `recxIzdVil9ewhBxN`, `recPg14iNRkxblMLs`
- Optional weekly email template / copy refinements
- Broader progression / standings certification packages
- Automation version inventory rows still UNKNOWN in Airtable UI
- Optional 066 OMNI sandbox confirm (K-H1)
- Lambda Storage Key retry proof + secret rotation
- RCC Airtable Interface install
- Open PRs: drafts **#353** / **#335** / **#244** — review before merge. Superseded **#234/#237/#238/#262/#307/#316/#340** CLOSED without merge
- Functional-closeout wave (2026-09-04): no remaining P0 silent-failure defect; **FUT-009 activated / Live Tested** 2026-09-04 — [`audits/FUT-009-LAMBDA-STATUS-20260904.md`](./audits/FUT-009-LAMBDA-STATUS-20260904.md) · prior wave [`audits/COORD-WAVE-FUNCTIONAL-CLOSEOUT-20260904.md`](./audits/COORD-WAVE-FUNCTIONAL-CLOSEOUT-20260904.md)
- FUT-003 Make paid scenario still **inactive** until Mike activation — [`audits/FUT-003-STRIPE-STATUS-20260904.md`](./audits/FUT-003-STRIPE-STATUS-20260904.md)
- FUT-025 athlete profile indexing cutover (Mike approval)
- FUT-010 supervised attachment apply only if eligible rows appear (R3 dry-run **0 eligible**)
- SC-147 Recorded Zoom half-XP — **COMPLETE / Live Tested** (101 **v6.8**; PR **#398**)
- FUT-025 athlete profile indexing — **COMPLETE / Live Tested** (PR **#397** + env cutover)
- SEO discoverability — **COMPLETE** (PR **#399**; draft **#310** closed)
- SC-148 mobile a11y — **COMPLETE / Live Tested** (PR **#396**)
- SC-057 / SC-058 — **Complete / Live Tested** (PR **#395**; inventory + SF remediation)
- Season Simulation — **SC-002 T122531Z CLOSED**; **SC-001 three-athlete READY (not executed)**; SC-002 rerun **NOT authorized**; SC-001 requires **`RUN 3-ATHLETE SEASON SIMULATION`**
- **SC-160** — **COMPLETE / Live Tested** — asset intake without Week + early/on-time/late HW + weekless WAS-for-PHA-Week — live **009 v1.3 / 020 v4.1 / 065 v10.7 / 057 2.5** — [audits/SC-160-STAGE6-FINAL-CLOSEOUT-20260905.md](./audits/SC-160-STAGE6-FINAL-CLOSEOUT-20260905.md)
- **SC wave 2026-09-05** — SC-161/162/163/164/165/149 residual **COMPLETE / Live Tested**; SC-166 **COMPLETE / owner-verified (2026-09-06)**; FUT-029 Deferred; **FUT-048** Deferred optional CloudFront custom domain (keep `d21ixrrrqpqz29.cloudfront.net`); SC-SEASON-SIM-001 prep wave 2026-09-06 — [audits/SC-SEASON-SIM-001-THREE-ATHLETE-PREP-READINESS-20260906.md](./audits/SC-SEASON-SIM-001-THREE-ATHLETE-PREP-READINESS-20260906.md); purge **#457** — [audits/SC-WAVE-20260905-CLOSEOUT.md](./audits/SC-WAVE-20260905-CLOSEOUT.md) · [audits/MASTER-LIST-RECONCILIATION-20260905.md](./audits/MASTER-LIST-RECONCILIATION-20260905.md)
- **SC-167/168/169 discrepancy wave** — [audits/SC-167-010-V1014-OPTION-A-LIVE-PROOF-20260905.md](./audits/SC-167-010-V1014-OPTION-A-LIVE-PROOF-20260905.md) · [audits/SC-167-168-169-LIVE-VERIFICATION-20260905.md](./audits/SC-167-168-169-LIVE-VERIFICATION-20260905.md) · PRs **#451/#453/#452/#454/#455/#456**
- **OPS-PURGE-20260905** — **COMPLETE** — PR **#457** `ba969433` — [testing/evidence/transactional-purge-2026-09-05/CLOSEOUT.md](./testing/evidence/transactional-purge-2026-09-05/CLOSEOUT.md)
- Airtable field deletion — **deferred** until functional verification complete
- Full administrative portal / optional card redesign — **deferred**
- **FUT-048** CloudFront custom domain for homework resources — **deferred** optional/low; keep `d21ixrrrqpqz29.cloudfront.net`; not required now
- Landing FUT-033–036 + Hub FUT-041/042/046/047 — repo merged locally; **GitHub push + Vercel deploy** pending auth (2026-09-01)

### Blocked

- PKG-037 core certification (depends on prior live proofs)
- PKG-004 schema ownership gate before schema feature work
- Full pre-season audit pack until dependency packages + 2027 Weeks proof

### Deferred

- V2-013 Program Instance multi-year architecture wave
- Drive/attachment retirement (C-023) and related low-priority cleanup
- Softr field rename / Tutorials table retirement (breaking schema)

### Unverified / requires live confirmation

- Exact ON/OFF and pasted versions for automations without 2026-08-19 Mike overlay
- Live Make scenario schedules beyond documented OFF/ON claims
- Live Tremendous production access (explicitly pending)
- That every Hub template ID in docs matches Hub UI today

**Partially verified (2026-08-25):** Vercel Production has `NEXT_PUBLIC_ALLOW_SEARCH_INDEXING` and `NEXT_PUBLIC_SITE_URL` configured (names confirmed via CLI; values not logged). Public indexing behavior verified via `npm run test:smoke:prod` and live URL checks.

---

## 14. Known limitations

- Repository text ≠ live Airtable paste proof.
- Offline / fixture tests ≠ controlled Production proof.
- The Production **`Automations` data table** is authority for **`Name` / `Status` / `Automation Code` only** after the 2026-08-20 refresh (see Authority rule above). Other columns on that table may still be stale.
- Pre-refresh historical inventories built from that table (2026-07-23 foundation-reset export, SC-058 refresh notes, reliability-audit P3 “re-export Automations table”) remain **non-authority** for that era.
- Automation **115** creates a new Submission per checked Run Test by design — not idempotency.
- Large historical overnight JSON snapshots retain athlete **names** after email redaction; treat as sensitive.
- Many local git worktrees and feature branches exist outside this working tree; they are not deleted by this audit (preserve history). They must not be confused with `master`.

---

## 15. Evidence links

| Concern | Link |
|---------|------|
| Release status | [`SHOOTING_CHALLENGE_COMPLETION_MASTER.md`](./SHOOTING_CHALLENGE_COMPLETION_MASTER.md) |
| Ops snapshot | [`PROJECT_STATE.md`](./PROJECT_STATE.md) |
| 2026-08-16 path reconciliation | [`prod-completion/2026-08-16/SC-2026-08-16-CURRENT-STATE-RECONCILIATION.md`](./prod-completion/2026-08-16/SC-2026-08-16-CURRENT-STATE-RECONCILIATION.md) |
| Email send plane | [`integrations/email-send-plane.md`](./integrations/email-send-plane.md) |
| Tremendous | [`integrations/tremendous-award-fulfillment.md`](./integrations/tremendous-award-fulfillment.md) |
| Automation inventory | [`AUTOMATION_VERSION_INVENTORY.md`](./AUTOMATION_VERSION_INVENTORY.md) |
| Integrity audit | [`REPOSITORY-INTEGRITY-AUDIT.md`](./REPOSITORY-INTEGRITY-AUDIT.md) |
| Archived / superseded | [`ARCHIVED-AND-SUPERSEDED-FILES.md`](./ARCHIVED-AND-SUPERSEDED-FILES.md) |
| Security / sensitive | [`SECURITY-AND-SENSITIVE-FILES.md`](./SECURITY-AND-SENSITIVE-FILES.md) |
