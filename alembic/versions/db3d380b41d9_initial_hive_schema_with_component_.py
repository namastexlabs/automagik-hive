"""Initial hive schema with component_versions, version_history, and agent_metrics tables.

Revision ID: db3d380b41d9
Revises:
Create Date: 2025-07-20 16:39:36.382070

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "db3d380b41d9"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create hive schema
    op.execute("CREATE SCHEMA IF NOT EXISTS hive")

    # Create component_versions table
    op.create_table(
        "component_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("component_id", sa.String(255), nullable=False),
        sa.Column("component_type", sa.String(50), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.Boolean(), default=False, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(255), default="system", nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="hive",
    )

    # Create indexes for component_versions
    op.create_index(
        "idx_component_versions_component_id",
        "component_versions",
        ["component_id"],
        schema="hive",
    )
    op.create_index(
        "idx_component_versions_component_type",
        "component_versions",
        ["component_type"],
        schema="hive",
    )
    op.create_index(
        "idx_component_versions_is_active",
        "component_versions",
        ["is_active"],
        schema="hive",
    )

    # Create version_history table
    op.create_table(
        "version_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("component_id", sa.String(255), nullable=False),
        sa.Column("from_version", sa.Integer(), nullable=True),
        sa.Column("to_version", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("changed_by", sa.String(255), default="system", nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="hive",
    )

    # Create indexes for version_history
    op.create_index(
        "idx_version_history_component_id",
        "version_history",
        ["component_id"],
        schema="hive",
    )

    # Create agent_metrics table
    op.create_table(
        "agent_metrics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("agent_name", sa.String(255), nullable=False),
        sa.Column("execution_type", sa.String(50), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("version", sa.String(10), nullable=False, default="1.0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="hive",
    )

    # Create indexes for agent_metrics
    op.create_index(
        "idx_agent_metrics_timestamp", "agent_metrics", ["timestamp"], schema="hive"
    )
    op.create_index(
        "idx_agent_metrics_agent_name", "agent_metrics", ["agent_name"], schema="hive"
    )
    op.create_index(
        "idx_agent_metrics_execution_type",
        "agent_metrics",
        ["execution_type"],
        schema="hive",
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order
    op.drop_table("agent_metrics", schema="hive")
    op.drop_table("version_history", schema="hive")
    op.drop_table("component_versions", schema="hive")

    # Drop schema (only if empty)
    op.execute("DROP SCHEMA IF EXISTS hive CASCADE")
