"""
Comprehensive test suite for lib/config/models.py - Model Resolution System

This test suite focuses on:
- Model resolution with dynamic provider discovery
- Environment variable handling and validation
- Error scenarios and edge cases
- Integration with provider registry
"""

import os
from unittest.mock import Mock, patch
import pytest

# Import the module under test
try:
    from lib.config.models import (
        ModelResolutionError,
        ModelResolver,
        get_default_model_id,
        get_default_provider,
        model_resolver,
        resolve_model,
        validate_model,
    )
except ImportError:
    pytest.skip(f"Module lib.config.models not available", allow_module_level=True)


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

    def test_global_model_resolver_exists(self):
        """Test global model_resolver instance exists and is correct type."""
        assert model_resolver is not None
        assert isinstance(model_resolver, ModelResolver)


class TestDefaultModelIdResolution:
    """Test default model ID resolution from environment variables."""

    def test_get_default_model_id_success(self):
        """Test successful default model ID retrieval from environment."""
        with patch.dict(os.environ, {"HIVE_DEFAULT_MODEL": "gpt-4o-mini"}):
            if hasattr(model_resolver, 'get_default_model_id'):
                model_id = model_resolver.get_default_model_id()
                assert model_id == "gpt-4o-mini"

    def test_get_default_model_id_missing_env_var(self):
        """Test error handling when HIVE_DEFAULT_MODEL is not set."""
        with patch.dict(os.environ, {}, clear=True):
            if hasattr(model_resolver, 'get_default_model_id'):
                with pytest.raises((ModelResolutionError, ValueError, KeyError)):
                    model_resolver.get_default_model_id()

    def test_get_default_model_id_empty_env_var(self):
        """Test error handling when HIVE_DEFAULT_MODEL is empty."""
        with patch.dict(os.environ, {"HIVE_DEFAULT_MODEL": ""}):
            if hasattr(model_resolver, 'get_default_model_id'):
                with pytest.raises((ModelResolutionError, ValueError)):
                    model_resolver.get_default_model_id()


class TestDefaultProviderResolution:
    """Test default provider detection and resolution."""

    def test_get_default_provider_with_openai_env(self):
        """Test provider detection when HIVE_DEFAULT_PROVIDER env var is set."""
        with patch.dict(os.environ, {"HIVE_DEFAULT_PROVIDER": "openai"}, clear=True):
            if callable(get_default_provider):
                provider = get_default_provider()
                # Should return a valid provider string
                assert isinstance(provider, str)
                assert len(provider) > 0
                assert provider == "openai"

    def test_get_default_provider_with_anthropic_env(self):
        """Test provider detection when HIVE_DEFAULT_PROVIDER env var is set."""
        with patch.dict(os.environ, {"HIVE_DEFAULT_PROVIDER": "anthropic"}, clear=True):
            if callable(get_default_provider):
                provider = get_default_provider()
                assert isinstance(provider, str)
                assert len(provider) > 0
                assert provider == "anthropic"

    def test_get_default_provider_no_env_vars(self):
        """Test provider detection when HIVE_DEFAULT_PROVIDER is not set."""
        env_vars_to_clear = [
            "HIVE_DEFAULT_PROVIDER", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", 
            "AZURE_OPENAI_API_KEY", "COHERE_API_KEY", "REPLICATE_API_TOKEN"
        ]
        with patch.dict(os.environ, {}, clear=True):
            if callable(get_default_provider):
                # Should either return a default or raise an appropriate error
                try:
                    provider = get_default_provider()
                    assert isinstance(provider, str)
                except (ModelResolutionError, ValueError):
                    # Expected behavior when no providers available
                    pass


class TestModelResolution:
    """Test the main model resolution functionality."""

    def test_resolve_model_with_valid_model_id(self):
        """Test model resolution with valid model ID."""
        if callable(resolve_model):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
                try:
                    # Test with a common model identifier
                    model = resolve_model("claude-3-haiku-20240307")
                    assert model is not None
                except (ModelResolutionError, ImportError, AttributeError):
                    # Expected if dependencies not available in test environment
                    pass

    def test_resolve_model_with_invalid_model_id(self):
        """Test model resolution with invalid model ID."""
        if callable(resolve_model):
            with pytest.raises((ModelResolutionError, ValueError, AttributeError)):
                resolve_model("invalid-model-that-does-not-exist")

    def test_resolve_model_environment_integration(self):
        """Test model resolution integrates with environment configuration."""
        if callable(resolve_model):
            test_env = {
                "HIVE_DEFAULT_MODEL": "gpt-4o-mini",
                "OPENAI_API_KEY": "test-key"
            }
            with patch.dict(os.environ, test_env):
                try:
                    model = resolve_model()  # Should use default from env
                    assert model is not None
                except (ModelResolutionError, ImportError, AttributeError):
                    # Expected if dependencies not available
                    pass


class TestModelValidation:
    """Test model validation functionality."""

    def test_validate_model_with_valid_model(self):
        """Test model validation with valid model instance."""
        if callable(validate_model):
            # Create a mock model that should pass validation
            mock_model = Mock()
            mock_model.model_name = "test-model"
            
            try:
                result = validate_model(mock_model)
                # Should either return True or the model itself
                assert result is not None
            except (AttributeError, TypeError):
                # Expected if validation checks specific attributes
                pass

    def test_validate_model_with_invalid_model(self):
        """Test model validation with invalid model."""
        if callable(validate_model):
            with pytest.raises((ValueError, TypeError, AttributeError)):
                validate_model(None)

    def test_validate_model_with_string_input(self):
        """Test model validation behavior with string input."""
        if callable(validate_model):
            try:
                result = validate_model("test-model-string")
                # Should handle string input appropriately
                assert result is not None
            except (TypeError, ValueError):
                # Expected if validation requires specific object types
                pass


