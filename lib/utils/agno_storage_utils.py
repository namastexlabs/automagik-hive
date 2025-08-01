"""
Shared Storage Utilities for Agno Proxy System

This module provides shared storage functionality to eliminate code duplication
across Agent, Team, and Workflow proxy classes. It implements the dynamic
storage creation pattern with introspection that maintains 1:1 compatibility
with all Agno storage backends.
"""

import importlib
import inspect
from typing import Any

from lib.logging import logger


def get_storage_type_mapping() -> dict[str, str]:
    """
    Centralized mapping of storage types to their Agno module paths.

    Returns:
        Dictionary mapping storage type names to their full module.class paths
    """
    return {
        "postgres": "agno.storage.postgres.PostgresStorage",
        "sqlite": "agno.storage.sqlite.SqliteStorage",
        "mongodb": "agno.storage.mongodb.MongoDbStorage",
        "redis": "agno.storage.redis.RedisStorage",
        "dynamodb": "agno.storage.dynamodb.DynamoDbStorage",
        "json": "agno.storage.json.JsonStorage",
        "yaml": "agno.storage.yaml.YamlStorage",
        "singlestore": "agno.storage.singlestore.SingleStoreStorage",
    }


def get_storage_class(storage_type: str):
    """
    Dynamic storage class resolution using importlib.

    Args:
        storage_type: Storage type from YAML (postgres, sqlite, mongodb, etc.)

    Returns:
        Storage class ready for instantiation

    Raises:
        ValueError: If storage type is not supported
        ImportError: If storage class cannot be imported
    """
    storage_type_map = get_storage_type_mapping()

    if storage_type not in storage_type_map:
        supported_types = list(storage_type_map.keys())
        raise ValueError(
            f"Unsupported storage type: {storage_type}. "
            f"Supported types: {supported_types}"
        )

    # Dynamic import and class resolution
    module_path, class_name = storage_type_map[storage_type].rsplit(".", 1)
    try:
        module = importlib.import_module(module_path)
        storage_class = getattr(module, class_name)
        logger.debug(f"🔧 Successfully imported {storage_type} storage class")
        return storage_class
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Failed to import {storage_type} storage class: {e}")


def create_dynamic_storage(
    storage_config: dict[str, Any],
    component_id: str,
    component_mode: str,
    db_url: str | None,
):
    """
    Fully dynamic storage creation using introspection.

    This function implements the same introspection pattern used for Agent
    parameter discovery, ensuring 1:1 compatibility with all Agno storage
    backends without hardcoding parameters.

    Args:
        storage_config: Storage configuration from YAML
        component_id: Component identifier (agent/team/workflow ID)
        component_mode: "agent", "team", or "workflow"
        db_url: Database URL if needed

    Returns:
        Dynamically created storage instance

    Raises:
        ValueError: If storage type is unsupported
        ImportError: If storage class cannot be imported
        Exception: If storage instantiation fails
    """
    # 1. Get storage type from YAML (default to postgres for backward compatibility)
    storage_type = storage_config.get("type", "postgres")

    # 2. Dynamic storage class resolution
    storage_class = get_storage_class(storage_type)

    # 3. Introspect storage class constructor (same pattern as Agent discovery)
    try:
        sig = inspect.signature(storage_class.__init__)
    except Exception as e:
        raise Exception(f"Failed to introspect {storage_type} storage constructor: {e}")

    storage_params = {}

    # 4. Auto-map ALL compatible parameters using introspection
    for param_name in sig.parameters:
        if param_name == "self":
            continue
        if param_name == "mode":
            # Auto-infer mode from component type
            storage_params["mode"] = component_mode
        elif param_name == "schema" and param_name not in storage_config:
            # Always use agno schema for Agno framework tables
            storage_params["schema"] = "agno"
        elif param_name == "table_name" and "table_name" not in storage_config:
            # Auto-generate table name if not specified
            storage_params["table_name"] = f"{component_mode}s_{component_id}"
        elif param_name in storage_config:
            # Direct mapping from YAML config
            storage_params[param_name] = storage_config[param_name]
        elif param_name == "db_url" and db_url:
            storage_params["db_url"] = db_url

    logger.debug(
        f"🐛 Creating {storage_type} storage for {component_mode} '{component_id}' with {len(storage_params)} parameters: {list(storage_params.keys())}"
    )

    try:
        # 5. Dynamic instantiation with mapped parameters
        storage_instance = storage_class(**storage_params)
        logger.debug(
            f"🔧 Successfully created {storage_type} storage for {component_id}"
        )
        return storage_instance
    except Exception as e:
        logger.error(
            f"🚨 Failed to create {storage_type} storage for {component_id}: {e}"
        )
        logger.debug(f"🔧 Attempted parameters: {storage_params}")
        raise


def get_supported_storage_types() -> list:
    """
    Get list of all supported storage types.

    Returns:
        List of supported storage type names
    """
    return list(get_storage_type_mapping().keys())


def validate_storage_config(storage_config: dict[str, Any]) -> dict[str, Any]:
    """
    Validate storage configuration and return analysis.

    Args:
        storage_config: Storage configuration dictionary

    Returns:
        Dictionary with validation results
    """
    storage_type = storage_config.get("type", "postgres")
    supported_types = get_supported_storage_types()

    validation_result = {
        "storage_type": storage_type,
        "is_supported": storage_type in supported_types,
        "supported_types": supported_types,
        "config_keys": list(storage_config.keys()),
    }

    if not validation_result["is_supported"]:
        validation_result["error"] = f"Unsupported storage type: {storage_type}"

    return validation_result
