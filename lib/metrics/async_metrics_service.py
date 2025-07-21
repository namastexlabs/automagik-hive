"""
Async Metrics Service with Queue Architecture

High-performance async metrics collection designed for <0.1ms agent latency impact.
Uses background queue processing with psycopg connection pooling.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from queue import Queue
from threading import Thread, Event

from lib.services.metrics_service import MetricsService

logger = logging.getLogger(__name__)


@dataclass
class MetricsEntry:
    """Structured metrics entry for type safety."""
    timestamp: datetime
    agent_name: str
    execution_type: str
    metrics: Dict[str, Any]
    version: str = "1.0"


class AsyncMetricsService:
    """
    High-performance async metrics service with <0.1ms target latency.
    
    Features:
    - Non-blocking queue-based collection
    - Background batch processing  
    - Connection pooling for efficiency
    - Automatic error recovery
    - Performance monitoring
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.batch_size = self.config.get("batch_size", 50)
        self.flush_interval = self.config.get("flush_interval", 5.0)
        
        self.metrics_queue = Queue(maxsize=1000)
        self.processing_thread = None
        self.stop_event = Event()
        
        self.async_loop = None
        self.async_loop_thread = None
        self.metrics_service = None
        
        self.stats = {
            "total_collected": 0,
            "total_stored": 0,
            "queue_overflows": 0,
            "storage_errors": 0,
            "last_flush": None
        }
        
        self._initialize()
    
    def _initialize(self):
        """Initialize metrics service and start background processing."""
        try:
            self._start_async_loop_thread()
            self._start_background_processing()
            logger.info("AsyncMetricsService initialized successfully with dedicated async loop")
            
        except Exception as e:
            logger.error(f"Failed to initialize AsyncMetricsService: {e}")
            raise
    
    def _start_async_loop_thread(self):
        """Start dedicated asyncio loop thread for safe async operations."""
        if self.async_loop_thread and self.async_loop_thread.is_alive():
            return
            
        def run_async_loop():
            self.async_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.async_loop)
            
            async def init_metrics_service():
                from lib.services.metrics_service import MetricsService
                self.metrics_service = MetricsService()
            
            self.async_loop.run_until_complete(init_metrics_service())
            try:
                self.async_loop.run_forever()
            except Exception as e:
                logger.error(f"Async loop thread error: {e}")
            finally:
                self.async_loop.close()
        
        self.async_loop_thread = Thread(
            target=run_async_loop,
            daemon=True,
            name="MetricsAsyncLoop"
        )
        self.async_loop_thread.start()
        
        timeout = 5.0
        start_time = time.time()
        while self.async_loop is None and (time.time() - start_time) < timeout:
            time.sleep(0.01)
        
        if self.async_loop is None:
            raise RuntimeError("Failed to start async loop thread")
        
        logger.info("Dedicated async loop thread started successfully")
    
    def _start_background_processing(self):
        """Start background thread for processing metrics queue."""
        if self.processing_thread and self.processing_thread.is_alive():
            return
            
        self.stop_event.clear()
        self.processing_thread = Thread(
            target=self._background_processor,
            daemon=True,
            name="MetricsProcessor"
        )
        self.processing_thread.start()
        logger.info("Background metrics processing started")
    
    def _background_processor(self):
        """Background thread that processes the metrics queue."""
        batch = []
        last_flush = time.time()
        
        while not self.stop_event.is_set():
            try:
                timeout = 0.1
                
                try:
                    entry = self.metrics_queue.get(timeout=timeout)
                    batch.append(entry)
                    self.metrics_queue.task_done()
                except:
                    pass
                
                current_time = time.time()
                should_flush = (
                    len(batch) >= self.batch_size or
                    (batch and current_time - last_flush >= self.flush_interval)
                )
                
                if should_flush and batch:
                    self._store_batch(batch)
                    batch.clear()
                    last_flush = current_time
                    self.stats["last_flush"] = datetime.now(timezone.utc)
                    
            except Exception as e:
                logger.error(f"Error in metrics background processor: {e}")
                # Clear problematic batch and continue
                batch.clear()
                time.sleep(1)
        
        # Flush remaining items on shutdown
        if batch:
            self._store_batch(batch)
            logger.info(f"Flushed {len(batch)} metrics on shutdown")
    
    def _store_batch(self, batch: List[MetricsEntry]):
        """Store a batch of metrics entries using safe async bridge pattern."""
        if not batch or not self.async_loop or not self.metrics_service:
            return
            
        try:
            stored_count = 0
            
            for entry in batch:
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        self.metrics_service.store_metrics(
                            timestamp=entry.timestamp,
                            agent_name=entry.agent_name,
                            execution_type=entry.execution_type,
                            metrics=entry.metrics,
                            version=entry.version
                        ),
                        self.async_loop
                    )
                    
                    def handle_result(fut):
                        try:
                            result = fut.result()
                            logger.debug(f"Stored metric entry with ID: {result}")
                        except Exception as e:
                            self.stats["storage_errors"] += 1
                            logger.warning(f"Async storage failed: {e}")
                    
                    future.add_done_callback(handle_result)
                    future.result(timeout=5.0)
                    stored_count += 1
                    
                except Exception as entry_error:
                    self.stats["storage_errors"] += 1
                    logger.warning(f"Failed to store metric entry: {entry_error}")
                    continue
            
            self.stats["total_stored"] += stored_count
            logger.debug(f"Stored batch of {stored_count}/{len(batch)} metrics entries via async bridge")
                
        except Exception as e:
            self.stats["storage_errors"] += 1
            logger.error(f"Failed to store metrics batch via async bridge: {e}")
    
    async def collect_metrics(self, 
                            agent_name: str,
                            execution_type: str, 
                            metrics: Dict[str, Any],
                            version: str = "1.0") -> bool:
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
        # Skip if metrics service not available (should not happen)
        if not self.metrics_service:
            return False
            
        try:
            # Create metrics entry
            entry = MetricsEntry(
                timestamp=datetime.now(timezone.utc),
                agent_name=agent_name,
                execution_type=execution_type,
                metrics=metrics,
                version=version
            )
            
            # Non-blocking queue put
            self.metrics_queue.put_nowait(entry)
            self.stats["total_collected"] += 1
            
            return True
            
        except:
            self.stats["queue_overflows"] += 1
            logger.warning("Metrics queue full, dropping metrics entry")
            return False
    
    def collect_from_response(self,
                            response: Any,
                            agent_name: str,
                            execution_type: str,
                            yaml_overrides: Optional[Dict[str, Any]] = None) -> bool:
        """
        Extract and collect metrics from an agent response (sync wrapper).
        
        This method maintains compatibility with existing code.
        """
        try:
            # Extract metrics from response
            metrics = self._extract_metrics_from_response(response, yaml_overrides)
            
            # Use async collect (run in event loop if available)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create task for async collection
                    asyncio.create_task(
                        self.collect_metrics(agent_name, execution_type, metrics)
                    )
                else:
                    # Run in new event loop
                    asyncio.run(
                        self.collect_metrics(agent_name, execution_type, metrics)
                    )
            except:
                # Fallback to sync-like collection
                return asyncio.run(
                    self.collect_metrics(agent_name, execution_type, metrics)
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to collect metrics from response: {e}")
            return False
    
    def _extract_metrics_from_response(self, 
                                     response: Any,
                                     yaml_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract metrics data from agent response."""
        metrics = {}
        
        try:
            # Basic response metrics
            if hasattr(response, 'content'):
                metrics['response_length'] = len(str(response.content))
            
            if hasattr(response, 'model'):
                metrics['model'] = str(response.model)
            
            if hasattr(response, 'usage'):
                usage = response.usage
                if hasattr(usage, 'input_tokens'):
                    metrics['input_tokens'] = usage.input_tokens
                if hasattr(usage, 'output_tokens'):
                    metrics['output_tokens'] = usage.output_tokens
                if hasattr(usage, 'total_tokens'):
                    metrics['total_tokens'] = usage.total_tokens
            
            # Apply YAML overrides
            if yaml_overrides:
                metrics.update(yaml_overrides)
            
        except Exception as e:
            logger.warning(f"Error extracting metrics from response: {e}")
        
        return metrics
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        return {
            **self.stats,
            "queue_size": self.metrics_queue.qsize(),
            "metrics_service_available": self.metrics_service is not None,
            "async_loop_running": self.async_loop is not None and not self.async_loop.is_closed(),
            "async_thread_alive": self.async_loop_thread.is_alive() if self.async_loop_thread else False,
            "is_processing": self.processing_thread.is_alive() if self.processing_thread else False
        }
    
    async def flush(self, timeout: float = 5.0) -> bool:
        """
        Force flush all queued metrics.
        
        Args:
            timeout: Maximum time to wait for flush
            
        Returns:
            bool: True if flushed successfully
        """
        if not self.processing_thread:
            return False
            
        queue_size = self.metrics_queue.qsize()
        if queue_size == 0:
            return True
            
        # Wait for queue to empty
        start_time = time.time()
        while (self.metrics_queue.qsize() > 0 and 
               time.time() - start_time < timeout):
            await asyncio.sleep(0.1)
        
        return self.metrics_queue.qsize() == 0
    
    def close(self):
        """Gracefully shutdown the metrics service."""
        logger.info("Shutting down AsyncMetricsService...")
        
        if self.stop_event:
            self.stop_event.set()
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5.0)
        if self.async_loop and self.async_loop_thread:
            try:
                self.async_loop.call_soon_threadsafe(self.async_loop.stop)
                
                if self.async_loop_thread.is_alive():
                    self.async_loop_thread.join(timeout=5.0)
                    
                if self.async_loop_thread.is_alive():
                    logger.warning("Async loop thread did not shut down within timeout")
                else:
                    logger.info("Async loop thread shut down successfully")
                    
            except Exception as e:
                logger.error(f"Error shutting down async loop: {e}")
        
        logger.info("AsyncMetricsService closed")


# Global metrics service instance
_metrics_service: Optional[AsyncMetricsService] = None


def get_metrics_service() -> Optional[AsyncMetricsService]:
    """Get the global metrics service instance."""
    return _metrics_service


def initialize_metrics_service(config: Optional[Dict[str, Any]] = None) -> AsyncMetricsService:
    """Initialize the global metrics service."""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = AsyncMetricsService(config)
    return _metrics_service


def shutdown_metrics_service():
    """Shutdown the global metrics service."""
    global _metrics_service
    if _metrics_service:
        _metrics_service.close()
        _metrics_service = None