"""
Comprehensive test suite for lib/metrics/agno_metrics_bridge.py

This module tests the AgnoMetricsBridge class targeting the 45 uncovered lines.
Focuses on metrics bridge functionality, Agno integration, metric collection,
and bridge patterns for improved test coverage.
"""

from unittest.mock import Mock, patch

from lib.metrics.agno_metrics_bridge import AgnoMetricsBridge
from lib.metrics.config import MetricsConfig


class TestAgnoMetricsBridgeInitialization:
    """Test AgnoMetricsBridge initialization and configuration."""

    def test_init_without_config(self):
        """Test initialization without configuration."""
        bridge = AgnoMetricsBridge()
        assert bridge is not None
        assert bridge.config is not None
        assert isinstance(bridge.config, MetricsConfig)

    def test_init_with_config(self):
        """Test initialization with custom configuration."""
        custom_config = MetricsConfig(
            collect_tokens=False,
            collect_time=True,
            collect_tools=False,
            collect_events=True,
            collect_content=False
        )
        bridge = AgnoMetricsBridge(config=custom_config)
        assert bridge.config is custom_config
        assert not bridge.config.collect_tokens
        assert bridge.config.collect_time

    def test_init_with_none_config(self):
        """Test initialization with None config creates default."""
        bridge = AgnoMetricsBridge(config=None)
        assert bridge.config is not None
        assert isinstance(bridge.config, MetricsConfig)


class TestAgnoResponseDetection:
    """Test AGNO response detection functionality."""

    def test_is_agno_response_with_run_response_metrics(self):
        """Test detection of AGNO response with run_response.metrics."""
        # Mock AGNO response with run_response.metrics
        mock_response = Mock()
        mock_response.run_response = Mock()
        mock_response.run_response.metrics = {"input_tokens": [100], "output_tokens": [50]}

        bridge = AgnoMetricsBridge()
        assert bridge._is_agno_response(mock_response) is True

    def test_is_agno_response_with_session_metrics(self):
        """Test detection of AGNO response with session_metrics."""
        # Mock AGNO response with session_metrics only (no run_response)
        mock_response = Mock(spec=["session_metrics"])
        mock_response.session_metrics = Mock()
        mock_response.session_metrics.input_tokens = 100

        bridge = AgnoMetricsBridge()
        assert bridge._is_agno_response(mock_response) is True

    def test_is_agno_response_with_direct_metrics(self):
        """Test detection of AGNO response with direct metrics."""
        # Mock AGNO response with direct metrics dict only (no run_response or session_metrics)
        mock_response = Mock(spec=["metrics"])
        mock_response.metrics = {"input_tokens": 100, "output_tokens": 50}

        bridge = AgnoMetricsBridge()
        assert bridge._is_agno_response(mock_response) is True

    def test_is_agno_response_without_run_response_attr(self):
        """Test detection fails when run_response missing metrics attr."""
        # Mock response with run_response but no metrics - use spec to avoid attributes
        mock_response = Mock(spec=["run_response"])
        mock_response.run_response = Mock(spec=[])  # run_response without metrics

        bridge = AgnoMetricsBridge()
        assert bridge._is_agno_response(mock_response) is False

    def test_is_agno_response_with_non_dict_metrics(self):
        """Test detection fails when metrics is not a dict."""
        # Mock response with non-dict metrics
        mock_response = Mock()
        mock_response.metrics = "not_a_dict"
        del mock_response.run_response
        del mock_response.session_metrics

        bridge = AgnoMetricsBridge()
        assert bridge._is_agno_response(mock_response) is False

    def test_is_agno_response_with_empty_object(self):
        """Test detection fails with empty/minimal object."""
        # Mock empty response object
        mock_response = Mock()
        # Remove all default attributes
        del mock_response.run_response
        del mock_response.session_metrics
        del mock_response.metrics

        bridge = AgnoMetricsBridge()
        assert bridge._is_agno_response(mock_response) is False

    def test_is_agno_response_with_none(self):
        """Test detection handles None response."""
        bridge = AgnoMetricsBridge()
        # Should not raise exception with None
        result = bridge._is_agno_response(None)
        assert result is False


