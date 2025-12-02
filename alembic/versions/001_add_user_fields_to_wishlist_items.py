"""add_user_name_plex_token_rating_key_to_wishlist_items

Revision ID: 001_add_user_fields
Revises: 000_initial
Create Date: 2025-11-24 20:45:00.000000

NOTE: These columns are now included in the initial schema (000_initial).
This migration is kept for compatibility with existing databases that were
created before the initial schema was refactored.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '001_add_user_fields'
down_revision = '000_initial'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column already exists in the table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    # Only add columns if they don't already exist (for fresh installs they're in 000_initial)
    if not column_exists('wishlist_items', 'user_name'):
        op.add_column('wishlist_items', sa.Column('user_name', sa.String(), nullable=True))
    if not column_exists('wishlist_items', 'plex_token'):
        op.add_column('wishlist_items', sa.Column('plex_token', sa.String(), nullable=True))
    if not column_exists('wishlist_items', 'rating_key'):
        op.add_column('wishlist_items', sa.Column('rating_key', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove the columns if we need to rollback
    if column_exists('wishlist_items', 'rating_key'):
        op.drop_column('wishlist_items', 'rating_key')
    if column_exists('wishlist_items', 'plex_token'):
        op.drop_column('wishlist_items', 'plex_token')
    if column_exists('wishlist_items', 'user_name'):
        op.drop_column('wishlist_items', 'user_name')




