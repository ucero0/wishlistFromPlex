"""add ingest error fields to antivirus_items

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-05-22 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "c9d0e1f2a3b4"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "antivirus_items",
        sa.Column("ingestError", sa.Text(), nullable=True),
    )
    op.add_column(
        "antivirus_items",
        sa.Column("plannedDestination", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("antivirus_items", "plannedDestination")
    op.drop_column("antivirus_items", "ingestError")
