"""
Agno-Based Version Factory

Clean implementation using Agno storage for component versioning.
Replaces the old database-based version factory.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow
from dotenv import load_dotenv

from lib.logging import logger

# Load environment variables
load_dotenv()

# Knowledge base creation is now handled by Agno CSVKnowledgeBase + PgVector directly

from lib.utils.yaml_cache import (
    get_yaml_cache_manager,
    load_yaml_cached,
)
from lib.versioning import AgnoVersionService
from lib.versioning.bidirectional_sync import BidirectionalSync
from lib.versioning.dev_mode import DevMode


def load_global_knowledge_config():
    """Load global knowledge configuration with fallback"""
    try:
        global_config_path = Path(__file__).parent.parent / "knowledge/config.yaml"
        global_config = load_yaml_cached(str(global_config_path))
        if global_config:
            return global_config.get("knowledge", {})
        raise FileNotFoundError("Knowledge config not found")
    except Exception as e:
        logger.warning("Could not load global knowledge config: %s", e)
        return {
            "csv_file_path": "knowledge_rag.csv",
            "max_results": 10,
            "enable_hot_reload": True,
        }


class VersionFactory:
    """
    Clean version factory using Agno storage.
    Creates versioned components with modern patterns.
    """

    def __init__(self):
        """Initialize with database URL from environment."""
        self.db_url = os.getenv("HIVE_DATABASE_URL")
        if not self.db_url:
            raise ValueError("HIVE_DATABASE_URL environment variable required")

        self.version_service = AgnoVersionService(self.db_url)
        self.sync_engine = BidirectionalSync(self.db_url)

    async def create_versioned_component(
        self,
        component_id: str,
        component_type: str,
        version: int | None = None,
        session_id: str | None = None,
        debug_mode: bool = False,
        user_id: str | None = None,
        metrics_service: object | None = None,
        **kwargs,
    ) -> Agent | Team | Workflow:
        """
        Create any component type with version support.

        Args:
            component_id: Component identifier
            component_type: "agent", "team", or "workflow"
            version: Version number (None for active)
            session_id: Session ID for tracking
            debug_mode: Enable debug mode
            user_id: User identifier
            metrics_service: Optional metrics collection service
            **kwargs: Additional parameters

        Returns:
            Configured component instance
        """

        # Clean two-path logic: DEV vs PRODUCTION
        if DevMode.is_enabled():
            # Dev mode: YAML only, no DB interaction
            logger.debug(f"Dev mode: Loading {component_id} from YAML only")
            config = await self._load_from_yaml_only(
                component_id, component_type, **kwargs
            )
        else:
            # Production: Always bidirectional sync
            logger.debug(
                f"Production mode: Loading {component_id} with bidirectional sync"
            )
            config = await self._load_with_bidirectional_sync(
                component_id, component_type, version, **kwargs
            )

        # Validate component configuration contains expected type
        if component_type not in config:
            raise ValueError(
                f"Component type {component_type} not found in configuration for {component_id}"
            )

        # Create component using type-specific method
        creation_methods = {
            "agent": self._create_agent,
            "team": self._create_team,
            "workflow": self._create_workflow,
            "coordinator": self._create_coordinator,
        }

        if component_type not in creation_methods:
            raise ValueError(f"Unsupported component type: {component_type}")

        return await creation_methods[component_type](
            component_id=component_id,
            config=config,
            session_id=session_id,
            debug_mode=debug_mode,
            user_id=user_id,
            metrics_service=metrics_service,
            **kwargs,
        )

    async def _create_agent(
        self,
        component_id: str,
        config: dict[str, Any],
        session_id: str | None,
        debug_mode: bool,
        user_id: str | None,
        metrics_service: object | None = None,
        **context_kwargs,
    ) -> Agent:
        """Create versioned agent using dynamic Agno proxy with inheritance support."""

        # Apply inheritance from team configuration if agent is part of a team
        enhanced_config = self._apply_team_inheritance(component_id, config)

        # Use the dynamic proxy system for automatic Agno compatibility
        from lib.utils.agno_proxy import get_agno_proxy

        proxy = get_agno_proxy()

        # Load custom tools
        tools = self._load_agent_tools(component_id, enhanced_config)

        # Prepare config with AGNO native context support
        if tools:
            enhanced_config["tools"] = tools

        # Add AGNO native context parameters - direct pass-through
        enhanced_config["context"] = context_kwargs  # Direct context data
        enhanced_config["add_context"] = (
            True  # Automatically inject context into messages
        )
        enhanced_config["resolve_context"] = True  # Resolve context at runtime

        # Create agent using dynamic proxy with native context
        agent = await proxy.create_agent(
            component_id=component_id,
            config=enhanced_config,
            session_id=session_id,
            debug_mode=debug_mode,
            user_id=user_id,
            db_url=self.db_url,
            metrics_service=metrics_service,
        )

        logger.debug(
            f"🤖 Agent {component_id} created with inheritance and {len(proxy.get_supported_parameters())} available parameters"
        )

        return agent

    def _apply_team_inheritance(
        self, agent_id: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply team inheritance to agent configuration if agent is part of a team."""
        try:
            import os

            from lib.utils.config_inheritance import ConfigInheritanceManager

            # Check if strict validation is enabled (fail-fast mode) - defaults to true
            strict_validation = (
                os.getenv("HIVE_STRICT_VALIDATION", "true").lower() == "true"
            )

            # Find team that contains this agent using cache
            cache_manager = get_yaml_cache_manager()
            team_id = cache_manager.get_agent_team_mapping(agent_id)
            team_config = None
            failed_team_configs = []

            if team_id:
                # Load the specific team config using cache
                team_config_file = f"ai/teams/{team_id}/config.yaml"
                try:
                    team_config = load_yaml_cached(team_config_file)
                    if not team_config:
                        failed_team_configs.append(team_config_file)
                        error_msg = f"Error reading team config {team_config_file}: file not found or invalid"

                        if strict_validation:
                            logger.error(f"🔧 STRICT VALIDATION FAILED: {error_msg}")
                            raise ValueError(
                                f"Agent {agent_id} inheritance validation failed: Cannot read team config {team_config_file}"
                            )
                        logger.warning(f"🔧 {error_msg}")

                except Exception as e:
                    failed_team_configs.append(team_config_file)
                    error_msg = f"Error reading team config {team_config_file}: {e}"

                    if strict_validation:
                        logger.error(f"🔧 STRICT VALIDATION FAILED: {error_msg}")
                        raise ValueError(
                            f"Agent {agent_id} inheritance validation failed: Cannot read team config {team_config_file}"
                        )
                    logger.warning(f"🔧 {error_msg}")

            # Report failed team configs if any
            if failed_team_configs and strict_validation:
                logger.error(
                    f"🔧 Agent {agent_id} inheritance check failed to read {len(failed_team_configs)} team configs: {failed_team_configs}"
                )

            if not team_config:
                logger.debug(
                    f"🔧 No team found for agent {agent_id}, using config as-is"
                )
                return config

            # Apply inheritance
            manager = ConfigInheritanceManager()
            agent_configs = {agent_id: config}
            enhanced_configs = manager.apply_inheritance(team_config, agent_configs)

            # Validate inheritance
            errors = manager.validate_configuration(team_config, enhanced_configs)
            if errors:
                if strict_validation:
                    logger.error(
                        f"🔧 STRICT VALIDATION FAILED: Inheritance validation errors for agent {agent_id}:"
                    )
                    for error in errors:
                        logger.error(f"  ❌ {error}")
                    raise ValueError(
                        f"Agent {agent_id} inheritance validation failed: {len(errors)} configuration errors"
                    )
                logger.warning(
                    f"🔧 Inheritance validation warnings for agent {agent_id}:"
                )
                for error in errors:
                    logger.warning(f"  ⚠️  {error}")

            # Generate inheritance report
            report = manager.generate_inheritance_report(
                team_config, agent_configs, enhanced_configs
            )
            logger.debug(f"🔧 Agent {agent_id} in team {team_id}: {report}")

            return enhanced_configs[agent_id]

        except ValueError:
            # Re-raise validation errors (these are intentional failures)
            raise
        except Exception as e:
            error_msg = f"Error applying inheritance to agent {agent_id}: {e}"
            strict_validation = (
                os.getenv("HIVE_STRICT_VALIDATION", "true").lower() == "true"
            )

            if strict_validation:
                logger.error(f"🔧 STRICT VALIDATION FAILED: {error_msg}")
                raise ValueError(
                    f"Agent {agent_id} inheritance failed due to unexpected error: {e}"
                )
            logger.warning(f"🔧 {error_msg}")
            return config  # Fallback to original config

    def _load_agent_tools(self, component_id: str, config: dict[str, Any]) -> list:
        """Load tools from YAML config via central registry (replaces tools.py approach)."""
        import os

        # Import the new tool registry
        from lib.tools.registry import ToolRegistry

        tools = []

        # Check if strict validation is enabled (fail-fast mode) - defaults to true
        strict_validation = (
            os.getenv("HIVE_STRICT_VALIDATION", "true").lower() == "true"
        )

        try:
            # Get tool configurations from YAML
            tool_configs = config.get("tools", [])

            if tool_configs:
                # Validate tool configurations
                for tool_config in tool_configs:
                    if not self._validate_tool_config(tool_config):
                        error_msg = f"Invalid tool configuration: {tool_config}"
                        if strict_validation:
                            logger.error(f"STRICT VALIDATION FAILED: {error_msg}")
                            raise ValueError(
                                f"Agent {component_id} tool validation failed: {error_msg}"
                            )
                        logger.warning(f"{error_msg}")

                # Load tools via central registry
                tools = ToolRegistry.load_tools(tool_configs)

                # Extract tool names for better logging (sorted for deterministic output)
                tool_names = []
                for tool_config in tool_configs:
                    if isinstance(tool_config, str):
                        tool_names.append(tool_config)
                    elif isinstance(tool_config, dict) and "name" in tool_config:
                        tool_names.append(tool_config["name"])

                if tool_names:
                    # Sort tool names alphabetically for consistent display
                    sorted_tool_names = sorted(tool_names)
                    logger.info(
                        f"Loaded tools for agent {component_id}: {', '.join(sorted_tool_names)}"
                    )
                else:
                    logger.info(
                        f"Loaded {len(tools)} tools for agent {component_id} via central registry"
                    )

            else:
                # No tools configured - that's okay for agents without specific tool requirements
                logger.debug(f"No tools configured for agent {component_id}")

        except ValueError:
            # Re-raise validation errors (these are intentional failures)
            raise
        except Exception as e:
            error_msg = f"Error loading tools for agent {component_id}: {e}"

            if strict_validation:
                logger.error(f"STRICT VALIDATION FAILED: {error_msg}")
                raise ValueError(
                    f"Agent {component_id} tool loading failed due to unexpected error: {e}"
                )
            logger.error(f"{error_msg}")

        return tools

    def _validate_tool_config(self, tool_config: dict[str, Any]) -> bool:
        """
        Validate tool configuration structure.

        Args:
            tool_config: Tool configuration dictionary from YAML

        Returns:
            True if valid, False otherwise
        """
        # Tool config can be just a string (tool name) or dict with name + description
        if isinstance(tool_config, str):
            return True  # Simple string format is valid

        if isinstance(tool_config, dict):
            required_fields = ["name"]
            return all(field in tool_config for field in required_fields)

        return False

    async def _create_team(
        self,
        component_id: str,
        config: dict[str, Any],
        session_id: str | None,
        debug_mode: bool,
        user_id: str | None,
        metrics_service: object | None = None,
        **kwargs,
    ) -> Team:
        """Create team using dynamic Agno Team proxy with inheritance validation."""

        logger.debug(
            f"🔧 Creating team {component_id} (session_id={session_id}, debug_mode={debug_mode})"
        )

        try:
            # Validate team inheritance configuration
            logger.debug(f"🔧 Validating inheritance for team {component_id}")
            enhanced_config = self._validate_team_inheritance(component_id, config)
            logger.debug(f"🔧 Team {component_id} inheritance validation completed")

            # Use the dynamic team proxy system for automatic Agno compatibility
            logger.debug(f"🔧 Loading AgnoTeamProxy for team {component_id}")
            from lib.utils.agno_proxy import get_agno_team_proxy

            proxy = get_agno_team_proxy()
            logger.debug(
                f"🔧 AgnoTeamProxy loaded successfully for team {component_id}"
            )

            # Create team using dynamic proxy
            logger.debug(f"🔧 Creating team instance via proxy for {component_id}")
            team = await proxy.create_team(
                component_id=component_id,
                config=enhanced_config,
                session_id=session_id,
                debug_mode=debug_mode,
                user_id=user_id,
                db_url=self.db_url,
                metrics_service=metrics_service,
                **kwargs,
            )

            logger.debug(
                f"🤖 Team {component_id} created with inheritance validation and {len(proxy.get_supported_parameters())} available parameters"
            )

            return team
        except Exception as e:
            logger.error(
                f"🔧 Team creation failed for {component_id}: {type(e).__name__}: {e!s}",
                exc_info=True,
            )
            raise

    def _validate_team_inheritance(
        self, team_id: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate team configuration for proper inheritance setup."""
        try:
            import os

            from lib.utils.config_inheritance import ConfigInheritanceManager

            # Check if strict validation is enabled (fail-fast mode) - defaults to true
            strict_validation = (
                os.getenv("HIVE_STRICT_VALIDATION", "true").lower() == "true"
            )

            # Load all member agent configurations
            agent_configs = {}
            members = config.get("members") or []
            missing_members = []
            logger.debug(f"🔧 Team {team_id} has members: {members}")

            for member_id in members:
                agent_config_path = f"ai/agents/{member_id}/config.yaml"
                logger.debug(f"🔧 Loading member config: {agent_config_path}")
                try:
                    agent_config = load_yaml_cached(agent_config_path)
                    if agent_config:
                        agent_configs[member_id] = agent_config
                        logger.debug(
                            f"🔧 Successfully loaded config for member {member_id}"
                        )
                    else:
                        raise FileNotFoundError(
                            f"Config file not found or invalid: {agent_config_path}"
                        )
                except Exception as e:
                    missing_members.append(member_id)
                    error_msg = f"Could not load member config for {member_id}: {e}"

                    if strict_validation:
                        logger.error(f"🔧 STRICT VALIDATION FAILED: {error_msg}")
                        logger.error(f"🔧 Failed path: {agent_config_path}")
                        raise ValueError(
                            f"Team {team_id} dependency validation failed: Missing required member '{member_id}' at {agent_config_path}"
                        )
                    logger.warning(f"🔧 {error_msg}")
                    logger.debug(f"🔧 Failed path: {agent_config_path}")
                    continue

            # Validate that we have at least some members loaded
            if not agent_configs:
                error_msg = f"No member agents found for team {team_id}"
                if strict_validation:
                    logger.error(f"🔧 STRICT VALIDATION FAILED: {error_msg}")
                    raise ValueError(
                        f"Team {team_id} has no valid members. Missing members: {missing_members}"
                    )
                logger.warning(f"🔧 {error_msg}")
                return config

            # Report missing members summary
            if missing_members:
                if strict_validation:
                    logger.error(
                        f"🔧 Team {team_id} missing {len(missing_members)} required members: {missing_members}"
                    )
                else:
                    logger.warning(
                        f"🔧 Team {team_id} missing {len(missing_members)} members (non-critical): {missing_members}"
                    )

            # Validate inheritance setup
            manager = ConfigInheritanceManager()
            errors = manager.validate_configuration(config, agent_configs)

            if errors:
                if strict_validation:
                    logger.error(
                        f"🔧 STRICT VALIDATION FAILED: Team inheritance validation errors for {team_id}:"
                    )
                    for error in errors:
                        logger.error(f"  ❌ {error}")
                    raise ValueError(
                        f"Team {team_id} inheritance validation failed: {len(errors)} configuration errors"
                    )
                logger.warning(f"🔧 Team inheritance validation errors for {team_id}:")
                for error in errors:
                    logger.warning(f"  ⚠️  {error}")

            # Generate inheritance preview report
            enhanced_agent_configs = manager.apply_inheritance(config, agent_configs)
            report = manager.generate_inheritance_report(
                config, agent_configs, enhanced_agent_configs
            )
            logger.debug(f"🔧 Team {team_id}: {report}")

            return config

        except ValueError:
            # Re-raise validation errors (these are intentional failures)
            raise
        except Exception as e:
            error_msg = f"Error validating team inheritance for {team_id}: {e}"
            strict_validation = (
                os.getenv("HIVE_STRICT_VALIDATION", "true").lower() == "true"
            )

            if strict_validation:
                logger.error(f"🔧 STRICT VALIDATION FAILED: {error_msg}")
                raise ValueError(
                    f"Team {team_id} validation failed due to unexpected error: {e}"
                )
            logger.warning(f"🔧 {error_msg}")
            return config  # Fallback to original config

    async def _create_workflow(
        self,
        component_id: str,
        config: dict[str, Any],
        session_id: str | None,
        debug_mode: bool,
        user_id: str | None,
        metrics_service: object | None = None,
        **kwargs,
    ) -> Workflow:
        """Create workflow using dynamic Agno Workflow proxy for future compatibility."""

        # Use the dynamic workflow proxy system for automatic Agno compatibility
        from lib.utils.agno_proxy import get_agno_workflow_proxy

        proxy = get_agno_workflow_proxy()

        # Create workflow using dynamic proxy
        workflow = await proxy.create_workflow(
            component_id=component_id,
            config=config,
            session_id=session_id,
            debug_mode=debug_mode,
            user_id=user_id,
            db_url=self.db_url,
            metrics_service=metrics_service,
            **kwargs,
        )

        logger.debug(
            f"🤖 Workflow {component_id} created with {len(proxy.get_supported_parameters())} available Agno Workflow parameters"
        )

        return workflow

    async def _create_coordinator(
        self,
        component_id: str,
        config: dict[str, Any],
        session_id: str | None,
        debug_mode: bool,
        user_id: str | None,
        metrics_service: object | None = None,
        **kwargs,
    ) -> Agent:
        """Create coordinator using dynamic Agno Agent proxy configured as coordinator."""

        # Use the dynamic coordinator proxy system for automatic Agno compatibility
        from lib.utils.agno_proxy import get_agno_coordinator_proxy

        proxy = get_agno_coordinator_proxy()

        # Create coordinator using dynamic proxy
        coordinator = await proxy.create_coordinator(
            component_id=component_id,
            config=config,
            session_id=session_id,
            debug_mode=debug_mode,
            user_id=user_id,
            db_url=self.db_url,
            metrics_service=metrics_service,
            **kwargs,
        )

        logger.debug(
            f"🎯 Coordinator {component_id} created with {len(proxy.get_supported_parameters())} available Agno Agent parameters"
        )

        return coordinator

    async def _load_from_yaml_only(
        self, component_id: str, component_type: str, **kwargs
    ) -> dict:
        """
        Load component configuration from YAML only (dev mode).

        Args:
            component_id: The component identifier
            component_type: The component type
            **kwargs: Additional parameters

        Returns:
            dict: Component configuration from YAML
        """
        from pathlib import Path

        # Determine config file path based on component type
        config_paths = {
            "agent": f"ai/agents/{component_id}/config.yaml",
            "team": f"ai/teams/{component_id}/config.yaml",
            "workflow": f"ai/workflows/{component_id}/config.yaml",
            "coordinator": f"ai/coordinators/{component_id}/config.yaml",
        }

        config_file = config_paths.get(component_type)
        if not config_file:
            raise ValueError(f"Unsupported component type: {component_type}")

        config_path = Path(config_file)
        if not config_path.exists():
            raise ValueError(f"Config file not found: {config_file}")

        # Load YAML configuration
        try:
            with open(config_path, encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to load YAML config from {config_file}: {e}")

        if not yaml_config or component_type not in yaml_config:
            raise ValueError(
                f"Invalid YAML config in {config_file}: missing '{component_type}' section"
            )

        logger.debug(
            f"Dev mode: Loaded {component_type} {component_id} configuration from YAML"
        )
        return yaml_config

    async def _load_with_bidirectional_sync(
        self,
        component_id: str,
        component_type: str,
        version: int | None = None,
        **kwargs,
    ) -> dict:
        """
        Load component configuration with bidirectional sync (production mode).

        Args:
            component_id: The component identifier
            component_type: The component type
            version: Specific version to load (None for active)
            **kwargs: Additional parameters

        Returns:
            dict: Synchronized component configuration
        """
        if version is not None:
            # Load specific version from database
            version_record = await self.version_service.get_version(
                component_id, version
            )
            if not version_record:
                raise ValueError(f"Version {version} not found for {component_id}")
            return version_record.config
        # Perform bidirectional sync and return result
        return await self.sync_engine.sync_component(component_id, component_type)

    async def _create_component_from_yaml(
        self,
        component_id: str,
        component_type: str,
        session_id: str | None,
        debug_mode: bool,
        user_id: str | None,
        metrics_service: object | None = None,
        **kwargs,
    ) -> Agent | Team | Workflow:
        """
        Fallback method to create components directly from YAML during first startup.
        Used when database doesn't have synced versions yet.
        """
        from pathlib import Path

        # Determine config file path based on component type
        config_paths = {
            "agent": f"ai/agents/{component_id}/config.yaml",
            "team": f"ai/teams/{component_id}/config.yaml",
            "workflow": f"ai/workflows/{component_id}/config.yaml",
            "coordinator": f"ai/coordinators/{component_id}/config.yaml",
        }

        config_file = config_paths.get(component_type)
        if not config_file:
            raise ValueError(f"Unsupported component type: {component_type}")

        config_path = Path(config_file)
        if not config_path.exists():
            raise ValueError(f"Config file not found: {config_file}")

        # Load YAML configuration
        try:
            with open(config_path, encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to load YAML config from {config_file}: {e}")

        if not yaml_config or component_type not in yaml_config:
            raise ValueError(
                f"Invalid YAML config in {config_file}: missing '{component_type}' section"
            )

        logger.debug(
            f"🔧 Loading {component_type} {component_id} from YAML (first startup fallback)"
        )

        # Use the same creation methods but with YAML config
        creation_methods = {
            "agent": self._create_agent,
            "team": self._create_team,
            "workflow": self._create_workflow,
            "coordinator": self._create_coordinator,
        }

        return await creation_methods[component_type](
            component_id=component_id,
            config=yaml_config,  # Pass the full YAML config
            session_id=session_id,
            debug_mode=debug_mode,
            user_id=user_id,
            metrics_service=metrics_service,
            **kwargs,
        )


# Global factory instance - lazy initialization
_version_factory = None


def get_version_factory() -> VersionFactory:
    """Get or create the global version factory instance"""
    global _version_factory
    if _version_factory is None:
        _version_factory = VersionFactory()
    return _version_factory


# Clean factory functions
async def create_agent(
    agent_id: str,
    version: int | None = None,
    metrics_service: object | None = None,
    **kwargs,
) -> Agent:
    """Create agent using factory pattern."""
    return await get_version_factory().create_versioned_component(
        agent_id, "agent", version, metrics_service=metrics_service, **kwargs
    )


async def create_team(
    team_id: str,
    version: int | None = None,
    metrics_service: object | None = None,
    **kwargs,
) -> Team:
    """Create team using factory pattern (unified with agents)."""
    return await get_version_factory().create_versioned_component(
        team_id, "team", version, metrics_service=metrics_service, **kwargs
    )


async def create_versioned_workflow(
    workflow_id: str, version: int | None = None, **kwargs
) -> Workflow:
    """Create versioned workflow using Agno storage."""
    return await get_version_factory().create_versioned_component(
        workflow_id, "workflow", version, **kwargs
    )


async def create_coordinator(
    coordinator_id: str,
    version: int | None = None,
    metrics_service: object | None = None,
    **kwargs,
) -> Agent:
    """Create coordinator using factory pattern."""
    return await get_version_factory().create_versioned_component(
        coordinator_id,
        "coordinator",
        version,
        metrics_service=metrics_service,
        **kwargs,
    )
