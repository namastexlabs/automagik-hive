"""
Comprehensive test suite for lib/config/models.py - Model Resolution System

This test suite targets 50+ uncovered lines to achieve 0.7% test coverage boost.
Focuses on:
- Model resolution with dynamic provider discovery
- Environment variable handling and validation
- Error scenarios and edge cases
- Portuguese language configurations
- Cache behavior and performance
- Integration with provider registry
"""

import os
from unittest.mock import Mock, patch

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


class TestModelResolutionError:
    """Test the ModelResolutionError exception class."""

    def test_model_resolution_error_creation(self):
        """Test ModelResolutionError can be created and raised."""
        error = ModelResolutionError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_model_resolution_error_inheritance(self):
        """Test ModelResolutionError inherits from Exception."""
        error = ModelResolutionError("Test")
        assert issubclass(type(error), Exception)

    def test_model_resolution_error_raise_and_catch(self):
        """Test ModelResolutionError can be raised and caught."""
        with pytest.raises(ModelResolutionError) as exc_info:
            raise ModelResolutionError("Custom error message")
        assert "Custom error message" in str(exc_info.value)


class TestModelResolverInitialization:
    """Test ModelResolver initialization and basic properties."""

    def test_model_resolver_initialization(self):
        """Test ModelResolver can be initialized successfully."""
        resolver = ModelResolver()
        assert resolver is not None
        assert hasattr(resolver, "get_default_model_id")
        assert hasattr(resolver, "_detect_provider")
        assert hasattr(resolver, "_discover_model_class")
        assert hasattr(resolver, "resolve_model")

    def test_global_model_resolver_exists(self):
        """Test global model_resolver instance exists and is correct type."""
        assert model_resolver is not None
        assert isinstance(model_resolver, ModelResolver)


class TestDefaultModelIdResolution:
    """Test default model ID resolution from environment variables."""

    def test_get_default_model_id_success(self):
        """Test successful default model ID retrieval from environment."""
        with patch.dict(os.environ, {"HIVE_DEFAULT_MODEL": "gpt-4o-mini"}):
            resolver = ModelResolver()
            model_id = resolver.get_default_model_id()
            assert model_id == "gpt-4o-mini"

    def test_get_default_model_id_missing_env_var(self):
        """Test ModelResolutionError when HIVE_DEFAULT_MODEL is not set."""
        with patch.dict(os.environ, {}, clear=True):
            resolver = ModelResolver()
            with pytest.raises(ModelResolutionError) as exc_info:
                resolver.get_default_model_id()

            error_msg = str(exc_info.value)
            assert "HIVE_DEFAULT_MODEL environment variable is required" in error_msg
            assert "Example: export HIVE_DEFAULT_MODEL=gpt-4o-mini" in error_msg

    def test_get_default_model_id_empty_env_var(self):
        """Test ModelResolutionError when HIVE_DEFAULT_MODEL is empty."""
        with patch.dict(os.environ, {"HIVE_DEFAULT_MODEL": ""}):
            resolver = ModelResolver()
            with pytest.raises(ModelResolutionError) as exc_info:
                resolver.get_default_model_id()

            assert "HIVE_DEFAULT_MODEL environment variable is required" in str(
                exc_info.value
            )


class TestProviderDetection:
    """Test provider detection using dynamic registry."""

    def test_detect_provider_success(self):
        """Test successful provider detection."""
        resolver = ModelResolver()

        # Mock the provider registry
        mock_registry = Mock()
        mock_registry.detect_provider.return_value = "openai"

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            provider = resolver._detect_provider("gpt-4o-mini")
            assert provider == "openai"
            mock_registry.detect_provider.assert_called_once_with("gpt-4o-mini")

    def test_detect_provider_cache_behavior(self):
        """Test provider detection uses caching."""
        resolver = ModelResolver()

        mock_registry = Mock()
        mock_registry.detect_provider.return_value = "openai"

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            # Call twice
            provider1 = resolver._detect_provider("gpt-4o-mini")
            provider2 = resolver._detect_provider("gpt-4o-mini")

            assert provider1 == provider2 == "openai"
            # Should only call registry once due to caching
            mock_registry.detect_provider.assert_called_once_with("gpt-4o-mini")

    def test_detect_provider_failure_raises_error(self):
        """Test provider detection failure raises ModelResolutionError."""
        resolver = ModelResolver()

        mock_registry = Mock()
        mock_registry.detect_provider.return_value = None
        mock_registry.get_available_providers.return_value = {
            "openai",
            "anthropic",
            "google",
        }

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            with pytest.raises(ModelResolutionError) as exc_info:
                resolver._detect_provider("unknown-model")

            # Check error message content
            error_msg = str(exc_info.value)
            assert "Cannot detect provider for model ID 'unknown-model'" in error_msg
            assert "Available providers: ['anthropic', 'google', 'openai']" in error_msg


