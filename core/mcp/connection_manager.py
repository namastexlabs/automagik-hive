"""
MCP Connection Manager with Pooling and Health Monitoring

Provides connection pooling, health monitoring, and circuit breaker patterns
for MCP server connections. Designed for enterprise-grade reliability and performance.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, Set, AsyncContextManager
from dataclasses import dataclass, field
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from enum import Enum
import weakref

from agno.tools.mcp import MCPTools

from .catalog import MCPCatalog, MCPServerConfig
from .exceptions import MCPConnectionError, MCPPoolExhaustedException, CircuitBreakerOpenError
from .config import PoolConfig, MCPSettings, get_mcp_settings
from .metrics import get_metrics_collector
from ..utils.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection state enumeration"""
    IDLE = "idle"
    ACTIVE = "active"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


# Note: PoolConfig is now imported from .config module


@dataclass
class PooledConnection:
    """Wrapper for pooled MCP connections"""
    connection_id: str
    mcp_tools: MCPTools
    server_name: str
    created_at: float
    last_used: float
    use_count: int = 0
    state: ConnectionState = ConnectionState.IDLE
    
    def mark_used(self):
        """Mark connection as recently used"""
        self.last_used = time.time()
        self.use_count += 1
    
    def is_expired(self, max_idle_time: float) -> bool:
        """Check if connection has exceeded idle time"""
        return (time.time() - self.last_used) > max_idle_time
    
    def is_healthy(self) -> bool:
        """Check if connection is in a healthy state"""
        return self.state in (ConnectionState.IDLE, ConnectionState.ACTIVE)


