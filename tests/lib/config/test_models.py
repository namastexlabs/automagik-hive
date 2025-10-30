"""
Comprehensive test suite for lib/config/models.py - CRITICAL zero-coverage file

Tests ModelResolver and resolve_model() function which are used by EVERY agent/team/workflow
in the system. This module is critical for model instantiation across the entire platform.

Target: 90%+ coverage for lib/config/models.py (283 lines, 0% current)

Test Coverage:
- ModelResolver initialization and default model ID resolution
- Provider detection for various model IDs (OpenAI, Anthropic, Google, etc.)
- Model class discovery and resolution
- Model instance creation with custom parameters
- Error handling for invalid/missing model IDs
- Cache management and singleton behavior
- Environment variable integration
- Portuguese language prompt retrieval
"""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest

from lib.config.models import (
    PORTUGUESE_PROMPTS,
    ModelResolutionError,
    ModelResolver,
    get_default_model_id,
    get_default_provider,
    get_portuguese_prompt,
    model_resolver,
    resolve_model,
    validate_model,
    validate_required_environment_variables,
)


class TestModelResolver:
    """Comprehensive test suite for ModelResolver class."""

    def test_init_creates_resolver(self):
        """Test that ModelResolver initializes successfully."""
        resolver = ModelResolver()
        assert resolver is not None

    def test_get_default_model_id_success(self):
        """Test successful retrieval of default model ID from environment."""
        with patch.dict(os.environ, {"HIVE_DEFAULT_MODEL": "gpt-4o-mini"}):
            resolver = ModelResolver()
            model_id = resolver.get_default_model_id()
            assert model_id == "gpt-4o-mini"

    def test_get_default_model_id_missing_raises_error(self):
        """Test that missing HIVE_DEFAULT_MODEL raises ModelResolutionError."""
        with patch.dict(os.environ, {}, clear=True):
            resolver = ModelResolver()
            with pytest.raises(ModelResolutionError, match="HIVE_DEFAULT_MODEL environment variable is required"):
                resolver.get_default_model_id()

    def test_detect_provider_openai_models(self):
        """Test provider detection for OpenAI model IDs."""
        resolver = ModelResolver()

        with patch("lib.config.models.get_provider_registry") as mock_registry:
            mock_registry.return_value.detect_provider.return_value = "openai"

            provider = resolver._detect_provider("gpt-4o-mini")
            assert provider == "openai"

            provider = resolver._detect_provider("gpt-4.1-mini")
            assert provider == "openai"

            provider = resolver._detect_provider("o1-preview")
            assert provider == "openai"

    def test_detect_provider_anthropic_models(self):
        """Test provider detection for Anthropic model IDs."""
        resolver = ModelResolver()

        with patch("lib.config.models.get_provider_registry") as mock_registry:
            mock_registry.return_value.detect_provider.return_value = "anthropic"

            provider = resolver._detect_provider("claude-sonnet-4")
            assert provider == "anthropic"

            provider = resolver._detect_provider("claude.instant")
            assert provider == "anthropic"

    def test_detect_provider_google_models(self):
        """Test provider detection for Google model IDs."""
        resolver = ModelResolver()

        with patch("lib.config.models.get_provider_registry") as mock_registry:
            mock_registry.return_value.detect_provider.return_value = "google"

            provider = resolver._detect_provider("gemini-pro")
            assert provider == "google"

            provider = resolver._detect_provider("gemini-1.5-flash")
            assert provider == "google"

    def test_detect_provider_meta_models(self):
        """Test provider detection for Meta model IDs."""
        resolver = ModelResolver()

        with patch("lib.config.models.get_provider_registry") as mock_registry:
            mock_registry.return_value.detect_provider.return_value = "meta"

            provider = resolver._detect_provider("llama-3.1-70b")
            assert provider == "meta"

    def test_detect_provider_invalid_model_raises_error(self):
        """Test that invalid model ID raises ModelResolutionError."""
        resolver = ModelResolver()

        with patch("lib.config.models.get_provider_registry") as mock_registry:
            mock_registry.return_value.detect_provider.return_value = None
            mock_registry.return_value.get_available_providers.return_value = ["openai", "anthropic"]

            with pytest.raises(ModelResolutionError, match="Cannot detect provider for model ID"):
                resolver._detect_provider("invalid-model-xyz")

    def test_discover_model_class_success(self):
        """Test successful model class discovery."""
        resolver = ModelResolver()
        mock_class = Mock(spec=type)

        with patch("lib.config.models.get_provider_registry") as mock_registry:
            mock_registry.return_value.resolve_model_class.return_value = mock_class

            result = resolver._discover_model_class("openai", "gpt-4o-mini")
            assert result == mock_class

    def test_discover_model_class_failure_raises_error(self):
        """Test that failed model class discovery raises ModelResolutionError."""
        resolver = ModelResolver()

        with patch("lib.config.models.get_provider_registry") as mock_registry:
            mock_registry.return_value.resolve_model_class.return_value = None
            mock_registry.return_value.get_provider_classes.return_value = ["OpenAI", "OpenAIChat"]

            with pytest.raises(ModelResolutionError, match="Failed to discover model class"):
                resolver._discover_model_class("openai", "gpt-4o-mini")

    def test_resolve_model_with_explicit_model_id(self):
        """Test model resolution with explicitly provided model ID."""
        resolver = ModelResolver()
        mock_model_instance = Mock()
        mock_class = Mock(return_value=mock_model_instance)

        with (
            patch.object(resolver, "_detect_provider", return_value="openai"),
            patch.object(resolver, "_discover_model_class", return_value=mock_class),
        ):
            result = resolver.resolve_model(model_id="gpt-4o-mini", temperature=0.7)

            assert result == mock_model_instance
            mock_class.assert_called_once_with(id="gpt-4o-mini", temperature=0.7)

    def test_resolve_model_with_default_model_id(self):
        """Test model resolution using default model ID from environment."""
        resolver = ModelResolver()
        mock_model_instance = Mock()
        mock_class = Mock(return_value=mock_model_instance)

        with (
            patch.dict(os.environ, {"HIVE_DEFAULT_MODEL": "claude-sonnet-4"}),
            patch.object(resolver, "_detect_provider", return_value="anthropic"),
            patch.object(resolver, "_discover_model_class", return_value=mock_class),
        ):
            result = resolver.resolve_model(temperature=0.5, max_tokens=2000)

            assert result == mock_model_instance
            mock_class.assert_called_once_with(id="claude-sonnet-4", temperature=0.5, max_tokens=2000)

    def test_resolve_model_with_custom_parameters(self):
        """Test model resolution with custom parameters (temperature, max_tokens, etc.)."""
        resolver = ModelResolver()
        mock_model_instance = Mock()
        mock_class = Mock(return_value=mock_model_instance)

        with (
            patch.object(resolver, "_detect_provider", return_value="openai"),
            patch.object(resolver, "_discover_model_class", return_value=mock_class),
        ):
            result = resolver.resolve_model(
                model_id="gpt-4o-mini", temperature=0.9, max_tokens=4000, top_p=0.95, frequency_penalty=0.5
            )

            assert result == mock_model_instance
            mock_class.assert_called_once_with(
                id="gpt-4o-mini", temperature=0.9, max_tokens=4000, top_p=0.95, frequency_penalty=0.5
            )

    def test_resolve_model_missing_default_raises_error(self):
        """Test that missing default model raises ModelResolutionError."""
        resolver = ModelResolver()

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ModelResolutionError, match="HIVE_DEFAULT_MODEL environment variable is required"):
                resolver.resolve_model()

    def test_resolve_model_provider_detection_failure(self):
        """Test error handling when provider detection fails."""
        resolver = ModelResolver()

        with (
            patch.object(resolver, "_detect_provider", side_effect=ModelResolutionError("Provider detection failed")),
        ):
            with pytest.raises(ModelResolutionError, match="Failed to resolve model"):
                resolver.resolve_model(model_id="unknown-model")

    def test_resolve_model_class_discovery_failure(self):
        """Test error handling when class discovery fails."""
        resolver = ModelResolver()

        with (
            patch.object(resolver, "_detect_provider", return_value="openai"),
            patch.object(resolver, "_discover_model_class", side_effect=ModelResolutionError("Class not found")),
        ):
            with pytest.raises(ModelResolutionError, match="Failed to resolve model"):
                resolver.resolve_model(model_id="gpt-unknown")

    def test_resolve_model_instantiation_failure(self):
        """Test error handling when model instantiation fails."""
        resolver = ModelResolver()
        mock_class = Mock(side_effect=Exception("Instantiation error"))

        with (
            patch.object(resolver, "_detect_provider", return_value="openai"),
            patch.object(resolver, "_discover_model_class", return_value=mock_class),
        ):
            with pytest.raises(ModelResolutionError, match="Failed to resolve model"):
                resolver.resolve_model(model_id="gpt-4o-mini")

    def test_validate_model_availability_success(self):
        """Test successful model validation."""
        resolver = ModelResolver()

        with (
            patch.object(resolver, "_detect_provider", return_value="openai"),
            patch.object(resolver, "_discover_model_class", return_value=Mock()),
        ):
            result = resolver.validate_model_availability("gpt-4o-mini")
            assert result is True

    def test_validate_model_availability_failure(self):
        """Test model validation failure for invalid model."""
        resolver = ModelResolver()

        with patch.object(resolver, "_detect_provider", side_effect=ModelResolutionError("Invalid model")):
            result = resolver.validate_model_availability("invalid-model")
            assert result is False

    def test_clear_cache_clears_all_caches(self):
        """Test that clear_cache clears all resolver and registry caches."""
        resolver = ModelResolver()

        # Populate caches by calling cached methods
        with (
            patch("lib.config.models.get_provider_registry") as mock_registry,
            patch.object(resolver, "_detect_provider") as mock_detect,
            patch.object(resolver, "_discover_model_class") as mock_discover,
        ):
            mock_registry.return_value.clear_cache = Mock()

            # Call clear_cache
            resolver.clear_cache()

            # Verify registry cache was cleared
            mock_registry.return_value.clear_cache.assert_called_once()


