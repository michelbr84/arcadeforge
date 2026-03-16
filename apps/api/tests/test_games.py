"""Tests for game CRUD and genre endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.auth.sessions import COOKIE_NAME


async def _register(client: AsyncClient, email: str, username: str) -> str:
    """Helper: register and return session cookie."""
    resp = await client.post(
        "/api/auth/register",
        json={"email": email, "username": username, "password": "securepass123"},
    )
    assert resp.status_code == 201
    return resp.cookies.get(COOKIE_NAME)


# === Genres ===


@pytest.mark.asyncio
async def test_list_genres(client: AsyncClient):
    """GET /api/games/genres returns genre list."""
    resp = await client.get("/api/games/genres")
    assert resp.status_code == 200
    genres = resp.json()
    assert len(genres) >= 3
    ids = [g["id"] for g in genres]
    assert "shooter" in ids
    assert "puzzle" in ids
    assert "sports" in ids


@pytest.mark.asyncio
async def test_get_genre_detail(client: AsyncClient):
    """GET /api/games/genres/:id returns genre details."""
    resp = await client.get("/api/games/genres/shooter")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "shooter"
    assert "difficulty_options" in data


@pytest.mark.asyncio
async def test_get_genre_not_found(client: AsyncClient):
    """GET /api/games/genres/:id returns 404 for unknown genre."""
    resp = await client.get("/api/games/genres/nonexistent")
    assert resp.status_code == 404


# === Game Creation ===


@pytest.mark.asyncio
async def test_create_game_returns_202(client: AsyncClient):
    """POST /api/games returns 202 Accepted with game_id."""
    cookie = await _register(client, "creator@example.com", "creator")

    # Mock the arq queue to avoid needing real Redis for job enqueue
    mock_queue = AsyncMock()
    with patch("app.games.router.get_queue", return_value=mock_queue):
        resp = await client.post(
            "/api/games",
            json={
                "genre": "shooter",
                "title": "My Space Game",
                "prompt": "Create a space shooter with asteroids and power-ups",
            },
            cookies={COOKIE_NAME: cookie},
        )

    assert resp.status_code == 202
    data = resp.json()
    assert "game_id" in data
    assert data["status"] == "queued"
    assert "status_url" in data
    mock_queue.enqueue_job.assert_called_once()


@pytest.mark.asyncio
async def test_create_game_invalid_genre(client: AsyncClient):
    """POST /api/games with unknown genre returns 422."""
    cookie = await _register(client, "badgenre@example.com", "badgenre")

    resp = await client.post(
        "/api/games",
        json={
            "genre": "nonexistent",
            "title": "Bad Game",
            "prompt": "This should fail because genre is invalid",
        },
        cookies={COOKIE_NAME: cookie},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_game_unauthenticated(client: AsyncClient):
    """POST /api/games without auth returns 401."""
    resp = await client.post(
        "/api/games",
        json={
            "genre": "shooter",
            "title": "Unauthorized Game",
            "prompt": "This should fail because user is not logged in at all",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_game_short_prompt(client: AsyncClient):
    """POST /api/games with too-short prompt returns 422."""
    cookie = await _register(client, "shortprompt@example.com", "shortprompt")

    resp = await client.post(
        "/api/games",
        json={
            "genre": "puzzle",
            "title": "Short",
            "prompt": "too short",
        },
        cookies={COOKIE_NAME: cookie},
    )
    assert resp.status_code == 422


# === Game List ===


@pytest.mark.asyncio
async def test_list_my_games(client: AsyncClient):
    """GET /api/games returns user's games."""
    cookie = await _register(client, "lister@example.com", "lister")

    mock_queue = AsyncMock()
    with patch("app.games.router.get_queue", return_value=mock_queue):
        await client.post(
            "/api/games",
            json={
                "genre": "shooter",
                "title": "Game One",
                "prompt": "A shooter game with asteroids and scoring system",
            },
            cookies={COOKIE_NAME: cookie},
        )
        await client.post(
            "/api/games",
            json={
                "genre": "puzzle",
                "title": "Game Two",
                "prompt": "A puzzle game with colored blocks and matching mechanics",
            },
            cookies={COOKIE_NAME: cookie},
        )

    resp = await client.get("/api/games", cookies={COOKIE_NAME: cookie})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["games"]) == 2


# === Game Detail ===


@pytest.mark.asyncio
async def test_get_game(client: AsyncClient):
    """GET /api/games/:id returns game details."""
    cookie = await _register(client, "detail@example.com", "detailuser")

    mock_queue = AsyncMock()
    with patch("app.games.router.get_queue", return_value=mock_queue):
        create_resp = await client.post(
            "/api/games",
            json={
                "genre": "sports",
                "title": "Pong Clone",
                "prompt": "A classic pong game with two paddles and a bouncing ball",
            },
            cookies={COOKIE_NAME: cookie},
        )

    game_id = create_resp.json()["game_id"]

    resp = await client.get(f"/api/games/{game_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Pong Clone"
    assert data["genre"] == "sports"


@pytest.mark.asyncio
async def test_get_game_not_found(client: AsyncClient):
    """GET /api/games/:id returns 404 for unknown game."""
    resp = await client.get("/api/games/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


# === Delete ===


@pytest.mark.asyncio
async def test_delete_game(client: AsyncClient):
    """DELETE /api/games/:id deletes the game."""
    cookie = await _register(client, "deleter@example.com", "deleter")

    mock_queue = AsyncMock()
    with patch("app.games.router.get_queue", return_value=mock_queue):
        create_resp = await client.post(
            "/api/games",
            json={
                "genre": "shooter",
                "title": "Delete Me",
                "prompt": "A game that will be deleted right after creation",
            },
            cookies={COOKIE_NAME: cookie},
        )

    game_id = create_resp.json()["game_id"]

    resp = await client.delete(f"/api/games/{game_id}", cookies={COOKIE_NAME: cookie})
    assert resp.status_code == 204

    # Verify gone
    get_resp = await client.get(f"/api/games/{game_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_game_not_owner(client: AsyncClient):
    """DELETE /api/games/:id by non-owner returns 403."""
    cookie1 = await _register(client, "owner@example.com", "gameowner")
    cookie2 = await _register(client, "other@example.com", "otheruser")

    mock_queue = AsyncMock()
    with patch("app.games.router.get_queue", return_value=mock_queue):
        create_resp = await client.post(
            "/api/games",
            json={
                "genre": "puzzle",
                "title": "Not Yours",
                "prompt": "This game belongs to someone else entirely",
            },
            cookies={COOKIE_NAME: cookie1},
        )

    game_id = create_resp.json()["game_id"]

    resp = await client.delete(f"/api/games/{game_id}", cookies={COOKIE_NAME: cookie2})
    assert resp.status_code == 403
