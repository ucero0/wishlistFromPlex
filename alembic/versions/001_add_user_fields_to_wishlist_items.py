"""add_user_name_plex_token_rating_key_to_wishlist_items

Revision ID: 001_add_user_fields
Revises: 
Create Date: 2025-11-24 20:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_user_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to wishlist_items table
    op.add_column('wishlist_items', sa.Column('user_name', sa.String(), nullable=True))
    op.add_column('wishlist_items', sa.Column('plex_token', sa.String(), nullable=True))
    op.add_column('wishlist_items', sa.Column('rating_key', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove the columns if we need to rollback
    op.drop_column('wishlist_items', 'rating_key')
    op.drop_column('wishlist_items', 'plex_token')
    op.drop_column('wishlist_items', 'user_name')




