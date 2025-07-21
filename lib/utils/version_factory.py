"""
Agno-Based Version Factory

Clean implementation using Agno storage for component versioning.
Replaces the old database-based version factory.
"""

from typing import Optional, Dict, Any, Union
from pathlib import Path
import yaml
import os
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.utils.log import logger

from lib.versioning import AgnoVersionService
# Knowledge base creation is now handled by Agno CSVKnowledgeBase + PgVector directly

from datetime import datetime


def load_global_knowledge_config():
    """Load global knowledge configuration with fallback"""
    try:
        global_config_path = Path(__file__).parent.parent / "knowledge/config.yaml"
        with open(global_config_path) as f:
            global_config = yaml.safe_load(f)
        return global_config.get("knowledge", {})
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
    
    # _create_context_functions method removed - AGNO handles context natively
    
    # _build_dynamic_instructions method removed - AGNO handles instructions natively
    
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
        
        # FIRST: Check if this is a dev version by reading YAML directly
        dev_version_record = self._check_for_dev_version(component_id, component_type)
        if dev_version_record:
            logger.info(f"🐛 DEV MODE: Loading {component_id} directly from YAML (bypassing database)")
            version_record = dev_version_record
        else:
            # Normal database lookup logic
            if version is not None:
                version_record = await self.version_service.get_version(component_id, version)
                if not version_record:
                    raise ValueError(f"Version {version} not found for {component_id}")
            else:
                version_record = await self.version_service.get_active_version(component_id)
                if not version_record:
                    # Fallback: Try to sync from YAML if no active version found
                    logger.warning(f"🔧 No active version found for {component_id}, attempting YAML fallback...")
                    try:
                        version_record = self._sync_from_yaml_fallback(component_id, component_type)
                        if not version_record:
                            raise ValueError(f"No active version found for {component_id} and YAML fallback failed")
                        logger.info(f"🔧 Loaded {component_id} from YAML fallback (version {version_record.version})")
                    except Exception as e:
                        raise ValueError(f"No active version found for {component_id} and YAML fallback failed: {e}")
        
        config = version_record.config
        
        # Validate component type matches
        if version_record.component_type != component_type:
            raise ValueError(f"Component {component_id} is type {version_record.component_type}, not {component_type}")
        
        # Create component based on type using appropriate Agno proxy
        if component_type == "agent":
            return self._create_agent(
                component_id=component_id,
                config=config,
                session_id=session_id,
                debug_mode=debug_mode,
                user_id=user_id,
                **kwargs
            )
        elif component_type == "team":
            return await self._create_team(
                component_id=component_id,
                config=config,
                session_id=session_id,
                debug_mode=debug_mode,
                user_id=user_id,
                **kwargs
            )
        elif component_type == "workflow":
            return self._create_workflow(
                component_id=component_id,
                config=config,
                session_id=session_id,
                debug_mode=debug_mode,
                user_id=user_id,
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported component type: {component_type}")
    
    def _create_agent(
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
        agent = proxy.create_agent(
            component_id=component_id,
            config=enhanced_config,
            session_id=session_id,
            debug_mode=debug_mode,
            user_id=user_id,
            db_url=self.db_url
        )
        
        logger.info(f"🤖 Agent {component_id} created with inheritance and {len(proxy.get_supported_parameters())} available parameters")
        
        return agent
    
    def _apply_team_inheritance(self, agent_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply team inheritance to agent configuration if agent is part of a team."""
        try:
            from lib.utils.config_inheritance import ConfigInheritanceManager
            import glob
            import yaml
            
            # Find team that contains this agent
            team_config = None
            team_id = None
            
            for team_config_file in glob.glob("ai/teams/*/config.yaml"):
                try:
                    with open(team_config_file, 'r') as f:
                        potential_team_config = yaml.safe_load(f)
                    
                    # Check if this agent is a member of this team
                    members = potential_team_config.get('members') or []
                    if agent_id in members:
                        team_config = potential_team_config
                        team_id = team_config_file.split('/')[-2]  # Extract team_id from path
                        break
                        
                except Exception as e:
                    logger.warning(f"🔧 Error reading team config {team_config_file}: {e}")
                    continue
            
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
                logger.warning(f"🔧 Inheritance validation warnings for agent {agent_id}:")
                for error in errors:
                    logger.warning(f"  ⚠️  {error}")
            
            # Generate inheritance report
            report = manager.generate_inheritance_report(team_config, agent_configs, enhanced_configs)
            logger.debug(f"🔧 Agent {agent_id} in team {team_id}: {report}")
            
            return enhanced_configs[agent_id]
            
        except Exception as e:
            logger.warning(f"🔧 Error applying inheritance to agent {agent_id}: {e}")
            return config  # Fallback to original config
    
    def _load_agent_tools(self, component_id: str, config: Dict[str, Any]) -> list:
        """Load custom tools for an agent from its tools.py file."""
        tools = []
        
        try:
            # Convert hyphenated agent ID to underscore for Python module path
            module_name = component_id.replace("-", "_")
            tools_module_path = f"ai.agents.{module_name}.tools"
            
            import importlib
            tools_module = importlib.import_module(tools_module_path)
            
            # Get tool names from config
            tool_names = config.get("tools", [])
            
            if tool_names:
                for tool_name in tool_names:
                    if hasattr(tools_module, tool_name):
                        tool_function = getattr(tools_module, tool_name)
                        tools.append(tool_function)
                        logger.info(f"🤖 Loaded tool '{tool_name}' for agent {component_id}")
                    else:
                        logger.warning(f"🤖 Tool '{tool_name}' not found in {tools_module_path}")
            else:
                # Fallback: load all tools from module's __all__ if no specific tools configured
                if hasattr(tools_module, '__all__'):
                    for tool_name in tools_module.__all__:
                        if hasattr(tools_module, tool_name):
                            tool_function = getattr(tools_module, tool_name)
                            tools.append(tool_function)
                            logger.info(f"🤖 Auto-loaded tool '{tool_name}' for agent {component_id}")
                            
        except ImportError:
            # No tools.py file - that's okay, just use default tools
            logger.debug(f"🤖 No custom tools found for agent {component_id}")
        except Exception as e:
            logger.error(f"🤖 Error loading tools for agent {component_id}: {e}")
        
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
        
        # Validate team inheritance configuration
        enhanced_config = self._validate_team_inheritance(component_id, config)
        
        # Use the dynamic team proxy system for automatic Agno compatibility
        from lib.utils.agno_proxy import get_agno_team_proxy
        
        proxy = get_agno_team_proxy()
        
        # Create team using dynamic proxy
        team = await proxy.create_team(
            component_id=component_id,
            config=enhanced_config,
            session_id=session_id,
            debug_mode=debug_mode,
            user_id=user_id,
            db_url=self.db_url,
            **kwargs
        )
        
        logger.info(f"🤖 Team {component_id} created with inheritance validation and {len(proxy.get_supported_parameters())} available parameters")
        
        return team
    
    def _validate_team_inheritance(self, team_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate team configuration for proper inheritance setup."""
        try:
            from lib.utils.config_inheritance import ConfigInheritanceManager
            import glob
            import yaml
            
            # Load all member agent configurations
            agent_configs = {}
            members = config.get('members') or []
            
            for member_id in members:
                agent_config_path = f"ai/agents/{member_id}/config.yaml"
                try:
                    with open(agent_config_path, 'r') as f:
                        agent_configs[member_id] = yaml.safe_load(f)
                except Exception as e:
                    logger.warning(f"🔧 Could not load member config for {member_id}: {e}")
                    continue
            
            if not agent_configs:
                logger.debug(f"🔧 No member agents found for team {team_id}")
                return config
            
            # Validate inheritance setup
            manager = ConfigInheritanceManager()
            errors = manager.validate_configuration(config, agent_configs)
            
            if errors:
                logger.warning(f"🔧 Team inheritance validation errors for {team_id}:")
                for error in errors:
                    logger.warning(f"  ⚠️  {error}")
            
            # Generate inheritance preview report
            enhanced_agent_configs = manager.apply_inheritance(config, agent_configs)
            report = manager.generate_inheritance_report(config, agent_configs, enhanced_agent_configs)
            logger.info(f"🔧 Team {team_id}: {report}")
            
            return config
            
        except Exception as e:
            logger.warning(f"🔧 Error validating team inheritance for {team_id}: {e}")
            return config  # Fallback to original config
    
    def _create_workflow(
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
        workflow = proxy.create_workflow(
            component_id=component_id,
            config=config,
            session_id=session_id,
            debug_mode=debug_mode,
            user_id=user_id,
            db_url=self.db_url,
            **kwargs
        )
        
        logger.info(f"🤖 Workflow {component_id} created with {len(proxy.get_supported_parameters())} available Agno Workflow parameters")
        
        return workflow
    
    def _sync_from_yaml_fallback(self, component_id: str, component_type: str):
        """Fallback: Read directly from YAML when no database version exists"""
        import yaml
        from pathlib import Path
        
        # Map component types to file patterns
        type_patterns = {
            "agent": f"ai/agents/*/config.yaml",
            "team": f"ai/teams/*/config.yaml", 
            "workflow": f"ai/workflows/*/config.yaml"
        }
        
        if component_type not in type_patterns:
            return None
            
        # Search for the component's config file
        import glob
        pattern = type_patterns[component_type]
        
        for config_file in glob.glob(pattern):
            try:
                with open(config_file, 'r') as f:
                    yaml_config = yaml.safe_load(f)
                
                if not yaml_config or component_type not in yaml_config:
                    continue
                
                # Check if this is the right component
                component_section = yaml_config[component_type]
                yaml_component_id = (
                    component_section.get('agent_id') or
                    component_section.get('team_id') or
                    component_section.get('workflow_id') or
                    component_section.get('component_id')
                )
                
                if yaml_component_id == component_id:
                    # Found matching component, create version record
                    from lib.versioning.agno_version_service import VersionInfo
                    
                    version = component_section.get('version', 1)
                    
                    
                    return VersionInfo(
                        component_id=component_id,
                        component_type=component_type,
                        version=version,
                        config=yaml_config,
                        created_at="yaml-fallback",
                        created_by="yaml-fallback",
                        description=f"Loaded from YAML fallback: {config_file}",
                        is_active=True
                    )
                    
            except Exception as e:
                logger.warning(f"🔧 Error reading {config_file}: {e}")
                continue
        
        return None
    
    def _check_for_dev_version(self, component_id: str, component_type: str):
        """Check if YAML has version: 'dev' and return direct YAML load"""
        import yaml
        import glob
        
        # Map component types to file patterns
        type_patterns = {
            "agent": f"ai/agents/*/config.yaml",
            "team": f"ai/teams/*/config.yaml", 
            "workflow": f"ai/workflows/*/config.yaml"
        }
        
        if component_type not in type_patterns:
            return None
            
        pattern = type_patterns[component_type]
        
        for config_file in glob.glob(pattern):
            try:
                with open(config_file, 'r') as f:
                    yaml_config = yaml.safe_load(f)
                
                if not yaml_config or component_type not in yaml_config:
                    continue
                
                component_section = yaml_config[component_type]
                yaml_component_id = (
                    component_section.get('agent_id') or
                    component_section.get('team_id') or
                    component_section.get('workflow_id') or
                    component_section.get('component_id')
                )
                
                if yaml_component_id == component_id:
                    version = component_section.get('version')
                    
                    # Check if version is "dev"
                    if version == "dev":
                        from lib.versioning.agno_version_service import VersionInfo
                        return VersionInfo(
                            component_id=component_id,
                            component_type=component_type,
                            version="dev",
                            config=yaml_config,
                            created_at="dev-mode",
                            created_by="dev-mode",
                            description=f"DEV MODE: Always load from YAML {config_file}",
                            is_active=True
                        )
                        
            except Exception as e:
                continue
        
        return None


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


# Synchronous wrappers for Agno framework compatibility
def create_agent_sync(agent_id: str, version: Optional[int] = None, **kwargs) -> Agent:
    """Synchronous wrapper for create_agent - for Agno framework compatibility."""
    import asyncio
    
    try:
        loop = asyncio.get_running_loop()
        # We're in an event loop, need to handle carefully
        import concurrent.futures
        
        def run_async():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(create_agent(agent_id, version, **kwargs))
            finally:
                new_loop.close()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            return future.result()
            
    except RuntimeError:
        return asyncio.run(create_agent(agent_id, version, **kwargs))


def create_team_sync(team_id: str, version: Optional[int] = None, **kwargs) -> Team:
    """Synchronous wrapper for create_team - for Agno framework compatibility."""
    import asyncio
    
    try:
        loop = asyncio.get_running_loop()
        # We're in an event loop, need to handle carefully
        import concurrent.futures
        
        def run_async():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(create_team(team_id, version, **kwargs))
            finally:
                new_loop.close()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            return future.result()
            
    except RuntimeError:
        return asyncio.run(create_team(team_id, version, **kwargs))


def create_versioned_workflow_sync(workflow_id: str, version: Optional[int] = None, **kwargs) -> Workflow:
    """Synchronous wrapper for create_versioned_workflow - for Agno framework compatibility."""
    import asyncio
    
    try:
        loop = asyncio.get_running_loop()
        # We're in an event loop, need to handle carefully
        import concurrent.futures
        
        def run_async():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(create_versioned_workflow(workflow_id, version, **kwargs))
            finally:
                new_loop.close()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            return future.result()
            
    except RuntimeError:
        return asyncio.run(create_versioned_workflow(workflow_id, version, **kwargs))