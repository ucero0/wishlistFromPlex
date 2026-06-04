"""Simplify torrent health config: drop legacy day/hour timers, add active minutes.

Revision ID: 0010_simplify_torrent_health
Revises: 0009_runtime_settings
Create Date: 2026-06-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0010_simplify_torrent_health"
down_revision: Union[str, None] = "0009_runtime_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_LEGACY_COLUMNS = (
    "unfinishable_days",
    "no_complete_zero_hours",
    "stall_no_peers_hours",
    "strict_unfinishable_days",
    "strict_no_complete_zero_hours",
    "strict_stall_no_peers_hours",
)


def upgrade() -> None:
    op.add_column(
        "torrent_health_config",
        sa.Column(
            "unfinishable_active_minutes",
            sa.Integer(),
            nullable=False,
            server_default="20",
        ),
    )
    op.add_column(
        "torrent_health_config",
        sa.Column(
            "strict_unfinishable_active_minutes",
            sa.Integer(),
            nullable=False,
            server_default="20",
        ),
    )
    for column in _LEGACY_COLUMNS:
        op.drop_column("torrent_health_config", column)


def downgrade() -> None:
    op.add_column(
        "torrent_health_config",
        sa.Column("unfinishable_days", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "torrent_health_config",
        sa.Column(
            "no_complete_zero_hours", sa.Integer(), nullable=False, server_default="12"
        ),
    )
    op.add_column(
        "torrent_health_config",
        sa.Column(
            "stall_no_peers_hours", sa.Integer(), nullable=False, server_default="24"
        ),
    )
    op.add_column(
        "torrent_health_config",
        sa.Column(
            "strict_unfinishable_days", sa.Integer(), nullable=False, server_default="1"
        ),
    )
    op.add_column(
        "torrent_health_config",
        sa.Column(
            "strict_no_complete_zero_hours",
            sa.Integer(),
            nullable=False,
            server_default="6",
        ),
    )
    op.add_column(
        "torrent_health_config",
        sa.Column(
            "strict_stall_no_peers_hours",
            sa.Integer(),
            nullable=False,
            server_default="8",
        ),
    )
    op.drop_column("torrent_health_config", "strict_unfinishable_active_minutes")
    op.drop_column("torrent_health_config", "unfinishable_active_minutes")
