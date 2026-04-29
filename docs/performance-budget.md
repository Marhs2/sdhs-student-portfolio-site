# Performance Budget

Created: 2026-04-29

This budget turns the large-scale optimization PRD into release checks. Update the baseline after intentional architecture changes, and keep exceptions written down instead of letting bundle and API costs drift quietly.

## Frontend Build Budget

Run:

```powershell
npm --prefix portfolio run build
```

Current verified build after the first optimization pass:

| Asset | Budget | 2026-04-29 Current |
| --- | ---: | ---: |
| Main app entry gzip | <= 45 kB | 44.37 kB |
| Auth/Supabase async chunk gzip | <= 58 kB | 55.80 kB |
| Largest route chunk gzip | <= 14 kB | 12.21 kB |
| Largest CSS chunk gzip | <= 3.5 kB | 2.98 kB |

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

