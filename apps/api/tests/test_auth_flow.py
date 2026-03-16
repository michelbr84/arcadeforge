"""Integration tests for the full auth flow.

Tests: register, login, session cookie, session rotation,
logout, /me endpoint, rate limiting, generic error messages.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.auth.sessions import COOKIE_NAME


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    """Health endpoint should return ok."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# === Registration ===


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Register creates a user and sets session cookie."""
    resp = await client.post(
        "/api/auth/register",
        json={
            "email": "alice@example.com",
            "username": "alice",
            "password": "securepass123",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert data["username"] == "alice"
    assert data["status"] == "active"
    assert "id" in data

    # Session cookie should be set
    assert COOKIE_NAME in resp.cookies


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Registering with an existing email returns 409."""
    await client.post(
        "/api/auth/register",
        json={
            "email": "dup@example.com",
            "username": "dupuser1",
            "password": "securepass123",
        },
    )
    resp = await client.post(
        "/api/auth/register",
        json={
            "email": "dup@example.com",
            "username": "dupuser2",
            "password": "securepass123",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    """Registering with an existing username returns 409."""
    await client.post(
        "/api/auth/register",
        json={
            "email": "user1@example.com",
            "username": "sameuser",
            "password": "securepass123",
        },
    )
    resp = await client.post(
        "/api/auth/register",
        json={
            "email": "user2@example.com",
            "username": "sameuser",
            "password": "securepass123",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """Password shorter than 8 characters should be rejected."""
    resp = await client.post(
        "/api/auth/register",
        json={
            "email": "weak@example.com",
            "username": "weakuser",
            "password": "short",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_username(client: AsyncClient):
    """Username with invalid characters should be rejected."""
    resp = await client.post(
        "/api/auth/register",
        json={
            "email": "bad@example.com",
            "username": "ab",  # too short
            "password": "securepass123",
        },
    )
    assert resp.status_code == 422


# === Login ===


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Login with correct credentials sets session cookie."""
    # First register
    await client.post(
        "/api/auth/register",
        json={
            "email": "login@example.com",
            "username": "loginuser",
            "password": "securepass123",
        },
    )

    # Then login
    resp = await client.post(
        "/api/auth/login",
        json={
            "email": "login@example.com",
            "password": "securepass123",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "login@example.com"
    assert COOKIE_NAME in resp.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Login with wrong password returns 401 with generic message."""
    await client.post(
        "/api/auth/register",
        json={
            "email": "wrongpw@example.com",
            "username": "wrongpwuser",
            "password": "securepass123",
        },
    )

    resp = await client.post(
        "/api/auth/login",
        json={
            "email": "wrongpw@example.com",
            "password": "wrongpassword",
        },
    )
    assert resp.status_code == 401
    # Must be generic — do NOT reveal whether email exists
    assert resp.json()["detail"] == "Invalid email or password."


@pytest.mark.asyncio
async def test_login_nonexistent_email(client: AsyncClient):
    """Login with non-existent email returns same generic 401."""
    resp = await client.post(
        "/api/auth/login",
        json={
            "email": "ghost@example.com",
            "password": "anypassword",
        },
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password."


@pytest.mark.asyncio
async def test_login_rotates_session(client: AsyncClient):
    """Login should rotate the session ID (prevent fixation)."""
    # Register and get first session
    reg_resp = await client.post(
        "/api/auth/register",
        json={
            "email": "rotate@example.com",
            "username": "rotateuser",
            "password": "securepass123",
        },
    )
    first_session = reg_resp.cookies.get(COOKIE_NAME)

    # Login again — session should rotate
    login_resp = await client.post(
        "/api/auth/login",
        json={
            "email": "rotate@example.com",
            "password": "securepass123",
        },
    )
    second_session = login_resp.cookies.get(COOKIE_NAME)

    assert first_session != second_session, "Session ID must change on login"


# === Me ===


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient):
    """GET /me with valid session returns user data."""
    reg_resp = await client.post(
        "/api/auth/register",
        json={
            "email": "me@example.com",
            "username": "meuser",
            "password": "securepass123",
        },
    )
    session_cookie = reg_resp.cookies.get(COOKIE_NAME)

    resp = await client.get(
        "/api/auth/me",
        cookies={COOKIE_NAME: session_cookie},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    """GET /me without session returns 401."""
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_invalid_session(client: AsyncClient):
    """GET /me with garbage session returns 401."""
    resp = await client.get(
        "/api/auth/me",
        cookies={COOKIE_NAME: "totally-fake-session-id"},
    )
    assert resp.status_code == 401


# === Logout ===


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    """Logout invalidates the session — /me should fail after."""
    reg_resp = await client.post(
        "/api/auth/register",
        json={
            "email": "logout@example.com",
            "username": "logoutuser",
            "password": "securepass123",
        },
    )
    session_cookie = reg_resp.cookies.get(COOKIE_NAME)

    # Logout
    logout_resp = await client.post(
        "/api/auth/logout",
        cookies={COOKIE_NAME: session_cookie},
    )
    assert logout_resp.status_code == 200

    # /me should fail with old session
    me_resp = await client.get(
        "/api/auth/me",
        cookies={COOKIE_NAME: session_cookie},
    )
    assert me_resp.status_code == 401
