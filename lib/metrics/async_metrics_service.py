"""
Async Metrics Service with Queue Architecture

High-performance async metrics collection designed for <0.1ms agent latency impact.
Uses background queue processing with psycopg connection pooling.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from queue import Queue
from threading import Thread, Event

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
        self.database_url = self._get_database_url()
        self.table_name = self.config.get("table_name", "agent_metrics")
        self.batch_size = self.config.get("batch_size", 50)
        self.flush_interval = self.config.get("flush_interval", 5.0)  # seconds
        
        # Queue and processing
        self.metrics_queue = Queue(maxsize=1000)
        self.processing_thread = None
        self.stop_event = Event()
        
        # Connection pool
        self.connection_pool = None
        
        # Performance tracking
        self.stats = {
            "total_collected": 0,
            "total_stored": 0,
            "queue_overflows": 0,
            "storage_errors": 0,
            "last_flush": None
        }
        
        # Initialize
        self._initialize()
    
    def _get_database_url(self) -> str:
        """Get database URL from config or environment."""
        return (self.config.get("database_url") or 
                os.getenv("HIVE_DATABASE_URL", 
                         "postgresql+psycopg://ai:ai@localhost:5532/ai"))
    
    def _initialize(self):
        """Initialize connection pool and create table."""
        try:
            # Import psycopg when needed
            import psycopg
            from psycopg_pool import ConnectionPool
            
            # Create connection pool
            self.connection_pool = ConnectionPool(
                conninfo=self.database_url,
                min_size=1,
                max_size=5
            )
            
            # Create table if needed
            self._create_table_if_not_exists()
            
            # Start background processing
            self._start_background_processing()
            
            logger.info("AsyncMetricsService initialized successfully")
            
        except ImportError:
            logger.warning("psycopg not available - AsyncMetricsService will be disabled")
            self.connection_pool = None
        except Exception as e:
            logger.error(f"Failed to initialize AsyncMetricsService: {e}")
            raise
    
    def _create_table_if_not_exists(self):
        """Create metrics table if it doesn't exist."""
        try:
            with self.connection_pool.connection() as conn:
                create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    agent_name VARCHAR(255) NOT NULL,
                    execution_type VARCHAR(50) NOT NULL,
                    metrics JSONB NOT NULL,
                    version VARCHAR(10) NOT NULL DEFAULT '1.0',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_timestamp 
                ON {self.table_name}(timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_agent_name 
                ON {self.table_name}(agent_name);
                """
                
                with conn.cursor() as cursor:
                    cursor.execute(create_table_sql)
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to create metrics table: {e}")
    
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
                # Collect metrics into batch
                timeout = 0.1  # 100ms timeout for responsiveness
                
                try:
                    entry = self.metrics_queue.get(timeout=timeout)
                    batch.append(entry)
                    self.metrics_queue.task_done()
                except:
                    pass  # Timeout is expected
                
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
        """Store a batch of metrics entries to database."""
        if not batch:
            return
            
        try:
            with self.connection_pool.connection() as conn:
                # Prepare batch insert using psycopg3 syntax
                insert_sql = f"""
                INSERT INTO {self.table_name} 
                (timestamp, agent_name, execution_type, metrics, version)
                VALUES (%s, %s, %s, %s, %s)
                """
                
                # Convert batch to values tuple
                values = []
                for entry in batch:
                    values.append((
                        entry.timestamp,
                        entry.agent_name,
                        entry.execution_type,
                        json.dumps(entry.metrics),
                        entry.version
                    ))
                
                # Execute batch insert using executemany
                with conn.cursor() as cursor:
                    cursor.executemany(insert_sql, values)
                conn.commit()
                
                # Update stats
                self.stats["total_stored"] += len(batch)
                
                logger.debug(f"Stored batch of {len(batch)} metrics entries")
                
        except Exception as e:
            self.stats["storage_errors"] += 1
            logger.error(f"Failed to store metrics batch: {e}")
    
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
        # Skip if service not properly initialized
        if not self.connection_pool:
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
            # Queue full - drop metrics to maintain performance
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
            "connection_pool_size": self.connection_pool.get_stats()["pool_size"] if self.connection_pool else 0,
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
        if self.stop_event:
            self.stop_event.set()
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5.0)
        
        if self.connection_pool:
            self.connection_pool.close()
        
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