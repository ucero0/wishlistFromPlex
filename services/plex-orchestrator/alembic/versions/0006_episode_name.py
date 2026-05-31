"""Add episodeName to active_downloads for Plex TV file naming.

Revision ID: 0006_episode_name
Revises: 0005_plex_guid_on_downloads
Create Date: 2026-05-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_episode_name"
down_revision: Union[str, None] = "0005_plex_guid_on_downloads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "active_downloads",
        sa.Column("episodeName", sa.String(), nullable=True),
    )
    op.add_column(
        "deferred_downloads",
        sa.Column("season", sa.Integer(), nullable=True),
    )
    op.add_column(
        "deferred_downloads",
        sa.Column("episode", sa.Integer(), nullable=True),
    )
    op.add_column(
        "deferred_downloads",
        sa.Column("episodeName", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("deferred_downloads", "episodeName")
    op.drop_column("deferred_downloads", "episode")
    op.drop_column("deferred_downloads", "season")
    op.drop_column("active_downloads", "episodeName")
