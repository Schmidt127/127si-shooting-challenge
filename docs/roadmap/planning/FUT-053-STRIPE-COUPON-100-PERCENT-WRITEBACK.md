# FUT-053 — Stripe coupon and 100%-payment writeback

**Status:** Launch-critical planning (extends FUT-003 — **do not activate Make / payment workflows here**)  
**Mike approval required before implementation:** **Yes**  
**Created:** 2026-09-14

## Purpose

Implementation-ready plan for Stripe + Fillout + Make + Airtable to correctly handle:

- coupon codes  
- free / **100% discount** registrations  
- payment status + reconciliation  
- idempotency  
- failed or delayed webhooks  
- staff reporting + family-facing enrollment state  

## Current baseline

- FUT-003 Make scenario historically **inactive** pending Fillout early-bird.  
- Payments / Enrollments writeback must remain idempotent on Stripe event id / payment intent.

## Target behaviors

| Case | Expected Airtable outcome |
|---|---|
| Full price paid | Payment = Paid; Enrollment Active (per product rules) |
| Coupon partial | Payment amount = net; coupon metadata stored; Paid |
| 100% / free | Payment = `$0` or `Comp` / `100% discount` status enum (choose one); Enrollment still Active |
| Webhook delay | Enrollment stays Pending until reconcile; staff view flags stale |
| Duplicate webhook | No second Payment row (idempotency key) |

## Idempotency

- Primary key: Stripe `event.id` or `payment_intent` / Checkout Session id.  
- Secondary: Fillout submission id.  
- Make scenario must short-circuit if Payment already exists for key.

## Failure handling

- Log Hub/Make errors; do not mark Paid on soft failure.  
- Staff Interface: “Payment writeback failed” filter.  
- Replay path documented (no silent double-charge).

## Family-facing state

- Private dashboard: Paid / Pending / Comp — never expose Stripe secrets or raw webhook payloads.  
- Public site: registration confirmation copy only.

## Staff reporting

- Coupons used (code, count, revenue forgone).  
- Free enrollments list.  
- Unreconciled sessions > N hours.

## Definition of done (plan)

- This plan accepted by Mike.  
- Activation checklist written under `docs/deploy-checklists/` in a **future** implement PR.  
- No scenario ON from this docs-only work.
