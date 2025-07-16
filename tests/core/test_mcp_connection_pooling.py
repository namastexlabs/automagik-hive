"""
Tests for MCP Connection Pooling System

Comprehensive test suite covering connection pool functionality,
health monitoring, circuit breaker behavior, and error handling.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from core.mcp.connection_manager import (
    MCPConnectionManager, MCPConnectionPool, PoolConfig, 
    PooledConnection, ConnectionState
)
from core.mcp.pooled_tools import PooledMCPTools, MCPToolsFactory
from core.mcp.catalog import MCPCatalog, MCPServerConfig
from core.mcp.exceptions import MCPConnectionError, MCPPoolExhaustedException
from core.utils.circuit_breaker import CircuitBreaker, CircuitBreakerState


class TestMCPConnectionPool:
    """Test suite for MCPConnectionPool"""
    
    @pytest.fixture
    def pool_config(self):
        """Basic pool configuration for testing"""
        return PoolConfig(
            min_connections=2,
            max_connections=5,
            max_idle_time=60.0,
            connection_timeout=10.0,
            health_check_interval=30.0
        )
    
    @pytest.fixture
    def server_config(self):
        """Mock server configuration"""
        return MCPServerConfig(
            name="test_server",
            type="command",
            command="test_command",
            args=["--arg1", "value1"],
            env={"TEST_ENV": "test_value"}
        )
    
    @pytest.fixture
    async def connection_pool(self, server_config, pool_config):
        """Create a connection pool for testing"""
        pool = MCPConnectionPool("test_server", server_config, pool_config)
        yield pool
        await pool.stop()
    
    @pytest.mark.asyncio
    async def test_pool_initialization(self, connection_pool):
        """Test pool initialization and minimum connections"""
        with patch('core.mcp.connection_manager.MCPTools') as mock_mcp_tools:
            mock_mcp_tools.return_value = Mock()
            
            await connection_pool.start()
            
            # Should create minimum connections
            assert len(connection_pool.connections) >= connection_pool.config.min_connections
            assert connection_pool.available_connections.qsize() >= connection_pool.config.min_connections
    
    @pytest.mark.asyncio
    async def test_connection_acquisition_and_release(self, connection_pool):
        """Test acquiring and releasing connections"""
        with patch('core.mcp.connection_manager.MCPTools') as mock_mcp_tools:
            mock_mcp_tools.return_value = Mock()
            
            await connection_pool.start()
            
            # Acquire connection
            async with connection_pool.get_connection() as connection:
                assert isinstance(connection, PooledConnection)
                assert connection.state == ConnectionState.ACTIVE
                assert connection.use_count > 0
            
            # Connection should be back to idle state
            assert connection.state == ConnectionState.IDLE
    
    @pytest.mark.asyncio
    async def test_pool_exhaustion(self, connection_pool):
        """Test behavior when pool is exhausted"""
        with patch('core.mcp.connection_manager.MCPTools') as mock_mcp_tools:
            mock_mcp_tools.return_value = Mock()
            
            await connection_pool.start()
            
            # Acquire all connections
            connections = []
            for _ in range(connection_pool.config.max_connections):
                conn = await connection_pool._acquire_connection()
                connections.append(conn)
            
            # Try to acquire one more - should timeout
            with pytest.raises(MCPPoolExhaustedException):
                await connection_pool._acquire_connection()
            
            # Release one connection
            await connection_pool._release_connection(connections[0])
            
            # Should be able to acquire again
            conn = await connection_pool._acquire_connection()
            assert conn is not None
    
    @pytest.mark.asyncio
    async def test_connection_health_checks(self, connection_pool):
        """Test connection health checking"""
        with patch('core.mcp.connection_manager.MCPTools') as mock_mcp_tools:
            mock_tools = Mock()
            mock_tools.list_tools.return_value = []
            mock_mcp_tools.return_value = mock_tools
            
            await connection_pool.start()
            
            # Perform health checks
            await connection_pool._perform_health_checks()
            
            # All connections should remain healthy
            assert all(conn.is_healthy() for conn in connection_pool.connections.values())
    
    @pytest.mark.asyncio
    async def test_expired_connection_cleanup(self, connection_pool):
        """Test cleanup of expired connections"""
        with patch('core.mcp.connection_manager.MCPTools') as mock_mcp_tools:
            mock_mcp_tools.return_value = Mock()
            
            # Use short idle time for testing
            connection_pool.config.max_idle_time = 0.1
            
            await connection_pool.start()
            
            initial_count = len(connection_pool.connections)
            
            # Wait for connections to expire
            await asyncio.sleep(0.2)
            
            # Trigger cleanup
            await connection_pool._cleanup_expired_connections()
            
            # Should maintain minimum connections
            assert len(connection_pool.connections) >= connection_pool.config.min_connections
    
    def test_circuit_breaker_integration(self, connection_pool):
        """Test circuit breaker functionality"""
        # Test initial state
        assert connection_pool.circuit_breaker.state == CircuitBreakerState.CLOSED
        
        # Simulate failures
        for _ in range(connection_pool.config.circuit_breaker_failure_threshold):
            connection_pool.circuit_breaker.record_failure()
        
        # Circuit breaker should be open
        assert connection_pool.circuit_breaker.state == CircuitBreakerState.OPEN
        assert connection_pool.circuit_breaker.is_open()
    
    def test_pool_metrics(self, connection_pool):
        """Test pool metrics collection"""
        metrics = connection_pool.get_metrics()
        
        expected_keys = [
            'server_name', 'total_connections', 'available_connections',
            'circuit_breaker_state', 'total_connections_created',
            'pool_hits', 'pool_misses', 'connection_errors'
        ]
        
        for key in expected_keys:
            assert key in metrics


class TestMCPConnectionManager:
    """Test suite for MCPConnectionManager"""
    
    @pytest.fixture
    def mock_catalog(self):
        """Mock MCP catalog"""
        catalog = Mock(spec=MCPCatalog)
        catalog.list_servers.return_value = ["server1", "server2"]
        catalog.get_server_config.return_value = MCPServerConfig(
            name="test_server",
            type="command",
            command="test_command"
        )
        return catalog
    
    @pytest.fixture
    async def connection_manager(self, mock_catalog):
        """Create a connection manager for testing"""
        manager = MCPConnectionManager(mock_catalog)
        yield manager
        await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self, connection_manager, mock_catalog):
        """Test connection manager initialization"""
        with patch('core.mcp.connection_manager.MCPConnectionPool') as mock_pool_class:
            mock_pool = AsyncMock()
            mock_pool_class.return_value = mock_pool
            
            await connection_manager.initialize()
            
            assert connection_manager._initialized
            assert len(connection_manager.pools) == len(mock_catalog.list_servers())
    
    @pytest.mark.asyncio
    async def test_get_mcp_tools(self, connection_manager):
        """Test getting MCP tools from manager"""
        with patch('core.mcp.connection_manager.MCPConnectionPool') as mock_pool_class:
            mock_pool = AsyncMock()
            mock_connection = Mock()
            mock_connection.mcp_tools = Mock()
            
            async def mock_get_connection():
                class MockAsyncContext:
                    async def __aenter__(self):
                        return mock_connection
                    async def __aexit__(self, *args):
                        pass
                return MockAsyncContext()
            
            mock_pool.get_connection = mock_get_connection
            mock_pool_class.return_value = mock_pool
            
            await connection_manager.initialize()
            
            async with await connection_manager.get_mcp_tools("server1") as tools:
                assert tools == mock_connection.mcp_tools
    
    @pytest.mark.asyncio
    async def test_manager_metrics(self, connection_manager):
        """Test manager metrics collection"""
        await connection_manager.initialize()
        
        metrics = connection_manager.get_pool_metrics()
        
        assert 'global_metrics' in metrics
        assert 'pools' in metrics
        assert isinstance(metrics['global_metrics'], dict)
        assert isinstance(metrics['pools'], dict)
    
    @pytest.mark.asyncio
    async def test_server_configuration(self, connection_manager):
        """Test server-specific pool configuration"""
        custom_config = PoolConfig(min_connections=5, max_connections=20)
        
        connection_manager.configure_server_pool("server1", custom_config)
        
        assert "server1" in connection_manager.server_configs
        assert connection_manager.server_configs["server1"] == custom_config


class TestPooledMCPTools:
    """Test suite for PooledMCPTools"""
    
    @pytest.fixture
    def mock_connection_manager(self):
        """Mock connection manager"""
        manager = AsyncMock(spec=MCPConnectionManager)
        
        async def mock_get_tools(server_name):
            class MockAsyncContext:
                async def __aenter__(self):
                    mock_tools = Mock()
                    mock_tools.list_tools.return_value = []
                    mock_tools.call_tool.return_value = {"result": "success"}
                    return mock_tools
                async def __aexit__(self, *args):
                    pass
            return MockAsyncContext()
        
        manager.get_mcp_tools = mock_get_tools
        return manager
    
    @pytest.fixture
    def pooled_tools(self, mock_connection_manager):
        """Create pooled MCP tools for testing"""
        return PooledMCPTools("test_server", mock_connection_manager)
    
    @pytest.mark.asyncio
    async def test_list_tools(self, pooled_tools):
        """Test list_tools method"""
        tools = pooled_tools.list_tools()
        assert isinstance(tools, list)
    
    @pytest.mark.asyncio
    async def test_call_tool(self, pooled_tools):
        """Test call_tool method"""
        result = pooled_tools.call_tool("test_tool", {"arg": "value"})
        assert result == {"result": "success"}
    
    @pytest.mark.asyncio
    async def test_error_handling(self, pooled_tools):
        """Test error handling in pooled tools"""
        # Mock connection manager to raise error
        async def mock_error_get_tools(server_name):
            raise Exception("Connection failed")
        
        pooled_tools._connection_manager.get_mcp_tools = mock_error_get_tools
        
        with pytest.raises(MCPConnectionError):
            pooled_tools.list_tools()


class TestMCPToolsFactory:
    """Test suite for MCPToolsFactory"""
    
    @pytest.fixture
    def factory(self):
        """Create MCP tools factory"""
        return MCPToolsFactory()
    
    def test_create_pooled_tools(self, factory):
        """Test creating pooled MCP tools"""
        tools = factory.create_mcp_tools("test_server")
        
        assert isinstance(tools, PooledMCPTools)
        assert tools.server_name == "test_server"
    
    @pytest.mark.asyncio
    async def test_create_direct_tools(self, factory):
        """Test creating direct MCP tools"""
        with patch('core.mcp.pooled_tools.MCPCatalog') as mock_catalog_class:
            mock_catalog = Mock()
            mock_catalog.get_server_config.return_value = MCPServerConfig(
                name="test_server",
                type="command",
                command="test_command"
            )
            mock_catalog_class.return_value = mock_catalog
            
            with patch('core.mcp.pooled_tools.MCPTools') as mock_mcp_tools:
                mock_tools = Mock()
                mock_mcp_tools.return_value = mock_tools
                
                tools = await factory.create_direct_mcp_tools("test_server")
                assert tools == mock_tools


class TestIntegration:
    """Integration tests for the complete MCP pooling system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete workflow from factory to tool execution"""
        with patch('core.mcp.connection_manager.MCPTools') as mock_mcp_tools:
            # Setup mock
            mock_tools = Mock()
            mock_tools.list_tools.return_value = [{"name": "test_tool"}]
            mock_tools.call_tool.return_value = {"result": "success"}
            mock_mcp_tools.return_value = mock_tools
            
            # Create system components
            catalog = Mock(spec=MCPCatalog)
            catalog.list_servers.return_value = ["test_server"]
            catalog.has_server.return_value = True
            catalog.get_server_config.return_value = MCPServerConfig(
                name="test_server",
                type="command",
                command="test_command"
            )
            
            # Initialize connection manager
            manager = MCPConnectionManager(catalog)
            await manager.initialize()
            
            try:
                # Create pooled tools
                factory = MCPToolsFactory(manager)
                pooled_tools = factory.create_mcp_tools("test_server")
                
                # Test tool operations
                tools_list = pooled_tools.list_tools()
                assert len(tools_list) == 1
                assert tools_list[0]["name"] == "test_tool"
                
                result = pooled_tools.call_tool("test_tool", {"arg": "value"})
                assert result == {"result": "success"}
                
            finally:
                await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent access to connection pools"""
        with patch('core.mcp.connection_manager.MCPTools') as mock_mcp_tools:
            mock_tools = Mock()
            mock_tools.call_tool.return_value = {"result": "success"}
            mock_mcp_tools.return_value = mock_tools
            
            catalog = Mock(spec=MCPCatalog)
            catalog.list_servers.return_value = ["test_server"]
            catalog.has_server.return_value = True
            catalog.get_server_config.return_value = MCPServerConfig(
                name="test_server",
                type="command",
                command="test_command"
            )
            
            manager = MCPConnectionManager(catalog)
            await manager.initialize()
            
            try:
                # Create multiple pooled tools instances
                factory = MCPToolsFactory(manager)
                tools_instances = [factory.create_mcp_tools("test_server") for _ in range(10)]
                
                # Execute operations concurrently
                async def call_tool(tools):
                    return tools.call_tool("test_tool", {"id": id(tools)})
                
                tasks = [call_tool(tools) for tools in tools_instances]
                results = await asyncio.gather(*tasks)
                
                # All operations should succeed
                assert len(results) == 10
                assert all(result == {"result": "success"} for result in results)
                
            finally:
                await manager.shutdown()


