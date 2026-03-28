"""arq job queue client for enqueuing tasks from the API."""

from urllib.parse import urlparse

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.config import settings

_pool: ArqRedis | None = None


def get_redis_settings() -> RedisSettings:
    """Parse REDIS_URL into arq RedisSettings.

    Supports both plain ``redis://`` and TLS ``rediss://`` URLs,
    including password-authenticated URLs such as those used by Upstash:
        rediss://default:PASSWORD@host:port/0
    """
    url = settings.redis_url
    parsed = urlparse(url)

    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
    password = parsed.password or None
    database = int(parsed.path.lstrip("/") or 0)
    ssl = parsed.scheme == "rediss"

    return RedisSettings(
        host=host,
        port=port,
        password=password,
        database=database,
        ssl=ssl,
    )


async def get_queue() -> ArqRedis:
    """Get or create the arq Redis connection pool."""
    global _pool
    if _pool is None:
        _pool = await create_pool(get_redis_settings())
    return _pool


async def close_queue() -> None:
    """Close the arq Redis connection pool."""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None
