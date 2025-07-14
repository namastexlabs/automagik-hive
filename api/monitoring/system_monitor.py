"""
System monitoring module for real-time health checks
Monitors system resources, database connections, and service availability
"""

import asyncio
import logging
import psutil
import socket
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DOWN = "down"

@dataclass
class ServiceHealth:
    """Service health information"""
    name: str
    status: HealthStatus
    response_time: float
    last_check: datetime
    message: str
    metadata: Dict[str, Any] = None

class SystemMonitor:
    """
    System monitoring and health check manager
    Provides real-time system health monitoring and alerts
    """
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.services: Dict[str, ServiceHealth] = {}
        self.system_stats: Dict[str, Any] = {}
        self.alerts: List[Dict[str, Any]] = []
        self.monitoring_active = False
        
        # Health check configurations
        self.health_checks = {
            'database': self._check_database_health,
            'memory': self._check_memory_health,
            'cpu': self._check_cpu_health,
            'disk': self._check_disk_health,
            'network': self._check_network_health,
            'agents': self._check_agent_health
        }
        
        # Thresholds for alerts
        self.thresholds = {
            'memory_warning': 80.0,      # %
            'memory_critical': 90.0,     # %
            'cpu_warning': 80.0,         # %
            'cpu_critical': 95.0,        # %
            'disk_warning': 80.0,        # %
            'disk_critical': 90.0,       # %
            'response_time_warning': 2.0,  # seconds
            'response_time_critical': 5.0, # seconds
        }
    
    async def start_monitoring(self):
        """Start the system monitoring loop"""
        self.monitoring_active = True
        logger.info("System monitoring started")
        
        while self.monitoring_active:
            try:
                await self._run_health_checks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """Stop the system monitoring loop"""
        self.monitoring_active = False
        logger.info("System monitoring stopped")
    
    async def _run_health_checks(self):
        """Run all configured health checks"""
        check_start = time.time()
        
        # Run all health checks concurrently
        check_tasks = []
        for service_name, check_func in self.health_checks.items():
            check_tasks.append(self._run_single_check(service_name, check_func))
        
        # Wait for all checks to complete
        await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Update system stats
        self.system_stats['last_check'] = datetime.now()
        self.system_stats['check_duration'] = time.time() - check_start
        self.system_stats['services_checked'] = len(self.health_checks)
        
        # Generate alerts for critical issues
        await self._process_alerts()
    
    async def _run_single_check(self, service_name: str, check_func):
        """Run a single health check"""
        try:
            start_time = time.time()
            result = await check_func()
            response_time = time.time() - start_time
            
            # Create service health record
            self.services[service_name] = ServiceHealth(
                name=service_name,
                status=result.get('status', HealthStatus.HEALTHY),
                response_time=response_time,
                last_check=datetime.now(),
                message=result.get('message', 'OK'),
                metadata=result.get('metadata', {})
            )
            
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            self.services[service_name] = ServiceHealth(
                name=service_name,
                status=HealthStatus.DOWN,
                response_time=0.0,
                last_check=datetime.now(),
                message=f"Health check failed: {str(e)}"
            )
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            from db.session import get_db_session
            
            start_time = time.time()
            
            # Test database connection
            async with get_db_session() as session:
                await session.execute("SELECT 1")
            
            response_time = time.time() - start_time
            
            # Determine status based on response time
            if response_time > self.thresholds['response_time_critical']:
                status = HealthStatus.CRITICAL
                message = f"Database response time critical: {response_time:.2f}s"
            elif response_time > self.thresholds['response_time_warning']:
                status = HealthStatus.WARNING
                message = f"Database response time high: {response_time:.2f}s"
            else:
                status = HealthStatus.HEALTHY
                message = "Database connection healthy"
            
            return {
                'status': status,
                'message': message,
                'metadata': {
                    'response_time': response_time,
                    'connection_test': 'passed'
                }
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.DOWN,
                'message': f"Database connection failed: {str(e)}",
                'metadata': {'error': str(e)}
            }
    
    async def _check_memory_health(self) -> Dict[str, Any]:
        """Check system memory usage"""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            
            # Determine status based on usage
            if usage_percent > self.thresholds['memory_critical']:
                status = HealthStatus.CRITICAL
                message = f"Memory usage critical: {usage_percent:.1f}%"
            elif usage_percent > self.thresholds['memory_warning']:
                status = HealthStatus.WARNING
                message = f"Memory usage high: {usage_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {usage_percent:.1f}%"
            
            return {
                'status': status,
                'message': message,
                'metadata': {
                    'usage_percent': usage_percent,
                    'total_mb': memory.total // (1024 * 1024),
                    'available_mb': memory.available // (1024 * 1024),
                    'used_mb': memory.used // (1024 * 1024)
                }
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.DOWN,
                'message': f"Memory check failed: {str(e)}",
                'metadata': {'error': str(e)}
            }
    
    async def _check_cpu_health(self) -> Dict[str, Any]:
        """Check CPU usage"""
        try:
            # Get CPU usage over 1 second interval
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Determine status based on usage
            if cpu_percent > self.thresholds['cpu_critical']:
                status = HealthStatus.CRITICAL
                message = f"CPU usage critical: {cpu_percent:.1f}%"
            elif cpu_percent > self.thresholds['cpu_warning']:
                status = HealthStatus.WARNING
                message = f"CPU usage high: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU usage normal: {cpu_percent:.1f}%"
            
            return {
                'status': status,
                'message': message,
                'metadata': {
                    'usage_percent': cpu_percent,
                    'cpu_count': psutil.cpu_count(),
                    'load_avg': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                }
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.DOWN,
                'message': f"CPU check failed: {str(e)}",
                'metadata': {'error': str(e)}
            }
    
    async def _check_disk_health(self) -> Dict[str, Any]:
        """Check disk space usage"""
        try:
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            
            # Determine status based on usage
            if usage_percent > self.thresholds['disk_critical']:
                status = HealthStatus.CRITICAL
                message = f"Disk usage critical: {usage_percent:.1f}%"
            elif usage_percent > self.thresholds['disk_warning']:
                status = HealthStatus.WARNING
                message = f"Disk usage high: {usage_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage normal: {usage_percent:.1f}%"
            
            return {
                'status': status,
                'message': message,
                'metadata': {
                    'usage_percent': usage_percent,
                    'total_gb': disk.total // (1024 * 1024 * 1024),
                    'free_gb': disk.free // (1024 * 1024 * 1024),
                    'used_gb': disk.used // (1024 * 1024 * 1024)
                }
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.DOWN,
                'message': f"Disk check failed: {str(e)}",
                'metadata': {'error': str(e)}
            }
    
    async def _check_network_health(self) -> Dict[str, Any]:
        """Check network connectivity"""
        try:
            # Test network connectivity to external service
            start_time = time.time()
            
            # Simple socket test to Google DNS
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('8.8.8.8', 53))
            sock.close()
            
            response_time = time.time() - start_time
            
            if result == 0:
                status = HealthStatus.HEALTHY
                message = "Network connectivity healthy"
            else:
                status = HealthStatus.CRITICAL
                message = "Network connectivity issues detected"
            
            return {
                'status': status,
                'message': message,
                'metadata': {
                    'response_time': response_time,
                    'connection_test': 'passed' if result == 0 else 'failed'
                }
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.DOWN,
                'message': f"Network check failed: {str(e)}",
                'metadata': {'error': str(e)}
            }
    
    async def _check_agent_health(self) -> Dict[str, Any]:
        """Check agent system health"""
        try:
            # Import metrics collector to get agent status
            from .metrics_collector import metrics_collector
            
            agent_metrics = metrics_collector.get_agent_metrics()
            
            # Analyze agent health
            critical_agents = []
            warning_agents = []
            
            for agent_name, metrics in agent_metrics.items():
                if isinstance(metrics, dict) and 'success_rate' in metrics:
                    success_rate = metrics['success_rate']
                    response_time = metrics['average_response_time']
                    
                    if success_rate < 90.0 or response_time > 5.0:
                        critical_agents.append(agent_name)
                    elif success_rate < 95.0 or response_time > 2.0:
                        warning_agents.append(agent_name)
            
            # Determine overall agent health
            if critical_agents:
                status = HealthStatus.CRITICAL
                message = f"Critical issues with agents: {', '.join(critical_agents)}"
            elif warning_agents:
                status = HealthStatus.WARNING
                message = f"Performance issues with agents: {', '.join(warning_agents)}"
            else:
                status = HealthStatus.HEALTHY
                message = "All agents performing normally"
            
            return {
                'status': status,
                'message': message,
                'metadata': {
                    'total_agents': len(agent_metrics),
                    'critical_agents': critical_agents,
                    'warning_agents': warning_agents,
                    'agent_details': agent_metrics
                }
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.DOWN,
                'message': f"Agent health check failed: {str(e)}",
                'metadata': {'error': str(e)}
            }
    
    async def _process_alerts(self):
        """Process health check results and generate alerts"""
        current_time = datetime.now()
        
        # Check for critical or warning states
        for service_name, health in self.services.items():
            if health.status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
                # Create alert
                alert = {
                    'id': f"{service_name}_{current_time.timestamp()}",
                    'service': service_name,
                    'status': health.status.value,
                    'message': health.message,
                    'timestamp': current_time.isoformat(),
                    'metadata': health.metadata
                }
                
                # Add to alerts list
                self.alerts.append(alert)
                
                # Keep only last 100 alerts
                if len(self.alerts) > 100:
                    self.alerts.pop(0)
                
                # Log alert
                logger.warning(f"Alert generated: {alert}")
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        if not self.services:
            return {
                'status': 'unknown',
                'message': 'No health checks have been performed yet',
                'services': {},
                'overall_health': 'unknown'
            }
        
        # Determine overall health
        has_critical = any(s.status == HealthStatus.CRITICAL for s in self.services.values())
        has_warning = any(s.status == HealthStatus.WARNING for s in self.services.values())
        has_down = any(s.status == HealthStatus.DOWN for s in self.services.values())
        
        if has_down or has_critical:
            overall_status = 'critical'
        elif has_warning:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        # Prepare service details
        services_detail = {}
        for service_name, health in self.services.items():
            services_detail[service_name] = {
                'status': health.status.value,
                'message': health.message,
                'response_time': health.response_time,
                'last_check': health.last_check.isoformat(),
                'metadata': health.metadata
            }
        
        return {
            'status': overall_status,
            'message': f"System status: {overall_status}",
            'services': services_detail,
            'overall_health': overall_status,
            'last_check': self.system_stats.get('last_check', datetime.now()).isoformat(),
            'check_duration': self.system_stats.get('check_duration', 0),
            'services_checked': self.system_stats.get('services_checked', 0)
        }
    
    def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get health status for a specific service"""
        if service_name not in self.services:
            return {
                'error': f'Service {service_name} not found',
                'available_services': list(self.services.keys())
            }
        
        health = self.services[service_name]
        return {
            'service': service_name,
            'status': health.status.value,
            'message': health.message,
            'response_time': health.response_time,
            'last_check': health.last_check.isoformat(),
            'metadata': health.metadata
        }
    
    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return self.alerts[-limit:] if self.alerts else []
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all services"""
        metrics = {
            'services': {},
            'system_overview': {
                'total_services': len(self.services),
                'healthy_services': sum(1 for s in self.services.values() if s.status == HealthStatus.HEALTHY),
                'warning_services': sum(1 for s in self.services.values() if s.status == HealthStatus.WARNING),
                'critical_services': sum(1 for s in self.services.values() if s.status == HealthStatus.CRITICAL),
                'down_services': sum(1 for s in self.services.values() if s.status == HealthStatus.DOWN)
            }
        }
        
        # Add individual service metrics
        for service_name, health in self.services.items():
            metrics['services'][service_name] = {
                'status': health.status.value,
                'response_time': health.response_time,
                'last_check': health.last_check.isoformat(),
                'uptime_percentage': self._calculate_uptime(service_name)
            }
        
        return metrics
    
    def _calculate_uptime(self, service_name: str) -> float:
        """Calculate service uptime percentage (simplified)"""
        # For now, return a simplified uptime calculation
        # In a real implementation, this would track historical data
        if service_name in self.services:
            health = self.services[service_name]
            if health.status in [HealthStatus.HEALTHY, HealthStatus.WARNING]:
                return 99.5  # Assume good uptime for healthy/warning services
            else:
                return 95.0  # Lower uptime for critical/down services
        return 0.0

# Global system monitor instance
system_monitor = SystemMonitor()