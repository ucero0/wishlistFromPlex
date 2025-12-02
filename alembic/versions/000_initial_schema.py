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

    # Create wishlist_items table
    op.create_table(
        'wishlist_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uid', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('user_name', sa.String(), nullable=True),
        sa.Column('plex_token', sa.String(), nullable=True),
        sa.Column('rating_key', sa.String(), nullable=True),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_wishlist_items_id', 'wishlist_items', ['id'])
    op.create_index('ix_wishlist_items_uid', 'wishlist_items', ['uid'], unique=True)
    op.create_index('ix_wishlist_items_title', 'wishlist_items', ['title'])
    op.create_index('ix_wishlist_items_year', 'wishlist_items', ['year'])
    op.create_index('idx_wishlist_items_uid', 'wishlist_items', ['uid'])

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

