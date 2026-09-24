# Smart Donation Distribution Tracker

A transparent donation lifecycle platform connecting donors, NGOs, volunteers and beneficiaries — built as a real full-stack application, not a static prototype.

> **Status**: Core backend (auth, RBAC, donations, pickups, warehouse/inventory, beneficiaries, distributions) is implemented, tested, and verified to import/run/pass tests. Frontend covers the donor journey (landing, register, login, donation list/create) end-to-end against the real API. NGO/Volunteer/Admin dashboards, notifications delivery, reports/CSV export, and e2e (Playwright) tests are scaffolded in the architecture but not yet built — see `docs/troubleshooting.md` → "Known gaps" for the honest list.

## What this is

Donors register donations → NGOs review/approve → volunteers pick them up → warehouse staff verify and stock them → NGOs match inventory to beneficiary need → volunteers deliver → donors see their donation marked complete. Every status change is recorded in an audit trail; every donation gets a public, PII-free tracking ID.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI + SQLAlchemy 2 (async) + PostgreSQL | Async I/O suits a request-heavy CRUD+workflow app; SQLAlchemy 2's typed ORM catches mistakes at write-time |
| Auth | Argon2id + JWT access token + rotating refresh token in HttpOnly cookies | OWASP-recommended hashing; rotation limits the blast radius of a stolen refresh token |
| Frontend | Next.js 15 (App Router) + TypeScript + Tailwind | Server/client component split fits a dashboard-heavy app; Tailwind keeps styling co-located |
| Migrations | Alembic | Standard, transactional, reversible schema changes |
| Infra | Docker Compose (Postgres, Redis, API, Web) | One command to run the whole stack locally |

Full reasoning in `docs/architecture.md`.

## Quick start (Docker)

```bash
git clone <your-fork-url>
cd smart-donation-distribution-tracker
cp apps/api/.env.example apps/api/.env
# Edit apps/api/.env - at minimum set APP_SECRET to a long random string
docker compose up --build
```

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API docs (Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/health/ready

Then, in a separate terminal, run migrations and seed demo data:

```bash
docker compose exec api alembic upgrade head
docker compose exec api python -m scripts.seed
```

Demo accounts (password for all: `DemoPass123!`):

| Role | Email |
|---|---|
| Super Admin | admin@sddt.demo |
| NGO Admin | ngo.admin@hopefoundation.demo |
| Donor | donor@sddt.demo |
| Volunteer | volunteer@sddt.demo |
| Beneficiary | beneficiary@sddt.demo |

**Change or remove these before any real deployment.**

## Quick start (manual, no Docker)

See `docs/troubleshooting.md` and the "Manual setup" section below for full detail. Summary:

```bash
# Backend
cd apps/api
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# start local Postgres + Redis yourself, then:
cp .env.example .env  # edit DATABASE_URL etc.
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload

# Frontend (new terminal)
cd apps/web
npm install
cp .env.example .env.local
npm run dev
```

## Running tests

```bash
cd apps/api
pip install -r requirements.txt aiosqlite
APP_SECRET=test-secret DATABASE_URL=sqlite+aiosqlite:///:memory: pytest tests/ -v
```

This backend test suite is real and passing (13/13 as of this build) — it covers registration/login, anti-enumeration error messages, session cookie behavior, RBAC boundaries (a donor cannot view another donor's donation or change donation status), the donation state-machine (invalid transitions are rejected with 409), and the public tracking endpoint's PII exclusion. Tests run against SQLite for fast CI feedback; re-run against real Postgres before a production release (see `docs/testing.md`) since a few Postgres-specific behaviors (CHECK constraints, JSONB) aren't exercised by SQLite.

## Repository structure

```
apps/
  api/            FastAPI backend (domain-organized: auth, donations, warehouses, tasks, beneficiaries, distributions, audit...)
  web/             Next.js frontend
docs/              Architecture, database, API, security, deployment, testing, troubleshooting
.github/workflows/ CI (lint, type check, test, build validation)
docker-compose.yml
```

## Documentation

- `docs/architecture.md` — system design + diagrams
- `docs/database.md` — schema + ER diagram
- `docs/api.md` — endpoint reference
- `docs/security.md` — security controls + checklist + known limitations
- `docs/deployment.md` — Vercel/Render/Railway deployment steps
- `docs/testing.md` — how to run and extend the test suite
- `docs/troubleshooting.md` — common issues + honest list of what's not yet built

## License

MIT — see `LICENSE`.
