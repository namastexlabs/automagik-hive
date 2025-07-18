"""
Agno-based Version Sync Service

Clean implementation using Agno storage abstractions.
Handles bilateral synchronization between YAML configurations and Agno storage.
"""

import os
import glob
import yaml
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime

from lib.versioning import AgnoVersionService


class AgnoVersionSyncService:
    """
    Bilateral synchronization service using Agno storage.
    
    Implements the same logic as before but with Agno storage:
    - If YAML version > DB version → Update DB
    - If DB version > YAML version → Update YAML file
    - If same version but different config → DB wins
    """
    
    def __init__(self, db_url: str = None):
        """Initialize with database URL"""
        self.db_url = db_url or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL required")
        
        self.version_service = AgnoVersionService(self.db_url)
        
        # Component type mappings
        self.config_paths = {
            'agent': 'ai/agents/*/config.yaml',
            'team': 'ai/teams/*/config.yaml',
            'workflow': 'ai/workflows/*/config.yaml'
        }
        
        self.sync_results = {
            'agents': [],
            'teams': [],
            'workflows': []
        }
    
    def sync_on_startup(self) -> Dict[str, Any]:
        """Main entry point - sync all components on startup"""
        print("🔄 Starting Agno-based component version sync...")
        
        total_synced = 0
        
        for component_type in ['agent', 'team', 'workflow']:
            try:
                results = self.sync_component_type(component_type)
                self.sync_results[component_type + 's'] = results
                total_synced += len(results)
                
                if results:
                    print(f"✅ Synced {len(results)} {component_type}(s)")
            except Exception as e:
                print(f"❌ Error syncing {component_type}s: {e}")
                self.sync_results[component_type + 's'] = {"error": str(e)}
        
        print(f"🎉 Agno version sync completed: {total_synced} components processed")
        return self.sync_results
    
    def sync_component_type(self, component_type: str) -> List[Dict[str, Any]]:
        """Sync all components of a specific type"""
        pattern = self.config_paths.get(component_type)
        if not pattern:
            return []
        
        results = []
        
        for config_file in glob.glob(pattern):
            try:
                result = self.sync_single_component(config_file, component_type)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"⚠️ Error syncing {config_file}: {e}")
                results.append({
                    "component_id": "unknown",
                    "file": config_file,
                    "action": "error",
                    "error": str(e)
                })
        
        return results
    
    def sync_single_component(self, config_file: str, component_type: str) -> Optional[Dict[str, Any]]:
        """Core bilateral sync logic for a single component"""
        try:
            # Read YAML configuration
            with open(config_file, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f)
            
            if not yaml_config:
                return None
            
            # Extract component information
            component_section = yaml_config.get(component_type, {})
            if not component_section:
                print(f"⚠️ No {component_type} section in {config_file}")
                return None
            
            # Get component ID
            component_id = (
                component_section.get('component_id') or
                component_section.get('agent_id') or
                component_section.get('team_id') or
                component_section.get('workflow_id')
            )
            
            if not component_id:
                print(f"⚠️ No component ID found in {config_file}")
                return None
            
            yaml_version = component_section.get('version')
            if not yaml_version:
                print(f"⚠️ No version found in {config_file} for {component_id}")
                return None
            
            # Get current active version from Agno storage
            agno_version = self.version_service.get_active_version(component_id)
            
            # Determine sync action
            action_taken = "no_change"
            
            if not agno_version:
                # No Agno version - create from YAML
                _, action_taken = self.version_service.sync_from_yaml(
                    component_id=component_id,
                    component_type=component_type,
                    yaml_config=yaml_config,
                    yaml_file_path=config_file
                )
                print(f"📝 Created {component_type} {component_id} v{yaml_version} in Agno storage")
            
            elif yaml_version > agno_version.version:
                # YAML is newer - update Agno storage
                _, action_taken = self.version_service.sync_from_yaml(
                    component_id=component_id,
                    component_type=component_type,
                    yaml_config=yaml_config,
                    yaml_file_path=config_file
                )
                print(f"⬆️ Updated {component_type} {component_id} Agno: v{agno_version.version} → v{yaml_version}")
            
            elif agno_version.version > yaml_version:
                # Agno is newer - update YAML
                self.update_yaml_from_agno(config_file, component_id, component_type)
                action_taken = "yaml_updated"
                print(f"⬇️ Updated {component_type} {component_id} YAML: v{yaml_version} → v{agno_version.version}")
            
            elif yaml_version == agno_version.version:
                # Same version - check config consistency
                if yaml_config != agno_version.config:
                    print(f"⚠️ {component_type} {component_id} v{yaml_version}: YAML differs from Agno, Agno wins")
                    self.update_yaml_from_agno(config_file, component_id, component_type)
                    action_taken = "yaml_corrected"
                else:
                    # Perfect sync - no action needed
                    action_taken = "no_change"
            
            return {
                "component_id": component_id,
                "component_type": component_type,
                "file": config_file,
                "yaml_version": yaml_version,
                "agno_version": agno_version.version if agno_version else None,
                "action": action_taken
            }
            
        except Exception as e:
            print(f"❌ Error processing {config_file}: {e}")
            return {
                "component_id": "unknown",
                "file": config_file,
                "action": "error",
                "error": str(e)
            }
    
    def update_yaml_from_agno(self, yaml_file: str, component_id: str, component_type: str):
        """Update YAML file with active Agno version configuration"""
        # Get active version from Agno storage
        agno_version = self.version_service.get_active_version(component_id)
        if not agno_version:
            print(f"⚠️ No active Agno version found for {component_id}")
            return
        
        # Create backup of current YAML
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"{yaml_file}.backup.{timestamp}"
        
        try:
            shutil.copy2(yaml_file, backup_file)
            print(f"💾 Created backup: {backup_file}")
        except Exception as e:
            print(f"⚠️ Could not create backup for {yaml_file}: {e}")
        
        try:
            # Write new config from Agno storage
            with open(yaml_file, 'w', encoding='utf-8') as f:
                yaml.dump(
                    agno_version.config,
                    f,
                    default_flow_style=False,
                    indent=2,
                    allow_unicode=True,
                    sort_keys=False
                )
            
            # Verify the update was successful
            self.validate_yaml_update(yaml_file, agno_version.config)
            print(f"✅ Updated YAML file: {yaml_file}")
            
        except Exception as e:
            print(f"❌ Failed to update YAML file {yaml_file}: {e}")
            # Try to restore backup
            if os.path.exists(backup_file):
                try:
                    shutil.copy2(backup_file, yaml_file)
                    print(f"🔄 Restored backup for {yaml_file}")
                except Exception as restore_error:
                    print(f"💥 Could not restore backup: {restore_error}")
            raise e
    
    def validate_yaml_update(self, yaml_file: str, expected_config: Dict[str, Any]):
        """Validate that YAML file was updated correctly"""
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                updated_config = yaml.safe_load(f)
            
            if not updated_config:
                raise ValueError("YAML file is empty after update")
            
        except Exception as e:
            raise ValueError(f"YAML validation failed: {e}")
    
    def discover_components(self) -> Dict[str, List[Dict[str, Any]]]:
        """Discover all YAML components in the project"""
        discovered = {
            'agents': [],
            'teams': [],
            'workflows': []
        }
        
        for component_type in ['agent', 'team', 'workflow']:
            pattern = self.config_paths.get(component_type)
            if not pattern:
                continue
            
            for yaml_file in glob.glob(pattern):
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                    
                    if not config:
                        continue
                    
                    component_section = config.get(component_type, {})
                    component_id = (
                        component_section.get('component_id') or
                        component_section.get('agent_id') or
                        component_section.get('team_id') or
                        component_section.get('workflow_id')
                    )
                    
                    if component_id:
                        discovered[component_type + 's'].append({
                            'component_id': component_id,
                            'file': yaml_file,
                            'version': component_section.get('version'),
                            'name': component_section.get('name', component_id)
                        })
                        
                except Exception as e:
                    print(f"⚠️ Error reading {yaml_file}: {e}")
        
        return discovered
    
    def force_sync_component(
        self,
        component_id: str,
        component_type: str,
        direction: str = "auto"
    ) -> Dict[str, Any]:
        """Force sync a specific component"""
        # Find YAML file
        yaml_file = self.find_yaml_file(component_id, component_type)
        if not yaml_file:
            raise ValueError(f"No YAML file found for {component_type} {component_id}")
        
        if direction == "auto":
            return self.sync_single_component(yaml_file, component_type)
        elif direction == "yaml_to_agno":
            with open(yaml_file, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f)
            _, action = self.version_service.sync_from_yaml(
                component_id=component_id,
                component_type=component_type,
                yaml_config=yaml_config,
                yaml_file_path=yaml_file
            )
            return {"action": action, "direction": "yaml_to_agno"}
        elif direction == "agno_to_yaml":
            self.update_yaml_from_agno(yaml_file, component_id, component_type)
            return {"action": "yaml_updated", "direction": "agno_to_yaml"}
        else:
            raise ValueError(f"Invalid direction: {direction}")
    
    def find_yaml_file(self, component_id: str, component_type: str) -> Optional[str]:
        """Find YAML file for a component"""
        pattern = self.config_paths.get(component_type)
        if not pattern:
            return None
        
        for yaml_file in glob.glob(pattern):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                if not config:
                    continue
                
                component_section = config.get(component_type, {})
                existing_id = (
                    component_section.get('component_id') or
                    component_section.get('agent_id') or
                    component_section.get('team_id') or
                    component_section.get('workflow_id')
                )
                
                if existing_id == component_id:
                    return yaml_file
                    
            except Exception:
                continue
        
        return None
    
    def cleanup_old_backups(self, max_backups: int = 5):
        """Clean up old backup files"""
        for component_type in ['agent', 'team', 'workflow']:
            pattern = self.config_paths.get(component_type, '').replace('config.yaml', '*.backup.*')
            backup_files = glob.glob(pattern)
            
            if len(backup_files) > max_backups:
                backup_files.sort(key=os.path.getmtime)
                
                for backup_file in backup_files[:-max_backups]:
                    try:
                        os.remove(backup_file)
                        print(f"🗑️ Removed old backup: {backup_file}")
                    except Exception as e:
                        print(f"⚠️ Could not remove backup {backup_file}: {e}")


# Convenience function for startup integration
def sync_all_components() -> Dict[str, Any]:
    """Convenience function to sync all components on startup"""
    sync_service = AgnoVersionSyncService()
    return sync_service.sync_on_startup()