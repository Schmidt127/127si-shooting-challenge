# MASTER REMAINING WORK LIST

**Project:** 127 Sports Intensity Shooting Challenge  
**Repository:** `Schmidt127/127-si-shooting-challenge`  
**Reconciled:** 2026-09-14  
**Authority SHA (docs branch base):** `origin/master` at reconcile time — re-verify after merge  
**Status vocabulary (this document):** `Launch-critical` · `Post-launch` · `Future` · `Deferred` · `Complete / historical`

**Related living docs:** [`docs/CURRENT-TRUTH.md`](docs/CURRENT-TRUTH.md) · [`docs/127-SI-MASTER-FUTURE-WORK-LIST.md`](docs/127-SI-MASTER-FUTURE-WORK-LIST.md) · [`docs/SHOOTING_CHALLENGE_COMPLETION_MASTER.md`](docs/SHOOTING_CHALLENGE_COMPLETION_MASTER.md) · planning packs under [`docs/roadmap/planning/`](docs/roadmap/planning/)

**Historical prior list (superseded as the active roadmap):** [`docs/roadmap/_archive/MASTER_REMAINING_WORK_LIST-pre-20260914.md`](docs/roadmap/_archive/MASTER_REMAINING_WORK_LIST-pre-20260914.md)

---

## Current production facts (2026-09-14)

| Fact | Value |
|---|---|
| Perfect Mike Schmidt season sim | **PASSED** pre-restore acceptance — run `SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt` — **4,980 active XP / 170 events** |
| Formulas after Stage Z | Production-normal bundle restored; no `SEASON-SIM` branches |
| Post-restore XP snapshot | **4,525** is **expected** under Production `NOW()` (future-dated streaks inactive) — **not** a failed season |
| Active PHA | **20** including **Week 9 × 2** |
| Automation version authority | **Published Airtable Automation editor / workflow deployment** (published script header/body + UI) — Automations tracking table is **not** authoritative for script versions |
| SC transactional sim residue | Cleaned to zero after exact-ID cleanup (verify packet on Perfect closeout branch / PR) |
| Three-athlete SC-SEASON-SIM-001 | Still **not executed** as a full three-athlete campaign (distinct from Perfect Mike path) |

Evidence: [`docs/audits/readiness-20260914/FINAL-PASS-SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt.md`](docs/audits/readiness-20260914/FINAL-PASS-SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt.md) · [`docs/audits/readiness-20260914/pre-restore-acceptance-evidence-SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt.json`](docs/audits/readiness-20260914/pre-restore-acceptance-evidence-SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt.json)

---

## How to use this list

1. Treat **this file** as the single non-duplicative **current roadmap**.  
2. Detailed narrative / history stays in `docs/127-SI-MASTER-FUTURE-WORK-LIST.md` and Completion Master.  
3. Each planning pack under `docs/roadmap/planning/` is **plan only** — no implementation from this reconcile task.  
4. **Mike approval required** means stop before schema deletes, provider activation, payment/Make activation, or Production paste.

---

## Launch-critical

| ID | Title | Purpose | Systems | Dependencies | Privacy / security | Definition of done | Mike approval before implement? |
|---|---|---|---|---|---|---|---|
| **MRW-L01** | Tier-1 launch ops paste / verify queue | Confirm live email producers and launch runbook items match GitHub and editor | Automations UI, Hub, Resend, docs runbook | CURRENT-TRUTH email queue | Allowlist / testMode discipline | Mike attests editor versions + smoke send to allowlist only | **Yes** (Production paste / UI) |
| **MRW-L02** | Stripe / Fillout payment writeback readiness (FUT-003 + **FUT-053**) | Paid + coupon + 100%-discount registrations write Payments correctly | Stripe, Fillout, Make, Airtable Payments/Enrollments | FUT-003 inactive scenario; FUT-053 plan | Payment PII, webhook secrets, idempotency | Plan approved; activation is a separate Mike gate | **Yes** |
| **MRW-L03** | Final Player Manual + Game Manual Addendum (**FUT-054** / FUT-026) | Families understand rules before season opens | Docs site / Player Manual assets | Production rules frozen enough to publish | No extra PII in public manual | Outlines approved; publish is separate gate | **Yes** (publish) |
| **MRW-L04** | Fillout / early-bird registration activation decision | Open registration only when payment + ops ready | Fillout, FUT-003/053, public site | MRW-L02 | Payment + guardian contact data | Mike decides open date; no silent activation | **Yes** |

