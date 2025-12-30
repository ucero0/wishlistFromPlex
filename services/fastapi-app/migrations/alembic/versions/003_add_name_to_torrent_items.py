"""add_fileName_to_torrent_items

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2025-01-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add fileName column to torrent_items table
    # Use raw SQL to ensure quoted identifier preserves case (PostgreSQL requirement)
    op.execute("ALTER TABLE torrent_items ADD COLUMN \"fileName\" VARCHAR")
    
    # Alternative approach using Alembic (but may create lowercase column):
    # op.add_column('torrent_items', sa.Column('fileName', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove fileName column from torrent_items table
    # Use raw SQL to ensure quoted identifier is used
    op.execute('ALTER TABLE torrent_items DROP COLUMN "fileName"')
    
    # Alternative approach:
    # op.drop_column('torrent_items', 'fileName')

