"""Tests for proxy_coordinators module - specifically output_model filtering."""

import pytest
from unittest.mock import Mock, patch
from lib.utils.proxy_coordinators import AgnoCoordinatorProxy


class TestAgnoCoordinatorProxy:
    """Test the AgnoCoordinatorProxy class."""

    def test_handle_model_config_filters_output_model(self):
        """Test that _handle_model_config properly filters out output_model parameter."""
        proxy = AgnoCoordinatorProxy()
        
        # Mock the components that are actually called in the new implementation
        with patch('lib.config.provider_registry.get_provider_registry') as mock_registry, \
             patch('lib.utils.dynamic_model_resolver.filter_model_parameters') as mock_filter:
            
            # Create mock registry with provider detection and model class resolution
            mock_provider_registry = Mock()
            mock_registry.return_value = mock_provider_registry
            mock_provider_registry.detect_provider.return_value = "anthropic"
            
            # Create mock model class
            mock_model_class = Mock()
            mock_model_instance = Mock()
            mock_model_class.return_value = mock_model_instance
            mock_provider_registry.resolve_model_class.return_value = mock_model_class
            
            # Mock filter to return filtered parameters
            filtered_config = {
                "id": "claude-sonnet-4-20250514",
                "temperature": 0.7,
                "max_tokens": 2000,
            }
            mock_filter.return_value = filtered_config
            
            # Test config with output_model that should be filtered out
            model_config = {
                "id": "claude-sonnet-4-20250514",
                "temperature": 0.7,
                "max_tokens": 2000,
                "output_model": {  # This should be filtered out
                    "provider": "openai",
                    "id": "gpt-5",
                    "service_tier": "scale"
                },
                "provider": "anthropic",  # This should also be filtered
                "reasoning": "enabled",  # This should be filtered
                "reasoning_model": "claude-opus",  # This should be filtered
            }
            
            # Call the method
            result = proxy._handle_model_config(
                model_config=model_config,
                config={},
                component_id="test-coordinator",
                db_url=None
            )
            
            # Verify provider detection was called
            mock_provider_registry.detect_provider.assert_called_once_with("claude-sonnet-4-20250514")
            
            # Verify model class resolution was called
            mock_provider_registry.resolve_model_class.assert_called_once_with("anthropic", "claude-sonnet-4-20250514")
            
            # Verify filtering was called with the model class and original config
            mock_filter.assert_called_once_with(mock_model_class, model_config)
            
            # Verify model class was called with filtered parameters
            mock_model_class.assert_called_once_with(**filtered_config)
            
            # Verify result is the model instance
            assert result == mock_model_instance

    def test_handle_model_config_preserves_valid_params(self):
        """Test that _handle_model_config preserves valid model parameters."""
        proxy = AgnoCoordinatorProxy()
        
        # Mock the components that are actually called in the new implementation
        with patch('lib.config.provider_registry.get_provider_registry') as mock_registry, \
             patch('lib.utils.dynamic_model_resolver.filter_model_parameters') as mock_filter:
            
            # Create mock registry with provider detection and model class resolution
            mock_provider_registry = Mock()
            mock_registry.return_value = mock_provider_registry
            mock_provider_registry.detect_provider.return_value = "openai"
            
            # Create mock model class
            mock_model_class = Mock()
            mock_model_instance = Mock()
            mock_model_class.return_value = mock_model_instance
            mock_provider_registry.resolve_model_class.return_value = mock_model_class
            
            # Test config with valid parameters that should be preserved
            model_config = {
                "id": "gpt-4o-mini",
                "temperature": 0.5,
                "max_tokens": 1500,
                "top_p": 0.9,  # Valid parameter that should be preserved
                "frequency_penalty": 0.1,  # Valid parameter that should be preserved
            }
            
            # Mock filter to return all parameters (none filtered)
            mock_filter.return_value = model_config
            
            # Call the method
            result = proxy._handle_model_config(
                model_config=model_config,
                config={},
                component_id="test-coordinator",
                db_url=None
            )
            
            # Verify provider detection was called
            mock_provider_registry.detect_provider.assert_called_once_with("gpt-4o-mini")
            
            # Verify model class resolution was called
            mock_provider_registry.resolve_model_class.assert_called_once_with("openai", "gpt-4o-mini")
            
            # Verify filtering was called with the model class and original config
            mock_filter.assert_called_once_with(mock_model_class, model_config)
            
            # Verify model class was called with all valid parameters
            mock_model_class.assert_called_once_with(**model_config)
            
            # Verify result is the model instance
            assert result == mock_model_instance