class TestModelClassDiscovery:
    """Test dynamic model class discovery."""

    def test_discover_model_class_success(self):
        """Test successful model class discovery."""
        resolver = ModelResolver()

        mock_registry = Mock()
        mock_class = Mock()
        mock_class.__name__ = "OpenAIChat"
        mock_registry.resolve_model_class.return_value = mock_class

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            discovered_class = resolver._discover_model_class("openai", "gpt-4o-mini")
            assert discovered_class == mock_class
            mock_registry.resolve_model_class.assert_called_once_with(
                "openai", "gpt-4o-mini"
            )

    def test_discover_model_class_cache_behavior(self):
        """Test model class discovery uses caching."""
        resolver = ModelResolver()

        mock_registry = Mock()
        mock_class = Mock()
        mock_class.__name__ = "Claude"
        mock_registry.resolve_model_class.return_value = mock_class

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            # Call twice
            class1 = resolver._discover_model_class("anthropic", "claude-3-sonnet")
            class2 = resolver._discover_model_class("anthropic", "claude-3-sonnet")

            assert class1 == class2 == mock_class
            # Should only call registry once due to caching
            mock_registry.resolve_model_class.assert_called_once_with(
                "anthropic", "claude-3-sonnet"
            )

    def test_discover_model_class_failure_raises_error(self):
        """Test model class discovery failure raises ModelResolutionError."""
        resolver = ModelResolver()

        mock_registry = Mock()
        mock_registry.resolve_model_class.return_value = None
        mock_registry.get_provider_classes.return_value = ["OpenAIChat", "OpenAI"]

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            with pytest.raises(ModelResolutionError) as exc_info:
                resolver._discover_model_class("openai", "gpt-4o-mini")

            # Check error message content
            error_msg = str(exc_info.value)
            assert "Failed to discover model class for provider 'openai'" in error_msg
            assert "Available classes: ['OpenAIChat', 'OpenAI']" in error_msg


class TestModelResolution:
    """Test complete model resolution workflow."""

    def test_resolve_model_with_explicit_model_id(self):
        """Test model resolution with explicitly provided model ID."""
        resolver = ModelResolver()

        # Mock dependencies
        mock_registry = Mock()
        mock_class = Mock()
        mock_instance = Mock()

        mock_registry.detect_provider.return_value = "openai"
        mock_registry.resolve_model_class.return_value = mock_class
        mock_class.return_value = mock_instance
        mock_class.__name__ = "MockModelClass"

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            result = resolver.resolve_model("gpt-4o-mini", temperature=0.7)

            assert result == mock_instance
            mock_class.assert_called_once_with(id="gpt-4o-mini", temperature=0.7)

    def test_resolve_model_with_default_model_id(self):
        """Test model resolution using default model ID from environment."""
        resolver = ModelResolver()

        # Mock dependencies
        mock_registry = Mock()
        mock_class = Mock()
        mock_instance = Mock()

        mock_registry.detect_provider.return_value = "anthropic"
        mock_registry.resolve_model_class.return_value = mock_class
        mock_class.return_value = mock_instance
        mock_class.__name__ = "MockClaudeClass"

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            with patch.dict(os.environ, {"HIVE_DEFAULT_MODEL": "claude-3-sonnet"}):
                result = resolver.resolve_model(max_tokens=1000)

                assert result == mock_instance
                mock_class.assert_called_once_with(
                    id="claude-3-sonnet", max_tokens=1000
                )

    def test_resolve_model_provider_detection_failure(self):
        """Test model resolution failure due to provider detection error."""
        resolver = ModelResolver()

        mock_registry = Mock()
        mock_registry.detect_provider.side_effect = ModelResolutionError(
            "Provider detection failed"
        )

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            with pytest.raises(ModelResolutionError) as exc_info:
                resolver.resolve_model("unknown-model")

            assert "Failed to resolve model 'unknown-model'" in str(exc_info.value)

    def test_resolve_model_class_discovery_failure(self):
        """Test model resolution failure due to class discovery error."""
        resolver = ModelResolver()

        mock_registry = Mock()
        mock_registry.detect_provider.return_value = "openai"
        mock_registry.resolve_model_class.side_effect = ModelResolutionError(
            "Class discovery failed"
        )

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            with pytest.raises(ModelResolutionError) as exc_info:
                resolver.resolve_model("gpt-4o-mini")

            assert "Failed to resolve model 'gpt-4o-mini'" in str(exc_info.value)

    def test_resolve_model_instance_creation_failure(self):
        """Test model resolution failure during instance creation."""
        resolver = ModelResolver()

        mock_registry = Mock()
        mock_class = Mock()
        mock_class.side_effect = Exception("Instance creation failed")

        mock_registry.detect_provider.return_value = "openai"
        mock_registry.resolve_model_class.return_value = mock_class

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            with pytest.raises(ModelResolutionError) as exc_info:
                resolver.resolve_model("gpt-4o-mini")

            assert "Failed to resolve model 'gpt-4o-mini'" in str(exc_info.value)