class TestAgnoNativeMetricsExtraction:
    """Test AGNO native metrics extraction functionality."""

    def test_extract_agno_native_metrics_with_session_metrics(self):
        """Test extraction from session_metrics (primary method)."""
        # Mock AGNO response with comprehensive session_metrics
        mock_response = Mock()
        mock_session_metrics = Mock()
        mock_session_metrics.input_tokens = 150
        mock_session_metrics.output_tokens = 75
        mock_session_metrics.total_tokens = 225
        mock_session_metrics.prompt_tokens = 100
        mock_session_metrics.completion_tokens = 50
        mock_session_metrics.audio_tokens = 25
        mock_session_metrics.input_audio_tokens = 10
        mock_session_metrics.output_audio_tokens = 15
        mock_session_metrics.cached_tokens = 30
        mock_session_metrics.cache_write_tokens = 5
        mock_session_metrics.reasoning_tokens = 40
        mock_session_metrics.time = 2.5
        mock_session_metrics.time_to_first_token = 0.8
        mock_response.session_metrics = mock_session_metrics

        bridge = AgnoMetricsBridge()
        metrics = bridge._extract_agno_native_metrics(mock_response)

        # Verify all session metrics are extracted
        assert metrics["input_tokens"] == 150
        assert metrics["output_tokens"] == 75
        assert metrics["total_tokens"] == 225
        assert metrics["prompt_tokens"] == 100
        assert metrics["completion_tokens"] == 50
        assert metrics["audio_tokens"] == 25
        assert metrics["input_audio_tokens"] == 10
        assert metrics["output_audio_tokens"] == 15
        assert metrics["cached_tokens"] == 30
        assert metrics["cache_write_tokens"] == 5
        assert metrics["reasoning_tokens"] == 40
        assert metrics["time"] == 2.5
        assert metrics["time_to_first_token"] == 0.8

    def test_extract_agno_native_metrics_with_detailed_metrics(self):
        """Test extraction of detailed metrics from session_metrics."""
        # Mock AGNO response with detailed metrics
        mock_response = Mock()
        mock_session_metrics = Mock()
        mock_session_metrics.input_tokens = 100
        mock_session_metrics.output_tokens = 50
        mock_session_metrics.prompt_tokens_details = {"reasoning": 20, "cached": 10}
        mock_session_metrics.completion_tokens_details = {"text": 40, "audio": 10}
        mock_session_metrics.additional_metrics = {"custom_metric": 42}
        mock_response.session_metrics = mock_session_metrics

        bridge = AgnoMetricsBridge()
        metrics = bridge._extract_agno_native_metrics(mock_response)

        # Verify detailed metrics are extracted
        assert metrics["prompt_tokens_details"] == {"reasoning": 20, "cached": 10}
        assert metrics["completion_tokens_details"] == {"text": 40, "audio": 10}
        assert metrics["additional_metrics"] == {"custom_metric": 42}

    def test_extract_agno_native_metrics_with_run_response_metrics(self):
        """Test extraction from run_response.metrics (secondary method)."""
        # Mock AGNO response with run_response.metrics - use spec to control attributes
        mock_response = Mock(spec=["run_response"])
        mock_response.run_response = Mock()
        mock_response.run_response.metrics = {
            "input_tokens": [100, 50, 25],  # List values to sum
            "output_tokens": [30, 20],
            "time": [1.2, 0.8],
            "custom_metric": ["value1", "value2"],  # Non-summable, use last value
        }

        bridge = AgnoMetricsBridge()
        metrics = bridge._extract_agno_native_metrics(mock_response)

        # Verify list aggregation
        assert metrics["input_tokens"] == 175  # 100 + 50 + 25
        assert metrics["output_tokens"] == 50   # 30 + 20
        assert metrics["time"] == 2.0          # 1.2 + 0.8
        assert metrics["custom_metric"] == "value2"  # Last value for non-summable

    def test_extract_agno_native_metrics_with_non_numeric_list(self):
        """Test extraction handles non-numeric list values."""
        # Mock response with mixed-type list values
        mock_response = Mock()
        mock_response.run_response = Mock()
        mock_response.run_response.metrics = {
            "mixed_tokens": [100, "invalid", 50],  # Mixed types
            "string_list": ["a", "b", "c"],       # Non-numeric list
        }
        del mock_response.session_metrics

        bridge = AgnoMetricsBridge()
        metrics = bridge._extract_agno_native_metrics(mock_response)

        # Should use last value for non-summable lists
        assert metrics["mixed_tokens"] == 50  # Last valid value
        assert metrics["string_list"] == "c"  # Last value

    def test_extract_agno_native_metrics_with_non_none_single_value(self):
        """Test extraction with non-None single values."""
        # Mock response to test lines 207-208: elif metric_values is not None
        mock_response = Mock()
        mock_response.run_response = Mock()
        mock_response.run_response.metrics = {
            "single_value": 42,  # Single value, not list
            "zero_value": 0,     # Test with zero which is not None
            "string_value": "test",  # String value
        }
        del mock_response.session_metrics

        bridge = AgnoMetricsBridge()
        metrics = bridge._extract_agno_native_metrics(mock_response)

        # Should extract single values directly
        assert metrics["single_value"] == 42
        assert metrics["zero_value"] == 0
        assert metrics["string_value"] == "test"

    def test_extract_agno_native_metrics_with_direct_metrics(self):
        """Test extraction from direct metrics (tertiary method)."""
        # Mock response with direct metrics dict
        mock_response = Mock()
        mock_response.metrics = {
            "input_tokens": 200,
            "output_tokens": 100,
            "custom_metric": "test_value"
        }
        del mock_response.session_metrics
        del mock_response.run_response

        bridge = AgnoMetricsBridge()
        metrics = bridge._extract_agno_native_metrics(mock_response)

        # Verify direct metrics are extracted
        assert metrics["input_tokens"] == 200
        assert metrics["output_tokens"] == 100
        assert metrics["custom_metric"] == "test_value"

    def test_extract_agno_native_metrics_with_model_information(self):
        """Test extraction of model information."""
        # Test direct model attribute
        mock_response = Mock()
        mock_response.model = "gpt-4-turbo"
        mock_response.metrics = {"input_tokens": 100}
        del mock_response.session_metrics
        del mock_response.run_response

        bridge = AgnoMetricsBridge()
        metrics = bridge._extract_agno_native_metrics(mock_response)

        assert metrics["model"] == "gpt-4-turbo"

    def test_extract_agno_native_metrics_with_run_response_model(self):
        """Test extraction of model from run_response."""
        # Test run_response model attribute
        mock_response = Mock()
        mock_response.run_response = Mock()
        mock_response.run_response.model = "claude-3-opus"
        mock_response.metrics = {"input_tokens": 100}
        del mock_response.session_metrics
        del mock_response.model

        bridge = AgnoMetricsBridge()
        metrics = bridge._extract_agno_native_metrics(mock_response)

        assert metrics["model"] == "claude-3-opus"

    def test_extract_agno_native_metrics_with_response_content(self):
        """Test extraction of response length from content."""
        # Test direct content attribute
        mock_response = Mock()
        mock_response.content = "This is a test response content"
        mock_response.metrics = {"input_tokens": 100}
        del mock_response.session_metrics
        del mock_response.run_response

        bridge = AgnoMetricsBridge()
        metrics = bridge._extract_agno_native_metrics(mock_response)

        assert metrics["response_length"] == len("This is a test response content")

    def test_extract_agno_native_metrics_with_run_response_content(self):
        """Test extraction of response length from run_response content."""
        # Test run_response content attribute
        mock_response = Mock()
        mock_response.run_response = Mock()
        mock_response.run_response.content = "Run response content"
        mock_response.metrics = {"input_tokens": 100}
        del mock_response.session_metrics
        del mock_response.content

        bridge = AgnoMetricsBridge()
        metrics = bridge._extract_agno_native_metrics(mock_response)

        assert metrics["response_length"] == len("Run response content")