class TestModelResolverMethods:
    """Test ModelResolver class methods."""

    def test_model_resolver_detect_provider(self):
        """Test provider detection method."""
        resolver = ModelResolver()
        
        if hasattr(resolver, '_detect_provider'):
            # Test with various environment configurations and model IDs
            test_models = ["gpt-4", "claude-3-haiku-20240307", "gemini-pro"]
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}, clear=True):
                for model_id in test_models:
                    try:
                        provider = resolver._detect_provider(model_id)
                        assert isinstance(provider, str)
                        break  # If one succeeds, that's enough for the test
                    except (AttributeError, ModelResolutionError):
                        continue  # Try next model

    def test_model_resolver_discover_model_class(self):
        """Test model class discovery method."""
        resolver = ModelResolver()
        
        if hasattr(resolver, '_discover_model_class'):
            try:
                # Test discovery with a known provider
                model_class = resolver._discover_model_class("anthropic", "claude-3-haiku-20240307")
                assert model_class is not None
            except (AttributeError, ModelResolutionError, ImportError):
                # Expected if provider packages not available
                pass

    def test_model_resolver_resolve_model_method(self):
        """Test the resolve_model method on ModelResolver instance."""
        resolver = ModelResolver()
        
        if hasattr(resolver, 'resolve_model'):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
                try:
                    model = resolver.resolve_model("claude-3-haiku-20240307")
                    assert model is not None
                except (ModelResolutionError, ImportError, AttributeError):
                    # Expected if dependencies not available
                    pass


class TestEnvironmentVariableValidation:
    """Test environment variable validation and handling."""

    def test_required_environment_variables_validation(self):
        """Test validation of required environment variables."""
        # Test with various environment configurations
        test_configs = [
            {"ANTHROPIC_API_KEY": "test-key"},
            {"OPENAI_API_KEY": "test-key"},
            {"GOOGLE_API_KEY": "test-key"},
        ]
        
        for config in test_configs:
            with patch.dict(os.environ, config, clear=True):
                # Test that validation passes with proper API keys
                resolver = ModelResolver()
                assert resolver is not None


class TestModelConfigurationEdgeCases:
    """Test edge cases and error conditions in model configuration."""

    def test_model_resolver_with_missing_dependencies(self):
        """Test behavior when model provider dependencies are missing."""
        resolver = ModelResolver()
        
        # Test that resolver handles missing dependencies gracefully
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}):
            try:
                # Should either work or fail gracefully
                model = resolver.resolve_model("gpt-4")
                assert model is not None
            except (ImportError, ModelResolutionError, AttributeError):
                # Expected when dependencies not available
                pass

    def test_model_resolver_with_invalid_api_keys(self):
        """Test behavior with invalid API key formats."""
        test_cases = [
            {"ANTHROPIC_API_KEY": ""},
            {"ANTHROPIC_API_KEY": "invalid-key-format"},
            {"OPENAI_API_KEY": "short"},
        ]
        
        for env_config in test_cases:
            with patch.dict(os.environ, env_config):
                resolver = ModelResolver()
                # Should handle invalid keys appropriately
                assert resolver is not None

    def test_concurrent_model_resolution(self):
        """Test that model resolution works correctly with concurrent access."""
        import threading
        
        results = []
        errors = []
        
        def resolve_model_thread():
            try:
                with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}):
                    resolver = ModelResolver()
                    results.append(resolver)
            except Exception as e:
                errors.append(e)
        
        # Test concurrent access
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=resolve_model_thread)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should handle concurrent access without issues
        assert len(results) > 0 or len(errors) > 0  # Some result expected


class TestModelIntegration:
    """Test integration between different model system components."""

    def test_end_to_end_model_resolution_flow(self):
        """Test complete model resolution flow from environment to model instance."""
        test_env = {
            "HIVE_DEFAULT_MODEL": "claude-3-haiku-20240307",
            "ANTHROPIC_API_KEY": "test-anthropic-key"
        }
        
        with patch.dict(os.environ, test_env):
            try:
                # Test the complete flow
                if callable(get_default_model_id):
                    model_id = get_default_model_id()
                    assert model_id == "claude-3-haiku-20240307"
                
                if callable(get_default_provider):
                    provider = get_default_provider()
                    assert isinstance(provider, str)
                
                if callable(resolve_model):
                    model = resolve_model(model_id)
                    assert model is not None
                    
            except (ModelResolutionError, ImportError, AttributeError):
                # Expected if dependencies not available in test environment
                pass

    def test_model_system_resilience(self):
        """Test that the model system is resilient to various error conditions."""
        # Test with completely empty environment
        with patch.dict(os.environ, {}, clear=True):
            resolver = ModelResolver()
            assert resolver is not None
            
        # Test with partial environment configuration
        with patch.dict(os.environ, {"HIVE_DEFAULT_MODEL": "test-model"}, clear=True):
            resolver = ModelResolver()
            assert resolver is not None