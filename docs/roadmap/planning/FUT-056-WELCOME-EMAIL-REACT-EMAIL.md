# FUT-056 — Welcome email visual redesign (React Email)

**Status:** Post-launch (design/technical brief — **do not change live producers**)  
**Mike approval required before live paste:** **Yes**  
**Created:** 2026-09-14

## Purpose

Replace the plain welcome email with branded **React Email** templates while leaving recipient-routing and safety controls unchanged.

## Brand direction

- Follow `BRAND_STANDARDS.md` + `APP_CONTEXT.md` (light-first, 127 SI, no generic AI purple/cream tropes).  
- Hero: program clarity + athlete first name; one primary CTA (dashboard / login).  
- Mobile-first single column; large tap targets.

## Accessibility

- Semantic headings; sufficient contrast; alt text for logo; no critical info in images only.  
- Plain-text fallback part required.

## Dynamic content

- Athlete name(s), guardian greeting, Program Instance name, season dates, dashboard link.  
- No other families’ data; no staff-only fields.

## Test / preview / approval

1. Render in React Email preview.  
2. Send to allowlisted `schmidt@fairfieldbasketballclub.com` only.  
3. Mike visual approve.  
4. Paste producer only after approval (separate implement task).

## Hub / Resend compatibility

- Keep Integration Events / Hub payload contract.  
- Preserve `testMode` / allowlist / EHQ gates (078A path).  
- **No** changes to recipient-routing or safety controls in this redesign.

## Definition of done (brief)

- Brief accepted; sample HTML preview stored under `docs/` or `web/emails` in a future PR.  
- Live paste is a separate Mike-gated step.
