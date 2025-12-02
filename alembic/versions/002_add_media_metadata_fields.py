"""Add media metadata fields to wishlist_items

Revision ID: 002_media_metadata
Revises: 001_add_user_fields
Create Date: 2025-12-02

Changes:
- Rename uid to guid (clearer naming - this is the Plex GUID used for account operations)
- Add media_type (movie, show, season, episode)
- Add summary (plot description)
- Add thumb (thumbnail URL)
- Add art (background art URL)
- Add content_rating (PG-13, R, TV-MA, etc.)
- Add studio (production studio)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '002_media_metadata'
down_revision = '001_add_user_fields'
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
        op.alter_column('wishlist_items', 'uid', new_column_name='guid')
        
        # Update indexes for the rename
        if index_exists('wishlist_items', 'idx_wishlist_items_uid'):
            op.drop_index('idx_wishlist_items_uid', table_name='wishlist_items')
        if index_exists('wishlist_items', 'ix_wishlist_items_uid'):
            op.drop_index('ix_wishlist_items_uid', table_name='wishlist_items')
        
        # Create new indexes
        if not index_exists('wishlist_items', 'idx_wishlist_items_guid'):
            op.create_index('idx_wishlist_items_guid', 'wishlist_items', ['guid'], unique=True)
    
    # Add media_type column (enum)
    if not column_exists('wishlist_items', 'media_type'):
        # Create enum type first
        media_type_enum = sa.Enum('MOVIE', 'SHOW', 'SEASON', 'EPISODE', name='mediatype')
        media_type_enum.create(op.get_bind(), checkfirst=True)
        op.add_column('wishlist_items', sa.Column('media_type', media_type_enum, nullable=True))
    
    # Add summary column
    if not column_exists('wishlist_items', 'summary'):
        op.add_column('wishlist_items', sa.Column('summary', sa.Text(), nullable=True))
    
    # Add thumb column
    if not column_exists('wishlist_items', 'thumb'):
        op.add_column('wishlist_items', sa.Column('thumb', sa.String(), nullable=True))
    
    # Add art column
    if not column_exists('wishlist_items', 'art'):
        op.add_column('wishlist_items', sa.Column('art', sa.String(), nullable=True))
    
    # Add content_rating column
    if not column_exists('wishlist_items', 'content_rating'):
        op.add_column('wishlist_items', sa.Column('content_rating', sa.String(), nullable=True))
    
    # Add studio column
    if not column_exists('wishlist_items', 'studio'):
        op.add_column('wishlist_items', sa.Column('studio', sa.String(), nullable=True))
    
    # Add index on rating_key if it doesn't exist
    if not index_exists('wishlist_items', 'ix_wishlist_items_rating_key'):
        op.create_index('ix_wishlist_items_rating_key', 'wishlist_items', ['rating_key'])


def downgrade() -> None:
    # Remove new columns
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
        # Drop enum type
        op.execute("DROP TYPE IF EXISTS mediatype")
    
    # Rename guid back to uid
    if column_exists('wishlist_items', 'guid') and not column_exists('wishlist_items', 'uid'):
        if index_exists('wishlist_items', 'idx_wishlist_items_guid'):
            op.drop_index('idx_wishlist_items_guid', table_name='wishlist_items')
        op.alter_column('wishlist_items', 'guid', new_column_name='uid')
        op.create_index('idx_wishlist_items_uid', 'wishlist_items', ['uid'], unique=True)

