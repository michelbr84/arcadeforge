from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# asyncpg doesn't understand Postgres query params like sslmode, channel_binding —
# strip them all and use connect_args for SSL instead
from urllib.parse import urlparse, urlunparse

_parsed = urlparse(settings.database_url)
_db_url = urlunparse(_parsed._replace(query=""))  # remove all query params

_connect_args: dict = {}
if settings.database_ssl:
    _connect_args["ssl"] = True
else:
    # Explicitly disable SSL for Fly.io internal Postgres (asyncpg defaults to SSL)
    _connect_args["ssl"] = False

engine = create_async_engine(
    _db_url,
    echo=settings.app_env == "development",
    pool_pre_ping=True,
    connect_args=_connect_args,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
