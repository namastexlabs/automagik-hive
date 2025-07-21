"""
Dynamic Provider Registry for Agno Model Resolution
=================================================

Zero-configuration provider registry that automatically discovers ALL Agno providers
through runtime module introspection. Eliminates hardcoded provider patterns and
class mappings while maintaining full compatibility with existing code.

Architecture:
- Dynamic provider discovery via pkgutil scanning of agno.models namespace
- Intelligent pattern matching for model ID → provider detection  
- Dynamic class discovery with smart naming pattern recognition
- Efficient caching with graceful fallbacks

Follows the same dynamic discovery patterns as teams/registry.py and agents/registry.py.
"""

import pkgutil
import importlib
import re
from typing import Dict, List, Optional, Type, Set
from functools import lru_cache
from lib.logging import logger


class ProviderRegistry:
    """
    Dynamic provider registry that auto-discovers Agno providers at runtime.
    
    This registry eliminates the need for hardcoded provider patterns and class
    mappings by intelligently scanning the Agno framework for available providers
    and dynamically generating appropriate detection patterns.
    """
    
    def __init__(self):
        self._providers_cache: Optional[Set[str]] = None
        self._pattern_cache: Optional[Dict[str, str]] = None
        self._class_cache: Dict[str, List[str]] = {}
    
    @lru_cache(maxsize=None)
    def get_available_providers(self) -> Set[str]:
        """
        Dynamically discover all available Agno providers by scanning the module namespace.
        
        Returns:
            Set of provider names (e.g., {'openai', 'anthropic', 'google', ...})
        """
        if self._providers_cache is not None:
            return self._providers_cache
            
        providers = set()
        
        try:
            # Scan agno.models namespace for provider modules
            import agno.models
            
            for importer, modname, ispkg in pkgutil.iter_modules(agno.models.__path__):
                # Skip internal modules, keep packages (actual providers)
                if not modname.startswith('_') and ispkg:
                    providers.add(modname)
                    logger.debug("🔧 Discovered provider", provider=modname)
            
            logger.info("🔧 Provider discovery complete", 
                       provider_count=len(providers), 
                       providers=sorted(providers))
                       
        except ImportError as e:
            logger.warning("🔧 Agno models module not available, using fallback providers", error=str(e))
            # Fallback to common providers if Agno isn't available
            providers = {'openai', 'anthropic', 'google', 'meta', 'mistral', 'cohere', 'groq'}
        
        self._providers_cache = providers
        return providers
    
    @lru_cache(maxsize=128)
    def get_provider_patterns(self) -> Dict[str, str]:
        """
        Generate dynamic provider detection patterns based on discovered providers.
        
        Returns:
            Dictionary mapping regex patterns to provider names
        """
        if self._pattern_cache is not None:
            return self._pattern_cache
            
        patterns = {}
        providers = self.get_available_providers()
        
        # Generate intelligent patterns for each discovered provider
        for provider in providers:
            provider_patterns = self._generate_provider_patterns(provider)
            patterns.update(provider_patterns)
            
        logger.debug("🔧 Generated provider patterns", pattern_count=len(patterns))
        self._pattern_cache = patterns
        return patterns
    
    def _generate_provider_patterns(self, provider: str) -> Dict[str, str]:
        """
        Generate regex patterns for a specific provider based on common naming conventions.
        
        Args:
            provider: Provider name (e.g., 'openai')
            
        Returns:
            Dictionary of patterns for this provider
        """
        patterns = {}
        
        # Provider-specific pattern generation
        if provider == 'openai':
            patterns.update({
                r'^gpt-': provider,
                r'^o1-': provider,
                r'^o3-': provider,
                r'^text-': provider,
                r'^davinci-': provider,
                r'^curie-': provider,
                r'^ada-': provider,
                r'^babbage-': provider
            })
        elif provider == 'anthropic':
            patterns.update({
                r'^claude-': provider,
                r'^claude\.': provider  # claude.instant format
            })
        elif provider == 'google':
            patterns.update({
                r'^gemini-': provider,
                r'^palm-': provider,
                r'^bison-': provider,
                r'^gecko-': provider
            })
        elif provider == 'xai':
            patterns.update({
                r'^grok-': provider
            })
        elif provider == 'meta':
            patterns.update({
                r'^llama-': provider,
                r'^llama2-': provider,
                r'^llama3-': provider,
                r'^codellama-': provider
            })
        elif provider == 'mistral':
            patterns.update({
                r'^mistral-': provider,
                r'^mixtral-': provider,
                r'^codestral-': provider
            })
        elif provider == 'cohere':
            patterns.update({
                r'^command-': provider,
                r'^embed-': provider
            })
        elif provider == 'deepseek':
            patterns.update({
                r'^deepseek-': provider
            })
        elif provider == 'groq':
            patterns.update({
                r'^groq-': provider
            })
        else:
            # Generic pattern for unknown providers
            patterns[f'^{provider}-'] = provider
            
        # Add provider name as exact match pattern
        patterns[f'^{provider}$'] = provider
        
        return patterns
    
    @lru_cache(maxsize=64)
    def detect_provider(self, model_id: str) -> Optional[str]:
        """
        Detect provider from model ID using dynamically generated patterns.
        
        Args:
            model_id: Model identifier (e.g., "gpt-4o-mini")
            
        Returns:
            Provider name or None if not detected
        """
        patterns = self.get_provider_patterns()
        model_lower = model_id.lower()
        
        # Try exact pattern matches first
        for pattern, provider in patterns.items():
            if re.match(pattern, model_lower, re.IGNORECASE):
                logger.debug("🔧 Provider detected", model_id=model_id, provider=provider, pattern=pattern)
                return provider
        
        # Fallback: substring matching for common cases
        for provider in self.get_available_providers():
            if provider in model_lower:
                logger.debug("🔧 Provider detected via substring", model_id=model_id, provider=provider)
                return provider
        
        logger.debug("🔧 Provider detection failed", model_id=model_id, 
                    available_providers=sorted(self.get_available_providers()))
        return None
    
    @lru_cache(maxsize=64)
    def get_provider_classes(self, provider: str) -> List[str]:
        """
        Dynamically discover model classes for a given provider.
        
        Args:
            provider: Provider name (e.g., 'openai')
            
        Returns:
            List of class names available for this provider
        """
        if provider in self._class_cache:
            return self._class_cache[provider]
            
        classes = []
        
        try:
            # Import the provider module
            module_path = f"agno.models.{provider}"
            module = importlib.import_module(module_path)
            
            # Find all classes in the module (uppercase names)
            for attr_name in dir(module):
                if not attr_name.startswith('_') and attr_name[0].isupper():
                    attr = getattr(module, attr_name)
                    # Check if it's a class and likely a model class
                    if isinstance(attr, type):
                        classes.append(attr_name)
            
            logger.debug("🔧 Discovered classes for provider", 
                        provider=provider, classes=classes)
                        
        except ImportError as e:
            logger.warning("🔧 Failed to import provider module", 
                          provider=provider, error=str(e))
            # Fallback class names for common providers
            classes = self._get_fallback_classes(provider)
        
        # Cache the result
        self._class_cache[provider] = classes
        return classes
    
    def _get_fallback_classes(self, provider: str) -> List[str]:
        """
        Provide fallback class names when module introspection fails.
        
        Args:
            provider: Provider name
            
        Returns:
            List of likely class names for the provider
        """
        fallback_classes = {
            'openai': ['OpenAIChat', 'OpenAI'],
            'anthropic': ['Claude'],
            'google': ['Gemini', 'GoogleChat'],
            'xai': ['Grok'],
            'meta': ['Llama'],
            'mistral': ['Mistral'],
            'cohere': ['Cohere'],
            'deepseek': ['DeepSeek'],
            'groq': ['Groq']
        }
        
        return fallback_classes.get(provider, [provider.title(), f"{provider.title()}Chat"])
    
    @lru_cache(maxsize=64)
    def resolve_model_class(self, provider: str, model_id: str) -> Optional[Type]:
        """
        Resolve the appropriate model class for a provider and model ID.
        
        Args:
            provider: Provider name
            model_id: Model identifier (for error context)
            
        Returns:
            Model class or None if not found
        """
        try:
            module_path = f"agno.models.{provider}"
            module = importlib.import_module(module_path)
            
            # Get candidate class names
            class_candidates = self.get_provider_classes(provider)
            
            # Try to find the model class
            for class_name in class_candidates:
                if hasattr(module, class_name):
                    model_class = getattr(module, class_name)
                    logger.debug("🔧 Model class resolved", 
                               provider=provider, class_name=class_name, 
                               model_id=model_id)
                    return model_class
            
            # If no specific class found, log available classes for debugging
            available_classes = [name for name in dir(module) 
                               if not name.startswith('_') and name[0].isupper()]
            logger.warning("🔧 No suitable model class found", 
                          provider=provider, model_id=model_id,
                          candidates=class_candidates, 
                          available=available_classes)
            return None
            
        except ImportError as e:
            logger.error("🔧 Provider module import failed", 
                        provider=provider, model_id=model_id, error=str(e))
            return None
    
    def clear_cache(self):
        """Clear all cached provider data."""
        self._providers_cache = None
        self._pattern_cache = None
        self._class_cache.clear()
        
        # Clear function caches
        self.get_available_providers.cache_clear()
        self.get_provider_patterns.cache_clear()
        self.detect_provider.cache_clear()
        self.get_provider_classes.cache_clear()
        self.resolve_model_class.cache_clear()
        
        logger.debug("🔧 Provider registry cache cleared")


# Global registry instance
_provider_registry: Optional[ProviderRegistry] = None

def get_provider_registry() -> ProviderRegistry:
    """Get or create the global provider registry instance."""
    global _provider_registry
    if _provider_registry is None:
        _provider_registry = ProviderRegistry()
    return _provider_registry

# Convenience functions for backward compatibility
def detect_provider(model_id: str) -> Optional[str]:
    """Detect provider from model ID."""
    return get_provider_registry().detect_provider(model_id)

def get_provider_classes(provider: str) -> List[str]:
    """Get available classes for a provider."""
    return get_provider_registry().get_provider_classes(provider)

def resolve_model_class(provider: str, model_id: str) -> Optional[Type]:
    """Resolve model class for provider."""
    return get_provider_registry().resolve_model_class(provider, model_id)

def list_available_providers() -> Set[str]:
    """List all available providers."""
    return get_provider_registry().get_available_providers()

def clear_provider_cache():
    """Clear provider registry cache."""
    get_provider_registry().clear_cache()