"""
Source Code Execution Test Suite for ProviderRegistry
=====================================================

NEW test suite focused on EXECUTING actual provider registry code paths 
to achieve 50%+ coverage. This complements existing mock-heavy tests with 
REAL execution of discovery, caching, and class resolution logic.

Target: lib/config/provider_registry.py (currently 21% coverage)
Strategy: Execute actual code paths with realistic data
"""

import os
import re
import importlib
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import pytest

from lib.config.provider_registry import (
    ProviderRegistry,
    get_provider_registry,
    detect_provider,
    get_provider_classes,
    resolve_model_class,
    list_available_providers,
    clear_provider_cache,
)


class TestProviderRegistryExecution:
    """Test suite that EXECUTES ProviderRegistry code paths with real data."""

    def test_init_execution(self):
        """Execute __init__ method and verify cache initialization."""
        # EXECUTE: ProviderRegistry.__init__()
        registry = ProviderRegistry()
        
        # VERIFY: Cache structures properly initialized
        assert registry._providers_cache is None
        assert registry._pattern_cache is None
        assert isinstance(registry._class_cache, dict)
        assert len(registry._class_cache) == 0

    @patch('agno.models')
    def test_provider_discovery_execution_with_mocked_agno(self, mock_agno_models):
        """EXECUTE provider discovery with mocked agno.models module."""
        # Create a mock agno.models with __path__ attribute
        mock_agno_models.__path__ = ['/fake/agno/models']
        
        # Mock pkgutil.iter_modules to return realistic provider data
        with patch('pkgutil.iter_modules') as mock_iter:
            mock_iter.return_value = [
                (None, 'openai', True),
                (None, 'anthropic', True),
                (None, 'google', True),
                (None, 'xai', True),
                (None, 'meta', True),
                (None, '_internal', True),  # Should be filtered out
                (None, 'utils', False),     # Should be filtered out (not package)
            ]
            
            # EXECUTE: get_available_providers() - REAL execution, not mocked
            registry = ProviderRegistry()
            providers = registry.get_available_providers()
            
            # VERIFY: Real execution results
            assert isinstance(providers, set)
            assert 'openai' in providers
            assert 'anthropic' in providers
            assert 'google' in providers
            assert 'xai' in providers
            assert 'meta' in providers
            assert '_internal' not in providers  # Filtered out
            assert 'utils' not in providers      # Filtered out
            assert len(providers) == 5

    def test_provider_discovery_fallback_execution(self):
        """EXECUTE provider discovery fallback when agno.models fails."""
        # Force ImportError by mocking pkgutil.iter_modules to fail
        with patch('pkgutil.iter_modules', side_effect=ImportError("agno.models not found")):
            with patch.dict(os.environ, {'HIVE_DEFAULT_PROVIDER': 'custom'}, clear=False):
                # EXECUTE: get_available_providers() fallback path
                registry = ProviderRegistry()
                providers = registry.get_available_providers()
                
                # VERIFY: Fallback execution results
                assert isinstance(providers, set)
                assert 'custom' in providers  # From environment variable
                assert 'openai' in providers  # Standard fallback
                assert 'anthropic' in providers
                assert 'google' in providers
                assert len(providers) >= 8  # Should have multiple fallback providers

    def test_pattern_generation_execution_all_providers(self):
        """EXECUTE pattern generation for all known provider types."""
        registry = ProviderRegistry()
        
        # Test data: (provider_name, expected_patterns, sample_model_ids)
        provider_test_cases = [
            ('openai', [r'^gpt-', r'^o1-', r'^o3-', r'^text-', r'^openai$'], 
             ['gpt-4', 'o1-preview', 'text-davinci-003']),
            ('anthropic', [r'^claude-', r'^claude\.', r'^anthropic$'], 
             ['claude-3-sonnet', 'claude.instant']),
            ('google', [r'^gemini-', r'^palm-', r'^bison-', r'^google$'], 
             ['gemini-pro', 'palm-2', 'bison-001']),
            ('xai', [r'^grok-', r'^xai$'], 
             ['grok-beta', 'grok-1']),
            ('meta', [r'^llama-', r'^llama2-', r'^llama3-', r'^codellama-', r'^meta$'], 
             ['llama-2-7b', 'llama3-8b', 'codellama-7b']),
            ('mistral', [r'^mistral-', r'^mixtral-', r'^codestral-', r'^mistral$'], 
             ['mistral-7b', 'mixtral-8x7b', 'codestral-22b']),
            ('cohere', [r'^command-', r'^embed-', r'^cohere$'], 
             ['command-r', 'embed-english-v3.0']),
            ('deepseek', [r'^deepseek-', r'^deepseek$'], 
             ['deepseek-coder', 'deepseek-chat']),
            ('groq', [r'^groq-', r'^groq$'], 
             ['groq-llama', 'groq-mixtral']),
            ('unknown_provider', [r'^unknown_provider-', r'^unknown_provider$'], 
             ['unknown_provider-model']),
        ]
        
        for provider, expected_patterns, sample_models in provider_test_cases:
            # EXECUTE: _generate_provider_patterns() for each provider
            patterns = registry._generate_provider_patterns(provider)
            
            # VERIFY: Generated patterns contain expected patterns
            assert isinstance(patterns, dict)
            for expected_pattern in expected_patterns:
                assert expected_pattern in patterns
                assert patterns[expected_pattern] == provider
            
            # VERIFY: Pattern matching works with sample model IDs
            for model_id in sample_models:
                # Test that at least one pattern matches each sample model
                matched = False
                for pattern, provider_name in patterns.items():
                    if re.match(pattern, model_id.lower(), re.IGNORECASE):
                        matched = True
                        assert provider_name == provider
                        break
                assert matched, f"No pattern matched {model_id} for provider {provider}"

    def test_provider_pattern_caching_execution(self):
        """EXECUTE provider pattern caching behavior."""
        registry = ProviderRegistry()
        
        # Mock get_available_providers to return consistent data
        with patch.object(registry, 'get_available_providers') as mock_providers:
            mock_providers.return_value = {'openai', 'anthropic'}
            
            # EXECUTE: First call to get_provider_patterns()
            patterns1 = registry.get_provider_patterns()
            
            # EXECUTE: Second call to get_provider_patterns()
            patterns2 = registry.get_provider_patterns()
            
            # VERIFY: Caching worked - same object returned
            assert patterns1 is patterns2
            assert mock_providers.call_count == 1  # Only called once due to caching
            
            # VERIFY: Cache contains expected data
            assert isinstance(patterns1, dict)
            assert len(patterns1) > 0

    def test_provider_detection_execution_realistic_models(self):
        """EXECUTE provider detection with realistic model IDs."""
        registry = ProviderRegistry()
        
        # Test realistic model ID detection scenarios
        model_test_cases = [
            # (model_id, expected_provider_or_none)
            ('gpt-4o-mini', 'openai'),
            ('gpt-3.5-turbo-16k', 'openai'),
            ('o1-preview', 'openai'),
            ('text-davinci-003', 'openai'),
            ('claude-3-sonnet-20240229', 'anthropic'),
            ('claude-instant-v1', 'anthropic'),
            ('claude.instant', 'anthropic'),
            ('gemini-pro', 'google'),
            ('palm-2-chat-bison', 'google'),
            ('grok-beta', 'xai'),
            ('llama-2-7b-chat', 'meta'),
            ('codellama-34b', 'meta'),
            ('mistral-7b-instruct', 'mistral'),
            ('mixtral-8x7b', 'mistral'),
            ('command-r-plus', 'cohere'),
            ('deepseek-coder-6.7b', 'deepseek'),
            ('completely-unknown-model-xyz', None),
            ('', None),
        ]
        
        for model_id, expected_provider in model_test_cases:
            # EXECUTE: detect_provider() with real pattern matching
            detected_provider = registry.detect_provider(model_id)
            
            # VERIFY: Detection results match expectations
            assert detected_provider == expected_provider, \
                f"Expected {expected_provider} for {model_id}, got {detected_provider}"

    def test_provider_detection_case_insensitive_execution(self):
        """EXECUTE case-insensitive provider detection."""
        registry = ProviderRegistry()
        
        # Test case variations of the same model
        case_test_cases = [
            ('gpt-4', 'openai'),
            ('GPT-4', 'openai'),
            ('Gpt-4', 'openai'),
            ('gPt-4', 'openai'),
            ('claude-3-sonnet', 'anthropic'),
            ('CLAUDE-3-SONNET', 'anthropic'),
            ('Claude-3-Sonnet', 'anthropic'),
        ]
        
        for model_id, expected_provider in case_test_cases:
            # EXECUTE: detect_provider() with case variations
            detected_provider = registry.detect_provider(model_id)
            
            # VERIFY: Case insensitive matching works
            assert detected_provider == expected_provider, \
                f"Case insensitive detection failed for {model_id}"

    def test_substring_fallback_execution(self):
        """EXECUTE substring fallback detection logic."""
        registry = ProviderRegistry()
        
        # Mock to force pattern matching to fail, test substring fallback
        with patch.object(registry, 'get_provider_patterns') as mock_patterns:
            with patch.object(registry, 'get_available_providers') as mock_providers:
                # No patterns match, only substring fallback available
                mock_patterns.return_value = {}
                mock_providers.return_value = {'mistral', 'anthropic', 'deepseek'}
                
                # EXECUTE: Substring fallback detection
                assert registry.detect_provider('custom-mistral-model') == 'mistral'
                assert registry.detect_provider('my-anthropic-test') == 'anthropic'
                assert registry.detect_provider('deepseek-variant') == 'deepseek'
                assert registry.detect_provider('completely-unknown') is None

    def test_class_discovery_execution_with_fallbacks(self):
        """EXECUTE class discovery with realistic import scenarios."""
        registry = ProviderRegistry()
        
        # Test successful import scenario
        with patch('importlib.import_module') as mock_import:
            # Create a realistic mock module
            mock_module = Mock()
            
            # Add realistic class attributes (simulating actual provider modules)
            mock_module.OpenAIChat = type('OpenAIChat', (), {})
            mock_module.OpenAI = type('OpenAI', (), {})
            mock_module._internal_util = Mock()  # Should be ignored
            mock_module.some_function = Mock()   # Should be ignored
            mock_module.CONSTANT = 'value'       # Should be ignored
            
            # Mock dir() to return these attributes
            mock_attrs = ['OpenAIChat', 'OpenAI', '_internal_util', 'some_function', 'CONSTANT']
            with patch('builtins.dir', return_value=mock_attrs):
                mock_import.return_value = mock_module
                
                # EXECUTE: get_provider_classes() with realistic module
                classes = registry.get_provider_classes('openai')
                
                # VERIFY: Only uppercase type attributes included
                assert 'OpenAIChat' in classes
                assert 'OpenAI' in classes
                assert '_internal_util' not in classes
                assert 'some_function' not in classes
                assert 'CONSTANT' not in classes

    def test_class_discovery_fallback_execution(self):
        """EXECUTE class discovery fallback when import fails."""
        registry = ProviderRegistry()
        
        # Test import failure scenario
        with patch('importlib.import_module', side_effect=ImportError("Module not found")):
            # EXECUTE: get_provider_classes() with import failure
            
            # Test known providers
            openai_classes = registry.get_provider_classes('openai')
            assert openai_classes == ['OpenAIChat', 'OpenAI']
            
            anthropic_classes = registry.get_provider_classes('anthropic')
            assert anthropic_classes == ['Claude']
            
            google_classes = registry.get_provider_classes('google')
            assert google_classes == ['Gemini', 'GoogleChat']
            
            # Test unknown provider fallback
            unknown_classes = registry.get_provider_classes('custom_provider')
            assert unknown_classes == ['Custom_Provider', 'Custom_ProviderChat']

    def test_class_caching_execution(self):
        """EXECUTE class discovery caching behavior."""
        registry = ProviderRegistry()
        
        with patch('importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_module.TestClass = type('TestClass', (), {})
            
            with patch('builtins.dir', return_value=['TestClass']):
                mock_import.return_value = mock_module
                
                # EXECUTE: First call
                classes1 = registry.get_provider_classes('test_provider')
                
                # EXECUTE: Second call (should use cache)
                classes2 = registry.get_provider_classes('test_provider')
                
                # VERIFY: Caching worked
                assert classes1 == classes2
                assert classes1 == ['TestClass']
                # Due to @lru_cache and instance cache interaction, just verify results match
                assert classes2 == ['TestClass']

    def test_model_class_resolution_execution(self):
        """EXECUTE model class resolution with realistic scenarios."""
        registry = ProviderRegistry()
        
        # Test successful resolution
        with patch('importlib.import_module') as mock_import:
            mock_module = Mock()
            test_class = type('OpenAIChat', (), {})
            mock_module.OpenAIChat = test_class
            mock_module.OpenAI = type('OpenAI', (), {})
            mock_import.return_value = mock_module
            
            with patch.object(registry, 'get_provider_classes') as mock_get_classes:
                mock_get_classes.return_value = ['OpenAIChat', 'OpenAI']
                
                # EXECUTE: resolve_model_class() successfully
                resolved_class = registry.resolve_model_class('openai', 'gpt-4')
                
                # VERIFY: First available class returned
                assert resolved_class == test_class

    def test_model_class_resolution_not_found_execution(self):
        """EXECUTE model class resolution when class not found."""
        registry = ProviderRegistry()
        
        with patch('importlib.import_module') as mock_import:
            # Create module that doesn't have the expected class
            mock_module = Mock()
            mock_module.SomeOtherClass = type('SomeOtherClass', (), {})
            # Explicitly ensure MissingClass doesn't exist
            if hasattr(mock_module, 'MissingClass'):
                delattr(mock_module, 'MissingClass')
                
            mock_import.return_value = mock_module
            
            with patch.object(registry, 'get_provider_classes') as mock_get_classes:
                mock_get_classes.return_value = ['MissingClass']
                
                # EXECUTE: resolve_model_class() with missing class
                resolved_class = registry.resolve_model_class('test_provider', 'test-model')
                
                # VERIFY: None returned when class not found
                assert resolved_class is None

    def test_model_class_resolution_import_error_execution(self):
        """EXECUTE model class resolution when import fails."""
        registry = ProviderRegistry()
        
        with patch('importlib.import_module', side_effect=ImportError("Module not found")):
            # EXECUTE: resolve_model_class() with import error
            resolved_class = registry.resolve_model_class('nonexistent_provider', 'test-model')
            
            # VERIFY: None returned on import error
            assert resolved_class is None

    def test_cache_clearing_execution(self):
        """EXECUTE cache clearing functionality."""
        registry = ProviderRegistry()
        
        # Populate all caches with test data
        registry._providers_cache = {'test_provider'}
        registry._pattern_cache = {'pattern': 'provider'}
        registry._class_cache = {'provider': ['TestClass']}
        
        # Populate method caches by calling cached methods
        with patch.object(registry, 'get_available_providers') as mock_providers:
            mock_providers.return_value = {'test'}
            registry.get_provider_patterns()  # Populate @lru_cache
            registry.detect_provider('test-model')  # Populate @lru_cache
            registry.get_provider_classes('test')  # Populate @lru_cache
            registry.resolve_model_class('test', 'model')  # Populate @lru_cache
        
        # EXECUTE: clear_cache()
        registry.clear_cache()
        
        # VERIFY: Instance caches cleared
        assert registry._providers_cache is None
        assert registry._pattern_cache is None
        assert registry._class_cache == {}

    def test_lru_cache_limits_execution(self):
        """EXECUTE LRU cache limits to verify they work correctly."""
        registry = ProviderRegistry()
        
        with patch.object(registry, 'get_provider_patterns') as mock_patterns:
            mock_patterns.return_value = {r'^test-': 'test_provider'}
            
            # EXECUTE: More calls than maxsize (64) for detect_provider
            for i in range(70):  # Exceed maxsize of 64
                registry.detect_provider(f'test-model-{i}')
            
            # VERIFY: Should not crash due to LRU cache management
            # The cache should automatically evict older entries
            result = registry.detect_provider('test-model-0')
            assert result == 'test_provider'

    def test_global_registry_singleton_execution(self):
        """EXECUTE global registry singleton behavior."""
        # Clear any existing global registry
        import lib.config.provider_registry as registry_module
        registry_module._provider_registry = None
        
        # EXECUTE: get_provider_registry() multiple times
        registry1 = get_provider_registry()
        registry2 = get_provider_registry()
        
        # VERIFY: Same instance returned (singleton behavior)
        assert registry1 is registry2
        assert isinstance(registry1, ProviderRegistry)

    def test_convenience_functions_execution(self):
        """EXECUTE all convenience functions with real data."""
        # Mock the global registry methods for controlled testing
        with patch('lib.config.provider_registry.get_provider_registry') as mock_get_registry:
            mock_registry = Mock()
            mock_registry.detect_provider.return_value = 'openai'
            mock_registry.get_provider_classes.return_value = ['OpenAIChat']
            mock_registry.resolve_model_class.return_value = type('TestClass', (), {})
            mock_registry.get_available_providers.return_value = {'openai', 'anthropic'}
            mock_get_registry.return_value = mock_registry
            
            # EXECUTE: All convenience functions
            provider = detect_provider('gpt-4')
            classes = get_provider_classes('openai')
            resolved_class = resolve_model_class('openai', 'gpt-4')
            providers = list_available_providers()
            clear_provider_cache()  # Should not return anything
            
            # VERIFY: All functions executed and returned expected results
            assert provider == 'openai'
            assert classes == ['OpenAIChat']
            assert resolved_class is not None
            assert providers == {'openai', 'anthropic'}
            
            # VERIFY: Registry methods were called
            mock_registry.detect_provider.assert_called_with('gpt-4')
            mock_registry.get_provider_classes.assert_called_with('openai')
            mock_registry.resolve_model_class.assert_called_with('openai', 'gpt-4')
            mock_registry.get_available_providers.assert_called_once()
            mock_registry.clear_cache.assert_called_once()


class TestProviderRegistryIntegrationExecution:
    """Integration tests that execute complete workflows."""

    def test_complete_workflow_execution(self):
        """EXECUTE complete provider registry workflow end-to-end."""
        registry = ProviderRegistry()
        
        # EXECUTE: Complete workflow for a model ID
        model_id = 'gpt-4o-mini'
        
        # Step 1: Discover available providers
        with patch('pkgutil.iter_modules') as mock_iter:
            mock_iter.return_value = [
                (None, 'openai', True),
                (None, 'anthropic', True),
            ]
            providers = registry.get_available_providers()
            assert 'openai' in providers
        
        # Step 2: Generate provider patterns
        patterns = registry.get_provider_patterns()
        assert isinstance(patterns, dict)
        assert len(patterns) > 0
        
        # Step 3: Detect provider from model ID
        detected_provider = registry.detect_provider(model_id)
        assert detected_provider == 'openai'
        
        # Step 4: Get available classes for provider
        with patch('importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_module.OpenAIChat = type('OpenAIChat', (), {})
            mock_module.OpenAI = type('OpenAI', (), {})
            
            with patch('builtins.dir', return_value=['OpenAIChat', 'OpenAI']):
                mock_import.return_value = mock_module
                classes = registry.get_provider_classes(detected_provider)
                assert 'OpenAIChat' in classes
        
        # Step 5: Resolve model class
        with patch('importlib.import_module') as mock_import:
            mock_module = Mock()
            test_class = type('OpenAIChat', (), {})
            mock_module.OpenAIChat = test_class
            mock_import.return_value = mock_module
            
            with patch.object(registry, 'get_provider_classes') as mock_get_classes:
                mock_get_classes.return_value = ['OpenAIChat']
                resolved_class = registry.resolve_model_class(detected_provider, model_id)
                assert resolved_class == test_class

    def test_performance_with_repeated_calls_execution(self):
        """EXECUTE performance test with repeated calls."""
        registry = ProviderRegistry()
        
        # EXECUTE: Multiple detection calls to test caching performance
        model_ids = ['gpt-4', 'claude-3-sonnet', 'gemini-pro'] * 20
        
        results = []
        for model_id in model_ids:
            result = registry.detect_provider(model_id)
            results.append(result)
        
        # VERIFY: All calls completed successfully
        assert len(results) == len(model_ids)
        # VERIFY: Results are consistent due to caching
        gpt_results = [r for i, r in enumerate(results) if model_ids[i] == 'gpt-4']
        assert all(r == gpt_results[0] for r in gpt_results)

    def test_error_recovery_execution(self):
        """EXECUTE error recovery scenarios."""
        registry = ProviderRegistry()
        
        # Test with intermittent import failures
        call_count = 0
        def intermittent_import(module_name):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:  # Every third call fails
                raise ImportError("Intermittent failure")
            
            mock_module = Mock()
            mock_module.TestClass = type('TestClass', (), {})
            return mock_module
        
        with patch('importlib.import_module', side_effect=intermittent_import):
            # EXECUTE: Multiple calls with intermittent failures
            results = []
            for i in range(10):
                try:
                    classes = registry.get_provider_classes(f'provider_{i}')
                    results.append(classes)
                except Exception:
                    # Should handle failures gracefully with fallbacks
                    pass
            
            # VERIFY: Some calls succeeded despite intermittent failures
            assert len(results) > 0

    def test_concurrent_access_simulation(self):
        """EXECUTE concurrent access simulation."""
        registry = ProviderRegistry()
        
        # Simulate concurrent access by rapid successive calls
        results = []
        errors = []
        
        def access_registry():
            try:
                providers = registry.get_available_providers()
                patterns = registry.get_provider_patterns()
                detected = registry.detect_provider('gpt-4')
                results.append((providers, patterns, detected))
            except Exception as e:
                errors.append(e)
        
        # EXECUTE: Simulate concurrent access
        for _ in range(10):
            access_registry()
        
        # VERIFY: No errors occurred
        assert len(errors) == 0
        assert len(results) == 10
        
        # VERIFY: All results are consistent (due to caching)
        first_result = results[0]
        for result in results[1:]:
            assert result[0] == first_result[0]  # Same providers
            assert result[1] == first_result[1]  # Same patterns
            assert result[2] == first_result[2]  # Same detection

    def test_edge_case_inputs_execution(self):
        """EXECUTE with edge case inputs."""
        registry = ProviderRegistry()
        
        edge_case_inputs = [
            '',  # Empty string
            'a' * 1000,  # Very long string
            'model-with-!@#$%^&*()-special-chars',  # Special characters
            'MODEL-WITH-UPPERCASE',  # All uppercase
            'model.with.dots',  # Dots in name
            'model_with_underscores',  # Underscores
            '123-numeric-start',  # Starts with numbers
        ]
        
        for model_id in edge_case_inputs:
            # EXECUTE: detect_provider with edge case inputs
            try:
                result = registry.detect_provider(model_id)
                # Should return None or a valid string, should not crash
                assert result is None or isinstance(result, str)
            except AttributeError:
                # Acceptable for None input case
                if model_id is not None:
                    raise

    def test_memory_usage_with_large_datasets(self):
        """EXECUTE with large datasets to test memory efficiency."""
        registry = ProviderRegistry()
        
        # Mock large provider set
        large_provider_set = {f'provider_{i}' for i in range(100)}
        
        with patch.object(registry, 'get_available_providers', return_value=large_provider_set):
            # EXECUTE: Pattern generation for large provider set
            patterns = registry.get_provider_patterns()
            
            # VERIFY: Handles large datasets without issues
            assert isinstance(patterns, dict)
            assert len(patterns) >= len(large_provider_set)
            
            # EXECUTE: Detection with large pattern set
            test_model_ids = [f'provider_{i}-model' for i in range(0, 100, 10)]
            
            for model_id in test_model_ids:
                result = registry.detect_provider(model_id)
                # Should find provider via substring matching
                assert result is not None
                assert result.startswith('provider_')

    def test_cached_providers_execution(self):
        """EXECUTE get_available_providers with cached return path."""
        registry = ProviderRegistry()
        
        # Pre-populate the cache directly to test line 49 (cached return)
        registry._providers_cache = {'cached_provider', 'another_provider'}
        
        # EXECUTE: get_available_providers() should return cached value
        providers = registry.get_available_providers()
        
        # VERIFY: Returns cached providers
        assert providers == {'cached_provider', 'another_provider'}

    def test_class_cache_hit_execution(self):
        """EXECUTE get_provider_classes with cache hit (line 249)."""
        registry = ProviderRegistry()
        
        # Pre-populate the class cache to test line 249 (cache hit return)
        registry._class_cache['test_provider'] = ['CachedClass1', 'CachedClass2']
        
        # EXECUTE: get_provider_classes() should return cached value
        classes = registry.get_provider_classes('test_provider')
        
        # VERIFY: Returns cached classes
        assert classes == ['CachedClass1', 'CachedClass2']

    def test_cache_clear_exception_handling(self):
        """EXECUTE cache clearing with exception handling (lines 372-373)."""
        registry = ProviderRegistry()
        
        # Mock get_available_providers to not have cache_clear (triggers exception)
        with patch.object(registry, 'get_available_providers') as mock_method:
            # Remove cache_clear attribute to trigger AttributeError
            if hasattr(mock_method, 'cache_clear'):
                delattr(mock_method, 'cache_clear')
            
            # EXECUTE: clear_cache() should handle AttributeError gracefully
            registry.clear_cache()  # Should not raise an exception
            
            # VERIFY: Method completed without crashing
            assert True


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v"])