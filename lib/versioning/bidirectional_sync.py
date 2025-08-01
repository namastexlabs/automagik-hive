"""
Bidirectional YAML-Database Sync Engine

This module implements the core bidirectional synchronization between YAML configuration
files and the database, providing the foundation for the clean sync architecture.
"""

import logging
from typing import Any

import yaml

from lib.versioning.agno_version_service import AgnoVersionService
from lib.versioning.dev_mode import DevMode
from lib.versioning.file_sync_tracker import FileSyncTracker

logger = logging.getLogger(__name__)


class BidirectionalSync:
    """Core bidirectional synchronization engine for YAML ↔ DATABASE."""

    def __init__(self, db_url: str):
        """
        Initialize the sync engine.

        Args:
            db_url: Database connection URL
        """
        self.version_service = AgnoVersionService(db_url)
        self.file_tracker = FileSyncTracker()

    async def sync_component(
        self, component_id: str, component_type: str
    ) -> dict[str, Any]:
        """
        Core sync logic - determines and performs YAML ↔ DATABASE synchronization.

        Args:
            component_id: The component identifier
            component_type: The component type (agent, workflow, team)

        Returns:
            Dict[str, Any]: The synchronized component configuration

        Raises:
            ValueError: If sync operation fails
        """
        logger.info(
            f"Starting bidirectional sync for {component_id} ({component_type})"
        )

        # Get current database version
        db_version = await self.version_service.get_active_version(component_id)

        # Load YAML configuration
        yaml_config = self._load_yaml_config(component_id, component_type)
        if not yaml_config:
            if db_version:
                # No YAML but DB exists - return DB config
                logger.info(f"No YAML found for {component_id}, using database version")
                return db_version.config
            raise ValueError(f"No configuration found for {component_id}")

        yaml_version = yaml_config.get(component_type, {}).get("version")
        if not isinstance(yaml_version, int):
            raise ValueError(
                f"Invalid version in YAML for {component_id}: {yaml_version}"
            )

        if not db_version:
            # No DB version exists - create from YAML (YAML → DB)
            logger.info(f"Creating new database version for {component_id} from YAML")
            await self._create_db_version(
                component_id, component_type, yaml_config, yaml_version
            )
            return yaml_config

        if self.file_tracker.yaml_newer_than_db(component_id, db_version.created_at):
            # YAML file is newer - update DB from YAML (YAML → DB)
            logger.info(f"YAML newer than DB for {component_id}, updating database")
            await self._update_db_from_yaml(
                component_id, component_type, yaml_config, yaml_version
            )
            return yaml_config

        if db_version.version > yaml_version:
            # DB has higher version number - update YAML from DB (DB → YAML)
            logger.info(f"Database newer than YAML for {component_id}, updating YAML")
            await self._update_yaml_from_db(component_id, component_type, db_version)
            return db_version.config

        # Versions are in sync
        logger.debug(f"Configurations in sync for {component_id}")
        return db_version.config

    def _load_yaml_config(
        self, component_id: str, component_type: str
    ) -> dict[str, Any] | None:
        """
        Load YAML configuration from file.

        Args:
            component_id: The component identifier
            component_type: The component type

        Returns:
            Optional[Dict[str, Any]]: YAML configuration or None if not found
        """
        try:
            yaml_path = self.file_tracker._get_yaml_path(component_id)
            with open(yaml_path) as f:
                config = yaml.safe_load(f)

            # Validate that the YAML contains the expected component type
            if component_type not in config:
                logger.warning(
                    f"Component type {component_type} not found in YAML for {component_id}"
                )
                return None

            return config
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.warning(f"Failed to load YAML config for {component_id}: {e}")
            return None

    async def _create_db_version(
        self,
        component_id: str,
        component_type: str,
        yaml_config: dict[str, Any],
        version: int,
    ) -> None:
        """
        Create new database version from YAML configuration.

        Args:
            component_id: The component identifier
            component_type: The component type
            yaml_config: The YAML configuration
            version: The version number
        """
        try:
            version_id = await self.version_service.create_version(
                component_id=component_id,
                component_type=component_type,
                version=version,
                config=yaml_config,
                description=f"Created from YAML sync for {component_id}",
            )

            # Set as active
            await self.version_service.set_active_version(
                component_id=component_id,
                version=version,
            )

            if not version_id:
                raise ValueError(
                    f"Failed to create database version for {component_id}"
                )

            logger.info(f"Created database version {version} for {component_id}")
        except Exception as e:
            logger.exception(
                f"Failed to create database version for {component_id}: {e}"
            )
            raise

    async def _update_db_from_yaml(
        self,
        component_id: str,
        component_type: str,
        yaml_config: dict[str, Any],
        version: int,
    ) -> None:
        """
        Update database from YAML configuration (YAML → DB).

        Args:
            component_id: The component identifier
            component_type: The component type
            yaml_config: The YAML configuration
            version: The version number
        """
        try:
            # Create new version
            version_id = await self.version_service.create_version(
                component_id=component_id,
                component_type=component_type,
                version=version,
                config=yaml_config,
                description=f"Updated from YAML sync for {component_id}",
            )

            # Set as active
            await self.version_service.set_active_version(
                component_id=component_id,
                version=version,
            )

            if not version_id:
                raise ValueError(
                    f"Failed to update database from YAML for {component_id}"
                )

            logger.info(
                f"Updated database version {version} for {component_id} from YAML"
            )
        except Exception as e:
            logger.exception(
                f"Failed to update database from YAML for {component_id}: {e}"
            )
            raise

    async def _update_yaml_from_db(
        self, component_id: str, component_type: str, db_version
    ) -> None:
        """
        Update YAML configuration from database (DB → YAML).

        Args:
            component_id: The component identifier
            component_type: The component type
            db_version: The database version record
        """
        try:
            yaml_path = self.file_tracker._get_yaml_path(component_id)

            # Write updated configuration to YAML file
            with open(yaml_path, "w") as f:
                yaml.dump(
                    db_version.config, f, default_flow_style=False, sort_keys=False
                )

            logger.info(
                f"Updated YAML config for {component_id} from database version {db_version.version}"
            )
        except Exception as e:
            logger.exception(
                f"Failed to update YAML from database for {component_id}: {e}"
            )
            raise

    async def write_back_to_yaml(
        self,
        component_id: str,
        component_type: str,
        config: dict[str, Any],
        version: int,
    ) -> None:
        """
        Write configuration back to YAML file (for API updates).

        Args:
            component_id: The component identifier
            component_type: The component type
            config: The configuration to write
            version: The version number
        """
        if DevMode.is_enabled():
            logger.debug(
                f"Dev mode enabled, skipping YAML write-back for {component_id}"
            )
            return

        try:
            yaml_path = self.file_tracker._get_yaml_path(component_id)

            with open(yaml_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            logger.info(
                f"Written API changes back to YAML for {component_id} version {version}"
            )
        except Exception as e:
            logger.exception(f"Failed to write back to YAML for {component_id}: {e}")
            raise
