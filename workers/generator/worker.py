"""Game generation worker (arq).

Picks generation jobs from Redis queue, generates game code
via template engine, saves files to workspace, and creates
version v0 in the database.

Run with: arq workers.generator.worker.WorkerSettings
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add workers/ and apps/api/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps" / "api"))

from shared_settings import get_redis_settings

logger = logging.getLogger("arcadeforge.generator")


async def generate_game_task(ctx: dict, game_id: str) -> dict:
    """Generate a game from its DB record.

    1. Load game + owner from DB
    2. If owner has LLM configured, generate via LLM
    3. Otherwise fall back to template
    4. Save files to workspace
    5. Create GameVersion v0
    6. Mark game ready + public
    """
    import uuid as uuid_mod

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.config import settings
    from app.db.models import Game, GameVersion, User
    from app.games.generator import GenerationResult, generate_game, generate_game_with_llm, save_to_workspace

    # Strip sslmode from URL for asyncpg
    db_url = settings.database_url
    for param in ("sslmode=disable", "sslmode=require", "sslmode=prefer"):
        db_url = db_url.replace(f"?{param}", "?").replace(f"&{param}", "")
    db_url = db_url.rstrip("?").rstrip("&")

    connect_args = {}
    if settings.database_ssl:
        connect_args["ssl"] = True
    else:
        connect_args["ssl"] = False

    engine = create_async_engine(db_url, connect_args=connect_args)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as session:
            # Load game
            result = await session.execute(select(Game).where(Game.id == game_id))
            game = result.scalar_one_or_none()
            if game is None:
                logger.error(f"Game {game_id} not found")
                return {"game_id": game_id, "status": "error", "message": "Game not found"}

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
                    logger.warning(
                        f"LLM generation failed for {game_id}, falling back to template: {e}"
                    )

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
                id=uuid_mod.uuid4(),
                game_id=game.id,
                version=0,
                blueprint_json=gen_result.metadata,
                source_code=gen_result.files.get("main.py", ""),
                source_zip_path=workspace_path,
            )
            session.add(version)

            # Mark ready and auto-publish
            game.status = "ready"
            game.visibility = "public"
            game.status_message = gen_result.summary
            await session.commit()

            logger.info(f"Game {game_id} ready → {workspace_path}")
            return {"game_id": game_id, "status": "ready", "workspace": workspace_path}

    except Exception as exc:
        logger.exception(f"Game generation failed for {game_id}")
        try:
            async with session_factory() as session:
                result = await session.execute(select(Game).where(Game.id == game_id))
                game = result.scalar_one_or_none()
                if game:
                    game.status = "failed"
                    game.status_message = str(exc)[:500]
                    await session.commit()
        except Exception:
            logger.exception("Failed to mark game as failed")
        return {"game_id": game_id, "status": "failed", "error": str(exc)}
    finally:
        await engine.dispose()


class WorkerSettings:
    """arq worker settings."""

    functions = [generate_game_task]
    redis_settings = get_redis_settings()
