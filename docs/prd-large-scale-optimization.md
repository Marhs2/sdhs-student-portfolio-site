# Large-Scale Optimization PRD

Created: 2026-04-29
Project: SDHS Student Portfolio Site
Status: Draft for implementation planning

## 1. Executive Summary

### Problem Statement

The portfolio directory is already structured around Vue 3, Vite, FastAPI, Supabase, and GitHub activity lookups, but the product will become harder to keep responsive as profile, portfolio item, image, and GitHub activity volume grows. The current implementation has useful first-pass caching and route-level code splitting, yet it lacks explicit performance budgets, pagination contracts, observability targets, and load-test criteria for larger school-wide usage.

### Proposed Solution

Execute a phased optimization program covering frontend delivery, API/data access, image/media handling, GitHub activity aggregation, cache invalidation, and operational visibility. The implementation should preserve the current user-facing behavior while making performance measurable, enforceable, and resilient under peak browsing and profile-editing traffic.

### Success Criteria

- Public browse route `/` reaches Largest Contentful Paint <= 2.5s and Interaction to Next Paint <= 200ms on a mid-tier mobile device profile in Lighthouse or equivalent lab testing.
- Initial public JavaScript transferred for first browse load is reduced by at least 20% from the 2026-04-29 build baseline, or a written exception explains why the current 44.25 kB gzip app entry is already acceptable.
- Public API p95 latency for `/api/profiles`, `/api/profiles/{id}/bundle`, and `/api/portfolio-items` is <= 500ms under a documented 50 concurrent user read test with warm cache.
- GitHub activity sorting does not block the first profile list render; the page remains usable while activity counts load or fail.
- Existing frontend and backend regression tests pass, with new performance-sensitive behavior covered by focused tests.

### Current Evidence

- Frontend stack: Vue 3.5, Vue Router 4.5, Vite 6.4, Supabase JS 2.49.
- Backend stack: FastAPI 0.104, Supabase Python 2.7, httpx, in-memory TTL cache.
- 2026-04-29 production build completed successfully after sandbox escalation.
- Build baseline:
  - `assets/index-CLbLy8qI.js`: 113.63 kB, 44.25 kB gzip.
  - `assets/authService-BSotIS5e.js`: 211.68 kB, 55.78 kB gzip.
  - `assets/StudioPage-DuFVn14V.js`: 33.08 kB, 12.21 kB gzip.
  - `assets/AdminCurationPage-Cj4wB9y4.js`: 25.24 kB, 8.33 kB gzip.
  - `assets/BrowsePage-BKge4j0K.js`: 13.20 kB, 5.11 kB gzip.
- Existing public cache layers:
  - Frontend public GET cache: 15 seconds.
  - Backend public cache default documented in README: 30 seconds fresh, 300 seconds stale.
- Known implementation anchors:
  - Browse page performs client-side filtering, pagination, and GitHub activity sorting.
  - Profile detail uses `/api/profiles/{id}/bundle` to reduce multiple detail requests.
  - Backend public repository functions cache profiles, profile HTML, portfolio items, and GitHub commit counts in process memory.

## 2. User Experience & Functionality

### User Personas

- Student viewer: browses public portfolios, filters by role or department, opens profiles and projects.
- Student owner: edits a profile, uploads profile images, adds portfolio items, and expects saves to reflect quickly.
- School admin: reviews public visibility, curation, metadata, and profile quality from admin screens.
- Maintainer: deploys frontend/backend services, verifies runtime health, and diagnoses slow requests.

### User Stories

- As a student viewer, I want the directory to render useful content quickly so that I can browse portfolios without waiting for all secondary data.
- As a student viewer, I want filters and pagination to stay responsive with hundreds of profiles so that I can narrow results without input lag.
- As a profile visitor, I want profile detail pages to load profile, HTML, and portfolio items in one predictable flow so that navigation feels direct.
- As a student owner, I want image uploads and profile saves to be bounded and validated so that failed media work does not break editing.
- As an admin, I want curation screens to remain usable as data grows so that review work does not slow down during peak submission periods.
- As a maintainer, I want slow requests and cache behavior to be visible so that optimization regressions can be diagnosed from logs and tests.

### Acceptance Criteria

- Browse first render:
  - Profile cards or loading skeletons appear within 1s on a throttled local run.
  - GitHub activity counts load after the base profile list and never prevent filtering, pagination, or route navigation.
  - Failed GitHub activity lookup shows a non-blocking warning and keeps deterministic fallback ordering.
