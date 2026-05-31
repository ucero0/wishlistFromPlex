"""Add TMDB users table for watchlist automation.

Revision ID: 0002_tmdb_users
Revises: 0001_initial_schema
Create Date: 2026-05-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_tmdb_users"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tmdb_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("access_token", sa.String(), nullable=False),
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
    op.create_index(op.f("ix_tmdb_users_id"), "tmdb_users", ["id"], unique=False)
    op.create_index(op.f("ix_tmdb_users_name"), "tmdb_users", ["name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tmdb_users_name"), table_name="tmdb_users")
    op.drop_index(op.f("ix_tmdb_users_id"), table_name="tmdb_users")
    op.drop_table("tmdb_users")
