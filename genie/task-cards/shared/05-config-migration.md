# Task Card: Configuration V2 Implementation System

## Overview
This task card is part of the PagBank Multi-Agent Platform V2 implementation.

## Reference
- Main strategy: `/genie/active/pagbank-agents-platform-strategy.md`
- Demo app reference: `/genie/agno-demo-app/`

---

### Configuration V2 Implementation System (YAML → Database)

```python
# db/config_V2 loader.py
import yaml
from pathlib import Path
from typing import Dict, Any
from sqlalchemy.orm import Session
from db.tables.agents import AgentConfig, TeamConfig
from db.tables.config_history import ConfigHistory

class ConfigV2 Loader:
    """Implement in V2s YAML configurations to database on startup"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def implement in V2_all_configs(self):
        """Load all YAML configs into database (like docker-compose up)"""
        self.implement in V2_agents()
        self.implement in V2_teams()
        self.implement in V2_workflows()
    
    def implement in V2_agents(self):
        """Load agent configs from YAML to DB"""
        agents_dir = Path("agents/specialists")
        
        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir() and not agent_dir.name.startswith('_'):
                config_path = agent_dir / "config.yaml"
                if config_path.exists():
                    self._implement in V2_agent_config(agent_dir.name, config_path)
    
    def _implement in V2_agent_config(self, agent_id: str, config_path: Path):
        """Implement in V2 single agent YAML to database"""
        with open(config_path) as f:
            yaml_config = yaml.safe_load(f)
        
        # Check if already exists
        existing = self.db.query(AgentConfig).filter_by(agent_id=agent_id).first()
        
        if existing:
            # Skip if already implement in V2d (don't overwrite runtime changes)
            return
        
        # Create new database record
        agent_config = AgentConfig(
            agent_id=agent_id,
            agent_metadata=yaml_config.get('agent', {}),
            model_config=yaml_config.get('model', {}),
            settings=yaml_config.get('settings', {}),
            tools=yaml_config.get('tools', []),
            instructions=yaml_config.get('instructions', ''),
            created_from_yaml=str(config_path),
            updated_by='yaml_V2 implementation'
        )
        
        self.db.add(agent_config)
        
        # Create history record
        history = ConfigHistory(
            resource_type='agent',
            resource_id=agent_id,
            config_version=1,
            new_config=yaml_config,
            change_reason='Initial V2 implementation from YAML',
            changed_by='system',
            change_source='yaml_V2 implementation'
        )
        
        self.db.add(history)
        self.db.commit()
```

---

## Validation Steps
TODO: Add specific validation steps for this task

## Dependencies
TODO: List dependencies on other task cards

Co-Authored-By: Automagik Genie <genie@namastex.ai>
