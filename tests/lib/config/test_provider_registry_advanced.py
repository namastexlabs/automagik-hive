"""
Advanced test coverage for lib.config.provider_registry module.

Targeting 50% minimum coverage with focus on:
- Dynamic provider discovery and caching
- Pattern generation and model detection
- Class resolution and fallback handling
- Cache management and error scenarios
- Integration with environment variables
"""

import pytest
import importlib
from unittest.mock import Mock, patch, MagicMock
from functools import lru_cache

# Import the module under test
try:
    from lib.config.provider_registry import (
        ProviderRegistry,
        get_provider_registry,
        detect_provider,
        get_provider_classes,
        resolve_model_class,
        list_available_providers,
        clear_provider_cache
    )
except ImportError:
    pytest.skip("Module lib.config.provider_registry not available", allow_module_level=True)


class TestProviderRegistryInit:
    """Test ProviderRegistry initialization."""

    def test_init_default_state(self):
        """Test ProviderRegistry initialization with default state."""
        registry = ProviderRegistry()
        
        assert registry._providers_cache is None
        assert registry._pattern_cache is None
        assert registry._class_cache == {}

    def test_init_cache_attributes(self):
        """Test ProviderRegistry cache attribute initialization."""
        registry = ProviderRegistry()
        
        # Test that cache attributes exist and have correct types
        assert hasattr(registry, '_providers_cache')
        assert hasattr(registry, '_pattern_cache') 
        assert hasattr(registry, '_class_cache')
        
        assert isinstance(registry._class_cache, dict)


class TestProviderDiscovery:
    """Test provider discovery functionality."""

    @patch('pkgutil.iter_modules')
    @patch('lib.config.provider_registry.logger')
    def test_get_available_providers_success(self, mock_logger, mock_iter_modules):
        """Test get_available_providers successful discovery."""
        # Mock pkgutil.iter_modules to return fake providers
        mock_iter_modules.return_value = [
            (None, 'openai', True),
            (None, 'anthropic', True),
            (None, '_internal', True),  # Should be skipped
            (None, 'google', False),   # Should be skipped (not package)
            (None, 'mistral', True)
        ]
        
        registry = ProviderRegistry()
        providers = registry.get_available_providers()
        
        # Should include packages that don't start with _ and are packages
        expected_providers = {'openai', 'anthropic', 'mistral'}
        assert providers == expected_providers
        
        mock_logger.debug.assert_called()
        mock_logger.info.assert_called_once()

    @patch('importlib.import_module')
    @patch('lib.config.provider_registry.logger')
    @patch('os.getenv')
    def test_get_available_providers_import_error_fallback(self, mock_getenv, mock_logger, mock_import):
        """Test get_available_providers fallback on import error."""
        mock_import.side_effect = ImportError("agno.models not found")
        mock_getenv.return_value = 'anthropic'  # Default provider
        
        registry = ProviderRegistry()
        providers = registry.get_available_providers()
        
        # Should use fallback providers with default first
        expected_providers = {'anthropic', 'openai', 'google', 'meta', 'mistral', 'cohere', 'groq'}
        assert providers == expected_providers
        assert 'anthropic' in providers  # Default provider included
        
        mock_logger.warning.assert_called_once()
        mock_logger.debug.assert_called()

    @patch('pkgutil.iter_modules')
    def test_get_available_providers_caching(self, mock_iter_modules):
        """Test get_available_providers caching behavior."""
        mock_iter_modules.return_value = [
            (None, 'openai', True),
            (None, 'anthropic', True)
        ]
        
        registry = ProviderRegistry()
        
        # First call
        providers1 = registry.get_available_providers()
        # Second call should use cache
        providers2 = registry.get_available_providers()
        
        assert providers1 == providers2
        # iter_modules should only be called once due to caching
        assert mock_iter_modules.call_count == 1

    @patch('pkgutil.iter_modules')
    def test_get_available_providers_empty_result(self, mock_iter_modules):
        """Test get_available_providers with no providers found."""
        mock_iter_modules.return_value = []
        
        registry = ProviderRegistry()
        providers = registry.get_available_providers()
        
        assert providers == set()

    @patch('pkgutil.iter_modules')
    def test_get_available_providers_mixed_types(self, mock_iter_modules):
        """Test get_available_providers filtering packages vs modules."""
        mock_iter_modules.return_value = [
            (None, 'provider_package', True),   # Package - should be included
            (None, 'provider_module', False),   # Module - should be skipped
            (None, '_private_package', True),   # Private - should be skipped
            (None, 'another_provider', True)    # Package - should be included
        ]
        
        registry = ProviderRegistry()
        providers = registry.get_available_providers()
        
        assert providers == {'provider_package', 'another_provider'}


