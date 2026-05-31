"""Persist watchlist subscribers on download rows for multi-user removal.

Revision ID: 0007_watchlist_subscribers
Revises: 0006_episode_name
Create Date: 2026-05-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007_watchlist_subscribers"
down_revision: Union[str, None] = "0006_episode_name"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "active_downloads",
        sa.Column("watchlistSubscribers", sa.Text(), nullable=True),
    )
    op.add_column(
        "deferred_downloads",
        sa.Column("watchlistSubscribers", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("deferred_downloads", "watchlistSubscribers")
    op.drop_column("active_downloads", "watchlistSubscribers")
