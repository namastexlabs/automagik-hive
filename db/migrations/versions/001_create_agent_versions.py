"""
Create agent versions tables

This migration creates the initial tables for the agent versioning system:
- agent_versions: Store different versions of agent configurations
- agent_version_history: Track changes and audit trail
- agent_version_metrics: Store performance metrics for A/B testing

Revision ID: 001
Revises: 
Create Date: 2025-01-14
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create agent versioning tables."""
    
    # Initialize PgVector extension for PostgreSQL
    bind = op.get_bind()
    if "postgresql" in str(bind.dialect):
        op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create agent_versions table
    op.create_table(
        'agent_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.String(length=255), nullable=False, comment='Stable agent identifier (e.g., pagbank-specialist)'),
        sa.Column('version', sa.Integer(), nullable=False, comment='Version number (e.g., 27, 28, 29)'),
        sa.Column('config', sa.JSON(), nullable=False, comment='Full agent configuration including prompts, tools, model settings'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), comment='When this version was created'),
        sa.Column('created_by', sa.String(length=255), comment='User who created this version'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false', comment='Whether this version is currently active'),
        sa.Column('is_deprecated', sa.Boolean(), nullable=False, server_default='false', comment='Whether this version is deprecated'),
        sa.Column('description', sa.Text(), comment='Description of changes in this version'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create unique index for agent_id + version
    op.create_index(
        'idx_agent_versions_unique', 
        'agent_versions', 
        ['agent_id', 'version'], 
        unique=True
    )
    
    # Create lookup index
    op.create_index(
        'idx_agent_versions_lookup',
        'agent_versions',
        ['agent_id', 'version']
    )
    
    # Create active version index
    op.create_index(
        'idx_agent_versions_active',
        'agent_versions',
        ['agent_id', 'is_active'],
        postgresql_where=sa.text('is_active = true')
    )
    
    # Create created_at index
    op.create_index(
        'idx_agent_versions_created',
        'agent_versions',
        ['created_at']
    )
    
    # Create agent_version_history table
    op.create_table(
        'agent_version_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.String(length=255), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False, comment='Action: created, activated, deactivated, deprecated'),
        sa.Column('previous_state', sa.JSON(), comment='Previous state before change'),
        sa.Column('new_state', sa.JSON(), comment='New state after change'),
        sa.Column('changed_by', sa.String(length=255), comment='User who made the change'),
        sa.Column('changed_at', sa.DateTime(), server_default=sa.text('now()'), comment='When the change was made'),
        sa.Column('reason', sa.Text(), comment='Reason for the change'),
        sa.PrimaryKeyConstraint('id')    )
    
    # Create history lookup index
    op.create_index(
        'idx_agent_version_history_lookup',
        'agent_version_history',
        ['agent_id', 'version', 'changed_at']    )
    
    # Create changed_at index
    op.create_index(
        'idx_agent_version_history_changed',
        'agent_version_history',
        ['changed_at']    )
    
    # Create agent_version_metrics table
    op.create_table(
        'agent_version_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.String(length=255), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('metric_date', sa.DateTime(), server_default=sa.text('now()'), comment='Date for this metric snapshot'),
        sa.Column('total_requests', sa.Integer(), nullable=False, server_default='0', comment='Total requests handled by this version'),
        sa.Column('successful_requests', sa.Integer(), nullable=False, server_default='0', comment='Successfully handled requests'),
        sa.Column('failed_requests', sa.Integer(), nullable=False, server_default='0', comment='Failed requests'),
        sa.Column('average_response_time', sa.Integer(), comment='Average response time in milliseconds'),
        sa.Column('escalation_rate', sa.Integer(), comment='Percentage of requests that were escalated'),
        sa.Column('user_satisfaction', sa.Integer(), comment='User satisfaction score (1-10)'),
        sa.PrimaryKeyConstraint('id')    )
    
    # Create metrics lookup index
    op.create_index(
        'idx_agent_version_metrics_lookup',
        'agent_version_metrics',
        ['agent_id', 'version', 'metric_date']    )
    
    # Create metric date index
    op.create_index(
        'idx_agent_version_metrics_date',
        'agent_version_metrics',
        ['metric_date']    )


def downgrade():
    """Drop agent versioning tables."""
    
    # Drop metrics table and its indexes
    op.drop_index('idx_agent_version_metrics_date', table_name='agent_version_metrics', schema='public')
    op.drop_index('idx_agent_version_metrics_lookup', table_name='agent_version_metrics', schema='public')
    op.drop_table('agent_version_metrics', schema='public')
    
    # Drop history table and its indexes
    op.drop_index('idx_agent_version_history_changed', table_name='agent_version_history', schema='public')
    op.drop_index('idx_agent_version_history_lookup', table_name='agent_version_history', schema='public')
    op.drop_table('agent_version_history', schema='public')
    
    # Drop versions table and its indexes
    op.drop_index('idx_agent_versions_created', table_name='agent_versions', schema='public')
    op.drop_index('idx_agent_versions_active', table_name='agent_versions', schema='public')
    op.drop_index('idx_agent_versions_lookup', table_name='agent_versions', schema='public')
    op.drop_index('idx_agent_versions_unique', table_name='agent_versions', schema='public')
    op.drop_table('agent_versions', schema='public')