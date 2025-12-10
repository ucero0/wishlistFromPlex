"""fix_wishlist_items_schema_mismatch

Revision ID: 118191698761
Revises: 006_torrent_search
Create Date: 2025-12-08 21:13:16.358834

Fixes schema mismatches in wishlist_items table:
- Renames uid to guid if uid exists and guid doesn't
- Removes legacy user_name and plex_token columns if they exist
- Adds missing columns from migration 002 if they don't exist
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '118191698761'
down_revision = '006_torrent_search'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column already exists in the table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(table_name, index_name):
    """Check if an index already exists."""
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade() -> None:
    # Rename uid to guid if uid exists and guid doesn't
    if column_exists('wishlist_items', 'uid') and not column_exists('wishlist_items', 'guid'):
        # Drop old indexes
        if index_exists('wishlist_items', 'idx_wishlist_items_uid'):
            op.drop_index('idx_wishlist_items_uid', table_name='wishlist_items')
        if index_exists('wishlist_items', 'ix_wishlist_items_uid'):
            op.drop_index('ix_wishlist_items_uid', table_name='wishlist_items')
        
        # Rename column
        op.alter_column('wishlist_items', 'uid', new_column_name='guid')
        
        # Create new indexes
        if not index_exists('wishlist_items', 'idx_wishlist_items_guid'):
            op.create_index('idx_wishlist_items_guid', 'wishlist_items', ['guid'], unique=True)
    
    # Remove legacy columns if they exist (migration 003 should have done this)
    if column_exists('wishlist_items', 'user_name'):
        op.drop_column('wishlist_items', 'user_name')
    if column_exists('wishlist_items', 'plex_token'):
        op.drop_column('wishlist_items', 'plex_token')
    
    # Add missing columns from migration 002 if they don't exist
    if not column_exists('wishlist_items', 'media_type'):
        # Create enum type first
        media_type_enum = sa.Enum('MOVIE', 'SHOW', 'SEASON', 'EPISODE', name='mediatype')
        media_type_enum.create(op.get_bind(), checkfirst=True)
        op.add_column('wishlist_items', sa.Column('media_type', media_type_enum, nullable=True))
    
    if not column_exists('wishlist_items', 'summary'):
        op.add_column('wishlist_items', sa.Column('summary', sa.Text(), nullable=True))
    
    if not column_exists('wishlist_items', 'thumb'):
        op.add_column('wishlist_items', sa.Column('thumb', sa.String(), nullable=True))
    
    if not column_exists('wishlist_items', 'art'):
        op.add_column('wishlist_items', sa.Column('art', sa.String(), nullable=True))
    
    if not column_exists('wishlist_items', 'content_rating'):
        op.add_column('wishlist_items', sa.Column('content_rating', sa.String(), nullable=True))
    
    if not column_exists('wishlist_items', 'studio'):
        op.add_column('wishlist_items', sa.Column('studio', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove columns added in this migration
    if column_exists('wishlist_items', 'studio'):
        op.drop_column('wishlist_items', 'studio')
    if column_exists('wishlist_items', 'content_rating'):
        op.drop_column('wishlist_items', 'content_rating')
    if column_exists('wishlist_items', 'art'):
        op.drop_column('wishlist_items', 'art')
    if column_exists('wishlist_items', 'thumb'):
        op.drop_column('wishlist_items', 'thumb')
    if column_exists('wishlist_items', 'summary'):
        op.drop_column('wishlist_items', 'summary')
    if column_exists('wishlist_items', 'media_type'):
        op.drop_column('wishlist_items', 'media_type')
    
    # Re-add legacy columns
    if not column_exists('wishlist_items', 'user_name'):
        op.add_column('wishlist_items', sa.Column('user_name', sa.String(), nullable=True))
    if not column_exists('wishlist_items', 'plex_token'):
        op.add_column('wishlist_items', sa.Column('plex_token', sa.String(), nullable=True))
    
    # Rename guid back to uid
    if column_exists('wishlist_items', 'guid') and not column_exists('wishlist_items', 'uid'):
        if index_exists('wishlist_items', 'idx_wishlist_items_guid'):
            op.drop_index('idx_wishlist_items_guid', table_name='wishlist_items')
        op.alter_column('wishlist_items', 'guid', new_column_name='uid')
        if not index_exists('wishlist_items', 'idx_wishlist_items_uid'):
            op.create_index('idx_wishlist_items_uid', 'wishlist_items', ['uid'], unique=True)



