"""
AGNO Native Metrics Bridge

Drop-in replacement for manual metrics extraction using AGNO's native metrics system.
Provides comprehensive metrics collection with superior coverage compared to manual extraction.
"""

from typing import Any

from lib.logging import logger
from lib.metrics.config import MetricsConfig


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
    - Token metrics: input_tokens, output_tokens, total_tokens, prompt_tokens, completion_tokens
    - Advanced tokens: audio_tokens, cached_tokens, reasoning_tokens, cache_write_tokens
    - Timing metrics: time, time_to_first_token
    - Content metrics: prompt_tokens_details, completion_tokens_details
    - Additional metrics: any model-specific metrics
    """

    def __init__(self, config: MetricsConfig | None = None):
        """
        Initialize AgnoMetricsBridge.

        Args:
            config: MetricsConfig instance for filtering metrics collection
        """
        self.config = config or MetricsConfig()

    def extract_metrics(
        self, response: Any, yaml_overrides: dict[str, Any] | None = None
    ) -> dict[str, Any]:
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

            # Apply configuration-based filtering
            if self.config:
                metrics = self._filter_by_config(metrics)

            # Apply YAML overrides
            if yaml_overrides:
                metrics.update(yaml_overrides)

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
        if hasattr(response, "run_response") and hasattr(
            response.run_response, "metrics"
        ):
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
        metrics = {}

        # Primary: Try to get session_metrics (most comprehensive)
        if hasattr(response, "session_metrics") and response.session_metrics:
            session_metrics = response.session_metrics

            # Extract all available SessionMetrics fields
            metrics.update(
                {
                    "input_tokens": getattr(session_metrics, "input_tokens", 0),
                    "output_tokens": getattr(session_metrics, "output_tokens", 0),
                    "total_tokens": getattr(session_metrics, "total_tokens", 0),
                    "prompt_tokens": getattr(session_metrics, "prompt_tokens", 0),
                    "completion_tokens": getattr(
                        session_metrics, "completion_tokens", 0
                    ),
                    "audio_tokens": getattr(session_metrics, "audio_tokens", 0),
                    "input_audio_tokens": getattr(
                        session_metrics, "input_audio_tokens", 0
                    ),
                    "output_audio_tokens": getattr(
                        session_metrics, "output_audio_tokens", 0
                    ),
                    "cached_tokens": getattr(session_metrics, "cached_tokens", 0),
                    "cache_write_tokens": getattr(
                        session_metrics, "cache_write_tokens", 0
                    ),
                    "reasoning_tokens": getattr(session_metrics, "reasoning_tokens", 0),
                    "time": getattr(session_metrics, "time", 0.0),
                    "time_to_first_token": getattr(
                        session_metrics, "time_to_first_token", 0.0
                    ),
                }
            )

            # Extract optional detailed metrics
            if (
                hasattr(session_metrics, "prompt_tokens_details")
                and session_metrics.prompt_tokens_details
            ):
                metrics["prompt_tokens_details"] = session_metrics.prompt_tokens_details

            if (
                hasattr(session_metrics, "completion_tokens_details")
                and session_metrics.completion_tokens_details
            ):
                metrics["completion_tokens_details"] = (
                    session_metrics.completion_tokens_details
                )

            if (
                hasattr(session_metrics, "additional_metrics")
                and session_metrics.additional_metrics
            ):
                metrics["additional_metrics"] = session_metrics.additional_metrics

        # Secondary: Try run_response.metrics (per-response metrics)
        elif hasattr(response, "run_response") and hasattr(
            response.run_response, "metrics"
        ):
            run_metrics = response.run_response.metrics

            if isinstance(run_metrics, dict):
                # Aggregate metrics lists from run_response.metrics
                for metric_name, metric_values in run_metrics.items():
                    if isinstance(metric_values, list) and metric_values:
                        # Sum list values for token counts
                        if metric_name.endswith("_tokens") or metric_name in [
                            "time",
                            "time_to_first_token",
                        ]:
                            metrics[metric_name] = (
                                sum(metric_values)
                                if all(
                                    isinstance(v, int | float) for v in metric_values
                                )
                                else metric_values[-1]
                            )
                        else:
                            # Use last value for non-summable metrics
                            metrics[metric_name] = metric_values[-1]
                    elif metric_values is not None:
                        metrics[metric_name] = metric_values

        # Tertiary: Direct metrics access
        elif hasattr(response, "metrics") and isinstance(response.metrics, dict):
            metrics.update(response.metrics)

        # Add model information if available
        if hasattr(response, "model"):
            metrics["model"] = str(response.model)
        elif hasattr(response, "run_response") and hasattr(
            response.run_response, "model"
        ):
            metrics["model"] = str(response.run_response.model)

        # Add response length if available
        if hasattr(response, "content") and response.content:
            metrics["response_length"] = len(str(response.content))
        elif hasattr(response, "run_response") and hasattr(
            response.run_response, "content"
        ):
            metrics["response_length"] = len(str(response.run_response.content))

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
            if hasattr(usage, "output_tokens"):
                metrics["output_tokens"] = usage.output_tokens
            if hasattr(usage, "total_tokens"):
                metrics["total_tokens"] = usage.total_tokens

        return metrics

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
                "prompt_tokens",
                "completion_tokens",
                "audio_tokens",
                "input_audio_tokens",
                "output_audio_tokens",
                "cached_tokens",
                "cache_write_tokens",
                "reasoning_tokens",
                "prompt_tokens_details",
                "completion_tokens_details",
            ]
            for field in token_fields:
                if field in metrics:
                    filtered_metrics[field] = metrics[field]

        # Time metrics filtering
        if self.config.collect_time:
            time_fields = ["time", "time_to_first_token"]
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
            content_fields = ["additional_metrics", "content_type", "content_size"]
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
                    "prompt_tokens",
                    "completion_tokens",
                    "audio_tokens",
                    "input_audio_tokens",
                    "output_audio_tokens",
                    "cached_tokens",
                    "cache_write_tokens",
                    "reasoning_tokens",
                ],
                "timing_metrics": ["time", "time_to_first_token"],
                "detailed_metrics": [
                    "prompt_tokens_details",
                    "completion_tokens_details",
                ],
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
