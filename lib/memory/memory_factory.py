"""Memory factory helpers for Agno v2."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from agno.db.postgres import PostgresDb
from agno.memory.manager import MemoryManager

from lib.config.models import get_default_model_id, resolve_model
from lib.exceptions import MemoryFactoryError
from lib.logging import logger


def _load_memory_config() -> dict[str, Any]:
    """Load memory configuration from YAML file."""

    config_path = Path(__file__).parent / "config.yaml"
    try:
        with open(config_path, encoding="utf-8") as file_handle:
            config = yaml.safe_load(file_handle)
        return config.get("memory", {})
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Could not load memory config, using defaults", error=str(exc))
        return {
            "model": {
                "id": get_default_model_id(),
                "provider": "auto",
            },
            "database": {"schema": "agno"},
        }


def _build_memory_db(
    table_name: str,
    db_url: str,
    schema: str,
) -> PostgresDb:
    """Create a PostgresDb configured for memory usage."""

    safe_name = table_name.replace("-", "_")
    return PostgresDb(
        db_url=db_url,
        db_schema=schema,
        session_table=f"{safe_name}_sessions",
        memory_table=table_name,
        metrics_table=f"{safe_name}_metrics",
        eval_table=f"{safe_name}_evals",
        knowledge_table=f"{safe_name}_knowledge",
    )


def create_memory_instance(
    table_name: str,
    db_url: str | None = None,
    model_id: str | None = None,
    db: PostgresDb | None = None,
) -> MemoryManager:
    """Create a MemoryManager backed by an Agno Db."""

    config = _load_memory_config()

    model_identifier = model_id or config.get("model", {}).get("id") or get_default_model_id()

    shared_db = db
    if shared_db is None:
        resolved_db_url = db_url or os.getenv("HIVE_DATABASE_URL")
        if not resolved_db_url:
            logger.error(
                "Memory creation failed: No database URL provided",
                table_name=table_name,
            )
            raise MemoryFactoryError(f"No HIVE_DATABASE_URL provided for memory table '{table_name}'")

        schema = config.get("database", {}).get("schema", "agno")
        shared_db = _build_memory_db(table_name, resolved_db_url, schema)

    try:
        model = resolve_model(model_identifier)
        return MemoryManager(model=model, db=shared_db)
    except Exception as exc:  # pragma: no cover - surfaced in tests via mocks
        logger.error(
            "Memory creation failed",
            table_name=table_name,
            error=str(exc),
            error_type=type(exc).__name__,
        )
        raise MemoryFactoryError(f"Memory creation failed for table '{table_name}': {exc}") from exc


def create_agent_memory(
    agent_id: str,
    db_url: str | None = None,
    *,
    db: PostgresDb | None = None,
) -> MemoryManager:
    """Create MemoryManager configured for an agent."""

    table_name = f"agent_memories_{agent_id}"
    return create_memory_instance(table_name, db_url=db_url, db=db)


def create_team_memory(
    team_id: str,
    db_url: str | None = None,
    *,
    db: PostgresDb | None = None,
) -> MemoryManager:
    """Create MemoryManager configured for a team."""

    table_name = f"team_memories_{team_id}"
    return create_memory_instance(table_name, db_url=db_url, db=db)
