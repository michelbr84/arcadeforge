"""Test configuration and fixtures for ArcadeForge API tests."""

from collections.abc import AsyncGenerator

import pytest_asyncio
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth import sessions as sessions_module
from app.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app

# Use a separate test database so tests don't destroy dev data.
# Prefer TEST_DATABASE_URL if set (CI workflows set it explicitly); otherwise
# derive from DATABASE_URL by appending "_test" to the database name. The old
# str.replace() approach was non-idempotent ("arcadeforge_test" -> "arcadeforge_test_test").
import os
from urllib.parse import urlparse, urlunparse


def _derive_test_db_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    path = parsed.path or "/"
    if not path.endswith("_test"):
        path = path + "_test"
    return urlunparse(parsed._replace(path=path))


TEST_DB_URL = os.environ.get("TEST_DATABASE_URL") or _derive_test_db_url(settings.database_url)


@pytest_asyncio.fixture(autouse=True)
async def reset_redis():
    """Reset the Redis session module's connection for each test.

    This prevents stale connections across different event loops.
    Also flushes test keys after each test.
    """
    # Force a fresh connection for this test's event loop
    sessions_module._redis = None

    # Flush at setup to ensure clean state
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    await r.flushdb()
    await r.aclose()

    yield

    # Cleanup: close and reset
    if sessions_module._redis is not None:
        # Flush session and rate limit keys
        try:
            await sessions_module._redis.flushdb()
            await sessions_module._redis.aclose()
        except Exception:
            pass
    sessions_module._redis = None


@pytest_asyncio.fixture
async def engine():
    """Create a fresh test database schema for each test."""
    test_engine = create_async_engine(TEST_DB_URL, echo=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for tests."""
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(engine) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP test client with its own DB session per request."""
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
