# MCP Connection Pooling System

This document provides comprehensive documentation for the production-ready MCP (Model Context Protocol) connection pooling system implemented in Genie Agents.

## Overview

The MCP connection pooling system provides enterprise-grade reliability, performance monitoring, and fault tolerance for MCP server connections. It includes:

- **Connection Pooling**: Efficient connection reuse with configurable pool sizes
- **Health Monitoring**: Automated health checks with circuit breaker patterns
- **Metrics Collection**: Comprehensive metrics for monitoring and observability
- **Configuration Management**: Flexible configuration via environment variables and YAML
- **Fault Tolerance**: Circuit breakers, retries, and graceful degradation

## Architecture

The system follows the project's dependency injection patterns and clean architecture:

```
MCPConnectionManager (Global Manager)
├── MCPConnectionPool (Per-Server Pools)
│   ├── PooledConnection (Individual Connections)
│   ├── CircuitBreaker (Fault Tolerance)
│   └── HealthCheck (Connection Monitoring)
├── MCPMetricsCollector (Metrics & Analytics)
└── MCPManagerConfig (Configuration Management)
```

## Quick Start

### Basic Usage

```python
from core.mcp import (
    get_mcp_connection_manager, 
    create_pooled_mcp_tools,
    load_mcp_config
)

# Option 1: Use pooled tools directly (recommended)
pooled_tools = create_pooled_mcp_tools("zen-server")

# Use in agent configuration
agent = Agent(
    name="My Agent",
    tools=[pooled_tools],
    # ... other config
)

# Option 2: Use connection manager directly
async def example():
    manager = await get_mcp_connection_manager()
    
    async with await manager.get_mcp_tools("zen-server") as tools:
        result = tools.call_tool("some_tool", {"param": "value"})
        return result
```

### Integration with Agent Factory

The system integrates seamlessly with the existing `AgentVersionFactory`:

```python
# In agent config.yaml
tools:
  - "mcp.zen-server"
  - "mcp.whatsapp-notifications"

# The factory automatically creates pooled connections
agent = create_versioned_agent("my-agent", version=1)
```

## Configuration

### Environment Variables

Configure the system via environment variables:

```bash
# Global MCP settings
MCP_LOG_LEVEL=info
MCP_ENABLE_METRICS=true
MCP_MAX_TOTAL_CONNECTIONS=100
MCP_CLEANUP_INTERVAL=300

# Pool configuration
MCP_DEFAULT_MIN_CONNECTIONS=2
MCP_DEFAULT_MAX_CONNECTIONS=10
MCP_CONNECTION_TIMEOUT=30
MCP_HEALTH_CHECK_INTERVAL=60

# Circuit breaker settings
MCP_ENABLE_CIRCUIT_BREAKERS=true
MCP_CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
MCP_CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# Metrics and monitoring
MCP_DETAILED_METRICS=false
MCP_METRICS_INTERVAL=60

# Development/testing
MCP_ENABLE_MOCKS=false
MCP_SINGLE_CONNECTION=false
MCP_DISABLE_HEALTH_CHECKS=false
```

### Programmatic Configuration

```python
from core.mcp import (
    MCPManagerConfig, PoolConfig, ServerSpecificConfig,
    HealthCheckConfig, CircuitBreakerConfig
)

# Create custom pool configuration
pool_config = PoolConfig(
    min_connections=1,
    max_connections=5,
    max_idle_time=300.0,
    connection_timeout=30.0,
    health_check=HealthCheckConfig(
        enabled=True,
        interval_seconds=60.0,
        failure_threshold=3
    ),
    circuit_breaker=CircuitBreakerConfig(
        enabled=True,
        failure_threshold=5,
        recovery_timeout=60.0
    )
)

# Create server-specific configuration
server_config = ServerSpecificConfig(
    server_name="high-priority-server",
    pool_config=pool_config,
    priority=10,
    tags=["production", "critical"],
    max_concurrent_requests=50
)

# Create manager configuration
manager_config = MCPManagerConfig()
manager_config.add_server_config(server_config)

# Use custom configuration
from core.mcp import MCPConnectionManager
manager = MCPConnectionManager(manager_config=manager_config)
```

