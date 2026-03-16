"""Game API routes: CRUD, genres, generation."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.models import Game, GameVersion, User
from app.db.session import get_db
from app.games.genres import Genre, get_all_genres, get_genre
from app.games.schemas import (
    CreateGameRequest,
    GameCreatedResponse,
    GameListResponse,
    GameResponse,
    GameVersionResponse,
)
from app.jobs.queue import get_queue

router = APIRouter(prefix="/api/games", tags=["games"])


# --- Genres ---


@router.get("/genres", response_model=list[Genre])
async def list_genres():
    """List all available game genres."""
    return get_all_genres()


@router.get("/genres/{genre_id}", response_model=Genre)
async def get_genre_detail(genre_id: str):
    """Get details for a specific genre."""
    genre = get_genre(genre_id)
    if genre is None:
        raise HTTPException(status_code=404, detail="Genre not found.")
    return genre


# --- Game CRUD ---


@router.post("", response_model=GameCreatedResponse, status_code=202)
async def create_game(
    body: CreateGameRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new game and enqueue generation job.

    Returns 202 Accepted — generation happens asynchronously.
    """
    game = Game(
        owner_user_id=user.id,
        genre=body.genre,
        title=body.title,
        prompt=body.prompt,
        pitch=body.prompt[:200] if body.prompt else None,
    )
    db.add(game)
    await db.flush()

    # Enqueue generation job
    queue = await get_queue()
    await queue.enqueue_job(
        "generate_game_task",
        str(game.id),
        _job_id=f"gen:{game.id}",
    )

    return GameCreatedResponse(
        game_id=str(game.id),
        status="queued",
        message="Game creation queued. Generation will begin shortly.",
    )


@router.get("", response_model=GameListResponse)
async def list_my_games(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List the current user's games."""
    count_result = await db.execute(
        select(func.count()).where(Game.owner_user_id == user.id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Game)
        .where(Game.owner_user_id == user.id)
        .order_by(Game.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    games = result.scalars().all()

    return GameListResponse(
        games=[
            GameResponse(
                id=str(g.id),
                owner_user_id=str(g.owner_user_id),
                genre=g.genre,
                title=g.title,
                pitch=g.pitch,
                prompt=g.prompt,
                visibility=g.visibility,
                play_count=g.play_count,
                created_at=g.created_at,
                updated_at=g.updated_at,
            )
            for g in games
        ],
        total=total,
    )


@router.get("/{game_id}", response_model=GameResponse)
async def get_game(
    game_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a game by ID. Public games are visible to all; private games only to owner."""
    try:
        uid = uuid.UUID(game_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid game ID.")

    result = await db.execute(select(Game).where(Game.id == uid))
    game = result.scalar_one_or_none()

    if game is None:
        raise HTTPException(status_code=404, detail="Game not found.")

    return GameResponse(
        id=str(game.id),
        owner_user_id=str(game.owner_user_id),
        genre=game.genre,
        title=game.title,
        pitch=game.pitch,
        prompt=game.prompt,
        visibility=game.visibility,
        play_count=game.play_count,
        created_at=game.created_at,
        updated_at=game.updated_at,
    )


@router.get("/{game_id}/versions", response_model=list[GameVersionResponse])
async def list_game_versions(
    game_id: str,
    db: AsyncSession = Depends(get_db),
):
    """List all versions of a game."""
    try:
        uid = uuid.UUID(game_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid game ID.")

    result = await db.execute(
        select(GameVersion)
        .where(GameVersion.game_id == uid)
        .order_by(GameVersion.version.desc())
    )
    versions = result.scalars().all()

    return [
        GameVersionResponse(
            id=str(v.id),
            game_id=str(v.game_id),
            version=v.version,
            blueprint_json=v.blueprint_json,
            source_code=v.source_code,
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.delete("/{game_id}", status_code=204)
async def delete_game(
    game_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a game. Only the owner can delete."""
    try:
        uid = uuid.UUID(game_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid game ID.")

    result = await db.execute(select(Game).where(Game.id == uid))
    game = result.scalar_one_or_none()

    if game is None:
        raise HTTPException(status_code=404, detail="Game not found.")

    if game.owner_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized.")

    await db.delete(game)
