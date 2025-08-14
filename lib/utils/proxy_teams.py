"""
Team Proxy Module

Specialized proxy for creating Agno Team instances with dynamic parameter mapping.
This module handles team-specific configuration processing including member loading
while leveraging shared storage utilities to eliminate code duplication.
"""

import inspect
from collections.abc import Callable
from typing import Any

from agno.agent import Agent
from agno.team import Team

from lib.logging import logger

from .agno_storage_utils import create_dynamic_storage


class AgnoTeamProxy:
    """
    Dynamic proxy that automatically maps config parameters to Agno Team constructor.

    This proxy introspects the current Agno Team class to discover all supported
    parameters and automatically maps config values, ensuring future compatibility
    even when Agno adds new Team parameters.
    """

    def __init__(self):
        """Initialize the proxy by introspecting the current Agno Team class."""
        self._supported_params = self._discover_team_parameters()
        self._custom_params = self._get_custom_parameter_handlers()
        logger.debug(
            f"🤖 AgnoTeamProxy initialized with {len(self._supported_params)} Agno Team parameters"
        )

    def _discover_team_parameters(self) -> set[str]:
        """
        Dynamically discover all parameters supported by the Agno Team constructor.

        Returns:
            Set of parameter names that Team.__init__ accepts
        """
        try:
            # Get the Team constructor signature
            sig = inspect.signature(Team.__init__)

            # Extract all parameter names except 'self'
            params = {
                param_name
                for param_name, param in sig.parameters.items()
                if param_name != "self"
            }

            logger.debug(
                f"🤖 Discovered {len(params)} Agno Team parameters: {sorted(params)}"
            )
            return params

        except Exception as e:
            logger.error(f"🤖 Failed to introspect Agno Team parameters: {e}")
            # Fallback to known parameters if introspection fails
            return self._get_fallback_parameters()

    def _get_fallback_parameters(self) -> set[str]:
        """
        Fallback set of known Agno Team parameters if introspection fails.

        Returns:
            Set of known parameter names from current Agno version
        """
        return {
            # Core Team Settings
            "members",
            "mode",
            "model",
            "name",
            "team_id",
            "user_id",
            "role",
            # Session Settings
            "session_id",
            "session_name",
            "session_state",
            "team_session_state",
            "workflow_session_state",
            "add_state_in_messages",
            "cache_session",
            # System Message
            "description",
            "instructions",
            "expected_output",
            "additional_context",
            "success_criteria",
            "markdown",
            "add_datetime_to_instructions",
            "add_location_to_instructions",
            "add_member_tools_to_system_message",
            "system_message",
            "system_message_role",
            # Context
            "context",
            "add_context",
            # Knowledge
            "knowledge",
            "knowledge_filters",
            "add_references",
            "enable_agentic_knowledge_filters",
            "retriever",
            "references_format",
            "enable_agentic_context",
            "share_member_interactions",
            "get_member_information_tool",
            "search_knowledge",
            "read_team_history",
            # Tools
            "tools",
            "mcp_servers",
            "show_tool_calls",
            "tool_call_limit",
            "tool_choice",
            "tool_hooks",
            # Response Processing
            "response_model",
            "parser_model",
            "parser_model_prompt",
            "use_json_mode",
            "parse_response",
            # Memory
            "memory",
            "enable_agentic_memory",
            "enable_user_memories",
            "add_memory_references",
            "enable_session_summaries",
            "add_session_summary_references",
            "enable_team_history",
            "add_history_to_messages",
            "num_of_interactions_from_history",
            "num_history_runs",
            # Storage
            "storage",
            "extra_data",
            # Reasoning
            "reasoning",
            "reasoning_model",
            "reasoning_agent",
            "reasoning_min_steps",
            "reasoning_max_steps",
            # Streaming
            "stream",
            "stream_intermediate_steps",
            "store_events",
            "events_to_skip",
            "stream_member_events",
            "show_members_responses",
            # Debug/Monitoring
            "debug_mode",
            "debug_level",
            "monitoring",
            "telemetry",
        }

    def _get_custom_parameter_handlers(self) -> dict[str, Callable]:
        """
        Define handlers for custom parameters that need special processing for Teams.

        Returns:
            Dictionary mapping custom parameter names to handler functions
        """
        return {
            # Model configuration with thinking support
            "model": self._handle_model_config,
            # Storage configuration (now uses shared utilities)
            "storage": self._handle_storage_config,
            # Memory configuration
            "memory": self._handle_memory_config,
            # Team metadata
            "team": self._handle_team_metadata,
            # Members handling (team-specific logic)
            "members": self._handle_members,
            # MCP servers (Agno native integration)
            "mcp_servers": self._handle_mcp_servers,
            # Tools handling (for native Agno tools only)
            "tools": self._handle_tools_config,
            # Custom business logic parameters (stored in metadata)
            "suggested_actions": self._handle_custom_metadata,
            "escalation_triggers": self._handle_custom_metadata,
            "streaming_config": self._handle_custom_metadata,
            "events_config": self._handle_custom_metadata,
            "context_config": self._handle_custom_metadata,
            "display_config": self._handle_custom_metadata,
        }

    async def create_team(
        self,
        component_id: str,
        config: dict[str, Any],
        session_id: str | None = None,
        debug_mode: bool = False,
        user_id: str | None = None,
        db_url: str | None = None,
        metrics_service: object | None = None,
        **kwargs,
    ) -> Team:
        """
        Create an Agno Team with dynamic parameter mapping.

        Args:
            component_id: Team identifier
            config: Configuration dictionary from YAML
            session_id: Session ID
            debug_mode: Debug mode flag
            user_id: User ID
            db_url: Database URL for storage
            metrics_service: Optional metrics collection service
            **kwargs: Additional parameters

        Returns:
            Configured Agno Team instance
        """
        # Process configuration into Agno parameters
        team_params = await self._process_config(config, component_id, db_url, **kwargs)

        # Add runtime parameters
        team_params.update(
            {
                "team_id": component_id,
                "session_id": session_id,
                "debug_mode": debug_mode,
                "user_id": user_id,
            }
        )

        # Filter to only supported Agno parameters
        filtered_params = {
            key: value
            for key, value in team_params.items()
            if key in self._supported_params and value is not None
        }

        logger.debug(f"🤖 Creating team with {len(filtered_params)} parameters")

        try:
            # Create the team with dynamically mapped parameters
            team = Team(**filtered_params)

            # Add custom metadata
            team.metadata = self._create_metadata(config, component_id)

            # Store metrics service for later use
            if metrics_service:
                team.metadata["metrics_service"] = metrics_service

            # Wrap team.run() method for metrics collection
            if metrics_service and hasattr(metrics_service, "collect_from_response"):
                team = self._wrap_team_with_metrics(
                    team, component_id, config, metrics_service
                )

            return team

        except Exception as e:
            logger.error(f"🤖 Failed to create team {component_id}: {e}")
            logger.debug(f"🤖 Attempted parameters: {list(filtered_params.keys())}")
            raise

    async def _process_config(
        self, config: dict[str, Any], component_id: str, db_url: str | None, **kwargs
    ) -> dict[str, Any]:
        """Process configuration dictionary into Agno Team parameters."""
        processed = {}

        # Process each configuration section
        for key, value in config.items():
            if key in self._custom_params:
                # Use custom handler
                if key == "members":
                    # Special handling for async members handler
                    handler_result = await self._custom_params[key](
                        value, config, component_id, db_url, **kwargs
                    )
                else:
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
                    f"🤖 Unknown Team parameter '{key}' in config for {component_id}"
                )

        return processed

    def _handle_model_config(
        self,
        model_config: dict[str, Any],
        config: dict[str, Any],
        component_id: str,
        db_url: str | None,
        **kwargs,
    ):
        """Handle model configuration with truly dynamic provider support.
        
        Uses runtime introspection instead of hardcoded parameter lists.
        """
        from lib.config.models import resolve_model
        from lib.utils.dynamic_model_resolver import filter_model_parameters
        from lib.config.provider_registry import get_provider_registry
        
        model_id = model_config.get("id")
        if not model_id:
            # Use default resolution
            return resolve_model(model_id=None, **model_config)
        
        # Detect provider and get model class
        provider = get_provider_registry().detect_provider(model_id)
        if not provider:
            # Fallback to standard resolution
            return resolve_model(model_id=model_id, **model_config)
        
        # Get the actual model class
        model_class = get_provider_registry().resolve_model_class(provider, model_id)
        if not model_class:
            # Fallback to standard resolution
            return resolve_model(model_id=model_id, **model_config)
        
        # Use dynamic filtering to only pass parameters the model class accepts
        filtered_config = filter_model_parameters(model_class, model_config)
        
        # Ensure teams default to higher temperature if not specified
        if "temperature" not in filtered_config and "temperature" in inspect.signature(model_class.__init__).parameters:
            filtered_config["temperature"] = 1.0  # Teams often use higher temp
        
        # Return configuration for lazy instantiation by Agno Team instead of creating instances
        return {"id": model_id, **filtered_config}

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
            component_mode="team",
            db_url=db_url,
        )

    def _handle_memory_config(
        self,
        memory_config: dict[str, Any],
        config: dict[str, Any],
        component_id: str,
        db_url: str | None,
        **kwargs,
    ) -> object | None:
        """Handle memory configuration."""
        if memory_config is not None and memory_config.get(
            "enable_user_memories", False
        ):
            from lib.memory.memory_factory import create_team_memory

            # Let MemoryFactoryError bubble up - no silent failures
            return create_team_memory(component_id, db_url)
        return None

    def _handle_team_metadata(
        self,
        team_config: dict[str, Any],
        config: dict[str, Any],
        component_id: str,
        db_url: str | None,
        **kwargs,
    ) -> dict[str, Any]:
        """Handle team metadata section."""
        return {
            "name": team_config.get("name", f"Team {component_id}"),
            "description": team_config.get("description"),
            "mode": team_config.get("mode", "route"),
        }

    async def _handle_members(
        self,
        members_config: list[str],
        config: dict[str, Any],
        component_id: str,
        db_url: str | None,
        **kwargs,
    ) -> list[Agent]:
        """
        Handle team members configuration (team-specific logic).

        This is unique to teams and loads member agents from the registry.
        """
        members = []

        for member_name in members_config:
            try:
                # Load member agents using the agent registry
                from ai.agents.registry import get_agent

                member_agent = await get_agent(
                    member_name,
                    session_id=kwargs.get("session_id"),
                    debug_mode=kwargs.get("debug_mode", False),
                    user_id=kwargs.get("user_id"),
                )
                members.append(member_agent)
                logger.debug(f"🤖 Loaded team member: {member_name}")
            except Exception as e:
                logger.warning(f"🤖 Could not load team member {member_name}: {e}")

        return members

    def _handle_mcp_servers(
        self,
        mcp_servers_config: list[str],
        config: dict[str, Any],
        component_id: str,
        db_url: str | None,
        **kwargs,
    ) -> list[str]:
        """
        Handle MCP servers configuration using Agno's native integration.

        Agno provides native MCP support via the mcp_servers parameter, eliminating
        the need for manual tool conversion. Just pass the server names directly.

        Args:
            mcp_servers_config: List of MCP server names from YAML
            config: Full team configuration
            component_id: Team identifier
            db_url: Database URL
            **kwargs: Additional parameters

        Returns:
            List of MCP server names for Agno's native integration
        """
        if not mcp_servers_config:
            return []

        # Agno handles MCP integration natively - just pass server names
        logger.info(
            f"🌐 Configured MCP servers for team {component_id}: {', '.join(mcp_servers_config)}"
        )
        return mcp_servers_config

    def _handle_tools_config(
        self,
        tools_config: list[dict[str, Any] | str | object],
        config: dict[str, Any],
        component_id: str,
        db_url: str | None,
        **kwargs,
    ) -> list[dict[str, Any] | str | object]:
        """
        Handle native Agno tools configuration.

        MCP tools are now handled by _handle_mcp_servers using Agno's native integration.
        This method handles native Agno tools like CalculatorTools(), custom @tool functions, etc.

        Args:
            tools_config: List of native Agno tool objects or configurations from YAML
            config: Full team configuration
            component_id: Team identifier
            db_url: Database URL
            **kwargs: Additional parameters

        Returns:
            List of native Agno tools (passed directly to Agno Team constructor)
        """
        if not tools_config:
            return []

        # Process native Agno tools from YAML configuration
        from lib.tools.registry import ToolRegistry

        processed_tools = []
        loaded_tool_names = []

        for tool_config in tools_config:
            if isinstance(tool_config, dict) and "name" in tool_config:
                tool_name = tool_config["name"]
                if tool_name == "ShellTools":
                    # Load native Agno ShellTools
                    shell_tool = ToolRegistry._load_native_agno_tool("ShellTools")
                    if shell_tool:
                        processed_tools.append(shell_tool)
                        loaded_tool_names.append(tool_name)
                    else:
                        logger.warning(f"Failed to load native Agno tool: {tool_name}")
                else:
                    logger.warning(f"Unknown native tool type: {tool_name}")
            else:
                # Handle other tool formats or pass through as-is
                processed_tools.append(tool_config)
                loaded_tool_names.append(str(tool_config))

        if loaded_tool_names:
            logger.info(
                f"🤖 Loaded native tools for team {component_id}: {', '.join(loaded_tool_names)}"
            )

        return processed_tools

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
        """Create metadata dictionary for the team."""
        team_config = config.get("team", {})

        return {
            "version": team_config.get("version", 1),
            "loaded_from": "proxy_teams",
            "team_id": component_id,
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

    def _wrap_team_with_metrics(
        self,
        team: Team,
        component_id: str,
        config: dict[str, Any],
        metrics_service: object,
    ) -> Team:
        """
        Wrap team.run() method to automatically collect metrics after execution.

        Args:
            team: The Agno Team instance
            component_id: Team identifier
            config: Team configuration
            metrics_service: Metrics collection service

        Returns:
            Team with wrapped run() method
        """
        # Store original run method
        original_run = team.run

        def wrapped_run(*args, **kwargs):
            """Wrapped run method that collects metrics after execution"""
            response = None
            try:
                # Execute original run method
                response = original_run(*args, **kwargs)

                # Only collect metrics if response is valid
                if response is not None:
                    try:
                        # Extract YAML overrides for metrics
                        yaml_overrides = self._extract_metrics_overrides(config)

                        # Collect metrics from response with validation
                        if hasattr(metrics_service, "collect_from_response"):
                            success = metrics_service.collect_from_response(
                                response=response,
                                agent_name=component_id,
                                execution_type="team",
                                yaml_overrides=yaml_overrides,
                            )
                            if not success:
                                logger.debug(
                                    f"🤖 Metrics collection returned false for team {component_id}"
                                )

                    except Exception as metrics_error:
                        # Don't let metrics collection failures break team execution
                        logger.warning(
                            f"🤖 Metrics collection error for team {component_id}: {metrics_error}"
                        )
                        # Continue execution - metrics failure should not affect team operation

                return response

            except Exception as e:
                # Log original execution failure separately from metrics
                logger.error(f"🤖 Team {component_id} execution failed: {e}")
                raise  # Re-raise the original exception

        # Replace the run method
        team.run = wrapped_run
        return team

    def _extract_metrics_overrides(self, config: dict[str, Any]) -> dict[str, bool]:
        """
        Extract metrics-related overrides from team config.

        Args:
            config: Team configuration dictionary

        Returns:
            Dictionary with metrics overrides
        """
        overrides = {}

        # Check for metrics_enabled in various config sections
        if "metrics_enabled" in config:
            overrides["metrics_enabled"] = config["metrics_enabled"]

        # Check team section
        team_config = config.get("team", {})
        if "metrics_enabled" in team_config:
            overrides["metrics_enabled"] = team_config["metrics_enabled"]

        return overrides

    def get_supported_parameters(self) -> set[str]:
        """Get the set of currently supported Agno Team parameters."""
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
