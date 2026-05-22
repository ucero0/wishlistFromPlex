"""add deferred_torrent_downloads queue table

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-05-22 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "e1f2a3b4c5d6"
down_revision = "d0e1f2a3b4c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deferred_torrent_downloads",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guid_plex", sa.String(), nullable=False),
        sa.Column("rating_key", sa.String(), nullable=True),
        sa.Column("plex_user_token", sa.String(), nullable=True),
        sa.Column("guid_prowlarr", sa.String(), nullable=False),
        sa.Column("indexer_id", sa.Integer(), nullable=False),
        sa.Column("torrent_title", sa.String(), nullable=False),
        sa.Column("media_title", sa.String(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("media_type", sa.String(), nullable=False),
        sa.Column("search_query", sa.String(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("magnet_url", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("defer_reason", sa.String(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_deferred_torrent_downloads_guid_plex",
        "deferred_torrent_downloads",
        ["guid_plex"],
    )
    op.create_index(
        "ix_deferred_torrent_downloads_status_created",
        "deferred_torrent_downloads",
        ["status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_deferred_torrent_downloads_status_created", "deferred_torrent_downloads")
    op.drop_index("ix_deferred_torrent_downloads_guid_plex", "deferred_torrent_downloads")
    op.drop_table("deferred_torrent_downloads")