- Frontend delivery:
  - Auth/Supabase-dependent code is not loaded into anonymous public browse unless required for visible functionality.
  - Route-level chunks remain lazy loaded for admin, studio, auth callback, and profile detail.
  - Any newly introduced browser cache or prefetch policy has an invalidation path after create/update/delete operations.
- API/data access:
  - Public list endpoints support an implementation plan for limit/offset or cursor pagination before profile volume exceeds 500 public records.
  - `/api/profiles/{id}/bundle` returns only fields needed by the current detail page.
  - Backend cache keys cover all query parameters that affect public response shape.
  - Mutations clear affected public caches without forcing unrelated long-lived private data to be reused.
- Media:
  - Uploaded profile images stay within configured byte limits and reject unsupported content.
  - Public image rendering uses lazy loading, async decoding where appropriate, and stable dimensions to reduce layout shift.
  - Future image transformation or CDN work has a documented fallback for existing Supabase-hosted image URLs.
- Observability:
  - Slow API requests already logged at >= 1500ms remain visible.
  - New optimization work adds either tests or measurable logs for cache hit/miss, GitHub lookup duration, or payload size where useful.
- Verification:
  - `npm --prefix portfolio run build` succeeds.
  - `npm --prefix portfolio test` succeeds.
  - `python -m unittest discover -s backend/tests` succeeds.
  - A documented manual smoke path covers browse, profile detail, studio edit, and admin page.

### Non-Goals

- Replacing Vue, FastAPI, Supabase, Vercel, Render, or Northflank.
- Adding a new database, queue, CDN, analytics vendor, or paid monitoring tool without a separate decision record.
- Redesigning the visual identity or information architecture beyond changes required for performance and resilience.
- Changing authentication policy for `@sdh.hs.kr` accounts.
- Removing legacy schema fallback behavior until a separate migration plan confirms it is safe.
- Optimizing for millions of records; this PRD targets school-scale growth first.

### Discovery Questions To Resolve Before Final Implementation

- What is the expected 2026 production scale: public profiles, portfolio items per profile, peak concurrent users, and expected submission periods?
- Which deployment target is authoritative for production performance measurement: Vercel + Render, Northflank split services, or another environment?
- Is GitHub activity sorting a core requirement for the default directory order, or can it become an optional sort that loads only on demand?

## 3. AI System Requirements (If Applicable)

No AI-powered product behavior is required for this optimization program.

### Tool Requirements

- Local build and test tools already present in the repository.
- Browser/Lighthouse or equivalent lab tooling for frontend performance measurement.
- Optional backend load-test tooling, selected without adding runtime dependencies to the app.

### Evaluation Strategy

- Treat any AI-assisted code generation or review as advisory only.
- Evaluate implementation through deterministic tests, build output, performance budgets, and manual smoke checks.
- Do not rely on AI judgments as pass/fail criteria for performance claims.

## 4. Technical Specifications

### Architecture Overview

The application has three primary runtime paths:

1. Anonymous public browsing:
   - Vue route `/` loads profile list from `/api/profiles`.
   - Browser caches public GET responses for 15 seconds.
   - Backend caches public Supabase-derived responses in `TtlCache`.
   - GitHub activity counts are fetched separately through `/api/github/commits`.
2. Profile detail:
   - Vue route `/profiles/:id` resolves auth state.
   - It fetches `/api/profiles/{id}/bundle`, optionally authenticated for private owner/admin access.
   - Backend assembles profile, HTML content, and portfolio items.
3. Editing/admin:
   - Authenticated routes use Supabase auth headers.
   - Mutations clear frontend public GET cache and backend public cache.
   - Admin views reuse profile and curation services.

Optimization should strengthen these paths without changing the public contracts unless the route and service tests are updated first.

### Frontend Requirements

- Maintain route-level lazy imports in `portfolio/src/router/index.js`.
- Audit `authService` and Supabase client import paths so anonymous browse does not eagerly load auth-heavy code unless needed.
- Keep profile list filtering deterministic and testable through pure functions where feasible.
- Add a performance budget document or CI-friendly build check for:
  - Main entry gzip size.
  - Largest route chunk gzip size.
  - CSS chunk count and largest CSS chunk.
- Ensure public GET cache behavior has tests for:
  - Cache hit within TTL.
  - In-flight request deduplication.
  - Cache clear after non-GET mutation.
  - Timeout retry behavior.
- Prefer browser-native features already in use, such as lazy images and `content-visibility`, before adding dependencies.

### Backend Requirements

