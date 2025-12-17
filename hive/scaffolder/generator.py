"""YAML to Agno Agent/Team/Workflow generator.

This module converts YAML configuration files into actual Agno components.
Handles model resolution, tool loading, knowledge base setup, and MCP integration.

12-year-old friendly: Give it a YAML file, get back a working agent!
"""

import os
import re
from typing import Any

import yaml
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow

from hive.config.builtin_tools import load_builtin_tool
from hive.scaffolder.validator import ConfigValidator


class GeneratorError(Exception):
    """Configuration generation failed."""

    pass


class ConfigGenerator:
    """Generates Agno components from YAML configs."""

    # Class-level cache for database instances to ensure singleton behavior
    # Key: (storage_type, connection_string/db_file) - Note: table_name excluded
    # Value: Database instance
    # Rationale: Agno generates DB IDs based on db_file alone. Multiple agents
    # can share one DB instance with different table_names for their sessions.
    _db_cache: dict[tuple[str, str], Any] = {}

    @classmethod
    def _extract_section_params(cls, config: dict, section: str, param_map: dict[str, str] | None = None) -> dict:
        """Extract parameters from a config section with optional key remapping.

        Args:
            config: Full configuration dictionary
            section: Section name to extract from
            param_map: Optional mapping of config_key -> agno_param_name

        Returns:
            Dictionary of parameters ready for Agno constructor
        """
        section_config = config.get(section, {})
        if not section_config:
            return {}

        params = {}
        for key, value in section_config.items():
            if value is not None:
                # Use remapped name if provided, otherwise use original key
                param_name = param_map.get(key, key) if param_map else key
                params[param_name] = value

        return params

    @classmethod
    def _load_pydantic_model(cls, import_path: str) -> Any:
        """Load a Pydantic model class from import path.

        Args:
            import_path: Dotted import path (e.g., 'myapp.models.ResponseModel')

        Returns:
            Pydantic model class

        Raises:
            GeneratorError: If loading fails
        """
        if not import_path or not isinstance(import_path, str):
            return None

        try:
            module_path, class_name = import_path.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        except Exception as e:
            raise GeneratorError(f"Failed to load Pydantic model '{import_path}': {e}") from e

    @classmethod
    def _load_hooks(cls, hook_paths: list | None) -> list:
        """Load hook functions from import paths.

        Args:
            hook_paths: List of dotted import paths to hook functions

        Returns:
            List of callable hook functions
        """
        if not hook_paths:
            return []

        hooks = []
        for path in hook_paths:
            if isinstance(path, str):
                try:
                    module_path, func_name = path.rsplit(".", 1)
                    module = __import__(module_path, fromlist=[func_name])
                    func = getattr(module, func_name)
                    if callable(func):
                        hooks.append(func)
                except Exception as e:
                    raise GeneratorError(f"Failed to load hook '{path}': {e}") from e
        return hooks

    @classmethod
    def _build_agent_params(cls, config: dict) -> dict:
        """Build complete Agno Agent parameters from config.

        Extracts all Agno Agent parameters from the Hive config structure.
        Supports all parameters from https://docs.agno.com/reference/agents/agent

        Args:
            config: Hive agent configuration dictionary

        Returns:
            Dictionary of parameters ready for Agent constructor
        """
        agent_config = config.get("agent", {})
        agent_params: dict[str, Any] = {}

        # Core parameters
        agent_params["name"] = agent_config.get("name")
        agent_params["description"] = agent_config.get("description")
        agent_params["instructions"] = config.get("instructions")

        # Parse model
        model_string = agent_config.get("model")
        if model_string:
            agent_params["model"] = cls._parse_model(model_string)

        # Role (for team membership)
        if agent_config.get("role"):
            agent_params["role"] = agent_config.get("role")

        # Load tools
        tools = cls._load_tools(config.get("tools", []))
        if tools:
            agent_params["tools"] = tools

        # Setup knowledge base
        knowledge = cls._setup_knowledge(config.get("knowledge"))
        if knowledge:
            agent_params["knowledge"] = knowledge

        # Setup storage (db parameter)
        db = cls._setup_storage(config.get("storage"))
        if db:
            agent_params["db"] = db
            # Auto-enable history when db is configured
            agent_params["add_history_to_context"] = True

        # MCP servers
        if config.get("mcp_servers"):
            agent_params["mcp_servers"] = config.get("mcp_servers")

        # Metadata and dependencies
        if config.get("metadata"):
            agent_params["metadata"] = config.get("metadata")
        if config.get("dependencies"):
            agent_params["dependencies"] = config.get("dependencies")

        # Session parameters
        session_config = config.get("session", {})
        session_params = [
            "user_id",
            "session_id",
            "session_state",
            "add_session_state_to_context",
            "enable_agentic_state",
            "overwrite_db_session_state",
            "cache_session",
        ]
        for param in session_params:
            if session_config.get(param) is not None:
                agent_params[param] = session_config[param]

        # Reasoning parameters
        reasoning_config = config.get("reasoning", {})
        if reasoning_config.get("enabled"):
            agent_params["reasoning"] = True
        if reasoning_config.get("model"):
            agent_params["reasoning_model"] = cls._parse_model(reasoning_config["model"])
        if reasoning_config.get("min_steps"):
            agent_params["reasoning_min_steps"] = reasoning_config["min_steps"]
        if reasoning_config.get("max_steps"):
            agent_params["reasoning_max_steps"] = reasoning_config["max_steps"]

        # Memory parameters
        memory_config = config.get("memory", {})
        memory_params = [
            "enable_agentic_memory",
            "enable_user_memories",
            "add_memories_to_context",
            "enable_session_summaries",
            "add_session_summary_to_context",
        ]
        for param in memory_params:
            if memory_config.get(param) is not None:
                agent_params[param] = memory_config[param]

        # History parameters
        history_config = config.get("history", {})
        history_params = [
            "add_history_to_context",
            "num_history_runs",
            "num_history_messages",
            "search_session_history",
            "num_history_sessions",
            "read_chat_history",
            "read_tool_call_history",
        ]
        for param in history_params:
            if history_config.get(param) is not None:
                agent_params[param] = history_config[param]

        # Tool control parameters
        tool_control = config.get("tool_control", {})
        if tool_control.get("tool_choice") is not None:
            agent_params["tool_choice"] = tool_control["tool_choice"]
        if tool_control.get("tool_call_limit") is not None:
            agent_params["tool_call_limit"] = tool_control["tool_call_limit"]
        if tool_control.get("max_tool_calls_from_history") is not None:
            agent_params["max_tool_calls_from_history"] = tool_control["max_tool_calls_from_history"]
        if tool_control.get("search_knowledge") is not None:
            agent_params["search_knowledge"] = tool_control["search_knowledge"]
        if tool_control.get("update_knowledge") is not None:
            agent_params["update_knowledge"] = tool_control["update_knowledge"]

        # Context enrichment
        context_config = config.get("context", {})
        context_params = [
            "add_name_to_context",
            "add_datetime_to_context",
            "add_location_to_context",
            "timezone_identifier",
            "additional_context",
            "expected_output",
        ]
        for param in context_params:
            if context_config.get(param) is not None:
                agent_params[param] = context_config[param]

        # Output configuration
        output_config = config.get("output", {})
        if output_config.get("output_schema"):
            agent_params["output_schema"] = cls._load_pydantic_model(output_config["output_schema"])
        if output_config.get("input_schema"):
            agent_params["input_schema"] = cls._load_pydantic_model(output_config["input_schema"])
        for param in [
            "use_json_mode",
            "structured_outputs",
            "parse_response",
            "references_format",
            "save_response_to_file",
        ]:
            if output_config.get(param) is not None:
                agent_params[param] = output_config[param]

        # Retry configuration
        retry_config = config.get("retry", {})
        for param in ["retries", "delay_between_retries", "exponential_backoff"]:
            if retry_config.get(param) is not None:
                agent_params[param] = retry_config[param]

        # Storage behavior
        store_config = config.get("store", {})
        for param in ["store_media", "store_tool_messages", "store_history_messages", "send_media_to_model"]:
            if store_config.get(param) is not None:
                agent_params[param] = store_config[param]

        # Hooks
        hooks_config = config.get("hooks", {})
        if hooks_config.get("pre_hooks"):
            agent_params["pre_hooks"] = cls._load_hooks(hooks_config["pre_hooks"])
        if hooks_config.get("post_hooks"):
            agent_params["post_hooks"] = cls._load_hooks(hooks_config["post_hooks"])
        if hooks_config.get("tool_hooks"):
            agent_params["tool_hooks"] = cls._load_hooks(hooks_config["tool_hooks"])

        # Streaming configuration
        streaming_config = config.get("streaming", {})
        for param in ["stream", "stream_events", "store_events"]:
            if streaming_config.get(param) is not None:
                agent_params[param] = streaming_config[param]

        # Legacy settings (backward compatibility)
        settings = config.get("settings", {})
        legacy_params = [
            "temperature",
            "max_tokens",
            "show_tool_calls",
            "markdown",
            "stream",
            "debug_mode",
            "debug_level",
            "telemetry",
        ]
        for param in legacy_params:
            if settings.get(param) is not None and param not in agent_params:
                agent_params[param] = settings[param]

        # Filter out None values
        return {k: v for k, v in agent_params.items() if v is not None}

    @classmethod
    def generate_agent_from_yaml(cls, yaml_path: str, validate: bool = True, **overrides) -> Agent:
        """Generate an Agno Agent from YAML configuration.

        Args:
            yaml_path: Path to agent YAML config
            validate: Validate config before generation
            **overrides: Runtime overrides (session_id, user_id, etc.)

        Returns:
            Configured Agno Agent instance

        Raises:
            GeneratorError: If generation fails
        """
        # Load and validate config
        config = cls._load_yaml(yaml_path)

        if validate:
            is_valid, errors = ConfigValidator.validate_agent(config)
            if not is_valid:
                raise GeneratorError("Invalid agent config:\n" + "\n".join(errors))

        # Substitute environment variables
        config = cls._substitute_env_vars(config)

        # Build agent parameters
        agent_params = cls._build_agent_params(config)

        # Extract agent_id for post-creation assignment
        agent_id = config.get("agent", {}).get("id")

        # Apply runtime overrides
        agent_params.update(overrides)

        # Create agent
        try:
            agent = Agent(**agent_params)
            if agent_id:
                agent.id = agent_id
            return agent
        except Exception as e:
            raise GeneratorError(f"Failed to create agent: {e}") from e

    @classmethod
    def generate_agent_from_dict(
        cls, config: dict, validate: bool = True, strict_env_vars: bool = False, **overrides
    ) -> Agent:
        """Generate an Agno Agent from configuration dictionary.

        Args:
            config: Agent configuration dictionary (Hive-compatible format)
            validate: Validate config before generation
            strict_env_vars: If True, raise error for missing env vars. If False, leave placeholders.
                            Default False for Genie agents (runtime variables).
            **overrides: Runtime overrides (session_id, user_id, etc.)

        Returns:
            Configured Agno Agent instance

        Raises:
            GeneratorError: If generation fails

        Example:
            >>> config = {
            ...     "agent": {"name": "test", "model": "openai:gpt-4o"},
            ...     "instructions": "Test agent instructions"
            ... }
            >>> agent = ConfigGenerator.generate_agent_from_dict(config)
        """
        if validate:
            is_valid, errors = ConfigValidator.validate_agent(config)
            if not is_valid:
                raise GeneratorError("Invalid agent config:\n" + "\n".join(errors))

        # Substitute environment variables (non-strict for Genie runtime agents)
        config = cls._substitute_env_vars(config, strict=strict_env_vars)

        # Build agent parameters using shared method
        agent_params = cls._build_agent_params(config)

        # Extract agent_id for post-creation assignment
        agent_id = config.get("agent", {}).get("id")

        # Apply runtime overrides
        agent_params.update(overrides)

        # Create agent
        try:
            agent = Agent(**agent_params)
            if agent_id:
                agent.id = agent_id
            return agent
        except Exception as e:
            raise GeneratorError(f"Failed to create agent: {e}") from e

    @classmethod
    def _build_team_params(cls, config: dict, members: list) -> dict:
        """Build complete Agno Team parameters from config.

        Extracts all Agno Team parameters from the Hive config structure.
        Supports all parameters from https://docs.agno.com/reference/teams/team

        Args:
            config: Hive team configuration dictionary
            members: List of loaded Agent/Team members

        Returns:
            Dictionary of parameters ready for Team constructor
        """
        team_config = config.get("team", {})
        team_params: dict[str, Any] = {}

        # Core parameters
        team_params["name"] = team_config.get("name")
        team_params["description"] = team_config.get("description")
        team_params["members"] = members
        team_params["instructions"] = config.get("instructions")

        # Role (for nested teams)
        if team_config.get("role"):
            team_params["role"] = team_config["role"]

        # Parse model
        model_string = config.get("model")
        if model_string:
            team_params["model"] = cls._parse_model(model_string)

        # Load tools
        tools = cls._load_tools(config.get("tools", []))
        if tools:
            team_params["tools"] = tools

        # Setup knowledge base
        knowledge = cls._setup_knowledge(config.get("knowledge"))
        if knowledge:
            team_params["knowledge"] = knowledge

        # Setup storage
        db = cls._setup_storage(config.get("storage"))
        if db:
            team_params["db"] = db

        # Translate mode to behavior flags (if provided)
        mode = team_config.get("mode")
        if mode:
            mode_flags = cls._translate_team_mode(mode)
            team_params.update(mode_flags)

        # Behavior configuration (direct control)
        behavior_config = config.get("behavior", {})
        behavior_params = [
            "respond_directly",
            "delegate_to_all_members",
            "determine_input_for_members",
            "share_member_interactions",
            "get_member_information_tool",
            "add_member_tools_to_context",
        ]
        for param in behavior_params:
            if behavior_config.get(param) is not None:
                team_params[param] = behavior_config[param]

        # Session parameters
        session_config = config.get("session", {})
        session_params = [
            "user_id",
            "session_id",
            "session_state",
            "add_session_state_to_context",
            "enable_agentic_state",
            "cache_session",
        ]
        for param in session_params:
            if session_config.get(param) is not None:
                team_params[param] = session_config[param]

        # Reasoning parameters
        reasoning_config = config.get("reasoning", {})
        if reasoning_config.get("enabled"):
            team_params["reasoning"] = True
        if reasoning_config.get("model"):
            team_params["reasoning_model"] = cls._parse_model(reasoning_config["model"])
        if reasoning_config.get("min_steps"):
            team_params["reasoning_min_steps"] = reasoning_config["min_steps"]
        if reasoning_config.get("max_steps"):
            team_params["reasoning_max_steps"] = reasoning_config["max_steps"]

        # Memory parameters
        memory_config = config.get("memory", {})
        memory_params = [
            "enable_agentic_memory",
            "enable_user_memories",
            "add_memories_to_context",
            "enable_session_summaries",
        ]
        for param in memory_params:
            if memory_config.get(param) is not None:
                team_params[param] = memory_config[param]

        # History parameters
        history_config = config.get("history", {})
        history_params = [
            "add_history_to_context",
            "num_history_runs",
            "num_history_messages",
            "add_team_history_to_members",
            "num_team_history_runs",
            "search_session_history",
            "read_chat_history",
        ]
        for param in history_params:
            if history_config.get(param) is not None:
                team_params[param] = history_config[param]

        # Context enrichment
        context_config = config.get("context", {})
        context_params = [
            "add_name_to_context",
            "add_datetime_to_context",
            "add_location_to_context",
            "timezone_identifier",
            "additional_context",
            "expected_output",
        ]
        for param in context_params:
            if context_config.get(param) is not None:
                team_params[param] = context_config[param]

        # Tool control
        tool_control = config.get("tool_control", {})
        for param in ["tool_choice", "tool_call_limit", "search_knowledge", "update_knowledge"]:
            if tool_control.get(param) is not None:
                team_params[param] = tool_control[param]

        # Output configuration
        output_config = config.get("output", {})
        if output_config.get("output_schema"):
            team_params["output_schema"] = cls._load_pydantic_model(output_config["output_schema"])
        if output_config.get("input_schema"):
            team_params["input_schema"] = cls._load_pydantic_model(output_config["input_schema"])
        for param in ["use_json_mode", "parse_response"]:
            if output_config.get(param) is not None:
                team_params[param] = output_config[param]

        # Retry configuration
        retry_config = config.get("retry", {})
        for param in ["retries", "delay_between_retries", "exponential_backoff"]:
            if retry_config.get(param) is not None:
                team_params[param] = retry_config[param]

        # Streaming configuration
        streaming_config = config.get("streaming", {})
        for param in ["stream", "stream_events", "stream_member_events", "store_events", "store_member_responses"]:
            if streaming_config.get(param) is not None:
                team_params[param] = streaming_config[param]

        # Hooks
        hooks_config = config.get("hooks", {})
        if hooks_config.get("pre_hooks"):
            team_params["pre_hooks"] = cls._load_hooks(hooks_config["pre_hooks"])
        if hooks_config.get("post_hooks"):
            team_params["post_hooks"] = cls._load_hooks(hooks_config["post_hooks"])
        if hooks_config.get("tool_hooks"):
            team_params["tool_hooks"] = cls._load_hooks(hooks_config["tool_hooks"])

        # Debug configuration
        debug_config = config.get("debug", {})
        for param in ["debug_mode", "debug_level", "show_members_responses"]:
            if debug_config.get(param) is not None:
                team_params[param] = debug_config[param]

        # Legacy settings (backward compatibility)
        settings = config.get("settings", {})
        legacy_params = ["show_routing", "stream", "debug_mode", "telemetry"]
        for param in legacy_params:
            if settings.get(param) is not None and param not in team_params:
                team_params[param] = settings[param]

        # Metadata and dependencies
        if config.get("metadata"):
            team_params["metadata"] = config["metadata"]
        if config.get("dependencies"):
            team_params["dependencies"] = config["dependencies"]

        # Filter out None values
        return {k: v for k, v in team_params.items() if v is not None}

    @classmethod
    def generate_team_from_yaml(cls, yaml_path: str, validate: bool = True, **overrides) -> Team:
        """Generate an Agno Team from YAML configuration.

        Args:
            yaml_path: Path to team YAML config
            validate: Validate config before generation
            **overrides: Runtime overrides

        Returns:
            Configured Agno Team instance

        Raises:
            GeneratorError: If generation fails
        """
        # Load and validate config
        config = cls._load_yaml(yaml_path)

        if validate:
            is_valid, errors = ConfigValidator.validate_team(config)
            if not is_valid:
                raise GeneratorError("Invalid team config:\n" + "\n".join(errors))

        # Substitute environment variables
        config = cls._substitute_env_vars(config)

        # Load member agents
        member_ids = config.get("members", [])
        members = cls._load_member_agents(member_ids)

        # Build team parameters
        team_params = cls._build_team_params(config, members)

        # Apply runtime overrides
        team_params.update(overrides)

        # Create team
        try:
            team = Team(**team_params)
            return team
        except Exception as e:
            raise GeneratorError(f"Failed to create team: {e}") from e

    @classmethod
    def _build_workflow_params(cls, config: dict, steps: list) -> dict:
        """Build complete Agno Workflow parameters from config.

        Extracts all Agno Workflow parameters from the Hive config structure.
        Supports all parameters from https://docs.agno.com/reference/workflows/workflow

        Args:
            config: Hive workflow configuration dictionary
            steps: List of loaded workflow steps

        Returns:
            Dictionary of parameters ready for Workflow constructor
        """
        workflow_config = config.get("workflow", {})
        workflow_params: dict[str, Any] = {}

        # Core parameters
        workflow_params["name"] = workflow_config.get("name")
        workflow_params["description"] = workflow_config.get("description")
        workflow_params["steps"] = steps

        # Setup storage
        db = cls._setup_storage(config.get("storage"))
        if db:
            workflow_params["db"] = db

        # Session parameters
        session_config = config.get("session", {})
        session_params = ["user_id", "session_id", "session_state", "cache_session"]
        for param in session_params:
            if session_config.get(param) is not None:
                workflow_params[param] = session_config[param]

        # History parameters
        history_config = config.get("history", {})
        if history_config.get("add_workflow_history_to_steps") is not None:
            workflow_params["add_workflow_history_to_steps"] = history_config["add_workflow_history_to_steps"]
        if history_config.get("num_history_runs") is not None:
            workflow_params["num_history_runs"] = history_config["num_history_runs"]

        # Streaming configuration
        streaming_config = config.get("streaming", {})
        for param in ["stream", "stream_events", "stream_executor_events", "store_events", "store_executor_outputs"]:
            if streaming_config.get(param) is not None:
                workflow_params[param] = streaming_config[param]

        # Output configuration
        output_config = config.get("output", {})
        if output_config.get("input_schema"):
            workflow_params["input_schema"] = cls._load_pydantic_model(output_config["input_schema"])

        # Debug configuration
        debug_config = config.get("debug", {})
        if debug_config.get("debug_mode") is not None:
            workflow_params["debug_mode"] = debug_config["debug_mode"]

        # Metadata
        if config.get("metadata"):
            workflow_params["metadata"] = config["metadata"]

        # Legacy settings (backward compatibility)
        settings = config.get("settings", {})
        legacy_params = ["stream", "debug_mode", "telemetry"]
        for param in legacy_params:
            if settings.get(param) is not None and param not in workflow_params:
                workflow_params[param] = settings[param]

        # Filter out None values
        return {k: v for k, v in workflow_params.items() if v is not None}

    @classmethod
    def generate_workflow_from_yaml(cls, yaml_path: str, validate: bool = True, **overrides) -> Workflow:
        """Generate an Agno Workflow from YAML configuration.

        Args:
            yaml_path: Path to workflow YAML config
            validate: Validate config before generation
            **overrides: Runtime overrides

        Returns:
            Configured Agno Workflow instance

        Raises:
            GeneratorError: If generation fails
        """
        # Load and validate config
        config = cls._load_yaml(yaml_path)

        if validate:
            is_valid, errors = ConfigValidator.validate_workflow(config)
            if not is_valid:
                raise GeneratorError("Invalid workflow config:\n" + "\n".join(errors))

        # Substitute environment variables
        config = cls._substitute_env_vars(config)

        # Load workflow steps
        steps_config = config.get("steps", [])
        steps = cls._load_workflow_steps(steps_config)

        # Build workflow parameters
        workflow_params = cls._build_workflow_params(config, steps)

        # Apply runtime overrides
        workflow_params.update(overrides)

        # Create workflow
        try:
            workflow = Workflow(**workflow_params)
            return workflow
        except Exception as e:
            raise GeneratorError(f"Failed to create workflow: {e}") from e

    # ===== HELPER METHODS =====

    @classmethod
    def _load_yaml(cls, yaml_path: str) -> dict[str, Any]:
        """Load and parse YAML file.

        Args:
            yaml_path: Path to YAML file

        Returns:
            Parsed configuration dictionary

        Raises:
            GeneratorError: If loading fails
        """
        if not os.path.exists(yaml_path):
            raise GeneratorError(f"Config file not found: {yaml_path}")

        try:
            with open(yaml_path, encoding="utf-8") as f:
                config: dict[str, Any] = yaml.safe_load(f)
                return config
        except yaml.YAMLError as e:
            raise GeneratorError(f"Invalid YAML syntax: {e}") from e
        except Exception as e:
            raise GeneratorError(f"Failed to load config: {e}") from e

    @classmethod
    def _parse_model(cls, model_string: str | dict | None) -> Any | None:
        """Parse model string or dict into Agno Model object.

        Supports 38+ providers via explicit mapping + dynamic fallback.

        Args:
            model_string: Model identifier (string like 'openai:gpt-4o-mini' or dict like {'provider': 'openai', 'id': 'gpt-4o-mini'})

        Returns:
            Agno Model instance or None

        Raises:
            GeneratorError: If model format is invalid
        """
        if not model_string:
            return None

        # Handle dict format (from YAML with provider/id keys)
        if isinstance(model_string, dict):
            provider = model_string.get("provider")
            model_id = model_string.get("id")

            if not provider or not model_id:
                # Check if it's already a model object (dict subclass)
                if hasattr(model_string, "id"):
                    return model_string
                raise GeneratorError(f"Invalid model dict format: {model_string}\nExpected keys: 'provider' and 'id'")

            # Convert dict to string format for parsing
            model_string = f"{provider}:{model_id}"

        if not isinstance(model_string, str):
            # Already a model object (not dict, not string)
            return model_string

        # Parse provider:model_id format
        if ":" not in model_string:
            raise GeneratorError(
                f"Invalid model format: {model_string}\n"
                f"Expected format: 'provider:model_id' (e.g., 'openai:gpt-4o-mini')"
            )

        provider, model_id = model_string.split(":", 1)
        provider = provider.lower()

        # Map provider names to their main model class
        # Covers most common providers - extensible mapping
        provider_class_map = {
            "openai": ("agno.models.openai", "OpenAIChat"),
            "anthropic": ("agno.models.anthropic", "Claude"),
            "google": ("agno.models.google", "Gemini"),
            "groq": ("agno.models.groq", "Groq"),
            "ollama": ("agno.models.ollama", "Ollama"),
            "xai": ("agno.models.xai", "xAI"),
            "together": ("agno.models.together", "Together"),
            "fireworks": ("agno.models.fireworks", "Fireworks"),
            "mistral": ("agno.models.mistral", "Mistral"),
            "cohere": ("agno.models.cohere", "Cohere"),
            "openrouter": ("agno.models.openrouter", "OpenRouter"),
            "perplexity": ("agno.models.perplexity", "Perplexity"),
            "deepseek": ("agno.models.deepseek", "DeepSeek"),
            "azure": ("agno.models.azure", "AzureOpenAIChat"),
            "aws": ("agno.models.aws", "AwsBedrock"),
            "vertexai": ("agno.models.vertexai", "Gemini"),
        }

        if provider in provider_class_map:
            module_path, class_name = provider_class_map[provider]
            try:
                import importlib

                module = importlib.import_module(module_path)
                model_class = getattr(module, class_name)
                return model_class(id=model_id)
            except Exception as e:
                raise GeneratorError(
                    f"Failed to initialize {provider} model: {e}\nMake sure the provider is installed and configured"
                ) from e
        else:
            # Fallback: try generic import pattern (agno.models.<provider>.<Provider>)
            try:
                import importlib

                module_path = f"agno.models.{provider}"
                module = importlib.import_module(module_path)

                # Try to find main class (usually capitalized provider name)
                provider_capitalized = provider.capitalize()
                if hasattr(module, provider_capitalized):
                    model_class = getattr(module, provider_capitalized)
                    return model_class(id=model_id)

                # List available classes for better error message
                available = [c for c in dir(module) if not c.startswith("_") and c[0].isupper()]
                raise GeneratorError(
                    f"Provider '{provider}' found but main class unclear.\n"
                    f"Available classes: {', '.join(available[:5])}\n"
                    f"Please add mapping to provider_class_map in generator.py"
                )
            except ImportError:
                raise GeneratorError(
                    f"Unknown model provider: {provider}\n"
                    f"Common providers: {', '.join(list(provider_class_map.keys())[:8])}\n"
                    f"See agno.models for full list of 38+ supported providers"
                )

    @classmethod
    def _substitute_env_vars(cls, config: Any, strict: bool = True) -> Any:
        """Recursively substitute ${VAR} with environment variables.

        Args:
            config: Configuration object (dict, list, str, etc.)
            strict: If True, raise error for missing vars. If False, leave placeholder.

        Returns:
            Config with substituted values
        """
        if isinstance(config, dict):
            return {k: cls._substitute_env_vars(v, strict) for k, v in config.items()}
        elif isinstance(config, list):
            return [cls._substitute_env_vars(item, strict) for item in config]
        elif isinstance(config, str):
            # Replace ${VAR} patterns
            def replace_var(match):
                var_name = match.group(1)
                value = os.getenv(var_name)
                if value is None:
                    if strict:
                        raise GeneratorError(
                            f"Environment variable not set: {var_name}\n💡 Add {var_name} to your .env file"
                        )
                    # Non-strict: leave placeholder as-is (for runtime agents)
                    return match.group(0)
                return value

            return re.sub(r"\$\{(\w+)\}", replace_var, config)
        else:
            return config

    @classmethod
    def _load_tools(cls, tools_config: list) -> list:
        """Load tools from configuration.

        Args:
            tools_config: List of tool names or configs

        Returns:
            List of tool instances
        """
        tools = []

        for tool in tools_config:
            if isinstance(tool, str):
                # Builtin tool name
                tool_instance = load_builtin_tool(tool)
                if tool_instance:
                    tools.append(tool_instance)
                else:
                    raise GeneratorError(f"Unknown builtin tool: {tool}")
            elif isinstance(tool, dict):
                # Custom tool config
                tool_name = tool.get("name")
                import_path = tool.get("import_path")

                if not import_path:
                    raise GeneratorError(f"Custom tool '{tool_name}' missing import_path")

                # Dynamic import
                try:
                    module_path, class_name = import_path.rsplit(".", 1)
                    module = __import__(module_path, fromlist=[class_name])
                    tool_class = getattr(module, class_name)

                    # Get tool config
                    tool_config = tool.get("config", {})
                    tool_instance = tool_class(**tool_config)
                    tools.append(tool_instance)
                except Exception as e:
                    raise GeneratorError(f"Failed to load custom tool '{tool_name}': {e}") from e

        return tools

    @classmethod
    def _setup_knowledge(cls, knowledge_config: dict | None) -> Any | None:
        """Setup knowledge base from configuration.

        Args:
            knowledge_config: Knowledge configuration dictionary

        Returns:
            Knowledge base instance or None
        """
        if not knowledge_config:
            return None

        kb_type = knowledge_config.get("type")
        source = knowledge_config.get("source")

        if kb_type == "csv":
            # CSV knowledge base
            from agno.document import CSVReader  # type: ignore[import-not-found]
            from agno.knowledge import DocumentKnowledgeBase  # type: ignore[attr-defined]

            try:
                reader = CSVReader(path=source)
                kb = DocumentKnowledgeBase(
                    reader=reader,
                    num_documents=knowledge_config.get("num_documents", 5),
                )
                return kb
            except Exception as e:
                raise GeneratorError(f"Failed to setup CSV knowledge base: {e}") from e

        elif kb_type == "database":
            # Database knowledge base
            knowledge_config.get("connection")
            knowledge_config.get("table")

            # TODO: Implement database knowledge base
            raise GeneratorError("Database knowledge base not yet implemented")

        else:
            raise GeneratorError(f"Unknown knowledge base type: {kb_type}")

    @classmethod
    def _setup_storage(cls, storage_config: dict | None) -> Any | None:
        """Setup storage from configuration.

        Args:
            storage_config: Storage configuration dictionary

        Returns:
            Storage instance or None

        Note:
            Uses class-level cache to ensure singleton behavior. Multiple agents
            with the same database configuration will share the same DB instance,
            preventing database ID conflicts in AgentOS.
        """
        if not storage_config:
            return None

        # Default to sqlite if type not specified (backward compatibility)
        storage_type = storage_config.get("type", "sqlite")

        if storage_type == "postgres":
            # PostgreSQL storage
            from agno.db import PostgresDb  # type: ignore[import-not-found]

            connection = storage_config.get("connection")
            if not connection:
                # Fallback to HIVE_DATABASE_URL environment variable
                connection = os.getenv("HIVE_DATABASE_URL")

            if not connection:
                raise GeneratorError(
                    "PostgreSQL storage requires 'connection' in config or HIVE_DATABASE_URL environment variable"
                )

            table_name = storage_config.get("table_name", "agent_sessions")

            # Cache key excludes table_name to prevent DB ID conflicts
            cache_key = ("postgres", connection)
            if cache_key in cls._db_cache:
                return cls._db_cache[cache_key]

            # Create new instance and cache it (use first table_name encountered)
            db_instance = PostgresDb(
                db_url=connection,
                session_table=table_name,
            )
            cls._db_cache[cache_key] = db_instance
            return db_instance

        elif storage_type == "sqlite":
            # SQLite storage
            from agno.db.sqlite import SqliteDb

            db_file = storage_config.get("db_file", "./data/agent.db")
            table_name = storage_config.get("table_name", "agent_sessions")

            # Cache key excludes table_name to prevent DB ID conflicts
            # All agents sharing a db_file will share the same DB instance
            cache_key = ("sqlite", db_file)
            if cache_key in cls._db_cache:
                return cls._db_cache[cache_key]

            # Create new instance and cache it (use first table_name encountered)
            db_instance = SqliteDb(
                db_file=db_file,
                session_table=table_name,
            )
            cls._db_cache[cache_key] = db_instance
            return db_instance

        else:
            raise GeneratorError(f"Unknown storage type: {storage_type}")

    @classmethod
    def _load_member_agents(cls, member_ids: list[str]) -> list[Agent]:
        """Load member agents for a team.

        Args:
            member_ids: List of agent IDs or YAML paths

        Returns:
            List of Agent instances

        Raises:
            GeneratorError: If loading fails
        """
        from hive.discovery import discover_agents, get_agent_by_id

        # Discover all available agents
        available_agents = discover_agents()

        members = []
        for member_id in member_ids:
            # Check if it's a path to YAML config
            if member_id.endswith(".yaml") or member_id.endswith(".yml"):
                # Load agent from YAML file
                try:
                    agent = cls.generate_agent_from_yaml(member_id, validate=False)
                    members.append(agent)
                except Exception as e:
                    raise GeneratorError(f"Failed to load member agent from {member_id}: {e}") from e
            else:
                # Lookup by agent_id from discovered agents
                found_agent = get_agent_by_id(member_id, available_agents)
                if found_agent is None:
                    agent_ids = [getattr(a, "id", a.name) for a in available_agents]
                    raise GeneratorError(f"Member agent not found: {member_id}\nAvailable agents: {agent_ids}")
                members.append(found_agent)

        return members

    @classmethod
    def _resolve_agent_reference(cls, agent_ref: str) -> Agent:
        """Resolve agent reference to Agent instance.

        Args:
            agent_ref: Agent ID or path to YAML config

        Returns:
            Agent instance

        Raises:
            GeneratorError: If agent not found
        """
        from hive.discovery import discover_agents, get_agent_by_id

        # Check if it's a YAML path
        if agent_ref.endswith(".yaml") or agent_ref.endswith(".yml"):
            return cls.generate_agent_from_yaml(agent_ref, validate=False)

        # Lookup by ID
        available_agents = discover_agents()
        agent = get_agent_by_id(agent_ref, available_agents)

        if agent is None:
            agent_ids = [getattr(a, "id", a.name) for a in available_agents]
            raise GeneratorError(f"Agent not found: {agent_ref}\nAvailable: {agent_ids}")

        return agent

    @classmethod
    def _translate_team_mode(cls, mode_string: str | None) -> dict[str, bool]:
        """Translate simplified mode string to Agno Team boolean flags.

        Args:
            mode_string: Mode name (default, collaboration, router, etc.)

        Returns:
            Dict with boolean flags for Team constructor

        Note:
            Agno Teams don't have a single 'mode' parameter.
            Behavior is controlled by combining boolean flags:
            - respond_directly: True = pass through, False = synthesize
            - delegate_task_to_all_members: True = all agents, False = team decides
            - determine_input_for_members: True = transform, False = raw
        """
        if not mode_string:
            # Default mode: team leader decides which agent(s), synthesizes response
            return {}

        mode_lower = mode_string.lower()

        # Define mode mappings based on Agno research
        mode_mappings = {
            "default": {
                # Team leader decides which agent(s) to use, synthesizes response
                "respond_directly": False,
                "delegate_task_to_all_members": False,
            },
            "collaboration": {
                # ALL agents work on same task in parallel, leader synthesizes
                "delegate_task_to_all_members": True,
                "respond_directly": False,
            },
            "router": {
                # Route to agent, return response AS-IS (no synthesis)
                "respond_directly": True,
                "determine_input_for_members": False,
            },
            "passthrough": {
                # Same as router - direct passthrough
                "respond_directly": True,
            },
        }

        if mode_lower in mode_mappings:
            return mode_mappings[mode_lower]
        else:
            raise GeneratorError(f"Unknown team mode: {mode_string}\nAvailable modes: {list(mode_mappings.keys())}")

    @classmethod
    def _build_condition_evaluator(cls, condition_config: dict):
        """Build condition evaluation function from config.

        Args:
            condition_config: Condition configuration with operator and operands

        Returns:
            Callable that evaluates to boolean (receives StepInput)

        Raises:
            GeneratorError: If condition config is invalid
        """

        operator = condition_config.get("operator")
        field = condition_config.get("field")
        value = condition_config.get("value")

        if not all([operator, field, value]):
            raise GeneratorError("Condition config must include: operator, field, value")

        # Ensure field is a string
        if not isinstance(field, str):
            raise GeneratorError(f"Condition field must be a string, got: {type(field)}")

        # Build condition lambda based on operator
        # Each lambda receives StepInput (not raw input)
        operators = {
            "equals": lambda si: getattr(si.input, field, None) == value
            if hasattr(si.input, field)
            else si.input.get(field) == value,  # type: ignore[union-attr]
            "not_equals": lambda si: getattr(si.input, field, None) != value
            if hasattr(si.input, field)
            else si.input.get(field) != value,  # type: ignore[union-attr]
            "contains": lambda si: (value if value is not None else "")
            in str(getattr(si.input, field, "") if hasattr(si.input, field) else si.input.get(field, "")),  # type: ignore[union-attr]
            "greater_than": lambda si: (
                getattr(si.input, field, 0) if hasattr(si.input, field) else si.input.get(field, 0)  # type: ignore[union-attr]
            )
            > (value if value is not None else 0),
            "less_than": lambda si: (
                getattr(si.input, field, 0) if hasattr(si.input, field) else si.input.get(field, 0)  # type: ignore[union-attr]
            )
            < (value if value is not None else 0),
        }

        if operator not in operators:
            raise GeneratorError(f"Unknown condition operator: {operator}\nAvailable: {list(operators.keys())}")

        return operators[operator]

    @classmethod
    def _build_loop_end_condition(cls, condition_config: dict):
        """Build loop end condition function from config.

        Args:
            condition_config: Loop end condition configuration

        Returns:
            Callable that evaluates to boolean (receives List[StepOutput])
            Returns True to break loop, False to continue

        Raises:
            GeneratorError: If condition config is invalid
        """

        check_type = condition_config.get("type")
        threshold = condition_config.get("threshold")

        if not check_type:
            raise GeneratorError("Loop end condition must include 'type'")

        # Build end condition based on type
        if check_type == "content_length":
            # Break if content exceeds threshold
            if not threshold:
                raise GeneratorError("content_length requires 'threshold'")

            def end_condition(outputs: list) -> bool:
                if not outputs:
                    return False
                for output in outputs:
                    if hasattr(output, "content") and output.content:
                        if len(output.content) >= threshold:
                            return True  # BREAK
                return False  # CONTINUE

            return end_condition

        elif check_type == "success_count":
            # Break if enough successful outputs
            if not threshold:
                raise GeneratorError("success_count requires 'threshold'")

            def end_condition(outputs: list) -> bool:
                if not outputs:
                    return False
                success_count = sum(1 for o in outputs if hasattr(o, "success") and o.success)
                return bool(success_count >= (threshold if threshold is not None else 0))  # True = BREAK

            return end_condition

        elif check_type == "always_continue":
            # Never break early, always run max_iterations
            return lambda outputs: False

        else:
            raise GeneratorError(
                f"Unknown loop end condition type: {check_type}\n"
                f"Available: content_length, success_count, always_continue"
            )

    @classmethod
    def _load_function_reference(cls, function_name: str):
        """Load function by name or import path.

        Args:
            function_name: Function name or dotted import path

        Returns:
            Callable function

        Raises:
            GeneratorError: If function not found
        """
        # Check if it's a dotted import path
        if "." in function_name:
            try:
                module_path, func_name = function_name.rsplit(".", 1)
                module = __import__(module_path, fromlist=[func_name])
                function = getattr(module, func_name)

                if not callable(function):
                    raise GeneratorError(f"{function_name} is not callable")

                return function
            except Exception as e:
                raise GeneratorError(f"Failed to load function {function_name}: {e}") from e
        else:
            # Simple function name - would need a function registry
            raise GeneratorError(
                f"Simple function name '{function_name}' requires function registry.\n"
                f"Use dotted import path instead: 'module.submodule.function_name'"
            )

    @classmethod
    def _load_workflow_steps(cls, steps_config: list[dict]) -> list:
        """Load workflow steps from configuration.

        Args:
            steps_config: List of step configurations

        Returns:
            List of workflow step instances

        Raises:
            GeneratorError: If loading fails
        """
        from agno.workflow import Condition, Loop, Parallel, Step

        steps = []

        for step_config in steps_config:
            step_name = step_config.get("name")
            step_type = step_config.get("type", "sequential")

            if step_type == "sequential":
                # Sequential step with agent
                agent_id = step_config.get("agent")
                if not agent_id:
                    raise GeneratorError(f"Step '{step_name}' missing agent reference")

                # Load agent from registry or YAML
                agent = cls._resolve_agent_reference(agent_id)
                step = Step(
                    name=step_name,
                    agent=agent,
                    description=step_config.get("description"),
                )
                steps.append(step)

            elif step_type == "parallel":
                # Parallel steps - NOTE: Parallel takes variadic args, not a list
                parallel_steps_config = step_config.get("parallel_steps", [])
                if not parallel_steps_config:
                    raise GeneratorError(f"Parallel step '{step_name}' has no parallel_steps")

                # Load nested steps
                loaded_parallel_steps = cls._load_workflow_steps(parallel_steps_config)

                # Parallel() accepts variadic args: Parallel(*steps, name=..., description=...)
                parallel_step = Parallel(
                    *loaded_parallel_steps,
                    name=step_name,
                    description=step_config.get("description"),
                )
                steps.append(parallel_step)  # type: ignore[arg-type]

            elif step_type == "conditional":
                # Conditional step
                condition_config = step_config.get("condition", {})
                nested_steps_config = step_config.get("steps", [])

                if not condition_config:
                    raise GeneratorError(f"Conditional step '{step_name}' missing condition config")
                if not nested_steps_config:
                    raise GeneratorError(f"Conditional step '{step_name}' has no nested steps")

                # Build condition evaluator (receives StepInput, returns bool)
                evaluator = cls._build_condition_evaluator(condition_config)

                # Load nested steps
                nested_steps = cls._load_workflow_steps(nested_steps_config)

                condition_step = Condition(
                    evaluator=evaluator,
                    steps=nested_steps,
                    name=step_name,
                    description=step_config.get("description"),
                )
                steps.append(condition_step)  # type: ignore[arg-type]

            elif step_type == "loop":
                # Loop step
                nested_steps_config = step_config.get("steps", [])
                max_iterations = step_config.get("max_iterations", 3)
                end_condition_config = step_config.get("end_condition")

                if not nested_steps_config:
                    raise GeneratorError(f"Loop step '{step_name}' has no nested steps")

                # Load nested steps
                nested_steps = cls._load_workflow_steps(nested_steps_config)

                # Build loop params
                loop_params = {
                    "steps": nested_steps,
                    "name": step_name,
                    "description": step_config.get("description"),
                    "max_iterations": max_iterations,
                }

                # Add end condition if specified
                if end_condition_config:
                    end_condition = cls._build_loop_end_condition(end_condition_config)
                    loop_params["end_condition"] = end_condition

                loop_step = Loop(**loop_params)
                steps.append(loop_step)  # type: ignore[arg-type]

            elif step_type == "function":
                # Function step with executor
                function_name = step_config.get("function")
                if not function_name:
                    raise GeneratorError(f"Step '{step_name}' missing function reference")

                # Load function
                function = cls._load_function_reference(function_name)

                # Use 'executor' parameter (not 'function')
                step = Step(
                    name=step_name,
                    executor=function,
                    description=step_config.get("description"),
                )
                steps.append(step)

            else:
                raise GeneratorError(f"Unknown step type: {step_type}")

        return steps


def generate_agent_from_yaml(yaml_path: str, **overrides) -> Agent:
    """Generate an Agno Agent from YAML configuration.

    Args:
        yaml_path: Path to agent YAML config
        **overrides: Runtime overrides (session_id, user_id, etc.)

    Returns:
        Configured Agno Agent instance

    Example:
        >>> agent = generate_agent_from_yaml("config.yaml")
        >>> response = agent.run("Hello!")
    """
    return ConfigGenerator.generate_agent_from_yaml(yaml_path, **overrides)


def generate_team_from_yaml(yaml_path: str, **overrides) -> Team:
    """Generate an Agno Team from YAML configuration.

    Args:
        yaml_path: Path to team YAML config
        **overrides: Runtime overrides

    Returns:
        Configured Agno Team instance
    """
    return ConfigGenerator.generate_team_from_yaml(yaml_path, **overrides)


def generate_workflow_from_yaml(yaml_path: str, **overrides) -> Workflow:
    """Generate an Agno Workflow from YAML configuration.

    Args:
        yaml_path: Path to workflow YAML config
        **overrides: Runtime overrides

    Returns:
        Configured Agno Workflow instance
    """
    return ConfigGenerator.generate_workflow_from_yaml(yaml_path, **overrides)
