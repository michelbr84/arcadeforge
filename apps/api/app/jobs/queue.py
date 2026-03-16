"""arq job queue client for enqueuing tasks from the API."""

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.config import settings

_pool: ArqRedis | None = None


def get_redis_settings() -> RedisSettings:
    """Parse REDIS_URL into arq RedisSettings."""
    url = settings.redis_url
    # redis://localhost:6379/0
    parts = url.replace("redis://", "").split("/")
    host_port = parts[0]
    database = int(parts[1]) if len(parts) > 1 else 0

    if ":" in host_port:
        host, port_str = host_port.split(":")
        port = int(port_str)
    else:
        host = host_port
        port = 6379

    return RedisSettings(host=host, port=port, database=database)


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
