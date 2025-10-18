"""Async metrics service behaviour for Agno v2 schemas."""

import asyncio
from types import SimpleNamespace

import pytest

from lib.metrics.async_metrics_service import AsyncMetricsService


@pytest.mark.asyncio
async def test_collect_from_response_normalizes_metrics(monkeypatch):
    """collect_from_response should hand off v2-normalized metrics to the queue task."""

    service = AsyncMetricsService()
    service._initialized = True
    service.metrics_service = object()  # truthy guard so collection proceeds

    captured_metrics: list[dict] = []

    async def fake_collect(agent_name, execution_type, metrics, version="1.0"):
        captured_metrics.append(metrics)
        return True

    service.collect_metrics = fake_collect  # type: ignore[method-assign]

    created_tasks: list[asyncio.Task] = []
    original_create_task = asyncio.create_task

    def capture_task(coro):
        task = original_create_task(coro)
        created_tasks.append(task)
        return task

    monkeypatch.setattr(asyncio, "create_task", capture_task)

    response = SimpleNamespace(
        session_metrics=SimpleNamespace(
            prompt_tokens=10,
            completion_tokens=4,
            total_tokens=14,
            time=0.25,
            provider_metrics={"groq": {"prompt_tokens": 10, "completion_tokens": 4}},
        )
    )

    result = service.collect_from_response(response, "demo-agent", "agent")

    # Allow scheduled task to finish
    await asyncio.gather(*created_tasks)

    assert result is True
    assert captured_metrics, "metrics should be captured from the async task"

    normalized = captured_metrics[0]
    assert normalized["input_tokens"] == 10
    assert normalized["output_tokens"] == 4
    assert normalized["duration"] == 0.25
    assert normalized["provider_metrics"] == {"groq": {"input_tokens": 10, "output_tokens": 4}}
    assert "prompt_tokens" not in normalized
