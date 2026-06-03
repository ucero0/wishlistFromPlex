"""Runtime operational settings (scheduler intervals, download buffers).

Revision ID: 0009_runtime_settings
Revises: 0008_torrent_health_config
Create Date: 2026-06-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0009_runtime_settings"
down_revision: Union[str, None] = "0008_torrent_health_config"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "runtime_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "watchlist_download_interval_minutes",
            sa.Integer(),
            nullable=False,
            server_default="60",
        ),
        sa.Column(
            "ingest_poll_interval_minutes", sa.Integer(), nullable=False, server_default="5"
        ),
        sa.Column(
            "deferred_download_process_interval_minutes",
            sa.Integer(),
            nullable=False,
            server_default="15",
        ),
        sa.Column(
            "plex_library_paths_sync_interval_minutes",
            sa.Integer(),
            nullable=False,
            server_default="360",
        ),
        sa.Column(
            "tv_watchlist_ahead_episodes", sa.Integer(), nullable=False, server_default="10"
        ),
        sa.Column(
            "download_min_free_buffer_gb",
            sa.Float(),
            nullable=False,
            server_default="10",
        ),
        sa.Column(
            "download_default_required_gb",
            sa.Float(),
            nullable=False,
            server_default="50",
        ),
        sa.Column(
            "plex_library_disk_stats_max_age_hours",
            sa.Integer(),
            nullable=False,
            server_default="6",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        sa.text(
            "INSERT INTO runtime_settings (id) VALUES (1) ON CONFLICT (id) DO NOTHING"
        )
    )


def downgrade() -> None:
    op.drop_table("runtime_settings")
