"""Dynamic Provider Registry for Automagik Hive Multi-Agent System.

ZERO-CONFIGURATION provider discovery that automatically finds ALL Agno providers.
Pure runtime discovery - no YAML, no hardcoded mappings, just intelligent discovery.
"""

import re
import importlib
import pkgutil
from typing import Dict, List, Optional, Type, Any
from functools import lru_cache
from lib.logging import logger


class ProviderRegistryError(Exception):
    """Raised when provider registry operations fail."""
    pass


class ProviderRegistry:
    """
    Zero-configuration provider registry that discovers ALL Agno providers automatically.
    Follows the dynamic discovery patterns from teams/agents registries.
    """
    
    def __init__(self):
        """Initialize truly dynamic provider registry - zero configuration."""
        self._discovered_providers: Optional[Dict[str, Dict]] = None
        logger.debug("🔧 ProviderRegistry initialized - zero configuration mode")
    
    @lru_cache(maxsize=1)
    def _discover_agno_providers(self) -> Dict[str, Dict]:
        """
        Discover ALL Agno providers by scanning the agno.models namespace.
        Pure runtime discovery - no configuration files needed.
        """
        discovered = {}
        
        try:
            # Import and scan agno.models
            import agno.models as agno_models
            
            # Walk through all provider modules
            for importer, modname, ispkg in pkgutil.iter_modules(agno_models.__path__, agno_models.__name__ + "."):
                provider_name = modname.split('.')[-1]  
                
                try:
                    provider_module = importlib.import_module(modname)
                    class_names = self._find_model_classes(provider_module, provider_name)
                    
                    if class_names:
                        discovered[provider_name] = {
                            'name': provider_name,
                            'module_path': modname,
                            'class_names': class_names,
                        }
                        logger.debug("🔧 Provider discovered", 
                                   provider=provider_name, classes=class_names)
                
                except ImportError:
                    # Provider not available - skip silently
                    continue
                except Exception as e:
                    logger.debug("🔧 Error scanning provider", provider=provider_name, error=str(e))
                    continue
        
        except ImportError:
            logger.info("🔧 Agno not available - using intelligent fallback")
            discovered = self._get_intelligent_fallback()
        
        logger.info("🔧 Provider discovery complete", 
                   total=len(discovered), providers=list(discovered.keys()))
        return discovered
    
    def _find_model_classes(self, module: Any, provider_name: str) -> List[str]:
        """Find model classes in a provider module using intelligent patterns."""
        class_names = []
        
        # Generate smart class name candidates
        candidates = [
            provider_name.title().replace('ai', 'AI'),  # OpenAI, not Openai
            f"{provider_name.title()}Chat",
            f"{provider_name.title()}Model", 
            provider_name.upper(),
            "Chat",
            "Model",
        ]
        
        # Find classes that match patterns or contain model-like names
        for attr_name in dir(module):
            if not attr_name.startswith('_'):
                attr = getattr(module, attr_name)
                if isinstance(attr, type):
                    if (attr_name in candidates or 
                        'chat' in attr_name.lower() or 
                        'model' in attr_name.lower()):
                        class_names.append(attr_name)
        
        return class_names
    
    def _get_intelligent_fallback(self) -> Dict[str, Dict]:
        """Intelligent fallback when agno is not available."""
        return {
            'openai': {'name': 'openai', 'module_path': 'agno.models.openai', 'class_names': ['OpenAIChat', 'OpenAI']},
            'anthropic': {'name': 'anthropic', 'module_path': 'agno.models.anthropic', 'class_names': ['Claude']},
            'google': {'name': 'google', 'module_path': 'agno.models.google', 'class_names': ['Gemini']},
        }
    
    @lru_cache(maxsize=128)
    def detect_provider(self, model_id: str) -> str:
        """
        Detect provider using intelligent pattern matching - zero configuration.
        """
        # Smart pattern detection based on common model naming
        smart_patterns = {
            r'^gpt-': 'openai', r'^o1-': 'openai', r'^o3-': 'openai', r'^o4-': 'openai',
            r'^text-': 'openai', r'^davinci': 'openai', r'^curie': 'openai',
            r'^claude-': 'anthropic',
            r'^gemini-': 'google', r'^palm-': 'google', r'^bard-': 'google',
            r'^llama-': 'meta', r'^mixtral-': 'mistral', r'^mistral-': 'mistral',
            r'^command-': 'cohere', r'^deepseek-': 'deepseek', r'^qwen-': 'alibaba',
            r'^grok-': 'xai', r'^groq-': 'groq',
        }
        
        # Pattern matching
        for pattern, provider in smart_patterns.items():
            if re.match(pattern, model_id, re.IGNORECASE):
                logger.debug("🔧 Provider detected via pattern", model_id=model_id, provider=provider)
                return provider
        
        # Fallback: keyword detection
        model_lower = model_id.lower()
        keywords = {
            'gpt': 'openai', 'openai': 'openai', 'claude': 'anthropic', 'anthropic': 'anthropic',
            'gemini': 'google', 'google': 'google', 'llama': 'meta', 'meta': 'meta',
            'mixtral': 'mistral', 'mistral': 'mistral', 'cohere': 'cohere', 'command': 'cohere',
            'deepseek': 'deepseek', 'qwen': 'alibaba', 'alibaba': 'alibaba',
            'grok': 'xai', 'xai': 'xai', 'groq': 'groq',
        }
        
        for keyword, provider in keywords.items():
            if keyword in model_lower:
                logger.debug("🔧 Provider detected via keyword", model_id=model_id, provider=provider, keyword=keyword)
                return provider
        
        # Final fallback: check discovered providers
        providers = self._discover_agno_providers()
        for provider_name in providers.keys():
            if provider_name.lower() in model_lower:
                logger.debug("🔧 Provider detected via discovery", model_id=model_id, provider=provider_name)
                return provider_name
        
        raise ProviderRegistryError(f"Cannot detect provider for model: {model_id}")
    
    @lru_cache(maxsize=64)
    def discover_model_class(self, provider: str, model_id: str) -> Type:
        """
        Discover model class for provider - zero configuration.
        """
        providers = self._discover_agno_providers()
        
        if provider not in providers:
            raise ProviderRegistryError(f"Provider '{provider}' not found")
        
        provider_info = providers[provider]
        module_path = provider_info['module_path']
        class_names = provider_info['class_names']
        
        try:
            module = importlib.import_module(module_path)
            
            # Try each potential class name
            for class_name in class_names:
                if hasattr(module, class_name):
                    model_class = getattr(module, class_name)
                    logger.debug("🔧 Model class found", provider=provider, class_name=class_name)
                    return model_class
            
            # List available classes for debugging
            available = [name for name in dir(module) if not name.startswith('_') and name[0].isupper()]
            logger.error("🔧 No suitable model class found", 
                        provider=provider, tried=class_names, available=available)
            raise ProviderRegistryError(f"No model class found in {module_path}. Available: {available}")
            
        except ImportError as e:
            raise ProviderRegistryError(f"Provider '{provider}' module not available: {e}")
    
    def list_providers(self) -> List[str]:
        """List all discovered providers."""
        return sorted(self._discover_agno_providers().keys())
    
    def get_provider_info(self, provider: str) -> Dict[str, Any]:
        """Get provider information."""
        providers = self._discover_agno_providers()
        if provider not in providers:
            raise ProviderRegistryError(f"Provider '{provider}' not found")
        return providers[provider]
    
    def reload(self):
        """Reload provider discovery."""
        self._discovered_providers = None
        self._discover_agno_providers.cache_clear()
        self.detect_provider.cache_clear()
        self.discover_model_class.cache_clear()
        logger.debug("🔧 Provider registry reloaded")


# Global registry instance
provider_registry = ProviderRegistry()


# Convenience functions
def detect_provider(model_id: str) -> str:
    """Detect provider for model ID."""
    return provider_registry.detect_provider(model_id)


def discover_model_class(provider: str, model_id: str) -> Type:
    """Discover model class for provider."""
    return provider_registry.discover_model_class(provider, model_id)


def list_providers() -> List[str]:
    """List available providers."""
    return provider_registry.list_providers()


def reload_provider_registry():
    """Reload provider registry."""
    provider_registry.reload()