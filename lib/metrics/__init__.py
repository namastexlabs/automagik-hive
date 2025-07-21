"""
Unified Metrics System

High-performance PostgreSQL-only metrics collection system for Agno framework integration.
Uses AsyncMetricsService with queue-based processing for <0.1ms latency impact.

Key Features:
- High-performance async metrics collection with psycopg3
- PostgreSQL-only storage using hive.agent_metrics table
- Queue-based background processing for minimal latency impact
- Environment variables for metrics collection control
- Automatic integration with agent/team proxies
- YAML-level overrides for metrics_enabled
- Uses established DatabaseService architecture

Usage:
    # Environment configuration
    HIVE_METRICS_COLLECT_TOKENS=true
    HIVE_DATABASE_URL=postgresql+psycopg://user:pass@host:port/database
    HIVE_AGNO_MONITOR=false
    
    # Automatic integration via proxies
    from lib.utils.agno_proxy import create_agent
    agent = create_agent("my-agent", config)  # Metrics automatically collected
    
    # Manual usage
    from lib.metrics import AsyncMetricsService
    service = AsyncMetricsService()
    await service.collect_metrics("agent-name", "agent", metrics_dict)
"""

from .config import (
    MetricsConfig,
    load_metrics_config,
    validate_environment_config,
    get_configuration_summary
)

from .async_metrics_service import (
    AsyncMetricsService,
    get_metrics_service,
    initialize_metrics_service,
    shutdown_metrics_service
)

# Public API
__all__ = [
    # Configuration
    "MetricsConfig",
    "load_metrics_config", 
    "validate_environment_config",
    "get_configuration_summary",
    
    # Async Service
    "AsyncMetricsService",
    "get_metrics_service",
    "initialize_metrics_service", 
    "shutdown_metrics_service"
]

# Version
__version__ = "1.0.0"

# Quick validation on import
_validation_error = validate_environment_config()
if _validation_error:
    import warnings
    warnings.warn(f"Metrics configuration issue: {_validation_error}", RuntimeWarning)


def get_metrics_status() -> dict:
    """
    Get current metrics system status for debugging
    
    Returns:
        Dictionary with system status information
    """
    config_summary = get_configuration_summary()
    
    # Test async metrics service availability
    metrics_service_available = False
    if config_summary.get("validation_status") == "valid":
        try:
            service = get_metrics_service()
            metrics_service_available = service is not None
        except Exception:
            pass
    
    return {
        "version": __version__,
        "configuration": config_summary,
        "metrics_service_available": metrics_service_available,
        "storage_backend": "postgres",
        "integration_points": {
            "agent_proxy": "lib.utils.proxy_agents",
            "team_proxy": "lib.utils.proxy_teams",
            "auto_injection": True
        }
    }