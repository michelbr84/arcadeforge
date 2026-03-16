"""Pydantic schemas for game endpoints."""

from datetime import datetime

from pydantic import BaseModel, field_validator

from app.games.genres import GENRE_MAP


class CreateGameRequest(BaseModel):
    genre: str
    title: str
    prompt: str
    difficulty: str = "medium"

    @field_validator("genre")
    @classmethod
    def validate_genre(cls, v: str) -> str:
        if v not in GENRE_MAP:
            raise ValueError(f"Unknown genre: {v}. Available: {list(GENRE_MAP.keys())}")
        return v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1 or len(v) > 200:
            raise ValueError("Title must be 1-200 characters")
        return v

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Prompt must be at least 10 characters")
        if len(v) > 2000:
            raise ValueError("Prompt must be at most 2000 characters")
        return v


class GameResponse(BaseModel):
    id: str
    owner_user_id: str
    genre: str
    title: str
    pitch: str | None = None
    prompt: str | None = None
    visibility: str
    play_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GameCreatedResponse(BaseModel):
    """Response for POST /api/games (202 Accepted)."""
    game_id: str
    status: str
    message: str


class GameVersionResponse(BaseModel):
    id: str
    game_id: str
    version: int
    blueprint_json: dict | None = None
    source_code: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class GameListResponse(BaseModel):
    games: list[GameResponse]
    total: int
