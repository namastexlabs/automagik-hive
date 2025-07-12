"""
Central Prompt Manager for PagBank Multi-Agent System
Handles all prompt loading, caching, and retrieval
"""

import os
from typing import Dict, Any, Optional
from functools import lru_cache

from .base.system_prompts import SYSTEM_PROMPTS
from .base.response_templates import RESPONSE_TEMPLATES
from .base.error_prompts import ERROR_PROMPTS
from .orchestrator.routing_prompts import ROUTING_PROMPTS
from .orchestrator.clarification_prompts import CLARIFICATION_PROMPTS
from .specialists.adquirencia_prompts import ADQUIRENCIA_PROMPTS
from .specialists.emissao_prompts import EMISSAO_PROMPTS
from .specialists.pagbank_prompts import PAGBANK_PROMPTS
from .specialists.human_handoff_prompts import HUMAN_HANDOFF_PROMPTS
from .escalation.human_escalation_prompts import HUMAN_ESCALATION_PROMPTS


class PromptManager:
    """
    Central prompt management with caching and templating
    """
    
    def __init__(self, language: str = "pt_BR"):
        """
        Initialize prompt manager
        
        Args:
            language: Language code (default: pt_BR for Brazilian Portuguese)
        """
        self.language = language
        self.prompts = self._load_all_prompts()
        
    def _load_all_prompts(self) -> Dict[str, Any]:
        """Load and organize all prompts"""
        return {
            "system": SYSTEM_PROMPTS,
            "response": RESPONSE_TEMPLATES,
            "error": ERROR_PROMPTS,
            "orchestrator": {
                "routing": ROUTING_PROMPTS,
                "clarification": CLARIFICATION_PROMPTS
            },
            "specialists": {
                "adquirencia": ADQUIRENCIA_PROMPTS,
                "emissao": EMISSAO_PROMPTS,
                "pagbank": PAGBANK_PROMPTS,
                "human_handoff": HUMAN_HANDOFF_PROMPTS
            },
            "escalation": {
                "human": HUMAN_ESCALATION_PROMPTS,
            }
        }
    
    def get_prompt(self, category: str, name: str, **kwargs) -> str:
        """
        Get formatted prompt with variable substitution
        
        Args:
            category: Prompt category (e.g., "system", "specialists")
            name: Prompt name within category
            **kwargs: Variables for string formatting
            
        Returns:
            Formatted prompt string
        """
        # Navigate nested structure
        prompt_dict = self.prompts
        for key in category.split("."):
            prompt_dict = prompt_dict.get(key, {})
        
        prompt = prompt_dict.get(name)
        if not prompt:
            raise ValueError(f"Prompt not found: {category}.{name}")
        
        # Format with provided variables
        if kwargs:
            return prompt.format(**kwargs)
        return prompt
    
    def get_specialist_prompt(self, specialist: str, prompt_type: str = "base") -> str:
        """
        Get specialist-specific prompts
        
        Args:
            specialist: Specialist name (e.g., "cards", "credit")
            prompt_type: Type of prompt (e.g., "base", "instructions", "examples")
            
        Returns:
            Specialist prompt string
        """
        return self.get_prompt(f"specialists.{specialist}", prompt_type)
    
    def get_routing_prompt(self) -> str:
        """Get main orchestrator routing prompt"""
        return self.get_prompt("orchestrator.routing", "main")
    
    def get_clarification_template(self, clarification_type: str) -> str:
        """Get clarification prompt template"""
        return self.get_prompt("orchestrator.clarification", clarification_type)
    
    def get_error_message(self, error_type: str, **kwargs) -> str:
        """Get formatted error message"""
        return self.get_prompt("error", error_type, **kwargs)
    
    def get_response_template(self, template_name: str, **kwargs) -> str:
        """Get response template"""
        return self.get_prompt("response", template_name, **kwargs)
    
    def list_prompts(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        List available prompts, optionally filtered by category
        
        Args:
            category: Optional category filter
            
        Returns:
            Dictionary of available prompts
        """
        if category:
            prompt_dict = self.prompts
            for key in category.split("."):
                prompt_dict = prompt_dict.get(key, {})
            return prompt_dict
        return self.prompts
    
    def validate_prompts(self) -> Dict[str, bool]:
        """
        Validate all prompts are loaded correctly
        
        Returns:
            Dictionary of prompt categories and their validation status
        """
        validation_results = {}
        
        def validate_dict(d: Dict, path: str = "") -> None:
            for key, value in d.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, dict):
                    validate_dict(value, current_path)
                else:
                    validation_results[current_path] = bool(value and isinstance(value, str))
        
        validate_dict(self.prompts)
        return validation_results


# Global instance
_prompt_manager = None


def get_prompt_manager(language: str = "pt_BR") -> PromptManager:
    """
    Get or create the global prompt manager instance
    
    Args:
        language: Language code
        
    Returns:
        PromptManager instance
    """
    global _prompt_manager
    if _prompt_manager is None or _prompt_manager.language != language:
        _prompt_manager = PromptManager(language)
    return _prompt_manager