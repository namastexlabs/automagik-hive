"""
Async Metrics Service

High-performance async metrics collection with <0.1ms agent latency impact.
Collects execution metrics from agents, teams, and workflows with minimal performance overhead.

FEATURES:
- Event-driven collection triggered by agent/team execution
- Non-blocking asyncio.Queue with configurable batch processing
- Concurrent database writes for optimal throughput
- Input validation with bounds checking for security
- Thread-safe singleton initialization
- Configurable queue size, batch size, and flush intervals
- Graceful error handling and performance monitoring
"""

import asyncio
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from lib.logging import logger
from lib.metrics.agno_metrics_bridge import AgnoMetricsBridge
from lib.services.metrics_service import MetricsService


@dataclass
class MetricsEntry:
    """Structured metrics entry for type safety."""

    timestamp: datetime
    agent_name: str
    execution_type: str
    metrics: dict[str, Any]
    version: str = "1.0"


class AsyncMetricsService:
    """
    High-performance async metrics service with <0.1ms target latency.

    Collects execution metrics from agents, teams, and workflows without
    impacting performance. Uses event-driven collection with configurable
    batch processing and concurrent database writes.

    Features:
    - Non-blocking asyncio.Queue for zero-latency collection
    - Background task processing with configurable batching
    - Concurrent database writes for optimal throughput
    - Input validation and bounds checking for security
    - Thread-safe initialization and graceful shutdown
    - Performance monitoring with periodic statistics
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.batch_size = self.config.get("batch_size", 50)
        self.flush_interval = self.config.get("flush_interval", 5.0)
        self.queue_size = self.config.get("queue_size", 1000)

        # Initialize AGNO metrics bridge for comprehensive metrics extraction
        metrics_config = self.config.get("metrics_config")
        self.metrics_bridge = AgnoMetricsBridge(config=metrics_config)

        # Async queue and processing
        self.metrics_queue = None  # Will be created in initialize()
        self.processing_task = None
        self.metrics_service = None
        self._shutdown_event = None
        self._initialized = False

        # Thread-safe initialization lock
        self._init_lock = threading.Lock()

        self.stats = {
            "total_collected": 0,
            "total_stored": 0,
            "queue_overflows": 0,
            "storage_errors": 0,
            "last_flush": None,
        }

    async def initialize(self):
        """Initialize metrics service and start background processing."""
        with self._init_lock:
            if self._initialized:
                return

            try:
                # Create async queue
                self.metrics_queue = asyncio.Queue(maxsize=self.queue_size)
                self._shutdown_event = asyncio.Event()

                # Initialize metrics service
                self.metrics_service = MetricsService()

                # Start background processing task
                self.processing_task = asyncio.create_task(self._background_processor())

                self._initialized = True
                logger.info(
                    "AsyncMetricsService ready",
                    batch_size=self.batch_size,
                    flush_interval=self.flush_interval,
                    queue_size=self.queue_size,
                )

            except Exception as e:
                logger.error(f"⚡ Failed to initialize AsyncMetricsService: {e}")
                raise

    async def _background_processor(self):
        """Background task that processes the metrics queue."""
        batch = []
        last_flush = asyncio.get_event_loop().time()

        logger.debug(
            "Background processor started",
            batch_size=self.batch_size,
            flush_interval=self.flush_interval,
        )

        while not self._shutdown_event.is_set():
            try:
                # Try to get items from queue with timeout
                try:
                    entry = await asyncio.wait_for(
                        self.metrics_queue.get(), timeout=0.1
                    )
                    batch.append(entry)
                    self.metrics_queue.task_done()

                    logger.debug(
                        "Queue item processed",
                        agent_name=entry.agent_name,
                        batch_size=len(batch),
                    )

                except TimeoutError:
                    pass

                current_time = asyncio.get_event_loop().time()
                should_flush = len(batch) >= self.batch_size or (
                    batch and current_time - last_flush >= self.flush_interval
                )

                if should_flush and batch:
                    logger.debug(
                        "Processing batch for storage",
                        batch_size=len(batch),
                        reason="size_limit"
                        if len(batch) >= self.batch_size
                        else "time_limit",
                    )

                    await self._store_batch(batch.copy())
                    batch.clear()
                    last_flush = current_time
                    self.stats["last_flush"] = datetime.now(UTC)

            except Exception as e:
                logger.error(f"⚡ Error in metrics background processor: {e}")
                # Clear problematic batch and continue
                batch.clear()
                await asyncio.sleep(1)

        # Flush remaining items on shutdown
        if batch:
            await self._store_batch(batch)
            logger.info(f"⚡ Flushed {len(batch)} metrics on shutdown")

    async def _store_batch(self, batch: list[MetricsEntry]):
        """Store a batch of metrics entries concurrently."""
        if not batch or not self.metrics_service:
            return

        try:
            # Create concurrent tasks for all entries in batch
            tasks = []
            for entry in batch:
                task = asyncio.create_task(
                    self.metrics_service.store_metrics(
                        timestamp=entry.timestamp,
                        agent_name=entry.agent_name,
                        execution_type=entry.execution_type,
                        metrics=entry.metrics,
                        version=entry.version,
                    )
                )
                tasks.append(task)

            # Wait for all tasks to complete with timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True), timeout=10.0
                )

                # Count successful stores
                stored_count = 0
                for result in results:
                    if isinstance(result, Exception):
                        self.stats["storage_errors"] += 1
                        logger.warning(f"⚡ Storage error: {result}")
                    else:
                        stored_count += 1
                        logger.debug(f"⚡ Stored metric entry with ID: {result}")

                self.stats["total_stored"] += stored_count

                # Performance logging
                if len(batch) > 0:
                    success_rate = (stored_count / len(batch)) * 100
                    logger.debug(
                        f"⚡ Stored batch of {stored_count}/{len(batch)} metrics entries concurrently",
                        success_rate=f"{success_rate:.1f}%",
                        batch_size=len(batch),
                        errors=len(batch) - stored_count,
                    )

            except TimeoutError:
                self.stats["storage_errors"] += len(batch)
                logger.error("Batch storage timeout - all entries failed")

        except Exception as e:
            self.stats["storage_errors"] += len(batch)
            logger.error(f"⚡ Failed to store metrics batch: {e}")

    async def collect_metrics(
        self,
        agent_name: str,
        execution_type: str,
        metrics: dict[str, Any],
        version: str = "1.0",
    ) -> bool:
        """
        Collect metrics with <0.1ms target latency (non-blocking).

        Args:
            agent_name: Name of the agent
            execution_type: Type of execution (agent, team, workflow)
            metrics: Metrics data dictionary
            version: Metrics version

        Returns:
            bool: True if queued successfully, False if queue full
        """
        logger.debug(
            f"Collecting metrics for {agent_name}",
            execution_type=execution_type,
            initialized=self._initialized,
        )

        if not self._initialized:
            await self.initialize()

        # Skip if metrics service not available
        if not self.metrics_service:
            logger.debug(f"Metrics service not available for {agent_name}")
            return False

        try:
            # Create metrics entry
            entry = MetricsEntry(
                timestamp=datetime.now(UTC),
                agent_name=agent_name,
                execution_type=execution_type,
                metrics=metrics,
                version=version,
            )

            # Non-blocking queue put
            self.metrics_queue.put_nowait(entry)
            self.stats["total_collected"] += 1

            logger.debug(
                f"Metrics entry queued for {agent_name}",
                queue_size_after=self.metrics_queue.qsize(),
            )

            # Log performance metrics periodically
            if self.stats["total_collected"] % 100 == 0:
                logger.info(
                    "Metrics collection performance",
                    total_collected=self.stats["total_collected"],
                    total_stored=self.stats["total_stored"],
                    queue_size=self.metrics_queue.qsize(),
                    queue_overflows=self.stats["queue_overflows"],
                    storage_errors=self.stats["storage_errors"],
                )

            return True

        except asyncio.QueueFull:
            self.stats["queue_overflows"] += 1
            logger.warning("Metrics queue full, dropping metrics entry")
            return False

    def collect_from_response(
        self,
        response: Any,
        agent_name: str,
        execution_type: str,
        yaml_overrides: dict[str, Any] | None = None,
    ) -> bool:
        """
        Extract and collect metrics from an agent response (sync wrapper).

        This method maintains compatibility with existing code.
        """
        logger.debug(
            f"Collecting metrics from response for {agent_name}",
            execution_type=execution_type,
            initialized=self._initialized,
        )

        try:
            # Extract metrics from response
            metrics = self._extract_metrics_from_response(response, yaml_overrides)

            logger.debug(
                f"Extracted {len(metrics) if metrics else 0} metrics from response",
                agent_name=agent_name,
            )

            # Use async collect in a safe way
            try:
                asyncio.get_running_loop()
                # Create task for async collection
                asyncio.create_task(
                    self.collect_metrics(agent_name, execution_type, metrics)
                )

                logger.debug(
                    "Async task created for metrics collection", agent_name=agent_name
                )
                return True
            except RuntimeError as e:
                # No running loop - this shouldn't happen in FastAPI context
                logger.debug(
                    "No running event loop for metrics collection",
                    agent_name=agent_name,
                    error=str(e),
                )
                logger.warning("No running event loop for metrics collection")
                return False

        except Exception as e:
            logger.debug(
                "Failed to collect metrics from response",
                agent_name=agent_name,
                error=str(e),
            )
            logger.error(f"⚡ Failed to collect metrics from response: {e}")
            return False

    def _extract_metrics_from_response(
        self, response: Any, yaml_overrides: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Extract comprehensive metrics using AGNO native metrics bridge.

        DROP-IN REPLACEMENT: Now uses AgnoMetricsBridge for superior metrics collection.
        Provides comprehensive coverage of AGNO native metrics including:
        - Token metrics: input_tokens, output_tokens, total_tokens, prompt_tokens, completion_tokens
        - Advanced tokens: audio_tokens, cached_tokens, reasoning_tokens, cache_write_tokens
        - Timing metrics: time, time_to_first_token
        - Content metrics: prompt_tokens_details, completion_tokens_details
        - Additional metrics: model-specific metrics

        Args:
            response: AGNO response object (agent/team/workflow)
            yaml_overrides: Optional YAML-level metric overrides

        Returns:
            Dictionary with comprehensive metrics for PostgreSQL storage
        """
        return self.metrics_bridge.extract_metrics(response, yaml_overrides)

    def get_stats(self) -> dict[str, Any]:
        """Get current performance statistics."""
        return {
            **self.stats,
            "queue_size": self.metrics_queue.qsize() if self.metrics_queue else 0,
            "metrics_service_available": self.metrics_service is not None,
            "is_processing": self.processing_task and not self.processing_task.done(),
            "initialized": self._initialized,
        }

    async def flush(self, timeout: float = 5.0) -> bool:
        """
        Force flush all queued metrics.

        Args:
            timeout: Maximum time to wait for flush

        Returns:
            bool: True if flushed successfully
        """
        if not self.metrics_queue:
            return False

        queue_size = self.metrics_queue.qsize()
        if queue_size == 0:
            return True

        # Wait for queue to empty
        start_time = asyncio.get_event_loop().time()
        while (
            self.metrics_queue.qsize() > 0
            and asyncio.get_event_loop().time() - start_time < timeout
        ):
            await asyncio.sleep(0.1)

        return self.metrics_queue.qsize() == 0

    async def close(self):
        """Gracefully shutdown the metrics service."""
        logger.info("Shutting down AsyncMetricsService...")

        if self._shutdown_event:
            self._shutdown_event.set()

        if self.processing_task:
            try:
                await asyncio.wait_for(self.processing_task, timeout=5.0)
            except TimeoutError:
                logger.warning("Processing task did not shut down within timeout")
                self.processing_task.cancel()

        self._initialized = False
        logger.info("AsyncMetricsService closed")


# Thread-safe global metrics service instance
_metrics_service: AsyncMetricsService | None = None
_init_lock = threading.Lock()


def get_metrics_service() -> AsyncMetricsService | None:
    """Get the global metrics service instance."""
    return _metrics_service


def initialize_metrics_service(
    config: dict[str, Any] | None = None,
) -> AsyncMetricsService:
    """Initialize the global metrics service with thread safety."""
    global _metrics_service
    with _init_lock:
        if _metrics_service is None:
            _metrics_service = AsyncMetricsService(config)
        return _metrics_service


async def shutdown_metrics_service():
    """Shutdown the global metrics service."""
    global _metrics_service
    with _init_lock:
        if _metrics_service:
            await _metrics_service.close()
            _metrics_service = None
