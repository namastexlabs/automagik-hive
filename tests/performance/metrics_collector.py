"""
Performance metrics collection and reporting system for Genie Agents.

This module provides comprehensive metrics collection for:
- Agent execution performance
- System resource utilization
- Business metrics and KPIs
- Historical trend analysis
- Automated reporting and alerting
"""

import time
import json
import psutil
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict, deque
import sqlite3
import asyncio

from utils.log import logger
from config.settings import settings


@dataclass
class AgentMetric:
    """Agent performance metric data structure."""
    timestamp: datetime
    agent_id: str
    version: Optional[str]
    operation: str  # 'run', 'stream', 'tool_call', etc.
    duration_seconds: float
    success: bool
    error_message: Optional[str]
    memory_usage_mb: float
    cpu_percent: float
    session_id: Optional[str]
    user_id: Optional[str]
    request_size_bytes: int
    response_size_bytes: int
    metadata: Dict[str, Any]


@dataclass
class SystemMetric:
    """System resource metric data structure."""
    timestamp: datetime
    memory_usage_mb: float
    memory_available_mb: float
    cpu_percent: float
    disk_usage_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_bytes_sent: float
    network_bytes_recv: float
    active_connections: int
    thread_count: int
    process_count: int


@dataclass
class BusinessMetric:
    """Business KPI metric data structure."""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    category: str  # 'performance', 'usage', 'quality', 'cost'
    agent_id: Optional[str]
    session_id: Optional[str]
    metadata: Dict[str, Any]


