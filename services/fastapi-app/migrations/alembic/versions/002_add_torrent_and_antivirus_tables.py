"""add_torrent_and_antivirus_tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-01-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create torrent_items table
    op.create_table('torrent_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('guidPlex', sa.String(), nullable=False),
    sa.Column('guidProwlarr', sa.String(), nullable=False),
    sa.Column('uid', sa.String(length=40), nullable=False, unique=True),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('season', sa.Integer(), nullable=True),
    sa.Column('episode', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_torrent_items_id', 'torrent_items', ['id'], unique=False)
    op.create_index('idx_torrent_items_guid_plex', 'torrent_items', ['guidPlex'], unique=False)
    op.create_index('idx_torrent_items_guid_prowlarr', 'torrent_items', ['guidProwlarr'], unique=False)
    op.create_index('idx_torrent_items_uid', 'torrent_items', ['uid'], unique=True)
    op.create_index('idx_torrent_items_type', 'torrent_items', ['type'], unique=False)
    
    # Create antivirus_items table
    op.create_table('antivirus_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('guidProwlarr', sa.String(), nullable=False),
    sa.Column('filePath', sa.String(), nullable=True),
    sa.Column('folderPathSrc', sa.String(), nullable=True),
    sa.Column('folderPathDst', sa.String(), nullable=True),
    sa.Column('Infected', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('scanDateTime', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_antivirus_items_id', 'antivirus_items', ['id'], unique=False)
    op.create_index('idx_antivirus_items_guid_prowlarr', 'antivirus_items', ['guidProwlarr'], unique=False)
    op.create_index('idx_antivirus_items_infected', 'antivirus_items', ['Infected'], unique=False)
    op.create_index('idx_antivirus_items_scan_datetime', 'antivirus_items', ['scanDateTime'], unique=False)


def downgrade() -> None:
    # Drop antivirus_items table and indexes
    op.drop_index('idx_antivirus_items_scan_datetime', table_name='antivirus_items')
    op.drop_index('idx_antivirus_items_infected', table_name='antivirus_items')
    op.drop_index('idx_antivirus_items_guid_prowlarr', table_name='antivirus_items')
    op.drop_index('ix_antivirus_items_id', table_name='antivirus_items')
    op.drop_table('antivirus_items')
    
    # Drop torrent_items table and indexes
    op.drop_index('idx_torrent_items_type', table_name='torrent_items')
    op.drop_index('idx_torrent_items_uid', table_name='torrent_items')
    op.drop_index('idx_torrent_items_guid_prowlarr', table_name='torrent_items')
    op.drop_index('idx_torrent_items_guid_plex', table_name='torrent_items')
    op.drop_index('ix_torrent_items_id', table_name='torrent_items')
    op.drop_table('torrent_items')

