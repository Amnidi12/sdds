import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test.donor@example.com",
            "password": "SecurePass123!",
            "full_name": "Test Donor",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "test.donor@example.com"
    assert body["is_email_verified"] is False

    # Email not verified yet - login should still succeed per this app's design
    # (verification gates certain actions, not login itself, per common UX patterns)
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test.donor@example.com",
            "password": "SecurePass123!",
        },
    )
    assert resp.status_code == 200
    assert "access_token" in resp.cookies
    assert "refresh_token" in resp.cookies


@pytest.mark.asyncio
async def test_login_wrong_password_generic_error(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user1@example.com",
            "password": "SecurePass123!",
            "full_name": "User One",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "user1@example.com", "password": "WrongPassword!"}
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["message"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_unknown_email_same_generic_error(client):
    """Anti-enumeration: unknown email and wrong password must return an identical error."""
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "doesnotexist@example.com", "password": "whatever123"}
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["message"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_me_requires_authentication(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_current_user_after_login(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user2@example.com",
            "password": "SecurePass123!",
            "full_name": "User Two",
        },
    )
    await client.post("/api/v1/auth/login", json={"email": "user2@example.com", "password": "SecurePass123!"})
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == "user2@example.com"


@pytest.mark.asyncio
async def test_logout_clears_session(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user3@example.com",
            "password": "SecurePass123!",
            "full_name": "User Three",
        },
    )
    await client.post("/api/v1/auth/login", json={"email": "user3@example.com", "password": "SecurePass123!"})
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 200

    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_password_too_short_rejected(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "shortpw@example.com",
            "password": "short",
            "full_name": "Short PW",
        },
    )
    assert resp.status_code == 422