class TestBasicMetricsExtraction:
    """Test basic metrics extraction for non-AGNO responses."""

    def test_extract_basic_metrics_with_content(self):
        """Test basic metrics extraction with content."""
        mock_response = Mock()
        mock_response.content = "This is basic response content"
        mock_response.model = "basic-model"

        bridge = AgnoMetricsBridge()
        metrics = bridge._extract_basic_metrics(mock_response)

        assert metrics["response_length"] == len("This is basic response content")
        assert metrics["model"] == "basic-model"

    def test_extract_basic_metrics_with_usage(self):
        """Test basic metrics extraction with usage information."""
        mock_response = Mock()
        mock_usage = Mock()
        mock_usage.input_tokens = 120
        mock_usage.output_tokens = 60
        mock_usage.total_tokens = 180
        mock_response.usage = mock_usage

        bridge = AgnoMetricsBridge()
        metrics = bridge._extract_basic_metrics(mock_response)

        assert metrics["input_tokens"] == 120
        assert metrics["output_tokens"] == 60
        assert metrics["total_tokens"] == 180

    def test_extract_basic_metrics_minimal_response(self):
        """Test basic metrics with minimal response object."""
        mock_response = Mock()
        # Remove all optional attributes
        del mock_response.content
        del mock_response.model
        del mock_response.usage

        bridge = AgnoMetricsBridge()
        metrics = bridge._extract_basic_metrics(mock_response)

        # Should return empty dict without errors
        assert metrics == {}


