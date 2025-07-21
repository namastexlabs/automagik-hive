"""AI Model configuration for Automagik Hive Multi-Agent System.

Centralized model resolution system that leverages Agno's native model ecosystem
without hardcoded provider mappings. Supports all 25+ Agno providers automatically.
"""

import os
import importlib
import re
from typing import Any, Dict, Optional, Type, Union
from functools import lru_cache
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from lib.logging import logger

# Load environment variables
load_dotenv()

class ModelResolutionError(Exception):
    """Raised when model resolution fails."""
    pass

class ModelResolver:
    """
    Agno-native model resolver that dynamically discovers model classes
    and creates instances based on configuration with environment-driven defaults.
    """
    
    def __init__(self):
        self._model_cache = {}
        self._provider_cache = {}
        logger.debug("🔧 ModelResolver initialized")
    
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
        Detect provider from model ID using pattern matching.
        
        Args:
            model_id: Model identifier (e.g., "gpt-4.1-mini")
            
        Returns:
            str: Provider name (e.g., "openai")
            
        Raises:
            ModelResolutionError: If provider cannot be detected
        """
        # Common provider patterns based on Agno's model ecosystem
        provider_patterns = {
            r'^gpt-': 'openai',
            r'^o1-': 'openai', 
            r'^o3-': 'openai',
            r'^claude-': 'anthropic',
            r'^gemini-': 'google',
            r'^llama-': 'meta',
            r'^mixtral-': 'mistral',
            r'^command-': 'cohere',
            r'^deepseek-': 'deepseek',
            r'^qwen-': 'alibaba'
        }
        
        for pattern, provider in provider_patterns.items():
            if re.match(pattern, model_id, re.IGNORECASE):
                logger.debug("🔧 Provider detected", model_id=model_id, provider=provider, pattern=pattern)
                return provider
        
        # Fallback: try to infer from common naming conventions
        model_lower = model_id.lower()
        if 'gpt' in model_lower or 'openai' in model_lower:
            return 'openai'
        elif 'claude' in model_lower or 'anthropic' in model_lower:
            return 'anthropic'
        elif 'gemini' in model_lower or 'google' in model_lower:
            return 'google'
        
        logger.error("🔧 Provider detection failed", model_id=model_id)
        raise ModelResolutionError(f"Cannot detect provider for model ID: {model_id}")
    
    @lru_cache(maxsize=64)
    def _discover_model_class(self, provider: str, model_id: str) -> Type:
        """
        Dynamically discover and import Agno model class for given provider.
        
        Args:
            provider: Provider name (e.g., "openai")
            model_id: Model identifier for error context
            
        Returns:
            Type: Agno model class
            
        Raises:
            ModelResolutionError: If model class cannot be imported
        """
        try:
            # Try to import from agno.models.{provider}
            module_path = f"agno.models.{provider}"
            module = importlib.import_module(module_path)
            
            # Common model class naming patterns in Agno
            class_names = [
                f"{provider.title()}",  # e.g., "Openai" -> "OpenAI" might be mapped
                f"{provider.title()}Chat",  # e.g., "OpenAIChat"
                "Chat",  # Generic chat class
                provider.upper(),  # e.g., "OPENAI"
                provider.title().replace('ai', 'AI')  # Fix AI capitalization
            ]
            
            # Special cases for known Agno providers
            provider_class_map = {
                'openai': ['OpenAIChat', 'OpenAI'],
                'anthropic': ['Claude'],
                'google': ['Gemini'],
                'meta': ['Llama'],
                'mistral': ['Mistral'],
                'cohere': ['Cohere'],
                'deepseek': ['DeepSeek'],
                'groq': ['Groq']
            }
            
            if provider in provider_class_map:
                class_names = provider_class_map[provider] + class_names
            
            # Try to find the model class
            for class_name in class_names:
                if hasattr(module, class_name):
                    model_class = getattr(module, class_name)
                    logger.debug("🔧 Model class discovered", 
                               provider=provider, class_name=class_name, 
                               module=module_path, model_id=model_id)
                    return model_class
            
            # If no specific class found, list available classes for debugging
            available_classes = [name for name in dir(module) if not name.startswith('_') and name[0].isupper()]
            logger.error("🔧 Model class not found", 
                        provider=provider, module=module_path, 
                        available_classes=available_classes, model_id=model_id)
            raise ModelResolutionError(f"No suitable model class found in {module_path}. Available: {available_classes}")
            
        except ImportError as e:
            logger.error("🔧 Provider module import failed", 
                        provider=provider, module_path=module_path, 
                        error=str(e), model_id=model_id)
            raise ModelResolutionError(f"Provider '{provider}' not available in Agno installation: {e}")
    
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
        
        # Check cache first
        cache_key = f"{resolved_model_id}:{hash(frozenset(config_overrides.items()))}"
        if cache_key in self._model_cache:
            logger.debug("🔧 Model resolved from cache", model_id=resolved_model_id)
            return self._model_cache[cache_key]
        
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
            
            # Cache the result
            self._model_cache[cache_key] = model_instance
            
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
        """Clear model resolution cache."""
        self._model_cache.clear()
        self._provider_cache.clear()
        # Clear LRU caches
        self._detect_provider.cache_clear()
        self._discover_model_class.cache_clear()
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

# Legacy compatibility - maintain existing ModelConfig interface
class ModelConfig:
    """Legacy configuration class for backward compatibility."""
    
    def __init__(self):
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_client = None
        
        # Use resolver for default models instead of hardcoded values
        self.default_model = get_default_model_id()
        self.reasoning_model = get_default_model_id()  # Can be overridden via env
        self.fast_model = os.getenv("HIVE_FAST_MODEL", "claude-3-5-haiku-20241022")
        
        # Model parameters
        self.default_params = {
            "max_tokens": 8192,
            "temperature": 0.7,
            "top_p": 0.9,
        }
        
        # Specific configurations for different use cases
        self.model_configs = {
            "main_orchestrator": {
                "model": self.default_model,
                "max_tokens": 4096,
                "temperature": 0.3,
                "top_p": 0.8,
            },
            "specialist_teams": {
                "model": self.default_model,
                "max_tokens": 8192,
                "temperature": 0.5,
                "top_p": 0.9,
            },
            "knowledge_search": {
                "model": self.fast_model,
                "max_tokens": 2048,
                "temperature": 0.1,
                "top_p": 0.7,
            },
            "memory_processing": {
                "model": self.fast_model,
                "max_tokens": 4096,
                "temperature": 0.2,
                "top_p": 0.8,
            },
        }
    
    def get_anthropic_client(self) -> Anthropic:
        """Get Anthropic client instance."""
        if not self.anthropic_client:
            if not self.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            self.anthropic_client = Anthropic(api_key=self.anthropic_api_key)
        return self.anthropic_client
    
    def get_config(self, use_case: str) -> Dict[str, Any]:
        """Get model configuration for specific use case."""
        if use_case in self.model_configs:
            return self.model_configs[use_case]
        return {
            "model": self.default_model,
            **self.default_params
        }
    
    def validate_api_key(self) -> bool:
        """Validate Anthropic API key."""
        try:
            client = self.get_anthropic_client()
            # Test with a simple message
            response = client.messages.create(
                model=self.fast_model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            return len(response.content) > 0
        except Exception:
            return False
    
    def get_embedding_config(self) -> Dict[str, Any]:
        """Get configuration for embedding models."""
        return {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "device": "cpu",  # Change to "cuda" if GPU available
            "normalize_embeddings": True,
            "batch_size": 32,
            "max_seq_length": 512
        }

# Global model configuration instance (legacy)
model_config = ModelConfig()

# Legacy compatibility functions
def get_claude_client() -> Anthropic:
    """Get Claude client."""
    return model_config.get_anthropic_client()

def get_model_params(use_case: str = "default") -> Dict[str, Any]:
    """Get model parameters for specific use case."""
    return model_config.get_config(use_case)

def validate_models() -> Dict[str, bool]:
    """Validate all model configurations."""
    return {
        "anthropic_api_key": model_config.validate_api_key(),
        "embedding_model": True,  # Will be validated when sentence-transformers loads
        "default_model_available": validate_model(get_default_model_id()),
    }

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