## Metrics and Monitoring

### Accessing Metrics

```python
from core.mcp import get_metrics_collector, get_mcp_connection_manager

# Get comprehensive metrics
metrics_collector = get_metrics_collector()
all_metrics = metrics_collector.get_all_metrics()

# Get health summary
health_summary = metrics_collector.get_health_summary()
print(f"Overall Status: {health_summary['overall_status']}")
print(f"Healthy Servers: {health_summary['healthy_servers']}")

# Get server-specific metrics
server_metrics = metrics_collector.get_server_metrics("zen-server")

# Get legacy pool metrics (backward compatibility)
manager = await get_mcp_connection_manager()
pool_metrics = manager.get_pool_metrics("zen-server")
```

### Metrics Export

```python
# Export metrics in JSON format
json_metrics = metrics_collector.export_metrics("json")

# Export metrics in Prometheus format
prometheus_metrics = metrics_collector.export_metrics("prometheus")

# Add custom metric callback
def custom_metrics_handler(metrics):
    # Send to external monitoring system
    pass

metrics_collector.add_metric_callback(custom_metrics_handler)
```

### Available Metrics

The system collects comprehensive metrics:

#### Connection Pool Metrics
- **Connection Counts**: Total, active, idle, failed connections
- **Lifecycle Events**: Connections created, destroyed, borrowed, returned
- **Pool Performance**: Hit ratio, miss ratio, utilization percentage
- **Timing Metrics**: Connection acquisition time, creation time, health check time

#### Health Metrics
- **Health Checks**: Performed, failed, consecutive failures
- **Circuit Breaker**: State, trip count, failure count
- **Error Tracking**: Connection errors, timeout errors, validation errors

#### Global Metrics
- **System Overview**: Total servers, connections, requests, errors
- **Health Summary**: Overall health status, server health distribution

## Error Handling

The system provides comprehensive error handling with specific exception types:

```python
from core.mcp import (
    MCPConnectionError, MCPPoolExhaustedException,
    CircuitBreakerOpenError, MCPTimeoutError,
    MCPHealthCheckError, MCPValidationError
)

try:
    async with await manager.get_mcp_tools("server") as tools:
        result = tools.call_tool("my_tool", params)
except CircuitBreakerOpenError:
    # Circuit breaker is protecting against failures
    logger.warning("Circuit breaker open, falling back to alternative")
except MCPPoolExhaustedException:
    # All connections are in use
    logger.error("Connection pool exhausted")
except MCPTimeoutError:
    # Operation timed out
    logger.error("Operation timed out")
except MCPConnectionError as e:
    # General connection error
    logger.error(f"Connection error: {e}")
```

## Health Monitoring

### Circuit Breaker

The circuit breaker prevents cascading failures:

```python
# Circuit breaker states:
# - CLOSED: Normal operation
# - OPEN: Blocking requests due to failures  
# - HALF_OPEN: Testing if service has recovered

# Monitor circuit breaker state
manager = await get_mcp_connection_manager()
pool = manager.pools["server-name"]
cb_state = pool.circuit_breaker.state
cb_stats = pool.circuit_breaker.get_stats()

# Force circuit breaker state (for testing)
pool.circuit_breaker.force_open()
pool.circuit_breaker.force_close()
pool.circuit_breaker.reset()
```

### Health Checks

Automated health monitoring ensures connection reliability:

```python
# Health check configuration
health_config = HealthCheckConfig(
    enabled=True,
    interval_seconds=60.0,      # Check every minute
    timeout_seconds=10.0,       # 10 second timeout
    failure_threshold=3,        # Open circuit after 3 failures
    success_threshold=2,        # Close circuit after 2 successes
    check_method="list_tools"   # Method to use for health check
)
```

## Performance Tuning

### Pool Sizing

Configure pool sizes based on workload:

```python
# For high-throughput applications
high_throughput_config = PoolConfig(
    min_connections=5,
    max_connections=20,
    connection_timeout=10.0,
    max_idle_time=180.0
)

# For low-latency applications
low_latency_config = PoolConfig(
    min_connections=10,
    max_connections=15,
    connection_timeout=5.0,
    validate_on_acquire=True
)

# For resource-constrained environments
resource_constrained_config = PoolConfig(
    min_connections=1,
    max_connections=3,
    max_idle_time=600.0,
    cleanup_interval=120.0
)
```