class MetricsCollector:
    """Comprehensive metrics collection system."""
    
    def __init__(self, db_path: str = "tests/performance/metrics.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory buffers for real-time metrics
        self.agent_metrics: deque = deque(maxlen=10000)
        self.system_metrics: deque = deque(maxlen=1000)
        self.business_metrics: deque = deque(maxlen=10000)
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread = None
        self.last_network_stats = None
        self.last_disk_stats = None
        
        # Initialize database
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database for metrics storage."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Agent metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                version TEXT,
                operation TEXT NOT NULL,
                duration_seconds REAL NOT NULL,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                memory_usage_mb REAL,
                cpu_percent REAL,
                session_id TEXT,
                user_id TEXT,
                request_size_bytes INTEGER,
                response_size_bytes INTEGER,
                metadata TEXT
            )
        """)
        
        # System metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory_usage_mb REAL,
                memory_available_mb REAL,
                cpu_percent REAL,
                disk_usage_percent REAL,
                disk_io_read_mb REAL,
                disk_io_write_mb REAL,
                network_bytes_sent REAL,
                network_bytes_recv REAL,
                active_connections INTEGER,
                thread_count INTEGER,
                process_count INTEGER
            )
        """)
        
        # Business metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS business_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                category TEXT NOT NULL,
                agent_id TEXT,
                session_id TEXT,
                metadata TEXT
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_metrics_timestamp ON agent_metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_metrics_agent_id ON agent_metrics(agent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_business_metrics_timestamp ON business_metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_business_metrics_name ON business_metrics(metric_name)")
        
        conn.commit()
        conn.close()
    
    def start_monitoring(self, interval_seconds: int = 5):
        """Start background system monitoring."""
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitor_system_metrics,
            args=(interval_seconds,)
        )
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        logger.info(f"Started metrics monitoring with {interval_seconds}s interval")
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
        logger.info("Stopped metrics monitoring")
    
    def _monitor_system_metrics(self, interval_seconds: int):
        """Background system metrics monitoring loop."""
        while self.monitoring_active:
            try:
                self._collect_system_metrics()
                time.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                time.sleep(interval_seconds)
    
    def _collect_system_metrics(self):
        """Collect current system metrics."""
        # Memory stats
        memory = psutil.virtual_memory()
        
        # CPU stats
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Disk stats
        disk_usage = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        # Network stats
        network_io = psutil.net_io_counters()
        
        # Process stats
        process = psutil.Process()
        
        # Calculate IO rates
        disk_read_mb = 0
        disk_write_mb = 0
        network_sent = 0
        network_recv = 0
        
        if self.last_disk_stats:
            disk_read_mb = (disk_io.read_bytes - self.last_disk_stats.read_bytes) / (1024 * 1024)
            disk_write_mb = (disk_io.write_bytes - self.last_disk_stats.write_bytes) / (1024 * 1024)
        
        if self.last_network_stats:
            network_sent = network_io.bytes_sent - self.last_network_stats.bytes_sent
            network_recv = network_io.bytes_recv - self.last_network_stats.bytes_recv
        
        self.last_disk_stats = disk_io
        self.last_network_stats = network_io
        
        # Create metric
        metric = SystemMetric(
            timestamp=datetime.now(timezone.utc),
            memory_usage_mb=memory.used / (1024 * 1024),
            memory_available_mb=memory.available / (1024 * 1024),
            cpu_percent=cpu_percent,
            disk_usage_percent=disk_usage.percent,
            disk_io_read_mb=disk_read_mb,
            disk_io_write_mb=disk_write_mb,
            network_bytes_sent=network_sent,
            network_bytes_recv=network_recv,
            active_connections=len(process.connections()),
            thread_count=process.num_threads(),
            process_count=len(psutil.pids())
        )
        
        # Store in buffer
        self.system_metrics.append(metric)
        
        # Persist to database every 10 metrics
        if len(self.system_metrics) % 10 == 0:
            self._persist_system_metrics()
    
    def record_agent_metric(self,
                          agent_id: str,
                          operation: str,
                          duration_seconds: float,
                          success: bool,
                          version: Optional[str] = None,
                          error_message: Optional[str] = None,
                          session_id: Optional[str] = None,
                          user_id: Optional[str] = None,
                          request_size_bytes: int = 0,
                          response_size_bytes: int = 0,
                          metadata: Optional[Dict[str, Any]] = None):
        """Record an agent performance metric."""
        
        # Get current resource usage
        process = psutil.Process()
        memory_usage = process.memory_info().rss / (1024 * 1024)
        cpu_percent = process.cpu_percent()
        
        metric = AgentMetric(
            timestamp=datetime.now(timezone.utc),
            agent_id=agent_id,
            version=version,
            operation=operation,
            duration_seconds=duration_seconds,
            success=success,
            error_message=error_message,
            memory_usage_mb=memory_usage,
            cpu_percent=cpu_percent,
            session_id=session_id,
            user_id=user_id,
            request_size_bytes=request_size_bytes,
            response_size_bytes=response_size_bytes,
            metadata=metadata or {}
        )
        
        # Store in buffer
        self.agent_metrics.append(metric)
        
        # Persist to database every 50 metrics
        if len(self.agent_metrics) % 50 == 0:
            self._persist_agent_metrics()
    
    def record_business_metric(self,
                             metric_name: str,
                             value: float,
                             unit: str,
                             category: str,
                             agent_id: Optional[str] = None,
                             session_id: Optional[str] = None,
                             metadata: Optional[Dict[str, Any]] = None):
        """Record a business KPI metric."""
        
        metric = BusinessMetric(
            timestamp=datetime.now(timezone.utc),
            metric_name=metric_name,
            value=value,
            unit=unit,
            category=category,
            agent_id=agent_id,
            session_id=session_id,
            metadata=metadata or {}
        )
        
        # Store in buffer
        self.business_metrics.append(metric)
        
        # Persist to database every 20 metrics
        if len(self.business_metrics) % 20 == 0:
            self._persist_business_metrics()
    
    def _persist_agent_metrics(self):
        """Persist agent metrics to database."""
        if not self.agent_metrics:
            return
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        for metric in self.agent_metrics:
            cursor.execute("""
                INSERT INTO agent_metrics 
                (timestamp, agent_id, version, operation, duration_seconds, success, 
                 error_message, memory_usage_mb, cpu_percent, session_id, user_id,
                 request_size_bytes, response_size_bytes, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.timestamp.isoformat(),
                metric.agent_id,
                metric.version,
                metric.operation,
                metric.duration_seconds,
                metric.success,
                metric.error_message,
                metric.memory_usage_mb,
                metric.cpu_percent,
                metric.session_id,
                metric.user_id,
                metric.request_size_bytes,
                metric.response_size_bytes,
                json.dumps(metric.metadata)
            ))
        
        conn.commit()
        conn.close()
        
        # Clear buffer
        self.agent_metrics.clear()
    
    def _persist_system_metrics(self):
        """Persist system metrics to database."""
        if not self.system_metrics:
            return
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        for metric in self.system_metrics:
            cursor.execute("""
                INSERT INTO system_metrics 
                (timestamp, memory_usage_mb, memory_available_mb, cpu_percent,
                 disk_usage_percent, disk_io_read_mb, disk_io_write_mb,
                 network_bytes_sent, network_bytes_recv, active_connections,
                 thread_count, process_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.timestamp.isoformat(),
                metric.memory_usage_mb,
                metric.memory_available_mb,
                metric.cpu_percent,
                metric.disk_usage_percent,
                metric.disk_io_read_mb,
                metric.disk_io_write_mb,
                metric.network_bytes_sent,
                metric.network_bytes_recv,
                metric.active_connections,
                metric.thread_count,
                metric.process_count
            ))
        
        conn.commit()
        conn.close()
        
        # Clear buffer
        self.system_metrics.clear()
    
    def _persist_business_metrics(self):
        """Persist business metrics to database."""
        if not self.business_metrics:
            return
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        for metric in self.business_metrics:
            cursor.execute("""
                INSERT INTO business_metrics 
                (timestamp, metric_name, value, unit, category, agent_id, session_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.timestamp.isoformat(),
                metric.metric_name,
                metric.value,
                metric.unit,
                metric.category,
                metric.agent_id,
                metric.session_id,
                json.dumps(metric.metadata)
            ))
        
        conn.commit()
        conn.close()
        
        # Clear buffer
        self.business_metrics.clear()
    
    def get_agent_performance_report(self, 
                                   agent_id: Optional[str] = None,
                                   hours: int = 24) -> Dict[str, Any]:
        """Generate agent performance report."""
        
        # Force persist any pending metrics
        self._persist_agent_metrics()
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Calculate time window
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Base query
        where_clause = "WHERE timestamp >= ?"
        params = [start_time.isoformat()]
        
        if agent_id:
            where_clause += " AND agent_id = ?"
            params.append(agent_id)
        
        # Get overall stats
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_requests,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests,
                AVG(duration_seconds) as avg_duration,
                MIN(duration_seconds) as min_duration,
                MAX(duration_seconds) as max_duration,
                AVG(memory_usage_mb) as avg_memory,
                MAX(memory_usage_mb) as peak_memory,
                AVG(cpu_percent) as avg_cpu
            FROM agent_metrics {where_clause}
        """, params)
        
        stats = cursor.fetchone()
        
        # Get per-agent breakdown
        cursor.execute(f"""
            SELECT 
                agent_id,
                COUNT(*) as requests,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                AVG(duration_seconds) as avg_duration,
                AVG(memory_usage_mb) as avg_memory
            FROM agent_metrics {where_clause}
            GROUP BY agent_id
            ORDER BY requests DESC
        """, params)
        
        agent_breakdown = [
            {
                "agent_id": row[0],
                "requests": row[1],
                "successful": row[2],
                "success_rate": row[2] / row[1] * 100 if row[1] > 0 else 0,
                "avg_duration": row[3],
                "avg_memory": row[4]
            }
            for row in cursor.fetchall()
        ]
        
        # Get error analysis
        cursor.execute(f"""
            SELECT 
                error_message,
                COUNT(*) as count
            FROM agent_metrics 
            {where_clause} AND success = 0 AND error_message IS NOT NULL
            GROUP BY error_message
            ORDER BY count DESC
            LIMIT 10
        """, params)
        
        errors = [
            {"error": row[0], "count": row[1]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        # Calculate derived metrics
        total_requests = stats[0] if stats[0] else 0
        successful_requests = stats[1] if stats[1] else 0
        success_rate = successful_requests / total_requests * 100 if total_requests > 0 else 0
        
        return {
            "time_window_hours": hours,
            "agent_id": agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_stats": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "success_rate": success_rate,
                "avg_duration_seconds": stats[2] if stats[2] else 0,
                "min_duration_seconds": stats[3] if stats[3] else 0,
                "max_duration_seconds": stats[4] if stats[4] else 0,
                "avg_memory_mb": stats[5] if stats[5] else 0,
                "peak_memory_mb": stats[6] if stats[6] else 0,
                "avg_cpu_percent": stats[7] if stats[7] else 0
            },
            "agent_breakdown": agent_breakdown,
            "top_errors": errors
        }
    
    def get_system_health_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate system health report."""
        
        # Force persist any pending metrics
        self._persist_system_metrics()
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Calculate time window
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Get system stats
        cursor.execute("""
            SELECT 
                AVG(memory_usage_mb) as avg_memory,
                MAX(memory_usage_mb) as peak_memory,
                AVG(cpu_percent) as avg_cpu,
                MAX(cpu_percent) as peak_cpu,
                AVG(disk_usage_percent) as avg_disk,
                MAX(disk_usage_percent) as peak_disk,
                AVG(active_connections) as avg_connections,
                MAX(active_connections) as peak_connections,
                AVG(thread_count) as avg_threads,
                MAX(thread_count) as peak_threads
            FROM system_metrics 
            WHERE timestamp >= ?
        """, [start_time.isoformat()])
        
        stats = cursor.fetchone()
        
        # Get recent trends (last hour vs previous hour)
        recent_time = datetime.now(timezone.utc) - timedelta(hours=1)
        previous_time = datetime.now(timezone.utc) - timedelta(hours=2)
        
        cursor.execute("""
            SELECT 
                AVG(memory_usage_mb) as avg_memory,
                AVG(cpu_percent) as avg_cpu
            FROM system_metrics 
            WHERE timestamp >= ?
        """, [recent_time.isoformat()])
        
        recent_stats = cursor.fetchone()
        
        cursor.execute("""
            SELECT 
                AVG(memory_usage_mb) as avg_memory,
                AVG(cpu_percent) as avg_cpu
            FROM system_metrics 
            WHERE timestamp >= ? AND timestamp < ?
        """, [previous_time.isoformat(), recent_time.isoformat()])
        
        previous_stats = cursor.fetchone()
        
        conn.close()
        
        # Calculate trends
        memory_trend = 0
        cpu_trend = 0
        
        if recent_stats and previous_stats and previous_stats[0] and previous_stats[1]:
            memory_trend = ((recent_stats[0] - previous_stats[0]) / previous_stats[0]) * 100
            cpu_trend = ((recent_stats[1] - previous_stats[1]) / previous_stats[1]) * 100
        
        return {
            "time_window_hours": hours,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_stats": {
                "avg_memory_mb": stats[0] if stats[0] else 0,
                "peak_memory_mb": stats[1] if stats[1] else 0,
                "avg_cpu_percent": stats[2] if stats[2] else 0,
                "peak_cpu_percent": stats[3] if stats[3] else 0,
                "avg_disk_percent": stats[4] if stats[4] else 0,
                "peak_disk_percent": stats[5] if stats[5] else 0,
                "avg_connections": stats[6] if stats[6] else 0,
                "peak_connections": stats[7] if stats[7] else 0,
                "avg_threads": stats[8] if stats[8] else 0,
                "peak_threads": stats[9] if stats[9] else 0
            },
            "trends": {
                "memory_change_percent": memory_trend,
                "cpu_change_percent": cpu_trend
            },
            "alerts": self._generate_health_alerts(stats)
        }
    
    def _generate_health_alerts(self, stats) -> List[Dict[str, Any]]:
        """Generate health alerts based on system metrics."""
        alerts = []
        
        if stats[1] and stats[1] > 8000:  # Peak memory > 8GB
            alerts.append({
                "type": "warning",
                "message": f"High memory usage detected: {stats[1]:.1f}MB",
                "metric": "memory",
                "value": stats[1]
            })
        
        if stats[3] and stats[3] > 80:  # Peak CPU > 80%
            alerts.append({
                "type": "warning",
                "message": f"High CPU usage detected: {stats[3]:.1f}%",
                "metric": "cpu",
                "value": stats[3]
            })
        
        if stats[5] and stats[5] > 90:  # Peak disk > 90%
            alerts.append({
                "type": "critical",
                "message": f"High disk usage detected: {stats[5]:.1f}%",
                "metric": "disk",
                "value": stats[5]
            })
        
        return alerts
    
    def get_business_metrics_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate business metrics report."""
        
        # Force persist any pending metrics
        self._persist_business_metrics()
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Calculate time window
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Get metrics by category
        cursor.execute("""
            SELECT 
                category,
                metric_name,
                COUNT(*) as count,
                AVG(value) as avg_value,
                MIN(value) as min_value,
                MAX(value) as max_value,
                unit
            FROM business_metrics 
            WHERE timestamp >= ?
            GROUP BY category, metric_name, unit
            ORDER BY category, metric_name
        """, [start_time.isoformat()])
        
        metrics_by_category = defaultdict(list)
        for row in cursor.fetchall():
            metrics_by_category[row[0]].append({
                "name": row[1],
                "count": row[2],
                "avg_value": row[3],
                "min_value": row[4],
                "max_value": row[5],
                "unit": row[6]
            })
        
        conn.close()
        
        return {
            "time_window_hours": hours,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics_by_category": dict(metrics_by_category)
        }
    
    def export_metrics(self, 
                      filename: Optional[str] = None,
                      format: str = "json",
                      hours: int = 24) -> str:
        """Export metrics to file."""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_export_{timestamp}.{format}"
        
        filepath = Path("tests/performance/exports") / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate comprehensive report
        report = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "time_window_hours": hours,
            "agent_performance": self.get_agent_performance_report(hours=hours),
            "system_health": self.get_system_health_report(hours=hours),
            "business_metrics": self.get_business_metrics_report(hours=hours)
        }
        
        if format == "json":
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return str(filepath)


