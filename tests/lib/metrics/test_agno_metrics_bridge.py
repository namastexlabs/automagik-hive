"""Tests for the AgnoMetricsBridge v2 schema normalization."""

from types import SimpleNamespace

from lib.metrics.agno_metrics_bridge import AgnoMetricsBridge


def _build_session_metrics(**overrides):
    base = {
        "prompt_tokens": 42,
        "completion_tokens": 21,
        "total_tokens": 63,
        "time": 1.5,
        "cache_write_tokens": 3,
        "provider_metrics": {"openai": {"prompt_tokens": 42, "completion_tokens": 21}},
        "additional_metrics": {"custom_latency": 12.3},
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_bridge_normalizes_session_metrics_to_v2_schema():
    """Session-level metrics should drop v1 keys and expose v2 names."""

    response = SimpleNamespace(
        session_metrics=_build_session_metrics(),
        model="gpt-test",
        content="hello world",
    )

    bridge = AgnoMetricsBridge()

    metrics = bridge.extract_metrics(response)

    assert metrics["input_tokens"] == 42
    assert metrics["output_tokens"] == 21
    assert metrics["total_tokens"] == 63
    assert metrics["duration"] == 1.5
    assert metrics["cache_write_tokens"] == 3
    assert metrics["provider_metrics"] == {"openai": {"input_tokens": 42, "output_tokens": 21}}
    assert "prompt_tokens" not in metrics
    assert "completion_tokens" not in metrics
    assert metrics["additional_metrics"] == {"custom_latency": 12.3}


def test_bridge_handles_run_response_metrics_and_yaml_overrides():
    """Fallback metrics and overrides should also be normalized and merged."""

    run_response = SimpleNamespace(
        metrics={
            "duration": 2.0,
            "prompt_tokens": 5,
            "completion_tokens": 7,
            "provider_metrics": {"anthropic": {"input_tokens": 5, "output_tokens": 7}},
        },
        model="anthropic-sonnet",
        content="response",
    )

    response = SimpleNamespace(run_response=run_response)
    bridge = AgnoMetricsBridge()

    overrides = {"input_tokens": 999, "custom_field": "override"}
    metrics = bridge.extract_metrics(response, overrides)

    assert metrics["input_tokens"] == 999  # override takes precedence
    assert metrics["output_tokens"] == 7
    assert metrics["duration"] == 2.0
    assert metrics["provider_metrics"] == {"anthropic": {"input_tokens": 5, "output_tokens": 7}}
    assert metrics["custom_field"] == "override"
    assert "prompt_tokens" not in metrics


def test_bridge_returns_empty_dict_on_errors():
    """Bridge should swallow unexpected errors and return an empty dict."""

    class BrokenObject:
        def __getattr__(self, _):
            raise RuntimeError("boom")

    bridge = AgnoMetricsBridge()

    metrics = bridge.extract_metrics(BrokenObject())
    assert metrics == {}
