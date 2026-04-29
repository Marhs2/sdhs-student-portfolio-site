# Security Policy

## Supported Versions

This project is currently pre-1.0 and deployed from the active main branch.
Security fixes are applied to the currently deployed version only.

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |
| < 0.1   | No        |

## Reporting a Vulnerability

Please do not open a public issue for a suspected vulnerability.

Report security issues privately to the project maintainer or repository owner
with the following details:

- A short description of the issue
- The affected page, API endpoint, table, bucket, or configuration
- Steps to reproduce
- The expected impact
- Any screenshots, logs, request examples, or proof-of-concept details

Expected response:

- Critical issues, such as authentication bypass, admin access bypass, service
  role key exposure, or unauthorized data writes, should be reviewed as soon as
  possible.
- Non-critical issues will be reviewed when maintainers are available.
- If the report is accepted, a fix will be prepared and deployed before public
  disclosure when practical.
- If the report is declined, the maintainer will explain why it is not treated
  as a vulnerability.

## Security Scope

In scope:

- FastAPI backend authorization and authentication behavior
- Admin and server-admin API access control
- Supabase RLS, table grants, storage policies, and exposed RPC functions
- Frontend routes that expose private or operational data
- Environment variable and secret handling

Out of scope:

- Denial-of-service attacks without a clear application-level fix
- Social engineering
- Issues requiring physical access to a maintainer device
- Vulnerabilities in third-party services unless this project misconfigures them

## Operational Notes

- Browser clients must not receive Supabase service role keys.
- Direct database writes from `anon` or `authenticated` Supabase roles should
  remain blocked unless intentionally reintroduced with narrow RLS policies.
- Admin UI access is not a security boundary by itself; backend API checks are
  the authority.




