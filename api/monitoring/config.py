"""
Configuration for the monitoring system
Contains settings for metrics collection, alerting, and analytics
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class MonitoringLevel(Enum):
    """Monitoring detail levels"""
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"

@dataclass
class MonitoringConfig:
    """Configuration for the monitoring system"""
    
    # Metrics collection settings
    metrics_collection_enabled: bool = True
    metrics_retention_days: int = 30
    metrics_storage_path: str = "logs/metrics"
    collection_interval_seconds: int = 30
    
    # System monitoring settings
    system_health_checks_enabled: bool = True
    health_check_interval_seconds: int = 30
    
    # Alert settings
    alerting_enabled: bool = True
    alert_storage_path: str = "logs/alerts"
    alert_cooldown_minutes: int = 15
    
    # Analytics settings
    analytics_enabled: bool = True
    analytics_cache_ttl_minutes: int = 5
    analytics_storage_path: str = "logs/analytics"
    
    # Dashboard settings
    dashboard_enabled: bool = True
    dashboard_refresh_interval_seconds: int = 30
    
    # Performance thresholds
    response_time_warning_threshold: float = 2.0
    response_time_critical_threshold: float = 5.0
    success_rate_warning_threshold: float = 95.0
    success_rate_critical_threshold: float = 90.0
    memory_usage_warning_threshold: float = 80.0
    memory_usage_critical_threshold: float = 90.0
    cpu_usage_warning_threshold: float = 80.0
    cpu_usage_critical_threshold: float = 95.0
    
    # Agent monitoring settings
    agent_metrics_enabled: bool = True
    agent_performance_tracking: bool = True
    agent_error_tracking: bool = True
    
    # Notification settings
    email_notifications_enabled: bool = False
    webhook_notifications_enabled: bool = False
    whatsapp_notifications_enabled: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        # Ensure storage paths exist
        import os
        for path in [self.metrics_storage_path, self.alert_storage_path, self.analytics_storage_path]:
            os.makedirs(path, exist_ok=True)

def get_monitoring_config() -> MonitoringConfig:
    """Get monitoring configuration from environment variables"""
    
    config = MonitoringConfig()
    
    # Override with environment variables if available
    config.metrics_collection_enabled = os.getenv("MONITORING_METRICS_ENABLED", "true").lower() == "true"
    config.system_health_checks_enabled = os.getenv("MONITORING_HEALTH_CHECKS_ENABLED", "true").lower() == "true"
    config.alerting_enabled = os.getenv("MONITORING_ALERTING_ENABLED", "true").lower() == "true"
    config.analytics_enabled = os.getenv("MONITORING_ANALYTICS_ENABLED", "true").lower() == "true"
    config.dashboard_enabled = os.getenv("MONITORING_DASHBOARD_ENABLED", "true").lower() == "true"
    
    # Thresholds
    config.response_time_warning_threshold = float(os.getenv("MONITORING_RESPONSE_TIME_WARNING", "2.0"))
    config.response_time_critical_threshold = float(os.getenv("MONITORING_RESPONSE_TIME_CRITICAL", "5.0"))
    config.success_rate_warning_threshold = float(os.getenv("MONITORING_SUCCESS_RATE_WARNING", "95.0"))
    config.success_rate_critical_threshold = float(os.getenv("MONITORING_SUCCESS_RATE_CRITICAL", "90.0"))
    config.memory_usage_warning_threshold = float(os.getenv("MONITORING_MEMORY_WARNING", "80.0"))
    config.memory_usage_critical_threshold = float(os.getenv("MONITORING_MEMORY_CRITICAL", "90.0"))
    config.cpu_usage_warning_threshold = float(os.getenv("MONITORING_CPU_WARNING", "80.0"))
    config.cpu_usage_critical_threshold = float(os.getenv("MONITORING_CPU_CRITICAL", "95.0"))
    
    # Intervals
    config.collection_interval_seconds = int(os.getenv("MONITORING_COLLECTION_INTERVAL", "30"))
    config.health_check_interval_seconds = int(os.getenv("MONITORING_HEALTH_CHECK_INTERVAL", "30"))
    config.dashboard_refresh_interval_seconds = int(os.getenv("MONITORING_DASHBOARD_REFRESH", "30"))
    
    # Retention
    config.metrics_retention_days = int(os.getenv("MONITORING_METRICS_RETENTION_DAYS", "30"))
    config.alert_cooldown_minutes = int(os.getenv("MONITORING_ALERT_COOLDOWN", "15"))
    config.analytics_cache_ttl_minutes = int(os.getenv("MONITORING_ANALYTICS_CACHE_TTL", "5"))
    
    # Storage paths
    config.metrics_storage_path = os.getenv("MONITORING_METRICS_STORAGE", "logs/metrics")
    config.alert_storage_path = os.getenv("MONITORING_ALERT_STORAGE", "logs/alerts")
    config.analytics_storage_path = os.getenv("MONITORING_ANALYTICS_STORAGE", "logs/analytics")
    
    # Notifications
    config.email_notifications_enabled = os.getenv("MONITORING_EMAIL_ENABLED", "false").lower() == "true"
    config.webhook_notifications_enabled = os.getenv("MONITORING_WEBHOOK_ENABLED", "false").lower() == "true"
    config.whatsapp_notifications_enabled = os.getenv("MONITORING_WHATSAPP_ENABLED", "false").lower() == "true"
    
    return config

def get_alert_delivery_config() -> Dict[str, Any]:
    """Get alert delivery configuration"""
    
    config = {
        'delivery_methods': []
    }
    
    # Always include log delivery
    config['delivery_methods'].append('log')
    
    # Email configuration
    if os.getenv("MONITORING_EMAIL_ENABLED", "false").lower() == "true":
        config['delivery_methods'].append('email')
        config['email'] = {
            'enabled': True,
            'smtp_server': os.getenv("MONITORING_EMAIL_SMTP_SERVER", "smtp.gmail.com"),
            'smtp_port': int(os.getenv("MONITORING_EMAIL_SMTP_PORT", "587")),
            'username': os.getenv("MONITORING_EMAIL_USERNAME", ""),
            'password': os.getenv("MONITORING_EMAIL_PASSWORD", ""),
            'recipients': os.getenv("MONITORING_EMAIL_RECIPIENTS", "").split(",") if os.getenv("MONITORING_EMAIL_RECIPIENTS") else []
        }
    
    # Webhook configuration
    if os.getenv("MONITORING_WEBHOOK_ENABLED", "false").lower() == "true":
        config['delivery_methods'].append('webhook')
        config['webhook'] = {
            'enabled': True,
            'url': os.getenv("MONITORING_WEBHOOK_URL", ""),
            'headers': {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {os.getenv('MONITORING_WEBHOOK_TOKEN', '')}"
            } if os.getenv("MONITORING_WEBHOOK_TOKEN") else {'Content-Type': 'application/json'}
        }
    
    # WhatsApp configuration
    if os.getenv("MONITORING_WHATSAPP_ENABLED", "false").lower() == "true":
        config['delivery_methods'].append('whatsapp')
        config['whatsapp'] = {
            'enabled': True,
            'instance': os.getenv("MONITORING_WHATSAPP_INSTANCE", ""),
            'recipient': os.getenv("MONITORING_WHATSAPP_RECIPIENT", "")
        }
    
    return config

def get_performance_baselines() -> Dict[str, float]:
    """Get performance baselines for comparison"""
    
    return {
        'response_time_baseline': float(os.getenv("MONITORING_BASELINE_RESPONSE_TIME", "1.0")),
        'success_rate_baseline': float(os.getenv("MONITORING_BASELINE_SUCCESS_RATE", "95.0")),
        'memory_usage_baseline': float(os.getenv("MONITORING_BASELINE_MEMORY", "60.0")),
        'cpu_usage_baseline': float(os.getenv("MONITORING_BASELINE_CPU", "40.0")),
        'interactions_per_hour_baseline': float(os.getenv("MONITORING_BASELINE_INTERACTIONS", "100.0"))
    }

def get_monitoring_features() -> Dict[str, bool]:
    """Get enabled monitoring features"""
    
    return {
        'metrics_collection': os.getenv("MONITORING_METRICS_ENABLED", "true").lower() == "true",
        'system_health_checks': os.getenv("MONITORING_HEALTH_CHECKS_ENABLED", "true").lower() == "true",
        'alerting': os.getenv("MONITORING_ALERTING_ENABLED", "true").lower() == "true",
        'analytics': os.getenv("MONITORING_ANALYTICS_ENABLED", "true").lower() == "true",
        'dashboard': os.getenv("MONITORING_DASHBOARD_ENABLED", "true").lower() == "true",
        'agent_tracking': os.getenv("MONITORING_AGENT_TRACKING_ENABLED", "true").lower() == "true",
        'performance_analysis': os.getenv("MONITORING_PERFORMANCE_ANALYSIS_ENABLED", "true").lower() == "true",
        'trend_analysis': os.getenv("MONITORING_TREND_ANALYSIS_ENABLED", "true").lower() == "true",
        'anomaly_detection': os.getenv("MONITORING_ANOMALY_DETECTION_ENABLED", "true").lower() == "true"
    }

# Global configuration instance
monitoring_config = get_monitoring_config()
alert_delivery_config = get_alert_delivery_config()
performance_baselines = get_performance_baselines()
monitoring_features = get_monitoring_features()