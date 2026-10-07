# 05 — Public Next.js Web App, Design System / Brand, and Media Kit

**Repo:** `Schmidt127/127-si-shooting-challenge` (read-only survey of `/workspace`, master)
**Scope of this inventory:** `web/` (Next.js app served at `https://www.fairfieldbasketballclub.com/shoot`), brand/design-system docs, and `media/` + `tools/airtable/_build_*` publicity tooling.
**Method:** repo-only reading. No live Airtable, no dev server, no MCP.

> All paths below are relative to repo root unless prefixed with `web/` ambiguity is noted. "SC" = Shooting Challenge. "PHA" = Program Homework Assignments. "HC" = Homework Completions. "WAS" = Weekly Athlete Summaries.

---

## 0. Executive orientation

| Fact | Value | Source |
|---|---|---|
| Framework | Next.js 16 App Router, React 19, TypeScript, Tailwind v4, shadcn-style primitives on `@base-ui/react`, `lucide-react`, `tw-animate-css` | `web/package.json` |
| Public mount | `basePath: "/shoot"` (env `NEXT_PUBLIC_BASE_PATH`, default `/shoot`) | `web/next.config.ts`, `web/lib/app-config.ts` |
| Hosting | Vercel, project Root Directory = `web`, production branch `master`; `vercel.json` redirects `/` → `/shoot` (temporary) | `docs/deployment-notes.md`, `web/vercel.json` |
| Data source | Airtable REST (server-only), one base (`AIRTABLE_BASE_ID`), plus Upstash Redis (auth tokens), Resend (magic-link email), optional AWS S3 (Curriculum Hub upload staging) | `web/lib/airtable/client.ts`, `web/lib/auth/*`, `web/lib/curriculum/*` |
| Forms | **No in-app write forms** for registration or daily submissions — both go to Fillout at `forms.fairfieldbasketballclub.com/shoot-playerregistration` and `/shoot-dailysubmissions` (open in new tab) | `web/lib/registration.ts`, `web/components/home/registration-gateway.tsx` |
| Auth | Parent **magic-link** sign-in (SC-112) → HMAC-signed httpOnly cookie `athlete_session`; multi-child household selection via opaque HMAC keys | `web/docs/athlete-auth-architecture.md`, `web/lib/auth/*` |
| Time zone | All dates rendered in `America/Denver`, labelled "MT" | `web/lib/formatters/montana-time.ts` |
| Theme | Primarily **light**; `.dark` tokens exist in CSS but a full dark theme is explicitly disallowed without Mike approval | `APP_CONTEXT.md`, `web/app/globals.css` |
| Legacy hosts | `hoopchallenges.com` / `www.hoopchallenges.com` are normalized to Fairfield host (SC-149) | `web/lib/app-config.ts`, `web/tests/production-smoke.spec.ts` |

Key canonical docs to carry forward: `web/docs/site-hierarchy.md` (route map + nav order), `web/docs/airtable-views.md` (view/revalidate contract), `web/docs/public-data-rules.md` (privacy allowlist), `web/docs/athlete-auth-architecture.md` (auth), `web/docs/seo.md`, `web/docs/sc-card-design-tokens.md`, `web/docs/website-data-contract-and-repair-protocol.md` (WEB-001…WEB-012), `web/docs/production-closeout.md` (release gate), `BRAND_STANDARDS.md`, `APP_CONTEXT.md`, `web/docs/brand-guide.md`.

---

## 1. Complete route inventory

### 1.1 Navigation order (public header)

From `web/lib/navigation/shooting-challenge-nav.ts` and `web/lib/navigation/nav-priority.ts`:

| Group | Routes (in order) |
|---|---|
| PRIMARY (always visible on desktop) | `/` (Overview), `/leaderboard`, `/homework`, `/levels`, `/zoom-meetings` |
| RESOURCES dropdown | `/tutorials`, `/shoutouts`, `/articles` |
| MORE dropdown | `/game-manual`, `/faq`, `/achievements`, `/dashboard/sign-in` (Family Dashboard) |
| Hidden from nav | `/dashboard` (auth-gated), `/public-display`, `/admin/*`, `/athletes/[slug]` (linked from leaderboard rows) |

