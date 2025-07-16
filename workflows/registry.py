"""Workflow registry for dynamic loading of workflow instances."""

from typing import Dict, Callable, Optional, Any
from agno import Workflow

from workflows.conversation_typification.workflow import get_conversation_typification_workflow
from workflows.human_handoff.workflow import get_human_handoff_workflow


# Registry mapping workflow IDs to their factory functions
WORKFLOW_REGISTRY: Dict[str, Callable[..., Workflow]] = {
    "conversation-typification": get_conversation_typification_workflow,
    "human-handoff": get_human_handoff_workflow,
}


def get_workflow(workflow_id: str, version: Optional[int] = None, **kwargs) -> Workflow:
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
    if workflow_id not in WORKFLOW_REGISTRY:
        available_workflows = ", ".join(sorted(WORKFLOW_REGISTRY.keys()))
        raise ValueError(
            f"Workflow '{workflow_id}' not found in registry. "
            f"Available workflows: {available_workflows}"
        )
    
    # Get the factory function for the workflow
    workflow_factory = WORKFLOW_REGISTRY[workflow_id]
    
    # Create and return the workflow instance
    # Pass version if provided, along with any other kwargs
    if version is not None:
        kwargs['version'] = version
        
    return workflow_factory(**kwargs)


def list_available_workflows() -> list[str]:
    """
    List all available workflow IDs in the registry.
    
    Returns:
        list[str]: Sorted list of workflow IDs
    """
    return sorted(WORKFLOW_REGISTRY.keys())


def is_workflow_registered(workflow_id: str) -> bool:
    """
    Check if a workflow is registered.
    
    Args:
        workflow_id: The workflow ID to check
        
    Returns:
        bool: True if the workflow is registered, False otherwise
    """
    return workflow_id in WORKFLOW_REGISTRY