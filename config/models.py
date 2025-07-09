"""AI Model configuration for PagBank Multi-Agent System."""

import os
from typing import Any, Dict

from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ModelConfig:
    """Configuration for AI models used in the PagBank system."""
    
    def __init__(self):
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_client = None
        
        # Default model configurations
        self.default_model = "claude-sonnet-4-20250514"
        self.reasoning_model = "claude-sonnet-4-20250514"
        self.fast_model = "claude-3-5-haiku-20241022"
        
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
            "escalation_agent": {
                "model": self.default_model,
                "max_tokens": 6144,
                "temperature": 0.4,
                "top_p": 0.9,
            },
            "feedback_collector": {
                "model": self.fast_model,
                "max_tokens": 2048,
                "temperature": 0.3,
                "top_p": 0.8,
            }
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

# Global model configuration instance
model_config = ModelConfig()

# Common model utilities
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