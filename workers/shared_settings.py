"""Shared arq Redis settings for all workers.

Workers import this to connect to the same Redis instance as the API.
"""

import os
from urllib.parse import urlparse

from arq.connections import RedisSettings


def get_redis_settings() -> RedisSettings:
    """Parse REDIS_URL env var into arq RedisSettings.

    Supports both plain ``redis://`` and TLS ``rediss://`` URLs,
    including password-authenticated URLs such as those used by Upstash:
        rediss://default:PASSWORD@host:port/0
    """
    url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
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
