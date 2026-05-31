"""Rename active_downloads watchlist columns to camelCase.

Revision ID: 0004_active_dl_watchlist_cols
Revises: 0003_watchlist_tracking
Create Date: 2026-05-31
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004_active_dl_watchlist_cols"
down_revision: Union[str, None] = "0003_watchlist_tracking"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "active_downloads",
        "watchlist_source",
        new_column_name="watchlistSource",
    )
    op.alter_column(
        "active_downloads",
        "tmdb_media_id",
        new_column_name="tmdbMediaId",
    )
    op.alter_column(
        "active_downloads",
        "tmdb_account_id",
        new_column_name="tmdbAccountId",
    )


def downgrade() -> None:
    op.alter_column(
        "active_downloads",
        "watchlistSource",
        new_column_name="watchlist_source",
    )
    op.alter_column(
        "active_downloads",
        "tmdbMediaId",
        new_column_name="tmdb_media_id",
    )
    op.alter_column(
        "active_downloads",
        "tmdbAccountId",
        new_column_name="tmdb_account_id",
    )
