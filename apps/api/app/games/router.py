"""Game API routes: CRUD, genres, generation, validation, play."""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.rate_limit import check_rate_limit
from app.db.models import Game, GameVersion, PlaySession, ValidationRun, User
from app.db.session import get_db
from app.games.genres import Genre, get_all_genres, get_genre
from app.games.play_schemas import PlaySessionCreatedResponse, PlaySessionResponse
from app.games.generator import GenerationResult, generate_game, generate_game_with_llm, save_to_workspace
from app.games.html_generator import generate_html_game
from app.games.scanner import scan_code

logger = logging.getLogger("arcadeforge.games")
from app.games.schemas import (
    CreateGameRequest,
    CreateVersionRequest,
    GameCreatedResponse,
    GameListResponse,
    GameResponse,
    GameStatusResponse,
    GameVersionResponse,
)
from app.games.validation_schemas import (
    ScanResultResponse,
    ValidationCreatedResponse,
    ValidationRunResponse,
)
from app.config import settings
from app.jobs.queue import get_queue

router = APIRouter(prefix="/api/games", tags=["games"])


def _game_response(g: Game) -> GameResponse:
    """Convert a Game ORM model to a GameResponse."""
    return GameResponse(
        id=str(g.id),
        owner_user_id=str(g.owner_user_id),
        genre=g.genre,
        title=g.title,
        pitch=g.pitch,
        prompt=g.prompt,
        visibility=g.visibility,
        play_count=g.play_count,
        status=g.status,
        status_message=g.status_message,
        created_at=g.created_at,
        updated_at=g.updated_at,
    )


