"""
PagBank Multi-Agent System Prompts
Centralized prompt management for all agents
"""

from .prompt_manager import PromptManager, get_prompt_manager

__all__ = [
    'PromptManager',
    'get_prompt_manager'
]