- Preserve `TtlCache` stale fallback semantics for transient Supabase failures.
- Add or document pagination support for public list endpoints:
  - `/api/profiles?limit=&cursor=` or `/api/profiles?page=&pageSize=`.
  - `/api/portfolio-items?limit=&cursor=` or equivalent.
  - Response metadata must include enough information for next-page loading.
- Review Supabase query shape for:
  - Public profile filters pushed to the database where possible.
  - Portfolio item owner filtering.
  - Avoiding full table scans for admin search once data exceeds documented thresholds.
- Keep legacy missing-column fallback behavior until migration completion is confirmed.
- Keep GitHub API calls bounded:
  - Existing HTTP timeouts remain.
  - Batch lookup continues to deduplicate usernames.
  - Cache key includes username and year.
  - Future enhancement may add partial response streaming or background refresh, but not in MVP.

### Integration Points

- Supabase:
  - `userProfile`, `userHtml`, and `portfoilo` tables.
  - Existing local-only test Supabase guardrails must remain.
- GitHub:
  - GraphQL contributions API through `GITHUB_TOKEN`.
  - Failure must degrade public sorting without making the directory unusable.
- Deploy:
  - Frontend on Vercel or Northflank.
  - Backend on Render or Northflank.
  - Cache-control settings must remain configurable through environment variables.

### Security & Privacy

- Do not expose service role keys, GitHub token, or admin-only fields to the frontend.
- Public endpoints must continue stripping private fields such as profile email and portfolio owner email unless authenticated policy allows access.
- Optimization caches must not mix authenticated/private responses with anonymous public responses.
- Image optimization must preserve current upload validation and content detection behavior.
- Slow-request logging must avoid storing bearer tokens, raw private HTML, or sensitive request bodies.

### Testing Requirements

- Unit tests:
  - Existing backend tests for cache, health/cache headers, auth context, profile bundle, profile visibility, uploads, GitHub commits.
  - Existing frontend service tests for API cache, auth session/domain, directory filters, profile sections, image crop.
- New tests:
  - Pagination contract tests for public profile and portfolio item endpoints when implemented.
  - Frontend tests for non-blocking GitHub activity sort behavior.
  - Cache invalidation tests around profile and portfolio item mutations if behavior changes.
- Performance tests:
  - Build output recorded before and after optimization.
  - One repeatable local Lighthouse or browser trace for `/`.
  - One backend read load test with warm cache and documented fixture size.

## 5. Risks & Roadmap

### Phased Rollout

#### MVP: Baseline and Low-Risk Wins

- Record current build output and API latency baselines.
- Add performance budget documentation.
- Split or defer auth/Supabase-heavy code from anonymous browse if build analysis confirms it is eagerly loaded.
- Ensure GitHub activity lookup is visibly secondary and non-blocking.
- Add focused regression tests around cache behavior and GitHub fallback.

#### v1.1: Data-Scale Read Path

- Add public list pagination contracts.
- Push supported public filters into backend queries where this reduces payload size.
- Add response metadata for client pagination.
- Preserve current client-side filtering behavior for small result sets until paginated UX is fully proven.

#### v1.2: Media and Payload Optimization

- Define image dimension and format recommendations for profile images.
- Evaluate generated thumbnails or CDN image transforms without changing existing URL compatibility.
- Trim profile bundle fields to the current page requirements.
- Add payload-size checks for representative public responses.

#### v2.0: Operational Hardening

- Add cache hit/miss and upstream duration metrics in a privacy-preserving form.
- Add scheduled or background GitHub activity refresh if default GitHub sorting remains a product requirement.
- Add production dashboard/runbook for slow requests, GitHub failures, and Supabase transient errors.

### Technical Risks

- In-memory caches are per process; multi-instance deployments can produce inconsistent cache freshness.
- Aggressive public caching can make student/admin edits appear stale unless invalidation remains conservative.
- GitHub GraphQL rate limits can make default activity sorting unreliable during high traffic.
- Pagination can change UX expectations if search/filter semantics move from full client-side data to server-windowed data.
- Build-size optimization may have small gains if current Vite code splitting is already adequate.
- Legacy schema fallback increases query complexity and can obscure database-index assumptions.

### Remaining Decisions

- Define production performance target environment and network/device profile.
- Decide whether GitHub activity sorting remains the default sort.
- Choose pagination style before implementation.
- Decide whether image optimization is handled by Supabase storage policy, CDN transforms, or client upload preprocessing.
- Decide whether performance budgets should be enforced in CI or kept as documented release checks.