async def _get_game_or_404(game_id: str, db: AsyncSession) -> Game:
    """Load a game by ID or raise 404."""
    try:
        uid = uuid.UUID(game_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid game ID.")

    result = await db.execute(select(Game).where(Game.id == uid))
    game = result.scalar_one_or_none()
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found.")
    return game


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


async def _generate_game_inline(game_id: str, user_id: str) -> None:
    """Generate a game directly in the API process (no worker needed).

    Runs as a FastAPI BackgroundTask so the endpoint returns immediately.
    """
    from app.db.session import async_session_factory

    try:
        async with async_session_factory() as session:
            result = await session.execute(select(Game).where(Game.id == game_id))
            game = result.scalar_one_or_none()
            if not game:
                logger.error(f"Game {game_id} not found for generation")
                return

            game.status = "generating"
            await session.commit()

            # Load owner for LLM settings
            user_result = await session.execute(
                select(User).where(User.id == game.owner_user_id)
            )
            owner = user_result.scalar_one_or_none()

            gen_result: GenerationResult | None = None

            # Try LLM generation if user has it configured
            if owner and owner.llm_provider and owner.llm_api_key_encrypted:
                try:
                    from app.auth.encryption import decrypt_api_key

                    api_key = decrypt_api_key(owner.llm_api_key_encrypted)
                    gen_result = await generate_game_with_llm(
                        provider=owner.llm_provider,
                        api_key=api_key,
                        model=owner.llm_model or "",
                        genre=game.genre,
                        title=game.title,
                        prompt=game.prompt or "",
                        difficulty="medium",
                    )
                    logger.info(f"Game {game_id} generated via LLM ({owner.llm_provider})")
                except Exception as e:
                    logger.warning(f"LLM failed for {game_id}, using template: {e}")

            # Fallback to template
            if gen_result is None:
                gen_result = await asyncio.to_thread(
                    generate_game,
                    genre=game.genre,
                    title=game.title,
                    prompt=game.prompt or "",
                    difficulty="medium",
                )

            # Save files to workspace
            workspace_path = await asyncio.to_thread(
                save_to_workspace,
                user_id=str(game.owner_user_id),
                game_id=str(game.id),
                version=0,
                result=gen_result,
            )

            # Create version v0
            version = GameVersion(
                id=uuid.uuid4(),
                game_id=game.id,
                version=0,
                blueprint_json=gen_result.metadata,
                source_code=gen_result.files.get("main.py", ""),
                source_zip_path=workspace_path,
            )
            session.add(version)

            game.status = "ready"
            game.visibility = "public"
            game.status_message = gen_result.summary
            await session.commit()
            logger.info(f"Game {game_id} ready → {workspace_path}")

    except Exception as exc:
        logger.exception(f"Game generation failed for {game_id}")
        try:
            async with async_session_factory() as session:
                result = await session.execute(select(Game).where(Game.id == game_id))
                game = result.scalar_one_or_none()
                if game:
                    game.status = "failed"
                    game.status_message = str(exc)[:500]
                    await session.commit()
        except Exception:
            logger.exception("Failed to mark game as failed")


@router.post("", response_model=GameCreatedResponse, status_code=202)
async def create_game(
    body: CreateGameRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new game and generate it immediately.

    Returns 202 Accepted after generation is complete.
    """
    game = Game(
        owner_user_id=user.id,
        genre=body.genre,
        title=body.title,
        prompt=body.prompt,
        pitch=body.prompt[:200] if body.prompt else None,
    )
    db.add(game)
    await db.commit()

    # Generate inline — BackgroundTasks unreliable on free-tier hosting
    await _generate_game_inline(str(game.id), str(user.id))

    # Re-fetch to get final status after generation
    result = await db.execute(select(Game).where(Game.id == game.id))
    game = result.scalar_one()

    return GameCreatedResponse(
        game_id=str(game.id),
        status=game.status,
        message=game.status_message or "Game created.",
        status_url=f"/api/games/{game.id}/status",
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
        games=[_game_response(g) for g in games],
        total=total,
    )


@router.get("/{game_id}", response_model=GameResponse)
async def get_game(game_id: str, db: AsyncSession = Depends(get_db)):
    """Get a game by ID."""
    game = await _get_game_or_404(game_id, db)
    return _game_response(game)


@router.get("/{game_id}/status", response_model=GameStatusResponse)
async def get_game_status(game_id: str, db: AsyncSession = Depends(get_db)):
    """Get the generation status of a game."""
    game = await _get_game_or_404(game_id, db)
    return GameStatusResponse(
        game_id=str(game.id),
        status=game.status,
        status_message=game.status_message,
    )


@router.get("/{game_id}/versions", response_model=list[GameVersionResponse])
async def list_game_versions(game_id: str, db: AsyncSession = Depends(get_db)):
    """List all versions of a game."""
    game = await _get_game_or_404(game_id, db)

    result = await db.execute(
        select(GameVersion)
        .where(GameVersion.game_id == game.id)
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


@router.post("/{game_id}/versions", response_model=GameVersionResponse, status_code=201)
async def create_version(
    game_id: str,
    body: CreateVersionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save edited code as a new version of the game.

    - Creates a new game_version row (v1, v2, etc.)
    - Runs code scanner automatically
    - Enqueues validation if scan passes
    """
    game = await _get_game_or_404(game_id, db)

    if game.owner_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized.")

    # Determine next version number
    latest_result = await db.execute(
        select(func.max(GameVersion.version)).where(GameVersion.game_id == game.id)
    )
    max_val = latest_result.scalar()
    next_version = (max_val + 1) if max_val is not None else 0

    # Create version
    version = GameVersion(
        game_id=game.id,
        version=next_version,
        source_code=body.source_code,
        blueprint_json=None,
    )
    db.add(version)
    await db.flush()

    # Auto-validate: run scanner
    scan_result = scan_code(body.source_code)
    validation = ValidationRun(
        game_version_id=version.id,
        status="passed" if scan_result.passed else "completed",
        scan_passed=scan_result.passed,
    )
    db.add(validation)

    # Touch the game so arcade listings reflect the update
    game.status_message = f"v{next_version} saved"

    # If scan passed, enqueue full smoke-check validation
    if scan_result.passed:
        try:
            queue = await get_queue()
            await queue.enqueue_job(
                "validate_game_task",
                str(validation.id),
                _job_id=f"val:{validation.id}",
            )
            validation.status = "running"
        except Exception:
            pass  # Queue not available — scan result still saved

    return GameVersionResponse(
        id=str(version.id),
        game_id=str(version.game_id),
        version=version.version,
        blueprint_json=version.blueprint_json,
        source_code=version.source_code,
        created_at=version.created_at,
    )


@router.delete("/{game_id}", status_code=204)
async def delete_game(
    game_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a game. Only the owner can delete."""
    game = await _get_game_or_404(game_id, db)

    if game.owner_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized.")

    await db.delete(game)


# --- Fork ---


@router.post("/{game_id}/fork", response_model=GameResponse, status_code=201)
async def fork_game(
    game_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fork a public game into the current user's library.

    Creates a new game owned by the user with the latest version's code.
    """
    source_game = await _get_game_or_404(game_id, db)

    if source_game.visibility != "public":
        raise HTTPException(status_code=403, detail="Only public games can be forked.")

    # Get latest version of the source game
    result = await db.execute(
        select(GameVersion)
        .where(GameVersion.game_id == source_game.id)
        .order_by(GameVersion.version.desc())
        .limit(1)
    )
    source_version = result.scalar_one_or_none()

    # Create forked game
    forked = Game(
        owner_user_id=user.id,
        genre=source_game.genre,
        title=f"{source_game.title} (fork)",
        prompt=source_game.prompt,
        pitch=source_game.pitch,
        status="ready",
    )
    db.add(forked)
    await db.flush()

    # Copy version as v0
    if source_version:
        v0 = GameVersion(
            game_id=forked.id,
            version=0,
            source_code=source_version.source_code,
            blueprint_json=source_version.blueprint_json,
        )
        db.add(v0)

    return _game_response(forked)


# --- Validation ---


@router.post("/{game_id}/validate", response_model=ValidationCreatedResponse, status_code=202)
async def validate_game(
    game_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Validate the latest version of a game.

    Runs static code scanner + smoke checks asynchronously.
    Returns 202 Accepted.
    """
    game = await _get_game_or_404(game_id, db)

    if game.owner_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized.")

    # Find latest version
    result = await db.execute(
        select(GameVersion)
        .where(GameVersion.game_id == game.id)
        .order_by(GameVersion.version.desc())
        .limit(1)
    )
    version = result.scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=400, detail="No versions to validate.")

    # Run scanner immediately (fast, synchronous)
    scan_result = None
    if version.source_code:
        scan_result = scan_code(version.source_code)

    # Create validation run
    validation = ValidationRun(
        game_version_id=version.id,
        status="running" if scan_result and scan_result.passed else "completed",
        scan_passed=scan_result.passed if scan_result else None,
        report_json_path=None,
    )
    db.add(validation)
    await db.flush()

    # If scan failed, mark completed immediately with findings
    if scan_result and not scan_result.passed:
        validation.status = "completed"
        return ValidationCreatedResponse(
            validation_id=str(validation.id),
            status="completed",
            message=f"Code scan failed: {scan_result.critical_count} critical, {scan_result.high_count} high severity findings.",
        )

    # Scan passed — enqueue full validation job
    queue = await get_queue()
    await queue.enqueue_job(
        "validate_game_task",
        str(validation.id),
        _job_id=f"val:{validation.id}",
    )

    return ValidationCreatedResponse(
        validation_id=str(validation.id),
        status="running",
        message="Validation started. Code scan passed.",
    )


@router.get("/{game_id}/validations", response_model=list[ValidationRunResponse])
async def list_validations(
    game_id: str,
    db: AsyncSession = Depends(get_db),
):
    """List validation runs for a game."""
    game = await _get_game_or_404(game_id, db)

    # Get all version IDs for this game
    versions_result = await db.execute(
        select(GameVersion.id).where(GameVersion.game_id == game.id)
    )
    version_ids = [v[0] for v in versions_result.all()]

    if not version_ids:
        return []

    result = await db.execute(
        select(ValidationRun)
        .where(ValidationRun.game_version_id.in_(version_ids))
        .order_by(ValidationRun.created_at.desc())
    )
    runs = result.scalars().all()

    return [
        ValidationRunResponse(
            id=str(r.id),
            game_version_id=str(r.game_version_id),
            status=r.status,
            scan_passed=r.scan_passed,
            report_json_path=r.report_json_path,
            screenshot_path=r.screenshot_path,
            created_at=r.created_at,
            completed_at=r.completed_at,
        )
        for r in runs
    ]


@router.post("/{game_id}/scan", response_model=ScanResultResponse)
async def scan_game_code(
    game_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Run the static code scanner on the latest version (no async job needed)."""
    game = await _get_game_or_404(game_id, db)

    result = await db.execute(
        select(GameVersion)
        .where(GameVersion.game_id == game.id)
        .order_by(GameVersion.version.desc())
        .limit(1)
    )
    version = result.scalar_one_or_none()
    if version is None or not version.source_code:
        raise HTTPException(status_code=400, detail="No code to scan.")

    scan_result = scan_code(version.source_code)

    return ScanResultResponse(
        passed=scan_result.passed,
        findings=[
            {
                "line": f.line,
                "pattern": f.pattern,
                "severity": f.severity,
                "message": f.message,
            }
            for f in scan_result.findings
        ],
        critical_count=scan_result.critical_count,
        high_count=scan_result.high_count,
    )


# --- Browser Play (HTML5) ---


@router.get("/{game_id}/play-html")
async def get_game_html(
    game_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Serve a self-contained HTML5 Canvas version of the game.

    Returns text/html that can be embedded in an iframe.
    No authentication required for public games. Rate limited per IP.
    """
    # Rate limit: 60 requests per minute per IP
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if not ip and request.client:
        ip = request.client.host
    allowed, remaining = await check_rate_limit(f"play_html:{ip}", 60, 60)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many requests.")

    game = await _get_game_or_404(game_id, db)

    # Only public, ready games can be played
    if game.visibility != "public":
        raise HTTPException(status_code=404, detail="Game not found.")
    if game.status != "ready":
        raise HTTPException(status_code=400, detail="Game is not ready to play.")

    # Get difficulty from latest version blueprint
    result = await db.execute(
        select(GameVersion)
        .where(GameVersion.game_id == game.id)
        .order_by(GameVersion.version.desc())
        .limit(1)
    )
    version = result.scalar_one_or_none()
    difficulty = "medium"
    if version and version.blueprint_json:
        difficulty = version.blueprint_json.get("difficulty", "medium")
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = "medium"

    try:
        html = generate_html_game(
            genre=game.genre,
            title=game.title,
            difficulty=difficulty,
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Browser play not available for genre: {game.genre}",
        )

    # Increment play count (debounce: once per IP+game per hour)
    play_key = f"play_seen:{game_id}:{ip}"
    seen, _ = await check_rate_limit(play_key, 1, 3600)
    if not seen:
        await db.execute(
            update(Game).where(Game.id == game.id).values(play_count=Game.play_count + 1)
        )
        await db.commit()

    from fastapi.responses import HTMLResponse
    return HTMLResponse(
        content=html,
        headers={
            "Content-Security-Policy": "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'",
            "X-Content-Type-Options": "nosniff",
        },
    )


# --- Play Sessions ---


@router.post("/{game_id}/play", response_model=PlaySessionCreatedResponse, status_code=202)
async def start_play_session(
    game_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Start a play session for a game.

    Creates a sandbox container and returns a WebSocket URL for noVNC.
    Authentication optional (guests can play public games, rate limited).
    """
    game = await _get_game_or_404(game_id, db)

    if game.status != "ready":
        raise HTTPException(status_code=400, detail="Game is not ready to play.")

    # Find latest version
    result = await db.execute(
        select(GameVersion)
        .where(GameVersion.game_id == game.id)
        .order_by(GameVersion.version.desc())
        .limit(1)
    )
    version = result.scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=400, detail="No game version available.")

    # Get user_id if authenticated (optional for public games)
    user_id = None
    from app.auth.sessions import COOKIE_NAME, get_session
    session_id = request.cookies.get(COOKIE_NAME)
    if session_id:
        session_data = await get_session(session_id)
        if session_data:
            user_id = uuid.UUID(session_data["user_id"])

    # Enforce max concurrent sessions per user (2 max)
    MAX_CONCURRENT_SESSIONS = 2
    if user_id:
        active_result = await db.execute(
            select(func.count()).where(
                PlaySession.user_id == user_id,
                PlaySession.status.in_(["starting", "running"]),
            )
        )
        active_count = active_result.scalar() or 0
        if active_count >= MAX_CONCURRENT_SESSIONS:
            raise HTTPException(
                status_code=429,
                detail=f"Maximum {MAX_CONCURRENT_SESSIONS} concurrent play sessions. Stop an existing session first.",
            )
    else:
        # Guest play: rate limit by IP (3 sessions per hour)
        ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if not ip and request.client:
            ip = request.client.host
        allowed, remaining = await check_rate_limit(f"guest_play:{ip}", 3, 3600)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Guest play limit reached. Sign in for more play sessions.",
                headers={"Retry-After": str(remaining)},
            )

    ttl = settings.sandbox_session_ttl_seconds
    now = datetime.now(timezone.utc)

    # Create play session record
    play_session = PlaySession(
        game_version_id=version.id,
        user_id=user_id,
        status="starting",
        expires_at=now + timedelta(seconds=ttl),
    )
    db.add(play_session)
    await db.flush()

    # Enqueue sandbox start job
    queue = await get_queue()
    await queue.enqueue_job(
        "start_sandbox_task",
        str(play_session.id),
        _job_id=f"play:{play_session.id}",
    )

    # Increment play count
    await db.execute(
        update(Game).where(Game.id == game.id).values(play_count=Game.play_count + 1)
    )

    return PlaySessionCreatedResponse(
        session_id=str(play_session.id),
        status="starting",
        message="Play session starting. Connect via WebSocket when ready.",
    )


@router.get("/{game_id}/play/{session_id}", response_model=PlaySessionResponse)
async def get_play_session(
    game_id: str,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the status of a play session."""
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID.")

    result = await db.execute(
        select(PlaySession).where(PlaySession.id == sid)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Play session not found.")

    return PlaySessionResponse(
        id=str(session.id),
        game_version_id=str(session.game_version_id),
        status=session.status,
        ws_url=session.ws_url,
        sandbox_ref=session.sandbox_ref,
        created_at=session.created_at,
        expires_at=session.expires_at,
    )


@router.post("/{game_id}/play/{session_id}/stop", status_code=200)
async def stop_play_session(
    game_id: str,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Stop a play session and clean up the sandbox."""
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID.")

    result = await db.execute(
        select(PlaySession).where(PlaySession.id == sid)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Play session not found.")

    if session.sandbox_ref and session.status == "running":
        import asyncio
        from app.games.sandbox import stop_sandbox
        await asyncio.to_thread(stop_sandbox, session.sandbox_ref)

    session.status = "stopped"
    return {"message": "Session stopped."}
