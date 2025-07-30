"""
LangWatch Integration for AGNO Metrics - Async Architecture

Provides seamless integration with LangWatch's AgnoInstrumentor for OpenTelemetry-based
metrics collection that works alongside PostgreSQL storage without conflicts.

ARCHITECTURE:
- Global Setup: langwatch.setup() called once per application in background task
- Manager Coordination: LangWatchManager waits for global setup before instrumentor init
- Zero Performance Impact: All LangWatch operations are async and separate from agents
- Dual-Path Metrics: PostgreSQL and OpenTelemetry paths operate independently

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
The integration follows the official LangWatch Agno pattern with async enhancements:
    https://docs.langwatch.ai/integration/python/integrations/agno
"""

import asyncio
from typing import Any

from lib.logging import logger


class LangWatchManager:
    """
    Manager for LangWatch AgnoInstrumentor integration.

    Provides dual-path metrics architecture:
    - PostgreSQL Path: AgnoMetricsBridge → AsyncMetricsService → PostgreSQL
    - OpenTelemetry Path: AgnoInstrumentor → LangWatch → OpenTelemetry backend

    Both systems access AGNO native metrics independently without conflicts.
    """

    def __init__(self, enabled: bool = False, config: dict[str, Any] | None = None):
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

    async def initialize(self) -> bool:
        """
        Initialize LangWatch AgnoInstrumentor.

        Waits for global LangWatch setup completion, then initializes only
        the instrumentor without calling langwatch.setup() directly.

        Returns:
            True if initialization successful, False otherwise
        """
        if not self.enabled:
            logger.debug("🔧 LangWatch integration disabled")
            return False

        if self._initialized:
            logger.debug("🔧 LangWatch already initialized")
            return True

        # Wait for global setup completion (non-blocking for agents)
        try:
            await asyncio.wait_for(_setup_complete.wait(), timeout=5.0)
            logger.debug(
                "🔧 Global LangWatch setup confirmed, proceeding with instrumentor"
            )
        except TimeoutError:
            logger.warning(
                "⚠️  LangWatch global setup timed out, proceeding anyway for graceful degradation"
            )

        try:
            # Import and create instrumentor instance only
            # Global langwatch.setup() is handled separately in startup
            from openinference.instrumentation.agno import AgnoInstrumentor

            # Create instrumentor instance
            self.instrumentor = AgnoInstrumentor()

            # Actually instrument the Agno framework
            self.instrumentor.instrument()

            self._initialized = True
            logger.info(
                "🚀 LangWatch AgnoInstrumentor initialized and instrumented successfully"
            )
            return True

        except ImportError as e:
            if "langwatch" in str(e):
                logger.warning(
                    "⚠️  LangWatch not available - install 'langwatch' package for OpenTelemetry integration"
                )
            elif "openinference" in str(e):
                logger.warning(
                    "⚠️  OpenInference Agno instrumentor not available - install 'openinference-instrumentation-agno' package"
                )
            else:
                logger.warning(
                    f"⚠️  LangWatch integration dependencies not available: {e}"
                )
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
            if self.instrumentor and hasattr(self.instrumentor, "uninstrument"):
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

    def get_status(self) -> dict[str, Any]:
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
            "description": "LangWatch OpenTelemetry integration running parallel to PostgreSQL metrics",
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
    Provides a compatible interface for agent integration by delegating to AsyncMetricsService.
    """

    def __init__(
        self,
        agno_bridge,
        langwatch_manager: LangWatchManager | None = None,
        async_metrics_service=None,
    ):
        """
        Initialize coordinator.

        Args:
            agno_bridge: AgnoMetricsBridge instance
            langwatch_manager: Optional LangWatch manager
            async_metrics_service: AsyncMetricsService instance for PostgreSQL collection
        """
        self.agno_bridge = agno_bridge
        self.langwatch_manager = langwatch_manager
        self.async_metrics_service = async_metrics_service

        from lib.logging import logger

        logger.debug(
            "DualPathMetricsCoordinator initialized",
            agno_bridge_available=agno_bridge is not None,
            langwatch_manager_available=langwatch_manager is not None,
            async_metrics_service_available=async_metrics_service is not None,
        )

    async def initialize(self) -> dict[str, bool]:
        """
        Initialize both metrics paths.

        Returns:
            Dictionary with initialization status for each path
        """
        status = {
            "agno_bridge": True,  # AgnoMetricsBridge is always available
            "langwatch": False,
        }

        # Initialize LangWatch if available (now async)
        if self.langwatch_manager:
            status["langwatch"] = await self.langwatch_manager.initialize()

        logger.info(
            f"🔧 Dual-path metrics initialized - PostgreSQL: {status['agno_bridge']}, LangWatch: {status['langwatch']}"
        )
        return status

    def extract_metrics(
        self, response: Any, yaml_overrides: dict[str, Any] | None = None
    ) -> dict[str, Any]:
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

    def collect_from_response(
        self,
        response: Any,
        agent_name: str,
        execution_type: str,
        yaml_overrides: dict[str, Any] | None = None,
    ) -> bool:
        """
        Collect metrics from an agent response (compatible interface for agent integration).

        Delegates to the underlying AsyncMetricsService for PostgreSQL collection.
        LangWatch collection happens automatically via OpenTelemetry instrumentation.

        Args:
            response: AGNO response object
            agent_name: Name of the agent
            execution_type: Type of execution (agent, team, workflow)
            yaml_overrides: Optional YAML overrides

        Returns:
            bool: True if collection was successful
        """
        logger.debug(
            f"Collecting metrics from response via coordinator for {agent_name}",
            execution_type=execution_type,
            async_service_available=self.async_metrics_service is not None,
        )

        if not self.async_metrics_service:
            logger.debug("No AsyncMetricsService available for metrics collection")
            return False

        try:
            result = self.async_metrics_service.collect_from_response(
                response=response,
                agent_name=agent_name,
                execution_type=execution_type,
                yaml_overrides=yaml_overrides,
            )

            logger.debug(
                f"Metrics collection delegation result for {agent_name}: {'success' if result else 'failed'}"
            )
            return result

        except Exception as e:
            logger.debug(
                f"Error in collect_from_response delegation for {agent_name}",
                error=str(e),
            )
            return False

    async def collect_metrics(
        self,
        agent_name: str,
        execution_type: str,
        metrics: dict[str, Any],
        version: str = "1.0",
    ) -> bool:
        """
        Collect metrics directly (compatible interface for agent integration).

        Delegates to the underlying AsyncMetricsService for PostgreSQL collection.

        Args:
            agent_name: Name of the agent
            execution_type: Type of execution (agent, team, workflow)
            metrics: Metrics data dictionary
            version: Metrics version

        Returns:
            bool: True if collection was successful
        """
        if not self.async_metrics_service:
            logger.warning("No AsyncMetricsService available for metrics collection")
            return False

        return await self.async_metrics_service.collect_metrics(
            agent_name=agent_name,
            execution_type=execution_type,
            metrics=metrics,
            version=version,
        )

    def get_stats(self) -> dict[str, Any]:
        """
        Get metrics collection statistics (compatible interface for agent integration).

        Returns:
            Dictionary with statistics from AsyncMetricsService
        """
        if not self.async_metrics_service:
            return {"error": "No AsyncMetricsService available"}

        return self.async_metrics_service.get_stats()

    def get_status(self) -> dict[str, Any]:
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
                "metrics_source": "AGNO native metrics",
            },
            "opentelemetry_path": {
                "active": self.langwatch_manager.is_active()
                if self.langwatch_manager
                else False,
                "component": "LangWatch AgnoInstrumentor",
                "storage": "OpenTelemetry backend",
                "metrics_source": "AGNO native metrics",
            },
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


# Global singleton instances
_langwatch_manager = None
_coordinator = None

# Global async setup coordination
# These are used to ensure langwatch.setup() is called only once per application
# and to coordinate between the global setup and manager initialization
_setup_complete = asyncio.Event()
_setup_task = None


async def setup_langwatch_global(config: dict[str, Any]) -> bool:
    """
    Global async LangWatch setup - called once per application lifecycle.

    This function performs the global langwatch.setup() call in a background task,
    completely separate from agent operations to ensure zero performance impact.
    Uses proper async coordination to signal completion to waiting components.

    Args:
        config: LangWatch configuration dictionary

    Returns:
        True if setup successful, False otherwise
    """
    global _setup_task
    if _setup_task is not None:
        return await _setup_task

    _setup_task = asyncio.create_task(_do_setup(config))
    return await _setup_task


async def _do_setup(config: dict[str, Any]) -> bool:
    """
    Internal async setup implementation with comprehensive error handling.

    Performs the actual langwatch.setup() call and signals completion to
    any waiting components regardless of success or failure.
    """
    try:
        # Import LangWatch and perform global setup
        import langwatch

        langwatch.setup(**config)
        _setup_complete.set()
        logger.info("🚀 LangWatch global async setup completed successfully")
        return True
    except ImportError as e:
        if "langwatch" in str(e):
            logger.warning(
                "⚠️  LangWatch not available - install 'langwatch' package for OpenTelemetry integration"
            )
        elif "openinference" in str(e):
            logger.warning(
                "⚠️  OpenInference dependencies not available - install 'openinference-instrumentation-agno' package"
            )
        else:
            logger.warning(f"⚠️  LangWatch integration dependencies not available: {e}")
        _setup_complete.set()  # Signal completion even if failed for graceful degradation
        return False
    except Exception as e:
        logger.error(f"🚨 Failed to initialize LangWatch globally: {e}")
        _setup_complete.set()  # Signal completion even if failed for graceful degradation
        return False


def initialize_langwatch(
    enabled: bool = False, config: dict[str, Any] | None = None
) -> LangWatchManager:
    """
    Create or retrieve the global LangWatch manager instance.

    This function manages the singleton LangWatch manager but does not perform
    any setup operations. Global langwatch.setup() is handled asynchronously
    during application startup, and instrumentor initialization is deferred
    until the manager is actually needed.

    Args:
        enabled: Whether to enable LangWatch integration
        config: Optional LangWatch configuration for the manager

    Returns:
        LangWatch manager instance (singleton)
    """
    global _langwatch_manager

    # Return existing manager if available
    if _langwatch_manager is not None:
        logger.debug("🔧 LangWatch manager already exists, returning existing instance")
        # Update configuration if provided
        if config:
            _langwatch_manager.configure(**config)
        return _langwatch_manager

    # Create new manager instance (initialization deferred)
    _langwatch_manager = LangWatchManager(enabled=enabled, config=config)
    logger.debug("🔧 LangWatch manager created (async initialization deferred)")

    return _langwatch_manager


def get_langwatch_manager() -> LangWatchManager | None:
    """
    Get the global LangWatch manager instance.

    Returns:
        LangWatch manager or None if not initialized
    """
    return _langwatch_manager


def initialize_dual_path_metrics(
    agno_bridge,
    langwatch_enabled: bool = False,
    langwatch_config: dict[str, Any] | None = None,
    async_metrics_service=None,
) -> DualPathMetricsCoordinator:
    """
    Create or retrieve the global dual-path metrics coordinator.

    Manages the singleton coordinator that orchestrates both PostgreSQL and
    LangWatch OpenTelemetry metrics paths. The coordinator is created immediately
    but async initialization is deferred until needed.

    Args:
        agno_bridge: AgnoMetricsBridge instance for PostgreSQL path
        langwatch_enabled: Whether to enable LangWatch integration
        langwatch_config: Optional LangWatch configuration
        async_metrics_service: AsyncMetricsService instance for PostgreSQL collection

    Returns:
        Dual-path metrics coordinator (singleton)
    """
    global _coordinator

    # Return existing coordinator if available
    if _coordinator is not None:
        logger.debug(
            "🔧 Dual-path metrics coordinator already exists, returning existing instance"
        )
        return _coordinator

    # Create LangWatch manager if needed
    langwatch_manager = initialize_langwatch(langwatch_enabled, langwatch_config)

    # Create coordinator with AsyncMetricsService (async initialization deferred)
    _coordinator = DualPathMetricsCoordinator(
        agno_bridge, langwatch_manager, async_metrics_service
    )
    logger.debug(
        "Dual-path metrics coordinator created (async initialization deferred)"
    )

    return _coordinator


def get_metrics_coordinator() -> DualPathMetricsCoordinator | None:
    """
    Get the global dual-path metrics coordinator.

    Returns:
        Metrics coordinator or None if not initialized
    """
    return _coordinator


def shutdown_langwatch_integration() -> None:
    """
    Shutdown LangWatch integration and cleanup all resources.

    Properly shuts down both the coordinator and manager, and resets
    global state for clean restart if needed.
    """
    global _langwatch_manager, _coordinator, _setup_complete, _setup_task

    # Shutdown coordinator first (which will shutdown manager)
    if _coordinator:
        _coordinator.shutdown()
        _coordinator = None

    # Shutdown manager if still active
    if _langwatch_manager:
        _langwatch_manager.shutdown()
        _langwatch_manager = None

    # Reset global setup state for clean restart
    _setup_complete.clear()
    _setup_task = None

    logger.info("🔧 LangWatch integration shutdown completed")