---

## Post-launch

| ID | Title | Purpose | Systems | Dependencies | Privacy / security | Definition of done | Mike approval before implement? |
|---|---|---|---|---|---|---|---|
| **FUT-049** | PHA Grade Band removal and migration | Stop owning athlete grade on PHA; Enrollment Grade Band + Curriculum Hub own differentiation | PHA, Enrollment, web homework/curriculum, 072 filter, operator formulas | Dependency inventory + audit | Avoid wrong-assignment exposure | Migration + audit + Mike delete gate | **Yes** (field delete) |
| **FUT-051** | Unused-field cleanup program (continues FUT-002) | Staged hide → observe → archive → delete with manifests | All Airtable tables | FUT-002 history | Do not delete protected/payment/secret fields | Each batch has exact manifest + Mike UI delete | **Yes** (each batch) |
| **FUT-055** | Interactive Curriculum Hub modernization | Vercel interactive lessons without a second XP path | Curriculum Hub, HC, web auth | FUT-029 deferred scope; Enrollment Grade Band | AuthZ, attachments, minors’ work | Phased rollout plan executed under separate implement PR | **Yes** |
| **FUT-056** | Welcome email visual redesign (React Email) | Replace plain welcome with branded, accessible template | 078A / Hub / Resend | Brand standards; allowlist safety unchanged | No routing/safety changes | Preview approved; paste is separate | **Yes** (live paste) |
| **FUT-057** | Family private-profile redesign | Accordion private dashboard; household-only authZ; full XP/HW/video/submission ledgers | `web/` private routes, Airtable reads | Auth session model | **Strict household isolation**; staff-only fields | Spec approved; build is separate | **Yes** (ship) |
| **FUT-004 / FUT-052** | Replace Tremendous for awards | Simple automated award emailer / provider replacement | Awards, email, Payments audit | FUT-004 intent; FUT-052 decision record | Financial controls, audit trail | Decision locked; provider activation separate | **Yes** |

---

## Future

| ID | Title | Purpose | Systems | Dependencies | Privacy / security | Definition of done | Mike approval before implement? |
|---|---|---|---|---|---|---|---|
| **FUT-050** | Dribble Challenge product decision | Choose module-in-SC vs own base/app; minutes not shooting XP | Product architecture | Shared enrollment/email/Zoom patterns | Separate athlete data if own base | ADR accepted | **Yes** (architecture) |
| **FUT-010** | Delete Airtable intake attachments after verified S3 upload | Reduce Airtable attachment retention | Make/upload, S3, Assets | Verified upload path | Attachment privacy | Controlled cleanup with dry-run | **Yes** |
| **FUT-025** | Athlete consent / indexability | Public athlete pages only with consent | SEO, athlete pages | SC-115 indexing complete | Minors / consent | Policy + implementation | **Yes** |
| **FUT-038** | Global configurable program-category on/off | Config-driven program categories | Config, web | Decision worksheet | Low | Config live | **Yes** |
| **SC-SEASON-SIM-001** | Three-athlete full-season simulation | Combined Perfect / Recovery / Edge proof | Season sim harness | Perfect path proven; cascade fixes | Allowlist email only | Mike says `RUN 3-ATHLETE SEASON SIMULATION` + pass | **Yes** (exact phrase) |

---

## Deferred

| ID | Title | Purpose | Notes |
|---|---|---|---|
| **FUT-029** | Grade-band homework platform / intake adapter | Broader homework platform | **Deferred** — do not implement in this reconcile; see FUT-055 for interactive Hub planning only |
| **FUT-048** | CloudFront custom domain for homework resources | Custom CDN domain | **Deferred** — not launch-blocking |
| **FUT-033–037** | Landing hub Youth Programs / Coach Tools copy & design | Landing repo work | **Wrong repo** for implementation — `hoopchallenges-landing` |

