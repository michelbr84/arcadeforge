"""Database models for ArcadeForge.

Tables: users, sessions, user_pages, games, game_versions,
        validation_runs, play_sessions.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(back_populates="user")
    games: Mapped[list["Game"]] = relationship(back_populates="owner")
    pages: Mapped[list["UserPage"]] = relationship(back_populates="user")


class Session(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions")


class UserPage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_pages"
    __table_args__ = (UniqueConstraint("user_id", "slug"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), default="private", nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="pages")


class Game(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "games"

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    genre: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    pitch: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), default="private", nullable=False)
    play_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="games")
    versions: Mapped[list["GameVersion"]] = relationship(back_populates="game")


class GameVersion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "game_versions"
    __table_args__ = (UniqueConstraint("game_id", "version"),)

    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    blueprint_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    source_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_zip_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    game: Mapped["Game"] = relationship(back_populates="versions")
    validation_runs: Mapped[list["ValidationRun"]] = relationship(
        back_populates="game_version"
    )


class ValidationRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "validation_runs"

    game_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("game_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    report_json_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    report_md_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    screenshot_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    scan_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    game_version: Mapped["GameVersion"] = relationship(
        back_populates="validation_runs"
    )


class PlaySession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "play_sessions"

    game_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("game_versions.id"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,  # nullable for guest play
    )
    status: Mapped[str] = mapped_column(String(20), default="starting", nullable=False)
    sandbox_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ws_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
