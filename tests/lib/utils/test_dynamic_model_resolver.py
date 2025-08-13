"""Tests for dynamic model parameter resolution."""

import pytest
from unittest.mock import Mock, MagicMock, patch
import inspect


class TestDynamicModelResolver:
    """Test the truly dynamic model parameter resolution."""
    
    def test_introspect_model_parameters(self):
        """Test that we can introspect a model class to find valid parameters."""
        from lib.utils.dynamic_model_resolver import DynamicModelResolver
        
        # Create a mock model class with known parameters
        class MockModel:
            def __init__(self, id: str, temperature: float = 0.7, max_tokens: int = 1000, **kwargs):
                self.id = id
                self.temperature = temperature
                self.max_tokens = max_tokens
                self.extra = kwargs
        
        resolver = DynamicModelResolver()
        valid_params = resolver.get_valid_parameters(MockModel)
        
        # Should discover the explicit parameters
        assert "id" in valid_params
        assert "temperature" in valid_params
        assert "max_tokens" in valid_params
        assert "kwargs" in valid_params  # **kwargs shows up as a parameter
        
        # Should not include 'self'
        assert "self" not in valid_params
    
    def test_filter_parameters_dynamically(self):
        """Test filtering parameters based on model class introspection."""
        from lib.utils.dynamic_model_resolver import DynamicModelResolver
        
        # Create a mock model that only accepts certain parameters
        class MockClaudeModel:
            def __init__(self, id: str, temperature: float = 0.7, max_tokens: int = 2000):
                self.id = id
                self.temperature = temperature
                self.max_tokens = max_tokens
        
        resolver = DynamicModelResolver()
        
        # Input parameters including some that should be filtered
        input_params = {
            "id": "claude-3",
            "temperature": 0.5,
            "max_tokens": 1500,
            "output_model": {"provider": "openai", "id": "gpt-4"},  # Should be filtered
            "reasoning": "enabled",  # Should be filtered
            "provider": "anthropic"  # Should be filtered
        }
        
        filtered = resolver.filter_parameters_for_model(MockClaudeModel, input_params)
        
        # Should keep valid parameters
        assert filtered["id"] == "claude-3"
        assert filtered["temperature"] == 0.5
        assert filtered["max_tokens"] == 1500
        
        # Should filter out invalid parameters
        assert "output_model" not in filtered
        assert "reasoning" not in filtered
        assert "provider" not in filtered
    
    def test_fallback_trial_instantiation(self):
        """Test fallback mechanism when introspection fails."""
        from lib.utils.dynamic_model_resolver import DynamicModelResolver
        
        # Create a model that raises TypeError for unknown params
        class StrictModel:
            def __init__(self, id: str, temperature: float = 0.7):
                if not isinstance(id, str):
                    raise TypeError("id must be a string")
                self.id = id
                self.temperature = temperature
        
        # Mock introspection failure
        resolver = DynamicModelResolver()
        
        with patch.object(resolver, 'get_valid_parameters', return_value=set()):
            # Should fall back to trial instantiation
            input_params = {
                "id": "test-model",
                "temperature": 0.5,
                "output_model": "should-fail",  # This will cause TypeError
                "unknown_param": "value"
            }
            
            # Mock the model to raise TypeError for unexpected kwargs
            with patch.object(StrictModel, '__init__', side_effect=[
                TypeError("__init__() got an unexpected keyword argument 'output_model'"),
                TypeError("__init__() got an unexpected keyword argument 'unknown_param'"),
                None  # Success on third try
            ]):
                filtered = resolver._filter_by_trial(StrictModel, input_params)
                
                # Should have removed problematic parameters
                assert "output_model" not in filtered
                assert "unknown_param" not in filtered
                assert "id" in filtered
                assert "temperature" in filtered
    
    def test_cache_parameters(self):
        """Test that parameter discovery is cached."""
        from lib.utils.dynamic_model_resolver import DynamicModelResolver
        
        class MockModel:
            def __init__(self, id: str):
                self.id = id
        
        resolver = DynamicModelResolver()
        
        # First call should populate cache
        params1 = resolver.get_valid_parameters(MockModel)
        
        # Mock inspect.signature to ensure it's not called again
        with patch('inspect.signature') as mock_signature:
            # Second call should use cache
            params2 = resolver.get_valid_parameters(MockModel)
            
            # inspect.signature should not be called (using cache)
            mock_signature.assert_not_called()
        
        assert params1 == params2
    
    def test_handle_agno_model_classes(self):
        """Test handling real Agno model class signatures."""
        from lib.utils.dynamic_model_resolver import filter_model_parameters
        
        # Mock an Agno Claude class
        class MockAgnoClaudeClass:
            def __init__(
                self,
                id: str,
                temperature: float = 0.7,
                max_tokens: int = 4096,
                top_p: float = 1.0,
                frequency_penalty: float = 0.0,
                presence_penalty: float = 0.0,
                # Note: no output_model parameter!
            ):
                pass
        
        # Test with typical YAML config parameters
        yaml_config = {
            "id": "claude-sonnet-4-20250514",
            "temperature": 0.1,
            "max_tokens": 8000,
            "output_model": {  # This should be filtered out
                "provider": "openai",
                "id": "gpt-5",
                "service_tier": "scale"
            },
            "provider": "anthropic",  # This should be filtered out
            "reasoning": "enabled",  # This should be filtered out
        }
        
        filtered = filter_model_parameters(MockAgnoClaudeClass, yaml_config)
        
        # Should include valid Claude parameters
        assert filtered["id"] == "claude-sonnet-4-20250514"
        assert filtered["temperature"] == 0.1
        assert filtered["max_tokens"] == 8000
        
        # Should exclude parameters not in Claude's signature
        assert "output_model" not in filtered
        assert "provider" not in filtered
        assert "reasoning" not in filtered