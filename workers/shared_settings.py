"""Shared arq Redis settings for all workers.

Workers import this to connect to the same Redis instance as the API.
"""

import os

from arq.connections import RedisSettings


def get_redis_settings() -> RedisSettings:
    """Parse REDIS_URL env var into arq RedisSettings."""
    url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
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
