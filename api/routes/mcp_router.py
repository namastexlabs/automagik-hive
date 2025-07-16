"""
MCP Connection Management API Routes

Provides REST endpoints for monitoring and managing MCP connection pools.
Integrates with the existing monitoring system and provides real-time visibility.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
import logging

from core.mcp.connection_manager import get_mcp_connection_manager, MCPConnectionManager
from api.monitoring.mcp_monitor import get_mcp_health_monitor, MCPHealthMonitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/mcp", tags=["MCP Management"])


@router.get("/status")
async def get_mcp_status(
    manager: MCPConnectionManager = Depends(get_mcp_connection_manager)
) -> Dict[str, Any]:
    """
    Get overall MCP system status and health summary.
    
    Returns:
        System status with pool counts, health metrics, and recent alerts
    """
    try:
        health_monitor = await get_mcp_health_monitor()
        health_summary = health_monitor.get_health_summary()
        
        return {
            "status": "ok",
            "mcp_health": health_summary,
            "available_servers": manager.list_available_servers(),
            "timestamp": health_summary.get("last_check")
        }
    except Exception as e:
        logger.error(f"Error getting MCP status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting MCP status: {e}")


@router.get("/pools")
async def list_connection_pools(
    manager: MCPConnectionManager = Depends(get_mcp_connection_manager)
) -> Dict[str, Any]:
    """
    List all MCP connection pools with their current metrics.
    
    Returns:
        Dictionary of pool metrics by server name
    """
    try:
        metrics = manager.get_pool_metrics()
        return {
            "status": "ok",
            "pools": metrics.get("pools", {}),
            "global_metrics": metrics.get("global_metrics", {}),
            "total_pools": len(metrics.get("pools", {}))
        }
    except Exception as e:
        logger.error(f"Error listing connection pools: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing pools: {e}")


@router.get("/pools/{server_name}")
async def get_pool_details(
    server_name: str,
    manager: MCPConnectionManager = Depends(get_mcp_connection_manager)
) -> Dict[str, Any]:
    """
    Get detailed metrics and health information for a specific pool.
    
    Args:
        server_name: Name of the MCP server
        
    Returns:
        Detailed pool metrics and health history
    """
    try:
        # Get pool metrics
        pool_metrics = manager.get_pool_metrics(server_name)
        
        if not pool_metrics:
            raise HTTPException(status_code=404, detail=f"Pool {server_name} not found")
        
        # Get health information
        health_monitor = await get_mcp_health_monitor()
        health_info = health_monitor.get_pool_health(server_name)
        
        return {
            "status": "ok",
            "server_name": server_name,
            "metrics": pool_metrics,
            "health": health_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pool details for {server_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting pool details: {e}")


@router.get("/alerts")
async def get_mcp_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity (warning, critical)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of alerts to return")
) -> Dict[str, Any]:
    """
    Get recent MCP alerts.
    
    Args:
        severity: Optional severity filter (warning, critical)
        limit: Maximum number of alerts to return
        
    Returns:
        List of recent alerts with details
    """
    try:
        health_monitor = await get_mcp_health_monitor()
        alerts = health_monitor.get_recent_alerts(severity=severity, limit=limit)
        
        return {
            "status": "ok",
            "alerts": alerts,
            "total_alerts": len(alerts),
            "filtered_by_severity": severity
        }
    except Exception as e:
        logger.error(f"Error getting MCP alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting alerts: {e}")


@router.get("/servers")
async def list_available_servers(
    manager: MCPConnectionManager = Depends(get_mcp_connection_manager)
) -> Dict[str, Any]:
    """
    List all available MCP servers.
    
    Returns:
        List of available server names and their basic information
    """
    try:
        servers = manager.list_available_servers()
        
        # Get additional server information
        server_details = {}
        for server_name in servers:
            try:
                pool_metrics = manager.get_pool_metrics(server_name)
                server_details[server_name] = {
                    "available": True,
                    "total_connections": pool_metrics.get("total_connections", 0),
                    "available_connections": pool_metrics.get("available_connections", 0),
                    "circuit_breaker_state": pool_metrics.get("circuit_breaker_state", "unknown")
                }
            except Exception as e:
                server_details[server_name] = {
                    "available": False,
                    "error": str(e)
                }
        
        return {
            "status": "ok",
            "servers": servers,
            "server_details": server_details,
            "total_servers": len(servers)
        }
    except Exception as e:
        logger.error(f"Error listing available servers: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing servers: {e}")


@router.post("/pools/{server_name}/health-check")
async def trigger_health_check(
    server_name: str,
    manager: MCPConnectionManager = Depends(get_mcp_connection_manager)
) -> Dict[str, Any]:
    """
    Trigger a manual health check for a specific pool.
    
    Args:
        server_name: Name of the MCP server
        
    Returns:
        Health check results
    """
    try:
        # Verify pool exists
        pool_metrics = manager.get_pool_metrics(server_name)
        if not pool_metrics:
            raise HTTPException(status_code=404, detail=f"Pool {server_name} not found")
        
        # Trigger health check via monitor
        health_monitor = await get_mcp_health_monitor()
        
        # Force a health check by getting current health
        health_info = health_monitor.get_pool_health(server_name)
        
        return {
            "status": "ok",
            "server_name": server_name,
            "health_check_triggered": True,
            "current_health": health_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering health check for {server_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error triggering health check: {e}")


@router.get("/metrics/summary")
async def get_metrics_summary(
    manager: MCPConnectionManager = Depends(get_mcp_connection_manager)
) -> Dict[str, Any]:
    """
    Get aggregated metrics summary across all pools.
    
    Returns:
        Aggregated metrics and performance statistics
    """
    try:
        all_metrics = manager.get_pool_metrics()
        pools = all_metrics.get("pools", {})
        global_metrics = all_metrics.get("global_metrics", {})
        
        # Calculate aggregated statistics
        total_connections = sum(pool.get("total_connections", 0) for pool in pools.values())
        total_available = sum(pool.get("available_connections", 0) for pool in pools.values())
        total_hits = sum(pool.get("pool_hits", 0) for pool in pools.values())
        total_misses = sum(pool.get("pool_misses", 0) for pool in pools.values())
        total_errors = sum(pool.get("connection_errors", 0) for pool in pools.values())
        
        # Calculate rates
        hit_rate = total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0
        utilization = 1 - (total_available / total_connections) if total_connections > 0 else 0
        
        # Count circuit breaker states
        circuit_breaker_states = {}
        for pool in pools.values():
            state = pool.get("circuit_breaker_state", "unknown")
            circuit_breaker_states[state] = circuit_breaker_states.get(state, 0) + 1
        
        return {
            "status": "ok",
            "summary": {
                "total_pools": len(pools),
                "total_connections": total_connections,
                "total_available_connections": total_available,
                "overall_utilization": utilization,
                "cache_hit_rate": hit_rate,
                "total_errors": total_errors,
                "circuit_breaker_states": circuit_breaker_states
            },
            "global_metrics": global_metrics,
            "performance": {
                "pool_hits": total_hits,
                "pool_misses": total_misses,
                "hit_rate_percentage": hit_rate * 100,
                "utilization_percentage": utilization * 100
            }
        }
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting metrics summary: {e}")


@router.get("/config")
async def get_mcp_configuration() -> Dict[str, Any]:
    """
    Get MCP system configuration information.
    
    Returns:
        Configuration details and available servers from catalog
    """
    try:
        from core.mcp.catalog import MCPCatalog
        
        catalog = MCPCatalog()
        servers = catalog.list_servers()
        
        server_configs = {}
        for server_name in servers:
            try:
                server_info = catalog.get_server_info(server_name)
                server_configs[server_name] = {
                    "type": server_info.get("type"),
                    "is_sse_server": server_info.get("is_sse_server"),
                    "is_command_server": server_info.get("is_command_server"),
                    "url": server_info.get("url"),
                    "command": server_info.get("command")
                }
            except Exception as e:
                server_configs[server_name] = {"error": str(e)}
        
        return {
            "status": "ok",
            "catalog_servers": servers,
            "server_configurations": server_configs,
            "total_configured_servers": len(servers)
        }
    except Exception as e:
        logger.error(f"Error getting MCP configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting configuration: {e}")


# Add router to the main application
def register_mcp_routes(app):
    """Register MCP routes with the FastAPI application"""
    app.include_router(router)