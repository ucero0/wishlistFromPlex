"""Create torrent_items table for Deluge integration

Revision ID: 004_torrent_items
Revises: 003_remove_legacy_user_fields
Create Date: 2025-12-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_torrent_items'
down_revision = '003_remove_legacy_user_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create torrent status enum
    torrent_status = sa.Enum(
        'queued', 'downloading', 'seeding', 'paused', 'checking', 'error', 'completed', 'removed',
        name='torrentstatus'
    )
    torrent_status.create(op.get_bind(), checkfirst=True)
    
    # Create torrent_items table
    op.create_table(
        'torrent_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rating_key', sa.String(), nullable=False),
        sa.Column('torrent_hash', sa.String(40), nullable=False),
        sa.Column('magnet_link', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('queued', 'downloading', 'seeding', 'paused', 'checking', 'error', 'completed', 'removed', name='torrentstatus'), nullable=False, server_default='queued'),
        sa.Column('progress', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_size', sa.BigInteger(), nullable=True),
        sa.Column('downloaded', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('uploaded', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('download_speed', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('upload_speed', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('save_path', sa.String(), nullable=True),
        sa.Column('num_seeds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('num_peers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ratio', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('eta', sa.Integer(), nullable=False, server_default='-1'),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_torrent_items_rating_key', 'torrent_items', ['rating_key'])
    op.create_index('idx_torrent_items_hash', 'torrent_items', ['torrent_hash'], unique=True)
    op.create_index('idx_torrent_items_status', 'torrent_items', ['status'])
    op.create_index(op.f('ix_torrent_items_id'), 'torrent_items', ['id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_torrent_items_id'), table_name='torrent_items')
    op.drop_index('idx_torrent_items_status', table_name='torrent_items')
    op.drop_index('idx_torrent_items_hash', table_name='torrent_items')
    op.drop_index('idx_torrent_items_rating_key', table_name='torrent_items')
    op.drop_table('torrent_items')
    
    # Drop enum
    sa.Enum(name='torrentstatus').drop(op.get_bind(), checkfirst=True)

