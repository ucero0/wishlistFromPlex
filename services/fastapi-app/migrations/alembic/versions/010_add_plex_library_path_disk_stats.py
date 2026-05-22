"""add disk stats columns to plex_library_paths

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-05-22 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "d0e1f2a3b4c5"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("plex_library_paths", sa.Column("volume_root", sa.String(), nullable=True))
    op.add_column("plex_library_paths", sa.Column("total_bytes", sa.BigInteger(), nullable=True))
    op.add_column("plex_library_paths", sa.Column("used_bytes", sa.BigInteger(), nullable=True))
    op.add_column("plex_library_paths", sa.Column("free_bytes", sa.BigInteger(), nullable=True))
    op.add_column("plex_library_paths", sa.Column("used_percent", sa.Float(), nullable=True))
    op.add_column(
        "plex_library_paths",
        sa.Column("disk_stats_synced_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "plex_library_paths",
        sa.Column("disk_stats_error", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("plex_library_paths", "disk_stats_error")
    op.drop_column("plex_library_paths", "disk_stats_synced_at")
    op.drop_column("plex_library_paths", "used_percent")
    op.drop_column("plex_library_paths", "free_bytes")
    op.drop_column("plex_library_paths", "used_bytes")
    op.drop_column("plex_library_paths", "total_bytes")
    op.drop_column("plex_library_paths", "volume_root")
