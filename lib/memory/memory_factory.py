"""
Memory Factory for Agno Framework Integration

Creates Memory instances with PostgresMemoryDb backends for user memory storage.
Clean implementation following Agno patterns.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.memory.v2.memory import Memory

from lib.config.models import get_default_model_id, resolve_model
from lib.exceptions import MemoryFactoryError
from lib.logging import logger


def _load_memory_config() -> dict[str, Any]:
    """Load memory configuration from YAML file."""
    config_path = Path(__file__).parent / "config.yaml"
    try:
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config.get("memory", {})
    except Exception as e:
        logger.warning("Could not load memory config, using defaults", error=str(e))
        return {
            "model": {
                "id": get_default_model_id(),
                "provider": "auto",  # Will be detected by resolver
            },
            "database": {"schema": "agno"},
        }


def create_memory_instance(
    table_name: str, db_url: str | None = None, model_id: str | None = None
) -> Memory:
    """
    Create Memory instance with PostgresMemoryDb backend.

    Args:
        table_name: Database table name for memories
        db_url: Database connection string (defaults to DATABASE_URL env var)
        model_id: Model ID for memory operations (defaults to config)

    Returns:
        Memory instance

    Raises:
        MemoryFactoryError: If memory instance creation fails
    """
    # Load configuration
    config = _load_memory_config()

    # Use provided model_id or fall back to config or resolver default
    if model_id is None:
        model_id = config.get("model", {}).get("id") or get_default_model_id()

    # Get database URL
    if not db_url:
        db_url = os.getenv("HIVE_DATABASE_URL")

    if not db_url:
        logger.error(
            "Memory creation failed: No database URL provided", table_name=table_name
        )
        raise MemoryFactoryError(
            f"No HIVE_DATABASE_URL provided for memory table '{table_name}'"
        )

    try:
        # Get schema from config
        schema = config.get("database", {}).get("schema", "agno")

        memory_db = PostgresMemoryDb(
            table_name=table_name, db_url=db_url, schema=schema
        )

        # Use ModelResolver to create model instance
        model = resolve_model(model_id)

        return Memory(db=memory_db, model=model)
    except Exception as e:
        logger.error(
            "Memory creation failed: Database connection error",
            table_name=table_name,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise MemoryFactoryError(
            f"Memory creation failed for table '{table_name}': {e}"
        ) from e


def create_agent_memory(agent_id: str, db_url: str | None = None) -> Memory:
    """Create Memory instance for an agent."""
    return create_memory_instance(f"agent_memories_{agent_id}", db_url)


def create_team_memory(team_id: str, db_url: str | None = None) -> Memory:
    """Create Memory instance for a team."""
    return create_memory_instance(f"team_memories_{team_id}", db_url)
