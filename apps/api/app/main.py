"""
Application entry point.

All router imports are grouped at the top (Section 6.4 code quality fix).
All routers are registered — including reports, notifications, uploads,
admin, and organizations routers that were previously missing.
"""

import logging

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.admin.routes import router as admin_router
from app.auth.routes import router as auth_router
from app.beneficiaries.routes import router as beneficiaries_router
from app.core.config import get_settings
from app.core.errors import http_exception_handler, unhandled_exception_handler, validation_exception_handler
from app.core.middleware import CSRFMiddleware, RequestIDMiddleware, SecurityHeadersMiddleware
from app.distributions.routes import router as distributions_router
from app.donations.categories_routes import router as donation_categories_router
from app.donations.routes import router as donations_router
from app.notifications.routes import router as notifications_router
from app.organizations.routes import router as organizations_router
from app.reports.routes import router as reports_router
from app.tasks.routes import router as pickups_router
from app.uploads.routes import router as uploads_router
from app.warehouses.routes import inventory_router, router as warehouses_router

logging.basicConfig(level=logging.INFO)
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Transparent donation lifecycle tracking platform for NGOs, donors, volunteers and beneficiaries.",
    docs_url="/docs" if settings.ENV != "production" else None,  # hide interactive docs in prod by default
    redoc_url="/redoc" if settings.ENV != "production" else None,
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,  # required for HttpOnly cookie auth
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# ---- Routers ----
app.include_router(auth_router)
app.include_router(donations_router)
app.include_router(donation_categories_router)
app.include_router(warehouses_router)
app.include_router(inventory_router)
app.include_router(pickups_router)
app.include_router(beneficiaries_router)
app.include_router(distributions_router)
app.include_router(notifications_router)
app.include_router(uploads_router)
app.include_router(reports_router)
app.include_router(admin_router)
app.include_router(organizations_router)


@app.get("/health/live", tags=["health"])
async def health_live():
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
async def health_ready():
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception:
        return {"status": "not_ready", "database": "unavailable"}

@app.get("/api/v1/public/stats", tags=["public"])
async def public_stats():
    from app.db.session import AsyncSessionLocal
    from sqlalchemy import select, func
    from app.donations.models import Donation
    from app.users.models import User, RoleName
    from app.beneficiaries.models import Beneficiary

    try:
        async with AsyncSessionLocal() as session:
            weight_res = await session.execute(select(func.sum(Donation.estimated_weight_kg)))
            total_weight = weight_res.scalar() or 0

            active_ngos = (await session.execute(select(func.count()).select_from(User).where(User.role == RoleName.NGO_ADMIN))).scalar_one()
            beneficiaries = (await session.execute(select(func.count()).select_from(Beneficiary))).scalar_one()
            fleets = (await session.execute(select(func.count()).select_from(User).where(User.role == RoleName.VOLUNTEER))).scalar_one()
            
            return {
                "processed_kg": float(total_weight),
                "active_ngos": active_ngos,
                "beneficiaries": beneficiaries,
                "active_fleets": fleets,
            }
    except Exception as e:
        logging.warning("public_stats query failed: %s", e)
        return {
            "processed_kg": 0,
            "active_ngos": 0,
            "beneficiaries": 0,
            "active_fleets": 0,
        }
