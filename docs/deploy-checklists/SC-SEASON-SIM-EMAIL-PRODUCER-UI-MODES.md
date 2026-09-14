# Email producer UI inputs — Live Perfect season simulation

**API cannot read Airtable automation `input.config()` values.**  
Mike must set and re-open each automation in the Airtable UI before any email-enabled Perfect execute.

## Welcome Test Mode root cause (T161924Z)

Partial run `SEASON-SIM-PERFECT-20260914T161924Z-mike-schmidt` created a WELCOME handoff with:

- Email Handoff Queue `Test Mode? = true`
- Hub Message `Send Mode = Test`

**Cause:** Automation **078A** sets queue `Test Mode?` from UI input `testMode`:

```js
const testMode = cfg.testMode === undefined ? true : Boolean(cfg.testMode);
```

When the input is absent/undefined (or a non-empty string such as `"false"`), the script writes **true**.  
Automation **079** copies that checkbox into the Hub ingress payload as `testMode`; Hub then sets `Msg Send Mode = Test`.

This is **not** Hub allowlist policy and **not** a harness override.

## Required Live-normal values (re-verify before execute)

| Automation | Input | Required value |
|---|---|---|
| **078A** | `testMode` | boolean **false** (must be present; blank → true) |
| 071, 073, 074, 076, 117 | `testMode` | boolean **false** |
| 072 | `sendModeInput` | `live` |
| 118 | `dryRun`, `sendMode`, `includeSchmidt` | `false`, `Live`, `false` |
| 119 | `dryRun`, `includeSchmidt` | `false`, `false` |
| 079 | `ingressSecret` | present; leave unchanged |

Repo helper (non-writing): `python -m season_simulation prove-perfect-launch` embeds `email_producer_mode_config` checklist.
