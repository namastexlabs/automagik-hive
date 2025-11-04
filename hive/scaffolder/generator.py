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

        # Extract agent config
        agent_config = config.get("agent", {})
        name = agent_config.get("name")
        description = agent_config.get("description")
        model_string = agent_config.get("model")

        # Instructions
        instructions = config.get("instructions")

        # Load tools
        tools = cls._load_tools(config.get("tools", []))

        # Setup knowledge base
        knowledge = cls._setup_knowledge(config.get("knowledge"))

        # Setup storage
        storage = cls._setup_storage(config.get("storage"))

        # Extract settings
        settings = config.get("settings", {})
        temperature = settings.get("temperature")
        max_tokens = settings.get("max_tokens")
        show_tool_calls = settings.get("show_tool_calls")
        markdown = settings.get("markdown")
        stream = settings.get("stream")
        debug_mode = settings.get("debug_mode")

        # MCP servers
        mcp_servers = config.get("mcp_servers")

        # Build agent parameters
        # Parse model string into Model object
        model = cls._parse_model(model_string)

        agent_params = {
            "name": name,
            "description": description,
            "model": model,
            "instructions": instructions,
        }

        # Add optional parameters
        if tools:
            agent_params["tools"] = tools
        if knowledge:
            agent_params["knowledge"] = knowledge
        if storage:
            agent_params["storage"] = storage
        if mcp_servers:
            agent_params["mcp_servers"] = mcp_servers
        if temperature is not None:
            agent_params["temperature"] = temperature
        if max_tokens is not None:
            agent_params["max_tokens"] = max_tokens
        if show_tool_calls is not None:
            agent_params["show_tool_calls"] = show_tool_calls
        if markdown is not None:
            agent_params["markdown"] = markdown
        if stream is not None:
            agent_params["stream"] = stream
        if debug_mode is not None:
            agent_params["debug_mode"] = debug_mode

        # Apply runtime overrides
        agent_params.update(overrides)

        # Create agent
        try:
            agent = Agent(**agent_params)
            return agent
        except Exception as e:
            raise GeneratorError(f"Failed to create agent: {e}") from e

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

        # Extract team config
        team_config = config.get("team", {})
        name = team_config.get("name")
        description = team_config.get("description")
        mode = team_config.get("mode")

        # Load member agents
        member_ids = config.get("members", [])
        members = cls._load_member_agents(member_ids)

        # Instructions
        instructions = config.get("instructions")

        # Model (optional for teams)
        model_string = config.get("model")

        # Setup storage
        storage = cls._setup_storage(config.get("storage"))

        # Extract settings
        settings = config.get("settings", {})
        show_routing = settings.get("show_routing")
        stream = settings.get("stream")
        # Parse model string into Model object
        model = cls._parse_model(model_string)

        debug_mode = settings.get("debug_mode")

        # Build team parameters (NO 'mode' parameter in Agno)
        team_params = {
            "name": name,
            "description": description,
            "members": members,
            "instructions": instructions,
        }

        # Translate mode string to boolean flags (if provided)
        if mode:
            mode_flags = cls._translate_team_mode(mode)
            team_params.update(mode_flags)

        # Add optional parameters
        if model:
            team_params["model"] = model
        if storage:
            team_params["storage"] = storage
        if show_routing is not None:
            team_params["show_routing"] = show_routing
        if stream is not None:
            team_params["stream"] = stream
        if debug_mode is not None:
            team_params["debug_mode"] = debug_mode

        # Apply runtime overrides
        team_params.update(overrides)

        # Create team
        try:
            team = Team(**team_params)
            return team
        except Exception as e:
            raise GeneratorError(f"Failed to create team: {e}") from e

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

        # Extract workflow config
        workflow_config = config.get("workflow", {})
        name = workflow_config.get("name")
        description = workflow_config.get("description")

        # Load workflow steps
        steps_config = config.get("steps", [])
        steps = cls._load_workflow_steps(steps_config)

        # Setup storage
        storage = cls._setup_storage(config.get("storage"))

        model_string = config.get("model")
        settings = config.get("settings", {})
        shared_state = settings.get("shared_state")
        # Parse model string into Model object
        cls._parse_model(model_string)

        retry_on_error = settings.get("retry_on_error")
        max_retries = settings.get("max_retries")
        stream = settings.get("stream")
        show_progress = settings.get("show_progress")
        debug_mode = settings.get("debug_mode")

        # Build workflow parameters
        workflow_params = {
            "name": name,
            "description": description,
            "steps": steps,
        }

        # Add optional parameters
        if storage:
            workflow_params["storage"] = storage
        if shared_state is not None:
            workflow_params["shared_state"] = shared_state
        if retry_on_error is not None:
            workflow_params["retry_on_error"] = retry_on_error
        if max_retries is not None:
            workflow_params["max_retries"] = max_retries
        if stream is not None:
            workflow_params["stream"] = stream
        if show_progress is not None:
            workflow_params["show_progress"] = show_progress
        if debug_mode is not None:
            workflow_params["debug_mode"] = debug_mode

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
    def _parse_model(cls, model_string: str | None) -> Any | None:
        """Parse model string into Agno Model object.

        Supports 38+ providers via explicit mapping + dynamic fallback.

        Args:
            model_string: Model identifier (e.g., 'openai:gpt-4o-mini', 'anthropic:claude-3-sonnet')

        Returns:
            Agno Model instance or None

        Raises:
            GeneratorError: If model format is invalid
        """
        if not model_string:
            return None

        if not isinstance(model_string, str):
            # Already a model object
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
    def _substitute_env_vars(cls, config: Any) -> Any:
        """Recursively substitute ${VAR} with environment variables.

        Args:
            config: Configuration object (dict, list, str, etc.)

        Returns:
            Config with substituted values
        """
        if isinstance(config, dict):
            return {k: cls._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [cls._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Replace ${VAR} patterns
            def replace_var(match):
                var_name = match.group(1)
                value = os.getenv(var_name)
                if value is None:
                    raise GeneratorError(
                        f"Environment variable not set: {var_name}\n💡 Add {var_name} to your .env file"
                    )
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
        """
        if not storage_config:
            return None

        storage_type = storage_config.get("type")

        if storage_type == "postgres":
            # PostgreSQL storage
            from agno.storage import PostgresStorage  # type: ignore[import-not-found]

            return PostgresStorage(
                connection_url=storage_config.get("connection"),
                table_name=storage_config.get("table_name", "agent_sessions"),
                auto_upgrade_schema=True,
            )

        elif storage_type == "sqlite":
            # SQLite storage
            from agno.storage import SqliteStorage  # type: ignore[import-not-found]

            return SqliteStorage(
                db_file=storage_config.get("db_file", "./data/agent.db"),
                table_name=storage_config.get("table_name", "agent_sessions"),
                auto_upgrade_schema=True,
            )

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
