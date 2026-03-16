"""Tests for user profile and account update endpoints."""

import pytest
from httpx import AsyncClient

from app.auth.sessions import COOKIE_NAME


async def _register(client: AsyncClient, email: str, username: str, password: str = "securepass123"):
    """Helper: register a user and return the session cookie."""
    resp = await client.post(
        "/api/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert resp.status_code == 201
    return resp.cookies.get(COOKIE_NAME)


# === GET /api/users/:username ===


@pytest.mark.asyncio
async def test_get_user_profile(client: AsyncClient):
    """Public profile endpoint returns user data."""
    await _register(client, "profile@example.com", "profileuser")

    resp = await client.get("/api/users/profileuser")
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "profileuser"
    assert data["email"] == "profile@example.com"


@pytest.mark.asyncio
async def test_get_user_profile_not_found(client: AsyncClient):
    """Non-existent username returns 404."""
    resp = await client.get("/api/users/ghostuser")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_user_profile_case_insensitive(client: AsyncClient):
    """Username lookup should be case-insensitive."""
    await _register(client, "case@example.com", "caseuser")

    resp = await client.get("/api/users/CaseUser")
    assert resp.status_code == 200
    assert resp.json()["username"] == "caseuser"


# === PATCH /api/auth/me ===


@pytest.mark.asyncio
async def test_update_username(client: AsyncClient):
    """Authenticated user can change their username."""
    cookie = await _register(client, "update@example.com", "oldname")

    resp = await client.patch(
        "/api/auth/me",
        json={"username": "newname"},
        cookies={COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "newname"

    # Verify via /me
    me_resp = await client.get("/api/auth/me", cookies={COOKIE_NAME: cookie})
    assert me_resp.json()["username"] == "newname"


@pytest.mark.asyncio
async def test_update_username_taken(client: AsyncClient):
    """Changing to an already-taken username returns 409."""
    await _register(client, "taken1@example.com", "taken")
    cookie = await _register(client, "taken2@example.com", "nottaken")

    resp = await client.patch(
        "/api/auth/me",
        json={"username": "taken"},
        cookies={COOKIE_NAME: cookie},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_update_password(client: AsyncClient):
    """Authenticated user can change their password."""
    cookie = await _register(client, "pwchange@example.com", "pwuser")

    resp = await client.patch(
        "/api/auth/me",
        json={"current_password": "securepass123", "new_password": "newpass456789"},
        cookies={COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200

    # Old password should no longer work
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "pwchange@example.com", "password": "securepass123"},
    )
    assert login_resp.status_code == 401

    # New password should work
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "pwchange@example.com", "password": "newpass456789"},
    )
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_update_password_wrong_current(client: AsyncClient):
    """Changing password with wrong current password returns 400."""
    cookie = await _register(client, "wrongpw@example.com", "wrongpwuser")

    resp = await client.patch(
        "/api/auth/me",
        json={"current_password": "wrongpassword", "new_password": "newpass456789"},
        cookies={COOKIE_NAME: cookie},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_password_missing_current(client: AsyncClient):
    """Changing password without current_password returns 400."""
    cookie = await _register(client, "nocurrent@example.com", "nocurrentuser")

    resp = await client.patch(
        "/api/auth/me",
        json={"new_password": "newpass456789"},
        cookies={COOKIE_NAME: cookie},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_me_unauthenticated(client: AsyncClient):
    """PATCH /me without session returns 401."""
    resp = await client.patch(
        "/api/auth/me",
        json={"username": "hacker"},
    )
    assert resp.status_code == 401