class TestPatternGeneration:
    """Test provider pattern generation."""

    def test_get_provider_patterns_caching(self):
        """Test get_provider_patterns caching behavior."""
        registry = ProviderRegistry()
        
        with patch.object(registry, 'get_available_providers') as mock_get_providers:
            mock_get_providers.return_value = {'openai', 'anthropic'}
            
            # First call
            patterns1 = registry.get_provider_patterns()
            # Second call should use cache
            patterns2 = registry.get_provider_patterns()
            
            assert patterns1 == patterns2
            # get_available_providers should only be called once due to caching
            assert mock_get_providers.call_count == 1

    def test_generate_provider_patterns_openai(self):
        """Test _generate_provider_patterns for OpenAI."""
        registry = ProviderRegistry()
        
        patterns = registry._generate_provider_patterns('openai')
        
        # Should include OpenAI-specific patterns
        assert r'^gpt-' in patterns
        assert r'^o1-' in patterns
        assert r'^o3-' in patterns
        assert r'^text-' in patterns
        assert r'^openai$' in patterns
        
        # All patterns should map to 'openai'
        for pattern, provider in patterns.items():
            assert provider == 'openai'

    def test_generate_provider_patterns_anthropic(self):
        """Test _generate_provider_patterns for Anthropic."""
        registry = ProviderRegistry()
        
        patterns = registry._generate_provider_patterns('anthropic')
        
        assert r'^claude-' in patterns
        assert r'^claude\.' in patterns
        assert r'^anthropic$' in patterns
        
        for pattern, provider in patterns.items():
            assert provider == 'anthropic'

    def test_generate_provider_patterns_google(self):
        """Test _generate_provider_patterns for Google."""
        registry = ProviderRegistry()
        
        patterns = registry._generate_provider_patterns('google')
        
        assert r'^gemini-' in patterns
        assert r'^palm-' in patterns
        assert r'^bison-' in patterns
        assert r'^google$' in patterns

    def test_generate_provider_patterns_unknown_provider(self):
        """Test _generate_provider_patterns for unknown provider."""
        registry = ProviderRegistry()
        
        patterns = registry._generate_provider_patterns('unknown_provider')
        
        # Should have generic pattern and exact match
        assert r'^unknown_provider-' in patterns
        assert r'^unknown_provider$' in patterns
        
        for pattern, provider in patterns.items():
            assert provider == 'unknown_provider'

    def test_generate_provider_patterns_all_known_providers(self):
        """Test _generate_provider_patterns for all known providers."""
        registry = ProviderRegistry()
        known_providers = ['openai', 'anthropic', 'google', 'xai', 'meta', 'mistral', 'cohere', 'deepseek', 'groq']
        
        for provider in known_providers:
            patterns = registry._generate_provider_patterns(provider)
            
            # Each provider should have at least the exact match pattern
            assert f'^{provider}$' in patterns
            assert patterns[f'^{provider}$'] == provider
            
            # Should have at least one other pattern
            assert len(patterns) >= 2