### Monitoring and Alerting

Set up monitoring for key metrics:

```python
# Set up metric thresholds
def setup_monitoring():
    collector = get_metrics_collector()
    
    def alert_handler(metrics):
        for server_name, server_metrics in metrics['servers'].items():
            # Check pool utilization
            utilization = server_metrics['pool_performance']['utilization_percent']
            if utilization > 90:
                send_alert(f"High pool utilization: {server_name} at {utilization}%")
            
            # Check error rate
            error_rate = server_metrics['health']['error_rate_percent']
            if error_rate > 5:
                send_alert(f"High error rate: {server_name} at {error_rate}%")
            
            # Check circuit breaker state
            if server_metrics['circuit_breaker']['open']:
                send_alert(f"Circuit breaker open: {server_name}")
    
    collector.add_metric_callback(alert_handler)
```

## Testing

### Mock Servers

Enable mock servers for testing:

```python
# Set environment variable
os.environ['MCP_ENABLE_MOCKS'] = 'true'

# Or in configuration
settings = MCPSettings(enable_mock_servers=True)
```

### Single Connection Mode

Force single connection for debugging:

```python
# Set environment variable
os.environ['MCP_SINGLE_CONNECTION'] = 'true'

# Or in configuration
settings = MCPSettings(force_single_connection=True)
```

### Disable Health Checks

Disable health checks for testing:

```python
# Set environment variable
os.environ['MCP_DISABLE_HEALTH_CHECKS'] = 'true'

# Or in configuration
settings = MCPSettings(disable_health_checks=True)
```

## Migration Guide

### From Direct MCPTools

Replace direct MCPTools usage:

```python
# Before
from agno.tools.mcp import MCPTools
tools = MCPTools(command="server-command", args=["--param", "value"])

# After
from core.mcp import create_pooled_mcp_tools
tools = create_pooled_mcp_tools("server-name")
```

### From Legacy MCP Integration

Update agent configurations:

```yaml
# Before (in config.yaml)
tools:
  - "mcp_direct_tool"

# After
tools:
  - "mcp.server-name"
```

### Backward Compatibility

The system maintains backward compatibility:

- Legacy `get_mcp_tools()` method still works
- Existing agent configurations continue to function
- Gradual migration path available

## Best Practices

### Configuration
- Use environment variables for deployment-specific settings
- Use YAML config files for server-specific settings
- Set appropriate pool sizes based on workload
- Enable health checks in production
- Configure circuit breakers for fault tolerance

### Monitoring
- Monitor pool utilization and error rates
- Set up alerts for circuit breaker trips
- Export metrics to external monitoring systems
- Review health summaries regularly

### Performance
- Use pooled tools instead of direct connections
- Configure appropriate timeouts
- Monitor connection acquisition times
- Tune pool sizes based on metrics

### Error Handling
- Handle specific exception types appropriately
- Implement fallback strategies for failures
- Log errors with sufficient context
- Monitor error patterns and trends

## Troubleshooting

### Common Issues

1. **Pool Exhaustion**
   - Increase `max_connections`
   - Check for connection leaks
   - Monitor acquisition patterns

2. **Circuit Breaker Trips**
   - Check server health
   - Review failure thresholds
   - Monitor error logs

3. **High Latency**
   - Increase `min_connections`
   - Reduce health check intervals
   - Monitor timing metrics

4. **Memory Usage**
   - Check `max_idle_time` settings
   - Monitor connection lifecycle
   - Review cleanup intervals

### Debug Commands

```python
# Get detailed pool state
pool_metrics = manager.get_pool_metrics()
print(json.dumps(pool_metrics, indent=2))

# Check health status
health = metrics_collector.get_health_summary()
print(f"Health: {health}")

# Reset metrics for troubleshooting
metrics_collector.reset_metrics()

# Force circuit breaker state
pool.circuit_breaker.force_close()
```

This comprehensive MCP connection pooling system provides enterprise-grade reliability and monitoring for the Genie Agents platform while maintaining full backward compatibility with existing code.