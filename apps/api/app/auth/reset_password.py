"""Password reset flow.

Implements secure, token-based password reset per OWASP guidelines:
- Generic responses (no email enumeration)
- Cryptographically random tokens (secrets.token_urlsafe)
- Token hashed at rest (SHA-256) — never stored in plaintext
- Short TTL (30 minutes)
- Single-use (deleted after use)
- All sessions invalidated after successful reset
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import redis.asyncio as aioredis

from app.auth.sessions import get_redis
from app.config import settings

TOKEN_TTL_MINUTES = 30
TOKEN_BYTES = 32


def _hash_token(token: str) -> str:
    """Hash a reset token for storage. Uses SHA-256."""
    return hashlib.sha256(token.encode()).hexdigest()


def _reset_key(token_hash: str) -> str:
    """Redis key for a password reset token."""
    return f"reset:{token_hash}"


async def create_reset_token(user_id: str, email: str) -> str:
    """Create a password reset token.

    Stores a hashed version in Redis with TTL.
    Returns the plaintext token (to be sent via email).
    """
    r = await get_redis()
    token = secrets.token_urlsafe(TOKEN_BYTES)
    token_hash = _hash_token(token)
    key = _reset_key(token_hash)

    await r.hset(
        key,
        mapping={
            "user_id": user_id,
            "email": email,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    await r.expire(key, TOKEN_TTL_MINUTES * 60)

    return token


async def verify_reset_token(token: str) -> dict | None:
    """Verify a password reset token.

    Returns the token data if valid, None if expired/invalid.
    Does NOT consume the token — call consume_reset_token after use.
    """
    r = await get_redis()
    token_hash = _hash_token(token)
    key = _reset_key(token_hash)

    data = await r.hgetall(key)
    if not data:
        return None

    return data


async def consume_reset_token(token: str) -> bool:
    """Consume (delete) a password reset token after use.

    Returns True if the token existed and was deleted.
    Single-use: token cannot be reused.
    """
    r = await get_redis()
    token_hash = _hash_token(token)
    key = _reset_key(token_hash)

    deleted = await r.delete(key)
    return deleted > 0


async def invalidate_all_sessions(user_id: str) -> int:
    """Invalidate all sessions for a user after password reset.

    Scans Redis for session keys belonging to this user.
    Returns number of sessions invalidated.
    """
    r = await get_redis()
    count = 0

    async for key in r.scan_iter("session:*"):
        data = await r.hgetall(key)
        if data and data.get("user_id") == user_id:
            await r.delete(key)
            count += 1

    return count