---

## Complete / historical (selected — do not re-open)

| ID | Title | Status note |
|---|---|---|
| **SC-SEASON-SIM-PERFECT-202231Z** | Perfect Mike Schmidt season simulation | **Complete / historical** — pre-restore **4980 / 170**; cleaned; formulas restored |
| **SC-SEASON-SIM-002** | Athlete 1 season sim infrastructure | **Complete / historical** — package closed; do not rerun T122531Z |
| **SC-167 / 168 / 169** | Season sim discrepancy wave | **Complete / historical** |
| **SC-PW-E2E / MRW-A01** | Perfect Week E2E live proof | **Complete / historical** |
| **FUT-001** | Homework assignment identity | **Complete / historical** (paste live) |
| **FUT-030 / OPS-PURGE-20260905** | Transactional resets | **Complete / historical** |
| **SC-065 calendar (18 PHA era)** | Early Bird + Weeks 1–8 only | **Superseded** — live PHA is **20** including Week 9 ×2 |
| **“Season sim NOT EXECUTED” (pre-20260914 Perfect)** | Prior roadmap claim | **Superseded** for Perfect Mike path; three-athlete remains not executed |
| **Automations table as version authority** | Pre-editor-authority claims | **Superseded** — editor is version authority |

Full historical detail: archive file above + Master Future Work List narrative entries.

---

## New planning packs (created 2026-09-14)

| ID | Document |
|---|---|
| FUT-049 | [`docs/roadmap/planning/FUT-049-PHA-GRADE-BAND-REMOVAL.md`](docs/roadmap/planning/FUT-049-PHA-GRADE-BAND-REMOVAL.md) |
| FUT-050 | [`docs/roadmap/planning/FUT-050-DRIBBLE-CHALLENGE-DECISION.md`](docs/roadmap/planning/FUT-050-DRIBBLE-CHALLENGE-DECISION.md) |
| FUT-051 | [`docs/roadmap/planning/FUT-051-UNUSED-FIELD-CLEANUP-PROGRAM.md`](docs/roadmap/planning/FUT-051-UNUSED-FIELD-CLEANUP-PROGRAM.md) |
| FUT-052 | [`docs/roadmap/planning/FUT-052-REPLACE-TREMENDOUS-DECISION.md`](docs/roadmap/planning/FUT-052-REPLACE-TREMENDOUS-DECISION.md) |
| FUT-053 | [`docs/roadmap/planning/FUT-053-STRIPE-COUPON-100-PERCENT-WRITEBACK.md`](docs/roadmap/planning/FUT-053-STRIPE-COUPON-100-PERCENT-WRITEBACK.md) |
| FUT-054 | [`docs/roadmap/planning/FUT-054-PLAYER-MANUAL-AND-GAME-ADDENDUM.md`](docs/roadmap/planning/FUT-054-PLAYER-MANUAL-AND-GAME-ADDENDUM.md) |
| FUT-055 | [`docs/roadmap/planning/FUT-055-INTERACTIVE-CURRICULUM-HUB.md`](docs/roadmap/planning/FUT-055-INTERACTIVE-CURRICULUM-HUB.md) |
| FUT-056 | [`docs/roadmap/planning/FUT-056-WELCOME-EMAIL-REACT-EMAIL.md`](docs/roadmap/planning/FUT-056-WELCOME-EMAIL-REACT-EMAIL.md) |
| FUT-057 | [`docs/roadmap/planning/FUT-057-FAMILY-PRIVATE-PROFILE.md`](docs/roadmap/planning/FUT-057-FAMILY-PRIVATE-PROFILE.md) |

---

## Next three implementation decisions for Mike

1. **Activate / verify payment path** — approve FUT-053 plan scope (coupons + 100% discount) and whether FUT-003 Make can be activated for early-bird.  
2. **Player Manual publish gate** — approve FUT-054 outlines and freeze which Production rules the public manual must match.  
3. **PHA Grade Band migration timing** — approve FUT-049 sequence (eligibility moves to Enrollment + Curriculum Hub) before any field hide/delete.
