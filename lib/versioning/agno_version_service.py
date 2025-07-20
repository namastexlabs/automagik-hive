"""
Component Version Service

Drop-in replacement using hive schema with psycopg3.
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
import json
import os
from pathlib import Path
import asyncio

from lib.services.component_version_service import ComponentVersionService, ComponentVersion as DBComponentVersion, VersionHistory as DBVersionHistory
from pydantic import BaseModel


class VersionInfo(BaseModel):
    """Version information model"""
    component_id: str
    component_type: str
    version: Union[int, str]
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
    """Component Version Service - drop-in replacement using hive schema."""
    
    def __init__(self, db_url: str, user_id: str = "system"):
        """Initialize with database URL"""
        self.db_url = db_url
        self.user_id = user_id
        self.component_service = ComponentVersionService()
        self.sync_results = {}
    
    def _db_to_version_info(self, db_version: DBComponentVersion) -> VersionInfo:
        """Convert database model to interface model."""
        return VersionInfo(
            component_id=db_version.component_id,
            component_type=db_version.component_type,
            version=db_version.version,
            config=db_version.config,
            created_at=db_version.created_at.isoformat(),
            created_by=db_version.created_by,
            description=db_version.description or "",
            is_active=db_version.is_active
        )
    
    def _db_to_version_history(self, db_history: DBVersionHistory) -> VersionHistory:
        """Convert database model to interface model."""
        return VersionHistory(
            component_id=db_history.component_id,
            version=db_history.to_version,
            action=db_history.action,
            timestamp=db_history.changed_at.isoformat(),
            changed_by=db_history.changed_by,
            reason=db_history.description or "",
            old_config=None,
            new_config=None
        )
    
    def create_version(
        self,
        component_id: str,
        component_type: str,
        version: int,
        config: Dict[str, Any],
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> int:
        """Create a new component version."""
        return asyncio.run(self._create_version_async(
            component_id, component_type, version, config, description, created_by
        ))
    
    async def _create_version_async(
        self,
        component_id: str,
        component_type: str,
        version: int,
        config: Dict[str, Any],
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> int:
        """Async implementation of create_version."""
        version_id = await self.component_service.create_component_version(
            component_id=component_id,
            component_type=component_type,
            version=version,
            config=config,
            description=description,
            created_by=created_by or self.user_id,
            is_active=False
        )
        
        await self.component_service.add_version_history(
            component_id=component_id,
            from_version=None,
            to_version=version,
            action="created",
            description=f"Version {version} created",
            changed_by=created_by or self.user_id
        )
        
        return version_id
    
    def get_version(self, component_id: str, version: int) -> Optional[VersionInfo]:
        """Get specific component version."""
        return asyncio.run(self._get_version_async(component_id, version))
    
    async def _get_version_async(self, component_id: str, version: int) -> Optional[VersionInfo]:
        """Async implementation of get_version."""
        db_version = await self.component_service.get_component_version(component_id, version)
        return self._db_to_version_info(db_version) if db_version else None
    
    def get_active_version(self, component_id: str) -> Optional[VersionInfo]:
        """Get active component version."""
        return asyncio.run(self._get_active_version_async(component_id))
    
    async def _get_active_version_async(self, component_id: str) -> Optional[VersionInfo]:
        """Async implementation of get_active_version."""
        db_version = await self.component_service.get_active_version(component_id)
        return self._db_to_version_info(db_version) if db_version else None
    
    def set_active_version(self, component_id: str, version: int, changed_by: Optional[str] = None) -> bool:
        """Set a version as active."""
        return asyncio.run(self._set_active_version_async(component_id, version, changed_by))
    
    async def _set_active_version_async(self, component_id: str, version: int, changed_by: Optional[str] = None) -> bool:
        """Async implementation of set_active_version."""
        return await self.component_service.set_active_version(
            component_id=component_id,
            version=version,
            changed_by=changed_by or self.user_id
        )
    
    def list_versions(self, component_id: str) -> List[VersionInfo]:
        """List all versions for a component."""
        return asyncio.run(self._list_versions_async(component_id))
    
    async def _list_versions_async(self, component_id: str) -> List[VersionInfo]:
        """Async implementation of list_versions."""
        db_versions = await self.component_service.list_component_versions(component_id)
        return [self._db_to_version_info(v) for v in db_versions]
    
    def get_version_history(self, component_id: str) -> List[VersionHistory]:
        """Get version history for a component.""" 
        return asyncio.run(self._get_version_history_async(component_id))
    
    async def _get_version_history_async(self, component_id: str) -> List[VersionHistory]:
        """Async implementation of get_version_history."""
        db_history = await self.component_service.get_version_history(component_id)
        return [self._db_to_version_history(h) for h in db_history]
    
    def sync_component_type(self, component_type: str) -> List[Dict[str, Any]]:
        """Sync components of a specific type."""
        return []
    
    def sync_on_startup(self) -> Dict[str, Any]:
        """Sync all components on startup."""
        return {
            "agents": [],
            "teams": [],
            "workflows": []
        }