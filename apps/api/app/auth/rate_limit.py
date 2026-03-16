"""Redis-backed rate limiting for auth endpoints.

Uses a sliding window counter pattern.
"""

import redis.asyncio as aioredis

from app.auth.sessions import get_redis


async def check_rate_limit(
    key: str,
    max_attempts: int,
    window_seconds: int,
) -> tuple[bool, int]:
    """Check if an action is rate limited.

    Args:
        key: Unique key for the rate limit (e.g., "login:192.168.1.1")
        max_attempts: Maximum allowed attempts in the window
        window_seconds: Time window in seconds

    Returns:
        Tuple of (allowed: bool, remaining: int)
    """
    r = await get_redis()
    rate_key = f"ratelimit:{key}"

    current = await r.get(rate_key)
    count = int(current) if current else 0

    if count >= max_attempts:
        ttl = await r.ttl(rate_key)
        return False, ttl

    pipe = r.pipeline()
    pipe.incr(rate_key)
    pipe.expire(rate_key, window_seconds, nx=True)
    await pipe.execute()

    return True, max_attempts - count - 1
