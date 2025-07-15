"""
Component Version Service

Unified service for managing versions of agents, teams, and workflows.
Supports bilateral sync between YAML configurations and database storage.
"""

from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime
import json
import yaml
import os
from pathlib import Path

from ..tables.component_versions import ComponentVersion, ComponentVersionHistory
from ..session import get_db


class ComponentVersionService:
    """
    Unified service for managing component versions across agents, teams, and workflows.
    
    Provides methods for creating, retrieving, updating, and managing
    component versions with full audit trail and bilateral sync support.
    """
    
    def __init__(self, db: Session = None):
        """Initialize with optional database session."""
        self.db = db or next(get_db())
    
    def create_version(
        self,
        component_id: str,
        component_type: str,
        version: int,
        config: Dict[str, Any],
        created_by: str = "system",
        description: str = None,
        is_active: bool = False,
        sync_source: str = "api"
    ) -> ComponentVersion:
        """
        Create a new component version.
        
        Args:
            component_id: Component identifier (e.g., 'pagbank-specialist', 'ana-team')
            component_type: Type of component ('agent', 'team', 'workflow')
            version: Version number
            config: Full component configuration dictionary
            created_by: User/system who created this version
            description: Description of changes
            is_active: Whether to make this version active immediately
            sync_source: Source of creation ('yaml', 'db', 'api')
            
        Returns:
            Created ComponentVersion instance
            
        Raises:
            ValueError: If version already exists
        """
        # Check if version already exists
        existing = self.get_version(component_id, version)
        if existing:
            raise ValueError(f"Version {version} already exists for {component_type} {component_id}")
        
        # If setting as active, deactivate others
        if is_active:
            self._deactivate_all_versions(component_id)
        
        # Create new version
        new_version = ComponentVersion(
            component_id=component_id,
            component_type=component_type,
            version=version,
            config=config,
            created_by=created_by,
            description=description or f"{component_type.title()} {component_id} version {version}",
            is_active=is_active
        )
        
        self.db.add(new_version)
        self.db.commit()
        self.db.refresh(new_version)
        
        # Log the creation
        self._log_version_change(
            component_id=component_id,
            component_type=component_type,
            version=version,
            action="created",
            new_state={"is_active": is_active, "config": config},
            changed_by=created_by,
            reason=description,
            sync_source=sync_source
        )
        
        return new_version
    
    def get_version(self, component_id: str, version: int) -> Optional[ComponentVersion]:
        """Get a specific component version."""
        return self.db.query(ComponentVersion).filter(
            and_(
                ComponentVersion.component_id == component_id,
                ComponentVersion.version == version
            )
        ).first()
    
    def get_latest_version(self, component_id: str) -> Optional[ComponentVersion]:
        """Get the latest version for a component."""
        return self.db.query(ComponentVersion).filter(
            ComponentVersion.component_id == component_id
        ).order_by(desc(ComponentVersion.version)).first()
    
    def get_active_version(self, component_id: str) -> Optional[ComponentVersion]:
        """Get the currently active version for a component."""
        return self.db.query(ComponentVersion).filter(
            and_(
                ComponentVersion.component_id == component_id,
                ComponentVersion.is_active == True
            )
        ).first()
    
    def list_versions(
        self, 
        component_id: str, 
        include_deprecated: bool = False
    ) -> List[ComponentVersion]:
        """List all versions for a component."""
        query = self.db.query(ComponentVersion).filter(
            ComponentVersion.component_id == component_id
        )
        
        if not include_deprecated:
            query = query.filter(ComponentVersion.is_deprecated == False)
        
        return query.order_by(desc(ComponentVersion.version)).all()
    
    def activate_version(
        self, 
        component_id: str, 
        version: int, 
        changed_by: str = "system",
        reason: str = None,
        sync_source: str = "api"
    ) -> ComponentVersion:
        """Activate a specific version (deactivates all others)."""
        # Get the version to activate
        version_to_activate = self.get_version(component_id, version)
        if not version_to_activate:
            raise ValueError(f"Version {version} not found for component {component_id}")
        
        # Deactivate all other versions
        self._deactivate_all_versions(component_id)
        
        # Activate the specified version
        version_to_activate.is_active = True
        
        self.db.commit()
        self.db.refresh(version_to_activate)
        
        # Log the activation
        self._log_version_change(
            component_id=component_id,
            component_type=version_to_activate.component_type,
            version=version,
            action="activated",
            new_state={"is_active": True},
            changed_by=changed_by,
            reason=reason or f"Activated version {version}",
            sync_source=sync_source
        )
        
        return version_to_activate
    
    def deprecate_version(
        self, 
        component_id: str, 
        version: int,
        changed_by: str = "system",
        reason: str = None
    ) -> ComponentVersion:
        """Mark a version as deprecated."""
        version_to_deprecate = self.get_version(component_id, version)
        if not version_to_deprecate:
            raise ValueError(f"Version {version} not found for component {component_id}")
        
        if version_to_deprecate.is_active:
            raise ValueError(f"Cannot deprecate active version {version}. Activate another version first.")
        
        version_to_deprecate.is_deprecated = True
        
        self.db.commit()
        self.db.refresh(version_to_deprecate)
        
        # Log the deprecation
        self._log_version_change(
            component_id=component_id,
            component_type=version_to_deprecate.component_type,
            version=version,
            action="deprecated",
            new_state={"is_deprecated": True},
            changed_by=changed_by,
            reason=reason or f"Deprecated version {version}"
        )
        
        return version_to_deprecate
    
    def update_config(
        self,
        component_id: str,
        version: int,
        config: Dict[str, Any],
        changed_by: str = "system",
        reason: str = None,
        sync_source: str = "api"
    ) -> ComponentVersion:
        """Update configuration for a specific version."""
        version_to_update = self.get_version(component_id, version)
        if not version_to_update:
            raise ValueError(f"Version {version} not found for component {component_id}")
        
        old_config = version_to_update.config
        version_to_update.config = config
        
        self.db.commit()
        self.db.refresh(version_to_update)
        
        # Log the configuration change
        self._log_version_change(
            component_id=component_id,
            component_type=version_to_update.component_type,
            version=version,
            action="config_updated",
            previous_state={"config": old_config},
            new_state={"config": config},
            changed_by=changed_by,
            reason=reason or f"Updated configuration for version {version}",
            sync_source=sync_source
        )
        
        return version_to_update
    
    def get_config(self, component_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific version or the active version."""
        if version is not None:
            component_version = self.get_version(component_id, version)
        else:
            component_version = self.get_active_version(component_id)
        
        return component_version.config if component_version else None
    
    def delete_version(self, component_id: str, version: int) -> bool:
        """Delete a specific version (soft delete via deprecation)."""
        version_to_delete = self.get_version(component_id, version)
        if not version_to_delete:
            return False
        
        if version_to_delete.is_active:
            raise ValueError(f"Cannot delete active version {version}. Activate another version first.")
        
        # Soft delete by marking as deprecated
        version_to_delete.is_deprecated = True
        self.db.commit()
        
        return True
    
    def sync_from_yaml(
        self, 
        component_id: str, 
        component_type: str, 
        yaml_config: Dict[str, Any],
        yaml_file_path: str = None
    ) -> Tuple[ComponentVersion, str]:
        """
        Sync component from YAML configuration to database.
        
        Returns:
            Tuple of (ComponentVersion, action_taken)
            action_taken can be: 'created', 'updated', 'no_change'
        """
        # Extract version from YAML config
        yaml_version = yaml_config.get(component_type, {}).get("version")
        if not yaml_version:
            raise ValueError(f"No version found in YAML config for {component_type} {component_id}")
        
        # Check current DB version
        db_version = self.get_active_version(component_id)
        
        if not db_version:
            # No DB version - create from YAML
            new_version = self.create_version(
                component_id=component_id,
                component_type=component_type,
                version=yaml_version,
                config=yaml_config,
                created_by="yaml_sync",
                description=f"Created from YAML file {yaml_file_path or 'unknown'}",
                is_active=True,
                sync_source="yaml"
            )
            return new_version, "created"
        
        elif yaml_version > db_version.version:
            # YAML is newer - create new version and activate
            new_version = self.create_version(
                component_id=component_id,
                component_type=component_type,
                version=yaml_version,
                config=yaml_config,
                created_by="yaml_sync",
                description=f"Updated from YAML file {yaml_file_path or 'unknown'}",
                is_active=True,
                sync_source="yaml"
            )
            return new_version, "updated"
        
        elif yaml_version == db_version.version:
            # Same version - check if config is different
            if yaml_config != db_version.config:
                # Update existing version with YAML config
                updated_version = self.update_config(
                    component_id=component_id,
                    version=yaml_version,
                    config=yaml_config,
                    changed_by="yaml_sync",
                    reason=f"Config updated from YAML file {yaml_file_path or 'unknown'}",
                    sync_source="yaml"
                )
                return updated_version, "updated"
            else:
                return db_version, "no_change"
        
        else:
            # DB is newer - no action needed (will be handled by sync_to_yaml)
            return db_version, "no_change"
    
    def get_yaml_file_path(self, component_id: str, component_type: str) -> Optional[str]:
        """Get the YAML file path for a component."""
        base_paths = {
            "agent": "agents",
            "team": "teams", 
            "workflow": "workflows"
        }
        
        base_path = base_paths.get(component_type)
        if not base_path:
            return None
        
        # Convert component_id to directory name
        # 'pagbank-specialist' -> 'pagbank', 'ana-team' -> 'ana'
        dir_name = component_id.split('-')[0]
        
        yaml_path = f"{base_path}/{dir_name}/config.yaml"
        if os.path.exists(yaml_path):
            return yaml_path
        
        return None
    
    def _deactivate_all_versions(self, component_id: str):
        """Deactivate all versions for a component."""
        self.db.query(ComponentVersion).filter(
            ComponentVersion.component_id == component_id
        ).update({"is_active": False})
    
    def _log_version_change(
        self,
        component_id: str,
        component_type: str,
        version: int,
        action: str,
        previous_state: Dict[str, Any] = None,
        new_state: Dict[str, Any] = None,
        changed_by: str = "system",
        reason: str = None,
        sync_source: str = "api"
    ) -> ComponentVersionHistory:
        """Log a version change to the history table."""
        history = ComponentVersionHistory(
            component_id=component_id,
            component_type=component_type,
            version=version,
            action=action,
            previous_state=previous_state,
            new_state=new_state,
            changed_by=changed_by,
            reason=reason,
            sync_source=sync_source
        )
        
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        
        return history
    
    def get_all_components(self) -> List[str]:
        """Get list of all component IDs that have versions."""
        result = self.db.query(ComponentVersion.component_id).distinct().all()
        return [row[0] for row in result]
    
    def get_components_by_type(self, component_type: str) -> List[str]:
        """Get list of component IDs by type."""
        result = self.db.query(ComponentVersion.component_id).filter(
            ComponentVersion.component_type == component_type
        ).distinct().all()
        return [row[0] for row in result]