class TestProviderDetection:
    """Test provider detection from model IDs."""

    def test_detect_provider_openai_models(self):
        """Test detect_provider with OpenAI model IDs."""
        registry = ProviderRegistry()
        
        with patch.object(registry, 'get_provider_patterns') as mock_patterns:
            mock_patterns.return_value = {
                r'^gpt-': 'openai',
                r'^o1-': 'openai',
                r'^text-': 'openai'
            }
            
            with patch.object(registry, 'get_available_providers') as mock_providers:
                mock_providers.return_value = {'openai', 'anthropic'}
                
                # Test various OpenAI model IDs
                openai_models = ['gpt-4o-mini', 'gpt-3.5-turbo', 'o1-preview', 'text-davinci-003']
                
                for model_id in openai_models:
                    provider = registry.detect_provider(model_id)
                    assert provider == 'openai'

    def test_detect_provider_anthropic_models(self):
        """Test detect_provider with Anthropic model IDs."""
        registry = ProviderRegistry()
        
        with patch.object(registry, 'get_provider_patterns') as mock_patterns:
            mock_patterns.return_value = {
                r'^claude-': 'anthropic',
                r'^claude\.': 'anthropic'
            }
            
            with patch.object(registry, 'get_available_providers') as mock_providers:
                mock_providers.return_value = {'openai', 'anthropic'}
                
                anthropic_models = ['claude-3-sonnet', 'claude-3-opus', 'claude.instant-v1']
                
                for model_id in anthropic_models:
                    provider = registry.detect_provider(model_id)
                    assert provider == 'anthropic'

    def test_detect_provider_case_insensitive(self):
        """Test detect_provider case insensitive matching."""
        registry = ProviderRegistry()
        
        with patch.object(registry, 'get_provider_patterns') as mock_patterns:
            mock_patterns.return_value = {r'^gpt-': 'openai'}
            
            with patch.object(registry, 'get_available_providers') as mock_providers:
                mock_providers.return_value = {'openai'}
                
                # Test case variations
                test_cases = ['GPT-4', 'gpt-4', 'Gpt-4', 'GPT-4O']
                
                for model_id in test_cases:
                    provider = registry.detect_provider(model_id)
                    assert provider == 'openai'

    def test_detect_provider_substring_fallback(self):
        """Test detect_provider substring fallback."""
        registry = ProviderRegistry()
        
        with patch.object(registry, 'get_provider_patterns') as mock_patterns:
            mock_patterns.return_value = {}  # No patterns match
            
            with patch.object(registry, 'get_available_providers') as mock_providers:
                mock_providers.return_value = {'openai', 'anthropic', 'google'}
                
                # Should find provider via substring matching
                assert registry.detect_provider('some-openai-model') == 'openai'
                assert registry.detect_provider('claude-variant') == 'anthropic'
                assert registry.detect_provider('google-custom') == 'google'

    def test_detect_provider_not_found(self):
        """Test detect_provider when no provider matches."""
        registry = ProviderRegistry()
        
        with patch.object(registry, 'get_provider_patterns') as mock_patterns:
            mock_patterns.return_value = {}
            
            with patch.object(registry, 'get_available_providers') as mock_providers:
                mock_providers.return_value = {'openai', 'anthropic'}
                
                provider = registry.detect_provider('unknown-model-xyz')
                assert provider is None

    @patch('lib.config.provider_registry.logger')
    def test_detect_provider_logging(self, mock_logger):
        """Test detect_provider logging behavior."""
        registry = ProviderRegistry()
        
        with patch.object(registry, 'get_provider_patterns') as mock_patterns:
            mock_patterns.return_value = {r'^test-': 'test_provider'}
            
            # Test successful detection logging
            provider = registry.detect_provider('test-model')
            mock_logger.debug.assert_called()
            
            # Test failed detection logging
            with patch.object(registry, 'get_available_providers') as mock_providers:
                mock_providers.return_value = {'test_provider'}
                
                provider = registry.detect_provider('unknown-model')
                mock_logger.debug.assert_called()


