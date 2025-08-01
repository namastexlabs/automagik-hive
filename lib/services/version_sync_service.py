"""
Agno-based Version Sync Service

Clean implementation using Agno storage abstractions.
Handles bilateral synchronization between YAML configurations and Agno storage.
"""

import glob
import os
import shutil
from datetime import datetime
from typing import Any

import yaml

from lib.logging import logger
from lib.versioning import AgnoVersionService


class AgnoVersionSyncService:
    """
    Bilateral synchronization service using Agno storage.

    Implements the same logic as before but with Agno storage:
    - If YAML version > DB version → Update DB
    - If DB version > YAML version → Update YAML file
    - If same version but different config → DB wins
    """

    def __init__(self, db_url: str | None = None):
        """Initialize with database URL"""
        self.db_url = db_url or os.getenv("HIVE_DATABASE_URL")
        if not self.db_url:
            raise ValueError("HIVE_DATABASE_URL required")

        self.version_service = AgnoVersionService(self.db_url)

        # Component type mappings
        self.config_paths = {
            "agent": "ai/agents/*/config.yaml",
            "team": "ai/teams/*/config.yaml",
            "workflow": "ai/workflows/*/config.yaml",
        }

        self.sync_results = {"agents": [], "teams": [], "workflows": []}

    async def sync_on_startup(self) -> dict[str, Any]:
        """Main entry point - sync all components on startup"""
        logger.info("Starting Agno-based component version sync")

        total_synced = 0

        for component_type in ["agent", "team", "workflow"]:
            try:
                results = await self.sync_component_type(component_type)
                self.sync_results[component_type + "s"] = results
                total_synced += len(results)

                if results:
                    logger.debug(
                        "Synchronized components",
                        component_type=component_type,
                        count=len(results),
                    )
            except Exception as e:
                logger.error(
                    "Error syncing components",
                    component_type=component_type,
                    error=str(e),
                )
                self.sync_results[component_type + "s"] = {"error": str(e)}

        logger.info("Agno version sync completed", total_components=total_synced)
        return self.sync_results

    async def sync_component_type(self, component_type: str) -> list[dict[str, Any]]:
        """Sync all components of a specific type"""
        pattern = self.config_paths.get(component_type)
        if not pattern:
            return []

        results = []

        for config_file in glob.glob(pattern):
            try:
                result = await self.sync_single_component(config_file, component_type)
                if result:
                    results.append(result)
            except Exception as e:
                logger.warning(
                    "Error syncing config file", config_file=config_file, error=str(e)
                )
                results.append(
                    {
                        "component_id": "unknown",
                        "file": config_file,
                        "action": "error",
                        "error": str(e),
                    }
                )

        return results

    async def sync_single_component(
        self, config_file: str, component_type: str
    ) -> dict[str, Any] | None:
        """Core bilateral sync logic for a single component"""
        try:
            # Read YAML configuration
            with open(config_file, encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f)

            # Skip shared configuration files
            if "shared" in config_file.lower():
                logger.debug(
                    "Skipping shared configuration file", config_file=config_file
                )
                return None

            if not isinstance(yaml_config, dict) or not any(
                section in yaml_config for section in ["agent", "team", "workflow"]
            ):
                logger.debug(
                    "Skipping non-component configuration file", config_file=config_file
                )
                return None

            if not yaml_config:
                return None

            # Extract component information
            component_section = yaml_config.get(component_type, {})
            if not component_section:
                # Show available sections for debugging
                available_sections = list(yaml_config.keys()) if yaml_config else []
                logger.warning(
                    f"🔧 No '{component_type}' section in {config_file}. Available sections: {available_sections}"
                )
                return None

            # Get component ID
            component_id = (
                component_section.get("component_id")
                or component_section.get("agent_id")
                or component_section.get("team_id")
                or component_section.get("workflow_id")
            )

            if not component_id:
                logger.warning(
                    "No component ID found in config file", config_file=config_file
                )
                return None

            yaml_version = component_section.get("version")
            if not yaml_version:
                logger.warning(
                    "No version found in config file",
                    config_file=config_file,
                    component_id=component_id,
                )
                return None

            # Get current active version from Agno storage
            try:
                agno_version = await self.version_service.get_active_version(
                    component_id
                )
            except Exception as version_error:
                logger.error(
                    "Error getting active version",
                    component_id=component_id,
                    error=str(version_error),
                )
                agno_version = None

            # Determine sync action
            action_taken = "no_change"

            if not agno_version:
                # No Agno version - create from YAML
                _, action_taken = await self.version_service.sync_from_yaml(
                    component_id=component_id,
                    component_type=component_type,
                    yaml_config=yaml_config,
                    yaml_file_path=config_file,
                )
                logger.debug(
                    "Created component in Agno storage",
                    component_type=component_type,
                    component_id=component_id,
                    version=yaml_version,
                )

            elif yaml_version == "dev":
                # Dev versions skip sync entirely
                action_taken = "dev_skip"
                logger.debug(
                    "Skipped sync for dev version",
                    component_type=component_type,
                    component_id=component_id,
                )

            elif (
                isinstance(yaml_version, int)
                and isinstance(agno_version.version, int)
                and yaml_version > agno_version.version
            ):
                # YAML is newer - update Agno storage
                _, action_taken = await self.version_service.sync_from_yaml(
                    component_id=component_id,
                    component_type=component_type,
                    yaml_config=yaml_config,
                    yaml_file_path=config_file,
                )
                logger.info(
                    "Updated Agno version from YAML",
                    component_type=component_type,
                    component_id=component_id,
                    old_version=agno_version.version,
                    new_version=yaml_version,
                )

            elif (
                isinstance(yaml_version, int)
                and isinstance(agno_version.version, int)
                and agno_version.version > yaml_version
            ):
                # Agno is newer - update YAML
                await self.update_yaml_from_agno(
                    config_file, component_id, component_type
                )
                action_taken = "yaml_updated"
                logger.info(
                    "Updated YAML version from Agno",
                    component_type=component_type,
                    component_id=component_id,
                    old_version=yaml_version,
                    new_version=agno_version.version,
                )

            elif yaml_version == agno_version.version:
                # Same version - check config consistency
                if yaml_config != agno_version.config:
                    # CRITICAL: Changed from destructive "database wins" to fail on conflict
                    # This prevents silent corruption of YAML files
                    logger.error(
                        "CRITICAL: Version conflict detected - manual resolution required",
                        component_type=component_type,
                        component_id=component_id,
                        yaml_version=yaml_version,
                        agno_version=agno_version.version,
                        yaml_file=config_file,
                    )
                    logger.error(
                        "YAML and database configs differ but have same version - this indicates data corruption or ID collision"
                    )
                    logger.error(
                        "Please manually resolve the conflict and ensure component IDs are unique across types"
                    )

                    # Return error instead of corrupting YAML
                    return {
                        "component_id": component_id,
                        "component_type": component_type,
                        "file": config_file,
                        "yaml_version": yaml_version,
                        "agno_version": agno_version.version,
                        "action": "version_conflict_error",
                        "error": f"Version conflict: YAML and DB configs differ but have same version {yaml_version}",
                    }
                # Perfect sync - no action needed
                action_taken = "no_change"

            return {
                "component_id": component_id,
                "component_type": component_type,
                "file": config_file,
                "yaml_version": yaml_version,
                "agno_version": agno_version.version if agno_version else None,
                "action": action_taken,
            }

        except Exception as e:
            logger.error(
                "Error processing config file", config_file=config_file, error=str(e)
            )
            return {
                "component_id": "unknown",
                "file": config_file,
                "action": "error",
                "error": str(e),
            }

    async def update_yaml_from_agno(
        self, yaml_file: str, component_id: str, component_type: str
    ):
        """Update YAML file with active Agno version configuration"""
        # Get active version from Agno storage
        try:
            agno_version = await self.version_service.get_active_version(component_id)
        except Exception as version_error:
            logger.error(
                "Error getting active version",
                component_id=component_id,
                error=str(version_error),
            )
            agno_version = None
        if not agno_version:
            logger.warning("No active Agno version found", component_id=component_id)
            return

        # Create backup of current YAML
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{yaml_file}.backup.{timestamp}"

        try:
            shutil.copy2(yaml_file, backup_file)
            logger.info("Created backup file", backup_file=backup_file)
        except Exception as e:
            logger.warning("Could not create backup", yaml_file=yaml_file, error=str(e))

        try:
            # Write new config from Agno storage
            with open(yaml_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    agno_version.config,
                    f,
                    default_flow_style=False,
                    indent=2,
                    allow_unicode=True,
                    sort_keys=False,
                )

            # Verify the update was successful
            self.validate_yaml_update(yaml_file, agno_version.config)
            logger.info("Updated YAML file", yaml_file=yaml_file)

        except Exception as e:
            logger.error(
                "Failed to update YAML file", yaml_file=yaml_file, error=str(e)
            )
            # Try to restore backup
            if os.path.exists(backup_file):
                try:
                    shutil.copy2(backup_file, yaml_file)
                    logger.info("Restored backup file", yaml_file=yaml_file)
                except Exception as restore_error:
                    logger.error("Could not restore backup", error=str(restore_error))
            raise

    def validate_yaml_update(self, yaml_file: str, expected_config: dict[str, Any]):
        """Validate that YAML file was updated correctly"""
        try:
            with open(yaml_file, encoding="utf-8") as f:
                updated_config = yaml.safe_load(f)

            if not updated_config:
                raise ValueError("YAML file is empty after update")

        except Exception as e:
            raise ValueError(f"YAML validation failed: {e}")

    def discover_components(self) -> dict[str, list[dict[str, Any]]]:
        """Discover all YAML components in the project"""
        discovered = {"agents": [], "teams": [], "workflows": []}

        for component_type in ["agent", "team", "workflow"]:
            pattern = self.config_paths.get(component_type)
            if not pattern:
                continue

            for yaml_file in glob.glob(pattern):
                try:
                    with open(yaml_file, encoding="utf-8") as f:
                        config = yaml.safe_load(f)

                    if not config:
                        continue

                    component_section = config.get(component_type, {})
                    component_id = (
                        component_section.get("component_id")
                        or component_section.get("agent_id")
                        or component_section.get("team_id")
                        or component_section.get("workflow_id")
                    )

                    if component_id:
                        discovered[component_type + "s"].append(
                            {
                                "component_id": component_id,
                                "file": yaml_file,
                                "version": component_section.get("version"),
                                "name": component_section.get("name", component_id),
                            }
                        )

                except Exception as e:
                    logger.warning(
                        "Error reading YAML file", yaml_file=yaml_file, error=str(e)
                    )

        return discovered

    async def force_sync_component(
        self, component_id: str, component_type: str, direction: str = "auto"
    ) -> dict[str, Any]:
        """Force sync a specific component"""
        # Find YAML file
        yaml_file = self.find_yaml_file(component_id, component_type)
        if not yaml_file:
            raise ValueError(f"No YAML file found for {component_type} {component_id}")

        if direction == "auto":
            return await self.sync_single_component(yaml_file, component_type)
        if direction == "yaml_to_agno":
            with open(yaml_file, encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f)
            _, action = await self.version_service.sync_from_yaml(
                component_id=component_id,
                component_type=component_type,
                yaml_config=yaml_config,
                yaml_file_path=yaml_file,
            )
            return {"action": action, "direction": "yaml_to_agno"}
        if direction == "agno_to_yaml":
            await self.update_yaml_from_agno(yaml_file, component_id, component_type)
            return {"action": "yaml_updated", "direction": "agno_to_yaml"}
        raise ValueError(f"Invalid direction: {direction}")

    def find_yaml_file(self, component_id: str, component_type: str) -> str | None:
        """Find YAML file for a component"""
        pattern = self.config_paths.get(component_type)
        if not pattern:
            return None

        for yaml_file in glob.glob(pattern):
            try:
                with open(yaml_file, encoding="utf-8") as f:
                    config = yaml.safe_load(f)

                if not config:
                    continue

                component_section = config.get(component_type, {})
                existing_id = (
                    component_section.get("component_id")
                    or component_section.get("agent_id")
                    or component_section.get("team_id")
                    or component_section.get("workflow_id")
                )

                if existing_id == component_id:
                    return yaml_file

            except Exception:
                continue

        return None

    def cleanup_old_backups(self, max_backups: int = 5):
        """Clean up old backup files"""
        for component_type in ["agent", "team", "workflow"]:
            pattern = self.config_paths.get(component_type, "").replace(
                "config.yaml", "*.backup.*"
            )
            backup_files = glob.glob(pattern)

            if len(backup_files) > max_backups:
                backup_files.sort(key=os.path.getmtime)

                for backup_file in backup_files[:-max_backups]:
                    try:
                        os.remove(backup_file)
                        logger.debug("Removed old backup", backup_file=backup_file)
                    except Exception as e:
                        logger.warning(
                            "Could not remove backup",
                            backup_file=backup_file,
                            error=str(e),
                        )


# Convenience function for startup integration
async def sync_all_components() -> dict[str, Any]:
    """Convenience function to sync all components on startup"""
    sync_service = AgnoVersionSyncService()
    return await sync_service.sync_on_startup()