class TestConfigurationFiltering:
    """Test metrics filtering based on configuration."""

    def test_filter_by_config_no_config(self):
        """Test filtering without configuration returns all metrics."""
        bridge = AgnoMetricsBridge(config=None)
        bridge.config = None

        test_metrics = {
            "input_tokens": 100,
            "output_tokens": 50,
            "time": 1.5,
            "model": "gpt-4"
        }

        filtered = bridge._filter_by_config(test_metrics)
        assert filtered == test_metrics

    def test_filter_by_config_basic_metrics_always_included(self):
        """Test that basic metrics are always included."""
        config = MetricsConfig(
            collect_tokens=False,
            collect_time=False,
            collect_tools=False,
            collect_events=False,
            collect_content=False
        )
        bridge = AgnoMetricsBridge(config=config)

        test_metrics = {
            "model": "gpt-4",
            "response_length": 100,
            "input_tokens": 50,  # Should be filtered out
            "time": 1.5         # Should be filtered out
        }

        filtered = bridge._filter_by_config(test_metrics)
        assert "model" in filtered
        assert "response_length" in filtered
        assert "input_tokens" not in filtered
        assert "time" not in filtered

    def test_filter_by_config_token_metrics(self):
        """Test filtering of token metrics."""
        config = MetricsConfig(collect_tokens=True, collect_time=False)
        bridge = AgnoMetricsBridge(config=config)

        test_metrics = {
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150,
            "prompt_tokens": 80,
            "completion_tokens": 70,
            "audio_tokens": 25,
            "input_audio_tokens": 10,
            "output_audio_tokens": 15,
            "cached_tokens": 30,
            "cache_write_tokens": 5,
            "reasoning_tokens": 40,
            "prompt_tokens_details": {"reasoning": 20},
            "completion_tokens_details": {"text": 50},
            "time": 1.5  # Should be filtered out
        }

        filtered = bridge._filter_by_config(test_metrics)

        # All token metrics should be included
        token_fields = [
            "input_tokens", "output_tokens", "total_tokens", "prompt_tokens",
            "completion_tokens", "audio_tokens", "input_audio_tokens",
            "output_audio_tokens", "cached_tokens", "cache_write_tokens",
            "reasoning_tokens", "prompt_tokens_details", "completion_tokens_details"
        ]
        for field in token_fields:
            assert field in filtered

        # Time should be filtered out since collect_time=False
        assert "time" not in filtered

    def test_filter_by_config_time_metrics(self):
        """Test filtering of time metrics."""
        config = MetricsConfig(collect_time=True, collect_tokens=False)
        bridge = AgnoMetricsBridge(config=config)

        test_metrics = {
            "time": 2.5,
            "time_to_first_token": 0.8,
            "input_tokens": 100,  # Should be filtered out
        }

        filtered = bridge._filter_by_config(test_metrics)
        assert "time" in filtered
        assert "time_to_first_token" in filtered
        assert "input_tokens" not in filtered

    def test_filter_by_config_tool_metrics(self):
        """Test filtering of tool metrics."""
        config = MetricsConfig(collect_tools=True, collect_tokens=False)
        bridge = AgnoMetricsBridge(config=config)

        test_metrics = {
            "tools": ["tool1", "tool2"],
            "tool_calls": 3,
            "tool_executions": 2,
            "input_tokens": 100,  # Should be filtered out
        }

        filtered = bridge._filter_by_config(test_metrics)
        assert "tools" in filtered
        assert "tool_calls" in filtered
        assert "tool_executions" in filtered
        assert "input_tokens" not in filtered

    def test_filter_by_config_event_metrics(self):
        """Test filtering of event metrics."""
        config = MetricsConfig(collect_events=True, collect_tokens=False)
        bridge = AgnoMetricsBridge(config=config)

        test_metrics = {
            "events": ["event1", "event2"],
            "messages": ["msg1", "msg2"],
            "message_count": 2,
            "input_tokens": 100,  # Should be filtered out
        }

        filtered = bridge._filter_by_config(test_metrics)
        assert "events" in filtered
        assert "messages" in filtered
        assert "message_count" in filtered
        assert "input_tokens" not in filtered

    def test_filter_by_config_content_metrics(self):
        """Test filtering of content metrics."""
        config = MetricsConfig(collect_content=True, collect_tokens=False)
        bridge = AgnoMetricsBridge(config=config)

        test_metrics = {
            "additional_metrics": {"custom": "value"},
            "content_type": "text",
            "content_size": 1024,
            "input_tokens": 100,  # Should be filtered out
        }

        filtered = bridge._filter_by_config(test_metrics)
        assert "additional_metrics" in filtered
        assert "content_type" in filtered
        assert "content_size" in filtered
        assert "input_tokens" not in filtered