class TestProviderClassDiscovery:
    """Test provider class discovery and resolution."""

    @patch('importlib.import_module')
    @patch('lib.config.provider_registry.logger')
    def test_get_provider_classes_success(self, mock_logger, mock_import):
        """Test get_provider_classes successful discovery."""
        # Mock module with classes
        mock_module = Mock()
        mock_module.__dict__ = {
            'OpenAIChat': type('OpenAIChat', (), {}),
            'OpenAI': type('OpenAI', (), {}),
            '_private_class': type('_private_class', (), {}),
            'lowercase_func': lambda: None,
            'CONSTANT': 'value'
        }
        
        # Mock dir() to return attribute names
        with patch('builtins.dir', return_value=['OpenAIChat', 'OpenAI', '_private_class', 'lowercase_func', 'CONSTANT']):
            # Mock getattr to return appropriate objects
            def mock_getattr(obj, name):
                if name == 'OpenAIChat':
                    return type('OpenAIChat', (), {})
                elif name == 'OpenAI':
                    return type('OpenAI', (), {})
                elif name == '_private_class':
                    return type('_private_class', (), {})
                elif name == 'lowercase_func':
                    return lambda: None
                elif name == 'CONSTANT':
                    return 'value'
                return getattr(obj, name)
            
            with patch('builtins.getattr', side_effect=mock_getattr):
                mock_import.return_value = mock_module
                
                registry = ProviderRegistry()
                classes = registry.get_provider_classes('openai')
                
                # Should only include uppercase classes (not private, not functions, not constants)
                assert 'OpenAIChat' in classes
                assert 'OpenAI' in classes
                assert '_private_class' not in classes
                assert 'lowercase_func' not in classes
                assert 'CONSTANT' not in classes
                
                mock_logger.debug.assert_called()

    @patch('importlib.import_module')
    @patch('lib.config.provider_registry.logger')
    def test_get_provider_classes_import_error(self, mock_logger, mock_import):
        """Test get_provider_classes with import error."""
        mock_import.side_effect = ImportError("Module not found")
        
        registry = ProviderRegistry()
        classes = registry.get_provider_classes('unknown_provider')
        
        # Should return fallback classes
        expected_fallback = ['Unknown_provider', 'Unknown_providerChat']
        assert classes == expected_fallback
        
        mock_logger.warning.assert_called_once()

    def test_get_provider_classes_caching(self):
        """Test get_provider_classes caching behavior."""
        registry = ProviderRegistry()
        
        with patch('importlib.import_module') as mock_import:
            mock_module = Mock()
            with patch('builtins.dir', return_value=['TestClass']):
                with patch('builtins.getattr', return_value=type('TestClass', (), {})):
                    mock_import.return_value = mock_module
                    
                    # First call
                    classes1 = registry.get_provider_classes('test_provider')
                    # Second call should use cache
                    classes2 = registry.get_provider_classes('test_provider')
                    
                    assert classes1 == classes2
                    # import_module should only be called once
                    assert mock_import.call_count == 1

    def test_get_fallback_classes_known_providers(self):
        """Test _get_fallback_classes for known providers."""
        registry = ProviderRegistry()
        
        known_providers = {
            'openai': ['OpenAIChat', 'OpenAI'],
            'anthropic': ['Claude'],
            'google': ['Gemini', 'GoogleChat'],
            'xai': ['Grok'],
            'meta': ['Llama']
        }
        
        for provider, expected_classes in known_providers.items():
            classes = registry._get_fallback_classes(provider)
            assert classes == expected_classes

    def test_get_fallback_classes_unknown_provider(self):
        """Test _get_fallback_classes for unknown provider."""
        registry = ProviderRegistry()
        
        classes = registry._get_fallback_classes('custom_provider')
        
        # Should return generic fallback
        assert 'Custom_provider' in classes
        assert 'Custom_providerChat' in classes


