"""
MCP Connection Monitoring Integration

Integrates MCP connection pool metrics with the existing monitoring system.
Provides real-time monitoring, alerting, and analytics for MCP connections.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from .metrics_collector import metrics_collector
from ..routes.monitoring import add_monitoring_endpoint

logger = logging.getLogger(__name__)


@dataclass
class MCPAlert:
    """MCP-specific alert data structure"""
    alert_type: str
    server_name: str
    message: str
    severity: str
    timestamp: datetime
    metrics: Dict[str, Any]


class MCPHealthMonitor:
    """
    Health monitor for MCP connection pools.
    
    Integrates with the existing monitoring system to provide
    comprehensive observability for MCP connections.
    """
    
    def __init__(self, connection_manager=None):
        self.connection_manager = connection_manager
        self.health_check_interval = 30.0  # seconds
        self.alert_thresholds = {
            'pool_exhaustion_threshold': 0.9,  # 90% pool utilization
            'connection_failure_rate_threshold': 0.1,  # 10% failure rate
            'response_time_threshold': 5.0,  # 5 seconds
            'circuit_breaker_open_alert': True
        }
        
        # Monitoring state
        self._monitoring_task: Optional[asyncio.Task] = None
        self._alerts: List[MCPAlert] = []
        self._health_history: Dict[str, List[Dict[str, Any]]] = {}
        self._shutdown = False
    
    async def start_monitoring(self):
        """Start MCP health monitoring"""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("MCP health monitoring started")
    
    async def stop_monitoring(self):
        """Stop MCP health monitoring"""
        self._shutdown = True
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self._monitoring_task = None
        logger.info("MCP health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while not self._shutdown:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in MCP monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _perform_health_checks(self):
        """Perform health checks on all MCP pools"""
        if not self.connection_manager:
            try:
                from core.mcp.connection_manager import get_mcp_connection_manager
                self.connection_manager = await get_mcp_connection_manager()
            except Exception as e:
                logger.warning(f"Could not get MCP connection manager: {e}")
                return
        
        # Get metrics from all pools
        pool_metrics = self.connection_manager.get_pool_metrics()
        
        # Process global metrics
        await self._process_global_metrics(pool_metrics.get('global_metrics', {}))
        
        # Process individual pool metrics
        for server_name, pool_data in pool_metrics.get('pools', {}).items():
            await self._process_pool_metrics(server_name, pool_data)
    
    async def _process_global_metrics(self, global_metrics: Dict[str, Any]):
        """Process global MCP metrics"""
        # Track global MCP metrics
        metrics_collector.system_metrics.total_requests += global_metrics.get('total_requests', 0)
        
        # Record global MCP health metrics
        interaction_id = metrics_collector.start_interaction(
            agent_name="mcp_system",
            user_id="system",
            session_id="monitoring",
            message="Global MCP health check"
        )
        
        # Calculate overall health
        total_errors = global_metrics.get('total_errors', 0)
        total_requests = global_metrics.get('total_requests', 1)
        error_rate = total_errors / total_requests if total_requests > 0 else 0
        
        success = error_rate < self.alert_thresholds['connection_failure_rate_threshold']
        
        metrics_collector.end_interaction(
            interaction_id=interaction_id,
            success=success,
            response=f"Global MCP health: {global_metrics}",
            error=f"High error rate: {error_rate:.2%}" if not success else None
        )
    
    async def _process_pool_metrics(self, server_name: str, pool_metrics: Dict[str, Any]):
        """Process metrics for a specific pool"""
        # Record pool health in monitoring system
        interaction_id = metrics_collector.start_interaction(
            agent_name=f"mcp_{server_name}",
            user_id="system",
            session_id="monitoring",
            message=f"Pool health check for {server_name}"
        )
        
        # Check for alerts
        alerts = self._check_pool_alerts(server_name, pool_metrics)
        
        # Record interaction result
        has_critical_alerts = any(alert.severity == 'critical' for alert in alerts)
        
        metrics_collector.end_interaction(
            interaction_id=interaction_id,
            success=not has_critical_alerts,
            response=f"Pool metrics: {pool_metrics}",
            error=f"Critical alerts: {[a.message for a in alerts if a.severity == 'critical']}" if has_critical_alerts else None
        )
        
        # Store health history
        if server_name not in self._health_history:
            self._health_history[server_name] = []
        
        self._health_history[server_name].append({
            'timestamp': datetime.now(),
            'metrics': pool_metrics,
            'alerts': [{'type': a.alert_type, 'severity': a.severity, 'message': a.message} for a in alerts]
        })
        
        # Keep only last 100 entries
        if len(self._health_history[server_name]) > 100:
            self._health_history[server_name] = self._health_history[server_name][-100:]
    
    def _check_pool_alerts(self, server_name: str, metrics: Dict[str, Any]) -> List[MCPAlert]:
        """Check for alert conditions in pool metrics"""
        alerts = []
        
        # Check pool exhaustion
        total_connections = metrics.get('total_connections', 0)
        available_connections = metrics.get('available_connections', 0)
        
        if total_connections > 0:
            utilization = 1 - (available_connections / total_connections)
            if utilization >= self.alert_thresholds['pool_exhaustion_threshold']:
                alerts.append(MCPAlert(
                    alert_type='pool_exhaustion',
                    server_name=server_name,
                    message=f"Pool utilization high: {utilization:.1%}",
                    severity='warning' if utilization < 0.95 else 'critical',
                    timestamp=datetime.now(),
                    metrics=metrics
                ))
        
        # Check circuit breaker state
        circuit_breaker_state = metrics.get('circuit_breaker_state', 'closed')
        if circuit_breaker_state == 'open' and self.alert_thresholds['circuit_breaker_open_alert']:
            alerts.append(MCPAlert(
                alert_type='circuit_breaker_open',
                server_name=server_name,
                message=f"Circuit breaker is open for {server_name}",
                severity='critical',
                timestamp=datetime.now(),
                metrics=metrics
            ))
        
        # Check connection errors
        connection_errors = metrics.get('connection_errors', 0)
        total_created = metrics.get('total_connections_created', 1)
        error_rate = connection_errors / total_created if total_created > 0 else 0
        
        if error_rate >= self.alert_thresholds['connection_failure_rate_threshold']:
            alerts.append(MCPAlert(
                alert_type='high_error_rate',
                server_name=server_name,
                message=f"High connection error rate: {error_rate:.1%}",
                severity='warning' if error_rate < 0.2 else 'critical',
                timestamp=datetime.now(),
                metrics=metrics
            ))
        
        # Store alerts
        self._alerts.extend(alerts)
        
        # Keep only recent alerts (last 1000)
        if len(self._alerts) > 1000:
            self._alerts = self._alerts[-1000:]
        
        return alerts
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary for MCP connections"""
        if not self.connection_manager:
            return {'status': 'unavailable', 'message': 'Connection manager not available'}
        
        try:
            pool_metrics = self.connection_manager.get_pool_metrics()
            
            # Calculate overall health
            total_pools = len(pool_metrics.get('pools', {}))
            healthy_pools = 0
            warning_pools = 0
            critical_pools = 0
            
            for server_name, metrics in pool_metrics.get('pools', {}).items():
                circuit_breaker_state = metrics.get('circuit_breaker_state', 'closed')
                connection_errors = metrics.get('connection_errors', 0)
                total_created = metrics.get('total_connections_created', 1)
                error_rate = connection_errors / total_created if total_created > 0 else 0
                
                if circuit_breaker_state == 'open' or error_rate >= 0.2:
                    critical_pools += 1
                elif error_rate >= 0.1:
                    warning_pools += 1
                else:
                    healthy_pools += 1
            
            # Determine overall status
            if critical_pools > 0:
                status = 'critical'
            elif warning_pools > 0:
                status = 'warning'
            else:
                status = 'healthy'
            
            return {
                'status': status,
                'total_pools': total_pools,
                'healthy_pools': healthy_pools,
                'warning_pools': warning_pools,
                'critical_pools': critical_pools,
                'recent_alerts': len([a for a in self._alerts if (datetime.now() - a.timestamp).seconds < 300]),
                'global_metrics': pool_metrics.get('global_metrics', {}),
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error getting health summary: {e}',
                'last_check': datetime.now().isoformat()
            }
    
    def get_pool_health(self, server_name: str) -> Dict[str, Any]:
        """Get health information for a specific pool"""
        if server_name not in self._health_history:
            return {'error': f'No health data for pool {server_name}'}
        
        history = self._health_history[server_name]
        if not history:
            return {'error': f'No health history for pool {server_name}'}
        
        latest = history[-1]
        recent_alerts = [a for a in self._alerts 
                        if a.server_name == server_name and 
                        (datetime.now() - a.timestamp).seconds < 3600]  # Last hour
        
        return {
            'server_name': server_name,
            'current_metrics': latest['metrics'],
            'current_alerts': latest['alerts'],
            'recent_alerts': [{'type': a.alert_type, 'severity': a.severity, 
                             'message': a.message, 'timestamp': a.timestamp.isoformat()} 
                            for a in recent_alerts],
            'history_length': len(history),
            'last_check': latest['timestamp'].isoformat()
        }
    
    def get_recent_alerts(self, severity: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts, optionally filtered by severity"""
        alerts = self._alerts
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        # Sort by timestamp (newest first) and limit
        alerts = sorted(alerts, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        return [
            {
                'alert_type': a.alert_type,
                'server_name': a.server_name,
                'message': a.message,
                'severity': a.severity,
                'timestamp': a.timestamp.isoformat(),
                'metrics': a.metrics
            }
            for a in alerts
        ]


# Global health monitor instance
_mcp_health_monitor: Optional[MCPHealthMonitor] = None


async def get_mcp_health_monitor() -> MCPHealthMonitor:
    """Get global MCP health monitor instance"""
    global _mcp_health_monitor
    
    if _mcp_health_monitor is None:
        _mcp_health_monitor = MCPHealthMonitor()
        await _mcp_health_monitor.start_monitoring()
    
    return _mcp_health_monitor


async def start_mcp_monitoring():
    """Start MCP monitoring (called from startup)"""
    monitor = await get_mcp_health_monitor()
    logger.info("MCP monitoring started")


async def stop_mcp_monitoring():
    """Stop MCP monitoring (called from shutdown)"""
    global _mcp_health_monitor
    
    if _mcp_health_monitor:
        await _mcp_health_monitor.stop_monitoring()
        _mcp_health_monitor = None