class TestModelValidation:
    """Test model availability validation."""

    def test_validate_model_availability_success(self):
        """Test successful model availability validation."""
        resolver = ModelResolver()

        mock_registry = Mock()
        mock_class = Mock()
        mock_class.__name__ = "OpenAIChat"  # Add missing name attribute

        mock_registry.detect_provider.return_value = "openai"
        mock_registry.resolve_model_class.return_value = mock_class

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            is_available = resolver.validate_model_availability("gpt-4o-mini")
            assert is_available is True

    def test_validate_model_availability_provider_detection_failure(self):
        """Test model availability validation with provider detection failure."""
        resolver = ModelResolver()

        mock_registry = Mock()
        mock_registry.detect_provider.side_effect = ModelResolutionError(
            "Provider not found"
        )

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            is_available = resolver.validate_model_availability("unknown-model")
            assert is_available is False

    def test_validate_model_availability_class_discovery_failure(self):
        """Test model availability validation with class discovery failure."""
        resolver = ModelResolver()

        mock_registry = Mock()
        mock_registry.detect_provider.return_value = "openai"
        mock_registry.resolve_model_class.side_effect = ModelResolutionError(
            "Class not found"
        )

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            is_available = resolver.validate_model_availability("gpt-unknown")
            assert is_available is False


