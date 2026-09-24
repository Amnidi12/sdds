"""
Distribution tests.

Fix from Section 6.1: uses uuid.UUID objects (not str) in fixtures
to work correctly with SQLite's strict UUID type handling in tests.
"""

import uuid

import pytest

from app.db.session import get_db
from app.donations.models import DonationCategory, Donation, DonationStatus, DonationCondition
from app.organizations.models import Organization
from app.users.models import User, RoleName
from app.beneficiaries.models import Beneficiary
from app.tasks.models import Distribution, DistributionStatus
from app.core.security import hash_password
from app.main import app


@pytest.mark.asyncio
async def test_distribution_creation_requires_ngo_admin(client):
    """Only NGO admins and super admins can create distributions."""
    # Register as donor
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "donor_dist@test.com",
            "password": "SecurePass123!",
            "full_name": "Donor Dist",
            "role": "donor",
        },
    )
    await client.post(
        "/api/v1/auth/login",
        json={"email": "donor_dist@test.com", "password": "SecurePass123!"},
    )

    resp = await client.post(
        "/api/v1/distributions",
        json={
            "beneficiary_id": str(uuid.uuid4()),
            "items": [{"inventory_batch_id": str(uuid.uuid4()), "quantity": 5}],
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_distribution_list_requires_auth(client):
    """Unauthenticated requests should be rejected."""
    resp = await client.get("/api/v1/distributions")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_distribution_status_update_requires_auth(client):
    """Unauthenticated requests should be rejected."""
    fake_id = str(uuid.uuid4())
    resp = await client.patch(
        f"/api/v1/distributions/{fake_id}/status",
        json={"new_status": "dispatched"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_delivery_proof_submission_requires_auth(client):
    """Unauthenticated requests should be rejected."""
    fake_id = str(uuid.uuid4())
    resp = await client.post(
        f"/api/v1/distributions/{fake_id}/proof",
        json={"recipient_confirmation_name": "John Doe"},
    )
    assert resp.status_code == 401