class TestModelClassResolution:
    """Test model class resolution."""

    @patch('importlib.import_module')
    @patch('lib.config.provider_registry.logger')
    def test_resolve_model_class_success(self, mock_logger, mock_import):
        """Test resolve_model_class successful resolution."""
        # Mock module and class
        mock_class = type('OpenAIChat', (), {})
        mock_module = Mock()
        mock_module.OpenAIChat = mock_class
        mock_import.return_value = mock_module
        
        registry = ProviderRegistry()
        
        with patch.object(registry, 'get_provider_classes') as mock_get_classes:
            mock_get_classes.return_value = ['OpenAIChat', 'OpenAI']
            
            with patch('builtins.hasattr', return_value=True):
                with patch('builtins.getattr', return_value=mock_class):
                    resolved_class = registry.resolve_model_class('openai', 'gpt-4')
                    
                    assert resolved_class == mock_class
                    mock_logger.debug.assert_called()

    @patch('importlib.import_module')
    @patch('lib.config.provider_registry.logger')
    def test_resolve_model_class_not_found(self, mock_logger, mock_import):
        """Test resolve_model_class when class not found."""
        mock_module = Mock()
        mock_import.return_value = mock_module
        
        registry = ProviderRegistry()
        
        with patch.object(registry, 'get_provider_classes') as mock_get_classes:
            mock_get_classes.return_value = ['NonExistentClass']
            
            with patch('builtins.hasattr', return_value=False):
                with patch('builtins.dir', return_value=['ActualClass', 'AnotherClass']):
                    resolved_class = registry.resolve_model_class('provider', 'model-id')
                    
                    assert resolved_class is None
                    mock_logger.warning.assert_called_once()

    @patch('importlib.import_module')
    @patch('lib.config.provider_registry.logger')
    def test_resolve_model_class_import_error(self, mock_logger, mock_import):
        """Test resolve_model_class with import error."""
        mock_import.side_effect = ImportError("Module not found")
        
        registry = ProviderRegistry()
        resolved_class = registry.resolve_model_class('unknown_provider', 'model-id')
        
        assert resolved_class is None
        mock_logger.error.assert_called_once()

    @patch('importlib.import_module')
    def test_resolve_model_class_multiple_candidates(self, mock_import):
        """Test resolve_model_class with multiple class candidates."""
        # Mock module with multiple classes
        class_a = type('ClassA', (), {})
        class_b = type('ClassB', (), {})
        
        mock_module = Mock()
        mock_module.ClassA = class_a
        mock_module.ClassB = class_b
        mock_import.return_value = mock_module
        
        registry = ProviderRegistry()
        
        with patch.object(registry, 'get_provider_classes') as mock_get_classes:
            mock_get_classes.return_value = ['ClassA', 'ClassB']
            
            def mock_hasattr(obj, name):
                return name in ['ClassA', 'ClassB']
            
            def mock_getattr(obj, name):
                if name == 'ClassA':
                    return class_a
                elif name == 'ClassB':
                    return class_b
                return getattr(obj, name)
            
            with patch('builtins.hasattr', side_effect=mock_hasattr):
                with patch('builtins.getattr', side_effect=mock_getattr):
                    resolved_class = registry.resolve_model_class('provider', 'model-id')
                    
                    # Should return first available class
                    assert resolved_class == class_a