class TestExtractMetricsMainMethod:
    """Test the main extract_metrics method."""

    def test_extract_metrics_with_agno_response(self):
        """Test extract_metrics with valid AGNO response."""
        # Mock AGNO response
        mock_response = Mock()
        mock_response.session_metrics = Mock()
        mock_response.session_metrics.input_tokens = 100
        mock_response.session_metrics.output_tokens = 50

        bridge = AgnoMetricsBridge()

        with patch.object(bridge, "_is_agno_response", return_value=True) as mock_is_agno, \
             patch.object(bridge, "_extract_agno_native_metrics", return_value={"input_tokens": 100}) as mock_extract_agno:

            metrics = bridge.extract_metrics(mock_response)

            mock_is_agno.assert_called_once_with(mock_response)
            mock_extract_agno.assert_called_once_with(mock_response)
            assert metrics == {"input_tokens": 100}

    def test_extract_metrics_with_non_agno_response(self):
        """Test extract_metrics with non-AGNO response."""
        mock_response = Mock()
        mock_response.content = "Basic response"

        bridge = AgnoMetricsBridge()

        with patch.object(bridge, "_is_agno_response", return_value=False) as mock_is_agno, \
             patch.object(bridge, "_extract_basic_metrics", return_value={"response_length": 14}) as mock_extract_basic:

            metrics = bridge.extract_metrics(mock_response)

            mock_is_agno.assert_called_once_with(mock_response)
            mock_extract_basic.assert_called_once_with(mock_response)
            assert metrics == {"response_length": 14}

    def test_extract_metrics_with_yaml_overrides(self):
        """Test extract_metrics with YAML overrides."""
        mock_response = Mock()
        mock_response.session_metrics = Mock()
        mock_response.session_metrics.input_tokens = 100

        bridge = AgnoMetricsBridge()
        yaml_overrides = {"custom_field": "custom_value", "input_tokens": 200}

        with patch.object(bridge, "_is_agno_response", return_value=True), \
             patch.object(bridge, "_extract_agno_native_metrics", return_value={"input_tokens": 100}):

            metrics = bridge.extract_metrics(mock_response, yaml_overrides=yaml_overrides)

            # YAML overrides should be applied
            assert metrics["custom_field"] == "custom_value"
            assert metrics["input_tokens"] == 200  # Override should win

    def test_extract_metrics_with_config_filtering(self):
        """Test extract_metrics with configuration filtering."""
        config = MetricsConfig(collect_tokens=True, collect_time=False)
        bridge = AgnoMetricsBridge(config=config)

        mock_response = Mock()

        with patch.object(bridge, "_is_agno_response", return_value=True), \
             patch.object(bridge, "_extract_agno_native_metrics", return_value={"input_tokens": 100, "time": 1.5}), \
             patch.object(bridge, "_filter_by_config", return_value={"input_tokens": 100}) as mock_filter:

            metrics = bridge.extract_metrics(mock_response)

            mock_filter.assert_called_once_with({"input_tokens": 100, "time": 1.5})
            assert metrics == {"input_tokens": 100}

    def test_extract_metrics_error_handling(self):
        """Test extract_metrics error handling."""
        mock_response = Mock()

        bridge = AgnoMetricsBridge()

        # Mock _is_agno_response to raise an exception
        with patch.object(bridge, "_is_agno_response", side_effect=Exception("Test error")):
            metrics = bridge.extract_metrics(mock_response)

            # Should return empty dict on error
            assert metrics == {}

    def test_extract_metrics_logging_agno_response(self):
        """Test extract_metrics logs correct message for AGNO response."""
        mock_response = Mock()

        bridge = AgnoMetricsBridge()

        with patch.object(bridge, "_is_agno_response", return_value=True), \
             patch.object(bridge, "_extract_agno_native_metrics", return_value={"input_tokens": 100, "output_tokens": 50}), \
             patch("lib.metrics.agno_metrics_bridge.logger") as mock_logger:

            bridge.extract_metrics(mock_response)

            # Should log AGNO native metrics message
            mock_logger.debug.assert_called_with("🔧 Extracted 2 AGNO native metrics fields")

    def test_extract_metrics_logging_basic_response(self):
        """Test extract_metrics logs correct message for basic response."""
        mock_response = Mock()

        bridge = AgnoMetricsBridge()

        with patch.object(bridge, "_is_agno_response", return_value=False), \
             patch.object(bridge, "_extract_basic_metrics", return_value={"response_length": 100}), \
             patch("lib.metrics.agno_metrics_bridge.logger") as mock_logger:

            bridge.extract_metrics(mock_response)

            # Should log basic metrics fallback message
            mock_logger.debug.assert_called_with("🔧 Using basic metrics fallback - 1 fields")


