# Environment variables — names and purpose only

**Status:** Authoritative (FUT-058 · 2026-09-15)  
**Never commit secret values.** Local files: `.env`, `.env.local`, `tools/airtable/.env` (gitignored).

## Shooting Challenge — Vercel / `web/`

| Name | Purpose |
|------|---------|
| `AIRTABLE_API_TOKEN` | Server-side Airtable API access |
| `AIRTABLE_BASE_ID` | Production SC base (`appn84sqPw03zEbTT`) |
| `AIRTABLE_ACTIVE_SCHOOL_YEAR` | Optional school-year filter when used |
| `NEXT_PUBLIC_BASE_PATH` | App base path (`/shoot`) |
| `NEXT_PUBLIC_LANDING_URL` | Club landing absolute URL |
| `NEXT_PUBLIC_SITE_URL` | Absolute `/shoot` site URL |
| `NEXT_PUBLIC_GAME_MANUAL_URL` | Optional game manual override |
| `NEXT_PUBLIC_ALLOW_SEARCH_INDEXING` | Public page robots indexing |
| `NEXT_PUBLIC_ATHLETE_PROFILE_INDEXING` | Athlete profile indexing |
| `SITE_ACCESS_TOKEN` | Optional site preview gate |
| `ADMIN_DIAGNOSTICS_TOKEN` | Admin diagnostics endpoint gate |
| `ATHLETE_AUTH_ENABLED` | Magic-link dashboard auth |
| `ATHLETE_AUTH_SECRET` | Session/token signing |
| `ATHLETE_AUTH_TEST_MODE` | Force test recipient routing |
| `ATHLETE_AUTH_TEST_RECIPIENT` | Allowlisted test inbox |
| `ATHLETE_AUTH_DEV_BYPASS` | Local bypass only |
| `ATHLETE_AUTH_TOKEN_TTL_MINUTES` | Magic-link TTL |
| `ATHLETE_AUTH_SESSION_TTL_DAYS` | Session TTL |
| `ATHLETE_AUTH_RATE_LIMIT_EMAIL_PER_HOUR` | Per-email rate limit |
| `ATHLETE_AUTH_RATE_LIMIT_IP_PER_HOUR` | Per-IP rate limit |
| `RESEND_API_KEY` | Magic-link / site Resend sends |
| `RESEND_FROM_EMAIL` | From address for site Resend |
| `CURRICULUM_HUB_URL` | Curriculum Hub base URL |
| `CURRICULUM_HANDOFF_SECRET` | SC → Hub handoff auth |
| `CURRICULUM_INGRESS_SECRET` | Hub → SC ingress auth |
| `CURRICULUM_STAGING_S3_BUCKET` | Homework upload staging |
| `CURRICULUM_UPLOAD_MAX_BYTES` | Upload size cap |
| `UPSTASH_REDIS_REST_URL` | Auth token store |
| `UPSTASH_REDIS_REST_TOKEN` | Auth token store |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION` | S3 homework delivery when used |
| `HOMEWORK_LIVE_INTEGRATION` | Integration test gate |
| `NODE_ENV` | Runtime mode |

Examples: root `.env.example`, `web/.env.local.example`.

## Communications Hub

| Name | Purpose |
|------|---------|
| `AIRTABLE_TOKEN` / `AIRTABLE_BASE_ID` | Hub base access |
| `SHOOTING_CHALLENGE_BASE_ID` | SC base for writeback |
| `SHOOTING_CHALLENGE_INGRESS_SECRET` | Authenticate SC **079** ingest |
| `HUB_DELIVERY_SECRET` | Authenticate `/api/deliveries/send` |
| `RESEND_API_KEY` | Provider send |
| `EMAIL_FROM` / `EMAIL_REPLY_TO` | From / reply-to |
| `RESEND_WEBHOOK_SECRET` | Provider webhook verify |

## Tools / Lambda / Make (ops)

| Name | Purpose |
|------|---------|
| `AIRTABLE_TOKEN` / `BASE_ID` | Schema export / admin CLIs |
| `UPLOAD_WEBHOOK_SECRET` | Upload engine auth |
| `LAMBDA_FUNCTION_URL` / `LAMBDA_FUNCTION_NAME` | Upload Lambda |
| `S3_BUCKET` | Media bucket |
| `MAKE_DEV_UPLOAD_WEBHOOK_URL` | Dev/upload webhook (non-email) |
| `MAKE_API_TOKEN` / `MAKE_ZONE` | Make tooling (legacy ops; not email) |

## Obsolete / do not treat as current email plane

| Name / class | Notes |
|--------------|-------|
| Gmail Make scenario secrets | Historical email only |
| DEV base ID `appTetnuCZlCZdTCT` | Retired — do not point Vercel at DEV |
| Softr env / tokens | Obsolete front end |

Airtable automation **input variables** (webhook URLs, Hub ingress URL, testMode flags) live in the Automation editor — document in deploy checklists; never commit filled secrets.
