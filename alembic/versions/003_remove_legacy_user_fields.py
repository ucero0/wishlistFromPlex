"""Remove legacy user_name and plex_token from wishlist_items

Revision ID: 003_remove_legacy_user_fields
Revises: 002_media_metadata
Create Date: 2025-12-02

These fields were redundant - the proper way to track which users have 
which items is through the wishlist_item_sources relationship table.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '003_remove_legacy_user_fields'
down_revision = '002_media_metadata'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column exists in the table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    # Remove legacy columns if they exist
    if column_exists('wishlist_items', 'user_name'):
        op.drop_column('wishlist_items', 'user_name')
    if column_exists('wishlist_items', 'plex_token'):
        op.drop_column('wishlist_items', 'plex_token')


def downgrade() -> None:
    # Re-add the columns if needed for rollback
    if not column_exists('wishlist_items', 'user_name'):
        op.add_column('wishlist_items', sa.Column('user_name', sa.String(), nullable=True))
    if not column_exists('wishlist_items', 'plex_token'):
        op.add_column('wishlist_items', sa.Column('plex_token', sa.String(), nullable=True))

