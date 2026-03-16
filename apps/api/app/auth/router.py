"""Auth API routes: register, login, logout, me."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.passwords import hash_password, needs_rehash, verify_password
from app.auth.rate_limit import check_rate_limit
from app.auth.schemas import (
    AuthMessageResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from app.auth.sessions import (
    COOKIE_NAME,
    COOKIE_PATH,
    COOKIE_SAMESITE,
    SESSION_TTL,
    create_session,
    delete_session,
    get_session,
    rotate_session,
)
from app.config import settings
from app.db.models import User
from app.db.session import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session_cookie(response: Response, session_id: str) -> None:
    """Set the session cookie on the response."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_id,
        max_age=int(SESSION_TTL.total_seconds()),
        path=COOKIE_PATH,
        secure=settings.app_env != "development",
        httponly=True,
        samesite=COOKIE_SAMESITE,
    )


def _clear_session_cookie(response: Response) -> None:
    """Clear the session cookie."""
    response.delete_cookie(
        key=COOKIE_NAME,
        path=COOKIE_PATH,
        secure=settings.app_env != "development",
        httponly=True,
        samesite=COOKIE_SAMESITE,
    )


def _client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    body: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account."""
    ip = _client_ip(request)

    # Rate limit: 3 registrations per IP per 10 minutes
    allowed, remaining = await check_rate_limit(f"register:{ip}", 3, 600)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many registration attempts. Try again later.",
        )

    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        # Generic error to avoid leaking whether email exists
        raise HTTPException(status_code=409, detail="Registration failed.")

    # Check if username already exists
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Registration failed.")

    # Create user
    user = User(
        email=body.email,
        username=body.username,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    await db.flush()

    # Create session
    user_agent = request.headers.get("user-agent", "")
    session_id = await create_session(user.id, ip, user_agent)
    _set_session_cookie(response, session_id)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        status=user.status,
        created_at=user.created_at,
        email_verified_at=user.email_verified_at,
    )


@router.post("/login", response_model=UserResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with email and password."""
    ip = _client_ip(request)

    # Rate limit: 5 login attempts per IP per minute
    allowed, remaining = await check_rate_limit(f"login:{ip}", 5, 60)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Try again later.",
        )

    # Generic error message — do NOT reveal whether email exists
    invalid_msg = "Invalid email or password."

    # Find user by email
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=401, detail=invalid_msg)

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail=invalid_msg)

    # Rehash if Argon2 parameters have changed
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(body.password)

    # Rotate session: invalidate any existing session, create new one
    user_agent = request.headers.get("user-agent", "")
    old_session_id = request.cookies.get(COOKIE_NAME)
    if old_session_id:
        session_id = await rotate_session(old_session_id, user.id, ip, user_agent)
    else:
        session_id = await create_session(user.id, ip, user_agent)

    _set_session_cookie(response, session_id)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        status=user.status,
        created_at=user.created_at,
        email_verified_at=user.email_verified_at,
    )


@router.post("/logout", response_model=AuthMessageResponse)
async def logout(request: Request, response: Response):
    """Log out and invalidate the current session."""
    session_id = request.cookies.get(COOKIE_NAME)
    if session_id:
        await delete_session(session_id)
    _clear_session_cookie(response)
    return AuthMessageResponse(message="Logged out successfully.")


@router.get("/me", response_model=UserResponse)
async def me(request: Request, db: AsyncSession = Depends(get_db)):
    """Get the current authenticated user."""
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

    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        status=user.status,
        created_at=user.created_at,
        email_verified_at=user.email_verified_at,
    )