class TestCacheManagement:
    """Test cache management functionality."""

    def test_clear_cache_clears_resolver_caches(self):
        """Test clear_cache clears ModelResolver caches."""
        resolver = ModelResolver()

        # Mock the registry
        mock_registry = Mock()

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            resolver.clear_cache()

            # Verify registry cache is cleared
            mock_registry.clear_cache.assert_called_once()


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_get_default_model_id_function(self):
        """Test get_default_model_id convenience function."""
        with patch.dict(os.environ, {"HIVE_DEFAULT_MODEL": "test-model"}):
            model_id = get_default_model_id()
            assert model_id == "test-model"

    def test_get_default_provider_success(self):
        """Test successful default provider retrieval."""
        with patch.dict(os.environ, {"HIVE_DEFAULT_PROVIDER": "openai"}):
            provider = get_default_provider()
            assert provider == "openai"

    def test_get_default_provider_missing_env_var(self):
        """Test ModelResolutionError when HIVE_DEFAULT_PROVIDER is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ModelResolutionError) as exc_info:
                get_default_provider()

            error_msg = str(exc_info.value)
            assert "HIVE_DEFAULT_PROVIDER environment variable is required" in error_msg
            assert "Example: export HIVE_DEFAULT_PROVIDER=openai" in error_msg

    def test_get_default_provider_empty_env_var(self):
        """Test ModelResolutionError when HIVE_DEFAULT_PROVIDER is empty."""
        with patch.dict(os.environ, {"HIVE_DEFAULT_PROVIDER": ""}):
            with pytest.raises(ModelResolutionError) as exc_info:
                get_default_provider()

            assert "HIVE_DEFAULT_PROVIDER environment variable is required" in str(
                exc_info.value
            )

    def test_resolve_model_function(self):
        """Test resolve_model convenience function."""
        mock_instance = Mock()

        with patch.object(
            model_resolver, "resolve_model", return_value=mock_instance
        ) as mock_resolve:
            result = resolve_model("gpt-4o-mini", temperature=0.5)

            assert result == mock_instance
            mock_resolve.assert_called_once_with("gpt-4o-mini", temperature=0.5)

    def test_validate_model_function(self):
        """Test validate_model convenience function."""
        with patch.object(
            model_resolver, "validate_model_availability", return_value=True
        ) as mock_validate:
            result = validate_model("gpt-4o-mini")

            assert result is True
            mock_validate.assert_called_once_with("gpt-4o-mini")


class TestEnvironmentValidation:
    """Test environment variable validation."""

    def test_validate_required_environment_variables_missing_both(self):
        """Test validation with both environment variables missing."""
        with patch.dict(os.environ, {}, clear=True):
            # Should not raise error, just log warning
            validate_required_environment_variables()

    def test_validate_required_environment_variables_missing_model_only(self):
        """Test validation with only model environment variable missing."""
        with patch.dict(os.environ, {"HIVE_DEFAULT_PROVIDER": "openai"}, clear=True):
            # Should not raise error, just log warning
            validate_required_environment_variables()

    def test_validate_required_environment_variables_missing_provider_only(self):
        """Test validation with only provider environment variable missing."""
        with patch.dict(os.environ, {"HIVE_DEFAULT_MODEL": "gpt-4o-mini"}, clear=True):
            # Should not raise error, just log warning
            validate_required_environment_variables()

    def test_validate_required_environment_variables_both_present(self):
        """Test validation with both environment variables present."""
        with patch.dict(
            os.environ,
            {"HIVE_DEFAULT_MODEL": "gpt-4o-mini", "HIVE_DEFAULT_PROVIDER": "openai"},
        ):
            # Should not log warning when both are present
            validate_required_environment_variables()


class TestPortugueseLanguageConfiguration:
    """Test Portuguese language specific configurations."""

    def test_portuguese_prompts_constant_structure(self):
        """Test PORTUGUESE_PROMPTS constant has expected structure."""
        assert isinstance(PORTUGUESE_PROMPTS, dict)

        expected_keys = {
            "system_instructions",
            "greeting",
            "error_message",
            "escalation_message",
            "feedback_request",
        }

        assert set(PORTUGUESE_PROMPTS.keys()) == expected_keys

    def test_portuguese_prompts_content_validation(self):
        """Test PORTUGUESE_PROMPTS contains Portuguese content."""
        # Check system instructions
        system_instructions = PORTUGUESE_PROMPTS["system_instructions"]
        assert "Você é um assistente especializado" in system_instructions
        assert "português brasileiro" in system_instructions
        assert "PagBank" in system_instructions

        # Check greeting
        greeting = PORTUGUESE_PROMPTS["greeting"]
        assert "Olá!" in greeting
        assert "PagBank" in greeting
        assert "Como posso ajudá-lo" in greeting

        # Check error message
        error_message = PORTUGUESE_PROMPTS["error_message"]
        assert "Desculpe" in error_message
        assert "suporte especializado" in error_message

        # Check escalation message
        escalation_message = PORTUGUESE_PROMPTS["escalation_message"]
        assert "conectar você" in escalation_message
        assert "especialista" in escalation_message

        # Check feedback request
        feedback_request = PORTUGUESE_PROMPTS["feedback_request"]
        assert "opinião é importante" in feedback_request
        assert "experiência" in feedback_request

    def test_get_portuguese_prompt_valid_keys(self):
        """Test get_portuguese_prompt returns correct values for valid keys."""
        assert get_portuguese_prompt("greeting") == PORTUGUESE_PROMPTS["greeting"]
        assert (
            get_portuguese_prompt("error_message")
            == PORTUGUESE_PROMPTS["error_message"]
        )
        assert (
            get_portuguese_prompt("escalation_message")
            == PORTUGUESE_PROMPTS["escalation_message"]
        )
        assert (
            get_portuguese_prompt("feedback_request")
            == PORTUGUESE_PROMPTS["feedback_request"]
        )

        # Test system instructions (multi-line)
        system_instructions = get_portuguese_prompt("system_instructions")
        assert "Você é um assistente especializado" in system_instructions
        assert len(system_instructions) > 50  # Should be multi-line content

    def test_get_portuguese_prompt_invalid_key(self):
        """Test get_portuguese_prompt returns empty string for invalid keys."""
        assert get_portuguese_prompt("nonexistent_key") == ""
        assert get_portuguese_prompt("") == ""
        assert get_portuguese_prompt("invalid") == ""

    def test_get_portuguese_prompt_none_key(self):
        """Test get_portuguese_prompt handles None key gracefully."""
        # This should either return empty string or handle None gracefully
        result = get_portuguese_prompt(None)
        assert isinstance(result, str)  # Should return string, likely empty

    def test_portuguese_prompts_all_strings(self):
        """Test all PORTUGUESE_PROMPTS values are strings."""
        for key, value in PORTUGUESE_PROMPTS.items():
            assert isinstance(value, str), f"Value for key '{key}' is not a string"
            assert len(value) > 0, f"Value for key '{key}' is empty"


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""

    def test_end_to_end_model_resolution_openai(self):
        """Test complete end-to-end model resolution for OpenAI."""
        resolver = ModelResolver()

        # Mock complete chain
        mock_registry = Mock()
        mock_class = Mock()
        mock_instance = Mock()

        mock_registry.detect_provider.return_value = "openai"
        mock_registry.resolve_model_class.return_value = mock_class
        mock_class.return_value = mock_instance
        mock_class.__name__ = "OpenAIChat"

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            result = resolver.resolve_model(
                "gpt-4o-mini", temperature=0.7, max_tokens=1000
            )

            # Verify complete chain
            mock_registry.detect_provider.assert_called_once_with("gpt-4o-mini")
            mock_registry.resolve_model_class.assert_called_once_with(
                "openai", "gpt-4o-mini"
            )
            mock_class.assert_called_once_with(
                id="gpt-4o-mini", temperature=0.7, max_tokens=1000
            )
            assert result == mock_instance

    def test_end_to_end_model_resolution_anthropic(self):
        """Test complete end-to-end model resolution for Anthropic."""
        resolver = ModelResolver()

        mock_registry = Mock()
        mock_class = Mock()
        mock_instance = Mock()

        mock_registry.detect_provider.return_value = "anthropic"
        mock_registry.resolve_model_class.return_value = mock_class
        mock_class.return_value = mock_instance
        mock_class.__name__ = "Claude"

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            with patch.dict(os.environ, {"HIVE_DEFAULT_MODEL": "claude-3-sonnet"}):
                result = resolver.resolve_model()  # Use default

                mock_registry.detect_provider.assert_called_once_with("claude-3-sonnet")
                mock_registry.resolve_model_class.assert_called_once_with(
                    "anthropic", "claude-3-sonnet"
                )
                mock_class.assert_called_once_with(id="claude-3-sonnet")
                assert result == mock_instance

    def test_model_resolver_with_config_overrides(self):
        """Test model resolution with various configuration overrides."""
        resolver = ModelResolver()

        mock_registry = Mock()
        mock_class = Mock()
        mock_instance = Mock()

        mock_registry.detect_provider.return_value = "google"
        mock_registry.resolve_model_class.return_value = mock_class
        mock_class.return_value = mock_instance
        mock_class.__name__ = "Gemini"

        config_overrides = {
            "temperature": 0.9,
            "max_tokens": 2000,
            "top_p": 0.95,
            "frequency_penalty": 0.5,
            "presence_penalty": 0.3,
        }

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            result = resolver.resolve_model("gemini-pro", **config_overrides)

            expected_config = {"id": "gemini-pro", **config_overrides}
            mock_class.assert_called_once_with(**expected_config)
            assert result == mock_instance


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and comprehensive error handling."""

    def test_model_id_with_special_characters(self):
        """Test model resolution with special characters in model ID."""
        resolver = ModelResolver()

        mock_registry = Mock()
        mock_class = Mock()
        mock_instance = Mock()

        mock_registry.detect_provider.return_value = "custom"
        mock_registry.resolve_model_class.return_value = mock_class
        mock_class.return_value = mock_instance
        mock_class.__name__ = "CustomModel"

        special_model_id = "custom-model_v2.1-beta@test"

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            result = resolver.resolve_model(special_model_id)

            mock_registry.detect_provider.assert_called_once_with(special_model_id)
            mock_class.assert_called_once_with(id=special_model_id)
            assert result == mock_instance

    def test_empty_model_id_handling(self):
        """Test handling of empty model ID."""
        resolver = ModelResolver()

        with patch.dict(os.environ, {"HIVE_DEFAULT_MODEL": "fallback-model"}):
            mock_registry = Mock()
            mock_class = Mock()
            mock_instance = Mock()

            mock_registry.detect_provider.return_value = "openai"
            mock_registry.resolve_model_class.return_value = mock_class
            mock_class.return_value = mock_instance
            mock_class.__name__ = "OpenAI"

            with patch(
                "lib.config.models.get_provider_registry", return_value=mock_registry
            ):
                # Empty string should use default
                resolver.resolve_model("")

                # Should have used fallback
                mock_registry.detect_provider.assert_called_once_with("fallback-model")
                mock_class.assert_called_once_with(id="fallback-model")

    def test_none_model_id_handling(self):
        """Test handling of None model ID."""
        resolver = ModelResolver()

        with patch.dict(os.environ, {"HIVE_DEFAULT_MODEL": "default-model"}):
            mock_registry = Mock()
            mock_class = Mock()
            mock_instance = Mock()

            mock_registry.detect_provider.return_value = "anthropic"
            mock_registry.resolve_model_class.return_value = mock_class
            mock_class.return_value = mock_instance
            mock_class.__name__ = "Claude"

            with patch(
                "lib.config.models.get_provider_registry", return_value=mock_registry
            ):
                resolver.resolve_model(None)

                mock_registry.detect_provider.assert_called_once_with("default-model")
                mock_class.assert_called_once_with(id="default-model")

    def test_config_overrides_with_none_values(self):
        """Test configuration overrides containing None values."""
        resolver = ModelResolver()

        mock_registry = Mock()
        mock_class = Mock()
        mock_instance = Mock()

        mock_registry.detect_provider.return_value = "openai"
        mock_registry.resolve_model_class.return_value = mock_class
        mock_class.return_value = mock_instance
        mock_class.__name__ = "OpenAI"

        config_with_nones = {
            "temperature": 0.7,
            "max_tokens": None,
            "top_p": 0.9,
            "timeout": None,
        }

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            result = resolver.resolve_model("gpt-4o-mini", **config_with_nones)

            expected_config = {"id": "gpt-4o-mini", **config_with_nones}
            mock_class.assert_called_once_with(**expected_config)
            assert result == mock_instance


