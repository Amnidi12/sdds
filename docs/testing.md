# Testing

## Backend

Real, passing test suite using pytest + httpx's `ASGITransport` (no running server needed) against an in-memory SQLite database for speed.

```bash
cd apps/api
pip install -r requirements.txt aiosqlite
APP_SECRET=test-secret DATABASE_URL=sqlite+aiosqlite:///:memory: pytest tests/ -v
```

Current coverage (`tests/test_auth.py`, `tests/test_donations.py`):
- Registration, login, generic anti-enumeration error messages
- Cookie-based session auth (`/auth/me` requires a valid cookie)
- Logout clears the session
- Password length validation (422 on short passwords)
- A donor can create and view their own donation
- A donor **cannot** view another donor's donation (RBAC boundary, 403)
- A donor **cannot** change donation status (RBAC boundary, 403)
- Invalid state transitions are rejected (409) — e.g. `pending_review` → `delivered` directly
- Valid state transitions succeed and are recorded in `donation_status_history`
- The public tracking endpoint returns exactly the 4 allowed fields and never PII

### Why SQLite for CI, and what that trade-off means

SQLite is fast and needs no external service, which keeps CI feedback quick. But it doesn't enforce everything Postgres does — notably `CHECK` constraints on `inventory_batches` and true `JSONB` behavior are approximated. **Before a production release, also run the suite against real Postgres**:

```bash
docker compose up -d postgres
APP_SECRET=test-secret \
DATABASE_URL=postgresql+asyncpg://sddt:sddt_dev_password@localhost:5432/sddt_test \
pytest tests/ -v
```

### Writing new tests

Follow the existing pattern in `tests/test_donations.py`: register/login helper → seed any required fixture data directly via the overridden DB session → call the API → assert both the HTTP status *and* the response shape. For RBAC tests specifically, always assert the **403/409**, not just the happy path — an authorization test that only checks the allowed case doesn't prove the boundary exists.

## Frontend

Not yet implemented in this build. Recommended setup when added:

```bash
cd apps/web
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom jsdom
```

Priority test targets: the login/register form validation, the API client's error handling (`ApiError` parsing), and the donation status label mapping.

## End-to-end (Playwright)

Not yet implemented. When added, prioritize the single most valuable path first: register → login → create donation → (as NGO admin) approve → verify the donor sees the updated status. That one flow exercises auth, RBAC, and the state machine together and would catch most regressions.

## Manual smoke test checklist

Useful when you don't have time to run the full suite:

1. `docker compose up --build` starts all 4 services without errors
2. `curl http://localhost:8000/health/live` returns `{"status": "ok"}`
3. `curl http://localhost:8000/health/ready` returns `{"status": "ready", "database": "connected"}` (fails clearly if Postgres isn't reachable)
4. Register a donor via the frontend, verify the email is printed to the API's console log (dev email backend)
5. Log in, create a donation, confirm it appears in "My Donations" with status "Pending Review"
6. `curl http://localhost:8000/api/v1/donations/track/<tracking_id>` returns only the 4 public fields
