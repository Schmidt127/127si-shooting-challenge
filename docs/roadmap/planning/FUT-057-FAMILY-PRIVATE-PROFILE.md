# FUT-057 — Family private-profile redesign

**Status:** Post-launch (implementation specification — **do not build UI or alter data access here**)  
**Mike approval required before ship:** **Yes**  
**Created:** 2026-09-14

## Purpose

Specify the authenticated family profile experience: accordion UX, strict household authorization, and complete athletic participation ledgers.

## UX

- Accordion: **only one major section open at a time**.  
- Clear loading, empty, and privacy/error states.  
- Mobile-first; brand-consistent with private dashboard.

## Authorization (non-negotiable)

- Logged-in family session may see **only** its own athlete(s) and household information.  
- Server-side Airtable filters must enforce household/enrollment ownership (never trust client-supplied athlete ids alone).  
- No cross-family leakage in lists, search, or error messages.

## Sections (content)

| Section | Contents |
|---|---|
| Family | Names, phones, emails, addresses, contact details |
| Athletes | Grade, school, grade band, enrollment status, program details |
| XP ledger | Every awarded XP Event in a complete table |
| Homework | Assignment, status, coach feedback, score/award detail |
| Video feedback | Status, coach feedback, award detail |
| Submissions | Complete history |
| Streaks & weekly thresholds | Current + historical as available |
| Zoom attendance | Attendance records for the household athletes |

## Field visibility matrix (draft)

| Class | Examples | Family-viewable? |
|---|---|---|
| Family contact | phones, emails, address | Yes (view); **edit later decision** |
| Athlete profile | grade, school, grade band | Yes |
| XP Events | amount, reason public, date, source type | Yes (public reason only) |
| XP debug | Reason Debug, internal keys | **Staff-only** |
| Payment amounts / Stripe ids | — | Staff-only (or high-level Paid/Pending) |
| Coach private notes | internal | Staff-only unless marked parent-facing |
| Automation / Source Keys | — | Staff-only |

## Later decision (explicit open question)

May families **edit** contact information, or **view only**? Default for v1: **view only** until a writeback + verification design exists.

## Definition of done (spec)

- This spec accepted.  
- Implement PR must include authZ tests proving cross-household denial.  
- No UI ship from this docs-only task.