class TestGetMetricsInfo:
    """Test get_metrics_info method."""

    def test_get_metrics_info_structure(self):
        """Test get_metrics_info returns correct structure."""
        bridge = AgnoMetricsBridge()
        info = bridge.get_metrics_info()

        # Verify top-level structure
        assert "bridge_version" in info
        assert "metrics_source" in info
        assert "capabilities" in info
        assert "advantages_over_manual" in info

        # Verify version and source
        assert info["bridge_version"] == "1.0.0"
        assert info["metrics_source"] == "agno_native"

    def test_get_metrics_info_capabilities(self):
        """Test get_metrics_info capabilities section."""
        bridge = AgnoMetricsBridge()
        info = bridge.get_metrics_info()

        capabilities = info["capabilities"]

        # Verify capabilities structure
        assert "token_metrics" in capabilities
        assert "timing_metrics" in capabilities
        assert "detailed_metrics" in capabilities
        assert "additional_metrics" in capabilities
        assert "configuration_filtering" in capabilities
        assert "yaml_overrides" in capabilities
        assert "fallback_support" in capabilities

        # Verify specific capabilities
        assert capabilities["configuration_filtering"] is True
        assert capabilities["yaml_overrides"] is True
        assert capabilities["fallback_support"] is True

    def test_get_metrics_info_token_metrics_list(self):
        """Test get_metrics_info token metrics list."""
        bridge = AgnoMetricsBridge()
        info = bridge.get_metrics_info()

        token_metrics = info["capabilities"]["token_metrics"]

        # Verify comprehensive token metrics support
        expected_tokens = [
            "input_tokens", "output_tokens", "total_tokens", "prompt_tokens",
            "completion_tokens", "audio_tokens", "input_audio_tokens",
            "output_audio_tokens", "cached_tokens", "cache_write_tokens",
            "reasoning_tokens"
        ]

        for token_type in expected_tokens:
            assert token_type in token_metrics

    def test_get_metrics_info_advantages(self):
        """Test get_metrics_info advantages section."""
        bridge = AgnoMetricsBridge()
        info = bridge.get_metrics_info()

        advantages = info["advantages_over_manual"]

        # Verify advantages list is comprehensive
        assert isinstance(advantages, list)
        assert len(advantages) > 5  # Should have multiple advantages

        # Verify key advantages are mentioned
        advantages_text = " ".join(advantages).lower()
        assert "comprehensive" in advantages_text
        assert "token" in advantages_text
        assert "timing" in advantages_text
        assert "automatic" in advantages_text


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling."""

    def test_extract_metrics_with_none_response(self):
        """Test extract_metrics handles None response."""
        bridge = AgnoMetricsBridge()
        metrics = bridge.extract_metrics(None)

        # Should handle gracefully and return empty dict
        assert metrics == {}

    def test_extract_agno_native_metrics_missing_attributes(self):
        """Test extraction handles missing attributes gracefully."""
        # Create a simple mock where getattr returns defaults for missing attributes
        class MockSessionMetrics:
            def __init__(self):
                self.input_tokens = 100
                # All other attributes will raise AttributeError

        class MockResponse:
            def __init__(self):
                self.session_metrics = MockSessionMetrics()

        mock_response = MockResponse()
        bridge = AgnoMetricsBridge()
        metrics = bridge._extract_agno_native_metrics(mock_response)

        # Should extract available attributes and use 0 for missing ones
        assert metrics["input_tokens"] == 100
        assert metrics["output_tokens"] == 0  # Default value from getattr
        assert metrics["total_tokens"] == 0   # Default value from getattr

    def test_extract_agno_native_metrics_with_empty_run_response_metrics(self):
        """Test extraction with empty run_response metrics."""
        mock_response = Mock()
        mock_response.run_response = Mock()
        mock_response.run_response.metrics = {}  # Empty dict
        del mock_response.session_metrics

        bridge = AgnoMetricsBridge()
        metrics = bridge._extract_agno_native_metrics(mock_response)

        # Should handle empty metrics dict
        assert isinstance(metrics, dict)

    def test_filter_by_config_with_missing_metrics(self):
        """Test filtering handles missing metrics gracefully."""
        config = MetricsConfig(collect_tokens=True)
        bridge = AgnoMetricsBridge(config=config)

        # Metrics dict missing expected fields
        test_metrics = {"unexpected_field": "value"}

        filtered = bridge._filter_by_config(test_metrics)

        # Should not crash and should handle gracefully
        assert isinstance(filtered, dict)
        assert "unexpected_field" not in filtered  # Should be filtered out


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_full_agno_extraction_workflow(self):
        """Test complete workflow with realistic AGNO response."""
        # Create realistic AGNO response mock
        mock_response = Mock()
        mock_session_metrics = Mock()
        mock_session_metrics.input_tokens = 150
        mock_session_metrics.output_tokens = 75
        mock_session_metrics.total_tokens = 225
        mock_session_metrics.time = 2.3
        mock_session_metrics.time_to_first_token = 0.5
        mock_response.session_metrics = mock_session_metrics
        mock_response.model = "gpt-4"
        mock_response.content = "This is a comprehensive test response"

        # Test with full configuration
        config = MetricsConfig(
            collect_tokens=True,
            collect_time=True,
            collect_tools=False,
            collect_events=False,
            collect_content=True
        )
        bridge = AgnoMetricsBridge(config=config)

        # Test extraction with YAML overrides
        yaml_overrides = {"experiment_id": "test_123", "custom_metric": 42}

        metrics = bridge.extract_metrics(mock_response, yaml_overrides=yaml_overrides)

        # Verify comprehensive metrics extraction
        assert metrics["input_tokens"] == 150
        assert metrics["output_tokens"] == 75
        assert metrics["total_tokens"] == 225
        assert metrics["time"] == 2.3
        assert metrics["time_to_first_token"] == 0.5
        assert metrics["model"] == "gpt-4"
        assert metrics["response_length"] == len("This is a comprehensive test response")
        assert metrics["experiment_id"] == "test_123"
        assert metrics["custom_metric"] == 42

    def test_basic_response_fallback_workflow(self):
        """Test complete workflow with basic non-AGNO response."""
        # Create basic response mock without AGNO attributes
        mock_response = Mock(spec=["content", "model", "usage"])
        mock_response.content = "Basic response content"
        mock_response.model = "basic-model"
        mock_usage = Mock()
        mock_usage.input_tokens = 80
        mock_usage.output_tokens = 40
        mock_response.usage = mock_usage

        config = MetricsConfig(collect_tokens=True)
        bridge = AgnoMetricsBridge(config=config)

        # Ensure it's not detected as AGNO response
        assert bridge._is_agno_response(mock_response) is False

        metrics = bridge.extract_metrics(mock_response)

        # Verify basic metrics extraction
        assert metrics["response_length"] == len("Basic response content")
        assert metrics["model"] == "basic-model"
        assert metrics["input_tokens"] == 80
        assert metrics["output_tokens"] == 40