class TestLRUCacheDecoratorBehavior:
    """Test LRU cache decorator behavior on resolver methods."""

    def test_detect_provider_cache_size_limit(self):
        """Test _detect_provider cache respects maxsize=128."""
        resolver = ModelResolver()

        # Verify cache info exists (indicates @lru_cache is applied)
        cache_info = resolver._detect_provider.cache_info()
        assert hasattr(cache_info, "maxsize")
        assert cache_info.maxsize == 128

    def test_discover_model_class_cache_size_limit(self):
        """Test _discover_model_class cache respects maxsize=64."""
        resolver = ModelResolver()

        cache_info = resolver._discover_model_class.cache_info()
        assert hasattr(cache_info, "maxsize")
        assert cache_info.maxsize == 64

    def test_cache_clear_resets_cache_info(self):
        """Test cache clearing resets cache statistics."""
        resolver = ModelResolver()

        mock_registry = Mock()
        mock_registry.detect_provider.return_value = "openai"

        with patch(
            "lib.config.models.get_provider_registry", return_value=mock_registry
        ):
            # Make some calls to populate cache
            resolver._detect_provider("gpt-4o-mini")
            resolver._detect_provider("gpt-3.5-turbo")

            # Verify cache has hits
            cache_info_before = resolver._detect_provider.cache_info()
            assert cache_info_before.currsize > 0

            # Clear cache
            resolver.clear_cache()

            # Verify cache is cleared
            cache_info_after = resolver._detect_provider.cache_info()
            assert cache_info_after.currsize == 0
            assert cache_info_after.hits == 0
            assert cache_info_after.misses == 0
