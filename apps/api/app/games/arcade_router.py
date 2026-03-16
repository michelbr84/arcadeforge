"""Public arcade routes — no authentication required."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rate_limit import check_rate_limit
from app.db.models import Game, User
from app.db.session import get_db
from app.games.schemas import GameListResponse, GameResponse

router = APIRouter(prefix="/api/arcade", tags=["arcade"])


def _game_response(g: Game, username: str | None = None) -> dict:
    """Convert a Game to response dict with owner username."""
    return {
        "id": str(g.id),
        "owner_user_id": str(g.owner_user_id),
        "owner_username": username,
        "genre": g.genre,
        "title": g.title,
        "pitch": g.pitch,
        "prompt": None,  # Don't expose prompts publicly
        "visibility": g.visibility,
        "play_count": g.play_count,
        "status": g.status,
        "status_message": None,  # Don't expose internal status messages
        "created_at": g.created_at.isoformat(),
        "updated_at": g.updated_at.isoformat(),
    }


@router.get("/games")
async def list_arcade_games(
    db: AsyncSession = Depends(get_db),
    q: str = Query(default="", description="Search title"),
    genre: str = Query(default="", description="Filter by genre"),
    sort: str = Query(default="trending", description="Sort: trending, newest"),
    limit: int = Query(default=20, le=50),
    offset: int = Query(default=0, ge=0),
):
    """List public, ready games for the arcade.

    No authentication required. Supports search, genre filter, and sorting.
    """
    # Base query: only public + ready games
    query = (
        select(Game, User.username)
        .join(User, Game.owner_user_id == User.id)
        .where(Game.visibility == "public", Game.status == "ready")
    )

    # Search filter
    if q:
        query = query.where(Game.title.ilike(f"%{q}%"))

    # Genre filter
    if genre:
        query = query.where(Game.genre == genre)

    # Count total before pagination
    count_query = select(func.count()).select_from(
        query.with_only_columns(Game.id).subquery()
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Sort
    if sort == "newest":
        query = query.order_by(Game.created_at.desc())
    else:  # trending (default)
        query = query.order_by(Game.play_count.desc(), Game.created_at.desc())

    # Paginate
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    rows = result.all()

    games = [_game_response(game, username) for game, username in rows]

    return {
        "games": games,
        "total": total,
        "query": q,
        "genre": genre,
        "sort": sort,
    }


@router.get("/games/{game_id}")
async def get_arcade_game(
    game_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a public game's details for the arcade view."""
    import uuid

    try:
        uid = uuid.UUID(game_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid game ID.")

    result = await db.execute(
        select(Game, User.username)
        .join(User, Game.owner_user_id == User.id)
        .where(Game.id == uid, Game.visibility == "public", Game.status == "ready")
    )
    row = result.first()

    if row is None:
        raise HTTPException(status_code=404, detail="Game not found or not public.")

    game, username = row
    return _game_response(game, username)
