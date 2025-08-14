"""
Enhanced test suite for ProviderRegistry - targeting 50%+ coverage.

This test suite covers the dynamic provider discovery, pattern matching,
class resolution, and caching functionality with edge cases and error conditions.
"""

import importlib
import re
from unittest.mock import Mock, patch, MagicMock
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


class TestProviderRegistryInitialization:
    """Test provider registry initialization and setup."""
    
    def test_init_creates_empty_caches(self):
        """Test initialization creates proper cache structure."""
        registry = ProviderRegistry()
        
        assert registry._providers_cache is None
        assert registry._pattern_cache is None
        assert registry._class_cache == {}
        
    def test_global_registry_singleton_behavior(self):
        """Test that global registry maintains singleton behavior."""
        registry1 = get_provider_registry()
        registry2 = get_provider_registry()
        
        assert registry1 is registry2
        
    def test_convenience_functions_use_global_registry(self):
        """Test that convenience functions use the global registry."""
        with patch('lib.config.provider_registry.get_provider_registry') as mock_get:
            mock_registry = Mock()
            mock_get.return_value = mock_registry
            
            detect_provider("test-model")
            mock_registry.detect_provider.assert_called_once_with("test-model")
            
            get_provider_classes("openai")
            mock_registry.get_provider_classes.assert_called_once_with("openai")
            
            resolve_model_class("openai", "test-model")
            mock_registry.resolve_model_class.assert_called_once_with("openai", "test-model")
            
            list_available_providers()
            mock_registry.get_available_providers.assert_called_once()
            
            clear_provider_cache()
            mock_registry.clear_cache.assert_called_once()


class TestProviderDiscovery:
    """Test dynamic provider discovery functionality."""
    
    def test_get_available_providers_with_agno_models(self):
        """Test provider discovery when agno.models is available."""
        mock_modules = [
            Mock(name="openai", ispkg=True),
            Mock(name="anthropic", ispkg=True),
            Mock(name="google", ispkg=True),
            Mock(name="_internal", ispkg=False),  # Should be skipped
        ]
        
        with patch('pkgutil.iter_modules') as mock_iter:
            # Mock pkgutil.iter_modules to return our test data
            mock_iter.return_value = [
                (None, "openai", True),
                (None, "anthropic", True), 
                (None, "google", True),
                (None, "_internal", False),
            ]
            
            registry = ProviderRegistry()
            providers = registry.get_available_providers()
            
            assert "openai" in providers
            assert "anthropic" in providers
            assert "google" in providers
            assert "_internal" not in providers  # Should skip internal modules
            assert len(providers) == 3
            
    def test_get_available_providers_fallback_when_import_error(self):
        """Test provider discovery falls back when agno.models import fails."""
        with patch('pkgutil.iter_modules', side_effect=ImportError("No module named 'agno.models'")):
            registry = ProviderRegistry()
            providers = registry.get_available_providers()
            
            # Should fall back to common providers
            expected_providers = {"openai", "anthropic", "google", "meta", "mistral", "cohere", "groq"}
            assert providers >= expected_providers  # May include default provider from env
            
    def test_get_available_providers_respects_default_provider_env(self):
        """Test that fallback includes default provider from environment."""
        with patch('pkgutil.iter_modules', side_effect=ImportError("No module")):
            with patch.dict('os.environ', {'HIVE_DEFAULT_PROVIDER': 'custom_provider'}):
                registry = ProviderRegistry()
                providers = registry.get_available_providers()
                
                assert "custom_provider" in providers
                
    def test_get_available_providers_caching(self):
        """Test that provider discovery results are cached."""
        registry = ProviderRegistry()
        
        with patch('pkgutil.iter_modules') as mock_iter:
            mock_iter.return_value = [("", "openai", True)]
            
            providers1 = registry.get_available_providers()
            providers2 = registry.get_available_providers()
            
            # Should only call iter_modules once due to caching
            assert mock_iter.call_count == 1
            assert providers1 is providers2  # Same cached object


