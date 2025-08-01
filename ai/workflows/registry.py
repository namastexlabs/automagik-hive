"""Workflow registry for dynamic loading of workflow instances."""

import importlib.util
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agno.workflow import Workflow

from lib.logging import logger


def _discover_workflows() -> dict[str, Callable[..., Workflow]]:
    """Dynamically discover workflows from filesystem"""
    workflows_dir = Path("ai/workflows")
    registry: dict[str, Callable[..., Workflow]] = {}

    if not workflows_dir.exists():
        return registry

    for workflow_path in workflows_dir.iterdir():
        if not workflow_path.is_dir() or workflow_path.name.startswith("_"):
            continue

        config_file = workflow_path / "config.yaml"
        workflow_file = workflow_path / "workflow.py"

        if config_file.exists() and workflow_file.exists():
            workflow_name = workflow_path.name

            try:
                # Load the workflow module dynamically
                spec = importlib.util.spec_from_file_location(
                    f"ai.workflows.{workflow_name}.workflow", workflow_file
                )
                if spec is None or spec.loader is None:
                    logger.warning(
                        "Failed to create module spec", workflow_name=workflow_name
                    )
                    continue
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Look for the factory function
                factory_func_name = f"get_{workflow_name.replace('-', '_')}_workflow"
                if hasattr(module, factory_func_name):
                    factory_func = getattr(module, factory_func_name)
                    registry[workflow_name] = factory_func

            except Exception as e:
                logger.warning(
                    "Failed to load workflow", workflow_name=workflow_name, error=str(e)
                )
                continue

    return registry


# Dynamic workflow registry - lazy initialization
_WORKFLOW_REGISTRY: dict[str, Callable[..., Workflow]] | None = None


def get_workflow_registry() -> dict[str, Callable[..., Workflow]]:
    """Get workflow registry with lazy initialization"""
    global _WORKFLOW_REGISTRY
    if _WORKFLOW_REGISTRY is None:
        logger.debug("Initializing workflow registry (lazy)")
        _WORKFLOW_REGISTRY = _discover_workflows()
        logger.info(
            "Workflow registry initialized", workflow_count=len(_WORKFLOW_REGISTRY)
        )
    return _WORKFLOW_REGISTRY


def get_workflow(
    workflow_id: str, version: int | None = None, **kwargs: Any
) -> Workflow:
    """
    Retrieve and instantiate a workflow by its ID.

    Args:
        workflow_id: The unique identifier of the workflow
        version: Optional version number for the workflow
        **kwargs: Additional keyword arguments to pass to the workflow factory

    Returns:
        Workflow: The instantiated workflow

    Raises:
        ValueError: If the workflow_id is not found in the registry
    """
    # Get registry with lazy initialization
    registry = get_workflow_registry()

    if workflow_id not in registry:
        available_workflows = ", ".join(sorted(registry.keys()))
        raise ValueError(
            f"Workflow '{workflow_id}' not found in registry. "
            f"Available workflows: {available_workflows}"
        )

    # Get the factory function for the workflow
    workflow_factory = registry[workflow_id]

    # Create and return the workflow instance
    # Pass version if provided, along with any other kwargs
    if version is not None:
        kwargs["version"] = version

    return workflow_factory(**kwargs)


def list_available_workflows() -> list[str]:
    """
    List all available workflow IDs in the registry.

    Returns:
        list[str]: Sorted list of workflow IDs
    """
    # Get registry with lazy initialization
    registry = get_workflow_registry()
    return sorted(registry.keys())


def is_workflow_registered(workflow_id: str) -> bool:
    """
    Check if a workflow is registered.

    Args:
        workflow_id: The workflow ID to check

    Returns:
        bool: True if the workflow is registered, False otherwise
    """
    # Get registry with lazy initialization
    registry = get_workflow_registry()
    return workflow_id in registry
