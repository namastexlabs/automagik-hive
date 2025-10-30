"""YAML to Agno Agent/Team/Workflow generator.

This module converts YAML configuration files into actual Agno components.
Handles model resolution, tool loading, knowledge base setup, and MCP integration.

12-year-old friendly: Give it a YAML file, get back a working agent!
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    def generate_agent_from_yaml(
        cls, yaml_path: str, validate: bool = True, **overrides
    ) -> Agent:
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
                raise GeneratorError(
                    f"Invalid agent config:\n" + "\n".join(errors)
                )

        # Substitute environment variables
        config = cls._substitute_env_vars(config)

        # Extract agent config
        agent_config = config.get("agent", {})
        name = agent_config.get("name")
        description = agent_config.get("description")
        model = agent_config.get("model")

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
    def generate_team_from_yaml(
        cls, yaml_path: str, validate: bool = True, **overrides
    ) -> Team:
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
                raise GeneratorError(
                    f"Invalid team config:\n" + "\n".join(errors)
                )

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
        model = config.get("model")

        # Setup storage
        storage = cls._setup_storage(config.get("storage"))

        # Extract settings
        settings = config.get("settings", {})
        show_routing = settings.get("show_routing")
        stream = settings.get("stream")
        debug_mode = settings.get("debug_mode")

        # Build team parameters
        team_params = {
            "name": name,
            "description": description,
            "mode": mode,
            "members": members,
            "instructions": instructions,
        }

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
    def generate_workflow_from_yaml(
        cls, yaml_path: str, validate: bool = True, **overrides
    ) -> Workflow:
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
                raise GeneratorError(
                    f"Invalid workflow config:\n" + "\n".join(errors)
                )

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

        # Extract settings
        settings = config.get("settings", {})
        shared_state = settings.get("shared_state")
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
    def _load_yaml(cls, yaml_path: str) -> Dict[str, Any]:
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
            with open(yaml_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise GeneratorError(f"Invalid YAML syntax: {e}") from e
        except Exception as e:
            raise GeneratorError(f"Failed to load config: {e}") from e

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
                        f"Environment variable not set: {var_name}\n"
                        f"💡 Add {var_name} to your .env file"
                    )
                return value

            return re.sub(r"\$\{(\w+)\}", replace_var, config)
        else:
            return config

    @classmethod
    def _load_tools(cls, tools_config: List) -> List:
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
                    raise GeneratorError(
                        f"Custom tool '{tool_name}' missing import_path"
                    )

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
                    raise GeneratorError(
                        f"Failed to load custom tool '{tool_name}': {e}"
                    ) from e

        return tools

    @classmethod
    def _setup_knowledge(cls, knowledge_config: Optional[Dict]) -> Optional[Any]:
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
            from agno.knowledge import DocumentKnowledgeBase
            from agno.document import CSVReader

            try:
                reader = CSVReader(path=source)
                kb = DocumentKnowledgeBase(
                    reader=reader,
                    num_documents=knowledge_config.get("num_documents", 5),
                )
                return kb
            except Exception as e:
                raise GeneratorError(
                    f"Failed to setup CSV knowledge base: {e}"
                ) from e

        elif kb_type == "database":
            # Database knowledge base
            connection = knowledge_config.get("connection")
            table = knowledge_config.get("table")

            # TODO: Implement database knowledge base
            raise GeneratorError("Database knowledge base not yet implemented")

        else:
            raise GeneratorError(f"Unknown knowledge base type: {kb_type}")

    @classmethod
    def _setup_storage(cls, storage_config: Optional[Dict]) -> Optional[Any]:
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
            from agno.storage import PostgresStorage

            return PostgresStorage(
                connection_url=storage_config.get("connection"),
                table_name=storage_config.get("table_name", "agent_sessions"),
                auto_upgrade_schema=True,
            )

        elif storage_type == "sqlite":
            # SQLite storage
            from agno.storage import SqliteStorage

            return SqliteStorage(
                db_file=storage_config.get("db_file", "./data/agent.db"),
                table_name=storage_config.get("table_name", "agent_sessions"),
                auto_upgrade_schema=True,
            )

        else:
            raise GeneratorError(f"Unknown storage type: {storage_type}")

    @classmethod
    def _load_member_agents(cls, member_ids: List[str]) -> List[Agent]:
        """Load member agents for a team.

        Args:
            member_ids: List of agent IDs

        Returns:
            List of Agent instances

        Raises:
            GeneratorError: If loading fails
        """
        # TODO: Implement agent registry lookup
        # For now, placeholder that assumes agents are defined elsewhere
        raise GeneratorError(
            "Member agent loading requires agent registry implementation"
        )

    @classmethod
    def _load_workflow_steps(cls, steps_config: List[Dict]) -> List:
        """Load workflow steps from configuration.

        Args:
            steps_config: List of step configurations

        Returns:
            List of workflow step instances

        Raises:
            GeneratorError: If loading fails
        """
        from agno.workflow import Step, Parallel, Condition, Loop

        steps = []

        for step_config in steps_config:
            step_name = step_config.get("name")
            step_type = step_config.get("type", "sequential")

            if step_type == "sequential":
                # Sequential step with agent
                agent_id = step_config.get("agent")
                if not agent_id:
                    raise GeneratorError(
                        f"Step '{step_name}' missing agent reference"
                    )

                # TODO: Load agent from registry
                step = Step(name=step_name, description=step_config.get("description"))
                steps.append(step)

            elif step_type == "parallel":
                # Parallel steps
                parallel_steps = step_config.get("parallel_steps", [])
                parallel_step = Parallel(
                    name=step_name,
                    description=step_config.get("description"),
                    steps=cls._load_workflow_steps(parallel_steps),
                )
                steps.append(parallel_step)

            elif step_type == "conditional":
                # Conditional step
                condition_config = step_config.get("condition", {})
                nested_steps = step_config.get("steps", [])

                # TODO: Implement condition evaluation
                condition_step = Condition(
                    name=step_name,
                    description=step_config.get("description"),
                    steps=cls._load_workflow_steps(nested_steps),
                )
                steps.append(condition_step)

            elif step_type == "loop":
                # Loop step
                agent_id = step_config.get("agent")
                max_iterations = step_config.get("max_iterations", 3)

                # TODO: Load agent and implement loop
                loop_step = Loop(
                    name=step_name,
                    description=step_config.get("description"),
                    max_iterations=max_iterations,
                )
                steps.append(loop_step)

            elif step_type == "function":
                # Function step
                function_name = step_config.get("function")
                if not function_name:
                    raise GeneratorError(
                        f"Step '{step_name}' missing function reference"
                    )

                # TODO: Load function
                step = Step(
                    name=step_name,
                    description=step_config.get("description"),
                    function=None,  # Placeholder
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