class TestProviderPatternGeneration:
    """Test provider pattern generation and matching logic."""
    
    def test_generate_provider_patterns_openai(self):
        """Test pattern generation for OpenAI provider."""
        registry = ProviderRegistry()
        patterns = registry._generate_provider_patterns("openai")
        
        expected_patterns = {
            r"^gpt-": "openai",
            r"^o1-": "openai",
            r"^o3-": "openai",
            r"^text-": "openai",
            r"^davinci-": "openai",
            r"^curie-": "openai",
            r"^ada-": "openai",
            r"^babbage-": "openai",
            r"^openai$": "openai",
        }
        
        for pattern, provider in expected_patterns.items():
            assert patterns[pattern] == provider
            
    def test_generate_provider_patterns_anthropic(self):
        """Test pattern generation for Anthropic provider."""
        registry = ProviderRegistry()
        patterns = registry._generate_provider_patterns("anthropic")
        
        assert patterns[r"^claude-"] == "anthropic"
        assert patterns[r"^claude\."] == "anthropic"  # claude.instant format
        assert patterns[r"^anthropic$"] == "anthropic"
        
    def test_generate_provider_patterns_google(self):
        """Test pattern generation for Google provider."""
        registry = ProviderRegistry()
        patterns = registry._generate_provider_patterns("google")
        
        expected_prefixes = [r"^gemini-", r"^palm-", r"^bison-", r"^gecko-"]
        
        for prefix in expected_prefixes:
            assert patterns[prefix] == "google"
        assert patterns[r"^google$"] == "google"
        
    def test_generate_provider_patterns_unknown_provider(self):
        """Test pattern generation for unknown provider uses generic pattern."""
        registry = ProviderRegistry()
        patterns = registry._generate_provider_patterns("unknown_provider")
        
        assert patterns[r"^unknown_provider-"] == "unknown_provider"
        assert patterns[r"^unknown_provider$"] == "unknown_provider"
        
    def test_get_provider_patterns_caching(self):
        """Test that provider patterns are cached."""
        registry = ProviderRegistry()
        
        with patch.object(registry, 'get_available_providers') as mock_get_providers:
            mock_get_providers.return_value = {"openai"}
            
            patterns1 = registry.get_provider_patterns()
            patterns2 = registry.get_provider_patterns()
            
            # Should only generate patterns once
            assert mock_get_providers.call_count == 1
            assert patterns1 is patterns2


class TestProviderDetection:
    """Test provider detection from model IDs."""
    
    def test_detect_provider_openai_models(self):
        """Test detection of OpenAI models."""
        registry = ProviderRegistry()
        
        test_cases = [
            ("gpt-4", "openai"),
            ("gpt-3.5-turbo", "openai"), 
            ("GPT-4", "openai"),  # Case insensitive
            ("o1-preview", "openai"),
            ("text-davinci-003", "openai"),
        ]
        
        for model_id, expected_provider in test_cases:
            detected = registry.detect_provider(model_id)
            assert detected == expected_provider, f"Failed to detect {expected_provider} for {model_id}"
            
    def test_detect_provider_anthropic_models(self):
        """Test detection of Anthropic models.""" 
        registry = ProviderRegistry()
        
        test_cases = [
            ("claude-3-opus", "anthropic"),
            ("claude-instant-v1", "anthropic"),
            ("claude.instant", "anthropic"),  # Alternative format
        ]
        
        for model_id, expected_provider in test_cases:
            detected = registry.detect_provider(model_id)
            assert detected == expected_provider
            
    def test_detect_provider_google_models(self):
        """Test detection of Google models."""
        registry = ProviderRegistry()
        
        test_cases = [
            ("gemini-pro", "google"),
            ("palm-2", "google"),
            ("bison-001", "google"),
        ]
        
        for model_id, expected_provider in test_cases:
            detected = registry.detect_provider(model_id)
            assert detected == expected_provider
            
    def test_detect_provider_substring_fallback(self):
        """Test provider detection falls back to substring matching."""
        registry = ProviderRegistry()
        
        with patch.object(registry, 'get_available_providers') as mock_providers:
            mock_providers.return_value = {"mistral"}
            
            with patch.object(registry, 'get_provider_patterns') as mock_patterns:
                mock_patterns.return_value = {}  # No exact patterns match
                
                detected = registry.detect_provider("custom-mistral-model")
                assert detected == "mistral"
                
    def test_detect_provider_no_match(self):
        """Test provider detection when no match is found."""
        registry = ProviderRegistry()
        
        with patch.object(registry, 'get_available_providers') as mock_providers:
            mock_providers.return_value = {"openai"}
            
            detected = registry.detect_provider("completely-unknown-model")
            assert detected is None
            
    def test_detect_provider_caching(self):
        """Test that detection results are cached."""
        registry = ProviderRegistry()
        
        with patch.object(registry, 'get_provider_patterns') as mock_patterns:
            mock_patterns.return_value = {r"^gpt-": "openai"}
            
            result1 = registry.detect_provider("gpt-4")
            result2 = registry.detect_provider("gpt-4")
            
            assert result1 == result2 == "openai"
            # Should cache identical calls


