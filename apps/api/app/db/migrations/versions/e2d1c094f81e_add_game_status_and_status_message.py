"""add game status and status_message

Revision ID: e2d1c094f81e
Revises: f87f692515ca
Create Date: 2026-03-16 12:12:36.994095

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e2d1c094f81e"
down_revision: Union[str, Sequence[str], None] = "f87f692515ca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "games",
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
    )
    op.add_column(
        "games",
        sa.Column("status_message", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("games", "status_message")
    op.drop_column("games", "status")