class MCPConnectionPool:
    """Connection pool for a specific MCP server"""
    
    def __init__(self, server_name: str, server_config: MCPServerConfig, 
                 pool_config: PoolConfig = None):
        self.server_name = server_name
        self.server_config = server_config
        self.config = pool_config or get_mcp_settings().get_pool_config()
        
        # Connection management
        self.connections: Dict[str, PooledConnection] = {}
        self.available_connections: asyncio.Queue = asyncio.Queue()
        self.connection_counter = 0
        self.lock = asyncio.Lock()
        
        # Health monitoring
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.failure_threshold,
            recovery_timeout=self.config.recovery_timeout
        )
        
        # Metrics integration
        self.metrics_collector = get_metrics_collector()
        
        # Simple metrics tracking
        self.metrics = {
            'connections_created': 0,
            'connections_destroyed': 0,
            'active_connections': 0,
            'pool_hits': 0,
            'pool_misses': 0
        }
        
        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown = False
    
    async def start(self):
        """Start the connection pool"""
        logger.info(f"Starting MCP connection pool for {self.server_name}")
        
        # Create minimum connections
        for _ in range(self.config.min_connections):
            try:
                connection = await self._create_connection()
                # Add newly created connection to available queue
                connection.state = ConnectionState.IDLE
                self.available_connections.put_nowait(connection.connection_id)
                logger.debug(f"Added connection {connection.connection_id} to available queue")
            except Exception as e:
                logger.warning(f"Failed to create initial connection for {self.server_name}: {e}")
        
        # Start background tasks
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop the connection pool and cleanup resources"""
        logger.info(f"Stopping MCP connection pool for {self.server_name}")
        self._shutdown = True
        
        # Cancel background tasks
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Close all connections
        async with self.lock:
            for connection in self.connections.values():
                try:
                    await self._close_connection(connection)
                except Exception as e:
                    logger.warning(f"Error closing connection {connection.connection_id}: {e}")
            
            self.connections.clear()
            
            # Clear queue
            while not self.available_connections.empty():
                try:
                    self.available_connections.get_nowait()
                except asyncio.QueueEmpty:
                    break
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncContextManager[PooledConnection]:
        """Get a connection from the pool with automatic return"""
        connection = None
        try:
            connection = await self._acquire_connection()
            yield connection
        finally:
            if connection:
                await self._release_connection(connection)
    
    async def _acquire_connection(self) -> PooledConnection:
        """Acquire a connection from the pool"""
        if self.circuit_breaker.is_open():
            raise CircuitBreakerOpenError(f"Circuit breaker open for {self.server_name}", self.server_name)
        
        start_time = time.time()
        
        try:
            # Try to get from available connections first
            try:
                connection_id = self.available_connections.get_nowait()
                connection = self.connections.get(connection_id)
                
                if connection and connection.is_healthy():
                    connection.state = ConnectionState.ACTIVE
                    connection.mark_used()
                    self.metrics['pool_hits'] += 1
                    
                    # Record metrics
                    acquire_time = time.time() - start_time
                    self.metrics_collector.record_connection_acquired(self.server_name)
                    
                    return connection
                else:
                    # Connection is invalid, remove it
                    if connection:
                        await self._remove_connection(connection)
            except asyncio.QueueEmpty:
                pass
            
            # No available connections, try to create new one
            self.metrics['pool_misses'] += 1
            
            async with self.lock:
                if len(self.connections) < self.config.max_connections:
                    connection = await self._create_connection()
                    connection.state = ConnectionState.ACTIVE
                    connection.mark_used()
                    
                    # Record metrics
                    acquire_time = time.time() - start_time
                    self.metrics_collector.record_connection_acquired(self.server_name)
                    
                    return connection
            
            # Pool is full, wait for available connection
            logger.warning(f"Pool exhausted for {self.server_name}, waiting for connection...")
            
            # Wait with timeout
            try:
                connection_id = await asyncio.wait_for(
                    self.available_connections.get(),
                    timeout=self.config.connection_timeout
                )
                
                connection = self.connections.get(connection_id)
                if connection and connection.is_healthy():
                    connection.state = ConnectionState.ACTIVE
                    connection.mark_used()
                    return connection
                else:
                    if connection:
                        await self._remove_connection(connection)
                    raise MCPConnectionError(f"Invalid connection retrieved for {self.server_name}")
                    
            except asyncio.TimeoutError:
                raise MCPPoolExhaustedException(f"No connections available for {self.server_name}")
        
        except Exception as e:
            self.circuit_breaker.record_failure()
            self.metrics['connection_errors'] += 1
            raise MCPConnectionError(f"Failed to acquire connection for {self.server_name}: {e}")
    
    async def _release_connection(self, connection: PooledConnection):
        """Release a connection back to the pool"""
        if connection.connection_id not in self.connections:
            # Connection was removed, don't return to pool
            return
        
        connection.state = ConnectionState.IDLE
        
        # Check if connection is still healthy
        if connection.is_healthy() and not self._shutdown:
            try:
                self.available_connections.put_nowait(connection.connection_id)
            except asyncio.QueueFull:
                # Queue is full, this shouldn't happen but handle gracefully
                logger.warning(f"Available connections queue full for {self.server_name}")
        else:
            # Connection is unhealthy, remove it
            await self._remove_connection(connection)
    
    async def _create_connection(self) -> PooledConnection:
        """Create a new MCP connection"""
        self.connection_counter += 1
        connection_id = f"{self.server_name}_{self.connection_counter}_{int(time.time())}"
        
        try:
            # Create MCPTools instance based on server type
            if self.server_config.is_sse_server:
                mcp_tools = MCPTools(
                    url=self.server_config.url,
                    transport="sse",
                    env=self.server_config.env or {}
                )
            elif self.server_config.is_command_server:
                command_parts = [self.server_config.command]
                if self.server_config.args:
                    command_parts.extend(self.server_config.args)
                
                mcp_tools = MCPTools(
                    command=" ".join(command_parts),
                    transport="stdio",
                    env=self.server_config.env or {}
                )
            else:
                raise MCPConnectionError(f"Unknown server type for {self.server_name}")
            
            connection = PooledConnection(
                connection_id=connection_id,
                mcp_tools=mcp_tools,
                server_name=self.server_name,
                created_at=time.time(),
                last_used=time.time()
            )
            
            self.connections[connection_id] = connection
            self.metrics['connections_created'] += 1
            self.metrics['active_connections'] = len(self.connections)
            
            logger.debug(f"Created new MCP connection {connection_id} for {self.server_name}")
            return connection
            
        except Exception as e:
            logger.error(f"Failed to create MCP connection for {self.server_name}: {e}")
            raise MCPConnectionError(f"Failed to create connection: {e}")
    
    async def _close_connection(self, connection: PooledConnection):
        """Close an MCP connection"""
        try:
            # MCPTools doesn't have explicit close method, let it be garbage collected
            connection.state = ConnectionState.FAILED
            logger.debug(f"Closed MCP connection {connection.connection_id}")
        except Exception as e:
            logger.warning(f"Error closing connection {connection.connection_id}: {e}")
    
    async def _remove_connection(self, connection: PooledConnection):
        """Remove a connection from the pool"""
        async with self.lock:
            if connection.connection_id in self.connections:
                await self._close_connection(connection)
                del self.connections[connection.connection_id]
                self.metrics['connections_destroyed'] += 1
                self.metrics['active_connections'] = len(self.connections)
    
    async def _health_check_loop(self):
        """Background task for health checking connections"""
        while not self._shutdown:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop for {self.server_name}: {e}")
    
    async def _cleanup_loop(self):
        """Background task for cleaning up expired connections"""
        while not self._shutdown:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._cleanup_expired_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop for {self.server_name}: {e}")
    
    async def _perform_health_checks(self):
        """Perform health checks on idle connections"""
        connections_to_check = []
        
        async with self.lock:
            for connection in self.connections.values():
                if connection.state == ConnectionState.IDLE:
                    connections_to_check.append(connection)
        
        for connection in connections_to_check:
            try:
                # Simple health check - try to access the tools
                if hasattr(connection.mcp_tools, 'list_tools'):
                    await asyncio.to_thread(lambda: list(connection.mcp_tools.list_tools()))
                else:
                    # If no list_tools method, assume healthy if connection exists
                    pass
                
                self.circuit_breaker.record_success()
                
            except Exception as e:
                logger.warning(f"Health check failed for connection {connection.connection_id}: {e}")
                self.metrics['health_check_failures'] += 1
                await self._remove_connection(connection)
    
    async def _cleanup_expired_connections(self):
        """Remove expired idle connections"""
        expired_connections = []
        
        async with self.lock:
            for connection in self.connections.values():
                if (connection.state == ConnectionState.IDLE and 
                    connection.is_expired(self.config.max_idle_time) and 
                    len(self.connections) > self.config.min_connections):
                    expired_connections.append(connection)
        
        for connection in expired_connections:
            logger.debug(f"Removing expired connection {connection.connection_id}")
            await self._remove_connection(connection)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get pool metrics"""
        return {
            'server_name': self.server_name,
            'total_connections': len(self.connections),
            'available_connections': self.available_connections.qsize(),
            'circuit_breaker_state': self.circuit_breaker.state.value,
            'circuit_breaker_failure_count': self.circuit_breaker.failure_count,
            **self.metrics
        }


