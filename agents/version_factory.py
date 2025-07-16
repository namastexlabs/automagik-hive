"""
Agent Version Factory

This module provides database-driven agent creation with version support.
Replaces file-based configuration with dynamic database loading.
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import yaml
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.tools import Function
from agno.tools.mcp import MCPTools

from db.services.component_version_service import ComponentVersionService
from db.session import get_db
from core.config.yaml_parser import YAMLConfigParser
from core.mcp.catalog import MCPCatalog
# Native Agno knowledge integration - no custom tools needed


class AgentVersionFactory:
    """
    Factory for creating versioned agents with database-driven configuration.
    
    This factory supports:
    - Loading specific versions from database
    - Falling back to file-based configuration
    - A/B testing with version distribution
    - Hot-swapping configurations without deployment
    - Dynamic tool loading from configuration
    """
    
    def __init__(self, db_session=None):
        """Initialize with optional database session."""
        self.db_session = db_session or next(get_db())
        self.version_service = ComponentVersionService(self.db_session)
        # MCP integration
        self.mcp_catalog = MCPCatalog()
        self.yaml_parser = YAMLConfigParser(self.mcp_catalog)
    
    def create_agent(
        self,
        agent_id: str,
        version: Optional[int] = None,
        session_id: Optional[str] = None,
        debug_mode: bool = False,
        db_url: Optional[str] = None,
        fallback_to_file: bool = True,
        memory: Optional[Any] = None
    ) -> Agent:
        """
        Create an agent with version support.
        
        Args:
            agent_id: Agent identifier (e.g., 'pagbank-specialist')
            version: Specific version to load, or None for active version
            session_id: Session ID for conversation tracking
            debug_mode: Enable debug mode
            db_url: Database URL override
            fallback_to_file: Whether to fall back to file-based config if DB fails
            
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
        
        # Create model instance
        model = self._create_model(config.get("model", {}))
        
        # Get database URL
        if db_url is None:
            from db.session import db_url as default_db_url
            db_url = default_db_url
        
        # Create storage instance
        storage = self._create_storage(config, db_url)
        
        # Create tools from configuration
        tools = self._create_tools(config)
        
        # Create knowledge base if configured
        knowledge_base = None
        search_knowledge = False
        enable_agentic_knowledge_filters = False
        knowledge_filters = {}
        
        if config.get("knowledge", {}).get("search_knowledge"):
            # Import knowledge base factory
            from context.knowledge.pagbank_knowledge_factory import get_knowledge_base
            knowledge_base = get_knowledge_base(db_url)
            
            # Get knowledge configuration
            knowledge_config = config["knowledge"]
            search_knowledge = knowledge_config["search_knowledge"]
            enable_agentic_knowledge_filters = knowledge_config["enable_agentic_knowledge_filters"]
            
            # Set business unit filter
            if config.get("knowledge_filter", {}).get("business_unit"):
                knowledge_filters["business_unit"] = config["knowledge_filter"]["business_unit"]
        
        # Create agent instance
        agent = Agent(
            name=config["agent"]["name"],
            agent_id=config["agent"]["agent_id"],
            instructions=config["instructions"],
            model=model,
            tools=tools if tools else None,
            storage=storage,
            session_id=session_id,
            debug_mode=debug_mode,
            # Knowledge base configuration
            knowledge=knowledge_base,
            search_knowledge=search_knowledge,
            enable_agentic_knowledge_filters=enable_agentic_knowledge_filters,
            knowledge_filters=knowledge_filters,
            # Memory configuration - FIX: Add memory parameters to prevent warnings
            memory=memory,                   # CRITICAL: Pass memory with database
            enable_user_memories=config.get("memory", {}).get("enable_user_memories", True),
            enable_agentic_memory=config.get("memory", {}).get("enable_agentic_memory", True),
            # Additional Agno parameters
            markdown=config.get("markdown", False),
            show_tool_calls=config.get("show_tool_calls", True),
            add_history_to_messages=config.get("memory", {}).get("add_history_to_messages", True),
            num_history_runs=config.get("memory", {}).get("num_history_runs", 5)
        )
        
        # Get the actual version from database or config
        actual_version = version
        if actual_version is None and config.get("agent", {}).get("version"):
            actual_version = config["agent"]["version"]
        elif actual_version is None:
            # Try to get active version from database
            try:
                active_version = self.version_service.get_active_version(agent_id)
                actual_version = active_version.version if active_version else 1
            except:
                actual_version = 1
        
        # Add version metadata
        agent.metadata = {
            "version": actual_version,
            "loaded_from": "database" if version is not None else "file",
            "agent_id": agent_id
        }
        
        return agent
    
    def _load_config_from_db(self, agent_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Load agent configuration from database.
        
        Args:
            agent_id: Agent identifier
            version: Specific version or None for active version
            
        Returns:
            Configuration dictionary or None if not found
        """
        try:
            version_record = self.version_service.get_version(agent_id, version) if version else self.version_service.get_active_version(agent_id)
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
        Load agent configuration from file (fallback).
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Configuration dictionary or None if not found
        """
        try:
            # Convert agent_id to folder name (remove -specialist suffix if present)
            folder_name = agent_id.replace("-specialist", "")
            
            config_path = Path(__file__).parent / folder_name / "config.yaml"
            if config_path.exists():
                with open(config_path) as f:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️ Failed to load config from file: {e}")
        
        return None
    
    def _create_model(self, model_config: Dict[str, Any]) -> Claude:
        """
        Create model instance from configuration.
        
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
        Create storage instance from configuration.
        
        Args:
            config: Full agent configuration
            db_url: Database URL
            
        Returns:
            Configured PostgresStorage instance
        """
        storage_config = config.get("storage", {})
        
        return PostgresStorage(
            table_name=storage_config.get("table_name", "agent_conversations"),
            db_url=db_url,
            auto_upgrade_schema=storage_config.get("auto_upgrade_schema", True)
        )
    
    def _create_tools(self, config: Dict[str, Any]) -> list:
        """
        Create tools from configuration with MCP support.
        
        Args:
            config: Full agent configuration
            
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
        Create an MCP tool instance.
        
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
            print(f"Error creating MCP tool '{mcp_tool_name}': {e}")
            return None
    
    # Native Agno knowledge integration - no custom knowledge search tools needed
    
    def migrate_file_to_database(
        self,
        agent_id: str,
        version: int,
        created_by: str = "migration",
        description: str = None
    ) -> bool:
        """
        Migrate file-based configuration to database.
        
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
            self.version_service.create_version(
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
        List all available agents from database and file system.
        
        Returns:
            Dictionary with agent information
        """
        agents_info = {}
        
        # Get agents from database
        db_agents = self.version_service.get_all_components("agent")
        for agent_id in db_agents:
            versions = self.version_service.list_versions(agent_id)
            active_version = self.version_service.get_active_version(agent_id)
            
            agents_info[agent_id] = {
                "source": "database",
                "versions": [v.version for v in versions],
                "active_version": active_version.version if active_version else None,
                "total_versions": len(versions)
            }
        
        # Check for file-based agents not in database
        agents_dir = Path(__file__).parent
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
        Get detailed information about a specific version.
        
        Args:
            agent_id: Agent identifier
            version: Version number, or None for active version
            
        Returns:
            Version information dictionary or None if not found
        """
        if version is not None:
            agent_version = self.version_service.get_version(agent_id, version)
        else:
            agent_version = self.version_service.get_active_version(agent_id)
        
        if not agent_version:
            return None
        
        return {
            "agent_id": agent_version.agent_id,
            "version": agent_version.version,
            "created_at": agent_version.created_at.isoformat() if agent_version.created_at else None,
            "created_by": agent_version.created_by,
            "is_active": agent_version.is_active,
            "is_deprecated": agent_version.is_deprecated,
            "description": agent_version.description,
            "config": agent_version.config
        }


# Factory instance for global use
agent_factory = AgentVersionFactory()


def create_versioned_agent(
    agent_id: str,
    version: Optional[int] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    db_url: Optional[str] = None,
    memory: Optional[Any] = None,
    # User context parameters (accepted but not used in current implementation)
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    cpf: Optional[str] = None,
    **kwargs
) -> Agent:
    """
    Convenience function for creating versioned agents.
    
    Args:
        agent_id: Agent identifier
        version: Specific version to load
        session_id: Session ID for conversation tracking
        debug_mode: Enable debug mode
        db_url: Database URL override
        
    Returns:
        Configured Agent instance
    """
    return agent_factory.create_agent(
        agent_id=agent_id,
        version=version,
        session_id=session_id,
        debug_mode=debug_mode,
        db_url=db_url,
        memory=memory
    )


def get_agent_version_info(agent_id: str, version: int = None) -> Optional[Dict[str, Any]]:
    """
    Get information about a specific agent version.
    
    Args:
        agent_id: Agent identifier
        version: Version number, or None for active version
        
    Returns:
        Version information dictionary
    """
    return agent_factory.get_version_info(agent_id, version)


def list_available_agents() -> Dict[str, Any]:
    """
    List all available agents.
    
    Returns:
        Dictionary with agent information
    """
    return agent_factory.list_available_agents()


def migrate_agent_to_database(
    agent_id: str,
    version: int,
    created_by: str = "migration"
) -> bool:
    """
    Migrate file-based agent configuration to database.
    
    Args:
        agent_id: Agent identifier
        version: Version number to assign
        created_by: User performing migration
        
    Returns:
        True if migration successful
    """
    return agent_factory.migrate_file_to_database(agent_id, version, created_by)