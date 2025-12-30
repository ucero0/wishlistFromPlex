"""fix_filename_column_case

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2025-12-30 08:55:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Fix fileName column case if it was created as lowercase 'filename'.
    This migration checks if 'filename' (lowercase) exists and renames it to 'fileName' (camelCase).
    """
    # Check if lowercase 'filename' column exists and rename it to 'fileName'
    # This handles the case where the previous migration created it as lowercase
    op.execute("""
        DO $$
        BEGIN
            -- Check if 'filename' (lowercase) column exists
            IF EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'torrent_items' 
                AND column_name = 'filename'
            ) THEN
                -- Rename lowercase column to camelCase
                ALTER TABLE torrent_items RENAME COLUMN filename TO "fileName";
            END IF;
            
            -- If 'fileName' doesn't exist at all, create it
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'torrent_items' 
                AND column_name = 'fileName'
            ) THEN
                ALTER TABLE torrent_items ADD COLUMN "fileName" VARCHAR;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """
    Revert the column name back to lowercase if needed.
    Note: This is a safety measure, but may not be necessary.
    """
    # Only rename if 'fileName' exists and 'filename' doesn't
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'torrent_items' 
                AND column_name = 'fileName'
            ) AND NOT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'torrent_items' 
                AND column_name = 'filename'
            ) THEN
                ALTER TABLE torrent_items RENAME COLUMN "fileName" TO filename;
            END IF;
        END $$;
    """)

