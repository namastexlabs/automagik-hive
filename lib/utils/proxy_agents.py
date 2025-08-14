"""
Agent Proxy Module

Specialized proxy for creating Agno Agent instances with dynamic parameter mapping.
This module handles agent-specific configuration processing while leveraging
shared storage utilities to eliminate code duplication.
"""

import inspect
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agno.agent import Agent

from lib.logging import logger

from .agno_storage_utils import create_dynamic_storage


class AgnoAgentProxy:
    """
    Dynamic proxy that automatically maps config parameters to Agno Agent constructor.

    This proxy introspects the current Agno Agent class to discover all supported
    parameters and automatically maps config values, ensuring future compatibility
    even when Agno adds new parameters.
    """

    def __init__(self):
        """Initialize the proxy by introspecting the current Agno Agent class."""
        self._supported_params = self._discover_agent_parameters()
        self._custom_params = self._get_custom_parameter_handlers()
        logger.info(
            f"AgnoAgentProxy initialized with {len(self._supported_params)} Agno parameters"
        )

    def _discover_agent_parameters(self) -> set[str]:
        """
        Dynamically discover all parameters supported by the Agno Agent constructor.

        Returns:
            Set of parameter names that Agent.__init__ accepts
        """
        try:
            # Get the Agent constructor signature
            sig = inspect.signature(Agent.__init__)

            # Extract all parameter names except 'self'
            params = {
                param_name
                for param_name, param in sig.parameters.items()
                if param_name != "self"
            }

            logger.debug(
                f"🤖 Discovered {len(params)} Agno Agent parameters: {sorted(params)}"
            )
            return params

        except Exception as e:
            logger.error(f"🤖 Failed to introspect Agno Agent parameters: {e}")
            # Fallback to known parameters if introspection fails
            return self._get_fallback_parameters()

    def _get_fallback_parameters(self) -> set[str]:
        """
        Fallback set of known Agno Agent parameters if introspection fails.

        Returns:
            Set of known parameter names from Agno 1.7.5
        """
        return {
            # Core Agent Settings
            "model",
            "name",
            "agent_id",
            "introduction",
            "user_id",
            # Session Settings
            "session_id",
            "session_name",
            "session_state",
            "search_previous_sessions_history",
            "num_history_sessions",
            "cache_session",
            # Context
            "context",
            "add_context",
            "resolve_context",
            # Memory
            "memory",
            "enable_agentic_memory",
            "enable_user_memories",
            "add_memory_references",
            "enable_session_summaries",
            "add_session_summary_references",
            # History
            "add_history_to_messages",
            "num_history_responses",
            "num_history_runs",
            # Knowledge
            "knowledge",
            "knowledge_filters",
            "enable_agentic_knowledge_filters",
            "add_references",
            "retriever",
            "references_format",
            # Storage
            "storage",
            "extra_data",
            # Tools
            "tools",
            "show_tool_calls",
            "tool_call_limit",
            "tool_choice",
            "tool_hooks",
            # Reasoning
            "reasoning",
            "reasoning_model",
            "reasoning_agent",
            "reasoning_min_steps",
            "reasoning_max_steps",
            # Default Tools
            "read_chat_history",
            "search_knowledge",
            "update_knowledge",
            "read_tool_call_history",
            # System Message
            "system_message",
            "system_message_role",
            "create_default_system_message",
            "description",
            "goal",
            "success_criteria",
            "instructions",
            "expected_output",
            "additional_context",
            # Display
            "markdown",
            "add_name_to_instructions",
            "add_datetime_to_instructions",
            "add_location_to_instructions",
            "timezone_identifier",
            "add_state_in_messages",
            # Extra Messages
            "add_messages",
            "user_message",
            "user_message_role",
            "create_default_user_message",
            # Response Processing
            "retries",
            "delay_between_retries",
            "exponential_backoff",
            "parser_model",
            "parser_model_prompt",
            "response_model",
            "parse_response",
            "output_model",
            "output_model_prompt",
            "structured_outputs",
            "use_json_mode",
            "save_response_to_file",
            # Streaming
            "stream",
            "stream_intermediate_steps",
            # Events
            "store_events",
            "events_to_skip",
            # Team
            "team",
            "team_data",
            "role",
            "respond_directly",
            "add_transfer_instructions",
            "team_response_separator",
            # Debug/Monitoring
            "debug_mode",
            "debug_level",
            "monitoring",
            "telemetry",
        }

    def _get_custom_parameter_handlers(self) -> dict[str, Callable]:
        """
        Define handlers for custom parameters that need special processing.

        Returns:
            Dictionary mapping custom parameter names to handler functions
        """
        return {
            # Our custom knowledge filter system
            "knowledge_filter": self._handle_knowledge_filter,
            # Model configuration with thinking support
            "model": self._handle_model_config,
            # Storage configuration (now uses shared utilities)
            "storage": self._handle_storage_config,
            # Memory configuration
            "memory": self._handle_memory_config,
            # Agent metadata
            "agent": self._handle_agent_metadata,
            # MCP servers (Agno native integration)
            "mcp_servers": self._handle_mcp_servers,
            # Custom business logic parameters (stored in metadata)
            "suggested_actions": self._handle_custom_metadata,
            "escalation_triggers": self._handle_custom_metadata,
            "streaming_config": self._handle_custom_metadata,
            "events_config": self._handle_custom_metadata,
            "context_config": self._handle_custom_metadata,
            "display_config": self._handle_custom_metadata,
            # Display section handler (flattens display parameters)
            "display": self._handle_display_section,
        }

    async def create_agent(
        self,
        component_id: str,
        config: dict[str, Any],
        session_id: str | None = None,
        debug_mode: bool = False,
        user_id: str | None = None,
        db_url: str | None = None,
        metrics_service: object | None = None,
    ) -> Agent:
        """
        Create an Agno Agent with dynamic parameter mapping.

        Args:
            component_id: Agent identifier
            config: Configuration dictionary from YAML
            session_id: Session ID
            debug_mode: Debug mode flag
            user_id: User ID
            db_url: Database URL for storage
            metrics_service: Optional metrics collection service

        Returns:
            Configured Agno Agent instance
        """
        # Process configuration into Agno parameters
        agent_params = self._process_config(config, component_id, db_url)

        # Add runtime parameters
        agent_params.update(
            {
                "agent_id": component_id,
                "session_id": session_id,
                "debug_mode": debug_mode,
                "user_id": user_id,
            }
        )

        # Filter to only supported Agno parameters
        filtered_params = {
            key: value
            for key, value in agent_params.items()
            if key in self._supported_params and value is not None
        }

        logger.debug(f"🤖 Creating agent with {len(filtered_params)} parameters")

        try:
            # Create the agent with dynamically mapped parameters
            agent = Agent(**filtered_params)

            # Add custom metadata
            agent.metadata = self._create_metadata(config, component_id)

            # Store metrics service for later use
            if metrics_service:
                agent.metadata["metrics_service"] = metrics_service

            # Wrap agent.run() method for metrics collection
            if metrics_service and hasattr(metrics_service, "collect_from_response"):
                agent = self._wrap_agent_with_metrics(
                    agent, component_id, config, metrics_service
                )

            return agent

        except Exception as e:
            logger.error(f"🤖 Failed to create agent {component_id}: {e}")
            logger.debug(f"🤖 Attempted parameters: {list(filtered_params.keys())}")
            raise

    def _process_config(
        self, config: dict[str, Any], component_id: str, db_url: str | None
    ) -> dict[str, Any]:
        """
        Process configuration dictionary into Agno Agent parameters.

        Args:
            config: Raw configuration from YAML
            component_id: Agent identifier
            db_url: Database URL

        Returns:
            Dictionary of processed parameters for Agent constructor
        """
        if config is None:
            raise ValueError(f"Config is None for agent {component_id}")

        processed = {}

        # Process each configuration section
        for key, value in config.items():
            if key in self._custom_params:
                # Use custom handler
                handler_result = self._custom_params[key](
                    value, config, component_id, db_url
                )
                if isinstance(handler_result, dict):
                    processed.update(handler_result)
                # Special case: knowledge_filter handler returns knowledge base object
                # that should be assigned to "knowledge" parameter, not "knowledge_filter"
                elif key == "knowledge_filter" and handler_result is not None:
                    processed["knowledge"] = handler_result
                else:
                    processed[key] = handler_result
            elif key in self._supported_params:
                # Direct mapping for supported parameters
                processed[key] = value
            else:
                # Log unknown parameters for debugging
                logger.debug(
                    f"🤖 Unknown parameter '{key}' in config for {component_id}"
                )

        # Post-processing: Merge MCP tools with regular tools
        self._merge_mcp_tools_with_regular_tools(processed, component_id)

        return processed

    def _merge_mcp_tools_with_regular_tools(
        self, processed: dict[str, Any], component_id: str
    ) -> None:
        """
        Merge MCP tools with regular tools in the processed configuration.

        Args:
            processed: Processed configuration dictionary (modified in-place)
            component_id: Agent identifier for logging
        """
        mcp_tools = processed.pop("mcp_tools", [])
        if not mcp_tools:
            return

        # Get existing tools (could be None, list, or other types)
        existing_tools = processed.get("tools", [])

        # Normalize existing tools to list
        if existing_tools is None:
            existing_tools = []
        elif not isinstance(existing_tools, list):
            existing_tools = [existing_tools]

        # Add MCP tools to the list
        combined_tools = existing_tools + mcp_tools
        processed["tools"] = combined_tools

        logger.debug(
            f"🌐 Merged {len(mcp_tools)} MCP tool instances with {len(existing_tools)} regular tools for agent {component_id}"
        )

    def _handle_model_config(
        self,
        model_config: dict[str, Any],
        config: dict[str, Any],
        component_id: str,
        db_url: str | None,
    ):
        """Handle model configuration with dynamic parameter filtering.
        
        Uses runtime introspection to determine which parameters
        belong to the model vs the Agent, ensuring compatibility
        across Agno updates.
        """
        from lib.config.models import resolve_model
        from lib.utils.dynamic_model_resolver import filter_model_parameters
        from lib.config.provider_registry import get_provider_registry
        
        # Debug: Log the incoming model config to trace the issue
        logger.info(f"🔍 TEMPLATE-AGENT MODEL CONFIG for {component_id}: {model_config}")
        print(f"🔍 TEMPLATE-AGENT MODEL CONFIG for {component_id}: {model_config}")
        
        model_id = model_config.get("id")
        provider = model_config.get("provider")
        
        # Use dynamic introspection to determine model parameters
        # This automatically adapts to ANY Agno updates without requiring code changes
        try:
            # First, get the provider and model class to inspect its parameters
            registry = get_provider_registry()
            detected_provider = registry.detect_provider(model_id) if model_id else provider
            
            if detected_provider:
                # Get the specific model class for this provider/model
                provider_classes = registry.get_provider_classes(detected_provider)
                model_class = registry.resolve_model_class(detected_provider, model_id or "default")
                
                # Use our dynamic model resolver to filter parameters
                filtered_model_config = filter_model_parameters(model_class, model_config)
                
                logger.debug(f"🔍 Dynamically filtered model config for {component_id}: {filtered_model_config}")
                if len(model_config) != len(filtered_model_config):
                    filtered_out = set(model_config.keys()) - set(filtered_model_config.keys())
                    logger.debug(f"🔍 Dynamically filtered out parameters: {filtered_out}")
                
            else:
                # Fallback: if we can't detect provider, use original config and let resolve_model handle it
                logger.warning(f"⚠️ Could not detect provider for {model_id}, using original config")
                filtered_model_config = model_config
                
        except Exception as e:
            logger.warning(f"🔍 Dynamic filtering failed for {component_id}: {e}. Using original config.")
            filtered_model_config = model_config
        
        # Fix: Return model configuration instead of creating instances during startup
        # This prevents multiple Agno model instantiations during bulk component discovery
        if model_id:
            logger.debug(f"🚀 Configured model: {model_id} for {component_id}")
            # Return configuration for lazy instantiation by Agno Agent
            return {"id": model_id, **filtered_model_config}
        else:
            # Fallback to default resolution only when no model ID is specified
            logger.warning(f"⚠️ No model ID specified for {component_id}, using default resolution")
            return resolve_model(model_id=None, **filtered_model_config)

    def _handle_storage_config(
        self,
        storage_config: dict[str, Any],
        config: dict[str, Any],
        component_id: str,
        db_url: str | None,
    ):
        """Handle storage configuration using shared utilities."""
        return create_dynamic_storage(
            storage_config=storage_config,
            component_id=component_id,
            component_mode="agent",
            db_url=db_url,
        )

    def _handle_memory_config(
        self,
        memory_config: dict[str, Any],
        config: dict[str, Any],
        component_id: str,
        db_url: str | None,
    ) -> object | None:
        """Handle memory configuration."""
        if memory_config is not None and memory_config.get(
            "enable_user_memories", False
        ):
            from lib.memory.memory_factory import create_agent_memory

            # Let MemoryFactoryError bubble up - no silent failures
            return create_agent_memory(component_id, db_url)
        return None

    def _handle_agent_metadata(
        self,
        agent_config: dict[str, Any],
        config: dict[str, Any],
        component_id: str,
        db_url: str | None,
    ) -> dict[str, Any]:
        """Handle agent metadata section."""
        return {
            "name": agent_config.get("name", f"Agent {component_id}"),
            "description": agent_config.get("description"),
            "role": agent_config.get("role"),
        }

    def _handle_knowledge_filter(
        self,
        knowledge_filter: dict[str, Any],
        config: dict[str, Any],
        component_id: str,
        db_url: str | None,
    ) -> object | None:
        """Handle custom knowledge filter system."""
        try:
            # Knowledge base creation is now handled by shared factory pattern

            # Load global knowledge config first
            try:
                from lib.utils.version_factory import load_global_knowledge_config

                global_knowledge = load_global_knowledge_config()
            except Exception:
                global_knowledge = {}

            # Use global config as primary source (csv_file_path should not be in agent configs)
            csv_path_raw = global_knowledge.get("csv_file_path")
            if csv_path_raw:
                # Resolve relative path to knowledge directory (like knowledge_factory.py)
                csv_path = str(
                    Path(__file__).parent.parent / "knowledge" / csv_path_raw
                )
                logger.debug(
                    f"🤖 Resolved CSV path for {component_id}", csv_path=csv_path
                )
            else:
                csv_path = None
            max_results = knowledge_filter.get(
                "max_results", global_knowledge.get("max_results", 10)
            )

            # Warn if agent config has csv_file_path (should be removed)
            if "csv_file_path" in knowledge_filter:
                logger.warning(
                    "csv_file_path found in agent config - should use global config instead",
                    component=component_id,
                    agent_path=knowledge_filter["csv_file_path"],
                )

            if csv_path and db_url:
                # Use shared knowledge base from factory to avoid duplicate CSV processing
                try:
                    from lib.knowledge.knowledge_factory import get_knowledge_base

                    knowledge_base = get_knowledge_base(
                        config=global_knowledge,
                        db_url=db_url,
                        num_documents=max_results,
                        csv_path=csv_path,
                    )
                    logger.debug(f"🤖 Using shared knowledge base for {component_id}")
                except Exception as e:
                    logger.warning(f"🤖 Failed to load shared knowledge base: {e}")

                return knowledge_base
        except Exception as e:
            logger.warning(
                f"🤖 Failed to create knowledge base for {component_id}: {e}"
            )

        return None

    def _handle_custom_metadata(
        self,
        value: Any,
        config: dict[str, Any],
        component_id: str,
        db_url: str | None,
    ) -> None:
        """Handle custom parameters that should be stored in metadata only."""
        # These parameters are not passed to Agent constructor
        # They are stored in metadata via _create_metadata
        return

    def _handle_display_section(
        self,
        display_config: dict[str, Any],
        config: dict[str, Any],
        component_id: str,
        db_url: str | None,
    ) -> dict[str, Any]:
        """Handle display section by flattening display parameters to root level."""
        if not isinstance(display_config, dict):
            logger.warning(
                f"🤖 Invalid display config for {component_id}: expected dict, got {type(display_config)}"
            )
            return {}

        # Flatten display parameters to root level for Agno Agent
        flattened = {}
        for key, value in display_config.items():
            if key in self._supported_params:
                flattened[key] = value
            else:
                logger.debug(f"🤖 Unknown display parameter '{key}' for {component_id}")

        logger.debug(
            f"🤖 Flattened {len(flattened)} display parameters for {component_id}"
        )
        return flattened

    def _handle_mcp_servers(
        self,
        mcp_servers_config: list[str],
        config: dict[str, Any],
        component_id: str,
        db_url: str | None,
    ) -> dict[str, Any]:
        """
        Handle MCP servers configuration with granular tool control.

        Supports both legacy format and new granular patterns:
        - "server_name" - All tools from server (legacy)
        - "server_name:*" - All tools from server (explicit)
        - "server_name:tool_name" - Only specific tool from server

        Args:
            mcp_servers_config: List of MCP server patterns from YAML
            config: Full agent configuration
            component_id: Agent identifier
            db_url: Database URL

        Returns:
            Dictionary with 'mcp_tools' key containing list of configured MCPTools instances
        """
        if not mcp_servers_config:
            return {}

        mcp_tools = []
        processed_servers = []

        for server_pattern in mcp_servers_config:
            try:
                # Parse granular pattern: "server_name:tool_pattern"
                if ":" in server_pattern:
                    server_name, tool_pattern = server_pattern.split(":", 1)
                else:
                    # Legacy format: just server name (all tools)
                    server_name = server_pattern
                    tool_pattern = "*"

                # Create MCPTools with granular control
                mcp_tool = self._create_mcp_tool_with_filters(
                    server_name, tool_pattern, component_id
                )

                if mcp_tool:
                    mcp_tools.append(mcp_tool)
                    processed_servers.append(f"{server_name}:{tool_pattern}")

            except Exception as e:
                logger.warning(
                    f"🌐 Failed to configure MCP server pattern '{server_pattern}' for {component_id}: {e}"
                )
                continue

        logger.info(
            f"🌐 Configured {len(mcp_tools)} MCP tool instances for agent {component_id}: {', '.join(processed_servers)}"
        )

        # Return as dictionary to be merged with other tools
        return {"mcp_tools": mcp_tools} if mcp_tools else {}

    def _create_mcp_tool_with_filters(
        self, server_name: str, tool_pattern: str, component_id: str
    ) -> object | None:
        """
        Create MCPTools instance with granular tool filtering.

        Args:
            server_name: MCP server name
            tool_pattern: Tool pattern ("*" for all, "specific_tool" for one tool)
            component_id: Agent identifier for logging

        Returns:
            MCPTools instance with appropriate filters, or None if failed
        """
        try:
            from agno.tools.mcp import MCPTools

            from lib.mcp import MCPCatalog

            # Get server configuration
            catalog = MCPCatalog()
            if not catalog.has_server(server_name):
                logger.warning(
                    f"🌐 MCP server '{server_name}' not available for agent {component_id} - tool will be skipped"
                )
                return None

            server_config = catalog.get_server_config(server_name)

            # Prepare MCPTools parameters
            mcp_params = {
                "env": server_config.env or {},
            }

            # Configure based on server type
            if server_config.is_sse_server:
                mcp_params.update({"url": server_config.url, "transport": "sse"})
            elif server_config.is_command_server:
                command_parts = [server_config.command]
                if server_config.args:
                    command_parts.extend(server_config.args)
                mcp_params.update(
                    {"command": " ".join(command_parts), "transport": "stdio"}
                )
            else:
                logger.warning(
                    f"🌐 Unknown server type for '{server_name}' for agent {component_id} - tool will be skipped"
                )
                return None

            # Apply granular tool filtering
            if tool_pattern != "*":
                # Specific tool pattern: include only the requested tool
                # Note: The actual tool name in MCP is just the tool name, not prefixed
                mcp_params["include_tools"] = [tool_pattern]
                logger.debug(
                    f"🌐 Filtering MCP server '{server_name}' to include only tool: {tool_pattern}"
                )
            else:
                logger.debug(f"🌐 Including all tools from MCP server '{server_name}'")

            # Create MCPTools instance
            return MCPTools(**mcp_params)

        except Exception as e:
            # Escape curly braces in error message to prevent Loguru formatting issues
            error_msg = str(e).replace("{", "{{").replace("}", "}}")
            logger.warning(
                f"🌐 Failed to create MCP tool for {server_name}:{tool_pattern} - {error_msg} - tool will be skipped"
            )
            return None

    def _create_metadata(
        self, config: dict[str, Any], component_id: str
    ) -> dict[str, Any]:
        """Create metadata dictionary for the agent."""
        agent_config = config.get("agent", {})

        return {
            "version": agent_config.get("version", 1),
            "loaded_from": "proxy_agents",
            "agent_id": component_id,
            "agno_parameters_count": len(self._supported_params),
            "custom_parameters": {
                "knowledge_filter": config.get("knowledge_filter", {}),
                "suggested_actions": config.get("suggested_actions", {}),
                "escalation_triggers": config.get("escalation_triggers", {}),
                "streaming_config": config.get("streaming_config", {}),
                "events_config": config.get("events_config", {}),
                "context_config": config.get("context_config", {}),
                "display_config": config.get("display_config", {}),
                "display": config.get("display", {}),
            },
        }

    def _wrap_agent_with_metrics(
        self,
        agent: Agent,
        component_id: str,
        config: dict[str, Any],
        metrics_service: object,
    ) -> Agent:
        """
        Wrap agent.run() method to automatically collect metrics after execution.

        Args:
            agent: The Agno Agent instance
            component_id: Agent identifier
            config: Agent configuration
            metrics_service: Metrics collection service

        Returns:
            Agent with wrapped run() method
        """
        logger.debug(
            f"Applying metrics wrapper to agent {component_id}",
            metrics_service_type=type(metrics_service).__name__,
            has_collect_from_response=hasattr(metrics_service, "collect_from_response"),
            agent_type=type(agent).__name__,
        )

        # Store original run method
        original_run = agent.run

        def wrapped_run(*args, **kwargs):
            """Wrapped run method that collects metrics after execution"""
            logger.debug(f"Agent {component_id} wrapped run() invoked")

            response = None
            try:
                # Execute original run method
                response = original_run(*args, **kwargs)

                logger.debug(
                    f"Agent {component_id} execution completed",
                    response_received=response is not None,
                )

                # Only collect metrics if response is valid
                if response is not None:
                    try:
                        # Extract YAML overrides for metrics
                        yaml_overrides = self._extract_metrics_overrides(config)

                        logger.debug(f"Collecting metrics for agent {component_id}")

                        # Collect metrics from response with validation
                        if hasattr(metrics_service, "collect_from_response"):
                            success = metrics_service.collect_from_response(
                                response=response,
                                agent_name=component_id,
                                execution_type="agent",
                                yaml_overrides=yaml_overrides,
                            )
                            logger.debug(
                                f"Metrics collection for {component_id}: {'success' if success else 'failed'}"
                            )
                            if not success:
                                logger.debug(
                                    f"🤖 Metrics collection returned false for agent {component_id}"
                                )
                        else:
                            logger.debug(
                                f"No collect_from_response method on metrics service for {component_id}"
                            )

                    except Exception as metrics_error:
                        # Don't let metrics collection failures break agent execution
                        logger.warning(
                            f"Metrics collection error for agent {component_id}: {metrics_error}"
                        )
                        # Continue execution - metrics failure should not affect agent operation

                return response

            except Exception as e:
                # Log original execution failure separately from metrics
                logger.error(f"🤖 Agent {component_id} execution failed: {e}")
                raise  # Re-raise the original exception

        # Replace both sync and async run methods for comprehensive coverage
        agent.run = wrapped_run

        # Also wrap arun (async run) method if it exists
        if hasattr(agent, "arun"):
            original_arun = agent.arun

            async def wrapped_arun(*args, **kwargs):
                """Wrapped arun method that collects metrics after execution"""
                logger.debug(f"Agent {component_id} wrapped arun() invoked")

                response = None
                try:
                    # Execute original arun method
                    response = await original_arun(*args, **kwargs)

                    logger.debug(
                        f"Agent {component_id} async execution completed",
                        response_received=response is not None,
                    )

                    # Only collect metrics if response is valid
                    if response is not None:
                        try:
                            # Extract YAML overrides for metrics
                            yaml_overrides = self._extract_metrics_overrides(config)

                            logger.debug(
                                f"Collecting async metrics for agent {component_id}"
                            )

                            # Collect metrics from response with validation
                            if hasattr(metrics_service, "collect_from_response"):
                                success = metrics_service.collect_from_response(
                                    response=response,
                                    agent_name=component_id,
                                    execution_type="agent",
                                    yaml_overrides=yaml_overrides,
                                )
                                logger.debug(
                                    f"Async metrics collection for {component_id}: {'success' if success else 'failed'}"
                                )
                                if not success:
                                    logger.debug(
                                        f"🤖 Async metrics collection returned false for agent {component_id}"
                                    )
                            else:
                                logger.debug(
                                    f"No collect_from_response method on metrics service for {component_id}"
                                )

                        except Exception as metrics_error:
                            # Don't let metrics collection failures break agent execution
                            logger.warning(
                                f"Async metrics collection error for agent {component_id}: {metrics_error}"
                            )
                            # Continue execution - metrics failure should not affect agent operation

                    return response

                except Exception as e:
                    # Log original execution failure separately from metrics
                    logger.error(f"🤖 Agent {component_id} async execution failed: {e}")
                    raise  # Re-raise the original exception

            agent.arun = wrapped_arun
            logger.debug(
                f"Both run() and arun() methods wrapped for agent {component_id}"
            )
        else:
            logger.debug(
                f"Only run() method wrapped for agent {component_id} (no arun method)"
            )

        return agent

    def _extract_metrics_overrides(self, config: dict[str, Any]) -> dict[str, bool]:
        """
        Extract metrics-related overrides from agent config.

        Args:
            config: Agent configuration dictionary

        Returns:
            Dictionary with metrics overrides
        """
        overrides = {}

        # Check for metrics_enabled in various config sections
        if "metrics_enabled" in config:
            overrides["metrics_enabled"] = config["metrics_enabled"]

        # Check agent section
        agent_config = config.get("agent", {})
        if "metrics_enabled" in agent_config:
            overrides["metrics_enabled"] = agent_config["metrics_enabled"]

        return overrides

    def get_supported_parameters(self) -> set[str]:
        """Get the set of currently supported Agno Agent parameters."""
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
