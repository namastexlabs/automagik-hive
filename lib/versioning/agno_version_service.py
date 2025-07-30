"""
Component Version Service

Drop-in replacement using hive schema with psycopg3.
"""

from typing import Any

from pydantic import BaseModel

from lib.services.component_version_service import (
    ComponentVersion as DBComponentVersion,
)
from lib.services.component_version_service import (
    ComponentVersionService,
)
from lib.services.component_version_service import (
    VersionHistory as DBVersionHistory,
)


class VersionInfo(BaseModel):
    """Version information model"""

    component_id: str
    component_type: str
    version: int | str
    config: dict[str, Any]
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
    old_config: dict[str, Any] | None = None
    new_config: dict[str, Any] | None = None


class AgnoVersionService:
    """Component Version Service - drop-in replacement using hive schema."""

    def __init__(self, db_url: str, user_id: str = "system"):
        """Initialize with database URL"""
        self.db_url = db_url
        self.user_id = user_id
        self.component_service = ComponentVersionService(db_url)
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
            is_active=db_version.is_active,
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
            new_config=None,
        )

    async def create_version(
        self,
        component_id: str,
        component_type: str,
        version: int,
        config: dict[str, Any],
        description: str | None = None,
        created_by: str | None = None,
    ) -> int:
        """Create a new component version."""
        return await self._create_version_async(
            component_id, component_type, version, config, description, created_by
        )

    async def _create_version_async(
        self,
        component_id: str,
        component_type: str,
        version: int,
        config: dict[str, Any],
        description: str | None = None,
        created_by: str | None = None,
    ) -> int:
        """Async implementation of create_version."""
        version_id = await self.component_service.create_component_version(
            component_id=component_id,
            component_type=component_type,
            version=version,
            config=config,
            description=description,
            created_by=created_by or self.user_id,
            is_active=False,
        )

        await self.component_service.add_version_history(
            component_id=component_id,
            from_version=None,
            to_version=version,
            action="created",
            description=f"Version {version} created",
            changed_by=created_by or self.user_id,
        )

        return version_id

    async def get_version(self, component_id: str, version: int) -> VersionInfo | None:
        """Get specific component version."""
        return await self._get_version_async(component_id, version)

    async def _get_version_async(
        self, component_id: str, version: int
    ) -> VersionInfo | None:
        """Async implementation of get_version."""
        db_version = await self.component_service.get_component_version(
            component_id, version
        )
        return self._db_to_version_info(db_version) if db_version else None

    async def get_active_version(self, component_id: str) -> VersionInfo | None:
        """Get active component version."""
        return await self._get_active_version_async(component_id)

    async def _get_active_version_async(self, component_id: str) -> VersionInfo | None:
        """Async implementation of get_active_version."""
        db_version = await self.component_service.get_active_version(component_id)
        return self._db_to_version_info(db_version) if db_version else None

    async def set_active_version(
        self, component_id: str, version: int, changed_by: str | None = None
    ) -> bool:
        """Set a version as active."""
        return await self._set_active_version_async(component_id, version, changed_by)

    async def _set_active_version_async(
        self, component_id: str, version: int, changed_by: str | None = None
    ) -> bool:
        """Async implementation of set_active_version."""
        return await self.component_service.set_active_version(
            component_id=component_id,
            version=version,
            changed_by=changed_by or self.user_id,
        )

    async def list_versions(self, component_id: str) -> list[VersionInfo]:
        """List all versions for a component."""
        return await self._list_versions_async(component_id)

    async def _list_versions_async(self, component_id: str) -> list[VersionInfo]:
        """Async implementation of list_versions."""
        db_versions = await self.component_service.list_component_versions(component_id)
        return [self._db_to_version_info(v) for v in db_versions]

    async def get_version_history(self, component_id: str) -> list[VersionHistory]:
        """Get version history for a component."""
        return await self._get_version_history_async(component_id)

    async def _get_version_history_async(
        self, component_id: str
    ) -> list[VersionHistory]:
        """Async implementation of get_version_history."""
        db_history = await self.component_service.get_version_history(component_id)
        return [self._db_to_version_history(h) for h in db_history]

    async def get_all_components(self) -> list[str]:
        """Get all distinct component IDs."""
        return await self.component_service.get_all_components()

    async def get_components_by_type(self, component_type: str) -> list[str]:
        """Get all distinct component IDs of a specific type."""
        return await self.component_service.get_components_by_type(component_type)

    def sync_component_type(self, component_type: str) -> list[dict[str, Any]]:
        """Sync components of a specific type."""
        # TODO: Implement component type synchronization
        _ = component_type  # Explicitly mark as unused for now
        return []

    def sync_on_startup(self) -> dict[str, Any]:
        """Sync all components on startup."""
        return {"agents": [], "teams": [], "workflows": []}

    async def sync_from_yaml(
        self,
        component_id: str,
        component_type: str,
        yaml_config: dict[str, Any],
        yaml_file_path: str,
    ) -> tuple[VersionInfo | None, str]:
        """Sync component from YAML configuration."""
        try:
            # Extract component section based on type
            component_section = yaml_config.get(component_type, {})
            if not component_section:
                return None, "no_component_section"

            version = component_section.get("version")
            if not version:
                return None, "no_version_specified"

            if not isinstance(version, int):
                return None, "invalid_version"

            # Check if version already exists
            existing = await self.get_version(component_id, version)
            if existing:
                return existing, "version_exists"

            # Create new version
            await self.create_version(
                component_id=component_id,
                component_type=component_type,
                version=version,
                config=yaml_config,
                description=f"Synced from {yaml_file_path}",
                created_by=self.user_id,
            )

            # Set as active
            await self.set_active_version(component_id, version, self.user_id)

            # Return the created version
            created_version = await self.get_version(component_id, version)
            return created_version, "created_and_activated"

        except Exception as e:
            return None, f"error: {e!s}"
