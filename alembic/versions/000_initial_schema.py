"""Initial schema - create all tables

Revision ID: 000_initial
Revises: 
Create Date: 2025-11-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '000_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create mediatype enum
    media_type_enum = sa.Enum('MOVIE', 'SHOW', 'SEASON', 'EPISODE', name='mediatype')
    media_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create plex_users table
    op.create_table(
        'plex_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('plex_token', sa.String(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_plex_users_id', 'plex_users', ['id'])
    op.create_index('ix_plex_users_name', 'plex_users', ['name'])

    # Create wishlist_items table with all fields
    op.create_table(
        'wishlist_items',
        sa.Column('id', sa.Integer(), nullable=False),
        # Plex Identifiers
        sa.Column('guid', sa.String(), nullable=False),  # Plex GUID for account-level operations
        sa.Column('rating_key', sa.String(), nullable=True),  # Local server ratingKey
        # Media Info
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('media_type', media_type_enum, nullable=True),
        # Additional Metadata
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('thumb', sa.String(), nullable=True),
        sa.Column('art', sa.String(), nullable=True),
        sa.Column('content_rating', sa.String(), nullable=True),
        sa.Column('studio', sa.String(), nullable=True),
        # Timestamps
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_wishlist_items_id', 'wishlist_items', ['id'])
    op.create_index('idx_wishlist_items_guid', 'wishlist_items', ['guid'], unique=True)
    op.create_index('ix_wishlist_items_title', 'wishlist_items', ['title'])
    op.create_index('ix_wishlist_items_year', 'wishlist_items', ['year'])
    op.create_index('ix_wishlist_items_rating_key', 'wishlist_items', ['rating_key'])

    # Create wishlist_item_sources table
    op.create_table(
        'wishlist_item_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('wishlist_item_id', sa.Integer(), nullable=False),
        sa.Column('plex_user_id', sa.Integer(), nullable=False),
        sa.Column('first_added_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['wishlist_item_id'], ['wishlist_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plex_user_id'], ['plex_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_wishlist_item_sources_id', 'wishlist_item_sources', ['id'])
    op.create_index('ix_wishlist_item_sources_wishlist_item_id', 'wishlist_item_sources', ['wishlist_item_id'])
    op.create_index('ix_wishlist_item_sources_plex_user_id', 'wishlist_item_sources', ['plex_user_id'])
    op.create_index('idx_wishlist_item_sources_item_user', 'wishlist_item_sources', ['wishlist_item_id', 'plex_user_id'])


def downgrade() -> None:
    op.drop_table('wishlist_item_sources')
    op.drop_table('wishlist_items')
    op.drop_table('plex_users')
    op.execute("DROP TYPE IF EXISTS mediatype")