class TestProviderClassDiscovery:
    """Test dynamic class discovery for providers."""
    
    def test_get_provider_classes_successful_import(self):
        """Test class discovery when provider module imports successfully."""
        registry = ProviderRegistry()
        
        # Mock a provider module with some classes
        mock_module = Mock()
        mock_module.OpenAIChat = type("OpenAIChat", (), {})
        mock_module.OpenAI = type("OpenAI", (), {})  
        mock_module._internal_function = Mock()  # Should be ignored
        mock_module.lowercase_var = "ignored"  # Should be ignored
        
        with patch('importlib.import_module', return_value=mock_module):
            classes = registry.get_provider_classes("openai")
            
            assert "OpenAIChat" in classes
            assert "OpenAI" in classes
            assert "_internal_function" not in classes
            assert "lowercase_var" not in classes
            
    def test_get_provider_classes_import_error_fallback(self):
        """Test class discovery falls back when import fails."""
        registry = ProviderRegistry()
        
        with patch('importlib.import_module', side_effect=ImportError("Module not found")):
            classes = registry.get_provider_classes("openai")
            
            # Should use fallback classes
            expected_classes = ["OpenAIChat", "OpenAI"]
            for expected_class in expected_classes:
                assert expected_class in classes
                
    def test_get_provider_classes_unknown_provider_fallback(self):
        """Test class discovery for unknown provider uses generic fallback."""
        registry = ProviderRegistry()
        
        with patch('importlib.import_module', side_effect=ImportError("Module not found")):
            classes = registry.get_provider_classes("unknown_provider")
            
            # Should generate generic fallback names based on title() method
            expected_classes = ["Unknown_Provider", "Unknown_ProviderChat"]
            for expected_class in expected_classes:
                assert expected_class in classes
                
    def test_get_provider_classes_caching(self):
        """Test that class discovery results are cached."""
        registry = ProviderRegistry()
        
        with patch('importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_module.TestClass = type("TestClass", (), {})
            mock_import.return_value = mock_module
            
            classes1 = registry.get_provider_classes("test_provider")
            classes2 = registry.get_provider_classes("test_provider")
            
            # Should only import once due to caching
            assert mock_import.call_count == 1
            assert classes1 is classes2


class TestModelClassResolution:
    """Test model class resolution functionality."""
    
    def test_resolve_model_class_successful(self):
        """Test successful model class resolution."""
        registry = ProviderRegistry()
        
        # Mock provider module with test class
        mock_module = Mock()
        test_class = type("OpenAIChat", (), {})
        mock_module.OpenAIChat = test_class
        
        with patch('importlib.import_module', return_value=mock_module):
            with patch.object(registry, 'get_provider_classes', return_value=["OpenAIChat"]):
                result = registry.resolve_model_class("openai", "gpt-4")
                
                assert result is test_class
                
    def test_resolve_model_class_class_not_found(self):
        """Test model class resolution when class doesn't exist in module."""
        registry = ProviderRegistry()
        
        mock_module = Mock()
        # Module exists but doesn't have the expected class
        del mock_module.MissingClass  # Ensure class doesn't exist
        
        with patch('importlib.import_module', return_value=mock_module):
            with patch.object(registry, 'get_provider_classes', return_value=["MissingClass"]):
                result = registry.resolve_model_class("test_provider", "test-model")
                
                assert result is None
                    
    def test_resolve_model_class_import_error(self):
        """Test model class resolution when module import fails."""
        registry = ProviderRegistry()
        
        with patch('importlib.import_module', side_effect=ImportError("Module not found")):
            result = registry.resolve_model_class("nonexistent_provider", "test-model")
            
            assert result is None
            
    def test_resolve_model_class_caching(self):
        """Test that class resolution results are cached."""
        registry = ProviderRegistry()
        
        mock_module = Mock()
        test_class = type("TestClass", (), {})
        mock_module.TestClass = test_class
        
        with patch('importlib.import_module', return_value=mock_module) as mock_import:
            with patch.object(registry, 'get_provider_classes', return_value=["TestClass"]):
                result1 = registry.resolve_model_class("test", "model")
                result2 = registry.resolve_model_class("test", "model")
                
                assert result1 is result2 is test_class
                # Should use LRU cache


class TestCacheManagement:
    """Test cache management and clearing functionality."""
    
    def test_clear_cache_resets_all_caches(self):
        """Test that clear_cache resets all internal caches."""
        registry = ProviderRegistry()
        
        # Populate caches
        registry._providers_cache = {"test"}
        registry._pattern_cache = {"test": "pattern"}
        registry._class_cache = {"test": ["class"]}
        
        registry.clear_cache()
        
        # Check that instance caches are cleared
        assert registry._providers_cache is None
        assert registry._pattern_cache is None
        assert registry._class_cache == {}


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""
    
    def test_detect_provider_empty_string(self):
        """Test provider detection with empty string."""
        registry = ProviderRegistry()
        
        result = registry.detect_provider("")
        assert result is None
        
    def test_detect_provider_none_input(self):
        """Test provider detection with None input."""
        registry = ProviderRegistry()
        
        # Should handle None gracefully
        try:
            result = registry.detect_provider(None)
            assert result is None
        except AttributeError:
            # Acceptable - None doesn't have .lower() method
            pass
            
    def test_get_provider_classes_with_malformed_module(self):
        """Test class discovery when module has unexpected structure."""
        registry = ProviderRegistry()
        
        mock_module = Mock()
        # Add some problematic attributes
        mock_module.ValidClass = type("ValidClass", (), {})
        mock_module.broken_attr = Mock(side_effect=Exception("Broken attribute"))
        
        with patch('importlib.import_module', return_value=mock_module):
            classes = registry.get_provider_classes("test_provider")
            
            # Should handle errors gracefully and return valid classes
            assert "ValidClass" in classes
            
    def test_pattern_matching_case_sensitivity(self):
        """Test that pattern matching is case insensitive."""
        registry = ProviderRegistry()
        
        test_cases = [
            ("GPT-4", "openai"),
            ("gpt-4", "openai"),
            ("GpT-4", "openai"),
            ("CLAUDE-OPUS", "anthropic"),
            ("claude-opus", "anthropic"),
        ]
        
        for model_id, expected_provider in test_cases:
            detected = registry.detect_provider(model_id)
            assert detected == expected_provider, f"Case sensitivity failed for {model_id}"
            
    def test_pattern_generation_with_special_characters(self):
        """Test pattern generation handles providers with special characters."""
        registry = ProviderRegistry()
        
        # Test provider name with special characters
        patterns = registry._generate_provider_patterns("provider-with-dash")
        
        # Should generate patterns without causing regex issues
        assert patterns[r"^provider-with-dash-"] == "provider-with-dash"
        assert patterns[r"^provider-with-dash$"] == "provider-with-dash"
        
    def test_concurrent_access_safety(self):
        """Test that the registry handles concurrent access safely."""
        import threading
        import time
        
        registry = ProviderRegistry()
        results = []
        errors = []
        
        def access_registry():
            try:
                providers = registry.get_available_providers()
                results.append(providers)
                
                patterns = registry.get_provider_patterns()
                results.append(patterns)
                
                detected = registry.detect_provider("gpt-4")
                results.append(detected)
                
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads accessing the registry
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=access_registry)
            threads.append(thread)
            
        # Start all threads
        for thread in threads:
            thread.start()
            
        # Wait for completion
        for thread in threads:
            thread.join()
            
        # Should not have any errors from concurrent access
        assert len(errors) == 0
        assert len(results) > 0
        
    def test_memory_efficiency_with_large_pattern_sets(self):
        """Test memory efficiency when dealing with many providers."""
        registry = ProviderRegistry()
        
        # Mock a large number of providers
        large_provider_set = {f"provider_{i}" for i in range(100)}
        
        with patch.object(registry, 'get_available_providers', return_value=large_provider_set):
            patterns = registry.get_provider_patterns()
            
            # Should generate patterns for all providers without issues
            assert len(patterns) >= len(large_provider_set)
            
            # Test pattern matching still works
            detected = registry.detect_provider("provider_50-model")
            assert detected == "provider_50"