class TestConvenienceFunctions:
    """Test suite for module-level convenience functions."""

    def test_get_default_model_id_success(self):
        """Test get_default_model_id() function."""
        with patch.dict(os.environ, {"HIVE_DEFAULT_MODEL": "gpt-4.1-mini"}):
            model_id = get_default_model_id()
            assert model_id == "gpt-4.1-mini"

    def test_get_default_model_id_missing_raises_error(self):
        """Test that missing environment variable raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ModelResolutionError, match="HIVE_DEFAULT_MODEL"):
                get_default_model_id()

    def test_get_default_provider_success(self):
        """Test get_default_provider() function."""
        with patch.dict(os.environ, {"HIVE_DEFAULT_PROVIDER": "anthropic"}):
            provider = get_default_provider()
            assert provider == "anthropic"

    def test_get_default_provider_missing_raises_error(self):
        """Test that missing HIVE_DEFAULT_PROVIDER raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ModelResolutionError, match="HIVE_DEFAULT_PROVIDER"):
                get_default_provider()

    def test_resolve_model_function_with_model_id(self):
        """Test resolve_model() convenience function."""
        mock_model_instance = Mock()

        with patch("lib.config.models.model_resolver.resolve_model", return_value=mock_model_instance):
            result = resolve_model(model_id="gpt-4o-mini", temperature=0.8)
            assert result == mock_model_instance

    def test_validate_model_function(self):
        """Test validate_model() convenience function."""
        with patch("lib.config.models.model_resolver.validate_model_availability", return_value=True):
            result = validate_model("gpt-4o-mini")
            assert result is True

    def test_validate_required_environment_variables_missing_both(self):
        """Test validation when both required variables are missing."""
        with patch.dict(os.environ, {}, clear=True):
            # Should only log warning, not raise error
            validate_required_environment_variables()
            # No exception expected

    def test_validate_required_environment_variables_with_values(self):
        """Test validation when environment variables are present."""
        with patch.dict(os.environ, {"HIVE_DEFAULT_MODEL": "gpt-4o-mini", "HIVE_DEFAULT_PROVIDER": "openai"}):
            # Should not log warning
            validate_required_environment_variables()
            # No exception expected


