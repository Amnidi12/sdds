# Security

This document describes the security controls actually implemented in this codebase, and is honest about what's not covered. **This system has not undergone a professional security audit or penetration test. Do not treat anything in this document as a guarantee.**

## Implemented controls

| Control | Implementation | Location |
|---|---|---|
| Password hashing | Argon2id via `argon2-cffi` | `app/core/security.py` |
| Session tokens | Short-lived JWT access token (15 min) + rotating opaque refresh token, hash-only storage | `app/core/security.py`, `app/auth/routes.py` |
| Cookie flags | `HttpOnly`, `SameSite=Lax`, `Secure` (prod) | `app/auth/routes.py::_set_auth_cookies` |
| RBAC | Backend dependency injection (`require_roles`), never frontend-only | `app/core/deps.py` |
| Org-tenant isolation | Every NGO-scoped query filters by `organization_id`; cross-org access returns 403 | `app/donations/service.py::assert_can_view_donation` and equivalents |
| Anti-enumeration | Identical error message for "wrong password" and "email doesn't exist" | `app/auth/routes.py::GENERIC_AUTH_ERROR` |
| Login rate limiting | Fixed-window limiter, Redis-backed with in-process fallback | `app/core/rate_limit.py` |
| SQL injection | 100% parameterized queries via SQLAlchemy ORM — no raw string SQL anywhere | throughout |
| Security headers | CSP, X-Frame-Options, X-Content-Type-Options, HSTS, Referrer-Policy | `app/core/middleware.py::SecurityHeadersMiddleware` |
| CORS | Explicit origin allowlist (`CORS_ORIGINS` env var), not wildcard | `app/main.py` |
| Error handling | Generic messages to clients; full detail logged server-side only | `app/core/errors.py` |
| Audit trail | Append-only `audit_logs` table for every state-changing action | `app/audit/models.py` |
| Non-root containers | Both Dockerfiles create and switch to an unprivileged user | `apps/api/Dockerfile`, `apps/web/Dockerfile` |
| Secrets | Never committed; `.env.example` has placeholders only, real `.env` is gitignored | `.gitignore`, `.env.example` |
| Public tracking privacy | `/donations/track/{id}` returns exactly 4 fields, no PII, no DB ID | `app/donations/schemas.py::PublicTrackingOut` |
| Inventory race conditions | `SELECT ... FOR UPDATE` row locking on every stock mutation | `app/warehouses/service.py` |
| Invalid state transitions | Explicit transition maps checked server-side, return 409 | `app/donations/models.py`, `app/tasks/models.py` |

## Not yet implemented (be aware before any real deployment)

- **CSRF protection**: cookie-based auth with `SameSite=Lax` mitigates most CSRF vectors for state-changing GET-adjacent requests, but a dedicated CSRF token for POST/PATCH/DELETE has not been added. Add `fastapi-csrf-protect` or equivalent before production use with cookie auth from a browser.
- **File upload validation**: the upload endpoints referenced in the architecture (donation photos, delivery proof photos) are modeled in the database but the actual upload routes with MIME/extension/size validation are not yet implemented.
- **Dependency scanning**: no `pip-audit`/`npm audit`/Dependabot configuration is included yet. Add before production.
- **Account lockout enforcement**: the `failed_login_attempts` / `locked_until` columns exist on `User` but the login route does not yet increment/check them — currently only the IP-based rate limiter provides brute-force protection.
- **Google OAuth**: config placeholders exist (`GOOGLE_CLIENT_ID`/`SECRET`) but the OAuth flow itself is not implemented.
- **Sentry/error monitoring**: `SENTRY_DSN` is read from config but not wired to the FastAPI app.

## Security checklist for production deployment

- [ ] Set `APP_SECRET` to a cryptographically random 64+ character string (`openssl rand -hex 32`)
- [ ] Set `COOKIE_SECURE=true` and serve everything over HTTPS
- [ ] Set `ENV=production` (disables `/docs` and `/redoc`)
- [ ] Restrict `CORS_ORIGINS` to your actual frontend domain(s) only
- [ ] Change/remove all seeded demo accounts
- [ ] Add CSRF protection before enabling cookie-based auth in a public deployment
- [ ] Implement and test file upload validation before enabling upload endpoints
- [ ] Run `pip-audit` / `npm audit` and address findings
- [ ] Enable database backups (see `docs/deployment.md`)
- [ ] Restrict database and Redis network access to the API service only (no public exposure)
- [ ] Rotate `APP_SECRET` on a schedule; understand this invalidates all active sessions
- [ ] Set up log aggregation and alerting on repeated 401/403/429 responses (possible attack indicator)

## Production readiness checklist (broader than security)

- [ ] Load-test the inventory reservation path (`FOR UPDATE` locking under concurrency)
- [ ] Confirm `alembic upgrade head` runs cleanly against your actual Postgres version
- [ ] Configure a real SMTP provider (SendGrid, SES, etc.) — the dev console backend must not be used in production
- [ ] Configure real S3-compatible storage — local disk storage does not survive container restarts on most PaaS platforms
- [ ] Add a background job queue if email/report volume grows beyond what synchronous sending can handle
- [ ] Add Playwright e2e coverage for the full donor→NGO→volunteer→beneficiary lifecycle before calling this "production-ready" in the fullest sense
