"""
Agno-based Component Version Service

Clean implementation that uses Agno's storage abstractions exclusively.
Replaces the old ComponentVersionService with modern patterns.
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
import json
import os
from pathlib import Path

from agno.storage.postgres import PostgresStorage
from agno.agent import Agent
from agno.models.anthropic import Claude
from pydantic import BaseModel


class VersionInfo(BaseModel):
    """Version information model"""
    component_id: str
    component_type: str
    version: Union[int, str]  # Allow both int and "dev" string
    config: Dict[str, Any]
    created_at: str
    created_by: str
    description: str
    is_active: bool


class VersionHistory(BaseModel):
    """Version history model"""
    component_id: str
    version: int
    action: str
    timestamp: str
    changed_by: str
    reason: str
    old_config: Optional[Dict[str, Any]] = None
    new_config: Optional[Dict[str, Any]] = None


class AgnoVersionService:
    """
    Modern versioning service using Agno storage exclusively.
    
    Uses Agno's session system to store version data with proper
    metadata and audit trails. No custom database tables needed.
    """
    
    def __init__(self, db_url: str, user_id: str = "system"):
        """Initialize with Agno storage"""
        self.db_url = db_url
        self.user_id = user_id
        
        # Version storage - for version definitions
        self.version_storage = PostgresStorage(
            db_url=db_url,
            table_name="component_versions",
            auto_upgrade_schema=True,
            mode="agent"
        )
        
        # History storage - for audit trails
        self.history_storage = PostgresStorage(
            db_url=db_url,
            table_name="version_history",
            auto_upgrade_schema=True,
            mode="agent"
        )
        
        # Storage agents for data operations
        self.version_agent = Agent(
            model=Claude(id="claude-sonnet-4-20250514"),
            storage=self.version_storage,
            instructions="Version management agent for component versioning"
        )
        
        self.history_agent = Agent(
            model=Claude(id="claude-sonnet-4-20250514"),
            storage=self.history_storage,
            instructions="History tracking agent for version audit trails"
        )
    
    def create_version(
        self,
        component_id: str,
        component_type: str,
        version: int,
        config: Dict[str, Any],
        created_by: str = "system",
        description: str = None,
        is_active: bool = False
    ) -> VersionInfo:
        """
        Create a new component version using Agno storage.
        
        Args:
            component_id: Component identifier
            component_type: Type ('agent', 'team', 'workflow')
            version: Version number
            config: Full configuration dictionary
            created_by: Creator identifier
            description: Version description
            is_active: Whether to activate this version
            
        Returns:
            VersionInfo: Created version information
        """
        # Check if version already exists
        existing = self.get_version(component_id, version)
        if existing:
            raise ValueError(f"Version {version} already exists for {component_type} {component_id}")
        
        # Create version info
        version_info = VersionInfo(
            component_id=component_id,
            component_type=component_type,
            version=version,
            config=config,
            created_at=datetime.now().isoformat(),
            created_by=created_by,
            description=description or f"{component_type.title()} {component_id} version {version}",
            is_active=is_active
        )
        
        # Store in Agno session
        session_id = f"version-{component_id}-{version}"
        self.version_agent.session_id = session_id
        self.version_agent.session_state = version_info.model_dump()
        
        # Store additional metadata in extra_data
        from agno.storage.session.agent import AgentSession
        session = AgentSession(
            session_id=session_id,
            user_id=self.user_id,
            session_data=version_info.model_dump(),
            extra_data={
                "component_id": component_id,
                "component_type": component_type,
                "version": version,
                "is_active": is_active,
                "created_by": created_by
            }
        )
        self.version_agent.storage.upsert(session)
        
        # If setting as active, deactivate others
        if is_active:
            self._deactivate_all_versions(component_id)
            # Update this version to active
            self._update_active_status(component_id, version, True)
        
        # Log the creation
        self._log_history(
            component_id=component_id,
            version=version,
            action="created",
            changed_by=created_by,
            reason=description,
            new_config=config
        )
        
        return version_info
    
    def get_version(self, component_id: str, version: int) -> Optional[VersionInfo]:
        """Get a specific version"""
        session_id = f"version-{component_id}-{version}"
        
        try:
            session = self.version_storage.read(session_id, user_id=self.user_id)
            if session and session.session_data:
                return VersionInfo(**session.session_data)
        except Exception:
            pass
        
        return None
    
    def get_active_version(self, component_id: str) -> Optional[VersionInfo]:
        """Get the currently active version"""
        # Get all sessions and filter by component_id and active status
        sessions = self.version_storage.get_all_sessions(user_id=self.user_id)
        
        # Filter for component_id and active status
        active_sessions = [
            s for s in sessions 
            if s.extra_data 
            and s.extra_data.get("component_id") == component_id
            and s.extra_data.get("is_active")
        ]
        
        if active_sessions:
            session_data = active_sessions[0].session_data
            return VersionInfo(**session_data)
        
        return None
    
    def list_versions(self, component_id: str) -> List[VersionInfo]:
        """List all versions for a component"""
        # Get all sessions and filter by component_id
        sessions = self.version_storage.get_all_sessions(user_id=self.user_id)
        
        # Filter for component_id
        component_sessions = [
            s for s in sessions 
            if s.extra_data 
            and s.extra_data.get("component_id") == component_id
        ]
        
        versions = []
        for session in component_sessions:
            if session.session_data:
                versions.append(VersionInfo(**session.session_data))
        
        # Sort by version number descending
        return sorted(versions, key=lambda v: v.version, reverse=True)
    
    def activate_version(
        self,
        component_id: str,
        version: int,
        changed_by: str = "system",
        reason: str = None
    ) -> VersionInfo:
        """Activate a specific version"""
        version_info = self.get_version(component_id, version)
        if not version_info:
            raise ValueError(f"Version {version} not found for component {component_id}")
        
        # Deactivate all other versions
        self._deactivate_all_versions(component_id)
        
        # Activate this version
        self._update_active_status(component_id, version, True)
        
        # Update the version info
        version_info.is_active = True
        
        # Log the activation
        self._log_history(
            component_id=component_id,
            version=version,
            action="activated",
            changed_by=changed_by,
            reason=reason or f"Activated version {version}"
        )
        
        return version_info
    
    def update_config(
        self,
        component_id: str,
        version: int,
        config: Dict[str, Any],
        changed_by: str = "system",
        reason: str = None
    ) -> VersionInfo:
        """Update configuration for a version"""
        version_info = self.get_version(component_id, version)
        if not version_info:
            raise ValueError(f"Version {version} not found for component {component_id}")
        
        old_config = version_info.config
        version_info.config = config
        
        # Update session data
        session_id = f"version-{component_id}-{version}"
        from agno.storage.session.agent import AgentSession
        session = AgentSession(
            session_id=session_id,
            user_id=self.user_id,
            session_data=version_info.model_dump(),
            extra_data={
                "component_id": component_id,
                "component_type": version_info.component_type,
                "version": version,
                "is_active": version_info.is_active,
                "created_by": version_info.created_by
            }
        )
        self.version_storage.upsert(session)
        
        # Log the change
        self._log_history(
            component_id=component_id,
            version=version,
            action="config_updated",
            changed_by=changed_by,
            reason=reason or f"Updated configuration for version {version}",
            old_config=old_config,
            new_config=config
        )
        
        return version_info
    
    def get_config(self, component_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get configuration for a version or active version"""
        if version is not None:
            version_info = self.get_version(component_id, version)
        else:
            version_info = self.get_active_version(component_id)
        
        return version_info.config if version_info else None
    
    def delete_version(self, component_id: str, version: int, changed_by: str = "system") -> bool:
        """Delete a version completely"""
        version_info = self.get_version(component_id, version)
        if not version_info:
            return False
        
        if version_info.is_active:
            raise ValueError(f"Cannot delete active version {version}. Activate another version first.")
        
        # Delete from storage
        session_id = f"version-{component_id}-{version}"
        self.version_storage.delete(session_id, user_id=self.user_id)
        
        # Log the deletion
        self._log_history(
            component_id=component_id,
            version=version,
            action="deleted",
            changed_by=changed_by,
            reason=f"Deleted version {version}"
        )
        
        return True
    
    def get_history(self, component_id: str, limit: int = 50) -> List[VersionHistory]:
        """Get version history for a component"""
        sessions = self.history_storage.get_recent_sessions(
            user_id=self.user_id,
            entity_id=component_id,
            limit=limit
        )
        
        history = []
        for session in sessions:
            if session.session_data:
                history.append(VersionHistory(**session.session_data))
        
        return sorted(history, key=lambda h: h.timestamp, reverse=True)
    
    def sync_from_yaml(
        self,
        component_id: str,
        component_type: str,
        yaml_config: Dict[str, Any],
        yaml_file_path: str = None
    ) -> Tuple[VersionInfo, str]:
        """Sync component from YAML (no backward compatibility)"""
        # Extract version from YAML
        yaml_version = yaml_config.get(component_type, {}).get("version")
        if not yaml_version:
            raise ValueError(f"No version found in YAML config for {component_type} {component_id}")
        
        # Get current active version
        current_version = self.get_active_version(component_id)
        
        if not current_version:
            # No existing version - create from YAML
            new_version = self.create_version(
                component_id=component_id,
                component_type=component_type,
                version=yaml_version,
                config=yaml_config,
                created_by="yaml_sync",
                description=f"Created from YAML file {yaml_file_path or 'unknown'}",
                is_active=True
            )
            return new_version, "created"
        
        elif yaml_version != current_version.version:
            # Different version - create new and activate
            new_version = self.create_version(
                component_id=component_id,
                component_type=component_type,
                version=yaml_version,
                config=yaml_config,
                created_by="yaml_sync",
                description=f"Synced from YAML file {yaml_file_path or 'unknown'}",
                is_active=True
            )
            return new_version, "updated"
        
        else:
            # Same version - check config differences
            if yaml_config != current_version.config:
                updated_version = self.update_config(
                    component_id=component_id,
                    version=yaml_version,
                    config=yaml_config,
                    changed_by="yaml_sync",
                    reason=f"Config updated from YAML file {yaml_file_path or 'unknown'}"
                )
                return updated_version, "updated"
            else:
                return current_version, "no_change"
    
    def _deactivate_all_versions(self, component_id: str):
        """Deactivate all versions for a component"""
        # Get all sessions and filter by component_id
        sessions = self.version_storage.get_all_sessions(user_id=self.user_id)
        
        # Filter for component_id
        component_sessions = [
            s for s in sessions 
            if s.extra_data 
            and s.extra_data.get("component_id") == component_id
        ]
        
        for session in component_sessions:
            if session.extra_data and session.extra_data.get("is_active"):
                # Update extra_data to mark as inactive
                session.extra_data["is_active"] = False
                
                # Update session data if it exists
                if session.session_data:
                    session.session_data["is_active"] = False
                
                # Save updated session
                self.version_storage.upsert(session)
    
    def _update_active_status(self, component_id: str, version: int, is_active: bool):
        """Update active status for a specific version"""
        session_id = f"version-{component_id}-{version}"
        session = self.version_storage.read(session_id, user_id=self.user_id)
        
        if session:
            # Update extra_data
            if session.extra_data:
                session.extra_data["is_active"] = is_active
            
            # Update session_data
            if session.session_data:
                session.session_data["is_active"] = is_active
            
            # Save updated session
            self.version_storage.upsert(session)
    
    def _log_history(
        self,
        component_id: str,
        version: int,
        action: str,
        changed_by: str,
        reason: str = None,
        old_config: Dict[str, Any] = None,
        new_config: Dict[str, Any] = None
    ):
        """Log version history"""
        history = VersionHistory(
            component_id=component_id,
            version=version,
            action=action,
            timestamp=datetime.now().isoformat(),
            changed_by=changed_by,
            reason=reason or f"Action: {action}",
            old_config=old_config,
            new_config=new_config
        )
        
        # Store in history storage
        history_id = f"history-{component_id}-{version}-{datetime.now().timestamp()}"
        from agno.storage.session.agent import AgentSession
        history_session = AgentSession(
            session_id=history_id,
            user_id=self.user_id,
            session_data=history.model_dump(),
            extra_data={
                "component_id": component_id,
                "version": version,
                "action": action,
                "timestamp": history.timestamp
            }
        )
        self.history_storage.upsert(history_session)
    
    def get_all_components(self) -> List[str]:
        """Get all component IDs that have versions"""
        sessions = self.version_storage.get_all_sessions(user_id=self.user_id)
        component_ids = set()
        
        for session in sessions:
            if session.extra_data and "component_id" in session.extra_data:
                component_ids.add(session.extra_data["component_id"])
        
        return sorted(list(component_ids))
    
    def get_components_by_type(self, component_type: str) -> List[str]:
        """Get component IDs by type"""
        sessions = self.version_storage.get_all_sessions(
            user_id=self.user_id
        )
        # Filter by component type
        filtered_sessions = [s for s in sessions if s.extra_data and s.extra_data.get("component_type") == component_type]
        
        component_ids = set()
        for session in filtered_sessions:
            if session.extra_data and "component_id" in session.extra_data:
                component_ids.add(session.extra_data["component_id"])
        
        return sorted(list(component_ids))