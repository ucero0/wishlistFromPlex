"""add_blacklist_torrents_table

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-03-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f6a7b8c9d0e1'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'blacklist_torrents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guid_prowlarr', sa.String(), nullable=False),
        sa.Column('reason', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_blacklist_torrents_id', 'blacklist_torrents', ['id'], unique=False)
    op.create_index('idx_blacklist_torrents_guid_prowlarr', 'blacklist_torrents', ['guid_prowlarr'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_blacklist_torrents_guid_prowlarr', table_name='blacklist_torrents')
    op.drop_index('ix_blacklist_torrents_id', table_name='blacklist_torrents')
    op.drop_table('blacklist_torrents')
