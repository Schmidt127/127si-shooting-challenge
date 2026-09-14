# FUT-052 — Replace Tremendous for awards (decision record)

**Status:** Post-launch (decision only — **do not activate a provider**)  
**Mike approval required before implementation:** **Yes**  
**Related:** FUT-004 (intent), C-028 (historical Tremendous sandbox)  
**Created:** 2026-09-14

## Purpose

Replace Tremendous as the long-term award fulfillment path with a simpler, controllable approach aligned to XP/achievements and parent communication.

## Desired award types / experience (draft)

- Perfect Week / milestone / coach discretionary gift recognition.  
- Parent receives a clear email with what was earned and next steps.  
- Staff can audit who was awarded, when, and which enrollment/source key.

## Options (compare later with quotes)

| Option | Idea | Effort (est.) | Notes |
|---|---|---|---|
| A | Manual / spreadsheet + branded email only | Low | No payment automation |
| B | Hub/Resend “award issued” email + staff fulfillment | Low–Med | Fits current Hub plane |
| C | New gift-card API provider (non-Tremendous) | Med–High | PCI/financial controls |
| D | Keep Tremendous temporarily | — | **Rejected** as future end-state (FUT-004) |

## Integration points

- XP Events / Athlete Achievement Unlocks / Award Recipients.  
- Parent email (Hub/Resend) — allowlist and testMode rules unchanged.  
- Payments / reconciliation if cash-value awards.  
- Audit history (who approved send).

## Security / financial controls

- Dual-control for cash-value sends.  
- No secrets in GitHub.  
- Idempotent award keys (one source → one award email).  
- Staff-only Interfaces for fulfillment status.

## Recommended next step

Lock **Option B** as the default architecture unless Mike requires automated card issuance (then Option C RFP). Do not enable Tremendous production sends for the new season design.

## Definition of done

- Written choice A/B/C.  
- No provider activation from this document alone.
