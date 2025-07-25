"""Simple tests for lib/services/metrics_service.py."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from typing import Dict, Any

from lib.services.metrics_service import (
    AgentMetric,
    MetricsService
)


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
            created_at=created_at
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
        
        with patch('lib.services.metrics_service.get_db_service', return_value=mock_db):
            service = MetricsService()
            timestamp = datetime.now()
            metrics_data = {"execution_time": 2.5, "tokens": 150}
            
            result_id = await service.store_metrics(
                timestamp=timestamp,
                agent_name="test-agent",
                execution_type="completion",
                metrics=metrics_data,
                version="2.0"
            )
        
        assert result_id == 123
        mock_db.fetch_one.assert_called_once()
        
        # Check the SQL query was called with correct parameters
        call_args = mock_db.fetch_one.call_args
        assert "INSERT INTO hive.agent_metrics" in call_args[0][0]
        assert call_args[1]["timestamp"] == timestamp
        assert call_args[1]["agent_name"] == "test-agent"
        assert call_args[1]["execution_type"] == "completion"
        assert call_args[1]["version"] == "2.0"
    
    @pytest.mark.asyncio
    async def test_store_metrics_default_version(self):
        """Test storing metrics with default version."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {"id": 456}
        
        with patch('lib.services.metrics_service.get_db_service', return_value=mock_db):
            service = MetricsService()
            timestamp = datetime.now()
            
            result_id = await service.store_metrics(
                timestamp=timestamp,
                agent_name="default-agent",
                execution_type="query",
                metrics={"key": "value"}
            )
        
        assert result_id == 456
        
        # Check default version was used
        call_args = mock_db.fetch_one.call_args
        assert call_args[1]["version"] == "1.0"
    
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
                "created_at": datetime.now()
            }
        ]
        mock_db.fetch_all.return_value = mock_metrics_data
        
        with patch('lib.services.metrics_service.get_db_service', return_value=mock_db):
            service = MetricsService()
            
            metrics = await service.get_metrics_by_agent("test-agent")
        
        assert len(metrics) == 1
        assert isinstance(metrics[0], AgentMetric)
        assert metrics[0].agent_name == "test-agent"
        
        # Check SQL query
        call_args = mock_db.fetch_all.call_args
        assert "SELECT" in call_args[0][0]
        assert "WHERE agent_name" in call_args[0][0]
        assert call_args[1]["agent_name"] == "test-agent"
    
    @pytest.mark.asyncio
    async def test_get_metrics_by_date_range(self):
        """Test getting metrics by date range."""
        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = []
        
        with patch('lib.services.metrics_service.get_db_service', return_value=mock_db):
            service = MetricsService()
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 31)
            
            metrics = await service.get_metrics_by_date_range(start_date, end_date)
        
        assert metrics == []
        
        # Check SQL query parameters
        call_args = mock_db.fetch_all.call_args
        assert "timestamp BETWEEN" in call_args[0][0]
        assert call_args[1]["start_date"] == start_date
        assert call_args[1]["end_date"] == end_date
    
    @pytest.mark.asyncio
    async def test_get_execution_stats(self):
        """Test getting execution statistics."""
        mock_db = AsyncMock()
        mock_stats = [
            {
                "agent_name": "agent-1",
                "execution_type": "query",
                "count": 10,
                "avg_execution_time": 1.5
            }
        ]
        mock_db.fetch_all.return_value = mock_stats
        
        with patch('lib.services.metrics_service.get_db_service', return_value=mock_db):
            service = MetricsService()
            
            stats = await service.get_execution_stats()
        
        assert len(stats) == 1
        assert stats[0]["agent_name"] == "agent-1"
        assert stats[0]["count"] == 10
        
        # Check SQL uses aggregation
        call_args = mock_db.fetch_all.call_args
        assert "GROUP BY" in call_args[0][0]
        assert "COUNT(" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_delete_old_metrics(self):
        """Test deleting old metrics."""
        mock_db = AsyncMock()
        
        with patch('lib.services.metrics_service.get_db_service', return_value=mock_db):
            service = MetricsService()
            cutoff_date = datetime(2024, 1, 1)
            
            await service.delete_old_metrics(cutoff_date)
        
        # Check DELETE query
        call_args = mock_db.execute.call_args
        assert "DELETE FROM" in call_args[0][0]
        assert "WHERE timestamp <" in call_args[0][0]
        assert call_args[1]["cutoff_date"] == cutoff_date


class TestMetricsServiceEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_store_metrics_with_complex_metrics_data(self):
        """Test storing metrics with complex JSON data."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {"id": 789}
        
        with patch('lib.services.metrics_service.get_db_service', return_value=mock_db):
            service = MetricsService()
            
            complex_metrics = {
                "execution_time": 3.14,
                "tokens": {"input": 50, "output": 75},
                "model_info": {
                    "provider": "anthropic",
                    "model": "claude-3",
                    "temperature": 0.7
                },
                "success": True,
                "error": None
            }
            
            result_id = await service.store_metrics(
                timestamp=datetime.now(),
                agent_name="complex-agent",
                execution_type="complex",
                metrics=complex_metrics
            )
        
        assert result_id == 789
        
        # Ensure metrics data was passed correctly
        call_args = mock_db.fetch_one.call_args
        stored_metrics = call_args[1]["metrics"]
        assert stored_metrics == complex_metrics
    
    @pytest.mark.asyncio
    async def test_get_metrics_empty_result(self):
        """Test getting metrics when no results found."""
        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = []
        
        with patch('lib.services.metrics_service.get_db_service', return_value=mock_db):
            service = MetricsService()
            
            metrics = await service.get_metrics_by_agent("non-existent-agent")
        
        assert metrics == []
    
    @pytest.mark.asyncio
    async def test_store_metrics_database_error(self):
        """Test storing metrics when database error occurs."""
        mock_db = AsyncMock()
        mock_db.fetch_one.side_effect = Exception("Database connection failed")
        
        with patch('lib.services.metrics_service.get_db_service', return_value=mock_db):
            service = MetricsService()
            
            with pytest.raises(Exception, match="Database connection failed"):
                await service.store_metrics(
                    timestamp=datetime.now(),
                    agent_name="error-agent",
                    execution_type="error",
                    metrics={"error": True}
                )
    
    @pytest.mark.asyncio
    async def test_get_metrics_with_limit(self):
        """Test getting metrics with result limit."""
        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = []
        
        with patch('lib.services.metrics_service.get_db_service', return_value=mock_db):
            service = MetricsService()
            
            metrics = await service.get_metrics_by_agent("test-agent", limit=100)
        
        # Check LIMIT clause in query
        call_args = mock_db.fetch_all.call_args
        assert "LIMIT" in call_args[0][0]
        assert call_args[1]["limit"] == 100