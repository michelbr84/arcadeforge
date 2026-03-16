"""Auth dependencies for FastAPI route protection."""

import uuid

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.sessions import COOKIE_NAME, get_session
from app.db.models import User
from app.db.session import get_db


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency that returns the authenticated user.

    Raises 401 if not authenticated or session expired.
    Use as: user: User = Depends(get_current_user)
    """
    session_id = request.cookies.get(COOKIE_NAME)
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated.")

    session_data = await get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=401, detail="Session expired.")

    user_id = uuid.UUID(session_data["user_id"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=401, detail="User not found.")

    return user
