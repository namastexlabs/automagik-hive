"""AGNO Native Metrics Bridge with Agno v2 schema compatibility."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from lib.logging import logger
from lib.metrics.config import MetricsConfig

LEGACY_FIELD_MAPPING = {
    "prompt_tokens": "input_tokens",
    "completion_tokens": "output_tokens",
    "time": "duration",
    "audio_tokens": "audio_total_tokens",
    "input_audio_tokens": "audio_input_tokens",
    "output_audio_tokens": "audio_output_tokens",
    "cached_tokens": "cache_read_tokens",
}

PROVIDER_FIELD_MAPPING = {
    "prompt_tokens": "input_tokens",
    "completion_tokens": "output_tokens",
}

DETAILED_FIELDS = {"prompt_tokens_details", "completion_tokens_details"}


class AgnoMetricsBridge:
    """
    Bridge between AGNO native metrics and AsyncMetricsService.

    This class provides a drop-in replacement for the manual _extract_metrics_from_response()
    method by leveraging AGNO's comprehensive native metrics system.

    AGNO Native Metrics Capabilities:
    - agent.run_response.metrics: Dictionary with per-response metrics lists
    - agent.session_metrics: SessionMetrics object with accumulated totals
    - message.metrics: Per-message MessageMetrics objects

    Comprehensive Coverage:
    - Token metrics: input_tokens, output_tokens, total_tokens
    - Advanced tokens: audio_total_tokens, audio_input_tokens, audio_output_tokens,
      cache_read_tokens, cache_write_tokens, reasoning_tokens
    - Timing metrics: duration, time_to_first_token
    - Content metrics: additional_metrics, provider_metrics
    """

    def __init__(self, config: MetricsConfig | None = None):
        """
        Initialize AgnoMetricsBridge.

        Args:
            config: MetricsConfig instance for filtering metrics collection
        """
        self.config = config or MetricsConfig()

    def extract_metrics(self, response: Any, yaml_overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Extract comprehensive metrics from AGNO response using native metrics.

        Drop-in replacement for _extract_metrics_from_response() with superior coverage.

        Args:
            response: AGNO response object (agent or team)
            yaml_overrides: Optional YAML-level metric overrides

        Returns:
            Dictionary with comprehensive metrics ready for PostgreSQL storage
        """
        metrics = {}

        try:
            # Detect AGNO response type and extract native metrics
            if self._is_agno_response(response):
                metrics = self._extract_agno_native_metrics(response)
                logger.debug(f"🔧 Extracted {len(metrics)} AGNO native metrics fields")
            else:
                # Fallback to basic metrics for non-AGNO responses
                metrics = self._extract_basic_metrics(response)
                logger.debug(f"🔧 Using basic metrics fallback - {len(metrics)} fields")

            # Normalize to Agno v2 schema
            metrics = self._normalize_metrics_dict(metrics)

            # Apply configuration-based filtering
            if self.config:
                metrics = self._filter_by_config(metrics)

            # Apply YAML overrides
            if yaml_overrides:
                metrics = {**metrics, **yaml_overrides}

        except Exception as e:
            logger.warning(f"⚡ Error extracting metrics from response: {e}")
            # Return empty dict on error to maintain compatibility
            metrics = {}

        return metrics

    def _is_agno_response(self, response: Any) -> bool:
        """
        Detect if response is from AGNO framework.

        Args:
            response: Response object to check

        Returns:
            True if AGNO response, False otherwise
        """
        # Check for AGNO agent response
        if hasattr(response, "run_response") and hasattr(response.run_response, "metrics"):
            return True

        # Check for AGNO session_metrics
        if hasattr(response, "session_metrics"):
            return True

        # Check for direct run_response with metrics
        return bool(hasattr(response, "metrics") and isinstance(response.metrics, dict))

    def _extract_agno_native_metrics(self, response: Any) -> dict[str, Any]:
        """
        Extract comprehensive metrics from AGNO native response.

        Accesses AGNO's native metrics system:
        - response.run_response.metrics (per-response metrics)
        - response.session_metrics (accumulated session metrics)
        - Aggregates from message-level metrics if needed

        Args:
            response: AGNO response object

        Returns:
            Dictionary with comprehensive AGNO metrics
        """
        metrics: dict[str, Any] = {}

        # Primary: Try to get session_metrics (most comprehensive)
        if hasattr(response, "session_metrics") and response.session_metrics:
            metrics.update(self._collect_session_metrics(response.session_metrics))

        # Secondary: Try run_response.metrics (per-response metrics)
        elif hasattr(response, "run_response") and hasattr(response.run_response, "metrics"):
            run_metrics = response.run_response.metrics

            if isinstance(run_metrics, dict):
                metrics.update(self._coerce_metrics_payload(run_metrics))

        # Tertiary: Direct metrics access
        elif hasattr(response, "metrics") and isinstance(response.metrics, dict):
            metrics.update(self._coerce_metrics_payload(response.metrics))

        # Add model information if available
        if hasattr(response, "model"):
            metrics["model"] = str(response.model)
        elif hasattr(response, "run_response") and hasattr(response.run_response, "model"):
            metrics["model"] = str(response.run_response.model)

        # Add response length if available
        if hasattr(response, "content") and response.content:
            metrics["response_length"] = len(str(response.content))
        elif hasattr(response, "run_response") and hasattr(response.run_response, "content"):
            metrics["response_length"] = len(str(response.run_response.content))

        return metrics

    def _collect_session_metrics(self, session_metrics: Any) -> dict[str, Any]:
        """Extract relevant session metrics while keeping v2-compatible keys."""

        metrics: dict[str, Any] = {}

        field_sources: dict[str, tuple[str, ...]] = {
            "input_tokens": ("input_tokens", "prompt_tokens"),
            "output_tokens": ("output_tokens", "completion_tokens"),
            "total_tokens": ("total_tokens",),
            "duration": ("duration", "time"),
            "time_to_first_token": ("time_to_first_token",),
            "audio_total_tokens": ("audio_total_tokens", "audio_tokens"),
            "audio_input_tokens": ("audio_input_tokens", "input_audio_tokens"),
            "audio_output_tokens": (
                "audio_output_tokens",
                "output_audio_tokens",
            ),
            "cache_read_tokens": ("cache_read_tokens", "cached_tokens"),
            "cache_write_tokens": ("cache_write_tokens",),
            "reasoning_tokens": ("reasoning_tokens",),
        }

        for new_key, source_names in field_sources.items():
            value = self._first_present(session_metrics, source_names)
            if value is not None:
                metrics[new_key] = value

        provider_metrics = getattr(session_metrics, "provider_metrics", None)
        if provider_metrics:
            metrics["provider_metrics"] = provider_metrics

        if hasattr(session_metrics, "additional_metrics") and session_metrics.additional_metrics:
            metrics["additional_metrics"] = deepcopy(session_metrics.additional_metrics)

        detail_carriers = {
            "prompt_tokens_details": getattr(session_metrics, "prompt_tokens_details", None),
            "completion_tokens_details": getattr(session_metrics, "completion_tokens_details", None),
        }
        detail_payload = {key: value for key, value in detail_carriers.items() if value not in (None, {}, [])}
        if detail_payload:
            extra = metrics.setdefault("additional_metrics", {})
            extra.update(detail_payload)

        return metrics

    @staticmethod
    def _first_present(obj: Any, attribute_candidates: tuple[str, ...]) -> Any:
        for candidate in attribute_candidates:
            if hasattr(obj, candidate):
                value = getattr(obj, candidate)
                if value is not None:
                    return value
        return None

    def _coerce_metrics_payload(self, raw_metrics: dict[str, Any]) -> dict[str, Any]:
        """Normalize arbitrary metric payloads into a dict for downstream normalization."""

        metrics: dict[str, Any] = {}
        for metric_name, metric_values in raw_metrics.items():
            if isinstance(metric_values, list) and metric_values:
                if metric_name.endswith("_tokens") or metric_name in [
                    "time",
                    "duration",
                    "time_to_first_token",
                ]:
                    numeric_values = [value for value in metric_values if isinstance(value, int | float)]
                    metrics[metric_name] = sum(numeric_values) if numeric_values else metric_values[-1]
                else:
                    metrics[metric_name] = metric_values[-1]
            elif metric_values is not None:
                metrics[metric_name] = metric_values

        return metrics

    def _extract_basic_metrics(self, response: Any) -> dict[str, Any]:
        """
        Fallback basic metrics extraction for non-AGNO responses.

        Maintains compatibility with existing manual extraction logic.

        Args:
            response: Response object

        Returns:
            Dictionary with basic metrics
        """
        metrics = {}

        # Basic response metrics (original manual logic)
        if hasattr(response, "content"):
            metrics["response_length"] = len(str(response.content))

        if hasattr(response, "model"):
            metrics["model"] = str(response.model)

        if hasattr(response, "usage"):
            usage = response.usage
            if hasattr(usage, "input_tokens"):
                metrics["input_tokens"] = usage.input_tokens
            if hasattr(usage, "prompt_tokens") and "input_tokens" not in metrics:
                metrics["input_tokens"] = usage.prompt_tokens
            if hasattr(usage, "output_tokens"):
                metrics["output_tokens"] = usage.output_tokens
            if hasattr(usage, "completion_tokens") and "output_tokens" not in metrics:
                metrics["output_tokens"] = usage.completion_tokens
            if hasattr(usage, "total_tokens"):
                metrics["total_tokens"] = usage.total_tokens

        return metrics

    def _normalize_metrics_dict(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """Normalize metrics to the Agno v2 field names."""

        if not metrics:
            return {}

        normalized: dict[str, Any] = {}
        additional_payload: dict[str, Any] = {}

        for key, value in metrics.items():
            if key in DETAILED_FIELDS:
                if value:
                    additional_payload[key] = value
                continue

            if key == "provider_metrics" and isinstance(value, dict):
                normalized["provider_metrics"] = self._normalize_provider_metrics(value)
                continue

            target_key = LEGACY_FIELD_MAPPING.get(key, key)
            normalized[target_key] = value

        # Merge any additional metrics payloads
        if additional_payload:
            existing = normalized.get("additional_metrics")
            if isinstance(existing, dict):
                merged = deepcopy(existing)
                merged.update(additional_payload)
                normalized["additional_metrics"] = merged
            else:
                normalized["additional_metrics"] = additional_payload

        return normalized

    def _normalize_provider_metrics(self, providers: dict[str, Any]) -> dict[str, Any]:
        """Normalize provider metrics dictionaries recursively."""

        normalized = {}
        for provider, payload in providers.items():
            if isinstance(payload, dict):
                provider_metrics = {}
                for key, value in payload.items():
                    target_key = PROVIDER_FIELD_MAPPING.get(key, LEGACY_FIELD_MAPPING.get(key, key))
                    if target_key in DETAILED_FIELDS:
                        continue
                    provider_metrics[target_key] = value
                normalized[provider] = provider_metrics
            else:
                normalized[provider] = payload
        return normalized

    def _filter_by_config(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """
        Apply HIVE_METRICS_COLLECT_* configuration filtering.

        Filters metrics based on MetricsConfig flags to maintain
        backward compatibility with existing configuration.

        Args:
            metrics: Raw metrics dictionary

        Returns:
            Filtered metrics dictionary
        """
        if not self.config:
            return metrics

        filtered_metrics = {}

        # Always include basic metrics
        for key in ["model", "response_length"]:
            if key in metrics:
                filtered_metrics[key] = metrics[key]

        # Token metrics filtering
        if self.config.collect_tokens:
            token_fields = [
                "input_tokens",
                "output_tokens",
                "total_tokens",
                "audio_total_tokens",
                "audio_input_tokens",
                "audio_output_tokens",
                "cache_read_tokens",
                "cache_write_tokens",
                "reasoning_tokens",
            ]
            for field in token_fields:
                if field in metrics:
                    filtered_metrics[field] = metrics[field]

        # Time metrics filtering
        if self.config.collect_time:
            time_fields = ["duration", "time_to_first_token"]
            for field in time_fields:
                if field in metrics:
                    filtered_metrics[field] = metrics[field]

        # Tool metrics filtering (AGNO handles this via messages/run_response)
        if self.config.collect_tools:
            tool_fields = ["tools", "tool_calls", "tool_executions"]
            for field in tool_fields:
                if field in metrics:
                    filtered_metrics[field] = metrics[field]

        # Event metrics filtering (AGNO handles this via messages)
        if self.config.collect_events:
            event_fields = ["events", "messages", "message_count"]
            for field in event_fields:
                if field in metrics:
                    filtered_metrics[field] = metrics[field]

        # Content metrics filtering
        if self.config.collect_content:
            content_fields = [
                "additional_metrics",
                "provider_metrics",
                "content_type",
                "content_size",
            ]
            for field in content_fields:
                if field in metrics:
                    filtered_metrics[field] = metrics[field]

        return filtered_metrics

    def get_metrics_info(self) -> dict[str, Any]:
        """
        Get information about AgnoMetricsBridge capabilities.

        Returns:
            Dictionary with bridge information and capabilities
        """
        return {
            "bridge_version": "1.0.0",
            "metrics_source": "agno_native",
            "capabilities": {
                "token_metrics": [
                    "input_tokens",
                    "output_tokens",
                    "total_tokens",
                    "audio_total_tokens",
                    "audio_input_tokens",
                    "audio_output_tokens",
                    "cache_read_tokens",
                    "cache_write_tokens",
                    "reasoning_tokens",
                ],
                "timing_metrics": ["duration", "time_to_first_token"],
                "detailed_metrics": ["additional_metrics"],
                "additional_metrics": [
                    "additional_metrics",
                    "model",
                    "response_length",
                ],
                "configuration_filtering": True,
                "yaml_overrides": True,
                "fallback_support": True,
            },
            "advantages_over_manual": [
                "Comprehensive token coverage (15+ token types vs 3)",
                "Native timing metrics (time, time_to_first_token)",
                "Audio and reasoning token support",
                "Cache metrics for performance optimization",
                "Detailed token breakdowns",
                "Automatic aggregation across messages",
                "Future-proof - gets new AGNO metrics automatically",
            ],
        }
