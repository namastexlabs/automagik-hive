"""
Component Version Service

Clean psycopg3 implementation replacing AgnoVersionService hack.
Manages component versions in hive schema using proper database patterns.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .database_service import DatabaseService, get_db_service


@dataclass
class ComponentVersion:
    """Component version data class."""

    id: int
    component_id: str
    component_type: str
    version: int
    config: dict[str, Any]
    description: str | None
    is_active: bool
    created_at: datetime
    created_by: str


@dataclass
class VersionHistory:
    """Version history data class."""

    id: int
    component_id: str
    from_version: int | None
    to_version: int
    action: str
    description: str | None
    changed_by: str
    changed_at: datetime


class ComponentVersionService:
    """
    Clean component version service using hive schema.
    Replaces the AgnoVersionService hack with proper database operations.
    """

    def __init__(self, db_url: str | None = None):
        """Initialize with optional database URL."""
        self.db_url = db_url
        self._db_service: DatabaseService | None = None

    async def _get_db_service(self) -> DatabaseService:
        """Get database service with optional URL override. Caches instance to prevent connection pool proliferation."""
        if self._db_service is None:
            if self.db_url:
                self._db_service = DatabaseService(self.db_url)
                await self._db_service.initialize()
            else:
                self._db_service = await get_db_service()
        return self._db_service

    async def close(self):
        """Clean up database service resources."""
        if self._db_service and hasattr(self._db_service, "close"):
            await self._db_service.close()
            self._db_service = None

    async def create_component_version(
        self,
        component_id: str,
        component_type: str,
        version: int,
        config: dict[str, Any],
        description: str | None = None,
        created_by: str = "system",
        is_active: bool = False,
    ) -> int:
        """Create a new component version."""
        db = await self._get_db_service()

        query = """
        INSERT INTO hive.component_versions
        (component_id, component_type, version, config, description, created_by, is_active)
        VALUES (%(component_id)s, %(component_type)s, %(version)s, %(config)s, %(description)s, %(created_by)s, %(is_active)s)
        RETURNING id
        """

        result = await db.fetch_one(
            query,
            {
                "component_id": component_id,
                "component_type": component_type,
                "version": version,
                "config": json.dumps(config),
                "description": description,
                "created_by": created_by,
                "is_active": is_active,
            },
        )

        return result["id"]

    async def get_component_version(
        self, component_id: str, version: int
    ) -> ComponentVersion | None:
        """Get specific component version."""
        db = await self._get_db_service()

        query = """
        SELECT id, component_id, component_type, version, config, description,
               is_active, created_at, created_by
        FROM hive.component_versions
        WHERE component_id = %(component_id)s AND version = %(version)s
        """

        result = await db.fetch_one(
            query, {"component_id": component_id, "version": version}
        )

        if result:
            return ComponentVersion(
                id=result["id"],
                component_id=result["component_id"],
                component_type=result["component_type"],
                version=result["version"],
                config=json.loads(result["config"])
                if isinstance(result["config"], str)
                else result["config"],
                description=result["description"],
                is_active=result["is_active"],
                created_at=result["created_at"],
                created_by=result["created_by"],
            )
        return None

    async def get_active_version(self, component_id: str) -> ComponentVersion | None:
        """Get active component version."""
        db = await self._get_db_service()

        query = """
        SELECT id, component_id, component_type, version, config, description,
               is_active, created_at, created_by
        FROM hive.component_versions
        WHERE component_id = %(component_id)s AND is_active = true
        """

        result = await db.fetch_one(query, {"component_id": component_id})

        if result:
            return ComponentVersion(
                id=result["id"],
                component_id=result["component_id"],
                component_type=result["component_type"],
                version=result["version"],
                config=json.loads(result["config"])
                if isinstance(result["config"], str)
                else result["config"],
                description=result["description"],
                is_active=result["is_active"],
                created_at=result["created_at"],
                created_by=result["created_by"],
            )
        return None

    async def set_active_version(
        self, component_id: str, version: int, changed_by: str = "system"
    ) -> bool:
        """Set a version as active (deactivates others)."""
        db = await self._get_db_service()

        operations = [
            # Deactivate all versions for this component
            (
                "UPDATE hive.component_versions SET is_active = false WHERE component_id = %(component_id)s",
                {"component_id": component_id},
            ),
            # Activate the specified version
            (
                "UPDATE hive.component_versions SET is_active = true WHERE component_id = %(component_id)s AND version = %(version)s",
                {"component_id": component_id, "version": version},
            ),
            # Record history
            (
                """INSERT INTO hive.version_history
                   (component_id, to_version, action, description, changed_by)
                   VALUES (%(component_id)s, %(version)s, 'activated', 'Version activated', %(changed_by)s)""",
                {
                    "component_id": component_id,
                    "version": version,
                    "changed_by": changed_by,
                },
            ),
        ]

        await db.execute_transaction(operations)
        return True

    async def list_component_versions(
        self, component_id: str
    ) -> list[ComponentVersion]:
        """List all versions for a component."""
        db = await self._get_db_service()

        query = """
        SELECT id, component_id, component_type, version, config, description,
               is_active, created_at, created_by
        FROM hive.component_versions
        WHERE component_id = %(component_id)s
        ORDER BY version DESC
        """

        results = await db.fetch_all(query, {"component_id": component_id})

        return [
            ComponentVersion(
                id=row["id"],
                component_id=row["component_id"],
                component_type=row["component_type"],
                version=row["version"],
                config=json.loads(row["config"])
                if isinstance(row["config"], str)
                else row["config"],
                description=row["description"],
                is_active=row["is_active"],
                created_at=row["created_at"],
                created_by=row["created_by"],
            )
            for row in results
        ]

    async def add_version_history(
        self,
        component_id: str,
        from_version: int | None,
        to_version: int,
        action: str,
        description: str | None = None,
        changed_by: str = "system",
    ) -> int:
        """Add version history record."""
        db = await self._get_db_service()

        query = """
        INSERT INTO hive.version_history
        (component_id, from_version, to_version, action, description, changed_by)
        VALUES (%(component_id)s, %(from_version)s, %(to_version)s, %(action)s, %(description)s, %(changed_by)s)
        RETURNING id
        """

        result = await db.fetch_one(
            query,
            {
                "component_id": component_id,
                "from_version": from_version,
                "to_version": to_version,
                "action": action,
                "description": description,
                "changed_by": changed_by,
            },
        )

        return result["id"]

    async def get_version_history(self, component_id: str) -> list[VersionHistory]:
        """Get version history for a component."""
        db = await self._get_db_service()

        query = """
        SELECT id, component_id, from_version, to_version, action, description, changed_by, changed_at
        FROM hive.version_history
        WHERE component_id = %(component_id)s
        ORDER BY changed_at DESC
        """

        results = await db.fetch_all(query, {"component_id": component_id})

        return [
            VersionHistory(
                id=row["id"],
                component_id=row["component_id"],
                from_version=row["from_version"],
                to_version=row["to_version"],
                action=row["action"],
                description=row["description"],
                changed_by=row["changed_by"],
                changed_at=row["changed_at"],
            )
            for row in results
        ]

    async def get_all_components(self) -> list[str]:
        """Get all distinct component IDs."""
        db = await self._get_db_service()

        query = """
        SELECT DISTINCT component_id
        FROM hive.component_versions
        ORDER BY component_id
        """

        results = await db.fetch_all(query)
        return [row["component_id"] for row in results]

    async def get_components_by_type(self, component_type: str) -> list[str]:
        """Get all component IDs of a specific type."""
        db = await self._get_db_service()

        query = """
        SELECT DISTINCT component_id
        FROM hive.component_versions
        WHERE component_type = %(component_type)s
        ORDER BY component_id
        """

        results = await db.fetch_all(query, {"component_type": component_type})
        return [row["component_id"] for row in results]