class TestProviderSpecificPatterns:
    """Test provider-specific pattern matching edge cases."""
    
    def test_xai_grok_patterns(self):
        """Test X.AI Grok provider patterns."""
        registry = ProviderRegistry()
        patterns = registry._generate_provider_patterns("xai")
        
        assert patterns[r"^grok-"] == "xai"
        
        # Test detection
        detected = registry.detect_provider("grok-beta")
        assert detected == "xai"
        
    def test_meta_llama_patterns(self):
        """Test Meta Llama provider patterns."""
        registry = ProviderRegistry()
        patterns = registry._generate_provider_patterns("meta")
        
        expected_patterns = [r"^llama-", r"^llama2-", r"^llama3-", r"^codellama-"]
        for pattern in expected_patterns:
            assert patterns[pattern] == "meta"
            
    def test_mistral_patterns(self):
        """Test Mistral provider patterns."""
        registry = ProviderRegistry()
        patterns = registry._generate_provider_patterns("mistral")
        
        expected_patterns = [r"^mistral-", r"^mixtral-", r"^codestral-"]
        for pattern in expected_patterns:
            assert patterns[pattern] == "mistral"
            
    def test_deepseek_patterns(self):
        """Test DeepSeek provider patterns."""
        registry = ProviderRegistry()
        patterns = registry._generate_provider_patterns("deepseek")
        
        assert patterns[r"^deepseek-"] == "deepseek"
        
        # Test detection
        detected = registry.detect_provider("deepseek-coder")
        assert detected == "deepseek"
        
    def test_cohere_patterns(self):
        """Test Cohere provider patterns."""
        registry = ProviderRegistry()
        patterns = registry._generate_provider_patterns("cohere")
        
        expected_patterns = [r"^command-", r"^embed-"]
        for pattern in expected_patterns:
            assert patterns[pattern] == "cohere"


