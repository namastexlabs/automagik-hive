"""
Unified Version Factory - Single Implementation for All Component Types

Consolidates ALL features from agents/teams/workflows version factories.
Eliminates 80%+ code duplication across component-specific implementations.

Features Consolidated:
- Agent Version Factory with MCP integration and knowledge base
- Team creation with enhanced parameters and YAML sync
- Workflow creation with specialized routing
- Migration capabilities and component discovery
- Configuration defaults and validation
"""

from typing import Optional, Dict, Any, Union, List
from pathlib import Path
import yaml
from sqlalchemy.orm import Session
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.tools import Function
from agno.tools.mcp import MCPTools
from agno.utils.log import logger

from db.session import get_db, db_url
from db.services.component_version_service import ComponentVersionService
from core.config.yaml_parser import YAMLConfigParser
from core.mcp.catalog import MCPCatalog


class UnifiedVersionFactory:
    """
    Single factory for creating versioned components of any type.
    Eliminates code duplication across agent/team/workflow factories.
    
    Features:
    - Database-driven versioning with fallback to file configurations
    - MCP integration with connection pooling
    - Component discovery and migration capabilities
    - Configuration validation and defaults
    - Knowledge base integration for agents
    """
    
    def __init__(self, db_session: Session = None):
        """Initialize with optional database session."""
        self.db_session = db_session or next(get_db())
        self.component_service = ComponentVersionService(self.db_session)
        
        # MCP integration
        self.mcp_catalog = MCPCatalog()
        self.yaml_parser = YAMLConfigParser(self.mcp_catalog)
    
    def create_versioned_component(
        self,
        component_id: str,
        component_type: str,  # "agent", "team", "workflow"
        version: Optional[int] = None,
        session_id: Optional[str] = None,
        debug_mode: bool = False,
        # User context parameters
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        cpf: Optional[str] = None,
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
            user_id, user_name, phone_number, cpf: User context
            
        Returns:
            Configured component instance
        """
        
        # Load version configuration
        if version is not None:
            version_record = self.component_service.get_version(component_id, version)
            if not version_record:
                raise ValueError(f"Version {version} not found for {component_id}")
        else:
            version_record = self.component_service.get_active_version(component_id)
            if not version_record:
                raise ValueError(f"No active version found for {component_id}")
        
        config = version_record.config
        
        # Validate component type matches
        if version_record.component_type != component_type:
            raise ValueError(f"Component {component_id} is type {version_record.component_type}, not {component_type}")
        
        # Create component based on type
        if component_type == "agent":
            return self._create_agent(component_id, config, session_id, debug_mode, 
                                    user_id, user_name, phone_number, cpf, **kwargs)
        elif component_type == "team":
            return self._create_team(component_id, config, session_id, debug_mode,
                                   user_id, user_name, phone_number, cpf, **kwargs)
        elif component_type == "workflow":
            return self._create_workflow(component_id, config, session_id, debug_mode,
                                       user_id, user_name, phone_number, cpf, **kwargs)
        else:
            raise ValueError(f"Unsupported component type: {component_type}")
    
    def _create_agent(self, component_id: str, config: Dict[str, Any], 
                     session_id: Optional[str], debug_mode: bool,
                     user_id: Optional[str], user_name: Optional[str],
                     phone_number: Optional[str], cpf: Optional[str],
                     **kwargs) -> Agent:
        """Create versioned agent with advanced features."""
        
        # Import memory system
        from core.memory.memory_manager import create_memory_manager
        
        # Initialize memory
        memory = kwargs.get("memory")
        if memory is None:
            try:
                memory_manager = create_memory_manager()
                memory = memory_manager.memory
            except Exception as e:
                logger.warning(f"Memory initialization failed: {e}")
        
        # Create model instance
        model = self._create_model(config.get("model", {}))
        
        # Create storage instance  
        storage = self._create_storage(config, db_url)
        
        # Create tools from configuration with MCP support
        tools = self._create_tools(config)
        
        # Create knowledge base if configured
        knowledge_base = None
        search_knowledge = False
        enable_agentic_knowledge_filters = False
        knowledge_filters = {}
        
        if config.get("knowledge", {}).get("search_knowledge"):
            # Import knowledge base factory
            from core.knowledge.pagbank_knowledge_factory import get_knowledge_base
            knowledge_base = get_knowledge_base(db_url)
            
            # Get knowledge configuration
            knowledge_config = config["knowledge"]
            search_knowledge = knowledge_config["search_knowledge"]
            enable_agentic_knowledge_filters = knowledge_config["enable_agentic_knowledge_filters"]
            
            # Set business unit filter
            if config.get("knowledge_filter", {}).get("business_unit"):
                knowledge_filters["business_unit"] = config["knowledge_filter"]["business_unit"]
        
        # Create agent instance with all features
        agent = Agent(
            name=config["agent"]["name"],
            agent_id=config["agent"]["agent_id"],
            role=config["agent"].get("role"),
            instructions=config["instructions"],
            model=model,
            tools=tools if tools else None,
            storage=storage,
            session_id=session_id,
            user_id=user_id,
            debug_mode=debug_mode,
            # Knowledge base configuration
            knowledge=knowledge_base,
            search_knowledge=search_knowledge,
            enable_agentic_knowledge_filters=enable_agentic_knowledge_filters,
            knowledge_filters=knowledge_filters,
            # Memory configuration
            memory=memory,
            enable_user_memories=config.get("memory", {}).get("enable_user_memories", True),
            enable_agentic_memory=config.get("memory", {}).get("enable_agentic_memory", True),
            # Additional Agno parameters
            markdown=config.get("markdown", False),
            show_tool_calls=config.get("show_tool_calls", True),
            add_history_to_messages=config.get("memory", {}).get("add_history_to_messages", True),
            num_history_runs=config.get("memory", {}).get("num_history_runs", 5)
        )
        
        # Add version metadata (from agents factory)
        actual_version = kwargs.get("version")
        if actual_version is None and config.get("agent", {}).get("version"):
            actual_version = config["agent"]["version"]
        elif actual_version is None:
            try:
                active_version = self.component_service.get_active_version(component_id)
                actual_version = active_version.version if active_version else 1
            except:
                actual_version = 1
        
        agent.metadata = {
            "version": actual_version,
            "loaded_from": "database" if kwargs.get("version") is not None else "file",
            "agent_id": component_id
        }
        
        return agent
    
    def _create_team(self, component_id: str, config: Dict[str, Any],
                    session_id: Optional[str], debug_mode: bool,
                    user_id: Optional[str], user_name: Optional[str], 
                    phone_number: Optional[str], cpf: Optional[str],
                    **kwargs) -> Team:
        """Create versioned team with enhanced parameters."""
        
        # Import dependencies
        from ai.agents.registry import get_agent
        from core.memory.memory_manager import create_memory_manager
        from core.utils.user_context_helper import create_user_context_state
        
        # Initialize memory system
        memory = kwargs.get("memory")
        if memory is None and config.get("memory"):
            try:
                memory_manager = create_memory_manager()
                memory = memory_manager.memory
            except Exception as e:
                logger.warning(f"Memory system initialization failed: {e}")
        
        # Create user context session_state
        user_context_state = create_user_context_state(
            user_id=user_id,
            user_name=user_name,
            phone_number=phone_number,
            cpf=cpf,
            **{k: v for k, v in kwargs.items() if k.startswith('user_') or k in ['customer_name', 'customer_phone', 'customer_cpf']}
        )
        
        # Get agent names from config or use defaults
        agent_names = config.get("members", ["adquirencia", "emissao", "pagbank", "human-handoff", "finalizacao"])
        
        # Load member agents
        members = [
            get_agent(
                name, 
                session_id=session_id, 
                debug_mode=debug_mode, 
                db_url=db_url, 
                memory=memory,
                user_id=user_id,
                user_name=user_name,
                phone_number=phone_number,
                cpf=cpf
            )
            for name in agent_names
        ]
        
        # Create Team with enhanced configuration from teams factory
        return Team(
            name=config["team"]["name"],
            team_id=config["team"]["team_id"],
            mode=config["team"].get("mode", "route"),
            members=members,
            instructions=config["instructions"],
            session_id=session_id,
            user_id=user_id,
            description=config["team"].get("description"),
            model=Claude(
                id=config["model"]["id"],
                max_tokens=config["model"].get("max_tokens", 2000),
                temperature=config["model"].get("temperature", 0.7),
                thinking=config["model"].get("thinking")
            ),
            # Team-specific parameters from teams factory
            show_members_responses=config.get("show_members_responses", True),
            stream_intermediate_steps=config.get("stream_intermediate_steps", True),
            stream_member_events=config.get("stream_member_events", True),
            store_events=config.get("store_events", False),
            enable_agentic_context=config.get("enable_agentic_context", True),
            share_member_interactions=config.get("share_member_interactions", True),
            markdown=config.get("markdown", True),
            show_tool_calls=config.get("show_tool_calls", True),
            add_datetime_to_instructions=config.get("add_datetime_to_instructions", True),
            add_member_tools_to_system_message=config.get("add_member_tools_to_system_message", True),
            # User context stored in session_state
            session_state=user_context_state if user_context_state.get('user_context') else None,
            add_state_in_messages=config.get("add_state_in_messages", True),
            storage=PostgresStorage(
                table_name=config["storage"]["table_name"],
                db_url=db_url,
                mode=config["storage"].get("mode", "team"),
                auto_upgrade_schema=config["storage"].get("auto_upgrade_schema", True),
            ),
            # Memory configuration
            memory=memory,
            enable_user_memories=config.get("memory", {}).get("enable_user_memories", True),
            enable_agentic_memory=config.get("memory", {}).get("enable_agentic_memory", True),
            add_history_to_messages=config.get("memory", {}).get("add_history_to_messages", True),
            num_history_runs=config.get("memory", {}).get("num_history_runs", 5),
            debug_mode=debug_mode,
        )
    
    def _create_workflow(self, component_id: str, config: Dict[str, Any],
                        session_id: Optional[str], debug_mode: bool,
                        user_id: Optional[str], user_name: Optional[str],
                        phone_number: Optional[str], cpf: Optional[str],
                        **kwargs) -> Workflow:
        """Create versioned workflow with specialized routing."""
        
        # Import specific workflow class based on workflow_id (from workflows factory)
        if component_id == "human-handoff":
            from ai.workflows.human_handoff.workflow import HumanHandoffWorkflow
            workflow_class = HumanHandoffWorkflow
        elif component_id == "conversation-typification":
            from ai.workflows.conversation_typification.workflow import get_conversation_typification_workflow
            # Use factory function instead of direct instantiation
            return get_conversation_typification_workflow(debug_mode=debug_mode)
        else:
            raise ValueError(f"Unknown workflow type: {component_id}")
        
        # Create workflow with version-specific configuration (from workflows factory)
        workflow = workflow_class(
            workflow_id=config.get("workflow", {}).get("workflow_id", component_id),
            session_id=session_id,
            user_id=user_id,
            debug_mode=debug_mode,
            description=config.get("workflow", {}).get("description"),
            storage=PostgresStorage(
                table_name=config.get("storage", {}).get("table_name", f"{component_id}_workflows"),
                db_url=db_url,
                auto_upgrade_schema=config.get("storage", {}).get("auto_upgrade_schema", True),
            ),
            # Workflow-specific parameters from config
            **{k: v for k, v in config.items() if k not in ["workflow", "storage", "model"]}
        )
        
        logger.info(f"✅ Created workflow {component_id} version {kwargs.get('version', 'active')}")
        return workflow
    
    def _create_model(self, model_config: Dict[str, Any]) -> Claude:
        """
        Create model instance from configuration (from agents factory).
        
        Args:
            model_config: Model configuration dictionary
            
        Returns:
            Configured Claude model instance
        """
        return Claude(
            id=model_config.get("id", "claude-sonnet-4-20250514"),
            temperature=model_config.get("temperature", 0.7),
            max_tokens=model_config.get("max_tokens", 2000)
        )
    
    def _create_storage(self, config: Dict[str, Any], db_url: str) -> PostgresStorage:
        """
        Create storage instance from configuration (from agents factory).
        
        Args:
            config: Full component configuration
            db_url: Database URL
            
        Returns:
            Configured PostgresStorage instance
        """
        storage_config = config.get("storage", {})
        
        return PostgresStorage(
            table_name=storage_config.get("table_name", "component_conversations"),
            db_url=db_url,
            auto_upgrade_schema=storage_config.get("auto_upgrade_schema", True)
        )
    
    def _create_tools(self, config: Dict[str, Any]) -> list:
        """
        Create tools from configuration with MCP support (from agents factory).
        
        Args:
            config: Full component configuration
            
        Returns:
            List of configured tools (regular + MCP)
        """
        tools = []
        
        # Get configured tools
        configured_tools = config.get("tools", [])
        
        # Parse tools into regular and MCP tools
        regular_tools = []
        mcp_tool_names = []
        
        for tool in configured_tools:
            if isinstance(tool, str) and tool.startswith("mcp."):
                # MCP tool format: mcp.toolname
                mcp_tool_names.append(tool[4:])  # Remove "mcp." prefix
            else:
                regular_tools.append(tool)
        
        # Load regular tools
        for tool_name in regular_tools:
            # Native Agno knowledge integration - no custom tools needed
            # Knowledge search is handled by Agno's native capabilities
            pass
        
        # Load MCP tools
        for mcp_tool_name in mcp_tool_names:
            mcp_tool = self._create_mcp_tool(mcp_tool_name)
            if mcp_tool:
                tools.append(mcp_tool)
        
        return tools
    
    def _create_mcp_tool(self, mcp_tool_name: str) -> Optional[MCPTools]:
        """
        Create an MCP tool instance with connection pooling (from agents factory).
        
        Args:
            mcp_tool_name: Name of the MCP server/tool
            
        Returns:
            PooledMCPTools instance or None if creation fails
        """
        try:
            # Check if server exists in catalog
            if not self.mcp_catalog.has_server(mcp_tool_name):
                print(f"Warning: MCP server '{mcp_tool_name}' not found in catalog")
                return None
            
            # Create pooled MCP tools instance
            from core.mcp.pooled_tools import create_pooled_mcp_tools
            pooled_tools = create_pooled_mcp_tools(mcp_tool_name)
            
            print(f"✅ Created pooled MCP tools for '{mcp_tool_name}'")
            return pooled_tools
                
        except Exception as e:
            print(f"Error creating MCP tool '{mcp_tool_name}': {e}")
            # Fallback to direct creation for backwards compatibility
            try:
                return self._create_direct_mcp_tool(mcp_tool_name)
            except Exception as fallback_error:
                print(f"Fallback creation also failed for '{mcp_tool_name}': {fallback_error}")
                return None
    
    def _create_direct_mcp_tool(self, mcp_tool_name: str) -> Optional[MCPTools]:
        """
        Create a direct (non-pooled) MCP tool instance as fallback (from agents factory).
        
        Args:
            mcp_tool_name: Name of the MCP server/tool
            
        Returns:
            MCPTools instance or None if creation fails
        """
        try:
            # Get server configuration from catalog
            server_config = self.mcp_catalog.get_server_config(mcp_tool_name)
            if not server_config:
                print(f"Warning: MCP server '{mcp_tool_name}' not found in catalog")
                return None
            
            # Create MCPTools instance based on server type
            if server_config.is_sse_server:
                return MCPTools(
                    url=server_config.url,
                    transport="sse",
                    env=server_config.env or {}
                )
            elif server_config.is_command_server:
                # For command servers, build command with args
                command_parts = [server_config.command]
                if server_config.args:
                    command_parts.extend(server_config.args)
                
                return MCPTools(
                    command=" ".join(command_parts),
                    transport="stdio",
                    env=server_config.env or {}
                )
            else:
                print(f"Warning: Unknown server type for MCP tool '{mcp_tool_name}'")
                return None
                
        except Exception as e:
            print(f"Error creating direct MCP tool '{mcp_tool_name}': {e}")
            return None


# Enhanced UnifiedVersionFactory for agent features (from agents factory)
class EnhancedAgentVersionFactory(UnifiedVersionFactory):
    """
    Enhanced factory with agent-specific capabilities from agents factory.
    Includes fallback to file configuration, migration, and discovery.
    """
    
    def create_agent(
        self,
        agent_id: str,
        version: Optional[int] = None,
        session_id: Optional[str] = None,
        debug_mode: bool = False,
        db_url: Optional[str] = None,
        fallback_to_file: bool = True,
        memory: Optional[Any] = None,
        **kwargs
    ) -> Agent:
        """
        Create an agent with version support and file fallback (from agents factory).
        
        Args:
            agent_id: Agent identifier (e.g., 'pagbank-specialist')
            version: Specific version to load, or None for active version
            session_id: Session ID for conversation tracking
            debug_mode: Enable debug mode
            db_url: Database URL override
            fallback_to_file: Whether to fall back to file-based config if DB fails
            memory: Memory instance to use
            
        Returns:
            Configured Agent instance
            
        Raises:
            ValueError: If agent_id is invalid or version not found
        """
        # Try to load from database first
        config = self._load_config_from_db(agent_id, version)
        
        # Fallback to file-based configuration if needed
        if config is None and fallback_to_file:
            config = self._load_config_from_file(agent_id)
            if config is None:
                raise ValueError(f"Agent '{agent_id}' not found in database or file system")
        elif config is None:
            raise ValueError(f"Agent '{agent_id}' version {version} not found in database")
        
        # Use enhanced agent creation
        return self._create_agent(
            agent_id, config, session_id, debug_mode,
            kwargs.get("user_id"), kwargs.get("user_name"),
            kwargs.get("phone_number"), kwargs.get("cpf"),
            memory=memory, version=version, **kwargs
        )
    
    def _load_config_from_db(self, agent_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Load agent configuration from database (from agents factory).
        
        Args:
            agent_id: Agent identifier
            version: Specific version or None for active version
            
        Returns:
            Configuration dictionary or None if not found
        """
        try:
            version_record = self.component_service.get_version(agent_id, version) if version else self.component_service.get_active_version(agent_id)
            config = version_record.config if version_record else None
            if config:
                # Ensure the config has the expected structure
                if "agent" not in config:
                    config["agent"] = {
                        "agent_id": agent_id, 
                        "version": version,
                        "name": config.get("name", f"Agent {agent_id}"),
                        "role": config.get("role", config.get("name", f"Agent {agent_id}")),
                        "description": config.get("description", f"Agent {agent_id}")
                    }
                else:
                    # Ensure required fields in agent section
                    if "agent_id" not in config["agent"]:
                        config["agent"]["agent_id"] = agent_id
                    if "name" not in config["agent"]:
                        config["agent"]["name"] = config.get("name", f"Agent {agent_id}")
                    if "role" not in config["agent"]:
                        config["agent"]["role"] = config["agent"].get("name", f"Agent {agent_id}")
                    if "description" not in config["agent"]:
                        config["agent"]["description"] = config.get("description", f"Agent {agent_id}")
                
                # Ensure other required sections exist
                if "instructions" not in config:
                    config["instructions"] = f"You are {config['agent']['name']}. Help users with their requests."
                if "model" not in config:
                    config["model"] = {"id": "claude-sonnet-4-20250514", "temperature": 0.7, "max_tokens": 2000}
                if "storage" not in config:
                    config["storage"] = {"table_name": "agent_conversations", "auto_upgrade_schema": True}
                if "memory" not in config:
                    config["memory"] = {"add_history_to_messages": True, "num_history_runs": 5}
                    
                return config
        except Exception as e:
            print(f"⚠️ Failed to load config from database: {e}")
        
        return None
    
    def _load_config_from_file(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Load agent configuration from file (fallback from agents factory).
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Configuration dictionary or None if not found
        """
        try:
            # Convert agent_id to folder name (remove -specialist suffix if present)
            folder_name = agent_id.replace("-specialist", "")
            
            config_path = Path(__file__).parent.parent / "agents" / folder_name / "config.yaml"
            if config_path.exists():
                with open(config_path) as f:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️ Failed to load config from file: {e}")
        
        return None
    
    def migrate_file_to_database(
        self,
        agent_id: str,
        version: int,
        created_by: str = "migration",
        description: str = None
    ) -> bool:
        """
        Migrate file-based configuration to database (from agents factory).
        
        Args:
            agent_id: Agent identifier
            version: Version number to assign
            created_by: User performing migration
            description: Description for this version
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            # Load configuration from file
            config = self._load_config_from_file(agent_id)
            if not config:
                print(f"⚠️ No file configuration found for {agent_id}")
                return False
            
            # Update the version in the config
            config["agent"]["version"] = version
            
            # Create database version
            self.component_service.create_version(
                component_id=agent_id,
                component_type="agent",
                version=version,
                config=config,
                created_by=created_by,
                description=description or "Migrated from file configuration",
                is_active=True  # Make it active since it's the first version
            )
            
            print(f"✅ Successfully migrated {agent_id} to database version {version}")
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to migrate {agent_id}: {e}")
            return False
    
    def list_available_agents(self) -> Dict[str, Any]:
        """
        List all available agents from database and file system (from agents factory).
        
        Returns:
            Dictionary with agent information
        """
        agents_info = {}
        
        # Get agents from database
        db_agents = self.component_service.get_all_components("agent")
        for agent_id in db_agents:
            versions = self.component_service.list_versions(agent_id)
            active_version = self.component_service.get_active_version(agent_id)
            
            agents_info[agent_id] = {
                "source": "database",
                "versions": [v.version for v in versions],
                "active_version": active_version.version if active_version else None,
                "total_versions": len(versions)
            }
        
        # Check for file-based agents not in database
        agents_dir = Path(__file__).parent.parent / "agents"
        if agents_dir.exists():
            for agent_dir in agents_dir.iterdir():
                if agent_dir.is_dir() and agent_dir.name not in ["__pycache__", "orchestrator", "prompts", "specialists", "tools"]:
                    config_path = agent_dir / "config.yaml"
                    if config_path.exists():
                        agent_id = f"{agent_dir.name}-specialist"
                        if agent_id not in agents_info:
                            agents_info[agent_id] = {
                                "source": "file",
                                "versions": [],
                                "active_version": None,
                                "total_versions": 0,
                                "can_migrate": True
                            }
        
        return agents_info
    
    def get_version_info(self, agent_id: str, version: int = None) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific version (from agents factory).
        
        Args:
            agent_id: Agent identifier
            version: Version number, or None for active version
            
        Returns:
            Version information dictionary or None if not found
        """
        if version is not None:
            agent_version = self.component_service.get_version(agent_id, version)
        else:
            agent_version = self.component_service.get_active_version(agent_id)
        
        if not agent_version:
            return None
        
        return {
            "agent_id": agent_version.component_id,
            "version": agent_version.version,
            "created_at": agent_version.created_at.isoformat() if agent_version.created_at else None,
            "created_by": agent_version.created_by,
            "is_active": agent_version.is_active,
            "is_deprecated": agent_version.is_deprecated,
            "description": agent_version.description,
            "config": agent_version.config
        }


# Configuration defaults and YAML sync (from teams/workflows factories)
def get_component_default_config(component_id: str, component_type: str) -> Dict[str, Any]:
    """
    Get default configuration for any component type.
    Consolidated from teams and workflows factories.
    
    Args:
        component_id: Component identifier  
        component_type: "agent", "team", or "workflow"
        
    Returns:
        Default configuration dictionary
    """
    if component_type == "team":
        return get_team_default_config(component_id)
    elif component_type == "workflow":
        return get_workflow_default_config(component_id)
    else:
        return {}

def get_team_default_config(team_id: str) -> Dict[str, Any]:
    """Get default configuration for team types (from teams factory)."""
    defaults = {
        "ana": {
            "team": {
                "name": "Ana - Assistant Virtual",
                "team_id": "ana",
                "mode": "route",
                "description": "Assistente virtual especializada em roteamento inteligente"
            },
            "model": {
                "provider": "anthropic",
                "id": "claude-sonnet-4-20250514",
                "temperature": 1.0,
                "max_tokens": 2000,
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": 1024
                }
            },
            "instructions": [
                "Você é a Ana, assistente virtual especializada em roteamento inteligente.",
                "Analise a mensagem do usuário e direcione para o agente especialista mais adequado:",
                "- Para dúvidas sobre cartões, emissão ou conta PagBank: direcione para 'emissao'",
                "- Para problemas com máquinas, vendas ou recebimentos: direcione para 'adquirencia'", 
                "- Para questões específicas do PagBank ou produtos financeiros: direcione para 'pagbank'",
                "- Se o usuário estiver frustrado ou solicitar atendimento humano: direcione para 'human-handoff'",
                "- Para encerramento de conversa ou despedidas: direcione para 'finalizacao'",
                "Seja silenciosa no roteamento - deixe o especialista responder diretamente ao usuário."
            ],
            "storage": {
                "type": "postgres",
                "table_name": "ana_team",
                "mode": "team",
                "auto_upgrade_schema": True
            },
            "memory": {
                "enable_user_memories": True,
                "enable_agentic_memory": True,
                "add_history_to_messages": True,
                "num_history_runs": 5
            },
            "members": ["adquirencia", "emissao", "pagbank", "human-handoff", "finalizacao"]
        }
    }
    return defaults.get(team_id, {})

def get_workflow_default_config(workflow_id: str) -> Dict[str, Any]:
    """Get default configuration for workflow types (from workflows factory)."""
    defaults = {
        "human-handoff": {
            "workflow": {
                "workflow_id": "human-handoff",
                "name": "Human Handoff Workflow",
                "description": "Workflow simplificado para escalação humana"
            },
            "storage": {
                "type": "postgres",
                "table_name": "human-handoff-workflows",
                "auto_upgrade_schema": True
            },
            "whatsapp_enabled": True,
            "whatsapp_instance": "SofIA"
        },
        "conversation-typification": {
            "workflow": {
                "workflow_id": "conversation-typification",
                "name": "Conversation Typification Workflow",
                "description": "5-level categorization workflow"
            },
            "storage": {
                "type": "postgres",
                "table_name": "conversation-typification-workflows",
                "auto_upgrade_schema": True
            },
            "max_levels": 5,
            "confidence_threshold": 0.85,
            "fallback_to_human": True
        }
    }
    return defaults.get(workflow_id, {})

def sync_component_version_from_yaml(component_id: str, component_type: str, yaml_config: Dict[str, Any]) -> int:
    """
    Sync component configuration from YAML to database.
    Consolidated from teams and workflows factories.
    
    Args:
        component_id: Component identifier
        component_type: "team" or "workflow"
        yaml_config: Configuration from YAML file
        
    Returns:
        Version number created
    """
    db: Session = next(get_db())
    
    try:
        service = ComponentVersionService(db)
        
        # Get current version or default to 1
        current_version = service.get_active_version(component_id)
        next_version = (current_version.version + 1) if current_version else 1
        
        # Create new version
        version_record = service.create_version(
            component_id=component_id,
            component_type=component_type,
            version=next_version,
            config=yaml_config,
            created_by="yaml_sync",
            description=f"Synced from YAML file",
            is_active=True,
            sync_source="yaml"
        )
        
        logger.info(f"✅ Synced {component_type} {component_id} to version {next_version}")
        return version_record.version
        
    except Exception as e:
        logger.error(f"❌ Failed to sync {component_type} {component_id}: {str(e)}")
        raise
    finally:
        db.close()


# Convenience functions for backward compatibility
def create_versioned_agent(agent_id: str, version: Optional[int] = None, **kwargs) -> Agent:
    """Create versioned agent using enhanced factory with file fallback."""
    factory = EnhancedAgentVersionFactory()
    return factory.create_agent(agent_id, version, **kwargs)


def create_versioned_team(team_id: str, version: Optional[int] = None, **kwargs) -> Team:
    """Create versioned team using unified factory."""
    factory = UnifiedVersionFactory()
    return factory.create_versioned_component(team_id, "team", version, **kwargs)


def create_versioned_workflow(workflow_id: str, version: Optional[int] = None, **kwargs) -> Workflow:
    """Create versioned workflow using unified factory."""
    factory = UnifiedVersionFactory()
    return factory.create_versioned_component(workflow_id, "workflow", version, **kwargs)


# Factory instances for global use (compatibility with agents factory)
agent_factory = EnhancedAgentVersionFactory()


# Additional convenience functions from agents factory
def get_agent_version_info(agent_id: str, version: int = None) -> Optional[Dict[str, Any]]:
    """Get information about a specific agent version."""
    return agent_factory.get_version_info(agent_id, version)


def list_available_agents() -> Dict[str, Any]:
    """List all available agents."""
    return agent_factory.list_available_agents()


def migrate_agent_to_database(
    agent_id: str,
    version: int,
    created_by: str = "migration"
) -> bool:
    """Migrate file-based agent configuration to database."""
    return agent_factory.migrate_file_to_database(agent_id, version, created_by)


# Enhanced workflow functions from workflows factory
def get_human_handoff_workflow_versioned(
    version: Optional[int] = None,
    whatsapp_enabled: bool = True,
    whatsapp_instance: str = "SofIA",
    **kwargs
):
    """Factory function for versioned human handoff workflow."""
    workflow_id = "human-handoff"
    
    if version is None:
        # Get active version
        db: Session = next(get_db())
        try:
            service = ComponentVersionService(db)
            active_version = service.get_active_version(workflow_id)
            version = active_version.version if active_version else 1
        finally:
            db.close()
    
    return create_versioned_workflow(
        workflow_id=workflow_id,
        version=version,
        whatsapp_enabled=whatsapp_enabled,
        whatsapp_instance=whatsapp_instance,
        **kwargs
    )