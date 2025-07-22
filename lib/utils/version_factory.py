"""
Agno-Based Version Factory

Clean implementation using Agno storage for component versioning.
Replaces the old database-based version factory.
"""

from typing import Optional, Dict, Any, Union
from pathlib import Path
import yaml
import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.utils.log import logger

# Load environment variables
load_dotenv()

from lib.versioning import AgnoVersionService
from lib.utils.yaml_cache import get_yaml_cache_manager, load_yaml_cached, discover_components_cached
# Knowledge base creation is now handled by Agno CSVKnowledgeBase + PgVector directly

from datetime import datetime


def load_global_knowledge_config():
    """Load global knowledge configuration with fallback"""
    try:
        global_config_path = Path(__file__).parent.parent / "knowledge/config.yaml"
        global_config = load_yaml_cached(str(global_config_path))
        if global_config:
            return global_config.get("knowledge", {})
        else:
            raise FileNotFoundError("Knowledge config not found")
    except Exception as e:
        logger.warning("🔧 Could not load global knowledge config: %s", e)
        return {
            "csv_file_path": "knowledge_rag.csv",
            "max_results": 10,
            "enable_hot_reload": True
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
        self.yaml_fallback_count = 0  # Track first-startup fallback usage
    
    
    async def create_versioned_component(
        self,
        component_id: str,
        component_type: str,
        version: Optional[int] = None,
        session_id: Optional[str] = None,
        debug_mode: bool = False,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Union[Agent, Team, Workflow]:
        """
        Create any component type with version support.
        
        Args:
            component_id: Component identifier
            component_type: "agent", "team", or "workflow"
            version: Version number (None for active)
            session_id: Session ID for tracking
            debug_mode: Enable debug mode
            user_id: User identifier
            **kwargs: Additional parameters
            
        Returns:
            Configured component instance
        """
        
        # Simple database lookup - no fallbacks (KISS principle)
        if version is not None:
            version_record = await self.version_service.get_version(component_id, version)
            if not version_record:
                raise ValueError(f"Version {version} not found for {component_id}")
        else:
            version_record = await self.version_service.get_active_version(component_id)
            if not version_record:
                # First startup case: No active version in database yet
                # Fall back to loading from YAML config directly
                self.yaml_fallback_count += 1
                logger.debug(f"🔧 No active version found for {component_id}, loading from YAML config (first startup)")
                result = await self._create_component_from_yaml(
                    component_id=component_id,
                    component_type=component_type,
                    session_id=session_id,
                    debug_mode=debug_mode,
                    user_id=user_id,
                    **kwargs
                )
                
                # Log summary for first few fallbacks only
                if self.yaml_fallback_count == 1:
                    logger.info("🔧 First startup detected: Loading components from YAML configs before database sync")
                
                return result
        
        config = version_record.config
        
        # Validate component type matches
        if version_record.component_type != component_type:
            raise ValueError(f"Component {component_id} is type {version_record.component_type}, not {component_type}")
        
        # Create component using type-specific method
        creation_methods = {
            "agent": self._create_agent,
            "team": self._create_team,
            "workflow": self._create_workflow
        }
        
        if component_type not in creation_methods:
            raise ValueError(f"Unsupported component type: {component_type}")
            
        return await creation_methods[component_type](
            component_id=component_id,
            config=config,
            session_id=session_id,
            debug_mode=debug_mode,
            user_id=user_id,
            **kwargs
        )
    
    async def _create_agent(
        self,
        component_id: str,
        config: Dict[str, Any],
        session_id: Optional[str],
        debug_mode: bool,
        user_id: Optional[str],
        **context_kwargs
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
        enhanced_config["add_context"] = True  # Automatically inject context into messages
        enhanced_config["resolve_context"] = True  # Resolve context at runtime
        
        # Create agent using dynamic proxy with native context
        agent = await proxy.create_agent(
            component_id=component_id,
            config=enhanced_config,
            session_id=session_id,
            debug_mode=debug_mode,
            user_id=user_id,
            db_url=self.db_url
        )
        
        logger.debug(f"🤖 Agent {component_id} created with inheritance and {len(proxy.get_supported_parameters())} available parameters")
        
        return agent
    
    def _apply_team_inheritance(self, agent_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply team inheritance to agent configuration if agent is part of a team."""
        try:
            from lib.utils.config_inheritance import ConfigInheritanceManager
            import yaml
            import os
            
            # Check if strict validation is enabled (fail-fast mode) - defaults to true
            strict_validation = os.getenv("HIVE_STRICT_VALIDATION", "true").lower() == "true"
            
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
                            raise ValueError(f"Agent {agent_id} inheritance validation failed: Cannot read team config {team_config_file}")
                        else:
                            logger.warning(f"🔧 {error_msg}")
                            
                except Exception as e:
                    failed_team_configs.append(team_config_file)
                    error_msg = f"Error reading team config {team_config_file}: {e}"
                    
                    if strict_validation:
                        logger.error(f"🔧 STRICT VALIDATION FAILED: {error_msg}")
                        raise ValueError(f"Agent {agent_id} inheritance validation failed: Cannot read team config {team_config_file}")
                    else:
                        logger.warning(f"🔧 {error_msg}")
            
            # Report failed team configs if any
            if failed_team_configs and strict_validation:
                logger.error(f"🔧 Agent {agent_id} inheritance check failed to read {len(failed_team_configs)} team configs: {failed_team_configs}")
            
            if not team_config:
                logger.debug(f"🔧 No team found for agent {agent_id}, using config as-is")
                return config
            
            # Apply inheritance
            manager = ConfigInheritanceManager()
            agent_configs = {agent_id: config}
            enhanced_configs = manager.apply_inheritance(team_config, agent_configs)
            
            # Validate inheritance
            errors = manager.validate_configuration(team_config, enhanced_configs)
            if errors:
                if strict_validation:
                    logger.error(f"🔧 STRICT VALIDATION FAILED: Inheritance validation errors for agent {agent_id}:")
                    for error in errors:
                        logger.error(f"  ❌ {error}")
                    raise ValueError(f"Agent {agent_id} inheritance validation failed: {len(errors)} configuration errors")
                else:
                    logger.warning(f"🔧 Inheritance validation warnings for agent {agent_id}:")
                    for error in errors:
                        logger.warning(f"  ⚠️  {error}")
            
            # Generate inheritance report
            report = manager.generate_inheritance_report(team_config, agent_configs, enhanced_configs)
            logger.debug(f"🔧 Agent {agent_id} in team {team_id}: {report}")
            
            return enhanced_configs[agent_id]
            
        except ValueError:
            # Re-raise validation errors (these are intentional failures)
            raise
        except Exception as e:
            error_msg = f"Error applying inheritance to agent {agent_id}: {e}"
            strict_validation = os.getenv("HIVE_STRICT_VALIDATION", "true").lower() == "true"
            
            if strict_validation:
                logger.error(f"🔧 STRICT VALIDATION FAILED: {error_msg}")
                raise ValueError(f"Agent {agent_id} inheritance failed due to unexpected error: {e}")
            else:
                logger.warning(f"🔧 {error_msg}")
                return config  # Fallback to original config
    
    def _load_agent_tools(self, component_id: str, config: Dict[str, Any]) -> list:
        """Load custom tools for an agent from its tools.py file."""
        import os
        tools = []
        missing_tools = []
        
        # Check if strict validation is enabled (fail-fast mode) - defaults to true
        strict_validation = os.getenv("HIVE_STRICT_VALIDATION", "true").lower() == "true"
        
        try:
            # Use agent ID as-is for Python module path (importlib handles hyphens)
            tools_module_path = f"ai.agents.{component_id}.tools"
            
            import importlib
            tools_module = importlib.import_module(tools_module_path)
            
            # Get tool names from config
            tool_names = config.get("tools", [])
            
            if tool_names:
                for tool_name in tool_names:
                    if hasattr(tools_module, tool_name):
                        tool_function = getattr(tools_module, tool_name)
                        tools.append(tool_function)
                        logger.debug(f"🤖 Loaded tool '{tool_name}' for agent {component_id}")
                    else:
                        missing_tools.append(tool_name)
                        error_msg = f"Tool '{tool_name}' not found in {tools_module_path}"
                        
                        if strict_validation:
                            logger.error(f"🤖 STRICT VALIDATION FAILED: {error_msg}")
                            raise ValueError(f"Agent {component_id} tool validation failed: Missing required tool '{tool_name}' in {tools_module_path}")
                        else:
                            logger.warning(f"🤖 {error_msg}")
                            
                # Report missing tools summary
                if missing_tools:
                    if strict_validation:
                        logger.error(f"🤖 Agent {component_id} missing {len(missing_tools)} required tools: {missing_tools}")
                    else:
                        logger.warning(f"🤖 Agent {component_id} missing {len(missing_tools)} tools (non-critical): {missing_tools}")
            else:
                # Fallback: load all tools from module's __all__ if no specific tools configured
                if hasattr(tools_module, '__all__'):
                    for tool_name in tools_module.__all__:
                        if hasattr(tools_module, tool_name):
                            tool_function = getattr(tools_module, tool_name)
                            tools.append(tool_function)
                            logger.debug(f"🤖 Auto-loaded tool '{tool_name}' for agent {component_id}")
                            
        except ImportError:
            # No tools.py file - check if tools are required
            tool_names = config.get("tools", [])
            if tool_names and strict_validation:
                logger.error(f"🤖 STRICT VALIDATION FAILED: No tools.py module found for agent {component_id} but tools are configured: {tool_names}")
                raise ValueError(f"Agent {component_id} tool validation failed: Missing tools.py module but tools are configured")
            else:
                # No tools.py file - that's okay, just use default tools
                logger.debug(f"🤖 No custom tools found for agent {component_id}")
        except ValueError:
            # Re-raise validation errors (these are intentional failures)
            raise
        except Exception as e:
            error_msg = f"Error loading tools for agent {component_id}: {e}"
            
            if strict_validation:
                logger.error(f"🤖 STRICT VALIDATION FAILED: {error_msg}")
                raise ValueError(f"Agent {component_id} tool loading failed due to unexpected error: {e}")
            else:
                logger.error(f"🤖 {error_msg}")
        
        return tools
    
    async def _create_team(
        self,
        component_id: str,
        config: Dict[str, Any],
        session_id: Optional[str],
        debug_mode: bool,
        user_id: Optional[str],
        **kwargs
    ) -> Team:
        """Create team using dynamic Agno Team proxy with inheritance validation."""
        
        logger.debug(f"🔧 Creating team {component_id} (session_id={session_id}, debug_mode={debug_mode})")
        
        try:
            # Validate team inheritance configuration
            logger.debug(f"🔧 Validating inheritance for team {component_id}")
            enhanced_config = self._validate_team_inheritance(component_id, config)
            logger.debug(f"🔧 Team {component_id} inheritance validation completed")
            
            # Use the dynamic team proxy system for automatic Agno compatibility
            logger.debug(f"🔧 Loading AgnoTeamProxy for team {component_id}")
            from lib.utils.agno_proxy import get_agno_team_proxy
            
            proxy = get_agno_team_proxy()
            logger.debug(f"🔧 AgnoTeamProxy loaded successfully for team {component_id}")
            
            # Create team using dynamic proxy
            logger.debug(f"🔧 Creating team instance via proxy for {component_id}")
            team = await proxy.create_team(
                component_id=component_id,
                config=enhanced_config,
                session_id=session_id,
                debug_mode=debug_mode,
                user_id=user_id,
                db_url=self.db_url,
                **kwargs
            )
            
            logger.debug(f"🤖 Team {component_id} created with inheritance validation and {len(proxy.get_supported_parameters())} available parameters")
            
            return team
        except Exception as e:
            logger.error(f"🔧 Team creation failed for {component_id}: {type(e).__name__}: {str(e)}", 
                        exc_info=True)
            raise
    
    def _validate_team_inheritance(self, team_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate team configuration for proper inheritance setup."""
        try:
            from lib.utils.config_inheritance import ConfigInheritanceManager
            import yaml
            import os
            
            # Check if strict validation is enabled (fail-fast mode) - defaults to true
            strict_validation = os.getenv("HIVE_STRICT_VALIDATION", "true").lower() == "true"
            
            # Load all member agent configurations
            agent_configs = {}
            members = config.get('members') or []
            missing_members = []
            logger.debug(f"🔧 Team {team_id} has members: {members}")
            
            for member_id in members:
                agent_config_path = f"ai/agents/{member_id}/config.yaml"
                logger.debug(f"🔧 Loading member config: {agent_config_path}")
                try:
                    agent_config = load_yaml_cached(agent_config_path)
                    if agent_config:
                        agent_configs[member_id] = agent_config
                        logger.debug(f"🔧 Successfully loaded config for member {member_id}")
                    else:
                        raise FileNotFoundError(f"Config file not found or invalid: {agent_config_path}")
                except Exception as e:
                    missing_members.append(member_id)
                    error_msg = f"Could not load member config for {member_id}: {e}"
                    
                    if strict_validation:
                        logger.error(f"🔧 STRICT VALIDATION FAILED: {error_msg}")
                        logger.error(f"🔧 Failed path: {agent_config_path}")
                        raise ValueError(f"Team {team_id} dependency validation failed: Missing required member '{member_id}' at {agent_config_path}")
                    else:
                        logger.warning(f"🔧 {error_msg}")
                        logger.debug(f"🔧 Failed path: {agent_config_path}")
                        continue
            
            # Validate that we have at least some members loaded
            if not agent_configs:
                error_msg = f"No member agents found for team {team_id}"
                if strict_validation:
                    logger.error(f"🔧 STRICT VALIDATION FAILED: {error_msg}")
                    raise ValueError(f"Team {team_id} has no valid members. Missing members: {missing_members}")
                else:
                    logger.warning(f"🔧 {error_msg}")
                    return config
            
            # Report missing members summary
            if missing_members:
                if strict_validation:
                    logger.error(f"🔧 Team {team_id} missing {len(missing_members)} required members: {missing_members}")
                else:
                    logger.warning(f"🔧 Team {team_id} missing {len(missing_members)} members (non-critical): {missing_members}")
            
            # Validate inheritance setup
            manager = ConfigInheritanceManager()
            errors = manager.validate_configuration(config, agent_configs)
            
            if errors:
                if strict_validation:
                    logger.error(f"🔧 STRICT VALIDATION FAILED: Team inheritance validation errors for {team_id}:")
                    for error in errors:
                        logger.error(f"  ❌ {error}")
                    raise ValueError(f"Team {team_id} inheritance validation failed: {len(errors)} configuration errors")
                else:
                    logger.warning(f"🔧 Team inheritance validation errors for {team_id}:")
                    for error in errors:
                        logger.warning(f"  ⚠️  {error}")
            
            # Generate inheritance preview report
            enhanced_agent_configs = manager.apply_inheritance(config, agent_configs)
            report = manager.generate_inheritance_report(config, agent_configs, enhanced_agent_configs)
            logger.debug(f"🔧 Team {team_id}: {report}")
            
            return config
            
        except ValueError:
            # Re-raise validation errors (these are intentional failures)
            raise
        except Exception as e:
            error_msg = f"Error validating team inheritance for {team_id}: {e}"
            strict_validation = os.getenv("HIVE_STRICT_VALIDATION", "true").lower() == "true"
            
            if strict_validation:
                logger.error(f"🔧 STRICT VALIDATION FAILED: {error_msg}")
                raise ValueError(f"Team {team_id} validation failed due to unexpected error: {e}")
            else:
                logger.warning(f"🔧 {error_msg}")
                return config  # Fallback to original config
    
    async def _create_workflow(
        self,
        component_id: str,
        config: Dict[str, Any],
        session_id: Optional[str],
        debug_mode: bool,
        user_id: Optional[str],
        **kwargs
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
            **kwargs
        )
        
        logger.debug(f"🤖 Workflow {component_id} created with {len(proxy.get_supported_parameters())} available Agno Workflow parameters")
        
        return workflow
    
    async def _create_component_from_yaml(
        self,
        component_id: str,
        component_type: str,
        session_id: Optional[str],
        debug_mode: bool,
        user_id: Optional[str],
        **kwargs
    ) -> Union[Agent, Team, Workflow]:
        """
        Fallback method to create components directly from YAML during first startup.
        Used when database doesn't have synced versions yet.
        """
        import yaml
        from pathlib import Path
        
        # Determine config file path based on component type
        config_paths = {
            'agent': f'ai/agents/{component_id}/config.yaml',
            'team': f'ai/teams/{component_id}/config.yaml', 
            'workflow': f'ai/workflows/{component_id}/config.yaml'
        }
        
        config_file = config_paths.get(component_type)
        if not config_file:
            raise ValueError(f"Unsupported component type: {component_type}")
        
        config_path = Path(config_file)
        if not config_path.exists():
            raise ValueError(f"Config file not found: {config_file}")
        
        # Load YAML configuration
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to load YAML config from {config_file}: {e}")
        
        if not yaml_config or component_type not in yaml_config:
            raise ValueError(f"Invalid YAML config in {config_file}: missing '{component_type}' section")
        
        logger.debug(f"🔧 Loading {component_type} {component_id} from YAML (first startup fallback)")
        
        # Use the same creation methods but with YAML config
        creation_methods = {
            "agent": self._create_agent,
            "team": self._create_team,
            "workflow": self._create_workflow
        }
        
        return await creation_methods[component_type](
            component_id=component_id,
            config=yaml_config,  # Pass the full YAML config
            session_id=session_id,
            debug_mode=debug_mode,
            user_id=user_id,
            **kwargs
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
async def create_agent(agent_id: str, version: Optional[int] = None, **kwargs) -> Agent:
    """Create agent using factory pattern."""
    return await get_version_factory().create_versioned_component(
        agent_id, "agent", version, **kwargs
    )


async def create_team(team_id: str, version: Optional[int] = None, **kwargs) -> Team:
    """Create team using factory pattern (unified with agents)."""
    return await get_version_factory().create_versioned_component(
        team_id, "team", version, **kwargs
    )


async def create_versioned_workflow(workflow_id: str, version: Optional[int] = None, **kwargs) -> Workflow:
    """Create versioned workflow using Agno storage."""
    return await get_version_factory().create_versioned_component(
        workflow_id, "workflow", version, **kwargs
    )
