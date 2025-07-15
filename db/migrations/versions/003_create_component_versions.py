"""Create component_versions table

Revision ID: 003
Revises: 002
Create Date: 2025-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Create component versions tables for versioning system."""
    
    # Create component_versions table
    op.create_table(
        'component_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('component_id', sa.String(length=255), nullable=False),
        sa.Column('component_type', sa.String(length=50), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_deprecated', sa.Boolean(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sync_source', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('component_id', 'version', name='uq_component_version')
    )
    
    # Create indexes for performance
    op.create_index('ix_component_versions_component_id', 'component_versions', ['component_id'])
    op.create_index('ix_component_versions_component_type', 'component_versions', ['component_type'])
    op.create_index('ix_component_versions_is_active', 'component_versions', ['is_active'])
    op.create_index('ix_component_versions_created_at', 'component_versions', ['created_at'])
    
    # Create component_version_history table for audit trail
    op.create_table(
        'component_version_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('component_id', sa.String(length=255), nullable=False),
        sa.Column('component_type', sa.String(length=50), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),  # created, activated, deprecated
        sa.Column('changed_by', sa.String(length=255), nullable=True),
        sa.Column('changed_at', sa.DateTime(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('previous_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for history table
    op.create_index('ix_component_version_history_component_id', 'component_version_history', ['component_id'])
    op.create_index('ix_component_version_history_changed_at', 'component_version_history', ['changed_at'])
    op.create_index('ix_component_version_history_action', 'component_version_history', ['action'])


def downgrade():
    """Drop component versions tables."""
    
    # Drop indexes first
    op.drop_index('ix_component_version_history_action', table_name='component_version_history')
    op.drop_index('ix_component_version_history_changed_at', table_name='component_version_history')
    op.drop_index('ix_component_version_history_component_id', table_name='component_version_history')
    
    op.drop_index('ix_component_versions_created_at', table_name='component_versions')
    op.drop_index('ix_component_versions_is_active', table_name='component_versions')
    op.drop_index('ix_component_versions_component_type', table_name='component_versions')
    op.drop_index('ix_component_versions_component_id', table_name='component_versions')
    
    # Drop tables
    op.drop_table('component_version_history')
    op.drop_table('component_versions')