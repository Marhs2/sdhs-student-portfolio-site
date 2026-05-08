# Finding Discovery Report

## Scope
Diff-scoped scan of the current working tree changes for administrator-issued profile badges and browser session persistence policy.

## Reviewed Diff Surfaces
- Backend schema validation: `backend/app/schemas.py`
- Backend normalization and database mapping: `backend/app/normalization.py`, `backend/app/repositories.py`
- Admin and server-admin authorization support: `backend/app/routers/admin_profiles.py`, `backend/app/routers/server_admin_profiles.py`, `backend/app/auth.py`
- Public profile response shaping: `backend/app/routers/profiles.py`
- Frontend admin badge input and display: `portfolio/src/pages/AdminCurationPage.vue`, `portfolio/src/features/directory/ProfileCard.vue`, `portfolio/src/pages/StudentProfilePage.vue`, `portfolio/src/services/profileService.js`
- Auth persistence change: `portfolio/src/services/supabaseClient.js`, `portfolio/src/pages/AuthCallbackPage.vue`, `portfolio/src/services/authService.js`

## Candidate Review

### Badge privilege spoofing
- Source checked: normal student profile create/update payloads and admin profile update payloads.
- Closest controls: `ProfilePayload` and `ProfileUpdatePayload` do not include `badges`; regular admin endpoint uses `require_admin`; server-admin endpoint uses `require_server_admin`.
- Discovery result: suppressed. The only backend write path for `badges` is through administrator profile update payload classes and protected admin routers.

### Badge XSS or HTML injection
- Source checked: badge normalization, public response propagation, Vue rendering sites.
- Closest controls: badge values are treated as strings, length/count bounded by schema, deduplicated in backend normalization, and rendered with Vue interpolation rather than `v-html`.
- Discovery result: suppressed. No executable HTML sink was introduced for badge text.

### Public sensitive data exposure
- Source checked: public profile payload filtering and profile normalization.
- Closest controls: `PUBLIC_PROFILE_HIDDEN_FIELDS` continues to hide email/admin/visibility/review status; `badges` is intended public administrator-issued metadata.
- Discovery result: suppressed. The diff exposes only the requested public trust signal, not hidden privilege state.

### Database schema fallback privilege weakening
- Source checked: `PROFILE_COLUMNS`, no-badges fallback, and legacy fallback in profile select/update.
- Closest controls: missing-column fallback only drops unsupported `badges` writes when the migration is not applied; existing admin-only fields still follow the prior extended or legacy update paths.
- Discovery result: suppressed. This is an availability/backward-compatibility behavior, not an authorization bypass.

### Session persistence policy regression
- Source checked: Supabase client options and auth callback/session handling.
- Closest controls: `persistSession: false` prevents durable browser storage. Existing bearer-token backend validation remains server-side through Supabase Auth.
- Discovery result: suppressed. The change reduces durable token exposure; it may shorten UX session lifetime but does not create a security vulnerability.

## Result
No technically plausible security finding candidates survived discovery. Per the Codex Security workflow, validation and attack-path analysis were not run because there were no candidates to validate.
