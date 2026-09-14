# Automation version sync — 035 / 053 / 065 (2026-09-14)

**Scope:** GitHub + docs upward sync only. No Production automation paste. No simulation.

## Authority

Production live Automation Code is runtime authority. Prior GitHub/docs lag was **documentation/mirror lag only** — never a reason to downgrade Production.

## Final identity (live Automations table + GitHub — 2026-09-14 re-read)

| Automation | Version | Deploy marker | Full SHA-256 (LF / API authority) | Notes |
| ---------- | ------- | ------------- | --------------------------------- | ----- |
| **035** | **v1.6** | `SC-SEASON-SIM-001-DEPLOY-20260913C` | `c7c1cf1330689f1f7336e36615af62eb232bc5a104df165448818f9252250677` | Automations-table mirror manually corrected to v1.6; AI Version `v1.6 - 2026-09-13`. Body SHA-256 `6ddaf1bd8803289efbb2cef32114717002eef98ba7771fab0aa4c3d26f3e4e71` matches Mike-attested paste body. |
| **053** | **5.8** | `SC-SEASON-SIM-001-DEPLOY-20260913B` | `bded88f5d40fc16213e70b2928dc96747537c6c4bf38002ab151521260e98dfa` | Exact live↔GitHub match. |
| **065** | **v10.11** | `SC-SEASON-SIM-001-DEPLOY-20260913B` | `0e84172d0f164ce19e3f3e27188eb702e83d6a3a4037705d16a9886f216ef4ac` | Exact live↔GitHub LF match. Prior focused-PR attestation hash `266ca405733a0e6797fedeb03b5fc30b2ceaf092b3bc0d17e9ff6699bf5bf305` is the **same logical bytes with CRLF** line endings. |

## Compare method

Tool: [`tools/readiness/compare_live_vs_github_automations.py`](../../../tools/readiness/compare_live_vs_github_automations.py)

Records per code (not “first version string found”):

1. Automation Code paste-body **SHA-256**
2. **`SCRIPT.version`** (docblock Version fallback)
3. **`deployMarker`** / season-sim deploy token
4. **`lastUpdated`**

Output: [`live-vs-github-automation-compare.json`](./live-vs-github-automation-compare.json)

## Behavioral deltas (live vs prior GitHub)

### 035

- Progressive Settled Through % state machine (`SC-SEASON-SIM-001-DEPLOY-20260913C`) so Threshold XP Ready? can re-enter for 125%/150% after partial awards.

### 053

- `toDateKey` Denver-safe datetime conversion (no UTC ISO-prefix slice) so Week End does not overlap next Week Start — unblocks 50/60-day streaks.

### 065

- v10.10 soft-skip when `Total Homework XP Awarded` not yet positive; v10.11 deploy bump. Protects 064→065 re-entry.

## Automations-table Version Number

Field is **`Version Number - AI Agent`** (`aiText`) — **not writable** via API. Do not attempt to write it. Mirror text refresh (done for 035) regenerates the AI Version.

## Remaining

- Perfect Mike Schmidt simulation still **not approved / not executed**.