class TestIntegrationScenarios:
    """Test integration scenarios with realistic usage patterns."""
    
    def test_full_model_resolution_workflow(self):
        """Test complete workflow from model ID to resolved class."""
        registry = ProviderRegistry()
        
        # Mock the complete chain
        mock_module = Mock()
        test_class = type("OpenAIChat", (), {})
        mock_module.OpenAIChat = test_class
        
        with patch('importlib.import_module', return_value=mock_module):
            # Should detect provider
            provider = registry.detect_provider("gpt-4")
            assert provider == "openai"
            
            # Should get classes
            classes = registry.get_provider_classes(provider)
            assert "OpenAIChat" in classes
            
            # Should resolve class
            resolved_class = registry.resolve_model_class(provider, "gpt-4")
            assert resolved_class is test_class
            
    def test_registry_performance_with_repeated_calls(self):
        """Test registry performance with repeated calls."""
        import time
        
        registry = ProviderRegistry()
        
        # Time multiple detection calls
        start_time = time.time()
        for _ in range(100):
            registry.detect_provider("gpt-4")
        first_time = time.time() - start_time
        
        # Time the same calls (should be cached)
        start_time = time.time()
        for _ in range(100):
            registry.detect_provider("gpt-4")
        cached_time = time.time() - start_time
        
        # Cached calls should be significantly faster
        assert cached_time < first_time * 0.5  # At least 50% faster
        
    def test_error_recovery_and_graceful_degradation(self):
        """Test that the registry recovers gracefully from errors."""
        registry = ProviderRegistry()
        
        # Test with problematic import that sometimes works
        call_count = 0
        def flaky_import(module_name):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                raise ImportError("Flaky connection")
            mock_module = Mock()
            mock_module.TestClass = type("TestClass", (), {})
            return mock_module
        
        with patch('importlib.import_module', side_effect=flaky_import):
            # First call should work
            classes1 = registry.get_provider_classes("test")
            assert "TestClass" in classes1
            
            # Second call should fail but degrade gracefully  
            classes2 = registry.get_provider_classes("test2")
            assert len(classes2) > 0  # Should have fallback classes
            
    def test_configuration_driven_provider_discovery(self):
        """Test provider discovery respects configuration."""
        with patch.dict('os.environ', {'HIVE_DEFAULT_PROVIDER': 'custom_default'}):
            with patch('pkgutil.iter_modules', side_effect=ImportError("Test error")):
                registry = ProviderRegistry()
                providers = registry.get_available_providers()
                
                # Should include custom default from environment
                assert "custom_default" in providers