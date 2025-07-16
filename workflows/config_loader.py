"""
Workflow Configuration Loader
============================

Utility module for loading YAML configurations for workflows.
Provides centralized configuration management following the project's YAML-first architecture.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from agno.utils.log import logger


class WorkflowConfigLoader:
    """
    Centralized loader for workflow YAML configurations.
    
    Supports:
    - Loading from config.yaml files in workflow directories
    - Environment variable substitution
    - Default value fallbacks
    - Model configuration extraction
    """
    
    def __init__(self, workflows_root: Optional[Path] = None):
        """
        Initialize configuration loader.
        
        Args:
            workflows_root: Root directory for workflows (defaults to this file's parent)
        """
        if workflows_root is None:
            workflows_root = Path(__file__).parent
        self.workflows_root = workflows_root
    
    def load_workflow_config(self, workflow_id: str) -> Dict[str, Any]:
        """
        Load configuration for a specific workflow.
        
        Args:
            workflow_id: Workflow identifier (e.g., 'conversation-typification')
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config.yaml not found
            ValueError: If configuration is invalid
        """
        # Convert workflow_id to directory name (replace dashes with underscores for consistency)
        workflow_dir = workflow_id.replace('-', '_')
        config_path = self.workflows_root / workflow_dir / "config.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Substitute environment variables
            config = self._substitute_env_vars(config)
            
            logger.info(f"Loaded configuration for workflow: {workflow_id}")
            return config
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration in {config_path}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load configuration from {config_path}: {e}")
    
    def get_model_config(self, workflow_id: str, agent_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract model configuration from workflow config.
        
        Args:
            workflow_id: Workflow identifier
            agent_key: Specific agent key for multi-agent workflows (optional)
            
        Returns:
            Model configuration dictionary with provider, id, temperature, etc.
        """
        config = self.load_workflow_config(workflow_id)
        
        # Check for agent-specific model config first
        if agent_key and 'agents' in config and agent_key in config['agents']:
            agent_config = config['agents'][agent_key]
            if 'model' in agent_config:
                return agent_config['model']
        
        # Fall back to workflow-level model config
        if 'model' in config:
            return config['model']
        
        # Fall back to default model config
        logger.warning(f"No model configuration found for {workflow_id}, using defaults")
        return {
            'provider': 'anthropic',
            'id': 'claude-sonnet-4-20250514',
            'temperature': 0.7,
            'max_tokens': 2000
        }
    
    def get_storage_config(self, workflow_id: str) -> Dict[str, Any]:
        """
        Extract storage configuration from workflow config.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Storage configuration dictionary
        """
        config = self.load_workflow_config(workflow_id)
        
        storage_config = config.get('storage', {})
        
        # Provide defaults
        return {
            'type': storage_config.get('type', 'postgres'),
            'table_name': storage_config.get('table_name', f'workflows-{workflow_id}'),
            'auto_upgrade_schema': storage_config.get('auto_upgrade_schema', True)
        }
    
    def get_workflow_settings(self, workflow_id: str) -> Dict[str, Any]:
        """
        Extract workflow-specific settings.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Workflow settings dictionary
        """
        config = self.load_workflow_config(workflow_id)
        
        workflow_info = config.get('workflow', {})
        settings = config.get('workflow_settings', {})
        
        return {
            'workflow_id': workflow_info.get('workflow_id', workflow_id),
            'name': workflow_info.get('name', workflow_id.replace('-', ' ').title()),
            'description': workflow_info.get('description', f'{workflow_id} workflow'),
            'version': workflow_info.get('version', 1),
            **settings
        }
    
    def _substitute_env_vars(self, config: Any) -> Any:
        """
        Recursively substitute environment variables in configuration.
        
        Args:
            config: Configuration value (dict, list, str, etc.)
            
        Returns:
            Configuration with environment variables substituted
        """
        if isinstance(config, dict):
            return {key: self._substitute_env_vars(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Handle ${VAR_NAME} format
            if config.startswith('${') and config.endswith('}'):
                env_var = config[2:-1]
                return os.getenv(env_var, config)  # Return original if env var not found
            return config
        else:
            return config


# Global loader instance
config_loader = WorkflowConfigLoader()


def load_workflow_config(workflow_id: str) -> Dict[str, Any]:
    """
    Convenience function to load workflow configuration.
    
    Args:
        workflow_id: Workflow identifier
        
    Returns:
        Configuration dictionary
    """
    return config_loader.load_workflow_config(workflow_id)


def get_model_config(workflow_id: str, agent_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to get model configuration.
    
    Args:
        workflow_id: Workflow identifier
        agent_key: Specific agent key (optional)
        
    Returns:
        Model configuration dictionary
    """
    return config_loader.get_model_config(workflow_id, agent_key)


def get_storage_config(workflow_id: str) -> Dict[str, Any]:
    """
    Convenience function to get storage configuration.
    
    Args:
        workflow_id: Workflow identifier
        
    Returns:
        Storage configuration dictionary
    """
    return config_loader.get_storage_config(workflow_id)


def get_workflow_settings(workflow_id: str) -> Dict[str, Any]:
    """
    Convenience function to get workflow settings.
    
    Args:
        workflow_id: Workflow identifier
        
    Returns:
        Workflow settings dictionary
    """
    return config_loader.get_workflow_settings(workflow_id)