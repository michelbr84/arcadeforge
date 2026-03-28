from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# asyncpg doesn't understand ?sslmode= query params — strip them and use connect_args instead
_db_url = settings.database_url
for _param in ("sslmode=disable", "sslmode=require", "sslmode=prefer"):
    _db_url = _db_url.replace(f"?{_param}", "?").replace(f"&{_param}", "")
_db_url = _db_url.rstrip("?").rstrip("&")

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