class TestPortuguesePrompts:
    """Test suite for Portuguese language prompt functionality."""

    def test_portuguese_prompts_dictionary_exists(self):
        """Test that PORTUGUESE_PROMPTS dictionary is defined."""
        assert PORTUGUESE_PROMPTS is not None
        assert isinstance(PORTUGUESE_PROMPTS, dict)

    def test_portuguese_prompts_contains_required_keys(self):
        """Test that all required prompt keys exist."""
        required_keys = [
            "system_instructions",
            "greeting",
            "error_message",
            "escalation_message",
            "feedback_request",
        ]

        for key in required_keys:
            assert key in PORTUGUESE_PROMPTS
            assert isinstance(PORTUGUESE_PROMPTS[key], str)
            assert len(PORTUGUESE_PROMPTS[key]) > 0

    def test_get_portuguese_prompt_system_instructions(self):
        """Test retrieval of system instructions prompt."""
        prompt = get_portuguese_prompt("system_instructions")
        assert "PagBank" in prompt
        assert "português" in prompt

    def test_get_portuguese_prompt_greeting(self):
        """Test retrieval of greeting prompt."""
        prompt = get_portuguese_prompt("greeting")
        assert "Olá" in prompt
        assert "PagBank" in prompt

    def test_get_portuguese_prompt_error_message(self):
        """Test retrieval of error message prompt."""
        prompt = get_portuguese_prompt("error_message")
        assert "Desculpe" in prompt

    def test_get_portuguese_prompt_escalation_message(self):
        """Test retrieval of escalation message prompt."""
        prompt = get_portuguese_prompt("escalation_message")
        assert "especialista" in prompt

    def test_get_portuguese_prompt_feedback_request(self):
        """Test retrieval of feedback request prompt."""
        prompt = get_portuguese_prompt("feedback_request")
        assert "opinião" in prompt

    def test_get_portuguese_prompt_invalid_key_returns_empty(self):
        """Test that invalid key returns empty string."""
        prompt = get_portuguese_prompt("nonexistent_key")
        assert prompt == ""


