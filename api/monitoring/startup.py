"""
Monitoring system startup and initialization
Handles background tasks and system setup
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from .config import monitoring_config, monitoring_features
from .metrics_collector import metrics_collector
from .system_monitor import system_monitor
from .alert_manager import alert_manager
from .analytics_engine import analytics_engine

logger = logging.getLogger(__name__)

class MonitoringSystemManager:
    """
    Manages the monitoring system lifecycle
    Handles startup, shutdown, and background tasks
    """
    
    def __init__(self):
        self.running = False
        self.background_tasks = []
        self.system_start_time = datetime.now()
    
    async def start_monitoring_system(self):
        """Start the complete monitoring system"""
        if self.running:
            logger.warning("Monitoring system is already running")
            return
        
        logger.info("Starting PagBank monitoring system...")
        
        try:
            # Initialize components
            await self._initialize_components()
            
            # Start background tasks
            await self._start_background_tasks()
            
            # Start system monitoring
            if monitoring_features['system_health_checks']:
                await self._start_system_monitoring()
            
            # Start periodic alert evaluation
            if monitoring_features['alerting']:
                await self._start_alert_evaluation()
            
            self.running = True
            logger.info("Monitoring system started successfully")
            
        except Exception as e:
            logger.error(f"Error starting monitoring system: {e}")
            raise
    
    async def stop_monitoring_system(self):
        """Stop the monitoring system"""
        if not self.running:
            logger.warning("Monitoring system is not running")
            return
        
        logger.info("Stopping monitoring system...")
        
        try:
            # Stop system monitoring
            system_monitor.stop_monitoring()
            
            # Cancel background tasks
            for task in self.background_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            self.background_tasks.clear()
            self.running = False
            
            logger.info("Monitoring system stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping monitoring system: {e}")
            raise
    
    async def _initialize_components(self):
        """Initialize monitoring components"""
        logger.info("Initializing monitoring components...")
        
        # Initialize metrics collector
        if monitoring_features['metrics_collection']:
            logger.info("Metrics collection enabled")
        
        # Initialize system monitor
        if monitoring_features['system_health_checks']:
            logger.info("System health checks enabled")
        
        # Initialize alert manager
        if monitoring_features['alerting']:
            logger.info("Alert system enabled")
        
        # Initialize analytics engine
        if monitoring_features['analytics']:
            logger.info("Analytics engine enabled")
        
        logger.info("Monitoring components initialized")
    
    async def _start_background_tasks(self):
        """Start background monitoring tasks"""
        logger.info("Starting background monitoring tasks...")
        
        # Start metrics aggregation task
        if monitoring_features['metrics_collection']:
            aggregation_task = asyncio.create_task(self._metrics_aggregation_loop())
            self.background_tasks.append(aggregation_task)
        
        # Start analytics update task
        if monitoring_features['analytics']:
            analytics_task = asyncio.create_task(self._analytics_update_loop())
            self.background_tasks.append(analytics_task)
        
        # Start cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.background_tasks.append(cleanup_task)
        
        logger.info("Background tasks started")
    
    async def _start_system_monitoring(self):
        """Start system health monitoring"""
        logger.info("Starting system health monitoring...")
        
        # Start system monitor in background
        monitoring_task = asyncio.create_task(system_monitor.start_monitoring())
        self.background_tasks.append(monitoring_task)
        
        logger.info("System health monitoring started")
    
    async def _start_alert_evaluation(self):
        """Start periodic alert evaluation"""
        logger.info("Starting alert evaluation...")
        
        # Start alert evaluation loop
        alert_task = asyncio.create_task(self._alert_evaluation_loop())
        self.background_tasks.append(alert_task)
        
        logger.info("Alert evaluation started")
    
    async def _metrics_aggregation_loop(self):
        """Background task for metrics aggregation"""
        while self.running:
            try:
                await asyncio.sleep(monitoring_config.collection_interval_seconds)
                
                # Trigger metrics aggregation
                await self._trigger_metrics_aggregation()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics aggregation loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _analytics_update_loop(self):
        """Background task for analytics updates"""
        while self.running:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Update analytics cache
                await self._update_analytics_cache()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in analytics update loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _alert_evaluation_loop(self):
        """Background task for alert evaluation"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Every minute
                
                # Evaluate alerts
                await self._evaluate_system_alerts()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert evaluation loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _cleanup_loop(self):
        """Background task for cleanup operations"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Every hour
                
                # Perform cleanup
                await self._perform_cleanup()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(300)  # Wait before retrying
    
    async def _trigger_metrics_aggregation(self):
        """Trigger metrics aggregation"""
        try:
            # This would typically trigger aggregation in the metrics collector
            # For now, just log the operation
            logger.debug("Triggering metrics aggregation")
            
        except Exception as e:
            logger.error(f"Error triggering metrics aggregation: {e}")
    
    async def _update_analytics_cache(self):
        """Update analytics cache"""
        try:
            # Update analytics cache
            await analytics_engine.generate_performance_report(metrics_collector, system_monitor)
            logger.debug("Analytics cache updated")
            
        except Exception as e:
            logger.error(f"Error updating analytics cache: {e}")
    
    async def _evaluate_system_alerts(self):
        """Evaluate system alerts"""
        try:
            # Get current metrics
            system_metrics = metrics_collector.get_system_metrics()
            agent_metrics = metrics_collector.get_agent_metrics()
            system_health = system_monitor.get_system_health()
            
            # Prepare metrics for alert evaluation
            evaluation_metrics = {
                "system": system_metrics,
                "agents": agent_metrics,
                "services": system_health.get("services", {})
            }
            
            # Evaluate alerts
            await alert_manager.evaluate_alerts(evaluation_metrics)
            
        except Exception as e:
            logger.error(f"Error evaluating system alerts: {e}")
    
    async def _perform_cleanup(self):
        """Perform cleanup operations"""
        try:
            # Clean up old metrics files
            await self._cleanup_old_metrics()
            
            # Clean up old alerts
            await self._cleanup_old_alerts()
            
            # Clean up analytics cache
            await self._cleanup_analytics_cache()
            
            logger.debug("Cleanup operations completed")
            
        except Exception as e:
            logger.error(f"Error performing cleanup: {e}")
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics files"""
        try:
            from pathlib import Path
            import time
            
            metrics_path = Path(monitoring_config.metrics_storage_path)
            
            if metrics_path.exists():
                current_time = time.time()
                retention_seconds = monitoring_config.metrics_retention_days * 24 * 3600
                
                for file_path in metrics_path.glob("*.jsonl"):
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > retention_seconds:
                        file_path.unlink()
                        logger.debug(f"Deleted old metrics file: {file_path}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")
    
    async def _cleanup_old_alerts(self):
        """Clean up old alerts"""
        try:
            # Keep only the last 1000 alerts in history
            if len(alert_manager.alert_history) > 1000:
                alert_manager.alert_history = alert_manager.alert_history[-1000:]
                logger.debug("Cleaned up old alerts from history")
                
        except Exception as e:
            logger.error(f"Error cleaning up old alerts: {e}")
    
    async def _cleanup_analytics_cache(self):
        """Clean up analytics cache"""
        try:
            # Clear expired cache entries
            current_time = datetime.now()
            expired_keys = []
            
            for key, timestamp in analytics_engine.cache_timestamp.items():
                if current_time - timestamp > analytics_engine.cache_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del analytics_engine.analytics_cache[key]
                del analytics_engine.cache_timestamp[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                
        except Exception as e:
            logger.error(f"Error cleaning up analytics cache: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get monitoring system status"""
        return {
            'running': self.running,
            'start_time': self.system_start_time.isoformat(),
            'uptime_seconds': (datetime.now() - self.system_start_time).total_seconds(),
            'active_tasks': len(self.background_tasks),
            'components': {
                'metrics_collection': monitoring_features['metrics_collection'],
                'system_health_checks': monitoring_features['system_health_checks'],
                'alerting': monitoring_features['alerting'],
                'analytics': monitoring_features['analytics'],
                'dashboard': monitoring_features['dashboard']
            },
            'configuration': {
                'collection_interval': monitoring_config.collection_interval_seconds,
                'health_check_interval': monitoring_config.health_check_interval_seconds,
                'alert_cooldown': monitoring_config.alert_cooldown_minutes,
                'metrics_retention_days': monitoring_config.metrics_retention_days
            }
        }

# Global monitoring system manager instance
monitoring_system = MonitoringSystemManager()

# Convenience functions
async def start_monitoring():
    """Start the monitoring system"""
    await monitoring_system.start_monitoring_system()

async def stop_monitoring():
    """Stop the monitoring system"""
    await monitoring_system.stop_monitoring_system()

def get_monitoring_status():
    """Get monitoring system status"""
    return monitoring_system.get_system_status()