"""
Shared tools and utilities for PagBank agents
Clean architecture - AI agents handle validation and business logic through natural language
No custom knowledge search tools - use Agno's native knowledge integration
"""

from typing import Any, Dict, List, Optional


# Tool registry for easy access
AGENT_TOOLS = {
    # No custom knowledge search tools - using Agno's native integration
}


def get_agent_tools(agent_type: str) -> List[Any]:
    """
    Get tools for a specific agent type
    
    Args:
        agent_type: Type of agent (e.g., 'adquirencia-specialist', 'pagbank-specialist')
        
    Returns:
        List of tools for the agent (empty list - using Agno native integration)
    """
    # Native Agno knowledge integration - no custom tools needed
    return []


