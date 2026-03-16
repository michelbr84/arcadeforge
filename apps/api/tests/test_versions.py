"""Tests for game version creation (editor save)."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.sessions import COOKIE_NAME
from app.db.models import Game, GameVersion

import uuid
from sqlalchemy import select, update


async def _register(client: AsyncClient, email: str, username: str) -> str:
    resp = await client.post(
        "/api/auth/register",
        json={"email": email, "username": username, "password": "securepass123"},
    )
    return resp.cookies.get(COOKIE_NAME)


async def _create_ready_game_with_v0(client: AsyncClient, cookie: str, db_session: AsyncSession) -> str:
    """Create a game with v0 already present."""
    mock_queue = AsyncMock()
    with patch("app.games.router.get_queue", return_value=mock_queue):
        resp = await client.post(
            "/api/games",
            json={
                "genre": "shooter",
                "title": "Editable Game",
                "prompt": "A game that will be edited in the editor view",
            },
            cookies={COOKIE_NAME: cookie},
        )
    game_id = resp.json()["game_id"]

    await db_session.execute(
        update(Game).where(Game.id == uuid.UUID(game_id)).values(status="ready")
    )
    v0 = GameVersion(
        game_id=uuid.UUID(game_id),
        version=0,
        source_code='import pygame\npygame.init()\nscreen = pygame.display.set_mode((800,600))\nrunning = True\nwhile running:\n    for event in pygame.event.get():\n        if event.type == pygame.QUIT:\n            running = False\n    pygame.display.flip()\npygame.quit()',
    )
    db_session.add(v0)
    await db_session.commit()
    await db_session.close()
    return game_id


@pytest.mark.asyncio
async def test_create_version_success(client: AsyncClient, db_session: AsyncSession):
    """POST /versions creates v1 from edited code."""
    cookie = await _register(client, "editor@example.com", "editor")
    game_id = await _create_ready_game_with_v0(client, cookie, db_session)

    new_code = 'import pygame\nimport random\npygame.init()\nscreen = pygame.display.set_mode((800,600))\nrunning = True\nwhile running:\n    for event in pygame.event.get():\n        if event.type == pygame.QUIT:\n            running = False\n    screen.fill((0,0,0))\n    pygame.display.flip()\npygame.quit()'

    mock_queue = AsyncMock()
    with patch("app.games.router.get_queue", return_value=mock_queue):
        resp = await client.post(
            f"/api/games/{game_id}/versions",
            json={"source_code": new_code},
            cookies={COOKIE_NAME: cookie},
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["version"] == 1
    assert data["source_code"] == new_code


@pytest.mark.asyncio
async def test_create_version_increments(client: AsyncClient, db_session: AsyncSession):
    """Creating multiple versions increments correctly."""
    cookie = await _register(client, "multi@example.com", "multiversion")
    game_id = await _create_ready_game_with_v0(client, cookie, db_session)

    mock_queue = AsyncMock()
    with patch("app.games.router.get_queue", return_value=mock_queue):
        resp1 = await client.post(
            f"/api/games/{game_id}/versions",
            json={"source_code": "import pygame\npygame.init()\n# version 1 edit with enough content here"},
            cookies={COOKIE_NAME: cookie},
        )
        resp2 = await client.post(
            f"/api/games/{game_id}/versions",
            json={"source_code": "import pygame\npygame.init()\n# version 2 edit with enough content here"},
            cookies={COOKIE_NAME: cookie},
        )

    assert resp1.json()["version"] == 1
    assert resp2.json()["version"] == 2


@pytest.mark.asyncio
async def test_create_version_not_owner(client: AsyncClient, db_session: AsyncSession):
    """Non-owner cannot create versions."""
    cookie1 = await _register(client, "own@example.com", "ownerguy")
    cookie2 = await _register(client, "other@example.com", "otherguy2")
    game_id = await _create_ready_game_with_v0(client, cookie1, db_session)

    resp = await client.post(
        f"/api/games/{game_id}/versions",
        json={"source_code": "import pygame\npygame.init()\n# hacked version should not be allowed"},
        cookies={COOKIE_NAME: cookie2},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_version_too_short(client: AsyncClient, db_session: AsyncSession):
    """Source code under 10 chars is rejected."""
    cookie = await _register(client, "short@example.com", "shortcode")
    game_id = await _create_ready_game_with_v0(client, cookie, db_session)

    resp = await client.post(
        f"/api/games/{game_id}/versions",
        json={"source_code": "short"},
        cookies={COOKIE_NAME: cookie},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_version_unauthenticated(client: AsyncClient, db_session: AsyncSession):
    """Unauthenticated users cannot create versions."""
    cookie = await _register(client, "auth@example.com", "authowner")
    game_id = await _create_ready_game_with_v0(client, cookie, db_session)

    # Clear cookies to simulate unauthenticated request
    client.cookies.clear()
    resp = await client.post(
        f"/api/games/{game_id}/versions",
        json={"source_code": "import pygame\npygame.init()\n# should fail for unauthenticated user"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_versions_list_includes_new(client: AsyncClient, db_session: AsyncSession):
    """GET /versions shows both v0 and new versions."""
    cookie = await _register(client, "list@example.com", "listversions")
    game_id = await _create_ready_game_with_v0(client, cookie, db_session)

    mock_queue = AsyncMock()
    with patch("app.games.router.get_queue", return_value=mock_queue):
        await client.post(
            f"/api/games/{game_id}/versions",
            json={"source_code": "import pygame\npygame.init()\n# new version with enough text to pass validation"},
            cookies={COOKIE_NAME: cookie},
        )

    resp = await client.get(f"/api/games/{game_id}/versions")
    assert resp.status_code == 200
    versions = resp.json()
    assert len(versions) == 2
    assert versions[0]["version"] == 1  # newest first
    assert versions[1]["version"] == 0
