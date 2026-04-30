# Performance Budget

Created: 2026-04-29

This budget turns the large-scale optimization PRD into release checks. Update the baseline after intentional architecture changes, and keep exceptions written down instead of letting bundle and API costs drift quietly.

## Frontend Build Budget

Run:

```powershell
npm --prefix portfolio run build
```

Current verified build after the browse compute-path optimization pass:

| Asset | Budget | 2026-04-30 Current |
| --- | ---: | ---: |
| Main app entry gzip | <= 45 kB | 44.36 kB |
| Auth/Supabase async chunk gzip | <= 58 kB | 54.66 kB |
| Largest route chunk gzip | <= 14 kB | 10.81 kB |
| Largest CSS chunk gzip | <= 3.5 kB | 3.13 kB |

Release rule: if any asset exceeds budget, either reduce it in the same change or add a short note in the PR/commit explaining why the increase is intentional.

## Runtime Budget

Public browse `/`:

- Render skeletons or profile cards within 1 second on a throttled local browser run.
- Do not block profile list rendering on GitHub activity counts.
- Do not eagerly load Supabase auth code during the first paint of anonymous browse.
- Keep public GET cache intact after read-only secondary lookups such as GitHub activity batches.

Public API:

- Warm-cache p95 for `/api/profiles`, `/api/profiles/{id}/bundle`, and `/api/portfolio-items`: <= 500ms under a documented 50 concurrent read test.
- Slow request logging at >= 1500ms must remain enabled.
- Public and authenticated cache entries must stay separated.

## Verification Checklist

- `npm --prefix portfolio test`
- `npm --prefix portfolio run build`
- `python -m unittest discover -s backend/tests`
- Manual smoke: browse, profile detail, studio edit, admin page.

## 2026-04-29 Optimization Notes

- Browse filtering and sorting now run through a tested pure utility that prepares profile search text, GitHub usernames, and commit counts before pagination/card rendering.
- Browse card images keep lazy loading and now include async decoding plus fixed intrinsic dimensions to reduce decode pressure and layout ambiguity.
- GitHub activity lookups still batch at 20 users, but large batches now overlap with bounded client concurrency of 2 so secondary sorting updates sooner without flooding the API.
- Backend public profile detail paths now skip a redundant public-owner email scan after the requested profile has already been verified as visible and approved.
- Backend in-memory TTL caches now support entry caps; public API cache is capped at 512 entries and GitHub commit cache at 2048 entries to bound long-running process memory growth.

## 2026-04-30 Optimization Notes

- Public service modules now lazy-load auth headers so anonymous browse no longer pulls `authService` and Supabase auth into the main entry bundle.
- The production build emits a separate `authService` async chunk and keeps the main entry under the documented gzip budget.
