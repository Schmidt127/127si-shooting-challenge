# Frozen production baseline & future-work categories

**Status:** Authoritative governance (FUT-058 **COMPLETE — CLOSED**)  
**Freeze date:** `2026-09-15`  
**Ecosystem verdict:** `ECOSYSTEM PRODUCTION CLEAN — CURRENT ARCHITECTURE CLOSED`  
**Required current production work:** `NONE`

Do **not** reopen FUT-058 for optional cleanup, tip-SHA hygiene, nested-folder cleanup, or future migration planning.

---

## Frozen pre-migration production baseline

| System | Repository | Full commit SHA |
|--------|------------|-----------------|
| **Shooting Challenge** | `Schmidt127/127-si-shooting-challenge` | `c0a7eba0d62e9582a259eb6ec180745e7d58251c` |
| **Communications Hub** | `Schmidt127/127-communication-hub` | `4485af3b6d89c80f2166eab09df38cc1c788b87f` |

These SHAs are the authoritative **pre-migration production baseline**. Future migration work must start from them. Old chat history is not production truth.

Verified closeout facts (do not re-audit unless new live drift appears):

- SC: 50/50 Airtable automations deployed; Automation **009** at **v1.3 / SC-160**; `/shoot` operational; docs reconciled  
- Hub: 13 tables / 0 Airtable automations; Vercel production READY; Resend healthy; scheduler off; six SC communication paths reconciled  

---

## Documentation hierarchy (cold-start)

| Layer | What it means | Open |
|-------|---------------|------|
| **CURRENT PRODUCTION TRUTH** | What is running now | [`../CURRENT-TRUTH.md`](../CURRENT-TRUTH.md) · this pack’s [`SYSTEM_OVERVIEW.md`](./SYSTEM_OVERVIEW.md) |
| **FROZEN PRODUCTION BASELINE** | Exact SHAs above | **This file** |
| **OPERATIONS** | How to run / troubleshoot current prod | [`OPERATIONS.md`](./OPERATIONS.md) · [`DEPLOYMENT.md`](./DEPLOYMENT.md) · [`../integrations/email-send-plane.md`](../integrations/email-send-plane.md) |
| **OPTIONAL CLEANUP** | Non-blocking cleanliness | § C below · [`CHANGELOG_AND_STATUS.md`](./CHANGELOG_AND_STATUS.md) |
| **FUTURE PRODUCT WORK** | Deferred features | [`../../MASTER_REMAINING_WORK_LIST.md`](../../MASTER_REMAINING_WORK_LIST.md) · [`../127-SI-MASTER-FUTURE-WORK-LIST.md`](../127-SI-MASTER-FUTURE-WORK-LIST.md) |
| **FUTURE MIGRATION** | Replacement architecture — **not begun** | § F below |
| **LEGACY / HISTORICAL** | Make/Gmail and retired paths (labeled only) | Hub `SYSTEM_ARCHITECTURE.md` (LEGACY banner) · SC retired scripts · [`CHANGELOG_AND_STATUS.md`](./CHANGELOG_AND_STATUS.md) |

Authority routing: [`../AUTHORITY-MAP.md`](../AUTHORITY-MAP.md).

---

## Work classification (post FUT-058)

### A. Required current production work

`NONE`

Any claim that the current Airtable / Vercel / Hub / Resend path is incomplete for production correctness contradicts the 2026-09-15 ecosystem verification.

### B. Operational / policy decisions (Mike-controlled)

These do **not** mean the architecture is incomplete:

- Broad participant **Live email cutover**
- Hub / SC **Test Allowlist** and `testMode=true` posture until cutover
- Keep Make **scheduling OFF** for email (email sender is Resend via Hub)

### C. Optional cleanup (NON-BLOCKING)

- COM-CC-007 operational views (Hub)
- Nested Hub `hub/` cleanup
- Historical Make / Webhook **field-name** hygiene (do not confuse with live send path)
- Older docs still saying Hub slug `Schmidt127/communications` → prefer `127-communication-hub`
- Stale tip-SHA text after docs-only merges
- Remote branch cleanup

### D. Future / deferred product work

Preserve as separate backlog (examples; full list in Master Remaining / Future Work List):

- Team Shot Tracker communications  
- Junior Ref communications  
- Season simulation expansion (**SC-SEASON-SIM-001**)  
- Stripe / payment writeback activation (**FUT-053** / MRW-L02)  
- Tremendous production API / awards replacement (**FUT-004** / **FUT-052**)  
- FUT-049, FUT-055–057, FUT-029 (deferred), FUT-048 (deferred), and other valid open FUT items  

### E. Future data cleanup

- **FUT-051** unused-field cleanup / review  

**Do not execute during closeout.** No Airtable fields may be deleted from this governance task.

### F. Future platform migration (SEPARATE — NOT STARTED)

The existing Airtable / Vercel / Communications Hub / Resend architecture is a **frozen, authoritative production baseline**.

Migration implementation has **NOT** begun. FUT-058 does **not** include migration design or build.

Migration planning (when Mike authorizes a new backlog ID) must deliberately cover, **before** implementation:

1. Interview / discovery  
2. Architecture design  
3. Ownership / source-of-truth design  
4. Data-model design  
5. Development workflow  
6. Repository strategy  
7. Environment strategy  
8. Permissions / authentication  
9. Secrets management  
10. Integration inventory  
11. AI-agent access model  
12. Testing strategy  
13. Deployment strategy  
14. Observability  
15. Backup / recovery  
16. Migration strategy  
17. Rollback strategy  
18. Documentation standards  

---

## Preserved requirement — shared challenge platform (future only)

The future 127 Sports Intensity application must support both:

- **Shooting Challenge**
- **Dribble Challenge**

They normally do **not** run simultaneously. They should share common challenge infrastructure rather than becoming two unrelated applications.

Shared infrastructure should include, where appropriate:

- athlete identity  
- enrollment  
- challenge / session model  
- XP Events  
- XP buckets / types  
- levels  
- achievements  
- progression  
- rewards  
- communications  
- reporting  
- administration  

Primary activity metric differs:

| Challenge | Primary activity metric |
|-----------|-------------------------|
| Shooting Challenge | **shots** |
| Dribble Challenge | **dribble minutes** |

This is a **planning constraint for future architecture**, not a current build task. Do **not** design or implement it from FUT-058. Near-term Dribble product options remain recorded under **FUT-050** (decision only); the shared-platform requirement above governs **future migration** planning regardless of near-term packaging choices.
