"""
Shared configuration loader for workflows.
Provides consistent access to YAML configuration files following Agno standards.
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path


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
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Process environment variables
            config = self._process_env_vars(config)
            
            self._config_cache[workflow_name] = config
        
        return self._config_cache[workflow_name]
    
    def get_workflow_info(self, workflow_name: str) -> Dict[str, Any]:
        """Get workflow metadata"""
        config = self.load_workflow_config(workflow_name)
        return config.get('workflow', {})
    
    def get_model_config(self, workflow_name: str, model_key: str = 'default') -> Dict[str, Any]:
        """Get model configuration for a specific workflow"""
        config = self.load_workflow_config(workflow_name)
        
        # Handle different config structures
        if 'models' in config:
            # New structure with multiple models
            models = config['models']
            if model_key in models:
                return models[model_key]
            elif 'default' in models:
                return models['default']
            else:
                raise KeyError(f"Model '{model_key}' not found in workflow '{workflow_name}'")
        elif 'model' in config:
            # Single model structure
            return config['model']
        else:
            raise KeyError(f"No model configuration found for workflow '{workflow_name}'")
    
    def get_storage_config(self, workflow_name: str) -> Dict[str, Any]:
        """Get storage configuration for a workflow"""
        config = self.load_workflow_config(workflow_name)
        return config.get('storage', {})
    
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
        def process_value(value):
            if isinstance(value, str):
                if value.startswith('${') and value.endswith('}'):
                    env_var = value[2:-1]
                    return os.getenv(env_var, value)
                return value
            elif isinstance(value, dict):
                return {k: process_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [process_value(item) for item in value]
            return value
        
        return process_value(config)
    
    def clear_cache(self):
        """Clear the configuration cache"""
        self._config_cache.clear()


# Global instance for consistent access
config_loader = WorkflowConfigLoader()