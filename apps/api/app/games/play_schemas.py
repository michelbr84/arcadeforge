"""Pydantic schemas for play session endpoints."""

from datetime import datetime

from pydantic import BaseModel


class PlaySessionResponse(BaseModel):
    id: str
    game_version_id: str
    status: str
    ws_url: str | None = None
    sandbox_ref: str | None = None
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


class PlaySessionCreatedResponse(BaseModel):
    session_id: str
    status: str
    message: str
    ws_url: str | None = None
