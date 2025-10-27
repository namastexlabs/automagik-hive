"""Shared database utilities for the Agno proxy system."""

from __future__ import annotations

import importlib
import inspect
from typing import Any

from lib.logging import logger

_DEFAULT_SCHEMA = "agno"


def get_storage_type_mapping() -> dict[str, str]:
    """Return mapping of logical storage types to Agno Db class paths."""

    return {
        "postgres": "agno.db.postgres.PostgresDb",
        "sqlite": "agno.db.sqlite.SqliteDb",
        "mongodb": "agno.db.mongo.MongoDb",
        "redis": "agno.db.redis.RedisDb",
        "dynamodb": "agno.db.dynamo.DynamoDb",
        "json": "agno.db.json.JsonDb",
        "yaml": "agno.db.yaml.YamlDb",
        "singlestore": "agno.db.singlestore.SingleStoreDb",
    }


def get_storage_class(storage_type: str):
    """Resolve the Agno Db class for the requested storage type."""

    storage_type_map = get_storage_type_mapping()

    if storage_type not in storage_type_map:
        supported_types = list(storage_type_map.keys())
        raise ValueError(f"Unsupported storage type: {storage_type}. Supported types: {supported_types}")

    module_path, class_name = storage_type_map[storage_type].rsplit(".", 1)
    try:
        module = importlib.import_module(module_path)
        storage_class = getattr(module, class_name)
        class_name_repr = getattr(storage_class, "__name__", type(storage_class).__name__)
        logger.debug("Resolved %s -> %s", storage_type, class_name_repr)
        return storage_class
    except (ImportError, AttributeError) as exc:
        raise ImportError(f"Failed to import {storage_type} storage class: {exc}")


def _default_table_name(component_mode: str, component_id: str, suffix: str) -> str:
    safe_component = component_id.replace("-", "_")
    return f"{component_mode}_{safe_component}_{suffix}"


def _detect_storage_type_from_url(db_url: str | None) -> str:
    """Auto-detect storage type from database URL."""
    if not db_url:
        return "postgres"  # Default fallback

    url_lower = db_url.lower()
    if url_lower.startswith("sqlite"):
        return "sqlite"
    elif url_lower.startswith("mongodb"):
        return "mongodb"
    elif url_lower.startswith("redis"):
        return "redis"
    elif url_lower.startswith("postgresql") or url_lower.startswith("postgres"):
        return "postgres"
    else:
        return "postgres"  # Default fallback


def create_dynamic_storage(
    storage_config: dict[str, Any],
    component_id: str,
    component_mode: str,
    db_url: str | None,
):
    """Build an Agno Db instance and dependency bundle for a component."""

    storage_config = storage_config or {}

    # Auto-detect storage type from URL if not explicitly configured
    if "type" not in storage_config and db_url:
        detected_type = _detect_storage_type_from_url(db_url)
        logger.info(
            "Auto-detected storage type '%s' from database URL for %s '%s'",
            detected_type,
            component_mode,
            component_id,
        )
        storage_type = detected_type
    else:
        storage_type = storage_config.get("type", "postgres")

    storage_class = get_storage_class(storage_type)

    try:
        signature = inspect.signature(storage_class.__init__)
    except Exception as exc:  # pragma: no cover - defensive logging
        raise Exception(f"Failed to introspect {storage_type} storage constructor: {exc}") from exc

    db_kwargs: dict[str, Any] = {}
    safe_component = component_id.replace("-", "_")
    table_name_override = storage_config.get("table_name")
    base_for_related = table_name_override or f"{component_mode}_{safe_component}"
    session_default = table_name_override or f"{component_mode}_{safe_component}_sessions"

    for param_name, _param in signature.parameters.items():
        if param_name == "self":
            continue

        if param_name == "db_url":
            candidate_url = storage_config.get("db_url") or db_url
            if candidate_url is not None:
                db_kwargs["db_url"] = candidate_url
        elif param_name == "db_schema":
            schema = storage_config.get("db_schema") or storage_config.get("schema")
            if schema is None and storage_type == "postgres":
                schema = _DEFAULT_SCHEMA
            if schema is not None:
                db_kwargs["db_schema"] = schema
        elif param_name == "session_table":
            db_kwargs["session_table"] = storage_config.get("session_table") or session_default
        elif param_name == "memory_table":
            db_kwargs["memory_table"] = storage_config.get("memory_table") or f"{base_for_related}_memories"
        elif param_name == "metrics_table":
            db_kwargs["metrics_table"] = storage_config.get("metrics_table") or f"{base_for_related}_metrics"
        elif param_name == "eval_table":
            db_kwargs["eval_table"] = storage_config.get("eval_table") or f"{base_for_related}_evals"
        elif param_name == "knowledge_table":
            db_kwargs["knowledge_table"] = storage_config.get("knowledge_table") or f"{base_for_related}_knowledge"
        elif param_name == "id":
            db_kwargs["id"] = storage_config.get("id") or f"{component_mode}-{component_id}"
        elif param_name in storage_config:
            db_kwargs[param_name] = storage_config[param_name]
        else:
            # Leave unspecified parameters to their defaults
            continue

    logger.debug(
        "Creating %s db for %s '%s' with kwargs: %s",
        storage_type,
        component_mode,
        component_id,
        db_kwargs,
    )

    try:
        db_instance = storage_class(**db_kwargs)
    except Exception as exc:  # pragma: no cover - surfaced in tests via mocks
        logger.error(
            "Failed to instantiate %s db for %s '%s': %s",
            storage_type,
            component_mode,
            component_id,
            exc,
        )
        raise

    dependencies_config = storage_config.get("dependencies") or {}
    if not isinstance(dependencies_config, dict):
        logger.warning("Ignoring non-dict dependencies config for %s '%s'", component_mode, component_id)
        dependencies_config = {}

    dependencies = dict(dependencies_config)
    dependencies.setdefault("db", db_instance)

    return {"db": db_instance, "dependencies": dependencies}


def get_supported_storage_types() -> list:
    """Expose supported storage/db types for diagnostics."""

    return list(get_storage_type_mapping().keys())


def validate_storage_config(storage_config: dict[str, Any]) -> dict[str, Any]:
    """Return a simple validation report for a storage configuration."""

    storage_type = storage_config.get("type", "postgres")
    supported_types = get_supported_storage_types()

    result = {
        "storage_type": storage_type,
        "is_supported": storage_type in supported_types,
        "supported_types": supported_types,
        "config_keys": list(storage_config.keys()),
    }

    if not result["is_supported"]:
        result["error"] = f"Unsupported storage type: {storage_type}"

    return result
