"""
Agent Version Factory

This module provides database-driven agent creation with version support.
Replaces file-based configuration with dynamic database loading.
"""

from typing import Optional, Dict, Any
from pathlib import Path
import yaml
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage

from db.services.agent_version_service import AgentVersionService
from db.session import get_db


class AgentVersionFactory:
    """
    Factory for creating versioned agents with database-driven configuration.
    
    This factory supports:
    - Loading specific versions from database
    - Falling back to file-based configuration
    - A/B testing with version distribution
    - Hot-swapping configurations without deployment
    """
    
    def __init__(self, db_session=None):
        """Initialize with optional database session."""
        self.db_session = db_session or next(get_db())
        self.version_service = AgentVersionService(self.db_session)
    
    def create_agent(
        self,
        agent_id: str,
        version: Optional[int] = None,
        session_id: Optional[str] = None,
        debug_mode: bool = False,
        db_url: Optional[str] = None,
        fallback_to_file: bool = True
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
        
        # Create agent instance
        agent = Agent(
            name=config["agent"]["name"],
            agent_id=config["agent"]["agent_id"],
            instructions=config["instructions"],
            model=model,
            storage=storage,
            session_id=session_id,
            debug_mode=debug_mode,
            # Additional Agno parameters
            markdown=config.get("markdown", False),
            show_tool_calls=config.get("show_tool_calls", True),
            add_history_to_messages=config.get("memory", {}).get("add_history_to_messages", True),
            num_history_runs=config.get("memory", {}).get("num_history_runs", 5)
        )
        
        # Add version metadata
        agent.metadata = {
            "version": config["agent"].get("version"),
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
            config = self.version_service.get_config(agent_id, version)
            if config:
                # Ensure the config has the expected structure
                if "agent" not in config:
                    config["agent"] = {"agent_id": agent_id, "version": version}
                elif "agent_id" not in config["agent"]:
                    config["agent"]["agent_id"] = agent_id
                    
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
                agent_id=agent_id,
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
        db_agents = self.version_service.get_all_agents()
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
    db_url: Optional[str] = None
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
        db_url=db_url
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