class MCPConnectionManager:
    """
    Global MCP connection manager with pooling support.
    
    Manages connection pools for all MCP servers and provides dependency injection
    integration for the FastAPI application.
    """
    
    def __init__(self, mcp_catalog: MCPCatalog = None):
        self.mcp_catalog = mcp_catalog or MCPCatalog()
        self.settings = get_mcp_settings()
        
        # Connection pools by server name
        self.pools: Dict[str, MCPConnectionPool] = {}
        
        # Metrics integration
        self.metrics_collector = get_metrics_collector()
        
        # Global metrics
        self.global_metrics = {
            'pools': 0,
            'connections': 0,
            'requests': 0,
            'errors': 0
        }
        
        self._initialized = False
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize connection manager and create pools"""
        if self._initialized:
            return
        
        async with self._lock:
            if self._initialized:
                return
            
            logger.info("Initializing MCP Connection Manager")
            
            # Create pools for all available servers
            for server_name in self.mcp_catalog.list_servers():
                try:
                    await self._create_pool(server_name)
                except Exception as e:
                    logger.error(f"Failed to create pool for {server_name}: {e}")
            
            self._initialized = True
            logger.info(f"MCP Connection Manager initialized with {len(self.pools)} pools")
    
    async def shutdown(self):
        """Shutdown all connection pools"""
        logger.info("Shutting down MCP Connection Manager")
        
        # Stop all pools
        shutdown_tasks = []
        for pool in self.pools.values():
            shutdown_tasks.append(pool.stop())
        
        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        
        self.pools.clear()
        self._initialized = False
    
    async def _create_pool(self, server_name: str):
        """Create a connection pool for a specific server"""
        server_config = self.mcp_catalog.get_server_config(server_name)
        pool_config = self.settings.get_pool_config()
        
        pool = MCPConnectionPool(server_name, server_config, pool_config)
        await pool.start()
        
        self.pools[server_name] = pool
        self.global_metrics['pools'] += 1
        
        logger.info(f"Created connection pool for {server_name}")
    
    async def get_mcp_tools(self, server_name: str) -> AsyncContextManager[MCPTools]:
        """
        Get MCPTools instance from connection pool.
        
        This method maintains the same interface as the original MCPTools creation
        but uses connection pooling for better performance and reliability.
        """
        if not self._initialized:
            await self.initialize()
        
        if server_name not in self.pools:
            raise MCPConnectionError(f"No pool available for server {server_name}")
        
        pool = self.pools[server_name]
        self.global_metrics['requests'] += 1
        
        @asynccontextmanager
        async def _get_tools():
            try:
                async with pool.get_connection() as connection:
                    yield connection.mcp_tools
            except Exception as e:
                self.global_metrics['errors'] += 1
                raise
        
        return _get_tools()
    
    def configure_server_pool(self, server_name: str, pool_config: PoolConfig):
        """Configure pool settings for a specific server"""
        # For simplicity, we'll recreate the pool with new config
        if server_name in self.pools:
            # TODO: Implement pool reconfiguration if needed
            pass
    
    def get_pool_metrics(self, server_name: str = None) -> Dict[str, Any]:
        """Get metrics for specific pool or all pools"""
        if server_name:
            pool = self.pools.get(server_name)
            return pool.get_metrics() if pool else {}
        else:
            return {
                'global': self.global_metrics,
                'pools': {name: pool.get_metrics() for name, pool in self.pools.items()},
                'health': self.metrics_collector.get_metrics_summary()
            }
    
    def list_available_servers(self) -> List[str]:
        """List all available MCP servers"""
        return list(self.pools.keys())


# Global connection manager instance for dependency injection
_connection_manager: Optional[MCPConnectionManager] = None


async def get_mcp_connection_manager() -> MCPConnectionManager:
    """
    Dependency injection function for FastAPI.
    
    Returns the global MCP connection manager instance.
    """
    global _connection_manager
    
    if _connection_manager is None:
        _connection_manager = MCPConnectionManager()
        await _connection_manager.initialize()
    
    return _connection_manager


async def shutdown_mcp_connection_manager():
    """Shutdown the global connection manager"""
    global _connection_manager
    
    if _connection_manager:
        await _connection_manager.shutdown()
        _connection_manager = None