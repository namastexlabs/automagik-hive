"""Simple tests for lib/services/metrics_service.py."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lib.services.metrics_service import AgentMetric, MetricsService


class TestAgentMetric:
    """Test AgentMetric dataclass."""

    def test_agent_metric_creation(self):
        """Test creating AgentMetric instance."""
        timestamp = datetime.now()
        created_at = datetime.now()
        metrics_data = {"execution_time": 1.5, "tokens": 100}

        metric = AgentMetric(
            id=1,
            timestamp=timestamp,
            agent_name="test-agent",
            execution_type="query",
            metrics=metrics_data,
            version="1.0",
            created_at=created_at,
        )

        assert metric.id == 1
        assert metric.timestamp == timestamp
        assert metric.agent_name == "test-agent"
        assert metric.execution_type == "query"
        assert metric.metrics == metrics_data
        assert metric.version == "1.0"
        assert metric.created_at == created_at


class TestMetricsService:
    """Test MetricsService functionality."""

    @pytest.mark.asyncio
    async def test_store_metrics_success(self):
        """Test successfully storing metrics."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {"id": 123}

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()
            timestamp = datetime.now()
            metrics_data = {"execution_time": 2.5, "tokens": 150}

            result_id = await service.store_metrics(
                timestamp=timestamp,
                agent_name="test-agent",
                execution_type="completion",
                metrics=metrics_data,
                version="2.0",
            )

        assert result_id == 123
        mock_db.fetch_one.assert_called_once()

        # Check the SQL query was called correctly
        mock_db.fetch_one.assert_called_once()
        call_args = mock_db.fetch_one.call_args
        # Verify INSERT query structure
        query = call_args[0][0]
        assert "INSERT INTO hive.agent_metrics" in query
        assert "timestamp" in query
        assert "agent_name" in query
        assert "execution_type" in query
        assert "metrics" in query
        assert "version" in query

    @pytest.mark.asyncio
    async def test_store_metrics_default_version(self):
        """Test storing metrics with default version."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {"id": 456}

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()
            timestamp = datetime.now()

            result_id = await service.store_metrics(
                timestamp=timestamp,
                agent_name="default-agent",
                execution_type="query",
                metrics={"key": "value"},
            )

        assert result_id == 456

        # Check the method was called with defaults
        mock_db.fetch_one.assert_called_once()
        call_args = mock_db.fetch_one.call_args
        query = call_args[0][0]
        assert "INSERT INTO hive.agent_metrics" in query

    @pytest.mark.asyncio
    async def test_get_metrics_by_agent(self):
        """Test getting metrics by agent name."""
        mock_db = AsyncMock()
        mock_metrics_data = [
            {
                "id": 1,
                "timestamp": datetime.now(),
                "agent_name": "test-agent",
                "execution_type": "query",
                "metrics": {"time": 1.0},
                "version": "1.0",
                "created_at": datetime.now(),
            },
        ]
        mock_db.fetch_all.return_value = mock_metrics_data

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            metrics = await service.get_metrics_by_agent("test-agent")

        assert len(metrics) == 1
        assert isinstance(metrics[0], AgentMetric)
        assert metrics[0].agent_name == "test-agent"

        # Check SQL query
        mock_db.fetch_all.assert_called_once()
        call_args = mock_db.fetch_all.call_args
        query = call_args[0][0]
        assert "SELECT" in query
        assert "WHERE agent_name" in query
        assert "LIMIT" in query

    @pytest.mark.asyncio
    async def test_get_metrics_by_date_range(self):
        """Test getting metrics by execution type (method exists in source)."""
        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = []

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            metrics = await service.get_metrics_by_execution_type("query")

        assert metrics == []

        # Check SQL query parameters
        mock_db.fetch_all.assert_called_once()
        call_args = mock_db.fetch_all.call_args
        query = call_args[0][0]
        assert "WHERE execution_type" in query
        assert "LIMIT" in query

    @pytest.mark.asyncio
    async def test_get_execution_stats(self):
        """Test getting metrics summary (method exists in source)."""
        mock_db = AsyncMock()
        mock_stats = {
            "total_executions": 10,
            "unique_agents": 3,
            "unique_execution_types": 2,
            "earliest_metric": datetime(2024, 1, 1),
            "latest_metric": datetime(2024, 1, 31),
        }
        mock_db.fetch_one.return_value = mock_stats

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            stats = await service.get_metrics_summary()

        assert stats["total_executions"] == 10
        assert stats["unique_agents"] == 3

        # Check SQL uses aggregation
        call_args = mock_db.fetch_one.call_args
        assert "COUNT(*)" in call_args[0][0]
        assert "COUNT(DISTINCT" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_delete_old_metrics(self):
        """Test cleaning up old metrics (method exists in source)."""
        mock_db = AsyncMock()
        mock_connection = AsyncMock()
        mock_result = AsyncMock()
        mock_result.rowcount = 5
        mock_connection.execute.return_value = mock_result

        # Create proper async context manager class
        class MockConnectionAsyncContext:
            async def __aenter__(self):
                return mock_connection

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        # Make get_connection() return the async context manager
        mock_db.get_connection = MagicMock(return_value=MockConnectionAsyncContext())

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            deleted_count = await service.cleanup_old_metrics(days_to_keep=30)

        assert deleted_count == 5
        # Check DELETE query
        call_args = mock_connection.execute.call_args
        assert "DELETE FROM hive.agent_metrics" in call_args[0][0]
        assert "INTERVAL" in call_args[0][0]


class TestMetricsServiceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_store_metrics_with_complex_metrics_data(self):
        """Test storing metrics with complex JSON data."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {"id": 789}

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            complex_metrics = {
                "execution_time": 3.14,
                "tokens": {"input": 50, "output": 75},
                "model_info": {
                    "provider": "anthropic",
                    "model": "claude-3",
                    "temperature": 0.7,
                },
                "success": True,
                "error": None,
            }

            result_id = await service.store_metrics(
                timestamp=datetime.now(),
                agent_name="complex-agent",
                execution_type="complex",
                metrics=complex_metrics,
            )

        assert result_id == 789

        # Ensure metrics data was passed correctly
        mock_db.fetch_one.assert_called_once()
        call_args = mock_db.fetch_one.call_args
        query = call_args[0][0]
        assert "INSERT INTO hive.agent_metrics" in query
        assert "metrics" in query

    @pytest.mark.asyncio
    async def test_get_metrics_empty_result(self):
        """Test getting metrics when no results found."""
        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = []

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            metrics = await service.get_metrics_by_agent("non-existent-agent")

        assert metrics == []

    @pytest.mark.asyncio
    async def test_store_metrics_database_error(self):
        """Test storing metrics when database error occurs."""
        mock_db = AsyncMock()
        mock_db.fetch_one.side_effect = Exception("Database connection failed")

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            with pytest.raises(Exception, match="Database connection failed"):
                await service.store_metrics(
                    timestamp=datetime.now(),
                    agent_name="error-agent",
                    execution_type="error",
                    metrics={"error": True},
                )

    @pytest.mark.asyncio
    async def test_get_metrics_with_limit(self):
        """Test getting metrics with result limit."""
        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = []

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            await service.get_metrics_by_agent("test-agent", limit=100)

        # Check LIMIT clause in query and parameters
        mock_db.fetch_all.assert_called_once()
        call_args = mock_db.fetch_all.call_args
        query = call_args[0][0]
        assert "LIMIT" in query
        assert "WHERE agent_name" in query


class TestMetricsServiceIntegration:
    """Test integration scenarios."""

    def test_module_imports(self):
        """Test that the module can be imported without errors."""
        import lib.services.metrics_service
        assert lib.services.metrics_service is not None