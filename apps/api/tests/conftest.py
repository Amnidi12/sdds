"""
Test configuration.

Uses an in-memory SQLite database via aiosqlite for fast, isolated unit/API
tests. Note: PostgreSQL-specific features (UUID/JSONB columns, CHECK
constraints enforced at the DB level) are approximated by SQLAlchemy's
generic types here - this is a deliberate trade-off for fast CI feedback.
Before production releases, also run the test suite against real Postgres
(see docs/testing.md) to validate Postgres-specific behavior.
"""

import asyncio
import os
import uuid

os.environ.setdefault("APP_SECRET", "test-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ENV", "test")  # disables CSRF middleware in tests

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app

# Import every model module so Base.metadata is fully populated before create_all.
from app.users.models import User, RefreshSession, EmailVerificationToken, PasswordResetToken  # noqa
from app.organizations.models import Organization  # noqa
from app.donations.models import DonationCategory, Donation, DonationMedia, DonationStatusHistory  # noqa
from app.warehouses.models import Warehouse, InventoryBatch, InventoryMovement  # noqa
from app.beneficiaries.models import Beneficiary, BeneficiaryRequest  # noqa
from app.tasks.models import PickupTask, Distribution, DistributionItem, DeliveryProof  # noqa
from app.audit.models import AuditLog, Notification  # noqa

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)


async def _get_test_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _get_test_db


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    from app.core.rate_limit import reset_rate_limits

    reset_rate_limits()  # login rate limiting uses in-process state; isolate each test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
