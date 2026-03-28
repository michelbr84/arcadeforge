"""Sandbox lifecycle worker (arq).

Manages game play session containers:
spin up sandbox, update session with connection details, handle TTL.

Run with: arq workers.sandbox.worker.WorkerSettings
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps" / "api"))

from shared_settings import get_redis_settings

logger = logging.getLogger("arcadeforge.sandbox")


async def start_sandbox_task(ctx: dict, play_session_id: str) -> dict:
    """Start a sandbox container for a play session.

    1. Load play session from DB
    2. Find the game workspace path
    3. Start sandbox container via Docker
    4. Update play session with ws_url and sandbox_ref
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.config import settings
    from app.db.models import GameVersion, PlaySession
    from app.games.sandbox import allocate_port, start_sandbox, start_sandbox_dispatch

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as session:
            # Load play session
            result = await session.execute(
                select(PlaySession).where(PlaySession.id == play_session_id)
            )
            play_session = result.scalar_one_or_none()
            if play_session is None:
                logger.error(f"PlaySession {play_session_id} not found")
                return {"status": "error", "message": "Session not found"}

            # Load game version to find workspace
            ver_result = await session.execute(
                select(GameVersion).where(GameVersion.id == play_session.game_version_id)
            )
            version = ver_result.scalar_one_or_none()
            if version is None or not version.source_zip_path:
                play_session.status = "failed"
                await session.commit()
                return {"status": "error", "message": "No workspace found"}

            workspace_path = version.source_zip_path

            # Verify workspace exists
            if not Path(workspace_path).exists():
                play_session.status = "failed"
                await session.commit()
                logger.error(f"Workspace not found: {workspace_path}")
                return {"status": "error", "message": "Workspace directory missing"}

            # Get existing ports from active sessions
            active_result = await session.execute(
                select(PlaySession).where(PlaySession.status == "running")
            )
            active_sessions = active_result.scalars().all()
            existing_ports = set()
            for s in active_sessions:
                if s.ws_url:
                    try:
                        port = int(s.ws_url.split(":")[-1])
                        existing_ports.add(port)
                    except (ValueError, IndexError):
                        pass

            # Use the dispatcher which selects Docker or Fly based on config
            if settings.sandbox_driver == "fly":
                # Fly driver is fully async — no port allocation needed
                sandbox_info = await start_sandbox_dispatch(
                    session_id=play_session_id,
                    game_workspace_path=str(Path(workspace_path).resolve()),
                    port=0,  # not used by Fly driver
                )
            else:
                # Docker driver — allocate a local port
                port = allocate_port(existing_ports)
                sandbox_info = await asyncio.to_thread(
                    start_sandbox,
                    session_id=play_session_id,
                    game_workspace_path=str(Path(workspace_path).resolve()),
                    port=port,
                )

            # Update play session
            play_session.status = "running"
            play_session.ws_url = sandbox_info["ws_url"]
            play_session.sandbox_ref = sandbox_info["container_name"]
            await session.commit()

            logger.info(
                f"Play session {play_session_id} started: "
                f"ws_url={sandbox_info['ws_url']}, "
                f"container={sandbox_info['container_name']}"
            )

            return {
                "status": "running",
                "ws_url": sandbox_info["ws_url"],
                "container": sandbox_info["container_name"],
            }

    except Exception as e:
        logger.exception(f"Failed to start sandbox for {play_session_id}")
        try:
            async with session_factory() as session:
                result = await session.execute(
                    select(PlaySession).where(PlaySession.id == play_session_id)
                )
                play_session = result.scalar_one_or_none()
                if play_session:
                    play_session.status = "failed"
                    await session.commit()
        except Exception:
            pass
        return {"status": "error", "message": str(e)}
    finally:
        await engine.dispose()


async def cleanup_sandbox_task(ctx: dict, sandbox_ref: str) -> dict:
    """Clean up an expired or stopped sandbox container."""
    from app.games.sandbox import stop_sandbox_dispatch

    stopped = await stop_sandbox_dispatch(sandbox_ref)
    return {"sandbox_ref": sandbox_ref, "stopped": stopped}


class WorkerSettings:
    """arq worker settings."""

    functions = [start_sandbox_task, cleanup_sandbox_task]
    redis_settings = get_redis_settings()
