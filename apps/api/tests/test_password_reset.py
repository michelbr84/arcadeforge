"""Tests for password reset flow."""

import pytest
from httpx import AsyncClient

from app.auth.sessions import COOKIE_NAME


async def _register(client: AsyncClient, email: str, username: str) -> str:
    resp = await client.post(
        "/api/auth/register",
        json={"email": email, "username": username, "password": "securepass123"},
    )
    return resp.cookies.get(COOKIE_NAME)


# === Request Reset ===


@pytest.mark.asyncio
async def test_forgot_password_generic_response(client: AsyncClient):
    """POST /forgot-password always returns same message (no enumeration)."""
    # With real email
    await _register(client, "reset@example.com", "resetuser")

    resp = await client.post(
        "/api/auth/forgot-password",
        json={"email": "reset@example.com"},
    )
    assert resp.status_code == 200
    msg1 = resp.json()["message"]

    # With non-existent email — same response
    resp = await client.post(
        "/api/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
    )
    assert resp.status_code == 200
    msg2 = resp.json()["message"]

    assert msg1 == msg2  # Generic, identical


# === Confirm Reset ===


@pytest.mark.asyncio
async def test_reset_password_full_flow(client: AsyncClient):
    """Full reset flow: request → get token → reset → login with new password."""
    from app.auth.reset_password import create_reset_token

    await _register(client, "fullreset@example.com", "fullreset")

    # Simulate getting a token (in prod this would be via email)
    from sqlalchemy import select
    from app.db.models import User

    # Get user_id via /me or directly
    # For testing, create token directly
    from app.auth.sessions import get_redis
    import redis.asyncio as aioredis

    # Create token for the user
    # We need the user_id — register sets cookie, /me gets it
    cookie = (await client.post(
        "/api/auth/login",
        json={"email": "fullreset@example.com", "password": "securepass123"},
    )).cookies.get(COOKIE_NAME)

    me_resp = await client.get("/api/auth/me", cookies={COOKIE_NAME: cookie})
    user_id = me_resp.json()["id"]

    token = await create_reset_token(user_id, "fullreset@example.com")

    # Reset password
    resp = await client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "newpassword456"},
    )
    assert resp.status_code == 200
    assert "reset" in resp.json()["message"].lower()

    # Old password should not work
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "fullreset@example.com", "password": "securepass123"},
    )
    assert login_resp.status_code == 401

    # New password should work
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "fullreset@example.com", "password": "newpassword456"},
    )
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_reset_invalid_token(client: AsyncClient):
    """Invalid token returns 400."""
    resp = await client.post(
        "/api/auth/reset-password",
        json={"token": "totally-fake-token", "new_password": "newpassword456"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_reset_token_single_use(client: AsyncClient):
    """Token can only be used once."""
    from app.auth.reset_password import create_reset_token

    await _register(client, "singleuse@example.com", "singleuse")

    cookie = (await client.post(
        "/api/auth/login",
        json={"email": "singleuse@example.com", "password": "securepass123"},
    )).cookies.get(COOKIE_NAME)
    me_resp = await client.get("/api/auth/me", cookies={COOKIE_NAME: cookie})
    user_id = me_resp.json()["id"]

    token = await create_reset_token(user_id, "singleuse@example.com")

    # First use — success
    resp1 = await client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "newpass11111"},
    )
    assert resp1.status_code == 200

    # Second use — fail
    resp2 = await client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "anotherpass22"},
    )
    assert resp2.status_code == 400


@pytest.mark.asyncio
async def test_reset_invalidates_sessions(client: AsyncClient):
    """After password reset, old sessions should be invalid."""
    from app.auth.reset_password import create_reset_token

    await _register(client, "sessions@example.com", "sessionuser")

    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "sessions@example.com", "password": "securepass123"},
    )
    cookie = login_resp.cookies.get(COOKIE_NAME)
    me_resp = await client.get("/api/auth/me", cookies={COOKIE_NAME: cookie})
    user_id = me_resp.json()["id"]

    token = await create_reset_token(user_id, "sessions@example.com")

    # Reset password
    await client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "brandnewpass99"},
    )

    # Old session should be invalid
    me_resp = await client.get("/api/auth/me", cookies={COOKIE_NAME: cookie})
    assert me_resp.status_code == 401


@pytest.mark.asyncio
async def test_reset_weak_password_rejected(client: AsyncClient):
    """Reset with password < 8 chars returns 422."""
    resp = await client.post(
        "/api/auth/reset-password",
        json={"token": "any-token", "new_password": "short"},
    )
    assert resp.status_code == 422
