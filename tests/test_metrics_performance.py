"""
Performance and load tests for AsyncMetricsService.

Tests verify that the metrics service delivers <0.1ms latency performance
and handles high load with concurrent processing correctly.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from lib.metrics.async_metrics_service import AsyncMetricsService


class TestMetricsServicePerformance:
    """Test performance characteristics of the AsyncMetricsService."""

    @pytest.fixture
    async def mock_metrics_service(self):
        """Create a metrics service with a mocked storage backend."""
        # Mock the MetricsService to avoid database dependencies
        mock_storage = AsyncMock()
        mock_storage.store_metrics.return_value = "test_id_123"

        config = {"batch_size": 10, "flush_interval": 0.5, "queue_size": 100}

        service = AsyncMetricsService(config)
        # Replace with our mock
        service.metrics_service = mock_storage

        await service.initialize()

        yield service, mock_storage

        # Cleanup
        await service.close()

    @pytest.mark.asyncio
    async def test_single_metric_collection_latency(self, mock_metrics_service):
        """Test that single metric collection has <0.1ms latency."""
        service, mock_storage = mock_metrics_service

        # Warm up
        await service.collect_metrics("test_agent", "agent", {"test": "value"})

        # Measure latency
        start_time = time.perf_counter()
        result = await service.collect_metrics("test_agent", "agent", {"test": "value"})
        end_time = time.perf_counter()

        latency_ms = (end_time - start_time) * 1000

        assert result is True
        assert latency_ms < 0.1, f"Latency {latency_ms:.3f}ms exceeds 0.1ms target"

    @pytest.mark.asyncio
    async def test_batch_collection_latency(self, mock_metrics_service):
        """Test that batch collection maintains low latency."""
        service, mock_storage = mock_metrics_service

        # Collect multiple metrics quickly
        latencies = []
        for i in range(50):
            start_time = time.perf_counter()
            result = await service.collect_metrics(f"agent_{i}", "agent", {"metric": i})
            end_time = time.perf_counter()

            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
            assert result is True

        # Check latencies
        max_latency = max(latencies)
        avg_latency = sum(latencies) / len(latencies)

        assert max_latency < 0.1, (
            f"Max latency {max_latency:.3f}ms exceeds 0.1ms target"
        )
        assert avg_latency < 0.05, (
            f"Avg latency {avg_latency:.3f}ms exceeds 0.05ms target"
        )

    @pytest.mark.asyncio
    async def test_concurrent_collection_performance(self, mock_metrics_service):
        """Test concurrent metric collection performance."""
        service, mock_storage = mock_metrics_service

        async def collect_metric(agent_id):
            start_time = time.perf_counter()
            result = await service.collect_metrics(
                f"agent_{agent_id}",
                "agent",
                {"id": agent_id},
            )
            end_time = time.perf_counter()
            return result, (end_time - start_time) * 1000

        # Run 100 concurrent collections
        tasks = [collect_metric(i) for i in range(100)]
        results = await asyncio.gather(*tasks)

        # Verify all succeeded
        for result, latency in results:
            assert result is True
            assert latency < 0.2, f"Concurrent latency {latency:.3f}ms too high"

        # Check average performance
        latencies = [latency for _, latency in results]
        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency < 0.1, f"Concurrent avg latency {avg_latency:.3f}ms too high"

    @pytest.mark.asyncio
    async def test_queue_overflow_handling(self, mock_metrics_service):
        """Test that queue overflow is handled gracefully."""
        service, mock_storage = mock_metrics_service

        # Fill up the queue (size 100 from fixture)
        successful_collections = 0
        queue_overflows = 0

        for i in range(150):  # Try to add more than queue size
            result = await service.collect_metrics(
                f"agent_{i}",
                "agent",
                {"overflow": i},
            )
            if result:
                successful_collections += 1
            else:
                queue_overflows += 1

        # Should have some successful collections and some overflows
        assert successful_collections <= 100, (
            "Too many successful collections for queue size"
        )
        assert queue_overflows >= 50, (
            "Expected some queue overflows with 150 items and size 100"
        )
        assert service.get_stats()["queue_overflows"] == queue_overflows

    @pytest.mark.asyncio
    async def test_background_processing_efficiency(self, mock_metrics_service):
        """Test that background processing handles batches efficiently."""
        service, mock_storage = mock_metrics_service

        # Add metrics to trigger batch processing
        for i in range(25):  # More than batch size of 10
            await service.collect_metrics(f"agent_{i}", "agent", {"batch_test": i})

        # Wait for background processing
        await asyncio.sleep(1.0)  # Wait for flush interval

        # Verify batch processing occurred
        stats = service.get_stats()
        assert stats["total_collected"] == 25

        # Check that store_metrics was called multiple times (batched)
        assert mock_storage.store_metrics.call_count > 0
        assert (
            mock_storage.store_metrics.call_count <= 25
        )  # Should be batched, not 1-to-1

    @pytest.mark.asyncio
    async def test_error_recovery_performance(self, mock_metrics_service):
        """Test that storage errors don't impact collection performance."""
        service, mock_storage = mock_metrics_service

        # Make storage fail occasionally
        call_count = 0

        async def failing_store_metrics(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:  # Fail every 3rd call
                raise Exception("Storage error")
            return f"success_{call_count}"

        mock_storage.store_metrics.side_effect = failing_store_metrics

        # Collect metrics despite storage errors
        start_time = time.perf_counter()
        for i in range(30):
            result = await service.collect_metrics(
                f"agent_{i}",
                "agent",
                {"error_test": i},
            )
            assert result is True  # Collection should still succeed

        collection_time = (time.perf_counter() - start_time) * 1000

        # Collection should remain fast despite storage errors
        avg_latency = collection_time / 30
        assert avg_latency < 0.1, (
            f"Error recovery avg latency {avg_latency:.3f}ms too high"
        )

        # Wait for background processing
        await asyncio.sleep(1.0)

        # Check stats show some storage errors
        stats = service.get_stats()
        assert stats["storage_errors"] > 0, "Expected some storage errors"
        assert stats["total_collected"] == 30, "Should have collected all metrics"

    @pytest.mark.asyncio
    async def test_flush_performance(self, mock_metrics_service):
        """Test that flush operation is efficient."""
        service, mock_storage = mock_metrics_service

        # Add some metrics
        for i in range(15):
            await service.collect_metrics(f"agent_{i}", "agent", {"flush_test": i})

        # Measure flush time
        start_time = time.perf_counter()
        result = await service.flush(timeout=2.0)
        flush_time = (time.perf_counter() - start_time) * 1000

        assert result is True, "Flush should succeed"
        assert flush_time < 100, f"Flush took {flush_time:.1f}ms, should be <100ms"

        # Queue should be empty after flush
        assert service.get_stats()["queue_size"] == 0

    @pytest.mark.asyncio
    async def test_shutdown_performance(self, mock_metrics_service):
        """Test that shutdown is quick and clean."""
        service, mock_storage = mock_metrics_service

        # Add some metrics
        for i in range(5):
            await service.collect_metrics(f"agent_{i}", "agent", {"shutdown_test": i})

        # Measure shutdown time
        start_time = time.perf_counter()
        await service.close()
        shutdown_time = (time.perf_counter() - start_time) * 1000

        assert shutdown_time < 200, (
            f"Shutdown took {shutdown_time:.1f}ms, should be <200ms"
        )

        # Service should be marked as not initialized
        stats = service.get_stats()
        assert stats["initialized"] is False

    def test_sync_wrapper_performance(self):
        """Test that the sync wrapper (collect_from_response) is efficient."""
        config = {"batch_size": 10, "flush_interval": 1.0, "queue_size": 100}

        service = AsyncMetricsService(config)

        # Mock response object
        mock_response = MagicMock()
        mock_response.content = "test response"
        mock_response.model = "test_model"
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_response.usage.total_tokens = 150

        # Test sync wrapper performance
        start_time = time.perf_counter()
        with pytest.raises(RuntimeError):  # Expected since no event loop
            service.collect_from_response(
                response=mock_response,
                agent_name="test_agent",
                execution_type="agent",
            )
        wrapper_time = (time.perf_counter() - start_time) * 1000

        # Should fail quickly without blocking
        assert wrapper_time < 1.0, (
            f"Sync wrapper took {wrapper_time:.3f}ms, should be <1ms"
        )

    @pytest.mark.asyncio
    async def test_memory_efficiency(self, mock_metrics_service):
        """Test that memory usage doesn't grow unbounded."""
        service, mock_storage = mock_metrics_service

        # Get initial stats
        service.get_stats()

        # Process many metrics
        for batch in range(10):
            for i in range(20):
                await service.collect_metrics(
                    f"batch_{batch}_agent_{i}",
                    "agent",
                    {"data": "x" * 100},
                )

            # Wait for processing
            await asyncio.sleep(0.1)

        # Wait for final processing
        await asyncio.sleep(1.0)

        final_stats = service.get_stats()

        # Queue should not be growing indefinitely
        assert final_stats["queue_size"] < 50, (
            f"Queue size {final_stats['queue_size']} too large"
        )

        # Most metrics should have been processed
        processing_rate = final_stats["total_stored"] / final_stats["total_collected"]
        assert processing_rate > 0.8, f"Processing rate {processing_rate:.2f} too low"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
