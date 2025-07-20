"""
Memory Factory for Agno Framework Integration

Creates Memory instances with PostgresMemoryDb backends for user memory storage.
Clean implementation following Agno patterns.
"""

from typing import Optional
import os
from agno.memory.v2.memory import Memory
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.models.anthropic import Claude


def create_memory_instance(
    table_name: str,
    db_url: Optional[str] = None,
    model_id: str = "claude-sonnet-4-20250514"
) -> Optional[Memory]:
    """
    Create Memory instance with PostgresMemoryDb backend.
    
    Args:
        table_name: Database table name for memories
        db_url: Database connection string (defaults to DATABASE_URL env var)
        model_id: Model ID for memory operations
        
    Returns:
        Memory instance or None if creation fails
    """
    if not db_url:
        db_url = os.getenv("HIVE_DATABASE_URL")
    
    if not db_url:
        print("Warning: No HIVE_DATABASE_URL provided for memory creation")
        return None
    
    try:
        memory_db = PostgresMemoryDb(
            table_name=table_name,
            db_url=db_url
        )
        
        return Memory(
            db=memory_db,
            model=Claude(id=model_id)
        )
    except Exception as e:
        print(f"Warning: Could not create Memory instance: {e}")
        return None


def create_agent_memory(agent_id: str, db_url: Optional[str] = None) -> Optional[Memory]:
    """Create Memory instance for an agent."""
    return create_memory_instance(f"agent_memories_{agent_id}", db_url)


def create_team_memory(team_id: str, db_url: Optional[str] = None) -> Optional[Memory]:
    """Create Memory instance for a team."""
    return create_memory_instance(f"team_memories_{team_id}", db_url)