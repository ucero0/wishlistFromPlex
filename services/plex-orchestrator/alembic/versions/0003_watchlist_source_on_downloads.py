"""Add watchlist source fields to active and deferred downloads.

Revision ID: 0003_watchlist_tracking
Revises: 0002_tmdb_users
Create Date: 2026-05-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_watchlist_tracking"
down_revision: Union[str, None] = "0002_tmdb_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "active_downloads",
        sa.Column("watchlist_source", sa.String(), nullable=True),
    )
    op.add_column(
        "active_downloads",
        sa.Column("tmdb_media_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "active_downloads",
        sa.Column("tmdb_account_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "deferred_downloads",
        sa.Column("watchlist_source", sa.String(), nullable=True),
    )
    op.add_column(
        "deferred_downloads",
        sa.Column("tmdb_media_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "deferred_downloads",
        sa.Column("tmdb_account_id", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("deferred_downloads", "tmdb_account_id")
    op.drop_column("deferred_downloads", "tmdb_media_id")
    op.drop_column("deferred_downloads", "watchlist_source")
    op.drop_column("active_downloads", "tmdb_account_id")
    op.drop_column("active_downloads", "tmdb_media_id")
    op.drop_column("active_downloads", "watchlist_source")