Footer groups (`web/lib/site-chrome/footer-config.ts`): **Compete** (Leaderboard, Levels, Achievements, Zoom), **Learn** (Homework, Tutorials, Shoutouts, Articles, Game Manual, FAQ), **Account** (Family Dashboard sign-in, Register, Submit Today's Activity). Footer has `FOOTER_CONSENT_COPY` (public standings consent statement) and Fairfield Basketball Club identity. Header CTA pair: "Register for the Challenge" + "Submit Today's Activity" (Fillout) + "Family Dashboard" — asserted by `web/tests/mobile-a11y.spec.ts` and `web/tests/production-smoke.spec.ts`.

### 1.2 Page routes

Rendering column: `revalidate` is Next ISR window (seconds). `0` = always fresh on request (dynamic); `300` = 5 min cache. Airtable fetches additionally pass `next: { revalidate }` per query in `web/lib/airtable/queries.ts` (see §3).

| Route (under `/shoot`) | File | Purpose / what the visitor sees | Airtable tables & views | Rendering | Auth / privacy | Audience |
|---|---|---|---|---|---|---|
| `/` | `web/app/(program)/page.tsx` → `components/home/home-page-view.tsx` | Overview/landing: hero with fact chips (grades 1–12, 100% online, May 1–June 30), **Registration Gateway** (two Fillout CTAs), "What is the Shooting Challenge", "How it works" (6 steps), 8 XP categories, 7 Educational Athletics traits, **About the Coach** (Mike Schmidt bio; FUT-028), participation facts, "For parents" section, challenge dates, **Program Pricing section** (Early Bird / Regular / Late from Airtable), Level Journey teaser, hero progress visual | `Program Instance - Sync` (filter `AND({Program - Linked}='Shooting Challenge',{Status}='Registering')`) for pricing | `revalidate = 0` | Public | Parents, athletes, search engines |
| `/leaderboard` | `web/app/(program)/leaderboard/page.tsx` → `components/leaderboard/*` | Season standings: podium top 3, ranked table (Level → Lifetime XP → Total Shots tiebreak), **Grade Band filter** (`?band=` query synced via `history.replaceState`), level badges, athlete avatars, ranking explanation + tiebreaker legend, link to athlete profile when a public slug exists | `Enrollments` view **`Web - Leaderboard`** (required; fail-closed), `Grade Bands` table, `Levels` | `revalidate = 0` | Public; names only per consent (`Public Display Name`), never rec IDs | Everyone |
| `/athletes/[slug]` | `web/app/(program)/athletes/[slug]/page.tsx` → `components/athlete/athlete-profile-view.tsx` | Public athlete profile (opt-in slug): ProfileHero, freshness notice, At-a-glance, Performance Snapshot, Shooting stat line (FG/2PT/3PT/FT splits), Progression panel (level + XP to next), Homework assignments (public subset), Streak section, **Recent Activity "Game Log"** with category filter + paginated API, **Perfect Week panel**, Weekly performance, Public Awards (only `Public On Web` = true), Achievement collection | `Enrollments` (slug resolve; duplicate slug ⇒ fail-closed 404), `Weekly Athlete Summaries`, `XP Events`, `Submissions`, `Homework Completions`, `Athlete Achievement Unlocks`, `Achievements`, `Award Recipients`, `Levels` | Dynamic per slug | Public but **indexing gated** by `NEXT_PUBLIC_ATHLETE_PROFILE_INDEXING`; excluded from sitemap; `noindex` when flag off | Families, extended family, coaches |
| `/public-display` | `web/app/(program)/public-display/page.tsx` → `components/public-display/public-display-view.tsx` | Kiosk/TV board: top-10 cards + podium, court-lines header (`sc-contrast`), manual **Refresh** button (client, `public-display-refresh.ts`), season label | Same as leaderboard | `revalidate = 0`; `noindex` | Public, hidden from nav | Gym lobby / event screens |
| `/homework` | `web/app/(program)/homework/page.tsx` → `components/homework/homework-catalog-view.tsx` | Compact week-grouped assignment list (SC-162): due status chips, category label, Brief Description, durable links; "This season" schedule from PHA + library content | `Program Homework Assignments` (active rows for current PI), `Homework Library` (`Published?`), `Weeks`, `Grade Bands` | `revalidate = 300` | Public | Athletes, parents |
| `/homework/[id]` | `web/app/(program)/homework/[id]/page.tsx` → `homework-detail-view.tsx` | Assignment detail: Assignment Name (FUT-045), Book/abbrev, topics, age-appropriate bands, Full description / Specific steps / Rationale (rich text renderer), **Docs + Cover image via delivery API** (never raw Airtable CDN), external link hint (Adobe/PDF/Drive), due date, retry actions on load error | PHA + Homework Library | `revalidate = 300`; id validated against `^rec[a-zA-Z0-9]{14}$` | Public | Athletes, parents |
| `/levels` | `web/app/(program)/levels/page.tsx` → `components/levels/levels-ladder-view.tsx` | 12-level ladder (Beginner → G.O.A.T.), level graphic per level, "Your Level Progress" orientation (SC-164), on-card gate requirements | `Levels`, `Level Gate Rules` | ISR | Public | Everyone |
| `/levels/[id]` | `web/app/(program)/levels/[id]/page.tsx` → `level-detail-view.tsx` | Level detail: XP required, badge/graphic, "Advance checklist" (gate rules: homework count, Zoom credit, etc.), prev/next | `Levels`, `Level Gate Rules` | ISR | Public | Everyone |
| `/achievements` | `web/app/(program)/achievements/page.tsx` → `components/achievements/achievements-grid-view.tsx` | Achievement catalog grid (name, description, XP, badge icon via `Badge Icon Name` → `shoot-icons` map) | `Achievements` (Active? + Visible?) | ISR | Public | Everyone |
| `/game-manual` | `web/app/(program)/game-manual/page.tsx` → `components/game-manual/game-manual-view.tsx` | Embedded/linked **Adobe Publish Online** manual (`NEXT_PUBLIC_GAME_MANUAL_URL`, repo default `indd.adobe.com/view/f3dcc153-…`), **live XP Reward Rules table** (never hardcoded), level ladder, quick-start steps | `XP Reward Rules` view `Active Rules Only`, `Levels` | ISR | Public | Parents, athletes |
| `/faq` | `web/app/(program)/faq/page.tsx` → `components/faq/faq-page-view.tsx` | 15 static Q&As (`lib/seo/faq-content.ts`), `<details>` items, deep-link hash support (`faq-hash.ts`), FAQPage JSON-LD, gift-card award commitment (FUT-027) | none | Static | Public | Parents |
| `/tutorials`, `/shoutouts`, `/articles` | `web/app/(program)/tutorials/page.tsx`, `shoutouts/page.tsx`, `articles/page.tsx` → `components/tutorials/*`, `tutorial-media/*` | Three filtered views of one catalog (`Type of Asset` → tutorial / shoutout / article), grouped by category; thumbnails, athlete headshots (shoutouts), video embed (YouTube/Vimeo/direct) | `Tutorials & Assets` (`tblDOTgsWfqPm18bw`), `Associated Program` = Shooting Challenge, publish flag `OK to Publish on Softr` | ISR | Public | Everyone |
| `/tutorials/[id]` | `.../tutorials/[id]/page.tsx` → `tutorial-detail-view.tsx` | Detail with `VideoEmbedPlayer` (iframe for YouTube/Vimeo, `<video>` for direct S3/MP4), descriptions, rationale, VideoObject metadata deferred | same | ISR | Public | Everyone |
| `/zoom-meetings` | `web/app/(program)/zoom-meetings/page.tsx` → `components/zoom-meetings/zoom-meetings-views.tsx` | Week-grouped meetings: status (scheduled / live / recording / recording-pending), join link, host, agenda, cover image (hides 410s), **"Earn makeup XP with the recording quiz"** orientation (cannot earn both live and recording XP) | `Zoom Meetings`, `Weeks` | ISR | Public | Athletes, parents |
| `/zoom-meetings/[id]` | `.../zoom-meetings/[id]/page.tsx` | Meeting detail: recording video/audio URLs, summary, agenda link, times in MT | same | ISR | Public | Athletes |
| `/dashboard/sign-in` | `web/app/(program)/dashboard/sign-in/page.tsx` → `components/auth/sign-in-form.tsx` | Parent email form → magic link; copy tells parents to use their **registration email** (Gmail allowed; SC-151); shows "check your email" state | — | Dynamic | Public page, rate-limited API | Parents |
| `/dashboard/select` | `web/app/(program)/dashboard/select/page.tsx` | Multi-child household picker: list of enrollments for the signed-in email; posts opaque selection key | `Enrollments` by parent email | `force-dynamic` | Session required | Parents |
| `/dashboard` | `web/app/(program)/dashboard/page.tsx` → `components/dashboard/athlete-dashboard-view.tsx` | **Private Family Dashboard**: Family enrollment switcher, section nav, LevelIndicator + ProgressMeter (season goal), XP activity table (paginated), homework section (HC status + coach feedback quotation, FUT-042), video feedback, awards incl. Tremendous gift-card fields, next-action derivation, sign-out; strips legacy `?enrollmentId` from URL; **"Open Homework" POST → `/api/curriculum/start`** when Curriculum Hub configured; placeholder when auth disabled | `Enrollments`, `XP Events`, `Submissions`, `Homework Completions`, `Video Feedback`, `Award Recipients`, `Levels` | Dynamic, `no-store`, `noindex` | Session cookie required; enrollment must belong to session email | Parents (and athletes with parent) |
| `/dashboard/preview` | `web/app/(program)/dashboard/preview/page.tsx` | Staff preview of XP activity for any `?enrollmentId=` | `XP Events` etc. | Dynamic | `SITE_ACCESS_TOKEN` cookie/header | Staff |
| `/admin` | `web/app/admin/page.tsx` → `components/shared/placeholder-page.tsx` | Placeholder; admin roadmap in `web/docs/admin-roadmap.md` (SC-116) | — | Static | Gated by preview token when set | Staff |
| `/admin/diagnostics` | `web/app/admin/diagnostics/page.tsx` | Env/config presence-only diagnostics (secrets redacted), Airtable reachability, auth/redis/resend/hub flags (SC-172) | `whoami` only | `force-dynamic` | `ADMIN_DIAGNOSTICS_TOKEN` or `SITE_ACCESS_TOKEN` | Ops |
| `/robots.txt`, `/sitemap.xml` | `web/app/robots.ts`, `web/app/sitemap.ts`, `lib/seo/sitemap-entries.ts` | Indexing policy by env flags; sitemap excludes athlete slugs, `/public-display`, `/dashboard*`, `/admin*` | — | Static | Public | Crawlers |
| `/not-found` | `web/app/not-found.tsx` (plus route-level `not-found.tsx`) | Branded 404 | — | Static | Public | — |

Rendering wrapper: `web/app/(program)/layout.tsx` → `components/layout/product-shell.tsx` (SkipToContent → SiteHeader → `<main id="main-content">` → SiteFooter, ambient blurred brand blobs). Root `web/app/layout.tsx` loads `Maven_Pro` + `Geist_Mono`, sets `themeColor` to brand blue, favicon/OG/Twitter metadata with basePath-aware icon URLs.

### 1.3 API routes

| Route | File | Method | Purpose | Auth | Notes |
|---|---|---|---|---|---|
| `/api/health` | `web/app/api/health/route.ts` | GET | `{status:"ok"}` liveness; **always public, bypasses preview gate** | none | SC-172 |
| `/api/airtable` | `web/app/api/airtable/route.ts` | GET | Config probe: token/base presence + `whoami` reachability | `SITE_ACCESS_TOKEN` when set | Used by `http-smoke.mjs` |
| `/api/admin/diagnostics` | `web/app/api/admin/diagnostics/route.ts` | GET | JSON of `lib/ops/diagnostics.ts` payload (presence booleans, redaction regexes for tokens/emails/URLs) | `ADMIN_DIAGNOSTICS_TOKEN` or `SITE_ACCESS_TOKEN` | never echoes secret values |
| `/api/athletes/[slug]/game-log` | `web/app/api/athletes/[slug]/game-log/route.ts` | GET | Paginated public Game Log: `?cursor&limit&category` (9 category slugs in `lib/data/game-log-categories.ts`) | Public (slug-gated) | Used by `recent-activity-log.tsx` "load more" |
| `/api/auth/magic-link` | `web/app/api/auth/magic-link/route.ts` | POST | Issue magic link: validate email, check enrollment match, rate-limit (5/email/hr, 20/IP/hr), store token in Redis (15 min TTL), send via Resend | Public | Always returns neutral success to avoid enumeration; `ATHLETE_AUTH_TEST_MODE` redirects mail to `ATHLETE_AUTH_TEST_RECIPIENT` |
| `/api/auth/verify` | `web/app/api/auth/verify/route.ts` | GET | Redeem token → set `athlete_session` cookie (v:2, HMAC, 30-day) → redirect to `/dashboard` or `/dashboard/select` | token | single-use |
| `/api/auth/select-enrollment` | `web/app/api/auth/select-enrollment/route.ts` | POST | Accept opaque HMAC selection key, bind enrollment to session, return app-relative `redirectTo` (bug history: doubled `/shoot/shoot`) | session | SC-112 |
| `/api/auth/sign-out` | `web/app/api/auth/sign-out/route.ts` | POST | Clear cookie | session | |
| `/api/curriculum/start` | `web/app/api/curriculum/start/route.ts` | GET/POST | Mint 2-min handoff token in Redis, `303` to `{CURRICULUM_HUB_URL}/auth/handoff?token=` | session | SSO into external **Curriculum Hub** |
| `/api/curriculum/redeem` | `web/app/api/curriculum/redeem/route.ts` | POST | Hub redeems handoff token → enrollment identity + 4-hour **submit authorization token** | `Bearer CURRICULUM_HANDOFF_SECRET` | server-to-server |
| `/api/curriculum/assignments` | `web/app/api/curriculum/assignments/route.ts` | GET | Scheduled assignments for enrollment/grade band (Assignment Key regex `^[A-Z][A-Z0-9]*(_[A-Z0-9]+)+$`; bands 1-2/3-4/5-6/7-8/9-12) | `Bearer CURRICULUM_INGRESS_SECRET` | contract tests in `lib/curriculum/*.contract.test.ts` |
| `/api/curriculum/homework/submit` | `web/app/api/curriculum/homework/submit/route.ts` | POST | Create/update **Homework Completion** (+ Attempts/Responses) from Hub; headers `Idempotency-Key`, `X-Curriculum-Submit-Authorization` | ingress secret + submit token | Only write path to Airtable in the web app; XP minted by Airtable automations, never here |
| `/api/curriculum/homework/upload-staging` | `web/app/api/curriculum/homework/upload-staging/route.ts` | POST (multipart) | Stage uploads to S3 `CURRICULUM_STAGING_S3_BUCKET` (`CURRICULUM_UPLOAD_MAX_BYTES`), then attach via Airtable content upload API | ingress secret + submit token | optional AWS SDK typed in `types/optional-aws-sdk.d.ts` |
| `/api/curriculum/library/sync` | `web/app/api/curriculum/library/sync/route.ts` | POST | Hub pushes library metadata into `Homework Library` | ingress secret | `lib/curriculum/library-sync-*.ts` |
| `/api/homework/[id]/attachment/[attachmentId]?field=` | `web/app/api/homework/[id]/attachment/[attachmentId]/route.ts` | GET | Re-fetch record and `302` to a **fresh** Airtable CDN URL (CDN URLs expire ~2h); `Cache-Control: private, no-store` | public | `Docs` / `Cover Images` only (`HOMEWORK_ATTACHMENT_FIELDS`) |
| `/api/homework/[id]/link?field=` | `web/app/api/homework/[id]/link/route.ts` | GET | Redirect to `URL` / `URL Additional` with validation | public | durable links (SC-162) |

### 1.4 Middleware / gating

`web/proxy.ts` (Next 16 "proxy" replacement for middleware): when `SITE_ACCESS_TOKEN` is set, every route except `/api/health`, `_next/static`, `_next/image`, `favicon.*`, `brand/*` requires cookie `site_access` (set for 30 days when `?token=` matches). Protected paths list in `lib/security/protected-paths.ts`; dashboard access rules in `lib/security/dashboard-access.ts`; user-facing error mapping in `lib/security/user-facing-errors.ts`.

---

## 2. Components and UI patterns

### 2.1 Layout and chrome

| Pattern | Implementation | Notes |
|---|---|---|
| Shell | `components/layout/product-shell.tsx` | Skip link → header → `main#main-content` → footer; decorative blurred brand blobs behind content |
| Header | `components/site/site-header.tsx`, `components/layout/product-nav.tsx` | Logo link "Fairfield Basketball Club home" → landing; PRIMARY links; RESOURCES / MORE dropdowns (`components/ui/dropdown-menu.tsx`); CTA pair; mobile dialog with `data-testid="mobile-nav-toggle|panel|close"`, `aria-expanded`, Escape to close, scroll lock, focus return to toggle |
| Footer | `components/site/site-footer.tsx`, `lib/site-chrome/footer-config.ts` | Three link groups, Fillout CTAs, consent copy, Fairfield identity, "Back to Fairfield Basketball Club" (`components/layout/back-to-hub-link.tsx`) |
| Page frame | `components/site/program-page.tsx` (`ProgramPage`, `DetailPageShell`), `components/ui/page-frame.tsx` (`PageFrame`, `PageHeader`), `components/site/page-hero.tsx`, `components/site/site-section.tsx`, `components/site/site-container.tsx` | Consistent hero + section rhythm; `SectionMarker` eyebrow labels (`accent-rail.tsx`) |
| Hero decorations | `components/site/leaderboard-hero-decoration.tsx`, `ladder-hero-decoration.tsx`, `components/home/hero-progress-visual.tsx`, `components/brand/basketball-graphic.tsx` | SVG court lines / ladder / 3-D basketball WebP (`public/images/branding/basketball-3d*.webp`) |
| Feature images | `components/site/program-feature-image.tsx` (`ProgramFeatureBanner`) | 1672×941 WebP banners in `web/public/images/shooting-challenge-leaderboard.webp`, `-homework.webp`; `public/images/shoutouts/shoutout_hero.png`; tested by `tests/feature-images.spec.ts` |

### 2.2 Cards, tables, badges, states

| Pattern | Implementation | Notes |
|---|---|---|
| **SC card design system** (FUT-043) | `components/ui/sc-card.tsx` + `web/docs/sc-card-design-tokens.md` | Class builders: `scCardListShell`, `scCardRow`, `scCardStandalone`, `scCardPanel`, `scCardInset`, `scCardEmpty`, `scCardAlert`, `scCardAccordion`, `scCardSectionEyebrow/Title/Heading`; `ScCardList` (ol), `ScCardRowItem`, `ScCardSectionHeader`. Mirrored into Communications Hub emails (`docs/communications-hub/card-tokens-mirror-reference.js`) |
| Generic cards | `components/ui/card.tsx`, `interactive-card.tsx`, `components/site/feature-card.tsx`, `components/catalog/media-panel.tsx` | |
| Tables | `.sc-table` in `globals.css`; `components/leaderboard/leaderboard-table.tsx`; `components/dashboard/xp-activity-table.tsx` | Leaderboard rows link to profile; XP table has load-more + category filter |
| Progress | `components/ui/progress-meter.tsx` (season goal; dashboard weekly goal hardcoded 400 shots in `lib/data/private-dashboard-loader.ts`), `components/athlete/progression-panel.tsx` | Accessible `role="progressbar"` semantics |
| Level badges | `components/leaderboard/level-badge.tsx`, `components/ui/level-indicator.tsx`, `lib/leaderboard/level-styles.ts` (12-step blue→orange→gold ramp, podium accents), `components/levels/level-graphic.tsx` + `lib/levels/level-graphic.ts` | Level names drive style lookup |
| Badges / status | `components/ui/badge.tsx`, `status-badge.tsx` (tones), `stat-tile.tsx` | Homework due chips: `resolveHomeworkDueStatus` / `homeworkDueStatusLabel` |
| Podium | `components/leaderboard/leaderboard-podium.tsx`, `athlete-avatar.tsx` | Top-3 with initials avatar |
| Charts | `components/charts/` is **empty** — no charting library; "charts" are CSS meters and stat tiles | New platform may add real charts |
| Empty / loading / error | `components/ui/empty-state.tsx`, `loading-state.tsx`, `error-state.tsx`; copy centralized in `lib/release/public-surface.ts` (`EMPTY_STATE_COPY`, `LOADING_LABELS`, `ACCESSIBILITY_LABELS`, `LEVEL_GATE_COPY`); `components/homework/homework-retry-actions.tsx`; `components/athlete/profile-freshness-notice.tsx` (degraded-data notice) | SC-113 |
| Coach feedback quotation | `components/coach-feedback-quote.tsx` | FUT-042 — feedback styled as blockquote on web and in emails |
| Rich text | `components/catalog/rich-content.tsx`, `lib/formatters/rich-text.ts` | Airtable long-text → blocks + inline markdown (bold/links) |
| Video | `components/catalog/video-embed-player.tsx`, `lib/formatters/video.ts` (`getYouTubeVideoId`, `getVimeoVideoId`, `getVideoEmbedUrl`, `getProviderPosterUrl`, `isDirectVideoUrl`) | iframe vs `<video>`; `data-canonical-video-url` attribute |
| External link hints | `lib/formatters/external-media.ts` (`isAdobeDocumentUrl`, `isPdfUrl`, `isGoogleDriveUrl`, `shouldOpenExternally`) | |
| Safe images | `components/media/safe-external-image.tsx` | Hides 404/410 Airtable CDN images gracefully |
| Icons | `components/icons/shoot-icons.tsx` (custom line icons), `lucide-react`; achievement badge icons resolved by `lib/achievements/resolve-badge-icon.tsx` from Airtable `Badge Icon Name` | Brand guide: thin white line art in blue circles |
| SEO components | `components/seo/json-ld.tsx`, `catalog-structured-data.tsx`, `detail-structured-data.tsx` | |
| FAQ | `components/faq/faq-details-item.tsx` (`<details>`), `faq-hash.ts` (deep links) | |
| Auth UI | `components/auth/sign-in-form.tsx`, `family-enrollment-switcher.tsx`, `sign-out-button.tsx` | |
| Dashboard | `components/dashboard/dashboard-section-nav.tsx`, `dashboard-xp-section.tsx`, `dashboard-homework-section.tsx` | |

### 2.3 Mobile, accessibility, responsive (SC-148 — complete, production attested 2026-09-04)

- Viewports tested: 375×812, 390×844, 768×1024, 1440×900 (`web/tests/mobile-a11y.spec.ts`, `web/tests/helpers/smoke.ts`).
- Assertions: exactly one `<h1>` per page, horizontal overflow ≤ 8px (smoke ≤ 24px), mobile menu `aria-expanded`, Escape closes + focus returns, 44px minimum CTA height, visible focus cue (outline or box-shadow), labelled sign-in inputs, no `target="_blank"` without `rel="noopener noreferrer"`.
- Skip link `.skip-to-content`; `prefers-reduced-motion` honoured for `.motion-rise`/`.motion-fade`.
- Accessibility checklist in `web/docs/production-closeout.md`; screenshots via `web/scripts/capture-mobile-a11y-shots.mjs`, `capture-landing.mjs`, `tests/public-pages-screenshots.spec.ts`, `tests/landing-screenshots.spec.ts`.
- Optional later: full axe-core CI gate (noted in Master list SC-148).

### 2.4 Things that do **not** exist (verified by grep)

| Capability | Status |
|---|---|
| Print stylesheet / PDF export | None (`@media print`, `window.print` absent) |
| PWA manifest / service worker | None (`public/icons/` is an empty `.gitkeep`; no `manifest.*`) |
| Share buttons / `navigator.share` | None |
| QR codes | None |
| In-app forms for registration/daily submission | None — Fillout |
| Charts library | None |
| Dark mode toggle | None (tokens only) |
| i18n | None (English only) |

---

## 3. Data layer

### 3.1 Airtable client (`web/lib/airtable/client.ts`)

- Server-only; `AIRTABLE_API_TOKEN` never reaches the browser.
- `listAirtableRecords(table, {view, fields, filterByFormula, sort, maxRecords, pageSize, revalidate})` with offset pagination, `fields[]` allowlists, `next: { revalidate }` caching, **429 retry with backoff**, typed `AirtableApiError` (`lib/airtable/errors.ts`).
- Write helpers (used only by Curriculum ingress): create / update / batch / attachment upload via `content.airtable.com`.
- REST normalization rules (lookup arrays, BOM primary field, `Record Id` lookups) in `web/docs/website-data-contract-and-repair-protocol.md`; tested by `lib/airtable/public-rest-contract.test.ts`.

### 3.2 Table / view registry (`web/lib/airtable/public-tables.ts`, `web/docs/airtable-views.md`)

| Table (ID where pinned) | Views / filters used | Consumer |
|---|---|---|
| `Enrollments` (`tbl3PFmwbRoabu1YV`) | **`Web - Leaderboard`** (required; fail-closed if missing); formula filters by `Public Slug`, parent email, `Active?`, `AIRTABLE_ACTIVE_SCHOOL_YEAR` clause | Leaderboard, profile, dashboard, auth |
| `Levels` | all, sort `Sort Order` | Levels, badges, game manual |
| `Level Gate Rules` | active | Level detail gates |
| `XP Reward Rules` | view `Active Rules Only` | Game manual table (`lib/data/xp-rules.ts` groups by Rule Key prefix, dedupes weekly thresholds) |
| `XP Events` | filter on **`Enrollment Record ID`** lookup (NOT `ARRAYJOIN({Enrollment})`), excludes `Duplicate Status = "Duplicate - Remove"`, `Active?` | Game log, dashboard (`lib/data/xp-activity-loader.ts`, 60 s revalidate, chunked linked-ID fetch) |
| `Submissions` | linked from enrollment | Activity dates, Total Shots Counted |
| `Weekly Athlete Summaries` | by enrollment | Weekly performance, Perfect Week panel |
| `Homework Completions`, `Homework Attempts`, `Homework Responses` | by enrollment / submit ingress | Dashboard homework, profile homework, Curriculum submit |
| `Program Homework Assignments` (`tblhA3maf7xOa8EUS`) | `Active?`, Program Instance match, duplicate slot resolution | Homework catalog schedule |
| `Homework Library` (`tblUuxwYlX4EQ9MKE`) | `Published?` | Homework content |
| `Weeks` | by PI | Week grouping/due dates (Start/End in America/Denver) |
| `Grade Bands` (`tblOhHrIqpjcsk2WG`) | active | Leaderboard filter, curriculum band validation |
| `Tutorials & Assets` (`tblDOTgsWfqPm18bw`) | `Associated Program` = Shooting Challenge, `OK to Publish on Softr` | Tutorials/Shoutouts/Articles |
| `Zoom Meetings` | by PI/Week | Zoom pages |
| `Achievements`, `Athlete Achievement Unlocks` | `Active?` + `Visible?` | Achievements, profile collection |
| `Award Recipients` (`tblTyQXl8aEP93ubK`) | **`Public On Web`** checkbox gate (public), full fields incl. Tremendous award fields (private) | Profile awards, dashboard awards |
| `Program Instance - Sync` | `AND({Program - Linked}='Shooting Challenge',{Status}='Registering')` | Pricing (`lib/data/program-pricing.ts`: Price Early Bird / Regular / Late + deadlines) |
| `Video Feedback` | by enrollment (private) | Dashboard video feedback + custom file name display (`lib/video-display-filename.ts`) |
| `Zoom Attendance` | by enrollment | (planned for FUT-057) |

### 3.3 Data modules (`web/lib/data/*`, `web/lib/*`)

| Module | Responsibility |
|---|---|
| `airtable-values.ts` | `asText`, `asNumber`, `asBoolean`, `asUrl`, `linkedRecordIds`, `selectName(s)`, `toAirtableDateKey`, `asOptionalDateKey` — defensive coercion of REST shapes |
| `leaderboard.ts`, `lib/airtable/queries.ts` | `LEADERBOARD_FIELDS`, ranking sort Level → Lifetime XP → Total Shots, dedupe duplicate Active? rows (SC-161) |
| `public-athlete-profile.ts`, `public-athlete-homework.ts`, `public-game-log.ts`, `public-awards.ts`, `profile-glance-summary.ts`, `game-log-presentation.ts` (Extra Credit tagline FUT-031), `game-log-pagination.ts`, `game-log-categories.ts` | Public profile assembly; privacy tests `public-athlete-profile-privacy.test.ts`, `public-missing-fields.test.ts` |
| `private-dashboard-loader.ts`, `athlete-dashboard.ts`, `opaque-dashboard-key.ts` | Private dashboard aggregation (HC/VF/AR fields, badge tones, `deriveNextAction`) |
| `homework.ts`, `homework-resources.ts`, `lib/airtable/pha-repository.ts` | PHA schedule parsing, library mapping, durable link/attachment delivery paths, due status |
| `tutorials.ts`, `tutorial-presentation.ts` | Catalog split by `Type of Asset`; BOM-safe Name read; `extractVideoUrl` from `Link to Video` only |
| `levels.ts`, `lib/levels/level-graphic.ts`, `lib/leaderboard/level-styles.ts` | Ladder + gates + visual ramp |
| `achievements.ts`, `lib/achievements/resolve-badge-icon.tsx` | Catalog + icon mapping |
| `zoom-meetings.ts`, `components/zoom-meetings/zoom-meetings-orientation.ts`, `lib/formatters/meeting.ts` | Status derivation, MT formatting |
| `xp-rules.ts`, `lib/game-manual/config.ts` | Live rules + manual URL |
| `grade-bands.ts`, `lib/airtable/grade-band-queries.ts` | Band list for filter |
| `program-pricing.ts` | Pricing + "what is included" copy |
| `secure-reviewer-url.ts` | Validates Lambda URL pattern `…lambda-url.us-east-2.on.aws/file/rec…` (secure reviewer links) |
| `lib/auth/*` (`config.ts`, `session.ts`, `token-store.ts`, `selection-token.ts`, `enrollment-access.ts`, `redirect-url.ts`, `responses.ts`, `magic-link-email.ts`) | Magic-link auth; defaults 15-min token, 30-day session, rate limits |
| `lib/curriculum/*` (`handoff.ts`, `submit-auth.ts`, `submit-service.ts`, `submit-validation.ts`, `upload-staging.ts`, `library-sync-*.ts`, `grade-band-validation.ts`, `homework-link.ts`) | Curriculum Hub integration |
| `lib/learning-activities/routing.ts`, `types/learning-activities.ts` | LA-001 contract: completion methods (`fillout_questions`, `file_upload`, `video_upload`, `quiz`, `assessment`, `reflection`, `special_assignment`, `mixed`), routing decision to HC, Submission Assets fan-out plan — **future schema, not live** |
| `lib/seo/*` (`metadata.ts`, `program-facts.ts`, `public-program-content.ts`, `faq-content.ts`, `structured-data.ts`, `sitemap-entries.ts`, `athlete-profile-metadata.ts`) | SEO facts: grades 1–12, Fairfield MT, "2026–2027 Shooting Challenge", May 1–June 30, level names; About the Coach; gift-card commitment |
| `lib/release/public-surface.ts`, `public-standings.ts`, `lib/navigation/public-route-readiness.ts` | Release gate constants: `PUBLIC_APP_ROUTES`, `FAMILY_FACING_SMOKE_PATHS`, `FORBIDDEN_CROSSOVER_PRODUCTS`, `SOFTR_CUTOVER_INDICATORS` |
| `lib/ops/diagnostics.ts` | Presence-only diagnostics payload + redaction |
| `lib/brand.ts` | `BRAND_LOGOS` (circle, horizontal; S3 sources), `BRAND_COLORS`, `PROGRAM_COLORS`, `BRAND_TYPOGRAPHY` |
| `lib/app-config.ts` | `withBasePath`, `toAppRouterHref`, `resolveLandingUrl`, `resolveSiteUrl`, legacy host normalization |

### 3.4 Types (`web/types/*`)

`leaderboard.ts`, `levels.ts` (incl. `CatalogAttachment`), `achievements.ts`, `homework.ts` (`HomeworkAssignment` with `urlAvailability`, `docs`, `coverImage`, `gradeBands`, `order`, `homeworkSlot`), `tutorials.ts`, `zoom-meetings.ts`, `xp.ts` (`XpSourceLabel` canonical values: Submission Base, Homework Completion, Video Submission, Perfect Week, Shot Milestone, Zoom Attendance: Base / Bonus 2 / Bonus 3, Zoom Recording; `XpEventSummary` with display-only joins), `public-athlete-profile.ts`, `private-athlete-dashboard.ts`, `athlete.ts`, `airtable.ts`, `learning-activities.ts`, `optional-aws-sdk.d.ts`.

### 3.5 Softr-era fields still consumed

| Field | Table | Note |
|---|---|---|
| `OK to Publish on Softr` | Tutorials & Assets | publish flag (rename deferred — SC-144) |
| `Published?` | Homework Library | |
| `Public Slug`, `Public Display Name`, `Public Missing *` | Enrollments | profile opt-in and missing-data flags |
| `Brief Description - Display`, `Assignment Full Name - Display` | Homework Library | "Presentation" fields (SC-054/SC-117 plan to move all public reads to Presentation fields) |
| BOM-prefixed `\uFEFFName` / field ID `fldduBizp8qAnAMJW` | Tutorials & Assets | primary field quirk |

### 3.6 Environment variables (complete sweep)

| Variable | Purpose | Required? |
|---|---|---|
| `AIRTABLE_API_TOKEN` | Server-only PAT | Yes |
| `AIRTABLE_BASE_ID` | SC base | Yes |
| `AIRTABLE_ACTIVE_SCHOOL_YEAR` | Optional filter clause for season scoping | No |
| `NEXT_PUBLIC_BASE_PATH` | default `/shoot` | No |
| `NEXT_PUBLIC_SITE_URL` | canonical `https://www.fairfieldbasketballclub.com` | Yes (prod) |
| `NEXT_PUBLIC_LANDING_URL` | landing/hub link target | Yes (prod) |
| `NEXT_PUBLIC_ALLOW_SEARCH_INDEXING` | `true` in prod (SC-115) | Yes |
| `NEXT_PUBLIC_ATHLETE_PROFILE_INDEXING` | `true` in prod (FUT-025) | Yes |
| `NEXT_PUBLIC_GAME_MANUAL_URL` | overrides repo default Adobe URL | No |
| `SITE_ACCESS_TOKEN` | preview gate (`proxy.ts`), staff preview, fallback for diagnostics | No |
| `ADMIN_DIAGNOSTICS_TOKEN` | `/admin/diagnostics` (SC-172, pending set) | Prod ops |
| `ATHLETE_AUTH_ENABLED` | turn on magic-link auth | Yes for dashboard |
| `ATHLETE_AUTH_SECRET` | HMAC for cookie + selection keys | Yes |
| `ATHLETE_AUTH_TEST_MODE`, `ATHLETE_AUTH_TEST_RECIPIENT` (default `schmidt@fairfieldbasketballclub.com`) | redirect all magic-link mail during testing | No |
| `ATHLETE_AUTH_DEV_BYPASS` | local dev only | No |
| `ATHLETE_AUTH_RATE_LIMIT_EMAIL_PER_HOUR` (5), `ATHLETE_AUTH_RATE_LIMIT_IP_PER_HOUR` (20) | limits | No |
| `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` | token store (required in prod) | Yes |
| `RESEND_API_KEY`, `RESEND_FROM_EMAIL` | magic-link mail | Yes |
| `CURRICULUM_HUB_URL` | external hub origin (enables "Open Homework") | No |
| `CURRICULUM_HANDOFF_SECRET` | `/api/curriculum/redeem` bearer | With hub |
| `CURRICULUM_INGRESS_SECRET` | assignments / submit / upload / sync bearer | With hub |
| `CURRICULUM_STAGING_S3_BUCKET`, `CURRICULUM_UPLOAD_MAX_BYTES` | upload staging | With hub |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` / `AWS_DEFAULT_REGION` | S3 staging | With hub |
| `NODE_ENV` | | |
| Test-only: `PLAYWRIGHT_BASE_URL`, `PLAYWRIGHT_PORT` (3001), `CI`, `SCREENSHOT_PHASE`, `SCREENSHOT_OUT_DIR`, `SMOKE_BASE_URL`, `SMOKE_OUT`, `SMOKE_REQUIRE_AIRTABLE_CONFIG`, `HOMEWORK_LIVE_INTEGRATION` | | |

Templates: `web/.env.example`, `web/.env.local.example`.

### 3.7 Public data contract (must carry forward)

From `web/docs/public-data-rules.md` and `lib/release/public-surface.ts`:
- Never render Airtable `rec…` IDs in URLs or HTML on public pages (slugs + opaque keys only); smoke tests assert no `rec` in URLs.
- Allowlisted fields only; no parent emails, phones, addresses, payment data, Reason Debug, Source Keys.
- Awards appear publicly only when `Public On Web` is checked.
- Profiles exist only when `Public Slug` is set; duplicate slugs ⇒ 404 (fail-closed).
- Ephemeral Airtable CDN attachment URLs must never be in HTML — use delivery redirects.
- Public pages degrade with freshness notice rather than erroring when secondary data fails.

---

## 4. Brand and design system

### 4.1 Canonical sources

| Doc | Role |
|---|---|
| `BRAND_STANDARDS.md` (v1.0) | Shared 127 SI foundation; **canonical copy lives in `Schmidt127/hoopchallenges-landing`** — compare versions before design work |
| `APP_CONTEXT.md` | This app's route, theme (light), accents, product boundaries |
| `web/docs/brand-guide.md` | Practical guide: logos, iconography, 5 layout patterns, contact (Mike Schmidt 406.590.2677) |
| `web/docs/sc-card-design-tokens.md` | Card system tokens (FUT-043) |
| `.cursor/rules/web-ui-brand.mdc` | Agent rule for web UI |
| `docs/brand-system.md` | **Older**; mentions dark UI default — superseded by APP_CONTEXT light theme |

### 4.2 Colors (`web/lib/brand.ts`, `web/app/globals.css`)

| Token | Hex | Use |
|---|---|---|
| 127 SI Blue (primary) | `#0034B7` | primary buttons, links, header accents, themeColor |
| 127 SI Orange | `#FF8B00` | CTAs, highlights, magic-link email button |
| Charcoal | `#262626` | body text |
| Light Gray | `#F2F2F2` | surfaces |
| Medium Gray | `#C4C4C4` | borders |
| Court Navy (program accent) | `#001A5C` | leaderboard hero/contrast (`.sc-contrast`) |
| Court Tan | `#C4A574` | court-floor accents |
| Court Gold | `#C9A227` | top level / podium gold |
| Level ramp | blue → orange → gold across 12 levels | `lib/leaderboard/level-styles.ts` |

### 4.3 Typography

- Display/body: **Maven Pro** (Google) as substitute for brand face Magistral; loaded via `next/font` in `web/app/layout.tsx`; `.font-display` utility.
- Stats/numerals: **Geist Mono**.
- Headline case and spacing rules in `web/docs/brand-guide.md`.

### 4.4 Logos and imagery

- `web/public/brand/logo-circle-blue-orange.png`, `logo-v1-blue-orange.png`; S3 canonical sources listed in `lib/brand.ts` `BRAND_LOGOS`.
- 3-D basketball `public/images/branding/basketball-3d*.{png,webp}` (`components/brand/basketball-graphic.tsx`, tests in `lib/brand/basketball-assets.test.ts`).
- Feature banners (WebP 1672×941) + shoutout hero; **cartoon/AI images were removed** (WEB-004); leftover ChatGPT-generated PNGs sit unused in `public/images/general/`.
- Icon style: thin white line art inside blue circles; no decorative emoji.
- `next.config.ts` `images.remotePatterns`: `v5.airtableusercontent.com`, `dl.airtable.com`, Make S3 bucket, `i.ytimg.com`, `img.youtube.com`.

### 4.5 CSS utilities and motion (`web/app/globals.css`)

`.skip-to-content`, `.court-lines`, `.shot-arc`, `.sc-contrast`, `.sc-table`, `.btn-primary`, `.btn-secondary`, `.sc-field`/`.sc-input`, `.motion-rise`/`.motion-fade` (disabled under `prefers-reduced-motion`), `@keyframes loading-bar`, shadow scale `shadow-site-md`, Tailwind v4 `@theme` tokens, `.dark` block (unused).

### 4.6 Voice and anti-patterns

- Educational Athletics voice; parent-first clarity; no Airtable/ops jargon (Phase 4 copy review CR-01…CR-18 in `docs/copy-reviews/2026-08-30-phase4-public-pages.md`).
- Program facts single source: `web/lib/seo/program-facts.ts`.
- Anti-AI design rules in `AGENTS.md` (no generic card grids, gradients, filler).

---

## 5. Testing and QA

| Layer | Tooling | Location | Notes |
|---|---|---|---|
| Unit / contract | **Vitest** (node env, `@` alias; also includes `../lib/aws-media-naming/**`) | 106 `*.test.ts` files across `lib/`, `components/`, `app/api/auth/*` | Latest recorded count 493/493 (SC-118). Includes REST contract, privacy allowlists, auth routes, curriculum contracts, SEO, nav readiness |
| E2E | **Playwright** (chromium, `next start -p 3001 -H 127.0.0.1`, `reuseExistingServer`; `PLAYWRIGHT_BASE_URL` for prod) | `web/tests/*.spec.ts` (18 specs): athlete-auth-privacy, athlete-profile, dashboard-privacy, family-dashboard-nav, feature-images, homework-due-date, landing-screenshots, mobile-a11y, multi-child-auth, national-seo, production-smoke, public-experience, public-hardening, public-pages-screenshots, registration-gateway, search-indexing, tutorials-shoutouts-video | `production-smoke` 52/52 against prod; read-only (never submits Fillout or writes Airtable) |
| HTTP smoke | `web/scripts/http-smoke.mjs` | 19 routes incl. 404 probe and `/api/airtable` | JSON summary, exit codes |
| Scripts | `npm run lint`, `typecheck`, `test`, `test:e2e`, `test:smoke`, `test:smoke:prod`, `test:smoke:http`, `test:smoke:http:prod` | `web/package.json` | |
| Ops scripts | `scripts/full-xp-reconciliation.mjs`, `xp-activity-reconciliation-report.mjs`, `xp-activity-live-probe.mjs`, `homework-diagnose.mjs`, `capture-*.mjs` | `web/scripts/` | Read-only Airtable diagnostics |
| Manual QA | `docs/browser-qa/BROWSER-QA-REPORT-2026-07-25.md`; release gate `web/docs/production-closeout.md` (Package 10: lint, typecheck, tests, build, 1440/768/375 screenshots, a11y checklist) | | |
| Audits | `web/docs/public-route-audit-2026-08-30.md`, `seo-audit-report-2026-08-30.md`, `asset-accessibility-audit.md` | | |

---

## 6. Deployment

| Item | Value | Source |
|---|---|---|
| Platform | Vercel; Root Directory `web`; production branch `master`; preview per PR | `docs/deployment-notes.md` |
| Domain | `www.fairfieldbasketballclub.com/shoot` (landing site at root is a separate repo `hoopchallenges-landing`) | `lib/app-config.ts` |
| Redirect | `vercel.json`: `/` → `/shoot` (temporary) | `web/vercel.json` |
| Env management | Vercel dashboard; checklist of prod cutovers in `docs/deploy-checklists/` (e.g. `2026-08-25-web-search-indexing-cutover.md`, `SC-172-health-admin-diagnostics.md`, `SC-109-game-manual-url-verification.md`, `TIER-1-LAUNCH-OPS-RUNBOOK-20260911.md`) | |
| Preview protection | `SITE_ACCESS_TOKEN` cookie gate in `proxy.ts` | |
| Post-deploy verification | `npm run test:smoke:prod`, `test:smoke:http:prod`, health 200 | SC-118, SC-172 |
| Pending ops | Set `ADMIN_DIAGNOSTICS_TOKEN` in Production + diagnostics smoke (SC-172) | Master list |
| Caching | ISR per route; Airtable fetch `revalidate` 0–300 s; XP loader 60 s; private routes `no-store` | `web/docs/airtable-views.md` |

---

## 7. Media / publicity kit

### 7.1 What exists (`media/`, `docs/media-kits.md`)

| Channel | Location | Status (2025–26) | Builder |
|---|---|---|---|
| Newspapers | `media/2025-2026/newspapers/final-packets/01…10-*/` + `*-SEND-READY.zip` | 10 regional packets built (Belgrade/Bozeman, Missoula, North-Central MT, Billings, Butte/Anaconda, Madison County, Bitterroot, Declo/Magic Valley, Wolf Point, Boulder/Clancy/Helena) | `tools/airtable/_build_town_packet.py`, `_build_*_packet.py`, `_build_remaining_packets.py`, `_agent45_media_packets.py` |
| Radio | `media/2025-2026/radio/01…12-*/` (`RADIO-MEDIA-KIT.md` + `EMAIL-TO-STATION.txt`), `BUILD-SUMMARY.md`, `RADIO-KIT-QA-REPORT.md`, `FINAL-RADIO-REVIEW.md`, `DOCX-EXPORT-SUMMARY.md` | 12 market kits | `_build_radio_media_kits.py`, `_export_radio_kits_docx.py` |
| Facebook | `media/2025-2026/facebook/README.md` | Not started | — |
| Photos / captions / award articles / templates | `photos/`, `captions/`, `award-articles/`, `templates/` READMEs | placeholders; headshots live per packet `Photos/` with `photo-download-checklist.csv` | |
| Source data | `newspapers/award-recognition-export.{csv,json}`, `athlete-master-export.*`, `athlete-school-town-index.csv`, `headshot-inventory.*`, `local-newspaper-targets.csv`, `potential-radio-targets.*`, `packet-plan-*.{md,json,csv}`, `master-athlete-coverage-checklist.csv`, `missing-or-ambiguous-athletes.md`, `user-review-needed.md`, `local-media-research-notes.md` | 65 athletes with 10+ counted shots; 91 newspaper rows; 13 radio options | exports from Airtable Award Recipients + Enrollments |
| Path constants | `tools/airtable/media_paths.py` | | |

Each newspaper packet contains: `01 Article - Main Version.docx`, `02 Article - Short Version.docx`, `03 Editor Email.docx/.txt`, `04 Photo Captions.docx`, `05 Headshot Checklist.docx`, `06 Manual Review Checklist.docx`, `Photos/` + `Photos.zip`. Headshot filenames follow `Last_First_School_Grade-N.jpg`.

Manual steps still required today: coach selects stations; article copy pasted where scripts left `PASTE FINAL TEXT FROM CHATGPT HERE`; manual review checklist before zipping.

### 7.2 Platform vision (V2-028, `media/2025-2026/future-enhancements/ROADMAP.md`)

One-click **Generate Media Kits** after awards finalize:
- Config tables: **Media Markets** (slug, communities[], outlets), **Media Outlets** (type newspaper|radio|social, contact), **Season Publicity Settings** (min shots, season label, public stat sources).
- Generator service `generate_media_kits(season_id, channels[], dry_run)`; idempotent via source hash; validation gate = award snapshot compare + headshot coverage; manifest JSON.
- UI: button with channel checkboxes, preview checklist (missing headshots, ambiguous town, duplicates), optional Make/Gmail send after approval; ops-only, not participant UI.
- Dependencies: C-013 S3 canonical headshot URLs, C-022 public display fields, C-012 schema ownership.
- Success: awards-final → send-ready < 1 day, zero eligible athletes missed, new region = config rows not code.

---

## 8. Known gaps and future ideas (IDs)

### 8.1 From `docs/127-SI-MASTER-FUTURE-WORK-LIST.md` (web-relevant)

| ID | One line | Status |
|---|---|---|
| FUT-011 | Athlete page level graphic + hero label polish | Complete |
| FUT-012 | Professional Game Log presentation (XP Event Log) | Complete |
| FUT-013 | Perfect Week activity panel on athlete page | Complete |
| FUT-014 | Homework page redesign + live Homework Library/PHA connection | Complete |
| FUT-015 | Levels page redesign | Complete |
| FUT-016 | Tutorials page redesign (portfolio catalog) | Complete |
| FUT-017 | Zoom Meeting page redesign | Complete |
| FUT-018 | Landing + SC page improvements | Complete |
| FUT-019 | Footer consistency | Complete |
| FUT-020–023 | National-first SEO foundation, homepage SEO, adapt pages, page titles/descriptions | Complete |
| FUT-024 | FAQ + structured org info | Partially complete (Team Shot Tracker FAQ omitted) |
| FUT-025 | Sitemap/indexing/public athlete profiles | Complete (athlete indexing on; sitemap still excludes athletes) |
| FUT-026 | Final Player Manual before launch | Deferred to pre-launch |
| FUT-027 | Program-wide gift-card award commitment (FAQ) | Complete |
| FUT-028 | About the Coach | Complete |
| FUT-029 | Grade-Band Homework Platform + Homework Intake Adapter | **Deferred — do not implement** |
| FUT-031 | Game Log Extra Credit tagline | Complete |
| FUT-033/035/036/037 | Landing copy, navy→brand blue, six program cards, program images (landing repo) | Complete |
| FUT-038 | Global configurable program-category on/off system | Brief needed |
| FUT-039 | Fillout branding/CSS consistency | Complete |
| FUT-042 | Coach feedback as quotation (web + emails) | Complete |
| FUT-043 | Consistent card design system (web + emails) | Complete |
| FUT-044 | Remove redundant Submitted Work card | Complete |
| FUT-045 | Use "Assignment Name" in public UI | Complete |
| FUT-048 | CloudFront custom domain for homework resources | Deferred (optional) |
| FUT-049 | PHA Grade Band removal → Enrollment Grade Band authoritative | Planning pack |
| FUT-050 | Dribble Challenge product decision | Planning |
| FUT-052 | Replace Tremendous for awards | Planning (affects dashboard award fields) |
| FUT-053 | Stripe coupon / 100% payment writeback | Planning |
| FUT-054 | Player Manual + Game Manual Addendum | Launch-critical outline; Mike approval before publish |
| FUT-055 | Interactive Curriculum Hub modernization — one XP path via HC; shadow → dual-run → cutover | Post-launch plan |
| FUT-056 | Welcome email React Email redesign | Planning |
| FUT-057 | **Family private-profile redesign**: accordion (one section open), household-only authZ, full ledgers (XP, homework, video, submissions, streaks, Zoom attendance), family contact view-only v1 | Post-launch spec |
| SC-102/103/104/105/106/107/108/109/110/111 | Airtable-backed public pages, leaderboard, homework, tutorials, levels, achievements, Zoom, game manual, public display, athlete profiles | Live / complete |
| SC-112 | Athlete auth + dashboard (multi-child) | Complete, Mike-verified |
| SC-113 | Loading/empty/error states | Live |
| SC-115 | noindex removal / indexing cutover | Complete |
| SC-116 | Admin roadmap (gated read-only first) | Built in repo (placeholder page) |
| SC-117 | Public Presentation fields consumed by web | Tracked under C-022 |
| SC-118 | Production readiness smoke package | Complete |
| SC-144 | Rename Softr-named publish flag | Deferred |
| SC-148 | Mobile usability + a11y | Complete (optional axe-core gate) |
| SC-149 | Fairfield branding URLs + Family Dashboard nav | Complete |
| SC-151 | Allow Gmail parent emails | Deployed |
| SC-161 | Leaderboard duplicate Active? heal | Complete |
| SC-162 | Homework compact list + durable links | Complete |
| SC-164 | Levels progress UX simplification | Complete |
| SC-165 | Awards + coaching messaging | Complete |
| SC-171 | Daily Submission + Homework Feedback parent presentation (emails/Hub) | Pending prod paste |
| SC-172 | Health + admin diagnostics routes | Deployed; pending token |
| V2-009 | `/shoot` rules + progress hub | Queued |
| V2-028 | Generate Media Kits platform | Queued (Wave 10–11) |

### 8.2 From `web/docs/website-data-contract-and-repair-protocol.md` (WEB backlog)

WEB-001…WEB-012: REST normalization, required-view contract, Presentation-field migration, cartoon image removal (WEB-004, done), duplicate h1 fixes, attachment delivery, freshness notices, Softr flag renames, repair protocol for data drift. (See doc for each line.)

### 8.3 From `web/docs/*`

| Doc | Ideas not yet built |
|---|---|
| `admin-roadmap.md` | Staff auth → read-only aggregates → later writes; diagnostics first slice shipped |
| `project-roadmap.md` | Phases 0–6; Phase 6 = admin tooling + comms |
| `athlete-auth-architecture.md` | Alumni/past-season access policy still open; family contact editing undecided |
| `seo-audit-report-2026-08-30.md` | Deferred VideoObject / Course / Event schema; Google Search Console steps |
| `v2-frontend-readiness.md` | Feature matrix mock vs live — Presentation fields, real season year on public display |
| `asset-accessibility-audit.md` | Dual-h1 fixes (done), remotePatterns hygiene |
| `page-plan.md` | Original page plan incl. per-athlete QR/kiosk ideas (not implemented) |

### 8.4 Gaps observed during this survey (not tracked by an ID)

- No print/PDF export of profiles or leaderboard; no PWA; no share/QR; no charts.
- Weekly shot goal (400) is hardcoded in `private-dashboard-loader.ts` rather than config.
- `components/cards/` and `components/charts/` directories are empty placeholders.
- Stray AI-generated PNGs in `web/public/images/general/` are unreferenced.
- `docs/brand-system.md` contradicts the light-theme rule and should be retired.
- Admin surface is a placeholder; all staff operations happen in Airtable Interfaces / OMNI.
