"""add_blacklist_torrents_name_year_type

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-03-07 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7b8c9d0e1f2'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('blacklist_torrents', sa.Column('name', sa.String(), nullable=True))
    op.add_column('blacklist_torrents', sa.Column('year', sa.Integer(), nullable=True))
    op.add_column('blacklist_torrents', sa.Column('type', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('blacklist_torrents', 'type')
    op.drop_column('blacklist_torrents', 'year')
    op.drop_column('blacklist_torrents', 'name')
