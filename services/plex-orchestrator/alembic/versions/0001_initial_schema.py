"""Initial schema (all application tables).

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "plex_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("plex_token", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_plex_users_id"), "plex_users", ["id"], unique=False)
    op.create_index(op.f("ix_plex_users_name"), "plex_users", ["name"], unique=False)

    op.create_table(
        "plex_library_paths",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("section_id", sa.String(), nullable=False),
        sa.Column("section_title", sa.String(), nullable=False),
        sa.Column("media_type", sa.String(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "last_synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("volume_root", sa.String(), nullable=True),
        sa.Column("total_bytes", sa.BigInteger(), nullable=True),
        sa.Column("used_bytes", sa.BigInteger(), nullable=True),
        sa.Column("free_bytes", sa.BigInteger(), nullable=True),
        sa.Column("used_percent", sa.Float(), nullable=True),
        sa.Column("disk_stats_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disk_stats_error", sa.String(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_plex_library_paths_id"), "plex_library_paths", ["id"], unique=False
    )

    op.create_table(
        "plex_server_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admin_token", sa.String(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "active_downloads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guidPlex", sa.String(), nullable=False),
        sa.Column("ratingKey", sa.String(), nullable=True),
        sa.Column("plexUserToken", sa.String(), nullable=True),
        sa.Column("guidProwlarr", sa.String(), nullable=False),
        sa.Column("uid", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("fileName", sa.String(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("season", sa.Integer(), nullable=True),
        sa.Column("episode", sa.Integer(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uid"),
    )
    op.create_index(op.f("ix_active_downloads_id"), "active_downloads", ["id"], unique=False)
    op.create_index(
        op.f("ix_active_downloads_guidPlex"), "active_downloads", ["guidPlex"], unique=False
    )
    op.create_index(
        op.f("ix_active_downloads_guidProwlarr"),
        "active_downloads",
        ["guidProwlarr"],
        unique=False,
    )
    op.create_index(op.f("ix_active_downloads_uid"), "active_downloads", ["uid"], unique=False)
    op.create_index("idx_active_downloads_guid_plex", "active_downloads", ["guidPlex"], unique=False)
    op.create_index(
        "idx_active_downloads_guid_prowlarr", "active_downloads", ["guidProwlarr"], unique=False
    )
    op.create_index("idx_active_downloads_uid", "active_downloads", ["uid"], unique=False)
    op.create_index("idx_active_downloads_type", "active_downloads", ["type"], unique=False)

    op.create_table(
        "deferred_downloads",
        sa.Column("id", sa.Integer(), nullable=False),
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
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("defer_reason", sa.String(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_deferred_downloads_id"), "deferred_downloads", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_deferred_downloads_guid_plex"),
        "deferred_downloads",
        ["guid_plex"],
        unique=False,
    )

    op.create_table(
        "blacklist_torrents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guid_prowlarr", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guid_prowlarr"),
    )
    op.create_index(
        op.f("ix_blacklist_torrents_id"), "blacklist_torrents", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_blacklist_torrents_guid_prowlarr"),
        "blacklist_torrents",
        ["guid_prowlarr"],
        unique=False,
    )
    op.create_index(
        "idx_blacklist_torrents_guid_prowlarr",
        "blacklist_torrents",
        ["guid_prowlarr"],
        unique=False,
    )

    op.create_table(
        "antivirus_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guidProwlarr", sa.String(), nullable=False),
        sa.Column("filePath", sa.String(), nullable=True),
        sa.Column("folderPathSrc", sa.String(), nullable=True),
        sa.Column("folderPathDst", sa.String(), nullable=True),
        sa.Column("plannedDestination", sa.String(), nullable=True),
        sa.Column("ingestError", sa.String(), nullable=True),
        sa.Column("Infected", sa.Boolean(), nullable=False),
        sa.Column(
            "scanDateTime",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_antivirus_items_id"), "antivirus_items", ["id"], unique=False)
    op.create_index(
        op.f("ix_antivirus_items_guidProwlarr"),
        "antivirus_items",
        ["guidProwlarr"],
        unique=False,
    )
    op.create_index(
        "idx_antivirus_items_guid_prowlarr", "antivirus_items", ["guidProwlarr"], unique=False
    )
    op.create_index(
        "idx_antivirus_items_infected", "antivirus_items", ["Infected"], unique=False
    )
    op.create_index(
        "idx_antivirus_items_scan_datetime", "antivirus_items", ["scanDateTime"], unique=False
    )


def downgrade() -> None:
    op.drop_table("antivirus_items")
    op.drop_table("blacklist_torrents")
    op.drop_table("deferred_downloads")
    op.drop_table("active_downloads")
    op.drop_table("plex_server_config")
    op.drop_table("plex_library_paths")
    op.drop_table("plex_users")