# Performance tests
class TestPerformance:
    """Performance tests for MCP connection pooling"""
    
    @pytest.mark.asyncio
    async def test_pool_performance_under_load(self):
        """Test pool performance under high load"""
        with patch('core.mcp.connection_manager.MCPTools') as mock_mcp_tools:
            mock_tools = Mock()
            mock_tools.call_tool.return_value = {"result": "success"}
            mock_mcp_tools.return_value = mock_tools
            
            # Configure pool for performance testing
            pool_config = PoolConfig(
                min_connections=5,
                max_connections=20,
                connection_timeout=1.0
            )
            
            server_config = MCPServerConfig(
                name="perf_server",
                type="command",
                command="test_command"
            )
            
            pool = MCPConnectionPool("perf_server", server_config, pool_config)
            await pool.start()
            
            try:
                # Measure performance
                start_time = time.time()
                
                async def perform_operation():
                    async with pool.get_connection() as connection:
                        return connection.mcp_tools.call_tool("test", {})
                
                # Execute 100 concurrent operations
                tasks = [perform_operation() for _ in range(100)]
                results = await asyncio.gather(*tasks)
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Performance assertions
                assert len(results) == 100
                assert duration < 5.0  # Should complete within 5 seconds
                
                # Check pool metrics
                metrics = pool.get_metrics()
                assert metrics['pool_hits'] > 0  # Should have cache hits
                
            finally:
                await pool.stop()