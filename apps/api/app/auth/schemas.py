"""Pydantic schemas for auth endpoints."""

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip().lower()
        if len(v) < 3 or len(v) > 30:
            raise ValueError("Username must be 3-30 characters")
        if not re.match(r"^[a-z0-9][a-z0-9_-]*[a-z0-9]$", v):
            raise ValueError(
                "Username must start and end with a letter or number, "
                "and contain only lowercase letters, numbers, hyphens, and underscores"
            )
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > 128:
            raise ValueError("Password must be at most 128 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    status: str
    created_at: datetime
    email_verified_at: datetime | None = None

    model_config = {"from_attributes": True}


class AuthMessageResponse(BaseModel):
    message: str
