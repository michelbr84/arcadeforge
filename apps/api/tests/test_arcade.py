"""Tests for public arcade endpoints."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.auth.sessions import COOKIE_NAME
from app.db.models import Game, GameVersion


async def _register(client: AsyncClient, email: str, username: str) -> str:
    resp = await client.post(
        "/api/auth/register",
        json={"email": email, "username": username, "password": "securepass123"},
    )
    return resp.cookies.get(COOKIE_NAME)


async def _create_public_game(
    client: AsyncClient, cookie: str, db_session: AsyncSession,
    title: str, genre: str = "shooter",
) -> str:
    """Create a public, ready game for arcade testing."""
    mock_queue = AsyncMock()
    with patch("app.games.router.get_queue", return_value=mock_queue):
        resp = await client.post(
            "/api/games",
            json={"genre": genre, "title": title, "prompt": f"A {genre} game called {title} for testing"},
            cookies={COOKIE_NAME: cookie},
        )
    game_id = resp.json()["game_id"]

    # Make it public and ready
    await db_session.execute(
        update(Game)
        .where(Game.id == uuid.UUID(game_id))
        .values(status="ready", visibility="public")
    )
    v0 = GameVersion(
        game_id=uuid.UUID(game_id),
        version=0,
        source_code="import pygame\npygame.init()",
    )
    db_session.add(v0)
    await db_session.commit()
    await db_session.close()
    return game_id


@pytest.mark.asyncio
async def test_arcade_lists_public_games(client: AsyncClient, db_session: AsyncSession):
    """GET /api/arcade/games returns public ready games."""
    cookie = await _register(client, "pub@example.com", "pubuser")
    await _create_public_game(client, cookie, db_session, "Public Shooter")

    resp = await client.get("/api/arcade/games")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any(g["title"] == "Public Shooter" for g in data["games"])


@pytest.mark.asyncio
async def test_arcade_excludes_private_games(client: AsyncClient, db_session: AsyncSession):
    """Private games should not appear in arcade."""
    cookie = await _register(client, "priv@example.com", "privuser")

    mock_queue = AsyncMock()
    with patch("app.games.router.get_queue", return_value=mock_queue):
        resp = await client.post(
            "/api/games",
            json={"genre": "puzzle", "title": "Private Game", "prompt": "This game should stay private and hidden"},
            cookies={COOKIE_NAME: cookie},
        )
    game_id = resp.json()["game_id"]
    # Mark ready but keep private (default)
    await db_session.execute(
        update(Game).where(Game.id == uuid.UUID(game_id)).values(status="ready")
    )
    await db_session.commit()
    await db_session.close()

    resp = await client.get("/api/arcade/games")
    assert resp.status_code == 200
    assert not any(g["title"] == "Private Game" for g in resp.json()["games"])


@pytest.mark.asyncio
async def test_arcade_search(client: AsyncClient, db_session: AsyncSession):
    """Search filters by title."""
    cookie = await _register(client, "search@example.com", "searchuser")
    await _create_public_game(client, cookie, db_session, "Alpha Blaster")
    await _create_public_game(client, cookie, db_session, "Beta Runner", "platformer")

    resp = await client.get("/api/arcade/games?q=Alpha")
    assert resp.status_code == 200
    games = resp.json()["games"]
    assert len(games) >= 1
    assert all("alpha" in g["title"].lower() for g in games)


@pytest.mark.asyncio
async def test_arcade_genre_filter(client: AsyncClient, db_session: AsyncSession):
    """Genre filter returns only matching genre."""
    cookie = await _register(client, "genre@example.com", "genreuser")
    await _create_public_game(client, cookie, db_session, "Pong", "sports")
    await _create_public_game(client, cookie, db_session, "Tetris", "puzzle")

    resp = await client.get("/api/arcade/games?genre=sports")
    assert resp.status_code == 200
    games = resp.json()["games"]
    assert all(g["genre"] == "sports" for g in games)


@pytest.mark.asyncio
async def test_arcade_hides_prompt(client: AsyncClient, db_session: AsyncSession):
    """Arcade responses should not expose the original prompt."""
    cookie = await _register(client, "noprompt@example.com", "noprompt")
    await _create_public_game(client, cookie, db_session, "No Prompt")

    resp = await client.get("/api/arcade/games")
    for game in resp.json()["games"]:
        if game["title"] == "No Prompt":
            assert game["prompt"] is None


@pytest.mark.asyncio
async def test_arcade_includes_username(client: AsyncClient, db_session: AsyncSession):
    """Arcade game cards include the owner's username."""
    cookie = await _register(client, "named@example.com", "nameduser")
    await _create_public_game(client, cookie, db_session, "Named Game")

    resp = await client.get("/api/arcade/games")
    for game in resp.json()["games"]:
        if game["title"] == "Named Game":
            assert game["owner_username"] == "nameduser"


@pytest.mark.asyncio
async def test_arcade_no_auth_required(client: AsyncClient):
    """Arcade endpoint works without authentication."""
    client.cookies.clear()
    resp = await client.get("/api/arcade/games")
    assert resp.status_code == 200