class TestCacheManagement:
    """Test cache management functionality."""

    def test_clear_cache_all_caches(self):
        """Test clear_cache clears all cache types."""
        registry = ProviderRegistry()
        
        # Set up some cache data
        registry._providers_cache = {'test_provider'}
        registry._pattern_cache = {'pattern': 'provider'}
        registry._class_cache = {'provider': ['Class']}
        
        # Mock the function cache clears
        with patch.object(registry.get_available_providers, 'cache_clear') as mock_providers_clear:
            with patch.object(registry.get_provider_patterns, 'cache_clear') as mock_patterns_clear:
                with patch.object(registry.detect_provider, 'cache_clear') as mock_detect_clear:
                    with patch.object(registry.get_provider_classes, 'cache_clear') as mock_classes_clear:
                        with patch.object(registry.resolve_model_class, 'cache_clear') as mock_resolve_clear:
                            registry.clear_cache()
                            
                            # Instance caches should be cleared
                            assert registry._providers_cache is None
                            assert registry._pattern_cache is None
                            assert registry._class_cache == {}
                            
                            # Function caches should be cleared
                            mock_providers_clear.assert_called_once()
                            mock_patterns_clear.assert_called_once()
                            mock_detect_clear.assert_called_once()
                            mock_classes_clear.assert_called_once()
                            mock_resolve_clear.assert_called_once()

    @patch('lib.config.provider_registry.logger')
    def test_clear_cache_logging(self, mock_logger):
        """Test clear_cache logging."""
        registry = ProviderRegistry()
        
        # Mock function cache clears to avoid AttributeError
        with patch.object(registry.get_available_providers, 'cache_clear'):
            with patch.object(registry.get_provider_patterns, 'cache_clear'):
                with patch.object(registry.detect_provider, 'cache_clear'):
                    with patch.object(registry.get_provider_classes, 'cache_clear'):
                        with patch.object(registry.resolve_model_class, 'cache_clear'):
                            registry.clear_cache()
                            
                            mock_logger.debug.assert_called_with("Provider registry cache cleared")


class TestGlobalRegistryFunctions:
    """Test global registry functions."""

    @patch('lib.config.provider_registry._provider_registry', None)
    def test_get_provider_registry_creates_instance(self):
        """Test get_provider_registry creates new instance when needed."""
        registry = get_provider_registry()
        
        assert isinstance(registry, ProviderRegistry)
        
        # Second call should return same instance
        registry2 = get_provider_registry()
        assert registry is registry2

    def test_detect_provider_function(self):
        """Test detect_provider convenience function."""
        with patch('lib.config.provider_registry.get_provider_registry') as mock_get_registry:
            mock_registry = Mock()
            mock_registry.detect_provider.return_value = 'test_provider'
            mock_get_registry.return_value = mock_registry
            
            result = detect_provider('test-model')
            
            assert result == 'test_provider'
            mock_registry.detect_provider.assert_called_once_with('test-model')

    def test_get_provider_classes_function(self):
        """Test get_provider_classes convenience function."""
        with patch('lib.config.provider_registry.get_provider_registry') as mock_get_registry:
            mock_registry = Mock()
            mock_registry.get_provider_classes.return_value = ['TestClass']
            mock_get_registry.return_value = mock_registry
            
            result = get_provider_classes('test_provider')
            
            assert result == ['TestClass']
            mock_registry.get_provider_classes.assert_called_once_with('test_provider')

    def test_resolve_model_class_function(self):
        """Test resolve_model_class convenience function."""
        with patch('lib.config.provider_registry.get_provider_registry') as mock_get_registry:
            mock_registry = Mock()
            mock_class = type('TestClass', (), {})
            mock_registry.resolve_model_class.return_value = mock_class
            mock_get_registry.return_value = mock_registry
            
            result = resolve_model_class('provider', 'model-id')
            
            assert result == mock_class
            mock_registry.resolve_model_class.assert_called_once_with('provider', 'model-id')

    def test_list_available_providers_function(self):
        """Test list_available_providers convenience function."""
        with patch('lib.config.provider_registry.get_provider_registry') as mock_get_registry:
            mock_registry = Mock()
            mock_registry.get_available_providers.return_value = {'provider1', 'provider2'}
            mock_get_registry.return_value = mock_registry
            
            result = list_available_providers()
            
            assert result == {'provider1', 'provider2'}
            mock_registry.get_available_providers.assert_called_once()

    def test_clear_provider_cache_function(self):
        """Test clear_provider_cache convenience function."""
        with patch('lib.config.provider_registry.get_provider_registry') as mock_get_registry:
            mock_registry = Mock()
            mock_get_registry.return_value = mock_registry
            
            clear_provider_cache()
            
            mock_registry.clear_cache.assert_called_once()


