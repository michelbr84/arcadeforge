"""TTL reaper for expired play sessions.

Runs periodically to:
1. Find play sessions past their expires_at
2. Stop the sandbox container
3. Mark session as "expired"

Can be run as:
- A standalone async loop (for development)
- An arq cron job (for production)
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.models import PlaySession
from app.games.sandbox import stop_sandbox

logger = logging.getLogger("arcadeforge.reaper")

# How often to check for expired sessions (seconds)
REAP_INTERVAL = 30


async def reap_expired_sessions(session_factory: async_sessionmaker) -> int:
    """Find and kill expired play sessions.

    Returns the number of sessions reaped.
    """
    reaped = 0
    now = datetime.now(timezone.utc)

    async with session_factory() as session:
        # Find expired running sessions
        result = await session.execute(
            select(PlaySession).where(
                PlaySession.status == "running",
                PlaySession.expires_at < now,
            )
        )
        expired_sessions = result.scalars().all()

        for play_session in expired_sessions:
            logger.info(
                f"Reaping expired session {play_session.id} "
                f"(expired at {play_session.expires_at})"
            )

            # Stop container
            if play_session.sandbox_ref:
                try:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None, stop_sandbox, play_session.sandbox_ref
                    )
                except Exception:
                    logger.exception(
                        f"Failed to stop sandbox {play_session.sandbox_ref}"
                    )

            # Mark as expired
            play_session.status = "expired"
            reaped += 1

        if reaped > 0:
            await session.commit()
            logger.info(f"Reaped {reaped} expired session(s)")

    return reaped


async def reap_stale_starting_sessions(session_factory: async_sessionmaker) -> int:
    """Clean up sessions stuck in 'starting' state for too long.

    If a session has been 'starting' for more than 2 minutes,
    it's likely the worker failed. Mark as failed.
    """
    from datetime import timedelta

    reaped = 0
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=2)

    async with session_factory() as session:
        result = await session.execute(
            select(PlaySession).where(
                PlaySession.status == "starting",
                PlaySession.created_at < cutoff,
            )
        )
        stale_sessions = result.scalars().all()

        for play_session in stale_sessions:
            logger.warning(f"Marking stale session {play_session.id} as failed")
            play_session.status = "failed"
            reaped += 1

        if reaped > 0:
            await session.commit()

    return reaped


async def reaper_loop():
    """Main reaper loop. Runs until cancelled.

    Use for standalone development or as a long-running background task.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    logger.info(f"TTL reaper started (interval: {REAP_INTERVAL}s)")

    try:
        while True:
            try:
                expired = await reap_expired_sessions(session_factory)
                stale = await reap_stale_starting_sessions(session_factory)
                if expired or stale:
                    logger.info(f"Reaper cycle: {expired} expired, {stale} stale")
            except Exception:
                logger.exception("Reaper cycle failed")

            await asyncio.sleep(REAP_INTERVAL)
    finally:
        await engine.dispose()
