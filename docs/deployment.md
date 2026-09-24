# Deployment

This describes deploying the frontend to Vercel and the backend to a Docker-compatible platform (Render or Railway used as examples), with managed Postgres/Redis and S3-compatible storage.

## 1. Database — Managed PostgreSQL

Any managed Postgres works (Render Postgres, Railway Postgres, Supabase, Neon, AWS RDS). Steps are the same in principle:

1. Create a Postgres 16 instance
2. Note the connection string, convert it to the `asyncpg` form:
   `postgresql+asyncpg://user:pass@host:5432/dbname`
3. Once the backend is deployed (step 3), run migrations against it:
   ```bash
   DATABASE_URL=<managed-db-url> alembic upgrade head
   DATABASE_URL=<managed-db-url> python -m scripts.seed   # optional, demo data only
   ```

## 2. Redis — Managed Redis (optional but recommended)

Render Redis, Railway Redis, or Upstash all work. The app degrades gracefully without Redis (rate limiting falls back to in-process, which is weaker but functional) — treat this as recommended, not blocking.

## 3. Backend — Render / Railway (Docker)

Both platforms build directly from the `apps/api/Dockerfile`.

**Render:**
1. New → Web Service → connect your repo
2. Root directory: `apps/api`
3. Environment: Docker
4. Set all environment variables from `.env.example` (especially `APP_SECRET`, `DATABASE_URL`, `FRONTEND_URL`, `CORS_ORIGINS`, `COOKIE_SECURE=true`, `ENV=production`)
5. Health check path: `/health/ready`

**Railway:** same idea — new project from repo, set root directory to `apps/api`, Railway auto-detects the Dockerfile, set the same env vars.

After first deploy, run migrations via the platform's shell/console:
```bash
alembic upgrade head
```

## 4. Storage — S3-compatible

Cloudflare R2, AWS S3, or Backblaze B2 all work. Set `S3_ENDPOINT`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_REGION`. If these are unset, the app falls back to local disk storage (`LOCAL_UPLOAD_DIR`) — **do not rely on local disk storage in production**, as most PaaS platforms use ephemeral filesystems that wipe uploads on every redeploy.

> Note: as documented in `docs/architecture.md`, the actual upload *routes* aren't implemented yet in this build — this section describes the intended configuration once they are.

## 5. Frontend — Vercel

1. Import the repo into Vercel
2. Root directory: `apps/web`
3. Framework preset: Next.js (auto-detected)
4. Environment variable: `NEXT_PUBLIC_API_URL=https://your-backend-url.onrender.com`
5. Deploy

## 6. Wire CORS and cookies together

After both are deployed:
- Backend `CORS_ORIGINS` must include the exact Vercel URL (e.g. `["https://your-app.vercel.app"]`)
- Backend `FRONTEND_URL` should match, for email verification/reset links
- Backend `COOKIE_DOMAIN` — leave unset unless frontend and backend share a parent domain (e.g. both under `.yourdomain.com`); cross-domain cookies between `vercel.app` and `onrender.com` require `SameSite=None; Secure` instead of the current `SameSite=Lax` default. If you deploy frontend and backend on different base domains, either put both behind one domain via a reverse proxy, or change `samesite="lax"` to `samesite="none"` in `app/auth/routes.py` (requires `COOKIE_SECURE=true`, i.e. HTTPS everywhere, which you should have anyway).

## 7. HTTPS

Vercel and Render/Railway both provision HTTPS automatically for their subdomains and any custom domain you attach. No manual certificate management needed at this scale.

## 8. Health checks

- Liveness: `GET /health/live` → `{"status": "ok"}` (process is running)
- Readiness: `GET /health/ready` → `{"status": "ready", "database": "connected"}` (can reach the DB)

Configure your platform's health check to poll `/health/ready`.

## Backups

- **Postgres**: enable your managed provider's automated daily backups (Render/Railway/Supabase all offer this in their dashboard — enable it, this repo cannot configure it for you). Test a restore at least once before you need it for real.
- **Object storage**: enable versioning on your S3 bucket/R2 bucket if the provider supports it.
- **Retention**: 30 days of daily backups is a reasonable default for an NGO-scale deployment; adjust based on your compliance requirements.

This document describes how to configure backups — it does not mean backups exist unless you've actually enabled them on your provider.
