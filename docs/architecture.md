# Architecture

## System overview

```mermaid
flowchart LR
    subgraph Client
        Web[Next.js Web App]
    end
    subgraph Backend
        API[FastAPI]
        Worker[Background tasks<br/>email, future job queue]
    end
    subgraph Data
        PG[(PostgreSQL)]
        Redis[(Redis<br/>rate limiting / cache)]
        S3[(S3-compatible<br/>object storage)]
    end

    Web -- HTTPS + HttpOnly cookies --> API
    API -- async SQLAlchemy --> PG
    API -- rate limit / cache --> Redis
    API -- signed URLs --> S3
    API -.-> Worker
```

## Donation lifecycle

```mermaid
stateDiagram-v2
    [*] --> pending_review
    pending_review --> approved
    pending_review --> rejected
    pending_review --> cancelled
    approved --> pickup_scheduled
    approved --> cancelled
    pickup_scheduled --> picked_up
    pickup_scheduled --> cancelled
    picked_up --> received_at_warehouse
    received_at_warehouse --> verified
    verified --> available
    available --> allocated
    allocated --> out_for_distribution
    allocated --> available: released back
    out_for_distribution --> delivered
    delivered --> completed
    completed --> [*]
    rejected --> [*]
    cancelled --> [*]
```

This state machine is enforced in code (`app/donations/models.py::ALLOWED_DONATION_TRANSITIONS`), not just documented — any request for an invalid transition returns `409 Conflict`.

## Distribution / inventory flow

```mermaid
sequenceDiagram
    participant NGO as NGO Admin
    participant API
    participant DB as PostgreSQL

    NGO->>API: POST /distributions {beneficiary_id, items}
    API->>DB: SELECT batch FOR UPDATE (row lock)
    API->>DB: check quantity_available >= requested
    API->>DB: quantity_available -= qty, quantity_reserved += qty
    API->>DB: INSERT inventory_movement (RESERVE)
    API-->>NGO: 201 Created (status=reserved)

    NGO->>API: PATCH /distributions/{id}/status {dispatched}
    API->>DB: quantity_reserved -= qty
    API->>DB: INSERT inventory_movement (OUT)
    API->>DB: advance linked donation(s) -> out_for_distribution

    NGO->>API: PATCH /distributions/{id}/status {delivered}
    API->>DB: advance linked donation(s) -> delivered

    NGO->>API: PATCH /distributions/{id}/status {completed}
    API->>DB: advance linked donation(s) -> completed
    Note over DB: Donor now sees "completed" on their original donation
```

Row-level locking (`SELECT ... FOR UPDATE`) around every quantity mutation is what prevents two concurrent distributions from double-allocating the same stock (requirement: "prevent negative inventory").

## Authentication flow

```mermaid
sequenceDiagram
    participant Browser
    participant API
    participant DB

    Browser->>API: POST /auth/login {email, password}
    API->>DB: SELECT user WHERE email=?
    API->>API: argon2.verify(password, hash)
    API->>DB: INSERT refresh_session (hash of new opaque token)
    API-->>Browser: Set-Cookie access_token (15min), refresh_token (30d, HttpOnly)

    Browser->>API: GET /donations (cookie sent automatically)
    API->>API: decode JWT, load user
    API-->>Browser: 200 OK

    Note over Browser,API: 15 minutes later, access token expired
    Browser->>API: POST /auth/refresh (refresh_token cookie)
    API->>DB: look up refresh_session by hash, check not revoked/expired
    API->>DB: revoke old session, insert new one (rotation)
    API-->>Browser: new access_token + refresh_token cookies
```

## Deployment architecture (production target)

```mermaid
flowchart TB
    User[Browser] --> Vercel[Next.js on Vercel]
    Vercel -- HTTPS --> Render[FastAPI on Render/Railway<br/>Docker container]
    Render --> ManagedPG[(Managed PostgreSQL)]
    Render --> ManagedRedis[(Managed Redis)]
    Render --> S3[(S3-compatible storage<br/>e.g. Cloudflare R2 / AWS S3)]
```

## Why these technology choices

- **FastAPI over Django/Flask**: native async support matters for an I/O-bound app (many DB round-trips per request in the distribution flow), and Pydantic-based request/response validation removes an entire class of input-handling bugs for free.
- **SQLAlchemy 2.x async + explicit service layer**: keeps route handlers thin (HTTP concerns only) and business logic (state machines, stock locking) testable in isolation from FastAPI.
- **JWT access + opaque refresh, not JWT-only**: a pure-JWT refresh scheme can't be revoked before expiry. Storing only the *hash* of an opaque refresh token lets the server revoke individual sessions (logout, logout-all-devices, password-reset-triggered revocation) without needing a JWT blocklist.
- **Next.js App Router**: server components reduce client bundle size for content-heavy pages (landing, tracking); client components are used precisely where interactivity is needed (forms, dashboards).
- **Alembic over "just let SQLAlchemy create_all in prod"**: production schema changes must be reviewable, reversible, and applied without downtime-causing full resyncs.

## Known architectural gaps (see also docs/troubleshooting.md)

- Background job queue (Celery/RQ) is referenced in the requirements but not implemented — emails currently send synchronously (fine at demo scale, not at production volume).
- S3 storage abstraction is designed in config (`S3_*` env vars) but the actual upload endpoints (`/uploads`) are not yet implemented — donation photos and delivery-proof photos are modeled in the DB (`donation_media`, `delivery_proofs.photo_storage_key`) but not yet wired to a working upload route.
- NGO/Volunteer/Admin dashboard UIs are not yet built (API endpoints they'd call already exist and are tested).
