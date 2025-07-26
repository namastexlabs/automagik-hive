"""
Workflow Proxy Module

Specialized proxy for creating Agno Workflow instances with dynamic parameter mapping.
This module handles workflow-specific configuration processing including steps processing
while leveraging shared storage utilities to eliminate code duplication.
"""

import inspect
from collections.abc import Callable
from typing import Any

from agno.workflow.v2.workflow import Workflow

from lib.logging import logger

from .agno_storage_utils import create_dynamic_storage


class AgnoWorkflowProxy:
    """
    Dynamic proxy that automatically maps config parameters to Agno Workflow (v2) constructor.

    This proxy introspects the current Agno Workflow class to discover all supported
    parameters and automatically maps config values, ensuring future compatibility
    even when Agno adds new Workflow parameters.
    """

    def __init__(self):
        """Initialize the proxy by introspecting the current Agno Workflow class."""
        self._supported_params = self._discover_workflow_parameters()
        self._custom_params = self._get_custom_parameter_handlers()
        logger.info(
            f"🤖 AgnoWorkflowProxy initialized with {len(self._supported_params)} Agno Workflow parameters"
        )

    def _discover_workflow_parameters(self) -> set[str]:
        """
        Dynamically discover all parameters supported by the Agno Workflow constructor.

        Returns:
            Set of parameter names that Workflow.__init__ accepts
        """
        try:
            # Get the Workflow constructor signature
            sig = inspect.signature(Workflow.__init__)

            # Extract all parameter names except 'self'
            params = {
                param_name
                for param_name, param in sig.parameters.items()
                if param_name != "self"
            }

            logger.debug(
                f"🤖 Discovered {len(params)} Agno Workflow parameters: {sorted(params)}"
            )
            return params

        except Exception as e:
            logger.error(f"🤖 Failed to introspect Agno Workflow parameters: {e}")
            # Fallback to known parameters if introspection fails
            return self._get_fallback_parameters()

    def _get_fallback_parameters(self) -> set[str]:
        """
        Fallback set of known Agno Workflow parameters if introspection fails.

        Returns:
            Set of known parameter names from current Agno version
        """
        return {
            # Core Workflow Settings
            "workflow_id",
            "name",
            "description",
            "storage",
            "steps",
            # Session Settings
            "session_id",
            "session_name",
            "workflow_session_state",
            "user_id",
            # Runtime Settings
            "debug_mode",
            # Streaming
            "stream",
            "stream_intermediate_steps",
            # Events
            "store_events",
            "events_to_skip",
        }

    def _get_custom_parameter_handlers(self) -> dict[str, Callable]:
        """
        Define handlers for custom parameters that need special processing for Workflows.

        Returns:
            Dictionary mapping custom parameter names to handler functions
        """
        return {
            # Storage configuration (now uses shared utilities)
            "storage": self._handle_storage_config,
            # Workflow metadata
            "workflow": self._handle_workflow_metadata,
            # Steps handling (workflow-specific logic)
            "steps": self._handle_steps,
            # Custom business logic parameters (stored in metadata)
            "suggested_actions": self._handle_custom_metadata,
            "escalation_triggers": self._handle_custom_metadata,
            "streaming_config": self._handle_custom_metadata,
            "events_config": self._handle_custom_metadata,
            "context_config": self._handle_custom_metadata,
            "display_config": self._handle_custom_metadata,
        }

    async def create_workflow(
        self,
        component_id: str,
        config: dict[str, Any],
        session_id: str | None = None,
        debug_mode: bool = False,
        user_id: str | None = None,
        db_url: str | None = None,
        **kwargs,
    ) -> Workflow:
        """
        Create an Agno Workflow with dynamic parameter mapping.

        Args:
            component_id: Workflow identifier
            config: Configuration dictionary from YAML
            session_id: Session ID
            debug_mode: Debug mode flag
            user_id: User ID
            db_url: Database URL for storage
            **kwargs: Additional parameters

        Returns:
            Configured Agno Workflow instance
        """
        # Process configuration into Agno parameters
        workflow_params = self._process_config(config, component_id, db_url, **kwargs)

        # Add runtime parameters
        workflow_params.update(
            {
                "workflow_id": component_id,
                "session_id": session_id,
                "debug_mode": debug_mode,
                "user_id": user_id,
            }
        )

        # Filter to only supported Agno parameters
        filtered_params = {
            key: value
            for key, value in workflow_params.items()
            if key in self._supported_params and value is not None
        }

        logger.debug(f"🤖 Creating workflow with {len(filtered_params)} parameters")

        try:
            # Create the workflow with dynamically mapped parameters
            workflow = Workflow(**filtered_params)

            # Add custom metadata
            workflow.metadata = self._create_metadata(config, component_id)

            return workflow

        except Exception as e:
            logger.error(f"🤖 Failed to create workflow {component_id}: {e}")
            logger.debug(f"🤖 Attempted parameters: {list(filtered_params.keys())}")
            raise

    def _process_config(
        self, config: dict[str, Any], component_id: str, db_url: str | None, **kwargs
    ) -> dict[str, Any]:
        """Process configuration dictionary into Agno Workflow parameters."""
        processed = {}

        # Process each configuration section
        for key, value in config.items():
            if key in self._custom_params:
                # Use custom handler
                handler_result = self._custom_params[key](
                    value, config, component_id, db_url, **kwargs
                )
                if isinstance(handler_result, dict):
                    processed.update(handler_result)
                else:
                    processed[key] = handler_result
            elif key in self._supported_params:
                # Direct mapping for supported parameters
                processed[key] = value
            else:
                # Log unknown parameters for debugging
                logger.debug(
                    f"🤖 Unknown Workflow parameter '{key}' in config for {component_id}"
                )

        return processed

    def _handle_storage_config(
        self,
        storage_config: dict[str, Any],
        config: dict[str, Any],
        component_id: str,
        db_url: str | None,
        **kwargs,
    ):
        """Handle storage configuration using shared utilities."""
        return create_dynamic_storage(
            storage_config=storage_config,
            component_id=component_id,
            component_mode="workflow",
            db_url=db_url,
        )

    def _handle_workflow_metadata(
        self,
        workflow_config: dict[str, Any],
        config: dict[str, Any],
        component_id: str,
        db_url: str | None,
        **kwargs,
    ) -> dict[str, Any]:
        """Handle workflow metadata section."""
        return {
            "name": workflow_config.get("name", f"Workflow {component_id}"),
            "description": workflow_config.get("description"),
        }

    def _handle_steps(
        self,
        steps_config: Any,
        config: dict[str, Any],
        component_id: str,
        db_url: str | None,
        **kwargs,
    ) -> Any:
        """
        Handle workflow steps configuration (workflow-specific logic).

        Steps handling depends on the specific workflow implementation.
        This could be a function, a list of steps, or custom step configuration.
        """
        logger.info(f"🤖 Processing steps for workflow {component_id}")

        # Steps can be:
        # 1. A callable function that defines the workflow
        # 2. A list of step configurations
        # 3. A custom step processing configuration

        if callable(steps_config):
            logger.debug(f"🤖 Steps config is a callable function for {component_id}")
        elif isinstance(steps_config, list):
            logger.debug(
                f"🤖 Steps config is a list of {len(steps_config)} steps for {component_id}"
            )
        else:
            logger.debug(f"🤖 Steps config is custom configuration for {component_id}")

        return steps_config

    def _handle_custom_metadata(
        self,
        value: Any,
        config: dict[str, Any],
        component_id: str,
        db_url: str | None,
        **kwargs,
    ) -> None:
        """Handle custom parameters that should be stored in metadata only."""
        return

    def _create_metadata(
        self, config: dict[str, Any], component_id: str
    ) -> dict[str, Any]:
        """Create metadata dictionary for the workflow."""
        workflow_config = config.get("workflow", {})

        return {
            "version": workflow_config.get("version", 1),
            "loaded_from": "proxy_workflows",
            "workflow_id": component_id,
            "agno_parameters_count": len(self._supported_params),
            "custom_parameters": {
                "suggested_actions": config.get("suggested_actions", {}),
                "escalation_triggers": config.get("escalation_triggers", {}),
                "streaming_config": config.get("streaming_config", {}),
                "events_config": config.get("events_config", {}),
                "context_config": config.get("context_config", {}),
                "display_config": config.get("display_config", {}),
            },
        }

    def get_supported_parameters(self) -> set[str]:
        """Get the set of currently supported Agno Workflow parameters."""
        return self._supported_params.copy()

    def validate_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Validate configuration and return analysis.

        Args:
            config: Configuration dictionary

        Returns:
            Dictionary with validation results
        """
        supported = []
        custom = []
        unknown = []

        for key in config:
            if key in self._supported_params:
                supported.append(key)
            elif key in self._custom_params:
                custom.append(key)
            else:
                unknown.append(key)

        return {
            "supported_agno_params": supported,
            "custom_params": custom,
            "unknown_params": unknown,
            "total_agno_params_available": len(self._supported_params),
            "coverage_percentage": (len(supported) / len(self._supported_params)) * 100,
        }
