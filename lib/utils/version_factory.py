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
from lib.knowledge.knowledge_factory import get_knowledge_base


def load_global_knowledge_config():
    """Load global knowledge configuration with fallback"""
    try:
        global_config_path = Path(__file__).parent.parent / "knowledge/config.yaml"
        with open(global_config_path) as f:
            global_config = yaml.safe_load(f)
        return global_config.get("knowledge", {})
    except Exception as e:
        logger.warning("Could not load global knowledge config: %s", e)
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
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable required")
        
        self.version_service = AgnoVersionService(self.db_url)
    
    def create_versioned_component(
        self,
        component_id: str,
        component_type: str,
        version: Optional[int] = None,
        session_id: Optional[str] = None,
        debug_mode: bool = False,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        cpf: Optional[str] = None
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
            user_name: User name
            phone_number: Phone number
            cpf: CPF
            
        Returns:
            Configured component instance
        """
        
        # Get version configuration
        if version is not None:
            version_record = self.version_service.get_version(component_id, version)
            if not version_record:
                raise ValueError(f"Version {version} not found for {component_id}")
        else:
            version_record = self.version_service.get_active_version(component_id)
            if not version_record:
                # Fallback: Try to sync from YAML if no active version found
                print(f"⚠️ No active version found for {component_id}, attempting YAML fallback...")
                try:
                    version_record = self._sync_from_yaml_fallback(component_id, component_type)
                    if not version_record:
                        raise ValueError(f"No active version found for {component_id} and YAML fallback failed")
                    print(f"✅ Loaded {component_id} from YAML fallback (version {version_record.version})")
                except Exception as e:
                    raise ValueError(f"No active version found for {component_id} and YAML fallback failed: {e}")
        
        config = version_record.config
        
        # Validate component type matches
        if version_record.component_type != component_type:
            raise ValueError(f"Component {component_id} is type {version_record.component_type}, not {component_type}")
        
        # Create component based on type
        if component_type == "agent":
            return self._create_agent(
                component_id=component_id,
                config=config,
                session_id=session_id,
                debug_mode=debug_mode,
                user_id=user_id
            )
        elif component_type == "team":
            return self._create_team(
                component_id=component_id,
                config=config,
                session_id=session_id,
                debug_mode=debug_mode,
                user_id=user_id
            )
        elif component_type == "workflow":
            return self._create_workflow(
                component_id=component_id,
                config=config,
                session_id=session_id,
                debug_mode=debug_mode,
                user_id=user_id
            )
        else:
            raise ValueError(f"Unsupported component type: {component_type}")
    
    def _create_agent(
        self,
        component_id: str,
        config: Dict[str, Any],
        session_id: Optional[str],
        debug_mode: bool,
        user_id: Optional[str]
    ) -> Agent:
        """Create versioned agent with clean configuration."""
        
        # Create model
        model_config = config.get("model", {})
        model = Claude(
            id=model_config.get("id", "claude-sonnet-4-20250514"),
            temperature=model_config.get("temperature", 0.7),
            max_tokens=model_config.get("max_tokens", 2000)
        )
        
        # Create storage
        storage_config = config.get("storage", {})
        storage = PostgresStorage(
            table_name=storage_config.get("table_name", "agent_sessions"),
            db_url=self.db_url,
            auto_upgrade_schema=storage_config.get("auto_upgrade_schema", True)
        )
        
        # Create memory if enabled
        memory = None
        memory_config = config.get("memory", {})
        if memory_config.get("enable_user_memories", False):
            from lib.memory.memory_factory import create_agent_memory
            memory = create_agent_memory(component_id, self.db_url)
        
        # Create knowledge base from configuration (global + agent overrides)
        knowledge_base = None
        
        # Load global knowledge config first
        global_knowledge = load_global_knowledge_config()
        
        # Get agent-specific knowledge config
        agent_knowledge = config.get("knowledge_filter", {})
        
        # Agent config overrides global config
        csv_path = agent_knowledge.get("csv_file_path") or global_knowledge.get("csv_file_path")
        max_results = agent_knowledge.get("max_results", global_knowledge.get("max_results", 10))
        
        if csv_path:
            try:
                knowledge_base = get_knowledge_base(
                    db_url=self.db_url,
                    num_documents=max_results,
                    csv_path=csv_path
                )
                logger.info(f"Knowledge base loaded for agent {component_id}: {csv_path}")
            except Exception as e:
                logger.error(f"Failed to load knowledge base for agent {component_id}: {e}")
        
        # Load custom tools if they exist
        tools = self._load_agent_tools(component_id, config)
        
        # Create agent
        agent_config = config.get("agent", {})
        agent = Agent(
            name=agent_config.get("name", f"Agent {component_id}"),
            agent_id=component_id,
            role=agent_config.get("role"),
            instructions=config.get("instructions", "You are a helpful assistant."),
            model=model,
            storage=storage,
            memory=memory,
            knowledge=knowledge_base,  # Add knowledge base to agent
            tools=tools,  # Add custom tools
            session_id=session_id,
            user_id=user_id,
            debug_mode=debug_mode,
            add_history_to_messages=config.get("memory", {}).get("add_history_to_messages", True),
            num_history_runs=config.get("memory", {}).get("num_history_runs", 5),
            enable_user_memories=memory_config.get("enable_user_memories", False),
            enable_agentic_memory=memory_config.get("enable_agentic_memory", False)
        )
        
        # Add metadata
        agent.metadata = {
            "version": agent_config.get("version", 1),
            "loaded_from": "agno_storage",
            "agent_id": component_id
        }
        
        return agent
    
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
                        logger.info(f"Loaded tool '{tool_name}' for agent {component_id}")
                    else:
                        logger.warning(f"Tool '{tool_name}' not found in {tools_module_path}")
            else:
                # Fallback: load all tools from module's __all__ if no specific tools configured
                if hasattr(tools_module, '__all__'):
                    for tool_name in tools_module.__all__:
                        if hasattr(tools_module, tool_name):
                            tool_function = getattr(tools_module, tool_name)
                            tools.append(tool_function)
                            logger.info(f"Auto-loaded tool '{tool_name}' for agent {component_id}")
                            
        except ImportError:
            # No tools.py file - that's okay, just use default tools
            logger.debug(f"No custom tools found for agent {component_id}")
        except Exception as e:
            logger.error(f"Error loading tools for agent {component_id}: {e}")
        
        return tools
    
    def _create_team(
        self,
        component_id: str,
        config: Dict[str, Any],
        session_id: Optional[str],
        debug_mode: bool,
        user_id: Optional[str]
    ) -> Team:
        """Create versioned team with clean configuration."""
        
        # Create model
        model_config = config.get("model", {})
        model = Claude(
            id=model_config.get("id", "claude-sonnet-4-20250514"),
            temperature=model_config.get("temperature", 1.0),
            max_tokens=model_config.get("max_tokens", 2000)
        )
        
        # Create storage
        storage_config = config.get("storage", {})
        storage = PostgresStorage(
            table_name=storage_config.get("table_name", "team_sessions"),
            db_url=self.db_url,
            mode=storage_config.get("mode", "team"),
            auto_upgrade_schema=storage_config.get("auto_upgrade_schema", True)
        )
        
        # Create team knowledge base from configuration (global + team overrides)
        team_knowledge_base = None
        
        # Load global knowledge config first
        global_knowledge = load_global_knowledge_config()
        
        # Get team-specific knowledge config
        team_knowledge = config.get("knowledge", {})
        
        # Team config overrides global config
        csv_path = team_knowledge.get("csv_file_path") or global_knowledge.get("csv_file_path")
        max_results = team_knowledge.get("max_results", global_knowledge.get("max_results", 10))
        
        if csv_path:
            try:
                team_knowledge_base = get_knowledge_base(
                    db_url=self.db_url,
                    num_documents=max_results,
                    csv_path=csv_path
                )
                logger.info(f"Team knowledge base loaded for team {component_id}: {csv_path}")
            except Exception as e:
                logger.error(f"Failed to load team knowledge base for team {component_id}: {e}")
        
        # Load member agents (simplified)
        members = []
        member_names = config.get("members", [])
        
        for member_name in member_names:
            try:
                # Try to get agent using registry
                from ai.agents.registry import get_agent
                member_agent = get_agent(
                    member_name,
                    session_id=session_id,
                    debug_mode=debug_mode,
                    user_id=user_id
                )
                members.append(member_agent)
            except Exception as e:
                logger.warning(f"Could not load team member {member_name}: {e}")
        
        # Create team
        team_config = config.get("team", {})
        team = Team(
            name=team_config.get("name", f"Team {component_id}"),
            team_id=component_id,
            mode=team_config.get("mode", "route"),
            members=members,
            instructions=config.get("instructions", "You are a helpful team."),
            model=model,
            storage=storage,
            knowledge_base=team_knowledge_base,  # Add team knowledge base
            session_id=session_id,
            user_id=user_id,
            debug_mode=debug_mode,
            add_history_to_messages=config.get("memory", {}).get("add_history_to_messages", True),
            num_history_runs=config.get("memory", {}).get("num_history_runs", 5)
        )
        
        # Add metadata
        team.metadata = {
            "version": team_config.get("version", 1),
            "loaded_from": "agno_storage",
            "team_id": component_id
        }
        
        return team
    
    def _create_workflow(
        self,
        component_id: str,
        config: Dict[str, Any],
        session_id: Optional[str],
        debug_mode: bool,
        user_id: Optional[str]
    ) -> Workflow:
        """Create versioned workflow with clean configuration."""
        
        # Create storage
        storage_config = config.get("storage", {})
        storage = PostgresStorage(
            table_name=storage_config.get("table_name", f"{component_id}_workflows"),
            db_url=self.db_url,
            auto_upgrade_schema=storage_config.get("auto_upgrade_schema", True)
        )
        
        # Import specific workflow class
        if component_id == "human-handoff":
            from ai.workflows.human_handoff.workflow import get_human_handoff_workflow
            workflow = get_human_handoff_workflow(
                session_id=session_id,
                user_id=user_id,
                debug_mode=debug_mode,
                storage=storage
            )
        elif component_id == "conversation-typification":
            from ai.workflows.conversation_typification.workflow import get_conversation_typification_workflow
            workflow = get_conversation_typification_workflow(debug_mode=debug_mode)
        else:
            raise ValueError(f"Unknown workflow type: {component_id}")
        
        # Add metadata
        workflow_config = config.get("workflow", {})
        workflow.metadata = {
            "version": workflow_config.get("version", 1),
            "loaded_from": "agno_storage",
            "workflow_id": component_id
        }
        
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
                print(f"⚠️ Error reading {config_file}: {e}")
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


# Convenience functions for backward compatibility
def create_agent(agent_id: str, version: Optional[int] = None, **kwargs) -> Agent:
    """Create agent using Agno storage and configuration."""
    return get_version_factory().create_versioned_component(
        agent_id, "agent", version, **kwargs
    )

# Backwards compatibility alias
create_versioned_agent = create_agent


def create_versioned_team(team_id: str, version: Optional[int] = None, **kwargs) -> Team:
    """Create versioned team using Agno storage."""
    return get_version_factory().create_versioned_component(
        team_id, "team", version, **kwargs
    )


def create_versioned_workflow(workflow_id: str, version: Optional[int] = None, **kwargs) -> Workflow:
    """Create versioned workflow using Agno storage."""
    return get_version_factory().create_versioned_component(
        workflow_id, "workflow", version, **kwargs
    )