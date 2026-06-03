"""Torrent health policy singleton (runtime-tunable without restart).

Revision ID: 0008_torrent_health_config
Revises: 0007_watchlist_subscribers
Create Date: 2026-06-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008_torrent_health_config"
down_revision: Union[str, None] = "0007_watchlist_subscribers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "torrent_health_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("grace_hours", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("min_availability", sa.Float(), nullable=False, server_default="1"),
        sa.Column("unfinishable_days", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("no_complete_copy_days", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("no_complete_zero_hours", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("stall_days", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("stall_no_peers_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column(
            "skip_when_vpn_unhealthy",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "use_strict_when_vpn_healthy",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("strict_grace_hours", sa.Integer(), nullable=False, server_default="3"),
        sa.Column(
            "strict_unfinishable_days", sa.Integer(), nullable=False, server_default="1"
        ),
        sa.Column(
            "strict_no_complete_copy_days", sa.Integer(), nullable=False, server_default="1"
        ),
        sa.Column(
            "strict_no_complete_zero_hours", sa.Integer(), nullable=False, server_default="6"
        ),
        sa.Column("strict_stall_days", sa.Integer(), nullable=False, server_default="2"),
        sa.Column(
            "strict_stall_no_peers_hours", sa.Integer(), nullable=False, server_default="8"
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
            "INSERT INTO torrent_health_config (id) VALUES (1) ON CONFLICT (id) DO NOTHING"
        )
    )


def downgrade() -> None:
    op.drop_table("torrent_health_config")
