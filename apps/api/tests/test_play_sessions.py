"""Tests for play session endpoints and lifecycle."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.sessions import COOKIE_NAME
from app.db.models import Game, GameVersion, PlaySession


async def _register(client: AsyncClient, email: str, username: str) -> str:
    resp = await client.post(
        "/api/auth/register",
        json={"email": email, "username": username, "password": "securepass123"},
    )
    return resp.cookies.get(COOKIE_NAME)


async def _create_ready_game(client: AsyncClient, cookie: str, db_session: AsyncSession) -> str:
    """Create a game and manually mark it as ready with a version."""
    mock_queue = AsyncMock()
    with patch("app.games.router.get_queue", return_value=mock_queue):
        resp = await client.post(
            "/api/games",
            json={
                "genre": "shooter",
                "title": "Playable Game",
                "prompt": "A space shooter that is ready for playing",
            },
            cookies={COOKIE_NAME: cookie},
        )
    game_id = resp.json()["game_id"]

    # Manually set game to ready and create a version
    from sqlalchemy import select, update
    import uuid

    await db_session.execute(
        update(Game).where(Game.id == uuid.UUID(game_id)).values(status="ready")
    )
    version = GameVersion(
        game_id=uuid.UUID(game_id),
        version=0,
        source_code='import pygame\npygame.init()\nprint("test")',
        source_zip_path="/data/workspaces/test/test/v0",
    )
    db_session.add(version)
    await db_session.commit()

    return game_id


# === Play Session Start ===


@pytest.mark.asyncio
async def test_play_returns_202(client: AsyncClient, db_session: AsyncSession):
    """POST /play on a ready game returns 202."""
    cookie = await _register(client, "player@example.com", "player")
    game_id = await _create_ready_game(client, cookie, db_session)

    mock_queue = AsyncMock()
    with patch("app.games.router.get_queue", return_value=mock_queue):
        resp = await client.post(
            f"/api/games/{game_id}/play",
            cookies={COOKIE_NAME: cookie},
        )

    assert resp.status_code == 202
    data = resp.json()
    assert "session_id" in data
    assert data["status"] == "starting"
    mock_queue.enqueue_job.assert_called_once()


@pytest.mark.asyncio
async def test_play_not_ready_returns_400(client: AsyncClient):
    """POST /play on a non-ready game returns 400."""
    cookie = await _register(client, "notready@example.com", "notready")

    mock_queue = AsyncMock()
    with patch("app.games.router.get_queue", return_value=mock_queue):
        resp = await client.post(
            "/api/games",
            json={
                "genre": "shooter",
                "title": "Queued Game",
                "prompt": "This game is still queued not ready yet",
            },
            cookies={COOKIE_NAME: cookie},
        )
    game_id = resp.json()["game_id"]

    with patch("app.games.router.get_queue", return_value=mock_queue):
        resp = await client.post(
            f"/api/games/{game_id}/play",
            cookies={COOKIE_NAME: cookie},
        )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_play_increments_play_count(client: AsyncClient, db_session: AsyncSession):
    """POST /play increments the game's play_count."""
    cookie = await _register(client, "counter@example.com", "counter")
    game_id = await _create_ready_game(client, cookie, db_session)

    mock_queue = AsyncMock()
    with patch("app.games.router.get_queue", return_value=mock_queue):
        await client.post(
            f"/api/games/{game_id}/play",
            cookies={COOKIE_NAME: cookie},
        )

    resp = await client.get(f"/api/games/{game_id}")
    assert resp.json()["play_count"] == 1


@pytest.mark.asyncio
async def test_play_session_not_found(client: AsyncClient, db_session: AsyncSession):
    """GET /play/:sessionId returns 404 for unknown session."""
    cookie = await _register(client, "nosess@example.com", "nosess")
    game_id = await _create_ready_game(client, cookie, db_session)

    resp = await client.get(
        f"/api/games/{game_id}/play/00000000-0000-0000-0000-000000000000"
    )
    assert resp.status_code == 404


# === Concurrent Session Limits ===


@pytest.mark.asyncio
async def test_max_concurrent_sessions(client: AsyncClient, db_session: AsyncSession):
    """Exceeding max concurrent sessions returns 429."""
    cookie = await _register(client, "heavy@example.com", "heavyuser")
    game_id = await _create_ready_game(client, cookie, db_session)

    mock_queue = AsyncMock()
    with patch("app.games.router.get_queue", return_value=mock_queue):
        # Start 2 sessions (max allowed)
        await client.post(f"/api/games/{game_id}/play", cookies={COOKIE_NAME: cookie})
        await client.post(f"/api/games/{game_id}/play", cookies={COOKIE_NAME: cookie})

        # Third should be rejected
        resp = await client.post(
            f"/api/games/{game_id}/play",
            cookies={COOKIE_NAME: cookie},
        )

    assert resp.status_code == 429
    assert "concurrent" in resp.json()["detail"].lower()


# === TTL Reaper ===


@pytest.mark.asyncio
async def test_reaper_expires_sessions(client: AsyncClient, db_session: AsyncSession, engine):
    """Reaper should mark expired running sessions as expired."""
    from app.games.reaper import reap_expired_sessions
    from sqlalchemy.ext.asyncio import async_sessionmaker

    # Create real parent records
    cookie = await _register(client, "reaper@example.com", "reaperuser")
    game_id = await _create_ready_game(client, cookie, db_session)

    # Get the version ID
    import uuid
    from sqlalchemy import select
    result = await db_session.execute(
        select(GameVersion).where(GameVersion.game_id == uuid.UUID(game_id))
    )
    version = result.scalar_one()

    # Create an expired play session
    expired_session = PlaySession(
        game_version_id=version.id,
        user_id=None,
        status="running",
        sandbox_ref="af-play-fake123",
        ws_url="ws://localhost:6100",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    db_session.add(expired_session)
    await db_session.commit()

    session_id = expired_session.id

    # Run reaper with the async engine from the fixture
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    with patch("app.games.reaper.stop_sandbox"):
        reaped = await reap_expired_sessions(session_factory)

    assert reaped == 1

    # Verify session is now expired — use a fresh session from the engine
    async with session_factory() as fresh_session:
        result = await fresh_session.execute(
            select(PlaySession).where(PlaySession.id == session_id)
        )
        updated = result.scalar_one()
        assert updated.status == "expired"
