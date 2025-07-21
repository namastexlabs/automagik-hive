"""
AGNO Configuration Inheritance System

This module implements hierarchical parameter inheritance to eliminate redundancy
between team and member agent configurations.

Key Features:
- Team-level defaults cascade to member agents
- Member agents can override team defaults  
- Validation prevents configuration drift
- Template-based standardization
"""

from typing import Dict, Any, List, Optional, Set
from pathlib import Path
import yaml
import copy
from agno.utils.log import logger


class ConfigInheritanceManager:
    """Manages hierarchical configuration inheritance for AGNO teams and agents."""
    
    # Parameters that should only be set at team level
    TEAM_ONLY_PARAMETERS = {
        'mode', 'enable_agentic_context', 'share_member_interactions',
        'team_session_state', 'get_member_information_tool', 'members',
        'show_members_responses', 'stream_member_events'
    }
    
    # Parameters that must be unique per agent (cannot be inherited)
    AGENT_ONLY_PARAMETERS = {
        'agent_id', 'name', 'role', 'instructions', 'tools', 'table_name',
        'description', 'goal', 'success_criteria', 'expected_output',
        'introduction', 'additional_context'
    }
    
    # Parameters that can be inherited from team to agents
    INHERITABLE_PARAMETERS = {
        'memory': [
            'enable_user_memories', 'add_memory_references', 
            'enable_session_summaries', 'add_session_summary_references',
            'add_history_to_messages', 'num_history_runs', 'enable_agentic_memory'
        ],
        'display': [
            'markdown', 'show_tool_calls', 'add_datetime_to_instructions',
            'add_location_to_instructions', 'add_name_to_instructions'
        ],
        'knowledge': [
            'search_knowledge', 'enable_agentic_knowledge_filters',
            'references_format', 'add_references'
        ],
        'storage': [
            'type', 'auto_upgrade_schema'
        ],
        'model': [
            'provider', 'id', 'temperature', 'max_tokens'
        ]
    }
    
    def __init__(self):
        self.validation_errors = []
        
    def apply_inheritance(
        self, 
        team_config: Dict[str, Any], 
        agent_configs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Apply hierarchical inheritance from team config to agent configs.
        
        Args:
            team_config: Team configuration dictionary
            agent_configs: Dictionary of agent_id -> agent_config
            
        Returns:
            Dictionary of enhanced agent configurations with inheritance applied
        """
        enhanced_configs = {}
        
        # Extract team defaults for inheritance
        team_defaults = self._extract_team_defaults(team_config)
        
        for agent_id, agent_config in agent_configs.items():
            try:
                enhanced_config = self._apply_inheritance_to_agent(
                    agent_config, team_defaults, agent_id
                )
                enhanced_configs[agent_id] = enhanced_config
                logger.info(f"✅ Applied inheritance to agent {agent_id}")
                
            except Exception as e:
                logger.error(f"❌ Error applying inheritance to agent {agent_id}: {e}")
                enhanced_configs[agent_id] = agent_config  # Fallback to original
                
        return enhanced_configs
    
    def _extract_team_defaults(self, team_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract inheritable defaults from team configuration."""
        defaults = {}
        
        for category, parameters in self.INHERITABLE_PARAMETERS.items():
            if category in team_config:
                defaults[category] = {}
                for param in parameters:
                    if param in team_config[category]:
                        defaults[category][param] = team_config[category][param]
                        
        return defaults
    
    def _apply_inheritance_to_agent(
        self, 
        agent_config: Dict[str, Any], 
        team_defaults: Dict[str, Any],
        agent_id: str
    ) -> Dict[str, Any]:
        """Apply team defaults to a single agent configuration."""
        enhanced_config = copy.deepcopy(agent_config)
        
        for category, defaults in team_defaults.items():
            if category not in enhanced_config:
                enhanced_config[category] = {}
                
            for param, default_value in defaults.items():
                # Only inherit if agent doesn't have explicit override
                if param not in enhanced_config[category]:
                    enhanced_config[category][param] = default_value
                    logger.debug(f"🔄 Inherited {category}.{param}={default_value} for {agent_id}")
                else:
                    logger.debug(f"🔧 Override kept {category}.{param} for {agent_id}")
                    
        return enhanced_config
    
    def validate_configuration(
        self, 
        team_config: Dict[str, Any], 
        agent_configs: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """
        Validate team and agent configurations for inheritance compliance.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate team-only parameters aren't in agent configs
        for agent_id, agent_config in agent_configs.items():
            for param in self.TEAM_ONLY_PARAMETERS:
                if param in agent_config:
                    errors.append(
                        f"Agent {agent_id} has team-only parameter '{param}' - "
                        f"this should only be in team config"
                    )
        
        # Validate required unique parameters
        for agent_id, agent_config in agent_configs.items():
            if 'agent_id' not in agent_config.get('agent', {}):
                errors.append(f"Agent {agent_id} missing required 'agent.agent_id'")
                
        # Check for configuration drift in inheritable parameters
        errors.extend(self._check_configuration_drift(agent_configs))
        
        return errors
    
    def _check_configuration_drift(
        self, 
        agent_configs: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Check for unintentional configuration drift between agents."""
        errors = []
        
        # Check memory.num_history_runs consistency
        history_runs = {}
        for agent_id, config in agent_configs.items():
            if 'memory' in config and 'num_history_runs' in config['memory']:
                runs = config['memory']['num_history_runs']
                if runs not in history_runs:
                    history_runs[runs] = []
                history_runs[runs].append(agent_id)
        
        if len(history_runs) > 2:  # Allow up to 2 different values (team default + 1 override)
            errors.append(
                f"Excessive num_history_runs variation detected: {history_runs}. "
                f"Consider standardizing or documenting intentional overrides."
            )
            
        return errors
    
    def generate_inheritance_report(
        self, 
        team_config: Dict[str, Any], 
        original_configs: Dict[str, Dict[str, Any]],
        enhanced_configs: Dict[str, Dict[str, Any]]
    ) -> str:
        """Generate a report showing inheritance changes."""
        report = ["🔄 AGNO Configuration Inheritance Report", "="*50]
        
        team_defaults = self._extract_team_defaults(team_config)
        total_inherited = 0
        
        for agent_id in original_configs.keys():
            agent_inherited = 0
            report.append(f"\n📋 Agent: {agent_id}")
            
            for category, defaults in team_defaults.items():
                for param, value in defaults.items():
                    original_has = (
                        category in original_configs[agent_id] and 
                        param in original_configs[agent_id][category]
                    )
                    if not original_has:
                        report.append(f"  ✅ Inherited {category}.{param} = {value}")
                        agent_inherited += 1
                        total_inherited += 1
                    else:
                        report.append(f"  🔧 Kept override {category}.{param}")
            
            if agent_inherited == 0:
                report.append("  ℹ️  No inheritance applied (all parameters explicitly set)")
        
        report.extend([
            f"\n📊 Summary:",
            f"  • Total parameters inherited: {total_inherited}",
            f"  • Agents processed: {len(original_configs)}",
            f"  • Average inheritance per agent: {total_inherited/len(original_configs):.1f}",
        ])
        
        return "\n".join(report)


def load_team_with_inheritance(team_id: str, base_path: str = "ai") -> Dict[str, Any]:
    """
    Load a team configuration with inheritance applied to all member agents.
    
    Args:
        team_id: Team identifier
        base_path: Base path to AI configurations
        
    Returns:
        Enhanced team configuration with inheritance applied
    """
    manager = ConfigInheritanceManager()
    
    # Load team config
    team_config_path = Path(base_path) / "teams" / team_id / "config.yaml"
    with open(team_config_path) as f:
        team_config = yaml.safe_load(f)
    
    # Load all member agent configs
    agent_configs = {}
    for member_id in team_config.get('members', []):
        agent_config_path = Path(base_path) / "agents" / member_id / "config.yaml"
        if agent_config_path.exists():
            with open(agent_config_path) as f:
                agent_configs[member_id] = yaml.safe_load(f)
    
    # Apply inheritance
    enhanced_configs = manager.apply_inheritance(team_config, agent_configs)
    
    # Validate
    errors = manager.validate_configuration(team_config, enhanced_configs)
    if errors:
        logger.warning(f"Configuration validation errors for team {team_id}:")
        for error in errors:
            logger.warning(f"  ⚠️  {error}")
    
    # Generate report
    report = manager.generate_inheritance_report(team_config, agent_configs, enhanced_configs)
    logger.info(report)
    
    return {
        'team_config': team_config,
        'member_configs': enhanced_configs,
        'validation_errors': errors
    }


# Template loading utilities
def load_template(template_name: str) -> Dict[str, Any]:
    """Load a configuration template."""
    template_path = Path("ai/templates") / f"{template_name}.yaml"
    with open(template_path) as f:
        return yaml.safe_load(f)
        

def create_from_template(
    template_name: str, 
    overrides: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a configuration from template with overrides."""
    template = load_template(template_name)
    
    # Deep merge overrides into template
    config = copy.deepcopy(template)
    _deep_merge(config, overrides)
    
    return config


def _deep_merge(base: Dict, override: Dict) -> None:
    """Deep merge override dictionary into base dictionary."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value