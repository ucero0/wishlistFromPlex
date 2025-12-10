"""Create torrent_search_results table for Prowlarr integration

Revision ID: 006_torrent_search
Revises: 005_scan_results
Create Date: 2025-12-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_torrent_search'
down_revision = '005_scan_results'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create search status enum
    search_status = sa.Enum(
        'pending', 'searching', 'found', 'not_found', 'added', 'error',
        name='searchstatus'
    )
    search_status.create(op.get_bind(), checkfirst=True)
    
    # Create torrent_search_results table
    op.create_table(
        'torrent_search_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rating_key', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'searching', 'found', 'not_found', 'added', 'error', name='searchstatus'), nullable=False, server_default='pending'),
        sa.Column('search_query', sa.String(), nullable=True),
        sa.Column('selected_torrent_title', sa.String(), nullable=True),
        sa.Column('selected_torrent_indexer', sa.String(), nullable=True),
        sa.Column('selected_torrent_size', sa.Float(), nullable=True),
        sa.Column('selected_torrent_seeders', sa.Integer(), nullable=True),
        sa.Column('selected_torrent_quality_score', sa.Integer(), nullable=True),
        sa.Column('quality_info', sa.JSON(), nullable=True),
        sa.Column('all_results', sa.JSON(), nullable=True),
        sa.Column('torrent_hash', sa.String(40), nullable=True),
        sa.Column('searched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('added_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_torrent_search_rating_key', 'torrent_search_results', ['rating_key'])
    op.create_index('idx_torrent_search_status', 'torrent_search_results', ['status'])
    op.create_index('idx_torrent_search_hash', 'torrent_search_results', ['torrent_hash'])
    op.create_index(op.f('ix_torrent_search_results_id'), 'torrent_search_results', ['id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_torrent_search_results_id'), table_name='torrent_search_results')
    op.drop_index('idx_torrent_search_hash', table_name='torrent_search_results')
    op.drop_index('idx_torrent_search_status', table_name='torrent_search_results')
    op.drop_index('idx_torrent_search_rating_key', table_name='torrent_search_results')
    op.drop_table('torrent_search_results')
    
    # Drop enum
    sa.Enum(name='searchstatus').drop(op.get_bind(), checkfirst=True)



