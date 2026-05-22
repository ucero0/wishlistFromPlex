"""add plex_library_paths table

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-05-22 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plex_library_paths",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("section_id", sa.String(), nullable=False),
        sa.Column("section_title", sa.String(), nullable=False),
        sa.Column("media_type", sa.String(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "last_synced_at",
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
    )
    op.create_index(
        "ix_plex_library_paths_section_path",
        "plex_library_paths",
        ["section_id", "path"],
        unique=True,
    )
    op.create_index(
        "ix_plex_library_paths_media_type_active",
        "plex_library_paths",
        ["media_type", "is_active"],
    )


def downgrade() -> None:
    op.drop_index("ix_plex_library_paths_media_type_active", "plex_library_paths")
    op.drop_index("ix_plex_library_paths_section_path", "plex_library_paths")
    op.drop_table("plex_library_paths")
