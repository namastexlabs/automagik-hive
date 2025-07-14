"""
Analytics engine for monitoring dashboard
Provides advanced analytics for agent performance and system insights
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import json
import statistics
from pathlib import Path
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class PerformanceTrend:
    """Performance trend analysis"""
    metric_name: str
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    trend_strength: float  # 0-1
    current_value: float
    previous_value: float
    change_percentage: float
    significance: str  # 'high', 'medium', 'low'

class AnalyticsEngine:
    """
    Advanced analytics engine for monitoring insights
    Provides trend analysis, predictions, and performance insights
    """
    
    def __init__(self, storage_path: str = "logs/analytics"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Analytics cache
        self.analytics_cache: Dict[str, Any] = {}
        self.cache_timestamp: Dict[str, datetime] = {}
        self.cache_ttl = timedelta(minutes=5)  # Cache for 5 minutes
        
        # Performance baselines
        self.performance_baselines: Dict[str, float] = {
            'response_time_baseline': 1.0,  # seconds
            'success_rate_baseline': 95.0,  # percentage
            'memory_usage_baseline': 60.0,  # percentage
            'cpu_usage_baseline': 40.0      # percentage
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is still valid"""
        if cache_key not in self.cache_timestamp:
            return False
        
        return datetime.now() - self.cache_timestamp[cache_key] < self.cache_ttl
    
    def _update_cache(self, cache_key: str, data: Any):
        """Update cache with new data"""
        self.analytics_cache[cache_key] = data
        self.cache_timestamp[cache_key] = datetime.now()
    
    async def generate_performance_report(self, metrics_collector, system_monitor) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        cache_key = "performance_report"
        
        if self._is_cache_valid(cache_key):
            return self.analytics_cache[cache_key]
        
        # Get current metrics
        agent_metrics = metrics_collector.get_agent_metrics()
        system_metrics = metrics_collector.get_system_metrics()
        system_health = system_monitor.get_system_health()
        
        # Analyze performance trends
        performance_trends = await self._analyze_performance_trends(metrics_collector)
        
        # Generate insights
        insights = await self._generate_insights(agent_metrics, system_metrics, performance_trends)
        
        # Calculate performance scores
        performance_scores = await self._calculate_performance_scores(agent_metrics, system_metrics)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(agent_metrics, system_metrics, insights)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'overall_health': system_health.get('overall_health', 'unknown'),
                'total_agents': len(agent_metrics),
                'total_interactions': system_metrics.get('total_requests', 0),
                'active_sessions': system_metrics.get('active_sessions', 0),
                'system_uptime': system_metrics.get('uptime', 0)
            },
            'performance_trends': performance_trends,
            'insights': insights,
            'performance_scores': performance_scores,
            'recommendations': recommendations,
            'detailed_metrics': {
                'agents': agent_metrics,
                'system': system_metrics,
                'health': system_health
            }
        }
        
        self._update_cache(cache_key, report)
        return report
    
    async def _analyze_performance_trends(self, metrics_collector) -> List[Dict[str, Any]]:
        """Analyze performance trends over time"""
        trends = []
        
        try:
            # Get historical data
            hourly_data = metrics_collector.get_analytics_data('hourly')
            daily_data = metrics_collector.get_analytics_data('daily')
            
            # Analyze hourly trends (last 24 hours)
            if hourly_data.get('data'):
                trends.extend(self._analyze_hourly_trends(hourly_data['data']))
            
            # Analyze daily trends (last 7 days)
            if daily_data.get('data'):
                trends.extend(self._analyze_daily_trends(daily_data['data']))
            
        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")
        
        return trends
    
    def _analyze_hourly_trends(self, hourly_data: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze hourly performance trends"""
        trends = []
        
        if len(hourly_data) < 2:
            return trends
        
        # System metrics trends
        memory_usage = [h['system']['memory_usage'] for h in hourly_data]
        cpu_usage = [h['system']['cpu_usage'] for h in hourly_data]
        total_requests = [h['system']['total_requests'] for h in hourly_data]
        
        # Calculate trends
        if len(memory_usage) >= 2:
            trends.append(self._calculate_trend('memory_usage_hourly', memory_usage, 'percentage'))
        
        if len(cpu_usage) >= 2:
            trends.append(self._calculate_trend('cpu_usage_hourly', cpu_usage, 'percentage'))
        
        if len(total_requests) >= 2:
            trends.append(self._calculate_trend('requests_hourly', total_requests, 'count'))
        
        # Agent performance trends
        agent_trends = self._analyze_agent_trends_hourly(hourly_data)
        trends.extend(agent_trends)
        
        return trends
    
    def _analyze_daily_trends(self, daily_data: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze daily performance trends"""
        trends = []
        
        if len(daily_data) < 2:
            return trends
        
        # Daily metrics trends
        total_interactions = [d['total_interactions'] for d in daily_data]
        avg_response_time = [d['average_response_time'] for d in daily_data]
        peak_memory = [d['peak_memory_usage'] for d in daily_data]
        total_errors = [d['total_errors'] for d in daily_data]
        
        # Calculate trends
        if len(total_interactions) >= 2:
            trends.append(self._calculate_trend('interactions_daily', total_interactions, 'count'))
        
        if len(avg_response_time) >= 2:
            trends.append(self._calculate_trend('response_time_daily', avg_response_time, 'seconds'))
        
        if len(peak_memory) >= 2:
            trends.append(self._calculate_trend('peak_memory_daily', peak_memory, 'percentage'))
        
        if len(total_errors) >= 2:
            trends.append(self._calculate_trend('errors_daily', total_errors, 'count'))
        
        return trends
    
    def _analyze_agent_trends_hourly(self, hourly_data: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze agent performance trends from hourly data"""
        agent_trends = []
        
        # Collect agent metrics over time
        agent_metrics_over_time = defaultdict(lambda: defaultdict(list))
        
        for hour_data in hourly_data:
            for agent_name, agent_data in hour_data.get('agents', {}).items():
                agent_metrics_over_time[agent_name]['success_rate'].append(agent_data.get('success_rate', 0))
                agent_metrics_over_time[agent_name]['response_time'].append(agent_data.get('average_response_time', 0))
                agent_metrics_over_time[agent_name]['interactions'].append(agent_data.get('total_interactions', 0))
        
        # Calculate trends for each agent
        for agent_name, metrics in agent_metrics_over_time.items():
            for metric_name, values in metrics.items():
                if len(values) >= 2:
                    trend = self._calculate_trend(f'{agent_name}_{metric_name}', values, 
                                                self._get_metric_unit(metric_name))
                    agent_trends.append(trend)
        
        return agent_trends
    
    def _calculate_trend(self, metric_name: str, values: List[float], unit: str) -> Dict[str, Any]:
        """Calculate trend for a metric"""
        if len(values) < 2:
            return {
                'metric': metric_name,
                'trend': 'insufficient_data',
                'unit': unit
            }
        
        # Calculate trend direction and strength
        current_value = values[-1]
        previous_value = values[-2] if len(values) >= 2 else values[0]
        
        if previous_value == 0:
            change_percentage = 0
        else:
            change_percentage = ((current_value - previous_value) / previous_value) * 100
        
        # Determine trend direction
        if abs(change_percentage) < 5:  # Less than 5% change
            trend_direction = 'stable'
            trend_strength = 0.0
        elif change_percentage > 0:
            trend_direction = 'increasing'
            trend_strength = min(abs(change_percentage) / 20, 1.0)  # Normalize to 0-1
        else:
            trend_direction = 'decreasing'
            trend_strength = min(abs(change_percentage) / 20, 1.0)
        
        # Determine significance
        if abs(change_percentage) >= 20:
            significance = 'high'
        elif abs(change_percentage) >= 10:
            significance = 'medium'
        else:
            significance = 'low'
        
        return {
            'metric': metric_name,
            'trend': trend_direction,
            'strength': trend_strength,
            'current_value': current_value,
            'previous_value': previous_value,
            'change_percentage': change_percentage,
            'significance': significance,
            'unit': unit
        }
    
    def _get_metric_unit(self, metric_name: str) -> str:
        """Get unit for a metric"""
        unit_map = {
            'success_rate': 'percentage',
            'response_time': 'seconds',
            'interactions': 'count',
            'memory_usage': 'percentage',
            'cpu_usage': 'percentage',
            'errors': 'count'
        }
        
        for key, unit in unit_map.items():
            if key in metric_name:
                return unit
        
        return 'unknown'
    
    async def _generate_insights(self, agent_metrics: Dict, system_metrics: Dict, 
                               performance_trends: List[Dict]) -> List[Dict[str, Any]]:
        """Generate actionable insights from metrics"""
        insights = []
        
        # Agent performance insights
        agent_insights = self._analyze_agent_performance_insights(agent_metrics)
        insights.extend(agent_insights)
        
        # System performance insights
        system_insights = self._analyze_system_performance_insights(system_metrics)
        insights.extend(system_insights)
        
        # Trend-based insights
        trend_insights = self._analyze_trend_insights(performance_trends)
        insights.extend(trend_insights)
        
        # Anomaly detection insights
        anomaly_insights = await self._detect_anomalies(agent_metrics, system_metrics)
        insights.extend(anomaly_insights)
        
        return insights
    
    def _analyze_agent_performance_insights(self, agent_metrics: Dict) -> List[Dict[str, Any]]:
        """Analyze agent performance for insights"""
        insights = []
        
        if not agent_metrics:
            return insights
        
        # Find best and worst performing agents
        agent_performance = []
        
        for agent_name, metrics in agent_metrics.items():
            if isinstance(metrics, dict) and 'success_rate' in metrics:
                agent_performance.append({
                    'name': agent_name,
                    'success_rate': metrics['success_rate'],
                    'response_time': metrics.get('average_response_time', 0),
                    'total_interactions': metrics.get('total_interactions', 0)
                })
        
        if not agent_performance:
            return insights
        
        # Sort by success rate
        agent_performance.sort(key=lambda x: x['success_rate'], reverse=True)
        
        # Best performer insight
        best_agent = agent_performance[0]
        if best_agent['success_rate'] > 95:
            insights.append({
                'type': 'positive',
                'category': 'agent_performance',
                'title': 'Top Performing Agent',
                'message': f"{best_agent['name']} is performing excellently with {best_agent['success_rate']:.1f}% success rate",
                'severity': 'info',
                'agent_name': best_agent['name']
            })
        
        # Worst performer insight
        worst_agent = agent_performance[-1]
        if worst_agent['success_rate'] < 90:
            insights.append({
                'type': 'warning',
                'category': 'agent_performance',
                'title': 'Underperforming Agent',
                'message': f"{worst_agent['name']} needs attention with {worst_agent['success_rate']:.1f}% success rate",
                'severity': 'warning',
                'agent_name': worst_agent['name'],
                'recommended_action': 'Review agent configuration and training data'
            })
        
        # High response time insight
        slow_agents = [a for a in agent_performance if a['response_time'] > 3.0]
        if slow_agents:
            insights.append({
                'type': 'warning',
                'category': 'performance',
                'title': 'High Response Times',
                'message': f"{len(slow_agents)} agents have response times above 3 seconds",
                'severity': 'warning',
                'affected_agents': [a['name'] for a in slow_agents],
                'recommended_action': 'Optimize agent processing logic or increase resources'
            })
        
        return insights
    
    def _analyze_system_performance_insights(self, system_metrics: Dict) -> List[Dict[str, Any]]:
        """Analyze system performance for insights"""
        insights = []
        
        # Memory usage insights
        memory_usage = system_metrics.get('memory_usage', 0)
        if memory_usage > 85:
            insights.append({
                'type': 'warning',
                'category': 'system_resources',
                'title': 'High Memory Usage',
                'message': f"Memory usage is at {memory_usage:.1f}%",
                'severity': 'warning' if memory_usage < 95 else 'critical',
                'recommended_action': 'Consider increasing memory or optimizing memory usage'
            })
        
        # CPU usage insights
        cpu_usage = system_metrics.get('cpu_usage', 0)
        if cpu_usage > 80:
            insights.append({
                'type': 'warning',
                'category': 'system_resources',
                'title': 'High CPU Usage',
                'message': f"CPU usage is at {cpu_usage:.1f}%",
                'severity': 'warning' if cpu_usage < 95 else 'critical',
                'recommended_action': 'Consider scaling resources or optimizing CPU-intensive operations'
            })
        
        # Active sessions insight
        active_sessions = system_metrics.get('active_sessions', 0)
        total_requests = system_metrics.get('total_requests', 0)
        
        if active_sessions > 100:
            insights.append({
                'type': 'info',
                'category': 'system_load',
                'title': 'High Session Activity',
                'message': f"Currently handling {active_sessions} active sessions",
                'severity': 'info',
                'recommended_action': 'Monitor for potential scaling needs'
            })
        
        return insights
    
    def _analyze_trend_insights(self, performance_trends: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze trends for insights"""
        insights = []
        
        for trend in performance_trends:
            if trend['significance'] == 'high':
                if trend['trend'] == 'increasing':
                    if 'error' in trend['metric'] or 'response_time' in trend['metric']:
                        insights.append({
                            'type': 'warning',
                            'category': 'performance_trend',
                            'title': 'Degrading Performance Trend',
                            'message': f"{trend['metric']} is increasing significantly ({trend['change_percentage']:.1f}%)",
                            'severity': 'warning',
                            'trend_data': trend,
                            'recommended_action': 'Investigate root cause and implement corrective measures'
                        })
                    elif 'success_rate' in trend['metric'] or 'interactions' in trend['metric']:
                        insights.append({
                            'type': 'positive',
                            'category': 'performance_trend',
                            'title': 'Improving Performance Trend',
                            'message': f"{trend['metric']} is improving significantly ({trend['change_percentage']:.1f}%)",
                            'severity': 'info',
                            'trend_data': trend
                        })
                
                elif trend['trend'] == 'decreasing':
                    if 'success_rate' in trend['metric'] or 'interactions' in trend['metric']:
                        insights.append({
                            'type': 'warning',
                            'category': 'performance_trend',
                            'title': 'Declining Performance Trend',
                            'message': f"{trend['metric']} is decreasing significantly ({trend['change_percentage']:.1f}%)",
                            'severity': 'warning',
                            'trend_data': trend,
                            'recommended_action': 'Investigate cause of performance decline'
                        })
        
        return insights
    
    async def _detect_anomalies(self, agent_metrics: Dict, system_metrics: Dict) -> List[Dict[str, Any]]:
        """Detect anomalies in metrics"""
        anomalies = []
        
        # Check for statistical anomalies in agent performance
        for agent_name, metrics in agent_metrics.items():
            if isinstance(metrics, dict):
                # Response time anomaly
                response_time = metrics.get('average_response_time', 0)
                if response_time > self.performance_baselines['response_time_baseline'] * 3:
                    anomalies.append({
                        'type': 'anomaly',
                        'category': 'performance_anomaly',
                        'title': 'Response Time Anomaly',
                        'message': f"{agent_name} response time ({response_time:.2f}s) is significantly above baseline",
                        'severity': 'warning',
                        'agent_name': agent_name,
                        'metric': 'response_time',
                        'value': response_time,
                        'baseline': self.performance_baselines['response_time_baseline']
                    })
                
                # Success rate anomaly
                success_rate = metrics.get('success_rate', 0)
                if success_rate < self.performance_baselines['success_rate_baseline'] * 0.8:
                    anomalies.append({
                        'type': 'anomaly',
                        'category': 'performance_anomaly',
                        'title': 'Success Rate Anomaly',
                        'message': f"{agent_name} success rate ({success_rate:.1f}%) is significantly below baseline",
                        'severity': 'critical',
                        'agent_name': agent_name,
                        'metric': 'success_rate',
                        'value': success_rate,
                        'baseline': self.performance_baselines['success_rate_baseline']
                    })
        
        return anomalies
    
    async def _calculate_performance_scores(self, agent_metrics: Dict, system_metrics: Dict) -> Dict[str, Any]:
        """Calculate performance scores"""
        scores = {}
        
        # Agent performance scores
        agent_scores = {}
        for agent_name, metrics in agent_metrics.items():
            if isinstance(metrics, dict):
                # Calculate composite score (0-100)
                success_rate = metrics.get('success_rate', 0)
                response_time = metrics.get('average_response_time', 0)
                
                # Success rate weight: 70%
                success_score = success_rate * 0.7
                
                # Response time weight: 30% (inverted, lower is better)
                response_time_score = max(0, (5 - response_time) / 5) * 30
                
                composite_score = success_score + response_time_score
                agent_scores[agent_name] = {
                    'composite_score': composite_score,
                    'success_rate_score': success_score,
                    'response_time_score': response_time_score,
                    'grade': self._get_performance_grade(composite_score)
                }
        
        scores['agents'] = agent_scores
        
        # System performance score
        memory_usage = system_metrics.get('memory_usage', 0)
        cpu_usage = system_metrics.get('cpu_usage', 0)
        
        # System health score (0-100)
        memory_score = max(0, (100 - memory_usage))
        cpu_score = max(0, (100 - cpu_usage))
        
        system_score = (memory_score + cpu_score) / 2
        scores['system'] = {
            'composite_score': system_score,
            'memory_score': memory_score,
            'cpu_score': cpu_score,
            'grade': self._get_performance_grade(system_score)
        }
        
        # Overall performance score
        if agent_scores:
            avg_agent_score = sum(a['composite_score'] for a in agent_scores.values()) / len(agent_scores)
            overall_score = (avg_agent_score + system_score) / 2
        else:
            overall_score = system_score
        
        scores['overall'] = {
            'score': overall_score,
            'grade': self._get_performance_grade(overall_score)
        }
        
        return scores
    
    def _get_performance_grade(self, score: float) -> str:
        """Get performance grade based on score"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    async def _generate_recommendations(self, agent_metrics: Dict, system_metrics: Dict, 
                                      insights: List[Dict]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Performance optimization recommendations
        memory_usage = system_metrics.get('memory_usage', 0)
        if memory_usage > 80:
            recommendations.append({
                'category': 'resource_optimization',
                'priority': 'high' if memory_usage > 90 else 'medium',
                'title': 'Memory Optimization',
                'description': 'System memory usage is high and may impact performance',
                'action': 'Implement memory optimization strategies or increase system memory',
                'estimated_impact': 'High',
                'implementation_effort': 'Medium'
            })
        
        # Agent optimization recommendations
        for agent_name, metrics in agent_metrics.items():
            if isinstance(metrics, dict):
                success_rate = metrics.get('success_rate', 0)
                response_time = metrics.get('average_response_time', 0)
                
                if success_rate < 90:
                    recommendations.append({
                        'category': 'agent_optimization',
                        'priority': 'high' if success_rate < 85 else 'medium',
                        'title': f'Improve {agent_name} Performance',
                        'description': f'Agent success rate is {success_rate:.1f}%, below optimal threshold',
                        'action': 'Review agent prompts, training data, and error handling',
                        'estimated_impact': 'High',
                        'implementation_effort': 'Medium',
                        'agent_name': agent_name
                    })
                
                if response_time > 3.0:
                    recommendations.append({
                        'category': 'performance_optimization',
                        'priority': 'medium',
                        'title': f'Optimize {agent_name} Response Time',
                        'description': f'Agent response time is {response_time:.2f}s, above optimal threshold',
                        'action': 'Optimize agent processing logic or increase computational resources',
                        'estimated_impact': 'Medium',
                        'implementation_effort': 'Low',
                        'agent_name': agent_name
                    })
        
        # Scaling recommendations
        total_requests = system_metrics.get('total_requests', 0)
        active_sessions = system_metrics.get('active_sessions', 0)
        
        if active_sessions > 50:
            recommendations.append({
                'category': 'scaling',
                'priority': 'medium',
                'title': 'Consider Horizontal Scaling',
                'description': f'High session activity ({active_sessions} active sessions) may benefit from scaling',
                'action': 'Implement load balancing and consider adding more instances',
                'estimated_impact': 'High',
                'implementation_effort': 'High'
            })
        
        # Security recommendations
        recommendations.append({
            'category': 'security',
            'priority': 'low',
            'title': 'Regular Security Audit',
            'description': 'Perform regular security assessments to maintain system integrity',
            'action': 'Schedule monthly security audits and vulnerability assessments',
            'estimated_impact': 'Medium',
            'implementation_effort': 'Low'
        })
        
        return recommendations
    
    async def get_typification_analytics(self, metrics_collector) -> Dict[str, Any]:
        """Get analytics specifically for typification accuracy"""
        # This would integrate with T-004 typification data
        # For now, return placeholder analytics
        return {
            'typification_accuracy': {
                'overall_accuracy': 85.5,
                'by_category': {
                    'adquirencia': 88.2,
                    'emissao': 82.1,
                    'pagbank': 86.7,
                    'human_handoff': 91.3
                },
                'improvement_trend': 2.3,  # % improvement over time
                'misclassification_rate': 14.5
            },
            'recommendations': [
                {
                    'type': 'training_improvement',
                    'message': 'Emissão category needs additional training examples',
                    'priority': 'high'
                }
            ]
        }
    
    async def get_versioning_analytics(self, metrics_collector) -> Dict[str, Any]:
        """Get analytics specifically for versioning effectiveness"""
        # This would integrate with T-005 versioning data
        # For now, return placeholder analytics
        return {
            'version_performance': {
                'current_version': '2.1.0',
                'version_comparison': {
                    '2.1.0': {'success_rate': 92.3, 'response_time': 1.8},
                    '2.0.0': {'success_rate': 88.1, 'response_time': 2.2},
                    '1.9.0': {'success_rate': 85.7, 'response_time': 2.5}
                },
                'rollback_rate': 2.1,  # % of deployments rolled back
                'version_adoption_rate': 98.5  # % of agents on latest version
            },
            'recommendations': [
                {
                    'type': 'version_optimization',
                    'message': 'Version 2.1.0 shows 4.2% improvement over 2.0.0',
                    'priority': 'info'
                }
            ]
        }

# Global analytics engine instance
analytics_engine = AnalyticsEngine()