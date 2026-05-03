# Security Hardening Pass - 2026-05-03

## Scope

This pass reviewed the SDHS student portfolio site against the current repo
security policy, Linear project constraints, and public API security guidance.

Inputs used:

- `SECURITY.md`: in-scope backend auth/authz, admin APIs, Supabase boundaries,
  public/private response shaping, environment and secret handling.
- Linear project `SDHS Student Portfolio Site Optimization`: preserve no service
  role exposure, no admin-only fields in public responses, and no mixing of
  authenticated/private cache with public cache.
- OWASP API Security Top 10 2023: API1 object authorization, API3 object
  property authorization, API4 resource consumption, API5 function
  authorization, API8 security misconfiguration.
- Supabase docs: service role/secret keys are backend-only and bypass RLS; RLS
  should be enabled for exposed schemas.

Reference URLs:

- https://owasp.org/API-Security/editions/2023/en/0x11-t10/
- https://supabase.com/docs/guides/getting-started/api-keys
- https://supabase.com/docs/guides/database/postgres/row-level-security
- https://linear.app/docs/private-teams

## Attack Scenarios Tried

### Scenario 1: Unauthenticated server-admin API access

Attack goal: read privileged profile data or operational admin fields without a
valid session.

Attempt:

- Browser automation from the deployed frontend called
  `GET https://sdhs-student-portfolio-site.onrender.com/api/server-admin/profiles`.

Result:

- `401 Unauthorized`
- `Cache-Control: no-store, private`

Disposition: blocked by `require_server_admin` and private API cache headers.

### Scenario 2: Public/private profile data exposure

Attack goal: use public profile and bundle endpoints to read hidden owner
fields such as `email`, `isAdmin`, `isVisible`, or `reviewStatus`.

Code evidence:

- Public profile responses pass through `_public_profile_payload`.
- Public portfolio items strip `ownerEmail`.
- Existing tests cover public bundle/profile response shaping.

Disposition: no new code change needed in this pass.

### Scenario 3: Stored HTML/script injection through profile HTML

Attack goal: store active HTML that executes in a visitor browser.

Code evidence:

- `HtmlContentPayload` limits HTML to 60,000 characters.
- `save_profile_html` calls `clean_rich_html` before storing.
- `ProfileHtmlSurface.vue` renders inside a sandboxed iframe with a restrictive
  `srcdoc` CSP: `default-src 'none'`, `script-src 'none'`, `connect-src 'none'`,
  `form-action 'none'`.
- Existing tests cover script removal, active-content removal, and obfuscated
  `javascript:` URLs.

Disposition: no new code change needed in this pass.

### Scenario 4: Authenticated write-resource exhaustion

Attack goal: use a valid student account to repeatedly call write endpoints and
force repeated Supabase writes or HTML sanitization/storage work.

Pre-fix finding:

- The existing middleware rate-limited repeated auth failures and selected
  sensitive mutations, but student write routes such as `/api/profiles/*` and
  `/api/portfolio-items/*` were not classified as sensitive mutations.

Fix:

- Added profile and portfolio write paths to `_is_sensitive_mutation_request`.
- Added regression coverage that `/api/profiles/7/html` and
  `/api/portfolio-items/11` are sensitive mutations.

Post-fix result:

- `backend/tests/test_runtime_logging.py`: 12 passed.
- `python -m compileall backend/app`: passed.
- Full backend pytest run executed all 125 collected tests; 124 passed before a
  Windows/OneDrive pytest temp/cache permission failure interrupted clean
  completion. The failing condition was test infrastructure path access, not an
  app assertion.

## Changed Files

- `backend/app/__init__.py`
- `backend/tests/test_runtime_logging.py`
- `docs/security-hardening-2026-05-03.md`

## Remaining Notes

- The live production write exploit was not attempted because sending a PUT
  XSS/write payload to the deployed backend could alter real data. The write
  scenario was verified with local regression coverage instead.
- The Browser Use plugin's preferred Node REPL runtime was not available in this
  Codex App session, so browser validation used the available Playwright browser
  MCP fallback.