# Global metrics collector instance
metrics_collector = MetricsCollector()


# Context manager for timing operations
class TimedOperation:
    """Context manager for timing operations and recording metrics."""
    
    def __init__(self, 
                 agent_id: str,
                 operation: str,
                 version: Optional[str] = None,
                 session_id: Optional[str] = None,
                 user_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.agent_id = agent_id
        self.operation = operation
        self.version = version
        self.session_id = session_id
        self.user_id = user_id
        self.metadata = metadata or {}
        self.start_time = None
        self.success = False
        self.error_message = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.success = True
        else:
            self.success = False
            self.error_message = str(exc_val)
        
        # Record metric
        metrics_collector.record_agent_metric(
            agent_id=self.agent_id,
            operation=self.operation,
            duration_seconds=duration,
            success=self.success,
            version=self.version,
            error_message=self.error_message,
            session_id=self.session_id,
            user_id=self.user_id,
            metadata=self.metadata
        )
        
        # Don't suppress exceptions
        return False


# CLI script for metrics management
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Genie Agents metrics management")
    parser.add_argument("--start-monitoring", action="store_true", help="Start background monitoring")
    parser.add_argument("--report", choices=["agent", "system", "business", "all"], 
                       default="all", help="Generate performance reports")
    parser.add_argument("--export", action="store_true", help="Export metrics to file")
    parser.add_argument("--hours", type=int, default=24, help="Time window in hours")
    parser.add_argument("--agent-id", type=str, help="Specific agent ID for reporting")
    
    args = parser.parse_args()
    
    if args.start_monitoring:
        print("Starting metrics monitoring...")
        metrics_collector.start_monitoring()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping metrics monitoring...")
            metrics_collector.stop_monitoring()
    
    if args.report in ["agent", "all"]:
        print("Generating agent performance report...")
        report = metrics_collector.get_agent_performance_report(
            agent_id=args.agent_id,
            hours=args.hours
        )
        print(json.dumps(report, indent=2))
    
    if args.report in ["system", "all"]:
        print("Generating system health report...")
        report = metrics_collector.get_system_health_report(hours=args.hours)
        print(json.dumps(report, indent=2))
    
    if args.report in ["business", "all"]:
        print("Generating business metrics report...")
        report = metrics_collector.get_business_metrics_report(hours=args.hours)
        print(json.dumps(report, indent=2))
    
    if args.export:
        print("Exporting metrics...")
        filepath = metrics_collector.export_metrics(hours=args.hours)
        print(f"Metrics exported to: {filepath}")