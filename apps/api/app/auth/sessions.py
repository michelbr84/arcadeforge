"""Server-side session management with Redis.

Sessions are stored in Redis with an opaque session ID.
The browser receives only the session ID in an HttpOnly cookie.
Session IDs are rotated on login to prevent session fixation.
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone

import redis.asyncio as aioredis

from app.config import settings

# Session ID: 32 bytes = 256 bits of entropy (OWASP recommends >= 128 bits)
SESSION_ID_BYTES = 32
SESSION_TTL = timedelta(hours=24)
SESSION_IDLE_TTL = timedelta(hours=2)

# Cookie configuration
# __Host- prefix requires Secure (HTTPS) — browsers silently drop it on http://
# Use plain name in development, __Host- prefix in production
COOKIE_NAME = "__Host-af_session" if settings.app_env == "production" else "af_session"
COOKIE_PATH = "/"
COOKIE_SAMESITE = "lax"

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get or create the Redis connection for sessions."""
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    return _redis


async def close_redis() -> None:
    """Close the Redis connection."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def _session_key(session_id: str) -> str:
    """Redis key for a session."""
    return f"session:{session_id}"


def generate_session_id() -> str:
    """Generate a cryptographically secure session ID."""
    return secrets.token_urlsafe(SESSION_ID_BYTES)


async def create_session(user_id: uuid.UUID, ip: str, user_agent: str) -> str:
    """Create a new server-side session in Redis.

    Returns the opaque session ID to be stored in the cookie.
    """
    r = await get_redis()
    session_id = generate_session_id()
    now = datetime.now(timezone.utc)

    session_data = {
        "user_id": str(user_id),
        "ip": ip,
        "user_agent": user_agent,
        "created_at": now.isoformat(),
        "last_active": now.isoformat(),
    }

    key = _session_key(session_id)
    await r.hset(key, mapping=session_data)
    await r.expire(key, int(SESSION_TTL.total_seconds()))

    return session_id


async def get_session(session_id: str) -> dict | None:
    """Retrieve a session from Redis.

    Returns None if the session doesn't exist or has expired.
    Also enforces idle timeout.
    """
    r = await get_redis()
    key = _session_key(session_id)
    data = await r.hgetall(key)

    if not data:
        return None

    # Check idle timeout
    last_active = datetime.fromisoformat(data["last_active"])
    if datetime.now(timezone.utc) - last_active > SESSION_IDLE_TTL:
        await r.delete(key)
        return None

    # Update last_active (touch)
    await r.hset(key, "last_active", datetime.now(timezone.utc).isoformat())

    return data


async def delete_session(session_id: str) -> None:
    """Delete a session from Redis (logout)."""
    r = await get_redis()
    await r.delete(_session_key(session_id))


async def rotate_session(
    old_session_id: str, user_id: uuid.UUID, ip: str, user_agent: str
) -> str:
    """Rotate session ID: delete old session, create new one.

    Prevents session fixation attacks per OWASP guidelines.
    Must be called after successful authentication.
    """
    await delete_session(old_session_id)
    return await create_session(user_id, ip, user_agent)
