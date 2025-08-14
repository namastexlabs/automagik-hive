"""
Coverage-focused tests for lib/services/metrics_service.py
Target: Boost coverage from 44% to 50%+ minimum with comprehensive test suite.
"""

import json
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lib.services.metrics_service import AgentMetric, MetricsService


class TestMetricsServiceCoverage:
    """Comprehensive coverage tests for MetricsService."""

    @pytest.mark.asyncio
    async def test_get_metrics_summary_with_agent_filter(self):
        """Test get_metrics_summary with agent_name filter - covers missing lines 150-151."""
        mock_db = AsyncMock()
        mock_stats = {
            "total_executions": 25,
            "unique_agents": 1,
            "unique_execution_types": 3,
            "earliest_metric": datetime(2024, 1, 1),
            "latest_metric": datetime(2024, 1, 31),
        }
        mock_db.fetch_one.return_value = mock_stats

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            # Test with agent_name filter to cover lines 150-151
            stats = await service.get_metrics_summary(agent_name="specific-agent")

        assert stats["total_executions"] == 25
        assert stats["unique_agents"] == 1
        assert stats["unique_execution_types"] == 3

        # Check SQL query includes WHERE clause for agent filtering
        call_args = mock_db.fetch_one.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        assert "WHERE agent_name = %(agent_name)s" in query
        assert "agent_name" in params
        assert params["agent_name"] == "specific-agent"

    @pytest.mark.asyncio
    async def test_get_metrics_by_agent_with_pagination(self):
        """Test pagination parameters for get_metrics_by_agent."""
        mock_db = AsyncMock()
        mock_metrics_data = [
            {
                "id": i,
                "timestamp": datetime.now(),
                "agent_name": "paginated-agent",
                "execution_type": "query",
                "metrics": json.dumps({"page": i}),
                "version": "1.0",
                "created_at": datetime.now(),
            }
            for i in range(1, 6)
        ]
        mock_db.fetch_all.return_value = mock_metrics_data

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            # Test with custom limit and offset
            metrics = await service.get_metrics_by_agent(
                agent_name="paginated-agent", limit=5, offset=10
            )

        assert len(metrics) == 5
        for metric in metrics:
            assert isinstance(metric, AgentMetric)
            assert metric.agent_name == "paginated-agent"

        # Verify pagination parameters were passed correctly
        call_args = mock_db.fetch_all.call_args
        params = call_args[0][1]
        assert params["limit"] == 5
        assert params["offset"] == 10

    @pytest.mark.asyncio
    async def test_get_metrics_by_execution_type_with_pagination(self):
        """Test pagination for get_metrics_by_execution_type."""
        mock_db = AsyncMock()
        mock_metrics_data = []
        mock_db.fetch_all.return_value = mock_metrics_data

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            metrics = await service.get_metrics_by_execution_type(
                execution_type="completion", limit=50, offset=100
            )

        assert metrics == []

        # Verify query structure and parameters
        call_args = mock_db.fetch_all.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        assert "WHERE execution_type = %(execution_type)s" in query
        assert "LIMIT %(limit)s OFFSET %(offset)s" in query
        assert params["execution_type"] == "completion"
        assert params["limit"] == 50
        assert params["offset"] == 100

    @pytest.mark.asyncio
    async def test_metrics_json_parsing_string_format(self):
        """Test JSON parsing when metrics is returned as string."""
        mock_db = AsyncMock()
        mock_metrics_data = [
            {
                "id": 1,
                "timestamp": datetime.now(),
                "agent_name": "json-agent",
                "execution_type": "test",
                "metrics": '{"execution_time": 2.5, "tokens": 100}',  # String format
                "version": "1.0",
                "created_at": datetime.now(),
            }
        ]
        mock_db.fetch_all.return_value = mock_metrics_data

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            metrics = await service.get_metrics_by_agent("json-agent")

        assert len(metrics) == 1
        metric = metrics[0]
        assert isinstance(metric.metrics, dict)
        assert metric.metrics["execution_time"] == 2.5
        assert metric.metrics["tokens"] == 100

    @pytest.mark.asyncio
    async def test_metrics_json_parsing_dict_format(self):
        """Test JSON parsing when metrics is already a dict."""
        mock_db = AsyncMock()
        mock_metrics_data = [
            {
                "id": 1,
                "timestamp": datetime.now(),
                "agent_name": "dict-agent",
                "execution_type": "test",
                "metrics": {"execution_time": 1.8, "success": True},  # Dict format
                "version": "1.0",
                "created_at": datetime.now(),
            }
        ]
        mock_db.fetch_all.return_value = mock_metrics_data

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            metrics = await service.get_metrics_by_execution_type("test")

        assert len(metrics) == 1
        metric = metrics[0]
        assert isinstance(metric.metrics, dict)
        assert metric.metrics["execution_time"] == 1.8
        assert metric.metrics["success"] is True

    @pytest.mark.asyncio
    async def test_cleanup_old_metrics_no_rows_deleted(self):
        """Test cleanup when no rows are deleted."""
        mock_db = AsyncMock()
        mock_connection = AsyncMock()
        mock_result = AsyncMock()
        mock_result.rowcount = None  # No rows affected
        mock_connection.execute.return_value = mock_result

        class MockConnectionAsyncContext:
            async def __aenter__(self):
                return mock_connection

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        mock_db.get_connection = MagicMock(return_value=MockConnectionAsyncContext())

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            deleted_count = await service.cleanup_old_metrics(days_to_keep=7)

        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_cleanup_old_metrics_custom_retention(self):
        """Test cleanup with different retention periods."""
        mock_db = AsyncMock()
        mock_connection = AsyncMock()
        mock_result = AsyncMock()
        mock_result.rowcount = 15
        mock_connection.execute.return_value = mock_result

        class MockConnectionAsyncContext:
            async def __aenter__(self):
                return mock_connection

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        mock_db.get_connection = MagicMock(return_value=MockConnectionAsyncContext())

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            # Test with 7 days retention
            deleted_count = await service.cleanup_old_metrics(days_to_keep=7)

        assert deleted_count == 15

        # Verify the query used the correct retention period
        call_args = mock_connection.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        assert "DELETE FROM hive.agent_metrics" in query
        assert "INTERVAL '%s days'" in query
        assert params == (7,)

    @pytest.mark.asyncio
    async def test_store_metrics_json_serialization(self):
        """Test that complex metrics data is properly JSON serialized."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {"id": 999}

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            nested_metrics = {
                "performance": {
                    "execution_time": 3.14159,
                    "memory_usage": 256.5,
                    "cpu_usage": 75.2,
                },
                "model_params": {
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "top_p": 0.9,
                },
                "results": {
                    "success": True,
                    "tokens_used": 847,
                    "cost": 0.0025,
                    "errors": [],
                },
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "version": "2.1.0",
                    "environment": "production",
                },
            }

            result_id = await service.store_metrics(
                timestamp=datetime.now(),
                agent_name="performance-agent",
                execution_type="benchmark",
                metrics=nested_metrics,
                version="2.1",
            )

        assert result_id == 999

        # Verify that metrics were JSON serialized
        call_args = mock_db.fetch_one.call_args
        params = call_args[0][1]
        serialized_metrics = params["metrics"]
        
        # Should be a JSON string, not the original dict
        assert isinstance(serialized_metrics, str)
        
        # Should be able to deserialize back to original structure
        deserialized = json.loads(serialized_metrics)
        assert deserialized["performance"]["execution_time"] == 3.14159
        assert deserialized["model_params"]["temperature"] == 0.7
        assert deserialized["results"]["success"] is True

    @pytest.mark.asyncio
    async def test_get_metrics_summary_edge_cases(self):
        """Test get_metrics_summary with edge case return values."""
        mock_db = AsyncMock()
        mock_stats = {
            "total_executions": 0,
            "unique_agents": 0,
            "unique_execution_types": 0,
            "earliest_metric": None,
            "latest_metric": None,
        }
        mock_db.fetch_one.return_value = mock_stats

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            stats = await service.get_metrics_summary()

        assert stats["total_executions"] == 0
        assert stats["unique_agents"] == 0
        assert stats["unique_execution_types"] == 0
        assert stats["earliest_metric"] is None
        assert stats["latest_metric"] is None

    @pytest.mark.asyncio
    async def test_agent_metric_dataclass_validation(self):
        """Test AgentMetric dataclass with various data types."""
        now = datetime.now()
        
        # Test with different metric types
        metric1 = AgentMetric(
            id=1,
            timestamp=now,
            agent_name="test-agent",
            execution_type="validation",
            metrics={"string": "value", "number": 42, "boolean": True, "null": None},
            version="1.0",
            created_at=now,
        )
        
        assert metric1.metrics["string"] == "value"
        assert metric1.metrics["number"] == 42
        assert metric1.metrics["boolean"] is True
        assert metric1.metrics["null"] is None

        # Test with empty metrics
        metric2 = AgentMetric(
            id=2,
            timestamp=now,
            agent_name="empty-agent",
            execution_type="empty",
            metrics={},
            version="1.0",
            created_at=now,
        )
        
        assert metric2.metrics == {}


class TestMetricsServiceErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_store_metrics_database_connection_error(self):
        """Test handling of database connection errors during store."""
        mock_db = AsyncMock()
        mock_db.fetch_one.side_effect = ConnectionError("Database unavailable")

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            with pytest.raises(ConnectionError, match="Database unavailable"):
                await service.store_metrics(
                    timestamp=datetime.now(),
                    agent_name="error-agent",
                    execution_type="error",
                    metrics={"test": "error"},
                )

    @pytest.mark.asyncio
    async def test_get_metrics_by_agent_database_error(self):
        """Test database error handling in get_metrics_by_agent."""
        mock_db = AsyncMock()
        mock_db.fetch_all.side_effect = TimeoutError("Query timeout")

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            with pytest.raises(TimeoutError, match="Query timeout"):
                await service.get_metrics_by_agent("timeout-agent")

    @pytest.mark.asyncio
    async def test_get_metrics_summary_database_error(self):
        """Test database error handling in get_metrics_summary."""
        mock_db = AsyncMock()
        mock_db.fetch_one.side_effect = RuntimeError("Summary query failed")

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            with pytest.raises(RuntimeError, match="Summary query failed"):
                await service.get_metrics_summary("error-agent")

    @pytest.mark.asyncio
    async def test_cleanup_old_metrics_connection_error(self):
        """Test cleanup error handling."""
        mock_db = AsyncMock()
        mock_connection = AsyncMock()
        mock_connection.execute.side_effect = Exception("Cleanup failed")

        class MockConnectionAsyncContext:
            async def __aenter__(self):
                return mock_connection

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        mock_db.get_connection = MagicMock(return_value=MockConnectionAsyncContext())

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            with pytest.raises(Exception, match="Cleanup failed"):
                await service.cleanup_old_metrics(14)


class TestMetricsServiceIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_complete_metrics_workflow(self):
        """Test a complete workflow of storing and retrieving metrics."""
        mock_db = AsyncMock()
        
        # Mock store operation
        mock_db.fetch_one.return_value = {"id": 100}
        
        # Mock retrieval operation
        stored_timestamp = datetime.now()
        mock_metrics_data = [
            {
                "id": 100,
                "timestamp": stored_timestamp,
                "agent_name": "workflow-agent",
                "execution_type": "workflow",
                "metrics": '{"duration": 5.0, "success": true}',
                "version": "1.5",
                "created_at": stored_timestamp,
            }
        ]
        mock_db.fetch_all.return_value = mock_metrics_data

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            # Store metrics
            metric_id = await service.store_metrics(
                timestamp=stored_timestamp,
                agent_name="workflow-agent",
                execution_type="workflow",
                metrics={"duration": 5.0, "success": True},
                version="1.5",
            )

            assert metric_id == 100

            # Retrieve metrics
            metrics = await service.get_metrics_by_agent("workflow-agent")

            assert len(metrics) == 1
            metric = metrics[0]
            assert metric.id == 100
            assert metric.agent_name == "workflow-agent"
            assert metric.execution_type == "workflow"
            assert metric.metrics["duration"] == 5.0
            assert metric.metrics["success"] is True
            assert metric.version == "1.5"

    @pytest.mark.asyncio
    async def test_high_volume_metrics_simulation(self):
        """Test handling of high-volume metrics scenarios."""
        mock_db = AsyncMock()
        
        # Simulate large result set
        large_dataset = [
            {
                "id": i + 1,
                "timestamp": datetime.now(),
                "agent_name": f"agent-{i % 10}",
                "execution_type": "bulk",
                "metrics": json.dumps({"batch": i + 1, "processed": True}),
                "version": "1.0",
                "created_at": datetime.now(),
            }
            for i in range(1000)
        ]
        mock_db.fetch_all.return_value = large_dataset

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            metrics = await service.get_metrics_by_execution_type(
                execution_type="bulk", limit=1000, offset=0
            )

        assert len(metrics) == 1000
        
        # Verify all metrics were properly parsed
        for i, metric in enumerate(metrics):
            assert isinstance(metric, AgentMetric)
            assert metric.execution_type == "bulk"
            assert metric.metrics["batch"] == i + 1
            assert metric.metrics["processed"] is True

    @pytest.mark.asyncio
    async def test_metrics_aggregation_scenarios(self):
        """Test various metrics aggregation scenarios."""
        mock_db = AsyncMock()
        
        # Test scenario 1: Multiple agents
        mock_stats_multi_agent = {
            "total_executions": 500,
            "unique_agents": 15,
            "unique_execution_types": 8,
            "earliest_metric": datetime(2024, 1, 1, 10, 0, 0),
            "latest_metric": datetime(2024, 1, 31, 18, 30, 0),
        }
        mock_db.fetch_one.return_value = mock_stats_multi_agent

        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service = MetricsService()

            stats = await service.get_metrics_summary()

        assert stats["total_executions"] == 500
        assert stats["unique_agents"] == 15
        assert stats["unique_execution_types"] == 8
        assert isinstance(stats["earliest_metric"], datetime)
        assert isinstance(stats["latest_metric"], datetime)

        # Test scenario 2: Single agent filter - create new service instance
        with patch("lib.services.metrics_service.get_db_service", return_value=mock_db):
            service2 = MetricsService()
            
            mock_stats_single_agent = {
                "total_executions": 50,
                "unique_agents": 1,
                "unique_execution_types": 3,
                "earliest_metric": datetime(2024, 1, 15, 9, 0, 0),
                "latest_metric": datetime(2024, 1, 31, 17, 45, 0),
            }
            mock_db.fetch_one.return_value = mock_stats_single_agent

            filtered_stats = await service2.get_metrics_summary(agent_name="specific-agent")

            assert filtered_stats["total_executions"] == 50
            assert filtered_stats["unique_agents"] == 1

    def test_agent_metric_dataclass_immutability(self):
        """Test AgentMetric dataclass properties."""
        timestamp = datetime.now()
        created_at = datetime.now()
        
        metric = AgentMetric(
            id=1,
            timestamp=timestamp,
            agent_name="immutable-agent",
            execution_type="test",
            metrics={"immutable": True},
            version="1.0",
            created_at=created_at,
        )
        
        # Test that all fields are accessible
        assert hasattr(metric, "id")
        assert hasattr(metric, "timestamp")
        assert hasattr(metric, "agent_name")
        assert hasattr(metric, "execution_type")
        assert hasattr(metric, "metrics")
        assert hasattr(metric, "version")
        assert hasattr(metric, "created_at")
        
        # Test values are as expected
        assert metric.id == 1
        assert metric.timestamp == timestamp
        assert metric.agent_name == "immutable-agent"
        assert metric.execution_type == "test"
        assert metric.metrics == {"immutable": True}
        assert metric.version == "1.0"
        assert metric.created_at == created_at