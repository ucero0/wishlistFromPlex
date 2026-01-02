"""add_ratingkey_and_plexusertoken_to_torrent_items

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-01-02 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add ratingKey and plexUserToken columns to torrent_items table.
    These columns are used to re-add items to the Plex watchlist after
    infected files are detected and removed.
    """
    # Add ratingKey column (nullable for backward compatibility)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'torrent_items' 
                AND column_name = 'ratingKey'
            ) THEN
                ALTER TABLE torrent_items ADD COLUMN "ratingKey" VARCHAR;
            END IF;
        END $$;
    """)
    
    # Add plexUserToken column (nullable for backward compatibility)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'torrent_items' 
                AND column_name = 'plexUserToken'
            ) THEN
                ALTER TABLE torrent_items ADD COLUMN "plexUserToken" VARCHAR;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """
    Remove ratingKey and plexUserToken columns from torrent_items table.
    """
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'torrent_items' 
                AND column_name = 'ratingKey'
            ) THEN
                ALTER TABLE torrent_items DROP COLUMN "ratingKey";
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'torrent_items' 
                AND column_name = 'plexUserToken'
            ) THEN
                ALTER TABLE torrent_items DROP COLUMN "plexUserToken";
            END IF;
        END $$;
    """)
