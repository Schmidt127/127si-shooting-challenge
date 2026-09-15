# Deployment

**Status:** Authoritative (FUT-058 · 2026-09-15)

## Shooting Challenge website

| Item | Value |
|------|-------|
| Repo | `Schmidt127/127-si-shooting-challenge` |
| Branch | `master` |
| Vercel root | `web/` |
| Public URL | https://www.fairfieldbasketballclub.com/shoot |
| CI | `.github/workflows/web.yml` (lint, typecheck, vitest, build) |
| Repo QA | `.github/workflows/repository-qa.yml` |

**Verify after deploy:** `/shoot` hub · `/shoot/api/health` · auth routes · leaderboard · homework · dashboard sign-in. Confirm env in Vercel dashboard (names in ENVIRONMENT.md).

**Do not** merge to `master` or production-deploy from agents without Mike approval.

## Airtable automations (SC)

1. Edit `airtable/automations/shooting-challenge/*.js` in GitHub  
2. PR / review  
3. Mike pastes **docblock through end** into Automation editor (skip GitHub-only header)  
4. Controlled disposable test  
5. `CHANGELOG.md` if production-impacting  
6. Prefer DEV-first historically; **current mode is Production-only** with Schmidt fixtures  

Promotion packets: `docs/deploy-checklists/`.

## Communications Hub

| Item | Value |
|------|-------|
| Repo | `Schmidt127/communications` |
| Vercel project | `communications` |
| Prod URL | https://communications-two-blue.vercel.app |
| CI | `.github/workflows/ci.yml` |

Verify: `/api/health` · controlled ingest with allowlisted recipient · no unintended Live sends.

## Make / Lambda (non-email)

| Path | Deploy |
|------|--------|
| Upload engine | Make blueprint in `make/blueprints/` + Lambda CodeOnly as documented |
| Tremendous | Keep sandbox / OFF until approved |
| Email Make | **Do not re-enable** |

## Verification checklist (release)

- [ ] `origin/master` SHA recorded in CURRENT-TRUTH when material  
- [ ] Web CI green  
- [ ] Critical automations present in Automation editor (see AUTOMATIONS.md)  
- [ ] Email plane still Hub→Resend  
- [ ] No secrets in git status  
- [ ] Promotion docs updated if Production intentionally changed  
