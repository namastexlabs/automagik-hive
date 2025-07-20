"""
Unified Metrics System

A secure, production-ready metrics collection system for Agno framework integration.
Extracts metrics from RunResponse objects and stores them in configurable backends.

Key Features:
- Extracts from Agno's native RunResponse.metrics (no custom metrics creation)
- 8 environment variables for configuration (5 core + 3 storage)
- 3 storage backends: file (default), console, PostgreSQL
- Automatic integration with agent/team proxies
- YAML-level overrides for metrics_enabled
- Security hardened against SQL injection and path traversal
- File storage default to ./logs/metrics.log
- Disables Agno platform telemetry (AGNO_MONITOR=false)

Usage:
    # Environment configuration
    METRICS_COLLECT_TOKENS=true
    METRICS_STORAGE_BACKEND=file
    AGNO_MONITOR=false
    
    # Automatic integration via proxies
    from lib.utils.agno_proxy import create_agent
    agent = create_agent("my-agent", config)  # Metrics automatically collected
    
    # Manual usage
    from lib.metrics import MetricsCollectionService
    service = MetricsCollectionService()
    service.collect_from_response(response, "agent-name")
"""

from .config import (
    MetricsConfig,
    load_metrics_config,
    validate_environment_config,
    get_configuration_summary
)

from .collection_service import MetricsCollectionService

from .async_metrics_service import (
    AsyncMetricsService,
    get_metrics_service,
    initialize_metrics_service,
    shutdown_metrics_service
)

from .storage import (
    MetricsStorage,
    StorageError,
    ConfigurationError,
    create_storage_backend
)

# Public API
__all__ = [
    # Configuration
    "MetricsConfig",
    "load_metrics_config", 
    "validate_environment_config",
    "get_configuration_summary",
    
    # Collection Service
    "MetricsCollectionService",
    
    # Async Service
    "AsyncMetricsService",
    "get_metrics_service",
    "initialize_metrics_service", 
    "shutdown_metrics_service",
    
    # Storage
    "MetricsStorage",
    "StorageError",
    "ConfigurationError", 
    "create_storage_backend"
]

# Version
__version__ = "1.0.0"

# Quick validation on import
_validation_error = validate_environment_config()
if _validation_error:
    import warnings
    warnings.warn(f"Metrics configuration issue: {_validation_error}", RuntimeWarning)


def create_metrics_service() -> MetricsCollectionService:
    """
    Factory function to create a configured metrics collection service
    
    Returns:
        MetricsCollectionService: Configured service instance
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
    validation_error = validate_environment_config()
    if validation_error:
        raise ConfigurationError(validation_error)
    
    return MetricsCollectionService()


def get_metrics_status() -> dict:
    """
    Get current metrics system status for debugging
    
    Returns:
        Dictionary with system status information
    """
    config_summary = get_configuration_summary()
    
    # Test storage backend availability
    storage_available = False
    if config_summary.get("validation_status") == "valid":
        try:
            service = MetricsCollectionService()
            storage_available = service.storage_backend is not None
        except Exception:
            pass
    
    return {
        "version": __version__,
        "configuration": config_summary,
        "storage_available": storage_available,
        "integration_points": {
            "agent_proxy": "lib.utils.proxy_agents",
            "team_proxy": "lib.utils.proxy_teams",
            "auto_injection": True
        }
    }