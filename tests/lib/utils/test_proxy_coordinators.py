"""Tests for proxy_coordinators module - specifically output_model filtering."""

import pytest
from unittest.mock import Mock, patch
from lib.utils.proxy_coordinators import AgnoCoordinatorProxy


class TestAgnoCoordinatorProxy:
    """Test the AgnoCoordinatorProxy class."""

    def test_handle_model_config_filters_output_model(self):
        """Test that _handle_model_config properly filters out output_model parameter."""
        proxy = AgnoCoordinatorProxy()
        
        # Mock the resolve_model function
        with patch('lib.config.models.resolve_model') as mock_resolve_model:
            mock_resolve_model.return_value = Mock()
            
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
            
            # Verify resolve_model was called with filtered parameters
            mock_resolve_model.assert_called_once()
            call_args = mock_resolve_model.call_args
            
            # Check positional arguments
            assert call_args[1]["model_id"] == "claude-sonnet-4-20250514"
            assert call_args[1]["temperature"] == 0.7
            assert call_args[1]["max_tokens"] == 2000
            
            # Check that filtered parameters are NOT in the call
            assert "output_model" not in call_args[1]
            assert "provider" not in call_args[1]
            assert "reasoning" not in call_args[1]
            assert "reasoning_model" not in call_args[1]

    def test_handle_model_config_preserves_valid_params(self):
        """Test that _handle_model_config preserves valid model parameters."""
        proxy = AgnoCoordinatorProxy()
        
        with patch('lib.config.models.resolve_model') as mock_resolve_model:
            mock_resolve_model.return_value = Mock()
            
            # Test config with valid parameters that should be preserved
            model_config = {
                "id": "gpt-4o-mini",
                "temperature": 0.5,
                "max_tokens": 1500,
                "top_p": 0.9,  # Valid parameter that should be preserved
                "frequency_penalty": 0.1,  # Valid parameter that should be preserved
            }
            
            # Call the method
            result = proxy._handle_model_config(
                model_config=model_config,
                config={},
                component_id="test-coordinator",
                db_url=None
            )
            
            # Verify resolve_model was called with all valid parameters
            mock_resolve_model.assert_called_once()
            call_args = mock_resolve_model.call_args
            
            # Check that valid parameters are preserved
            assert call_args[1]["model_id"] == "gpt-4o-mini"
            assert call_args[1]["temperature"] == 0.5
            assert call_args[1]["max_tokens"] == 1500
            assert call_args[1]["top_p"] == 0.9
            assert call_args[1]["frequency_penalty"] == 0.1