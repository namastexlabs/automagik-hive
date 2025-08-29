"""Jack Retrieval Agent Implementation

WhatsApp conversational agent for processamento-faturas data retrieval
using direct PostgreSQL database queries with Agno Agent setup.

Implementation features:
- Agent class with instructions parameter for natural language processing
- PostgresStorage for session management 
- postgres:query MCP tool for database access
- send_whatsapp_message MCP tool for WhatsApp integration
- External watchdog library for file monitoring
"""

from typing import Any
from agno.agent import Agent
from lib.utils.version_factory import create_agent

# No more manual tool imports - tools managed via YAML config


async def get_jack_retrieval_agent(**kwargs: Any) -> Agent:
    """
    Create Jack Retrieval Agent for WhatsApp PO queries.
    
    Implementation using Agno capabilities:
    - Agent class with instructions parameter
    - PostgresStorage for session management
    - MCP tools: postgres:query, send_whatsapp_message
    - Manual database schema management
    - External file monitoring via Python watchdog library
    
    Args:
        **kwargs: Context parameters for WhatsApp PO operations
        
    Returns:
        Agent configured for PostgreSQL-based PO queries
    """
    return await create_agent("jack_retrieval", **kwargs)
