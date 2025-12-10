"""Create scan_results table for virus scanner

Revision ID: 005_scan_results
Revises: 004_torrent_items
Create Date: 2025-12-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_scan_results'
down_revision = '004_torrent_items'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create scan status enum
    scan_status = sa.Enum(
        'pending', 'scanning', 'clean', 'infected', 'error',
        name='scanstatus'
    )
    scan_status.create(op.get_bind(), checkfirst=True)
    
    # Create scan_results table
    op.create_table(
        'scan_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('torrent_hash', sa.String(40), nullable=False),
        sa.Column('status', sa.Enum('pending', 'scanning', 'clean', 'infected', 'error', name='scanstatus'), nullable=False, server_default='pending'),
        sa.Column('clamav_result', sa.JSON(), nullable=True),
        sa.Column('yara_result', sa.JSON(), nullable=True),
        sa.Column('original_path', sa.String(), nullable=True),
        sa.Column('destination_path', sa.String(), nullable=True),
        sa.Column('threat_name', sa.String(), nullable=True),
        sa.Column('scan_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scan_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_scan_results_torrent_hash', 'scan_results', ['torrent_hash'])
    op.create_index('idx_scan_results_status', 'scan_results', ['status'])
    op.create_index(op.f('ix_scan_results_id'), 'scan_results', ['id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_scan_results_id'), table_name='scan_results')
    op.drop_index('idx_scan_results_status', table_name='scan_results')
    op.drop_index('idx_scan_results_torrent_hash', table_name='scan_results')
    op.drop_table('scan_results')
    
    # Drop enum
    sa.Enum(name='scanstatus').drop(op.get_bind(), checkfirst=True)

