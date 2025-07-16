"""
MCP Connection Pool Metrics

Comprehensive metrics collection and monitoring for MCP connection pools
with real-time performance tracking and health assessment.
"""

import time
import asyncio
from typing import Dict, List, Optional, Any, NamedTuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import json


class MetricType(str, Enum):
    """Types of metrics collected"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class PoolStatus(str, Enum):
    """Pool health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNAVAILABLE = "unavailable"


@dataclass
class MetricValue:
    """Individual metric measurement"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags
        }


@dataclass
class PoolMetrics:
    """Metrics for a single connection pool"""
    
    server_name: str
    
    # Connection metrics
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    
    # Performance metrics
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    
    # Usage metrics
    requests_per_minute: float = 0.0
    cache_hit_rate: float = 0.0
    
    # Health metrics
    status: PoolStatus = PoolStatus.HEALTHY
    error_rate: float = 0.0
    last_health_check: Optional[datetime] = None
    
    # Circuit breaker metrics
    circuit_breaker_state: str = "closed"
    failure_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "server_name": self.server_name,
            "connections": {
                "total": self.total_connections,
                "active": self.active_connections,
                "idle": self.idle_connections
            },
            "performance": {
                "avg_response_time": self.avg_response_time,
                "p95_response_time": self.p95_response_time,
                "p99_response_time": self.p99_response_time,
                "requests_per_minute": self.requests_per_minute,
                "cache_hit_rate": self.cache_hit_rate
            },
            "health": {
                "status": self.status.value,
                "error_rate": self.error_rate,
                "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None
            },
            "circuit_breaker": {
                "state": self.circuit_breaker_state,
                "failure_count": self.failure_count
            }
        }


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """System alert for monitoring issues"""
    
    level: AlertLevel
    message: str
    server_name: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "level": self.level.value,
            "message": self.message,
            "server_name": self.server_name,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "metadata": self.metadata
        }


class TimingContext:
    """Context manager for timing operations"""
    
    def __init__(self, metrics_collector: 'MCPMetricsCollector', server_name: str, operation: str):
        self.metrics_collector = metrics_collector
        self.server_name = server_name
        self.operation = operation
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.perf_counter() - self.start_time
            self.metrics_collector.record_operation_time(
                self.server_name, 
                self.operation, 
                duration,
                success=exc_type is None
            )


class MCPMetricsCollector:
    """Collects and aggregates MCP connection pool metrics"""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        
        # Metrics storage
        self.pool_metrics: Dict[str, PoolMetrics] = {}
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Alert system
        self.alerts: deque = deque(maxlen=100)
        self.alert_suppression: Dict[str, datetime] = {}
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._export_task: Optional[asyncio.Task] = None
        
        # Performance counters
        self.operation_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.error_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    
    async def start(self):
        """Start background metric collection tasks"""
        self._cleanup_task = asyncio.create_task(self._cleanup_old_metrics())
        self._export_task = asyncio.create_task(self._export_metrics_periodically())
    
    async def stop(self):
        """Stop background tasks"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._export_task:
            self._export_task.cancel()
    
    def get_server_metrics(self, server_name: str) -> PoolMetrics:
        """Get or create metrics for a server"""
        if server_name not in self.pool_metrics:
            self.pool_metrics[server_name] = PoolMetrics(server_name=server_name)
        return self.pool_metrics[server_name]
    
    def record_connection_created(self, server_name: str):
        """Record a new connection creation"""
        metrics = self.get_server_metrics(server_name)
        metrics.total_connections += 1
        self.operation_counts[server_name]["connections_created"] += 1
        
        self._record_metric(server_name, "connections_total", metrics.total_connections, MetricType.GAUGE)
    
    def record_connection_destroyed(self, server_name: str):
        """Record a connection destruction"""
        metrics = self.get_server_metrics(server_name)
        metrics.total_connections = max(0, metrics.total_connections - 1)
        self.operation_counts[server_name]["connections_destroyed"] += 1
        
        self._record_metric(server_name, "connections_total", metrics.total_connections, MetricType.GAUGE)
    
    def record_connection_acquired(self, server_name: str):
        """Record a connection being acquired from pool"""
        metrics = self.get_server_metrics(server_name)
        metrics.active_connections += 1
        metrics.idle_connections = max(0, metrics.idle_connections - 1)
        self.operation_counts[server_name]["connections_acquired"] += 1
        
        self._record_metric(server_name, "connections_active", metrics.active_connections, MetricType.GAUGE)
        self._record_metric(server_name, "connections_idle", metrics.idle_connections, MetricType.GAUGE)
    
    def record_connection_returned(self, server_name: str):
        """Record a connection being returned to pool"""
        metrics = self.get_server_metrics(server_name)
        metrics.active_connections = max(0, metrics.active_connections - 1)
        metrics.idle_connections += 1
        self.operation_counts[server_name]["connections_returned"] += 1
        
        self._record_metric(server_name, "connections_active", metrics.active_connections, MetricType.GAUGE)
        self._record_metric(server_name, "connections_idle", metrics.idle_connections, MetricType.GAUGE)
    
    def record_operation_time(self, server_name: str, operation: str, duration: float, success: bool = True):
        """Record operation timing and success/failure"""
        self.response_times[server_name].append(duration)
        
        if success:
            self.operation_counts[server_name][f"{operation}_success"] += 1
        else:
            self.operation_counts[server_name][f"{operation}_error"] += 1
            self.error_counts[server_name][operation] += 1
        
        # Update metrics
        metrics = self.get_server_metrics(server_name)
        response_times = list(self.response_times[server_name])
        
        if response_times:
            metrics.avg_response_time = sum(response_times) / len(response_times)
            sorted_times = sorted(response_times)
            metrics.p95_response_time = sorted_times[int(len(sorted_times) * 0.95)]
            metrics.p99_response_time = sorted_times[int(len(sorted_times) * 0.99)]
        
        # Calculate error rate
        total_ops = sum(self.operation_counts[server_name].values())
        total_errors = sum(self.error_counts[server_name].values())
        metrics.error_rate = (total_errors / total_ops * 100) if total_ops > 0 else 0.0
        
        self._record_metric(server_name, f"{operation}_duration", duration, MetricType.TIMER)
        self._record_metric(server_name, "error_rate", metrics.error_rate, MetricType.GAUGE)
    
    def record_cache_hit(self, server_name: str):
        """Record a cache hit (connection reuse)"""
        self.operation_counts[server_name]["cache_hits"] += 1
        self._update_cache_hit_rate(server_name)
    
    def record_cache_miss(self, server_name: str):
        """Record a cache miss (new connection needed)"""
        self.operation_counts[server_name]["cache_misses"] += 1
        self._update_cache_hit_rate(server_name)
    
    def _update_cache_hit_rate(self, server_name: str):
        """Update cache hit rate calculation"""
        metrics = self.get_server_metrics(server_name)
        hits = self.operation_counts[server_name]["cache_hits"]
        misses = self.operation_counts[server_name]["cache_misses"]
        total = hits + misses
        
        metrics.cache_hit_rate = (hits / total * 100) if total > 0 else 0.0
        self._record_metric(server_name, "cache_hit_rate", metrics.cache_hit_rate, MetricType.GAUGE)
    
    def update_pool_status(self, server_name: str, status: PoolStatus, circuit_breaker_state: str = "closed", failure_count: int = 0):
        """Update pool health status"""
        metrics = self.get_server_metrics(server_name)
        old_status = metrics.status
        
        metrics.status = status
        metrics.circuit_breaker_state = circuit_breaker_state
        metrics.failure_count = failure_count
        metrics.last_health_check = datetime.now()
        
        # Generate alerts for status changes
        if old_status != status and status in [PoolStatus.WARNING, PoolStatus.CRITICAL]:
            self._create_alert(
                AlertLevel.WARNING if status == PoolStatus.WARNING else AlertLevel.CRITICAL,
                f"Pool {server_name} status changed to {status.value}",
                server_name
            )
        
        self._record_metric(server_name, "pool_status", 1.0 if status == PoolStatus.HEALTHY else 0.0, MetricType.GAUGE)
    
    def _record_metric(self, server_name: str, metric_name: str, value: float, metric_type: MetricType):
        """Record a metric value"""
        metric = MetricValue(
            name=metric_name,
            value=value,
            metric_type=metric_type,
            tags={"server": server_name}
        )
        
        metric_key = f"{server_name}.{metric_name}"
        self.metric_history[metric_key].append(metric)
    
    def _create_alert(self, level: AlertLevel, message: str, server_name: Optional[str] = None, **metadata):
        """Create a new alert with suppression"""
        alert_key = f"{level.value}:{message}:{server_name}"
        
        # Check suppression (don't spam same alert)
        if alert_key in self.alert_suppression:
            if datetime.now() - self.alert_suppression[alert_key] < timedelta(minutes=5):
                return
        
        alert = Alert(
            level=level,
            message=message,
            server_name=server_name,
            metadata=metadata
        )
        
        self.alerts.append(alert)
        self.alert_suppression[alert_key] = datetime.now()
        
        # Log alert
        print(f"MCP ALERT [{level.value.upper()}]: {message}")
    
    def get_all_metrics(self) -> Dict[str, PoolMetrics]:
        """Get all current pool metrics"""
        return self.pool_metrics.copy()
    
    def get_recent_alerts(self, hours: int = 1) -> List[Alert]:
        """Get recent alerts within specified timeframe"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alerts if alert.timestamp >= cutoff]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get aggregated metrics summary"""
        total_pools = len(self.pool_metrics)
        healthy_pools = sum(1 for m in self.pool_metrics.values() if m.status == PoolStatus.HEALTHY)
        total_connections = sum(m.total_connections for m in self.pool_metrics.values())
        active_connections = sum(m.active_connections for m in self.pool_metrics.values())
        
        avg_response_time = 0.0
        if self.pool_metrics:
            avg_response_time = sum(m.avg_response_time for m in self.pool_metrics.values()) / len(self.pool_metrics)
        
        return {
            "overview": {
                "total_pools": total_pools,
                "healthy_pools": healthy_pools,
                "total_connections": total_connections,
                "active_connections": active_connections,
                "avg_response_time": avg_response_time
            },
            "pools": {name: metrics.to_dict() for name, metrics in self.pool_metrics.items()},
            "recent_alerts": [alert.to_dict() for alert in self.get_recent_alerts()],
            "timestamp": datetime.now().isoformat()
        }
    
    def time_operation(self, server_name: str, operation: str) -> TimingContext:
        """Context manager for timing operations"""
        return TimingContext(self, server_name, operation)
    
    async def _cleanup_old_metrics(self):
        """Background task to clean up old metrics"""
        while True:
            try:
                cutoff = datetime.now() - timedelta(hours=self.retention_hours)
                
                for metric_key, history in self.metric_history.items():
                    # Remove old metrics
                    while history and history[0].timestamp < cutoff:
                        history.popleft()
                
                # Clean up old alerts
                while self.alerts and self.alerts[0].timestamp < cutoff:
                    self.alerts.popleft()
                
                # Clean up alert suppression
                expired_keys = [
                    key for key, timestamp in self.alert_suppression.items()
                    if datetime.now() - timestamp > timedelta(hours=1)
                ]
                for key in expired_keys:
                    del self.alert_suppression[key]
                
                await asyncio.sleep(300)  # Clean up every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in metrics cleanup: {e}")
                await asyncio.sleep(60)
    
    async def _export_metrics_periodically(self):
        """Background task to export metrics"""
        while True:
            try:
                # Export metrics (could be to file, external system, etc.)
                summary = self.get_metrics_summary()
                
                # For now, just log summary periodically
                print(f"MCP Metrics Summary: {summary['overview']}")
                
                await asyncio.sleep(60)  # Export every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in metrics export: {e}")
                await asyncio.sleep(60)


# Global metrics collector instance
_metrics_collector: Optional[MCPMetricsCollector] = None


def get_metrics_collector() -> MCPMetricsCollector:
    """Get or create global metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MCPMetricsCollector()
    return _metrics_collector


async def start_metrics_collection():
    """Start global metrics collection"""
    collector = get_metrics_collector()
    await collector.start()


async def stop_metrics_collection():
    """Stop global metrics collection"""
    collector = get_metrics_collector()
    await collector.stop()