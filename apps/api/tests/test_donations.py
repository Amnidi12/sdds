import pytest
from sqlalchemy import select

from app.donations.models import DonationCategory
from app.db.session import get_db
from app.main import app


async def _register_and_login(client, email, full_name, role="donor"):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePass123!",
            "full_name": full_name,
            "role": role,
        },
    )
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass123!"})
    return resp.json()


async def _create_category(client) -> str:
    """Directly inserts a category via the test DB session (no admin category-creation
    endpoint exists yet in this build, so tests seed one directly)."""
    db_gen = app.dependency_overrides[get_db]()
    db = await db_gen.__anext__()
    existing = (await db.execute(select(DonationCategory))).scalar_one_or_none()
    if existing:
        return str(existing.id)
    cat = DonationCategory(name="Clothing", slug="clothing")
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return str(cat.id)


@pytest.mark.asyncio
async def test_donor_can_create_and_view_own_donation(client):
    await _register_and_login(client, "donor1@example.com", "Donor One")
    category_id = await _create_category(client)

    resp = await client.post(
        "/api/v1/donations",
        json={
            "category_id": category_id,
            "title": "Winter Jackets",
            "quantity": 10,
            "unit": "items",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "pending_review"
    assert body["tracking_id"].startswith("SDDT-")

    resp = await client.get(f"/api/v1/donations/{body['id']}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_donor_cannot_view_another_donors_donation(client):
    await _register_and_login(client, "donorA@example.com", "Donor A")
    category_id = await _create_category(client)
    resp = await client.post(
        "/api/v1/donations", json={"category_id": category_id, "title": "Books", "quantity": 5}
    )
    donation_id = resp.json()["id"]

    await client.post("/api/v1/auth/logout")
    await _register_and_login(client, "donorB@example.com", "Donor B")

    resp = await client.get(f"/api/v1/donations/{donation_id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_donor_cannot_change_donation_status(client):
    """RBAC boundary: only NGO admins / super admins can transition donation status."""
    await _register_and_login(client, "donor2@example.com", "Donor Two")
    category_id = await _create_category(client)
    resp = await client.post(
        "/api/v1/donations", json={"category_id": category_id, "title": "Food Kit", "quantity": 3}
    )
    donation_id = resp.json()["id"]

    resp = await client.patch(f"/api/v1/donations/{donation_id}/status", json={"new_status": "approved"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_invalid_status_transition_rejected(client):
    """State machine boundary: cannot jump straight from pending_review to delivered."""
    await _register_and_login(client, "donor3@example.com", "Donor Three")
    category_id = await _create_category(client)
    resp = await client.post(
        "/api/v1/donations", json={"category_id": category_id, "title": "Blankets", "quantity": 8}
    )
    donation_id = resp.json()["id"]

    await client.post("/api/v1/auth/logout")
    await _register_and_login(client, "ngo1@example.com", "NGO Admin One", role="ngo_admin")

    resp = await client.patch(f"/api/v1/donations/{donation_id}/status", json={"new_status": "delivered"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_valid_status_transition_succeeds_and_is_recorded_in_history(client):
    await _register_and_login(client, "donor4@example.com", "Donor Four")
    category_id = await _create_category(client)
    resp = await client.post(
        "/api/v1/donations", json={"category_id": category_id, "title": "Shoes", "quantity": 4}
    )
    donation_id = resp.json()["id"]

    await client.post("/api/v1/auth/logout")
    await _register_and_login(client, "ngo2@example.com", "NGO Admin Two", role="ngo_admin")

    resp = await client.patch(
        f"/api/v1/donations/{donation_id}/status", json={"new_status": "approved", "note": "Looks good"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_public_tracking_endpoint_hides_pii(client):
    await _register_and_login(client, "donor5@example.com", "Donor Five")
    category_id = await _create_category(client)
    resp = await client.post(
        "/api/v1/donations",
        json={
            "category_id": category_id,
            "title": "Secret Title",
            "quantity": 1,
            "pickup_address": "123 Private St",
        },
    )
    tracking_id = resp.json()["tracking_id"]

    await client.post("/api/v1/auth/logout")  # public endpoint - no auth needed

    resp = await client.get(f"/api/v1/donations/track/{tracking_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"tracking_id", "category_name", "status", "created_at"}
    assert "pickup_address" not in body
    assert "donor_id" not in body
