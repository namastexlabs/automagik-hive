"""AI Model configuration for Automagik Hive Multi-Agent System.

ZERO-CONFIGURATION model resolution system with dynamic provider discovery.
Automatically discovers and supports ALL Agno providers at runtime without hardcoded mappings.

Architecture:
- Dynamic provider discovery via runtime scanning of agno.models namespace
- Intelligent pattern matching for model ID → provider detection
- Zero-configuration class resolution for all Agno model classes
- Follows the same dynamic registry patterns as teams/agents registries
- No YAML files, no hardcoded mappings - pure runtime intelligence

This eliminates Issues 2 & 3:
- Issue 2: Hardcoded provider patterns → Dynamic pattern detection
- Issue 3: Hardcoded provider mappings → Runtime provider discovery
"""

import os
from typing import Any, Dict, Optional
from functools import lru_cache

from anthropic import Anthropic
from dotenv import load_dotenv
from lib.logging import logger
from lib.config.provider_registry import provider_registry

# Load environment variables
load_dotenv()

class ModelResolutionError(Exception):
    """Raised when model resolution fails."""
    pass

class ModelResolver:
    """
    Zero-configuration model resolver with dynamic provider discovery.
    
    Features:
    - Automatically discovers ALL Agno providers at runtime
    - Intelligent model ID → provider detection using pattern matching
    - Dynamic class resolution without hardcoded mappings
    - Environment-driven default model configuration
    - Follows project's dynamic registry architecture patterns
    
    No configuration files needed - pure runtime intelligence.
    """
    
    def __init__(self):
        logger.debug("🔧 ModelResolver initialized - using dynamic provider registry")
    
    def get_default_model_id(self) -> str:
        """
        Get default model ID from environment variable with system fallback.
        
        Returns:
            str: Model ID (e.g., "gpt-4.1-mini", "claude-sonnet-4", "gemini-2.5-flash")
        """
        default = os.getenv("HIVE_DEFAULT_MODEL", "gpt-4.1-mini")
        logger.debug("🔧 Default model resolved", model_id=default, source="HIVE_DEFAULT_MODEL" if "HIVE_DEFAULT_MODEL" in os.environ else "system_default")
        return default
    
    @lru_cache(maxsize=128)
    def _detect_provider(self, model_id: str) -> str:
        """
        Detect provider from model ID using dynamic registry.
        
        Args:
            model_id: Model identifier (e.g., "gpt-4.1-mini")
            
        Returns:
            str: Provider name (e.g., "openai")
            
        Raises:
            ModelResolutionError: If provider cannot be detected
        """
        try:
            provider = provider_registry.detect_provider(model_id)
            logger.debug("🔧 Provider detected via registry", model_id=model_id, provider=provider)
            return provider
        except Exception as e:
            logger.error("🔧 Provider detection failed", model_id=model_id, error=str(e))
            raise ModelResolutionError(f"Cannot detect provider for model ID '{model_id}': {e}")
    
    @lru_cache(maxsize=64)
    def _discover_model_class(self, provider: str, model_id: str):
        """
        Dynamically discover and import Agno model class using registry.
        
        Args:
            provider: Provider name (e.g., "openai")
            model_id: Model identifier for error context
            
        Returns:
            Type: Agno model class
            
        Raises:
            ModelResolutionError: If model class cannot be imported
        """
        try:
            model_class = provider_registry.discover_model_class(provider, model_id)
            logger.debug("🔧 Model class discovered via registry", 
                       provider=provider, class_name=model_class.__name__, model_id=model_id)
            return model_class
        except Exception as e:
            logger.error("🔧 Model class discovery failed", 
                        provider=provider, error=str(e), model_id=model_id)
            raise ModelResolutionError(f"Failed to discover model class for provider '{provider}': {e}")
    
    def resolve_model(self, model_id: Optional[str] = None, **config_overrides) -> Any:
        """
        Create model instance with Agno-native resolution and configuration merging.
        
        Args:
            model_id: Model identifier (None uses default)
            **config_overrides: Additional configuration parameters
            
        Returns:
            Agno model instance
            
        Raises:
            ModelResolutionError: If model resolution or creation fails
        """
        # Resolve model ID with precedence: param -> default
        resolved_model_id = model_id or self.get_default_model_id()
        
        
        try:
            # Detect provider and discover model class
            provider = self._detect_provider(resolved_model_id)
            model_class = self._discover_model_class(provider, resolved_model_id)
            
            # Prepare model configuration
            model_config = {
                'id': resolved_model_id,
                **config_overrides
            }
            
            # Create model instance
            model_instance = model_class(**model_config)
            
            
            logger.info("🔧 Model resolved successfully", 
                       model_id=resolved_model_id, provider=provider, 
                       class_name=model_class.__name__, config_keys=list(config_overrides.keys()))
            
            return model_instance
            
        except Exception as e:
            logger.error("🔧 Model resolution failed", 
                        model_id=resolved_model_id, error=str(e), 
                        error_type=type(e).__name__)
            raise ModelResolutionError(f"Failed to resolve model '{resolved_model_id}': {e}")
    
    def validate_model_availability(self, model_id: str) -> bool:
        """
        Validate that a model can be resolved without creating an instance.
        
        Args:
            model_id: Model identifier to validate
            
        Returns:
            bool: True if model can be resolved
        """
        try:
            provider = self._detect_provider(model_id)
            self._discover_model_class(provider, model_id)
            return True
        except ModelResolutionError:
            return False
    
    def clear_cache(self):
        """Clear model resolver and provider registry caches."""
        self._detect_provider.cache_clear()
        self._discover_model_class.cache_clear()
        provider_registry.reload()
        logger.debug("🔧 Model resolver cache cleared")

# Global model resolver instance
model_resolver = ModelResolver()

# Convenience functions for easy access
def get_default_model_id() -> str:
    """Get default model ID from environment or system default."""
    return model_resolver.get_default_model_id()

def resolve_model(model_id: Optional[str] = None, **config_overrides) -> Any:
    """Create model instance using centralized resolver."""
    return model_resolver.resolve_model(model_id, **config_overrides)

def validate_model(model_id: str) -> bool:
    """Validate model availability without creating instance."""
    return model_resolver.validate_model_availability(model_id)


# Portuguese language specific configurations
PORTUGUESE_PROMPTS = {
    "system_instructions": """
    Você é um assistente especializado em serviços financeiros do PagBank.
    Sempre responda em português brasileiro, de forma clara e profissional.
    Mantenha um tom cordial e helpful.
    """,
    "greeting": "Olá! Sou seu assistente PagBank. Como posso ajudá-lo hoje?",
    "error_message": "Desculpe, houve um problema. Vou transferir você para suporte especializado.",
    "escalation_message": "Vou conectar você com um especialista para melhor atendimento.",
    "feedback_request": "Sua opinião é importante! Como foi sua experiência?"
}

def get_portuguese_prompt(key: str) -> str:
    """Get Portuguese language prompt."""
    return PORTUGUESE_PROMPTS.get(key, "")