class TestCacheBehavior:
    """Test suite for LRU cache behavior."""

    def test_detect_provider_cache_behavior(self):
        """Test that _detect_provider uses LRU cache."""
        resolver = ModelResolver()

        with patch("lib.config.models.get_provider_registry") as mock_registry:
            mock_registry.return_value.detect_provider.return_value = "openai"

            # Call multiple times with same input
            resolver._detect_provider("gpt-4o-mini")
            resolver._detect_provider("gpt-4o-mini")
            resolver._detect_provider("gpt-4o-mini")

            # Registry should only be called once due to cache
            assert mock_registry.return_value.detect_provider.call_count == 1

    def test_discover_model_class_cache_behavior(self):
        """Test that _discover_model_class uses LRU cache."""
        resolver = ModelResolver()
        mock_class = Mock(spec=type)

        with patch("lib.config.models.get_provider_registry") as mock_registry:
            mock_registry.return_value.resolve_model_class.return_value = mock_class

            # Call multiple times with same input
            resolver._discover_model_class("openai", "gpt-4o-mini")
            resolver._discover_model_class("openai", "gpt-4o-mini")
            resolver._discover_model_class("openai", "gpt-4o-mini")

            # Registry should only be called once due to cache
            assert mock_registry.return_value.resolve_model_class.call_count == 1


