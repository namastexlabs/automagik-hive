"""
Metrics Service

Clean psycopg3 implementation for agent metrics in hive schema.
Replaces direct SQL CREATE TABLE statements with proper service pattern.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .database_service import get_db_service


@dataclass
class AgentMetric:
    """Agent metric data class."""

    id: int
    timestamp: datetime
    agent_name: str
    execution_type: str
    metrics: dict[str, Any]
    version: str
    created_at: datetime


class MetricsService:
    """
    Clean metrics service using hive schema.
    Replaces direct SQL table creation with proper service pattern.
    """

    async def store_metrics(
        self,
        timestamp: datetime,
        agent_name: str,
        execution_type: str,
        metrics: dict[str, Any],
        version: str = "1.0",
    ) -> int:
        """Store agent metrics data."""
        db = await get_db_service()

        query = """
        INSERT INTO hive.agent_metrics
        (timestamp, agent_name, execution_type, metrics, version)
        VALUES (%(timestamp)s, %(agent_name)s, %(execution_type)s, %(metrics)s, %(version)s)
        RETURNING id
        """

        result = await db.fetch_one(
            query,
            {
                "timestamp": timestamp,
                "agent_name": agent_name,
                "execution_type": execution_type,
                "metrics": json.dumps(metrics),
                "version": version,
            },
        )

        return result["id"]

    async def get_metrics_by_agent(
        self, agent_name: str, limit: int = 100, offset: int = 0
    ) -> list[AgentMetric]:
        """Get metrics for a specific agent."""
        db = await get_db_service()

        query = """
        SELECT id, timestamp, agent_name, execution_type, metrics, version, created_at
        FROM hive.agent_metrics
        WHERE agent_name = %(agent_name)s
        ORDER BY timestamp DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """

        results = await db.fetch_all(
            query, {"agent_name": agent_name, "limit": limit, "offset": offset}
        )

        return [
            AgentMetric(
                id=row["id"],
                timestamp=row["timestamp"],
                agent_name=row["agent_name"],
                execution_type=row["execution_type"],
                metrics=json.loads(row["metrics"])
                if isinstance(row["metrics"], str)
                else row["metrics"],
                version=row["version"],
                created_at=row["created_at"],
            )
            for row in results
        ]

    async def get_metrics_by_execution_type(
        self, execution_type: str, limit: int = 100, offset: int = 0
    ) -> list[AgentMetric]:
        """Get metrics by execution type."""
        db = await get_db_service()

        query = """
        SELECT id, timestamp, agent_name, execution_type, metrics, version, created_at
        FROM hive.agent_metrics
        WHERE execution_type = %(execution_type)s
        ORDER BY timestamp DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """

        results = await db.fetch_all(
            query, {"execution_type": execution_type, "limit": limit, "offset": offset}
        )

        return [
            AgentMetric(
                id=row["id"],
                timestamp=row["timestamp"],
                agent_name=row["agent_name"],
                execution_type=row["execution_type"],
                metrics=json.loads(row["metrics"])
                if isinstance(row["metrics"], str)
                else row["metrics"],
                version=row["version"],
                created_at=row["created_at"],
            )
            for row in results
        ]

    async def get_metrics_summary(
        self, agent_name: str | None = None
    ) -> dict[str, Any]:
        """Get metrics summary statistics."""
        db = await get_db_service()

        base_query = """
        SELECT
            COUNT(*) as total_executions,
            COUNT(DISTINCT agent_name) as unique_agents,
            COUNT(DISTINCT execution_type) as unique_execution_types,
            MIN(timestamp) as earliest_metric,
            MAX(timestamp) as latest_metric
        FROM hive.agent_metrics
        """

        params = {}
        if agent_name:
            base_query += " WHERE agent_name = %(agent_name)s"
            params["agent_name"] = agent_name

        result = await db.fetch_one(base_query, params)

        return {
            "total_executions": result["total_executions"],
            "unique_agents": result["unique_agents"],
            "unique_execution_types": result["unique_execution_types"],
            "earliest_metric": result["earliest_metric"],
            "latest_metric": result["latest_metric"],
        }

    async def cleanup_old_metrics(self, days_to_keep: int = 30) -> int:
        """Clean up metrics older than specified days."""
        db = await get_db_service()

        query = """
        DELETE FROM hive.agent_metrics
        WHERE created_at < NOW() - INTERVAL '%s days'
        """

        # Execute and get count of deleted rows
        async with db.get_connection() as conn:
            result = await conn.execute(query, (days_to_keep,))
            return result.rowcount if result.rowcount else 0
