"""
Metrics collection system for agent performance monitoring
Tracks agent interactions, response times, and success rates
"""

import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import deque
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class AgentMetrics:
    """Agent performance metrics data structure"""
    agent_name: str
    total_interactions: int = 0
    successful_interactions: int = 0
    failed_interactions: int = 0
    average_response_time: float = 0.0
    last_interaction_time: Optional[datetime] = None
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    error_history: deque = field(default_factory=lambda: deque(maxlen=50))
    success_rate: float = 0.0
    
    def update_success_rate(self):
        """Update success rate calculation"""
        if self.total_interactions > 0:
            self.success_rate = (self.successful_interactions / self.total_interactions) * 100
        else:
            self.success_rate = 0.0
    
    def update_average_response_time(self):
        """Update average response time calculation"""
        if self.response_times:
            self.average_response_time = sum(self.response_times) / len(self.response_times)
        else:
            self.average_response_time = 0.0

@dataclass
class SystemMetrics:
    """System-wide performance metrics"""
    total_requests: int = 0
    active_sessions: int = 0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    response_time_p95: float = 0.0
    response_time_p99: float = 0.0
    error_rate: float = 0.0
    uptime: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)

class MetricsCollector:
    """
    Centralized metrics collection system
    Tracks agent performance, system health, and user interactions
    """
    
    def __init__(self, storage_path: str = "logs/metrics"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Agent metrics storage
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        
        # System metrics
        self.system_metrics = SystemMetrics()
        
        # Time-series data for analytics
        self.hourly_metrics: deque = deque(maxlen=24*7)  # 7 days of hourly data
        self.daily_metrics: deque = deque(maxlen=30)     # 30 days of daily data
        
        # Real-time monitoring
        self.active_interactions: Dict[str, Dict[str, Any]] = {}
        self.recent_errors: deque = deque(maxlen=100)
        
        # Performance thresholds
        self.thresholds = {
            'response_time_warning': 2.0,    # seconds
            'response_time_critical': 5.0,   # seconds
            'success_rate_warning': 95.0,    # percentage
            'success_rate_critical': 90.0,   # percentage
            'memory_usage_warning': 80.0,    # percentage
            'memory_usage_critical': 90.0,   # percentage
        }
        
        # Start background tasks
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background monitoring tasks"""
        # Don't start tasks during import - no event loop yet
        self._tasks_started = False
    
    def start_monitoring(self):
        """Start monitoring tasks when event loop is ready"""
        if not self._tasks_started:
            asyncio.create_task(self._periodic_aggregation())
            asyncio.create_task(self._system_health_check())
            self._tasks_started = True
    
    async def _periodic_aggregation(self):
        """Periodically aggregate metrics for analytics"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                await self._aggregate_hourly_metrics()
                
                # Daily aggregation at midnight
                if datetime.now().hour == 0:
                    await self._aggregate_daily_metrics()
                    
            except Exception as e:
                logger.error(f"Error in periodic aggregation: {e}")
    
    async def _system_health_check(self):
        """Monitor system health metrics"""
        import psutil
        
        while True:
            try:
                # Update system metrics
                self.system_metrics.memory_usage = psutil.virtual_memory().percent
                self.system_metrics.cpu_usage = psutil.cpu_percent(interval=1)
                self.system_metrics.uptime = (datetime.now() - self.system_metrics.start_time).total_seconds()
                
                await asyncio.sleep(30)  # Every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in system health check: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute
    
    def start_interaction(self, agent_name: str, user_id: str, session_id: str, 
                         message: str, metadata: Optional[Dict] = None) -> str:
        """
        Start tracking an agent interaction
        
        Args:
            agent_name: Name of the agent handling the interaction
            user_id: User identifier
            session_id: Session identifier
            message: User message
            metadata: Additional context
            
        Returns:
            Interaction ID for tracking
        """
        interaction_id = f"{agent_name}_{user_id}_{session_id}_{int(time.time())}"
        
        self.active_interactions[interaction_id] = {
            'agent_name': agent_name,
            'user_id': user_id,
            'session_id': session_id,
            'message': message,
            'metadata': metadata or {},
            'start_time': datetime.now(),
            'status': 'active'
        }
        
        # Initialize agent metrics if not exists
        if agent_name not in self.agent_metrics:
            self.agent_metrics[agent_name] = AgentMetrics(agent_name=agent_name)
        
        return interaction_id
    
    def end_interaction(self, interaction_id: str, success: bool = True, 
                       response: Optional[str] = None, error: Optional[str] = None):
        """
        End tracking an agent interaction
        
        Args:
            interaction_id: Interaction ID from start_interaction
            success: Whether the interaction was successful
            response: Agent response (if successful)
            error: Error message (if failed)
        """
        if interaction_id not in self.active_interactions:
            logger.warning(f"Interaction {interaction_id} not found in active interactions")
            return
        
        interaction = self.active_interactions[interaction_id]
        agent_name = interaction['agent_name']
        
        # Calculate response time
        response_time = (datetime.now() - interaction['start_time']).total_seconds()
        
        # Update agent metrics
        agent_metrics = self.agent_metrics[agent_name]
        agent_metrics.total_interactions += 1
        agent_metrics.response_times.append(response_time)
        agent_metrics.last_interaction_time = datetime.now()
        
        if success:
            agent_metrics.successful_interactions += 1
        else:
            agent_metrics.failed_interactions += 1
            agent_metrics.error_history.append({
                'timestamp': datetime.now(),
                'error': error,
                'user_id': interaction['user_id'],
                'message': interaction['message']
            })
            
            # Add to recent errors
            self.recent_errors.append({
                'timestamp': datetime.now(),
                'agent_name': agent_name,
                'error': error,
                'interaction_id': interaction_id
            })
        
        # Update calculated metrics
        agent_metrics.update_success_rate()
        agent_metrics.update_average_response_time()
        
        # Update system metrics
        self.system_metrics.total_requests += 1
        
        # Mark interaction as completed
        interaction['status'] = 'completed'
        interaction['end_time'] = datetime.now()
        interaction['response_time'] = response_time
        interaction['success'] = success
        interaction['response'] = response
        interaction['error'] = error
        
        # Archive the interaction
        self._archive_interaction(interaction_id, interaction)
        
        # Remove from active interactions
        del self.active_interactions[interaction_id]
    
    def _archive_interaction(self, interaction_id: str, interaction: Dict[str, Any]):
        """Archive completed interaction for analytics"""
        archive_file = self.storage_path / f"interactions_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        try:
            with open(archive_file, 'a') as f:
                # Convert datetime objects to ISO format
                archived_interaction = interaction.copy()
                archived_interaction['start_time'] = interaction['start_time'].isoformat()
                archived_interaction['end_time'] = interaction['end_time'].isoformat()
                archived_interaction['interaction_id'] = interaction_id
                
                f.write(json.dumps(archived_interaction) + '\n')
        except Exception as e:
            logger.error(f"Error archiving interaction {interaction_id}: {e}")
    
    async def _aggregate_hourly_metrics(self):
        """Aggregate metrics for the current hour"""
        now = datetime.now()
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        
        # Aggregate agent metrics
        agent_summaries = {}
        for agent_name, metrics in self.agent_metrics.items():
            agent_summaries[agent_name] = {
                'total_interactions': metrics.total_interactions,
                'success_rate': metrics.success_rate,
                'average_response_time': metrics.average_response_time,
                'recent_errors': len([e for e in metrics.error_history 
                                    if e['timestamp'] >= hour_start])
            }
        
        hourly_summary = {
            'timestamp': hour_start,
            'agents': agent_summaries,
            'system': {
                'total_requests': self.system_metrics.total_requests,
                'active_sessions': self.system_metrics.active_sessions,
                'memory_usage': self.system_metrics.memory_usage,
                'cpu_usage': self.system_metrics.cpu_usage,
                'error_rate': self.system_metrics.error_rate
            }
        }
        
        self.hourly_metrics.append(hourly_summary)
    
    async def _aggregate_daily_metrics(self):
        """Aggregate metrics for the current day"""
        now = datetime.now()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Use hourly metrics to calculate daily summaries
        today_hourly = [h for h in self.hourly_metrics 
                       if h['timestamp'] >= day_start]
        
        if not today_hourly:
            return
        
        # Aggregate daily metrics
        daily_summary = {
            'timestamp': day_start,
            'total_interactions': sum(h['system']['total_requests'] for h in today_hourly),
            'average_response_time': sum(
                sum(agent_data['average_response_time'] for agent_data in h['agents'].values()) 
                for h in today_hourly
            ) / len(today_hourly) if today_hourly else 0,
            'peak_memory_usage': max(h['system']['memory_usage'] for h in today_hourly),
            'peak_cpu_usage': max(h['system']['cpu_usage'] for h in today_hourly),
            'total_errors': sum(
                sum(agent_data['recent_errors'] for agent_data in h['agents'].values()) 
                for h in today_hourly
            )
        }
        
        self.daily_metrics.append(daily_summary)
    
    def get_agent_metrics(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get agent performance metrics"""
        if agent_name:
            if agent_name in self.agent_metrics:
                metrics = self.agent_metrics[agent_name]
                return {
                    'agent_name': metrics.agent_name,
                    'total_interactions': metrics.total_interactions,
                    'successful_interactions': metrics.successful_interactions,
                    'failed_interactions': metrics.failed_interactions,
                    'success_rate': metrics.success_rate,
                    'average_response_time': metrics.average_response_time,
                    'last_interaction_time': metrics.last_interaction_time.isoformat() if metrics.last_interaction_time else None,
                    'recent_errors': list(metrics.error_history)[-10:],  # Last 10 errors
                    'response_time_distribution': {
                        'p50': self._calculate_percentile(list(metrics.response_times), 50),
                        'p90': self._calculate_percentile(list(metrics.response_times), 90),
                        'p95': self._calculate_percentile(list(metrics.response_times), 95),
                        'p99': self._calculate_percentile(list(metrics.response_times), 99),
                    }
                }
            else:
                return {'error': f'Agent {agent_name} not found'}
        else:
            # Return all agents
            return {
                agent_name: {
                    'total_interactions': metrics.total_interactions,
                    'success_rate': metrics.success_rate,
                    'average_response_time': metrics.average_response_time,
                    'last_interaction_time': metrics.last_interaction_time.isoformat() if metrics.last_interaction_time else None
                }
                for agent_name, metrics in self.agent_metrics.items()
            }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide performance metrics"""
        return {
            'total_requests': self.system_metrics.total_requests,
            'active_sessions': self.system_metrics.active_sessions,
            'active_interactions': len(self.active_interactions),
            'memory_usage': self.system_metrics.memory_usage,
            'cpu_usage': self.system_metrics.cpu_usage,
            'uptime': self.system_metrics.uptime,
            'start_time': self.system_metrics.start_time.isoformat(),
            'recent_errors': list(self.recent_errors)[-20:],  # Last 20 errors
            'system_health': self._get_system_health_status()
        }
    
    def get_analytics_data(self, period: str = 'hourly') -> Dict[str, Any]:
        """Get analytics data for dashboard"""
        if period == 'hourly':
            return {
                'period': 'hourly',
                'data': list(self.hourly_metrics),
                'summary': self._get_hourly_summary()
            }
        elif period == 'daily':
            return {
                'period': 'daily', 
                'data': list(self.daily_metrics),
                'summary': self._get_daily_summary()
            }
        else:
            return {'error': f'Unknown period: {period}'}
    
    def _get_system_health_status(self) -> Dict[str, Any]:
        """Determine system health status"""
        status = 'healthy'
        issues = []
        
        # Check memory usage
        if self.system_metrics.memory_usage > self.thresholds['memory_usage_critical']:
            status = 'critical'
            issues.append(f"Memory usage critical: {self.system_metrics.memory_usage:.1f}%")
        elif self.system_metrics.memory_usage > self.thresholds['memory_usage_warning']:
            if status == 'healthy':
                status = 'warning'
            issues.append(f"Memory usage high: {self.system_metrics.memory_usage:.1f}%")
        
        # Check agent success rates
        for agent_name, metrics in self.agent_metrics.items():
            if metrics.success_rate < self.thresholds['success_rate_critical']:
                status = 'critical'
                issues.append(f"Agent {agent_name} success rate critical: {metrics.success_rate:.1f}%")
            elif metrics.success_rate < self.thresholds['success_rate_warning']:
                if status == 'healthy':
                    status = 'warning'
                issues.append(f"Agent {agent_name} success rate low: {metrics.success_rate:.1f}%")
        
        # Check response times
        for agent_name, metrics in self.agent_metrics.items():
            if metrics.average_response_time > self.thresholds['response_time_critical']:
                status = 'critical'
                issues.append(f"Agent {agent_name} response time critical: {metrics.average_response_time:.1f}s")
            elif metrics.average_response_time > self.thresholds['response_time_warning']:
                if status == 'healthy':
                    status = 'warning'
                issues.append(f"Agent {agent_name} response time high: {metrics.average_response_time:.1f}s")
        
        return {
            'status': status,
            'issues': issues,
            'last_check': datetime.now().isoformat()
        }
    
    def _get_hourly_summary(self) -> Dict[str, Any]:
        """Get summary of hourly metrics"""
        if not self.hourly_metrics:
            return {}
        
        recent_hours = list(self.hourly_metrics)[-24:]  # Last 24 hours
        
        return {
            'total_interactions_24h': sum(h['system']['total_requests'] for h in recent_hours),
            'average_memory_usage_24h': sum(h['system']['memory_usage'] for h in recent_hours) / len(recent_hours),
            'average_cpu_usage_24h': sum(h['system']['cpu_usage'] for h in recent_hours) / len(recent_hours),
            'peak_interactions_hour': max(h['system']['total_requests'] for h in recent_hours),
            'agent_performance_24h': self._get_agent_performance_summary(recent_hours)
        }
    
    def _get_daily_summary(self) -> Dict[str, Any]:
        """Get summary of daily metrics"""
        if not self.daily_metrics:
            return {}
        
        recent_days = list(self.daily_metrics)[-7:]  # Last 7 days
        
        return {
            'total_interactions_7d': sum(d['total_interactions'] for d in recent_days),
            'average_response_time_7d': sum(d['average_response_time'] for d in recent_days) / len(recent_days),
            'peak_memory_usage_7d': max(d['peak_memory_usage'] for d in recent_days),
            'peak_cpu_usage_7d': max(d['peak_cpu_usage'] for d in recent_days),
            'total_errors_7d': sum(d['total_errors'] for d in recent_days)
        }
    
    def _get_agent_performance_summary(self, hourly_data: List[Dict]) -> Dict[str, Any]:
        """Get agent performance summary from hourly data"""
        agent_summary = {}
        
        for hour_data in hourly_data:
            for agent_name, agent_data in hour_data['agents'].items():
                if agent_name not in agent_summary:
                    agent_summary[agent_name] = {
                        'total_interactions': 0,
                        'response_times': [],
                        'success_rates': [],
                        'errors': 0
                    }
                
                agent_summary[agent_name]['total_interactions'] += agent_data['total_interactions']
                agent_summary[agent_name]['response_times'].append(agent_data['average_response_time'])
                agent_summary[agent_name]['success_rates'].append(agent_data['success_rate'])
                agent_summary[agent_name]['errors'] += agent_data['recent_errors']
        
        # Calculate averages
        for agent_name, data in agent_summary.items():
            data['average_response_time'] = sum(data['response_times']) / len(data['response_times']) if data['response_times'] else 0
            data['average_success_rate'] = sum(data['success_rates']) / len(data['success_rates']) if data['success_rates'] else 0
            del data['response_times']
            del data['success_rates']
        
        return agent_summary
    
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of a list of values"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            weight = index - lower_index
            return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight

# Global metrics collector instance
metrics_collector = MetricsCollector()