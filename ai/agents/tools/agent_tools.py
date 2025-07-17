"""
Shared tools and utilities for PagBank agents
Clean architecture - AI agents handle validation and business logic through natural language
"""

from typing import Any, Dict, List, Optional


def get_agent_tools(agent_type: str) -> List[Any]:
    """
    Get tools for a specific agent type
    
    Args:
        agent_type: Type of agent (e.g., 'adquirencia-specialist', 'pagbank-specialist')
        
    Returns:
        List of tools for the agent (empty list - using Agno native integration)
    """
    return []
