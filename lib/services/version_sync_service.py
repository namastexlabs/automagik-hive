"""
Agno-based Version Sync Service

Clean implementation using Agno storage abstractions.
Handles bilateral synchronization between YAML configurations and Agno storage.
"""

import glob
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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

    def __init__(self, db_url: str | None = None, db_service=None):
        """Initialize with database URL and optional db_service for testing"""
        self.db_url = db_url or os.getenv("HIVE_DATABASE_URL")
        if not self.db_url and not db_service:
            raise ValueError("HIVE_DATABASE_URL required")

        self._db_service = db_service  # For testing injection
        self.version_service = AgnoVersionService(self.db_url) if self.db_url else None

        # Component type mappings
        self.config_paths = {
            "agent": "ai/agents/*/config.yaml",
            "team": "ai/teams/*/config.yaml",
            "workflow": "ai/workflows/*/config.yaml",
        }

        self.sync_results = {"agents": [], "teams": [], "workflows": []}

    async def _get_db_service(self):
        """Get database service - either injected for testing or create new one"""
        if self._db_service:
            return self._db_service
        
        from lib.services.database_service import DatabaseService
        return DatabaseService(self.db_url)

    async def get_yaml_component_versions(self, component_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get component versions from YAML files.
        
        Args:
            component_type: Optional filter by component type ('agent', 'team', 'workflow')
        
        Returns:
            List of component version dictionaries
        """
        versions = []
        component_types = [component_type] if component_type else ["agent", "team", "workflow"]
        
        for comp_type in component_types:
            try:
                # Get the directory path for this component type
                if comp_type == "agent":
                    base_dir = Path("ai/agents")
                elif comp_type == "team":
                    base_dir = Path("ai/teams")
                elif comp_type == "workflow":
                    base_dir = Path("ai/workflows")
                else:
                    continue
                
                if not base_dir.exists():
                    continue
                
                # Look for component directories
                for component_dir in base_dir.iterdir():
                    if not component_dir.is_dir():
                        continue
                    
                    # Look for YAML/YML config files in the component directory
                    for config_file in component_dir.iterdir():
                        if config_file.suffix not in ['.yaml', '.yml']:
                            continue
                        
                        try:
                            with open(config_file, 'r', encoding='utf-8') as f:
                                config = yaml.safe_load(f)
                            
                            if not config or not isinstance(config, dict):
                                continue
                            
                            # Extract component info - handle both nested and flat structures
                            component_section = config.get(comp_type, {})
                            
                            # If no nested section, check if the root has component data
                            if not component_section:
                                # Check if root level has name/version (test structure)
                                if 'name' in config or 'version' in config:
                                    component_section = config
                                else:
                                    continue
                            
                            # Get version, defaulting to "1.0.0" if missing
                            version = component_section.get('version', '1.0.0')
                            name = component_section.get('name', component_dir.name)
                            
                            versions.append({
                                'component_type': comp_type,
                                'name': name,
                                'version': version,
                                'file_path': str(config_file),
                                'updated_at': datetime.fromtimestamp(config_file.stat().st_mtime)
                            })
                            
                            # Only process the first valid config file per directory
                            break
                            
                        except (yaml.YAMLError, IOError, OSError) as e:
                            logger.warning(f"Error reading YAML file {config_file}: {e}")
                            continue
                        
            except Exception as e:
                logger.error(f"Error processing component type {comp_type}: {e}")
                continue
        
        return versions

    async def get_db_component_versions(self, component_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get component versions from database.
        
        Args:
            component_type: Optional filter by component type
        
        Returns:
            List of component version dictionaries from database
        """
        try:
            # Get database service (supports dependency injection for testing)
            db_service = await self._get_db_service()
            
            # Build query
            if component_type:
                query = """
                    SELECT component_type, name, version, updated_at 
                    FROM hive.component_versions 
                    WHERE component_type = %(component_type)s
                    ORDER BY component_type, name
                """
                params = {"component_type": component_type}
            else:
                query = """
                    SELECT component_type, name, version, updated_at 
                    FROM hive.component_versions 
                    ORDER BY component_type, name
                """
                params = None
            
            # Execute query
            results = await db_service.fetch_all(query, params)
            
            # Convert to list of dictionaries
            versions = []
            for row in results:
                versions.append({
                    'component_type': row['component_type'],
                    'name': row['name'],
                    'version': row['version'],
                    'updated_at': row['updated_at']
                })
            
            return versions
            
        except Exception as e:
            logger.error(f"Error fetching component versions from database: {e}")
            return []

    async def sync_component_to_db(self, component_data: Dict[str, Any]) -> None:
        """
        Sync a single component to database.
        
        Args:
            component_data: Dictionary with component_type, name, version
        """
        try:
            # Get database service (supports dependency injection for testing)
            db_service = await self._get_db_service()
            
            # Check if component already exists
            existing_query = """
                SELECT version, updated_at 
                FROM hive.component_versions 
                WHERE component_type = %(component_type)s AND name = %(name)s
            """
            existing = await db_service.fetch_one(
                existing_query,
                {
                    "component_type": component_data['component_type'],
                    "name": component_data['name']
                }
            )
            
            if existing is None:
                # Insert new component
                insert_query = """
                    INSERT INTO hive.component_versions (component_type, name, version, updated_at)
                    VALUES (%(component_type)s, %(name)s, %(version)s, NOW())
                """
                await db_service.execute(
                    insert_query,
                    {
                        "component_type": component_data['component_type'],
                        "name": component_data['name'],
                        "version": component_data['version']
                    }
                )
                logger.debug(f"Inserted new component: {component_data['component_type']}/{component_data['name']} v{component_data['version']}")
                
            elif existing['version'] != component_data['version']:
                # Update existing component with different version
                update_query = """
                    UPDATE hive.component_versions 
                    SET version = %(version)s, updated_at = NOW()
                    WHERE component_type = %(component_type)s AND name = %(name)s
                """
                await db_service.execute(
                    update_query,
                    {
                        "version": component_data['version'],
                        "component_type": component_data['component_type'],
                        "name": component_data['name']
                    }
                )
                logger.debug(f"Updated component: {component_data['component_type']}/{component_data['name']} {existing['version']} -> {component_data['version']}")
            
            # If versions match, no action needed
            
        except Exception as e:
            logger.error(f"Error syncing component to database: {e}")
            raise

    async def sync_yaml_to_db(self, component_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Sync YAML components to database.
        
        Args:
            component_type: Optional filter by component type
        
        Returns:
            Dictionary with sync results
        """
        try:
            # Get YAML components
            yaml_components = await self.get_yaml_component_versions(component_type)
            
            synced_count = 0
            component_types = []
            seen_types = set()
            
            # Sync each component
            for component in yaml_components:
                try:
                    await self.sync_component_to_db(component)
                    synced_count += 1
                    # Add to component_types list in order, avoiding duplicates
                    if component['component_type'] not in seen_types:
                        component_types.append(component['component_type'])
                        seen_types.add(component['component_type'])
                except Exception as e:
                    logger.error(f"Error syncing component {component['name']}: {e}")
            
            return {
                'synced_count': synced_count,
                'component_types': component_types,
                'total_found': len(yaml_components)
            }
            
        except Exception as e:
            logger.error(f"Error in sync_yaml_to_db: {e}")
            return {
                'synced_count': 0,
                'component_types': [],
                'total_found': 0,
                'error': str(e)
            }

    async def get_sync_status(self, component_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get synchronization status between YAML and database.
        
        Args:
            component_type: Optional filter by component type
        
        Returns:
            Dictionary with sync status information
        """
        try:
            # Get components from both sources
            yaml_components = await self.get_yaml_component_versions(component_type)
            db_components = await self.get_db_component_versions(component_type)
            
            # Create lookup dictionaries
            yaml_lookup = {
                f"{comp['component_type']}/{comp['name']}": comp 
                for comp in yaml_components
            }
            db_lookup = {
                f"{comp['component_type']}/{comp['name']}": comp 
                for comp in db_components
            }
            
            # Find matches and mismatches
            in_sync = []
            out_of_sync = []
            
            # Check YAML components against DB
            for key, yaml_comp in yaml_lookup.items():
                db_comp = db_lookup.get(key)
                if db_comp and yaml_comp['version'] == db_comp['version']:
                    in_sync.append({
                        'component_type': yaml_comp['component_type'],
                        'name': yaml_comp['name'],
                        'version': yaml_comp['version']
                    })
                else:
                    out_of_sync.append({
                        'component_type': yaml_comp['component_type'],
                        'name': yaml_comp['name'],
                        'yaml_version': yaml_comp['version'],
                        'db_version': db_comp['version'] if db_comp else None,
                        'status': 'version_mismatch' if db_comp else 'missing_in_db'
                    })
            
            # Check for DB components not in YAML
            for key, db_comp in db_lookup.items():
                if key not in yaml_lookup:
                    out_of_sync.append({
                        'component_type': db_comp['component_type'],
                        'name': db_comp['name'],
                        'yaml_version': None,
                        'db_version': db_comp['version'],
                        'status': 'missing_in_yaml'
                    })
            
            return {
                'total_yaml_components': len(yaml_components),
                'total_db_components': len(db_components),
                'in_sync_count': len(in_sync),
                'out_of_sync_count': len(out_of_sync),
                'in_sync_components': in_sync,
                'out_of_sync_components': out_of_sync,
                'sync_percentage': (len(in_sync) / max(len(yaml_components), 1)) * 100
            }
            
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {
                'total_yaml_components': 0,
                'total_db_components': 0,
                'in_sync_count': 0,
                'out_of_sync_count': 0,
                'in_sync_components': [],
                'out_of_sync_components': [],
                'sync_percentage': 0,
                'error': str(e)
            }

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