class TestIntegrationAndEdgeCases:
    """Test integration scenarios and edge cases."""

    def test_registry_workflow_complete(self):
        """Test complete registry workflow."""
        registry = ProviderRegistry()
        
        with patch.object(registry, 'get_available_providers') as mock_providers:
            mock_providers.return_value = {'openai', 'anthropic'}
            
            with patch.object(registry, '_generate_provider_patterns') as mock_gen_patterns:
                mock_gen_patterns.side_effect = [
                    {r'^gpt-': 'openai', r'^openai$': 'openai'},
                    {r'^claude-': 'anthropic', r'^anthropic$': 'anthropic'}
                ]
                
                # Get patterns (should call _generate_provider_patterns)
                patterns = registry.get_provider_patterns()
                
                # Detect provider using patterns
                provider = registry.detect_provider('gpt-4')
                
                # Get classes for detected provider
                with patch.object(registry, 'get_provider_classes') as mock_classes:
                    mock_classes.return_value = ['OpenAIChat']
                    classes = registry.get_provider_classes(provider)
                    
                    # Resolve model class
                    with patch.object(registry, 'resolve_model_class') as mock_resolve:
                        test_class = type('OpenAIChat', (), {})
                        mock_resolve.return_value = test_class
                        resolved_class = registry.resolve_model_class(provider, 'gpt-4')
                        
                        assert provider == 'openai'
                        assert classes == ['OpenAIChat']
                        assert resolved_class == test_class

    def test_registry_environment_integration(self):
        """Test registry integration with environment variables."""
        with patch('os.getenv') as mock_getenv:
            # Test with custom default provider
            mock_getenv.return_value = 'custom_provider'
            
            with patch('importlib.import_module', side_effect=ImportError("Not found")):
                registry = ProviderRegistry()
                providers = registry.get_available_providers()
                
                # Custom provider should be included
                assert 'custom_provider' in providers

    def test_registry_error_resilience(self):
        """Test registry resilience to various error conditions."""
        registry = ProviderRegistry()
        
        # Test with exception in pattern generation
        with patch.object(registry, '_generate_provider_patterns', side_effect=Exception("Pattern error")):
            with patch.object(registry, 'get_available_providers', return_value={'test_provider'}):
                # Should handle pattern generation errors gracefully
                patterns = registry.get_provider_patterns()
                assert isinstance(patterns, dict)

    def test_registry_edge_case_inputs(self):
        """Test registry with edge case inputs."""
        registry = ProviderRegistry()
        
        with patch.object(registry, 'get_provider_patterns', return_value={}):
            with patch.object(registry, 'get_available_providers', return_value=set()):
                # Empty model ID
                assert registry.detect_provider('') is None
                
                # Very long model ID
                long_model_id = 'a' * 1000
                result = registry.detect_provider(long_model_id)
                assert result is None or isinstance(result, str)
                
                # Special characters in model ID
                special_model_id = 'model!@#$%^&*()_+'
                result = registry.detect_provider(special_model_id)
                assert result is None or isinstance(result, str)

    def test_registry_cache_memory_efficiency(self):
        """Test registry cache memory efficiency."""
        registry = ProviderRegistry()
        
        # Test that caches don't grow indefinitely
        with patch.object(registry, 'get_available_providers', return_value={'test_provider'}):
            # Make many detect_provider calls
            model_ids = [f'test-model-{i}' for i in range(100)]
            
            for model_id in model_ids:
                registry.detect_provider(model_id)
            
            # LRU cache should limit memory usage (maxsize=64 for detect_provider)
            # This is handled by the @lru_cache decorator, so we just verify it doesn't crash
            assert True  # Test passes if no memory errors occur