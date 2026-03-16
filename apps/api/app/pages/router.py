"""Public user profile routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import UserResponse
from app.db.models import User
from app.db.session import get_db

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/{username}", response_model=UserResponse)
async def get_user_profile(
    username: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a user's public profile by username."""
    result = await db.execute(
        select(User).where(User.username == username.lower())
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        status=user.status,
        created_at=user.created_at,
        email_verified_at=user.email_verified_at,
    )
