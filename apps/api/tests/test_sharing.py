"""Tests for sharing features: fork, public visibility."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.sessions import COOKIE_NAME
from app.db.models import Game, GameVersion


async def _register(client: AsyncClient, email: str, username: str) -> str:
    resp = await client.post(
        "/api/auth/register",
        json={"email": email, "username": username, "password": "securepass123"},
    )
    return resp.cookies.get(COOKIE_NAME)


async def _create_public_game(
    client: AsyncClient, cookie: str, db_session: AsyncSession, title: str = "Forkable Game"
) -> str:
    """Create a public, ready game with v0 containing a known marker string.

    Idempotently forces status/visibility and upserts v0 so the helper is resilient
    to inline-gen flakiness.
    """
    resp = await client.post(
        "/api/games",
        json={"genre": "shooter", "title": title, "prompt": f"A public shooter game called {title}"},
        cookies={COOKIE_NAME: cookie},
    )
    game_id = resp.json()["game_id"]
    uid = uuid.UUID(game_id)
    marker_source = "import pygame\npygame.init()\n# original code"

    await db_session.execute(
        update(Game).where(Game.id == uid).values(status="ready", visibility="public")
    )
    result = await db_session.execute(
        update(GameVersion)
        .where(GameVersion.game_id == uid, GameVersion.version == 0)
        .values(source_code=marker_source, blueprint_json={"genre": "shooter"})
    )
    if result.rowcount == 0:
        db_session.add(GameVersion(
            game_id=uid,
            version=0,
            source_code=marker_source,
            blueprint_json={"genre": "shooter"},
        ))
    await db_session.commit()
    await db_session.close()
    return game_id


# === Fork ===


@pytest.mark.asyncio
async def test_fork_public_game(client: AsyncClient, db_session: AsyncSession):
    """Fork creates a new game owned by the forking user."""
    owner_cookie = await _register(client, "owner@example.com", "forkowner")
    game_id = await _create_public_game(client, owner_cookie, db_session)

    forker_cookie = await _register(client, "forker@example.com", "forker")

    resp = await client.post(
        f"/api/games/{game_id}/fork",
        cookies={COOKIE_NAME: forker_cookie},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "fork" in data["title"].lower()
    assert data["genre"] == "shooter"
    assert data["status"] == "ready"


@pytest.mark.asyncio
async def test_fork_private_game_fails(client: AsyncClient, db_session: AsyncSession):
    """Cannot fork a private game."""
    owner_cookie = await _register(client, "privowner@example.com", "privforkowner")
    resp = await client.post(
        "/api/games",
        json={"genre": "puzzle", "title": "Private", "prompt": "A private puzzle game that cannot be forked"},
        cookies={COOKIE_NAME: owner_cookie},
    )
    game_id = resp.json()["game_id"]

    # Force ready + private regardless of inline-gen outcome
    await db_session.execute(
        update(Game).where(Game.id == uuid.UUID(game_id)).values(status="ready", visibility="private")
    )
    await db_session.commit()
    await db_session.close()

    forker_cookie = await _register(client, "forker2@example.com", "forker2")
    resp = await client.post(
        f"/api/games/{game_id}/fork",
        cookies={COOKIE_NAME: forker_cookie},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_fork_unauthenticated_fails(client: AsyncClient, db_session: AsyncSession):
    """Unauthenticated users cannot fork."""
    owner_cookie = await _register(client, "aowner@example.com", "aowner")
    game_id = await _create_public_game(client, owner_cookie, db_session)

    client.cookies.clear()
    resp = await client.post(f"/api/games/{game_id}/fork")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_fork_includes_source_code(client: AsyncClient, db_session: AsyncSession):
    """Forked game has v0 with the source code from the original."""
    owner_cookie = await _register(client, "srcowner@example.com", "srcowner")
    game_id = await _create_public_game(client, owner_cookie, db_session, "Code Source")

    forker_cookie = await _register(client, "srcforker@example.com", "srcforker")
    resp = await client.post(
        f"/api/games/{game_id}/fork",
        cookies={COOKIE_NAME: forker_cookie},
    )
    forked_id = resp.json()["id"]

    # Check versions
    ver_resp = await client.get(f"/api/games/{forked_id}/versions")
    assert ver_resp.status_code == 200
    versions = ver_resp.json()
    assert len(versions) == 1
    assert versions[0]["version"] == 0
    assert "original code" in versions[0]["source_code"]