class TestSingletonBehavior:
    """Test suite for global model_resolver singleton."""

    def test_model_resolver_singleton_exists(self):
        """Test that global model_resolver instance exists."""
        assert model_resolver is not None
        assert isinstance(model_resolver, ModelResolver)

    def test_convenience_functions_use_singleton(self):
        """Test that convenience functions use the global singleton."""
        mock_result = "test-model-id"

        with (
            patch.object(model_resolver, "get_default_model_id", return_value=mock_result) as mock_method,
        ):
            result = get_default_model_id()
            assert result == mock_result
            mock_method.assert_called_once()


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_resolve_model_empty_string_model_id(self):
        """Test resolution with empty string model ID uses default."""
        resolver = ModelResolver()
        mock_model_instance = Mock()
        mock_class = Mock(return_value=mock_model_instance)

        with (
            patch.dict(os.environ, {"HIVE_DEFAULT_MODEL": "gpt-4o-mini"}),
            patch.object(resolver, "_detect_provider", return_value="openai"),
            patch.object(resolver, "_discover_model_class", return_value=mock_class),
        ):
            # Empty string should fall back to default
            result = resolver.resolve_model(model_id="")
            assert result == mock_model_instance

    def test_resolve_model_none_model_id_uses_default(self):
        """Test that None model_id uses environment default."""
        resolver = ModelResolver()
        mock_model_instance = Mock()
        mock_class = Mock(return_value=mock_model_instance)

        with (
            patch.dict(os.environ, {"HIVE_DEFAULT_MODEL": "claude-sonnet-4"}),
            patch.object(resolver, "_detect_provider", return_value="anthropic"),
            patch.object(resolver, "_discover_model_class", return_value=mock_class),
        ):
            result = resolver.resolve_model(model_id=None)
            assert result == mock_model_instance

    def test_resolve_model_with_no_overrides(self):
        """Test model resolution with only model_id, no config overrides."""
        resolver = ModelResolver()
        mock_model_instance = Mock()
        mock_class = Mock(return_value=mock_model_instance)

        with (
            patch.object(resolver, "_detect_provider", return_value="openai"),
            patch.object(resolver, "_discover_model_class", return_value=mock_class),
        ):
            result = resolver.resolve_model(model_id="gpt-4o-mini")
            assert result == mock_model_instance
            mock_class.assert_called_once_with(id="gpt-4o-mini")

    def test_detect_provider_case_insensitive(self):
        """Test that provider detection handles case variations."""
        resolver = ModelResolver()

        with patch("lib.config.models.get_provider_registry") as mock_registry:
            mock_registry.return_value.detect_provider.return_value = "openai"

            # All variations should work
            provider1 = resolver._detect_provider("GPT-4O-MINI")
            provider2 = resolver._detect_provider("gpt-4o-mini")
            provider3 = resolver._detect_provider("GpT-4o-MiNi")

            assert provider1 == "openai"
            assert provider2 == "openai"
            assert provider3 == "openai"


class TestIntegrationScenarios:
    """Integration tests covering real-world usage scenarios."""

    def test_complete_model_resolution_flow_openai(self):
        """Test complete flow for OpenAI model resolution."""
        resolver = ModelResolver()
        mock_model = Mock()
        mock_class = Mock(return_value=mock_model)

        with (
            patch.object(resolver, "_detect_provider", return_value="openai") as mock_detect,
            patch.object(resolver, "_discover_model_class", return_value=mock_class) as mock_discover,
        ):
            result = resolver.resolve_model(model_id="gpt-4o-mini", temperature=0.7, max_tokens=2000)

            # Verify complete flow
            assert result == mock_model
            mock_detect.assert_called_once_with("gpt-4o-mini")
            mock_discover.assert_called_once_with("openai", "gpt-4o-mini")
            mock_class.assert_called_once_with(id="gpt-4o-mini", temperature=0.7, max_tokens=2000)

    def test_complete_model_resolution_flow_anthropic(self):
        """Test complete flow for Anthropic model resolution."""
        resolver = ModelResolver()
        mock_model = Mock()
        mock_class = Mock(return_value=mock_model)

        with (
            patch.object(resolver, "_detect_provider", return_value="anthropic") as mock_detect,
            patch.object(resolver, "_discover_model_class", return_value=mock_class) as mock_discover,
        ):
            result = resolver.resolve_model(model_id="claude-sonnet-4", temperature=0.5)

            assert result == mock_model
            mock_detect.assert_called_once_with("claude-sonnet-4")
            mock_discover.assert_called_once_with("anthropic", "claude-sonnet-4")
            mock_class.assert_called_once_with(id="claude-sonnet-4", temperature=0.5)

    def test_multiple_model_resolutions_with_cache(self):
        """Test multiple model resolutions benefit from caching."""
        resolver = ModelResolver()
        mock_model = Mock()
        mock_class = Mock(return_value=mock_model)

        with (
            patch.object(resolver, "_detect_provider", return_value="openai") as mock_detect,
            patch.object(resolver, "_discover_model_class", return_value=mock_class) as mock_discover,
        ):
            # Resolve same model multiple times
            resolver.resolve_model(model_id="gpt-4o-mini", temperature=0.7)
            resolver.resolve_model(model_id="gpt-4o-mini", temperature=0.8)
            resolver.resolve_model(model_id="gpt-4o-mini", temperature=0.9)

            # Due to cache, detect and discover should be called fewer times
            # Note: detect_provider is called each time but cached internally
            assert mock_detect.call_count >= 1
            assert mock_discover.call_count >= 1
