# Threat Model: SDHS Student Portfolio Site

## Product Surface
This repository is a Vue 3 frontend and FastAPI backend for student portfolio creation, public browsing, authenticated profile editing, administrator curation, server-administrator controls, image upload, GitHub activity lookup, and Supabase-backed authentication/database access.

## Assets and Privileges
- Supabase auth tokens, anon key in the browser, and backend service role keys in environment variables.
- Student profile records, email addresses, visibility/review status, project records, custom HTML, uploaded images, and administrator-issued metadata.
- Administrator privileges (`isAdmin`) and environment-configured server administrator privileges (`PORTFOLIO_ADMIN_EMAILS`).
- Backend-only access to Supabase DB/Auth service role capabilities.
- Public trust in displayed profile metadata, badges, portfolio links, and GitHub activity.

## Trust Boundaries
- Browser to FastAPI API over `/api/*`, with bearer tokens supplied by Supabase auth.
- FastAPI backend to Supabase Auth and DB projects using service role credentials.
- Public unauthenticated profile/list endpoints versus authenticated owner/admin/server-admin endpoints.
- Admin curation endpoints versus server-admin endpoints that can grant administrator status or delete profiles.
- User-provided rich HTML and URL fields rendered in the frontend after backend normalization/sanitization.
- Local upload storage served by FastAPI under `/uploads/*`.

## Attacker-Controlled Inputs
- OAuth identity attributes and bearer tokens presented to backend endpoints.
- Profile fields: name, description, job, tags, GitHub URL, image URL, visibility settings, and custom HTML.
- Portfolio item fields: title, description, contribution, tags, URLs, video URL, image URL.
- Admin/server-admin curation inputs when an authenticated admin account is compromised or misconfigured.
- Upload file names, file bytes, MIME declarations, and image content.
- Query parameters for profile listing, admin filtering, GitHub commit status, and route IDs.
- Frontend route parameters and URL fragments during OAuth callbacks.

## Security Invariants
- Backend service role keys must never be exposed to browser bundles, logs, or public errors.
- State-changing admin and server-admin actions must require the correct backend authorization dependency.
- Regular users must not be able to set administrator-managed curation fields or administrator-issued trust signals.
- Server-admin-only fields (`isAdmin`, school/department policy controls, deletes) must stay out of regular admin mutation paths.
- Public endpoints must only expose approved/visible profiles unless requester is authorized to view private data.
- User-provided HTML and URLs must be sanitized/normalized before storage or rendering.
- Uploads must remain bounded by size/type/path controls and must not allow path traversal or active content execution.
- Authentication storage must match the intended session lifetime and avoid durable token exposure beyond policy.
- CORS must only allow intended frontend origins, especially when bearer-token API calls are used.

## High-Impact Failure Modes
- Authorization bypass in admin/server-admin endpoints enabling badge spoofing, admin grant, profile deletion, or publication of hidden profiles.
- XSS through profile descriptions, custom HTML, badge text, tags, URLs, or uploaded content.
- Service role key leakage through frontend env misuse, error messages, logs, or repository files.
- IDOR allowing one student to modify or view another student's private profile or portfolio items.
- Unsafe Supabase project/env mixing causing public deployment to use local/test projects or wrong credentials.
- Upload path traversal, dangerous file type serving, or storage exposure.
- Overly broad CORS or OAuth callback behavior that leaks tokens or accepts untrusted origins.
