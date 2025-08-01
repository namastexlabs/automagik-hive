"""
AGNO Native Metrics Integration

High-performance metrics collection system with AGNO native metrics and LangWatch integration.
Features AgnoMetricsBridge for comprehensive metrics with superior coverage over manual extraction.

Key Features:
- AGNO Native Metrics: Direct access to agent.run_response.metrics and session_metrics
- AgnoMetricsBridge: Drop-in replacement with 15+ token types vs 3 manual
- LangWatch Integration: Dual-path metrics (PostgreSQL + OpenTelemetry)
- High-performance async collection with psycopg3
- Queue-based background processing for <0.1ms latency impact
- Environment variables for metrics collection control
- Automatic integration with agent/team/workflow proxies

Comprehensive Metrics Coverage:
- Token metrics: input_tokens, output_tokens, total_tokens, prompt_tokens, completion_tokens
- Advanced tokens: audio_tokens, cached_tokens, reasoning_tokens, cache_write_tokens
- Timing metrics: time, time_to_first_token
- Content metrics: prompt_tokens_details, completion_tokens_details

Usage:
    # Environment configuration
    HIVE_METRICS_COLLECT_TOKENS=true
    HIVE_DATABASE_URL=postgresql+psycopg://user:pass@host:port/database
    HIVE_AGNO_MONITOR=false

    # Automatic AGNO native metrics via proxies
    from lib.utils.agno_proxy import create_agent
    agent = create_agent("my-agent", config)  # AGNO metrics automatically collected

    # Manual usage with AGNO bridge
    from lib.metrics import AsyncMetricsService, AgnoMetricsBridge
    service = AsyncMetricsService()
    await service.collect_metrics("agent-name", "agent", agno_response)

    # LangWatch integration
    from lib.metrics import initialize_dual_path_metrics
    coordinator = initialize_dual_path_metrics(bridge, langwatch_enabled=True)
"""

from .agno_metrics_bridge import AgnoMetricsBridge
from .async_metrics_service import (
    AsyncMetricsService,
    get_metrics_service,
    initialize_metrics_service,
    shutdown_metrics_service,
)
from .config import (
    MetricsConfig,
    get_configuration_summary,
    load_metrics_config,
    validate_environment_config,
)
from .langwatch_integration import (
    DualPathMetricsCoordinator,
    LangWatchManager,
    get_langwatch_manager,
    get_metrics_coordinator,
    initialize_dual_path_metrics,
    initialize_langwatch,
    setup_langwatch_global,
    shutdown_langwatch_integration,
)

# Public API
__all__ = [
    # AGNO Native Metrics Bridge
    "AgnoMetricsBridge",
    # Async Service with AGNO Native Metrics
    "AsyncMetricsService",
    "DualPathMetricsCoordinator",
    # LangWatch Integration
    "LangWatchManager",
    # Configuration
    "MetricsConfig",
    "get_configuration_summary",
    "get_langwatch_manager",
    "get_metrics_coordinator",
    "get_metrics_service",
    "initialize_dual_path_metrics",
    "initialize_langwatch",
    "initialize_metrics_service",
    "load_metrics_config",
    "setup_langwatch_global",
    "shutdown_langwatch_integration",
    "shutdown_metrics_service",
    "validate_environment_config",
]

# Version
__version__ = "1.0.0"

# Quick validation on import
_validation_error = validate_environment_config()
if _validation_error:
    import warnings

    warnings.warn(
        f"Metrics configuration issue: {_validation_error}",
        RuntimeWarning,
        stacklevel=2,
    )


def _check_langwatch_availability() -> bool:
    """
    Check if LangWatch is available for integration.

    Returns:
        True if LangWatch can be imported, False otherwise
    """
    try:
        import langwatch
        from openinference.instrumentation.agno import AgnoInstrumentor

        return True
    except ImportError:
        return False


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
        "metrics_extraction": "agno_native",
        "bridge_version": "1.0.0",
        "langwatch_available": _check_langwatch_availability(),
        "integration_points": {
            "agent_proxy": "lib.utils.proxy_agents",
            "team_proxy": "lib.utils.proxy_teams",
            "workflow_proxy": "lib.utils.proxy_workflows",
            "auto_injection": True,
            "agno_native_metrics": True,
            "langwatch_integration": True,
        },
        "advantages": [
            "AGNO native metrics (15+ token types vs 3 manual)",
            "Native timing metrics (time, time_to_first_token)",
            "Audio and reasoning token support",
            "Cache metrics for performance optimization",
            "LangWatch OpenTelemetry integration",
            "Future-proof automatic metric updates",
        ],
    }
