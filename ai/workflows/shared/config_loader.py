"""
Shared configuration loader for workflows.
Provides consistent access to YAML configuration files following Agno standards.
"""

import yaml
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Use agno logger if available, fallback to standard logging
try:
    from agno.utils.log import logger
except ImportError:
    logger = logging.getLogger(__name__)


class WorkflowConfigLoader:
    """Centralized configuration loader for all workflows"""
    
    def __init__(self):
        self.workflows_dir = Path(__file__).parent.parent
        self._config_cache: Dict[str, Dict[str, Any]] = {}
    
    def load_workflow_config(self, workflow_name: str) -> Dict[str, Any]:
        """Load complete configuration for a workflow"""
        if workflow_name not in self._config_cache:
            config_path = self.workflows_dir / workflow_name / "config.yaml"
            
            if not config_path.exists():
                logger.error(f"Configuration file not found: {config_path}")
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                # Process environment variables
                config = self._process_env_vars(config)
                
                logger.info(f"Loaded configuration for workflow: {workflow_name}")
                self._config_cache[workflow_name] = config
                
            except yaml.YAMLError as e:
                logger.error(f"Invalid YAML configuration in {config_path}: {e}")
                raise ValueError(f"Invalid YAML configuration in {config_path}: {e}")
            except Exception as e:
                logger.error(f"Failed to load configuration from {config_path}: {e}")
                raise ValueError(f"Failed to load configuration from {config_path}: {e}")
        else:
            logger.debug(f"Using cached configuration for workflow: {workflow_name}")
        
        return self._config_cache[workflow_name]
    
    def get_workflow_info(self, workflow_name: str) -> Dict[str, Any]:
        """Get workflow metadata"""
        config = self.load_workflow_config(workflow_name)
        return config.get('workflow', {})
    
    def get_model_config(self, workflow_name: str, model_key: str = 'default') -> Dict[str, Any]:
        """Get model configuration for a specific workflow"""
        config = self.load_workflow_config(workflow_name)
        
        try:
            # Handle different config structures
            if 'models' in config:
                # New structure with multiple models
                models = config['models']
                if model_key in models:
                    logger.debug(f"Found model config '{model_key}' for workflow '{workflow_name}'")
                    return models[model_key]
                elif 'default' in models:
                    logger.warning(f"Model '{model_key}' not found, using default for workflow '{workflow_name}'")
                    return models['default']
                else:
                    available_models = list(models.keys())
                    logger.error(f"Model '{model_key}' not found in workflow '{workflow_name}'. Available: {available_models}")
                    raise ValueError(f"Model '{model_key}' not found in workflow '{workflow_name}'. Available models: {available_models}")
            elif 'model' in config:
                # Single model structure
                logger.debug(f"Using single model config for workflow '{workflow_name}'")
                return config['model']
            else:
                logger.error(f"No model configuration found for workflow '{workflow_name}'")
                raise ValueError(f"No model configuration found for workflow '{workflow_name}'. Expected 'model' or 'models' section in config.yaml")
        except KeyError as e:
            logger.error(f"Configuration error in workflow '{workflow_name}': {e}")
            raise ValueError(f"Configuration error in workflow '{workflow_name}': {e}")
    
    def get_storage_config(self, workflow_name: str) -> Dict[str, Any]:
        """Get storage configuration for a workflow"""
        config = self.load_workflow_config(workflow_name)
        storage_config = config.get('storage', {})
        
        if not storage_config:
            logger.warning(f"No storage configuration found for workflow '{workflow_name}', using defaults")
        else:
            logger.debug(f"Storage config for '{workflow_name}': {list(storage_config.keys())}")
        
        return storage_config
    
    def get_execution_config(self, workflow_name: str) -> Dict[str, Any]:
        """Get execution settings for a workflow"""
        config = self.load_workflow_config(workflow_name)
        return config.get('execution', {})
    
    def get_business_rules(self, workflow_name: str) -> Dict[str, Any]:
        """Get business rules configuration"""
        config = self.load_workflow_config(workflow_name)
        return config.get('business_rules', {})
    
    def get_integration_config(self, workflow_name: str) -> Dict[str, Any]:
        """Get integration settings"""
        config = self.load_workflow_config(workflow_name)
        return config.get('integrations', {})
    
    def get_monitoring_config(self, workflow_name: str) -> Dict[str, Any]:
        """Get monitoring and alerting settings"""
        config = self.load_workflow_config(workflow_name)
        return config.get('monitoring', {})
    
    def get_development_config(self, workflow_name: str) -> Dict[str, Any]:
        """Get development settings"""
        config = self.load_workflow_config(workflow_name)
        return config.get('development', {})
    
    def get_whatsapp_config(self, workflow_name: str) -> Dict[str, Any]:
        """Get WhatsApp notification configuration"""
        config = self.load_workflow_config(workflow_name)
        return config.get('whatsapp', {})
    
    def get_escalation_config(self, workflow_name: str) -> Dict[str, Any]:
        """Get escalation configuration"""
        config = self.load_workflow_config(workflow_name)
        return config.get('escalation', {})
    
    def _process_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process environment variables in configuration"""
        substitutions_made = []
        
        def process_value(value, path=""):
            if isinstance(value, str):
                if value.startswith('${') and value.endswith('}'):
                    env_var = value[2:-1]
                    env_value = os.getenv(env_var)
                    if env_value is not None:
                        substitutions_made.append(f"{path}: ${{{env_var}}} -> {env_value}")
                        return env_value
                    else:
                        logger.warning(f"Environment variable '{env_var}' not found at {path}, keeping original value")
                        return value
                return value
            elif isinstance(value, dict):
                return {k: process_value(v, f"{path}.{k}" if path else k) for k, v in value.items()}
            elif isinstance(value, list):
                return [process_value(item, f"{path}[{i}]") for i, item in enumerate(value)]
            return value
        
        result = process_value(config)
        
        if substitutions_made:
            logger.debug(f"Environment variable substitutions: {substitutions_made}")
        
        return result
    
    def clear_cache(self):
        """Clear the configuration cache"""
        cache_size = len(self._config_cache)
        self._config_cache.clear()
        logger.info(f"Configuration cache cleared ({cache_size} entries removed)")


# Global instance for consistent access
config_loader = WorkflowConfigLoader()