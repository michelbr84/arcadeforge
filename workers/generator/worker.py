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

    1. Load game row from DB
    2. Mark status = 'generating'
    3. Run generate_game() via asyncio.to_thread() (blocking I/O)
    4. Save files to workspace atomically
    5. Create game_version v0
    6. Mark status = 'ready' or 'failed'
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.config import settings
    from app.db.models import Game, GameVersion
    from app.games.generator import generate_game, save_to_workspace

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as session:
            # Load game
            result = await session.execute(select(Game).where(Game.id == game_id))
            game = result.scalar_one_or_none()

            if game is None:
                logger.error(f"Game {game_id} not found")
                return {"game_id": game_id, "status": "error", "message": "Game not found"}

            # Mark generating
            game.status = "generating"
            await session.commit()

            logger.info(f"Generating game {game_id}: {game.title} ({game.genre})")

            # Generate code (blocking — run in thread)
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

            # Create version v0 with explicit UUID
            import uuid as uuid_mod

            version_id = uuid_mod.uuid4()
            version = GameVersion(
                id=version_id,
                game_id=game.id,
                version=0,
                blueprint_json=gen_result.metadata,
                source_code=gen_result.files.get("main.py", ""),
                source_zip_path=workspace_path,
            )
            session.add(version)

            # Mark ready
            game.status = "ready"
            game.status_message = gen_result.summary
            await session.commit()

            logger.info(f"Game {game_id} generated successfully → {workspace_path}")
            return {"game_id": game_id, "status": "ready", "workspace": workspace_path}

    except Exception as e:
        logger.exception(f"Failed to generate game {game_id}")

        # Mark failed
        try:
            async with session_factory() as session:
                result = await session.execute(select(Game).where(Game.id == game_id))
                game = result.scalar_one_or_none()
                if game:
                    game.status = "failed"
                    game.status_message = str(e)[:500]
                    await session.commit()
        except Exception:
            logger.exception("Failed to mark game as failed")

        return {"game_id": game_id, "status": "failed", "message": str(e)}

    finally:
        await engine.dispose()


class WorkerSettings:
    """arq worker settings."""

    functions = [generate_game_task]
    redis_settings = get_redis_settings()
