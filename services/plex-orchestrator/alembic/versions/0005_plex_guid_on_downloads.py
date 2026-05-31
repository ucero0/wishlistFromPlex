"""Add plexGuid column for resolved Plex library identity on downloads.

Revision ID: 0005_plex_guid_on_downloads
Revises: 0004_active_dl_watchlist_cols
Create Date: 2026-05-31

"""
from alembic import op
import sqlalchemy as sa

revision = "0005_plex_guid_on_downloads"
down_revision = "0004_active_dl_watchlist_cols"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "active_downloads",
        sa.Column("plexGuid", sa.String(), nullable=True),
    )
    op.create_index(
        "idx_active_downloads_plex_guid",
        "active_downloads",
        ["plexGuid"],
        unique=False,
    )
    op.add_column(
        "deferred_downloads",
        sa.Column("plex_guid", sa.String(), nullable=True),
    )
    op.create_index(
        "idx_deferred_downloads_plex_guid",
        "deferred_downloads",
        ["plex_guid"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_deferred_downloads_plex_guid", table_name="deferred_downloads")
    op.drop_column("deferred_downloads", "plex_guid")
    op.drop_index("idx_active_downloads_plex_guid", table_name="active_downloads")
    op.drop_column("active_downloads", "plexGuid")
