"""Add LLM settings to users and change game visibility default.

Revision ID: c3a7f8b2d1e4
Revises: e2d1c094f81e
Create Date: 2026-03-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c3a7f8b2d1e4"
down_revision: str | None = "e2d1c094f81e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("llm_provider", sa.String(20), nullable=True))
    op.add_column("users", sa.Column("llm_api_key_encrypted", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("llm_model", sa.String(100), nullable=True))
    op.alter_column("games", "visibility", server_default="public")


def downgrade() -> None:
    op.alter_column("games", "visibility", server_default="private")
    op.drop_column("users", "llm_model")
    op.drop_column("users", "llm_api_key_encrypted")
    op.drop_column("users", "llm_provider")
