# FUT-055 — Interactive Curriculum Hub modernization

**Status:** Post-launch planning (**do not implement FUT-029**; **do not change current homework path**)  
**Mike approval required before implementation:** **Yes**  
**Created:** 2026-09-14

## Purpose

Plan integration of the newer Curriculum Hub and Vercel-authored interactive lessons with existing Homework Completions — **one XP path only**.

## Canonical ownership

| Artifact | Owner |
|---|---|
| Weekly schedule row | PHA (SC base) |
| Lesson content / interactive module | Curriculum Hub + Vercel lesson app |
| Athlete attempt / grade band | Enrollment Grade Band |
| Completion + coach score | Homework Completions (SC) |
| XP | Existing HC → XP Event automations only |

## No second XP path

Interactive submit must **create or update** the same HC record shape that production automations already settle. Never mint XP Events from the lesson app directly.

## Grade-band differentiation

Driven by **Enrollment.Grade Band** (+ Hub content variants). Aligns with FUT-049 (remove PHA Grade Band ownership).

## Auth / privacy / attachments / feedback

- Authenticated family session; household-only enrollment access.  
- Attachments: prefer existing S3/upload patterns; no unbounded Airtable attachment growth.  
- Coach feedback remains on HC / staff Interfaces.  
- Minors’ responses treated as private.

## Migration / phased rollout

1. Shadow: interactive lesson writes draft HC fields behind feature flag.  
2. Dual-run: compare interactive HC vs classic intake for allowlisted athlete.  
3. Cutover per Program Instance or Week.  
4. Rollback: disable flag; classic path remains authoritative.

## Definition of done (plan)

- Ownership matrix accepted.  
- Explicit “no direct XP” rule in implement PR checklist.  
- FUT-029 remains Deferred until Mike reopens.
