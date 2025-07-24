"""
LangWatch Integration for AGNO Metrics

Provides seamless integration with LangWatch's AgnoInstrumentor for OpenTelemetry-based
metrics collection that works alongside PostgreSQL storage without conflicts.

DEPENDENCIES:
To use LangWatch integration, install the required packages:
    pip install langwatch openinference-instrumentation-agno

ENVIRONMENT VARIABLES:
    LANGWATCH_API_KEY=your-api-key      # Your LangWatch API key (required)
    HIVE_ENABLE_LANGWATCH=true/false    # Optional: explicitly enable/disable (overrides auto-enable)
    LANGWATCH_ENDPOINT=https://...       # Optional custom LangWatch endpoint

    AUTO-ENABLE LOGIC:
    LangWatch automatically enables when:
    - HIVE_ENABLE_METRICS=true (default) AND
    - LANGWATCH_API_KEY is set

    Set HIVE_ENABLE_LANGWATCH explicitly to override this behavior.

USAGE:
The integration follows the official LangWatch Agno pattern:
    https://docs.langwatch.ai/integration/python/integrations/agno
"""

from typing import Optional, Dict, Any
from lib.logging import logger


class LangWatchManager:
    """
    Manager for LangWatch AgnoInstrumentor integration.

    Provides dual-path metrics architecture:
    - PostgreSQL Path: AgnoMetricsBridge → AsyncMetricsService → PostgreSQL
    - OpenTelemetry Path: AgnoInstrumentor → LangWatch → OpenTelemetry backend

    Both systems access AGNO native metrics independently without conflicts.
    """

    def __init__(self, enabled: bool = False, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LangWatch manager.

        Args:
            enabled: Whether LangWatch integration is enabled
            config: Optional configuration for LangWatch setup
        """
        self.enabled = enabled
        self.config = config or {}
        self.instrumentor = None
        self._initialized = False

    def initialize(self) -> bool:
        """
        Initialize LangWatch AgnoInstrumentor.

        Sets up LangWatch instrumentation alongside AgnoMetricsBridge
        without interfering with PostgreSQL metrics collection.

        Uses the official Agno integration pattern from LangWatch docs.

        Returns:
            True if initialization successful, False otherwise
        """
        if not self.enabled:
            logger.debug("🔧 LangWatch integration disabled")
            return False

        if self._initialized:
            logger.debug("🔧 LangWatch already initialized")
            return True

        try:
            # Import LangWatch and proper Agno instrumentor
            import langwatch
            from openinference.instrumentation.agno import AgnoInstrumentor

            # Create instrumentor instance
            self.instrumentor = AgnoInstrumentor()

            # Initialize LangWatch with Agno instrumentor
            # This follows the official pattern from LangWatch docs
            langwatch.setup(
                instrumentors=[self.instrumentor],
                **self.config  # Pass any additional config to langwatch.setup()
            )

            self._initialized = True
            logger.info("🚀 LangWatch AgnoInstrumentor initialized successfully with langwatch.setup()")
            return True

        except ImportError as e:
            if "langwatch" in str(e):
                logger.warning("⚠️  LangWatch not available - install 'langwatch' package for OpenTelemetry integration")
            elif "openinference" in str(e):
                logger.warning("⚠️  OpenInference Agno instrumentor not available - install 'openinference-instrumentation-agno' package")
            else:
                logger.warning(f"⚠️  LangWatch integration dependencies not available: {e}")
            return False
        except Exception as e:
            logger.error(f"🚨 Failed to initialize LangWatch: {e}")
            return False

    def shutdown(self) -> None:
        """
        Clean shutdown of LangWatch instrumentation.

        Properly uninstruments and cleans up LangWatch resources.
        """
        if not self._initialized:
            return

        try:
            # Uninstrument the AgnoInstrumentor if available
            if self.instrumentor and hasattr(self.instrumentor, 'uninstrument'):
                self.instrumentor.uninstrument()

            self.instrumentor = None
            self._initialized = False
            logger.info("🔧 LangWatch AgnoInstrumentor shutdown completed")

        except Exception as e:
            logger.warning(f"⚠️  Error during LangWatch shutdown: {e}")

    def is_active(self) -> bool:
        """
        Check if LangWatch instrumentation is active.

        Returns:
            True if LangWatch is initialized and active
        """
        return self.enabled and self._initialized and self.instrumentor is not None

    def get_status(self) -> Dict[str, Any]:
        """
        Get LangWatch integration status.

        Returns:
            Dictionary with status information
        """
        return {
            "enabled": self.enabled,
            "initialized": self._initialized,
            "active": self.is_active(),
            "instrumentor_available": self.instrumentor is not None,
            "config": self.config,
            "integration_type": "dual_path",
            "description": "LangWatch OpenTelemetry integration running parallel to PostgreSQL metrics"
        }

    def configure(self, **kwargs) -> None:
        """
        Update LangWatch configuration.

        Args:
            **kwargs: Configuration parameters to update
        """
        self.config.update(kwargs)

        # Apply configuration to active instrumentor
        if self._initialized and self.instrumentor:
            for key, value in kwargs.items():
                if hasattr(self.instrumentor, key):
                    setattr(self.instrumentor, key, value)
                    logger.debug(f"🔧 Updated LangWatch config: {key} = {value}")


class DualPathMetricsCoordinator:
    """
    Coordinator for dual-path metrics architecture.

    Ensures AgnoMetricsBridge and LangWatch work together without conflicts.
    """

    def __init__(self, agno_bridge, langwatch_manager: Optional[LangWatchManager] = None):
        """
        Initialize coordinator.

        Args:
            agno_bridge: AgnoMetricsBridge instance
            langwatch_manager: Optional LangWatch manager
        """
        self.agno_bridge = agno_bridge
        self.langwatch_manager = langwatch_manager

    def initialize(self) -> Dict[str, bool]:
        """
        Initialize both metrics paths.

        Returns:
            Dictionary with initialization status for each path
        """
        status = {
            "agno_bridge": True,  # AgnoMetricsBridge is always available
            "langwatch": False
        }

        # Initialize LangWatch if available
        if self.langwatch_manager:
            status["langwatch"] = self.langwatch_manager.initialize()

        logger.info(f"🔧 Dual-path metrics initialized - PostgreSQL: {status['agno_bridge']}, LangWatch: {status['langwatch']}")
        return status

    def extract_metrics(self, response: Any, yaml_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extract metrics using AgnoMetricsBridge.

        LangWatch operates independently through OpenTelemetry instrumentation.

        Args:
            response: AGNO response object
            yaml_overrides: Optional YAML overrides

        Returns:
            Metrics dictionary for PostgreSQL storage
        """
        return self.agno_bridge.extract_metrics(response, yaml_overrides)

    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of dual-path metrics.

        Returns:
            Dictionary with status of both metrics paths
        """
        status = {
            "architecture": "dual_path",
            "postgresql_path": {
                "active": True,
                "component": "AgnoMetricsBridge",
                "storage": "PostgreSQL via AsyncMetricsService",
                "metrics_source": "AGNO native metrics"
            },
            "opentelemetry_path": {
                "active": self.langwatch_manager.is_active() if self.langwatch_manager else False,
                "component": "LangWatch AgnoInstrumentor",
                "storage": "OpenTelemetry backend",
                "metrics_source": "AGNO native metrics"
            }
        }

        if self.langwatch_manager:
            status["langwatch_status"] = self.langwatch_manager.get_status()

        return status

    def shutdown(self) -> None:
        """
        Shutdown both metrics paths.
        """
        if self.langwatch_manager:
            self.langwatch_manager.shutdown()

        logger.info("🔧 Dual-path metrics coordinator shutdown completed")


# Global instance for easy access
_langwatch_manager = None
_coordinator = None


def initialize_langwatch(enabled: bool = False, config: Optional[Dict[str, Any]] = None) -> LangWatchManager:
    """
    Initialize global LangWatch manager.

    Args:
        enabled: Whether to enable LangWatch integration
        config: Optional LangWatch configuration

    Returns:
        LangWatch manager instance
    """
    global _langwatch_manager

    _langwatch_manager = LangWatchManager(enabled=enabled, config=config)
    _langwatch_manager.initialize()

    return _langwatch_manager


def get_langwatch_manager() -> Optional[LangWatchManager]:
    """
    Get the global LangWatch manager instance.

    Returns:
        LangWatch manager or None if not initialized
    """
    return _langwatch_manager


def initialize_dual_path_metrics(agno_bridge, langwatch_enabled: bool = False,
                                langwatch_config: Optional[Dict[str, Any]] = None) -> DualPathMetricsCoordinator:
    """
    Initialize complete dual-path metrics architecture.

    Args:
        agno_bridge: AgnoMetricsBridge instance
        langwatch_enabled: Whether to enable LangWatch integration
        langwatch_config: Optional LangWatch configuration

    Returns:
        Dual-path metrics coordinator
    """
    global _coordinator

    # Initialize LangWatch manager
    langwatch_manager = initialize_langwatch(langwatch_enabled, langwatch_config)

    # Create coordinator
    _coordinator = DualPathMetricsCoordinator(agno_bridge, langwatch_manager)
    _coordinator.initialize()

    return _coordinator


def get_metrics_coordinator() -> Optional[DualPathMetricsCoordinator]:
    """
    Get the global dual-path metrics coordinator.

    Returns:
        Metrics coordinator or None if not initialized
    """
    return _coordinator


def shutdown_langwatch_integration() -> None:
    """
    Shutdown LangWatch integration and cleanup resources.
    """
    global _langwatch_manager, _coordinator

    if _coordinator:
        _coordinator.shutdown()
        _coordinator = None

    if _langwatch_manager:
        _langwatch_manager.shutdown()
        _langwatch_manager = None

    logger.info("🔧 LangWatch integration shutdown completed")