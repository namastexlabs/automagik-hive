# Task Card: Database-Driven Configuration API

## Overview
This task card is part of the PagBank Multi-Agent Platform V2 implementation.

## Reference
- Main strategy: `/genie/active/pagbank-agents-platform-strategy.md`
- Demo app reference: `/genie/agno-demo-app/`

---

### Database-Driven Configuration API

```python
# api/routes/agents.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.tables.agents import AgentConfig
from db.tables.config_history import ConfigHistory

@router.get("/{agent_id}/config")
async def get_agent_config(agent_id: str, db: Session = Depends(get_db)):
    """Get current runtime configuration from database"""
    config = db.query(AgentConfig).filter_by(
        agent_id=agent_id, is_active=True
    ).first()
    
    if not config:
        raise HTTPException(404, f"Agent {agent_id} not found")
    
    return {
        "agent": config.agent_metadata,
        "model": config.model_config,
        "settings": config.settings,
        "tools": config.tools,
        "instructions": config.instructions,
        "meta": {
            "version": config.config_version,
            "last_updated": config.last_updated,
            "source": "database"
        }
    }

@router.put("/{agent_id}/config")
async def update_agent_config(
    agent_id: str, 
    config_update: dict,
    reason: str = "API update",
    db: Session = Depends(get_db)
):
    """Update runtime configuration in database (NOT YAML file)"""
    
    # Get current config
    current = db.query(AgentConfig).filter_by(
        agent_id=agent_id, is_active=True
    ).first()
    
    if not current:
        raise HTTPException(404, f"Agent {agent_id} not found")
    
    # Store old config for history
    old_config = {
        "agent": current.agent_metadata,
        "model": current.model_config,
        "settings": current.settings,
        "tools": current.tools,
        "instructions": current.instructions
    }
    
    # Apply updates (merge, don't replace)
    if "model" in config_update:
        current.model_config = {**current.model_config, **config_update["model"]}
    if "settings" in config_update:
        current.settings = {**current.settings, **config_update["settings"]}
    if "instructions" in config_update:
        current.instructions = config_update["instructions"]
    
    # Increment version
    current.config_version += 1
    current.last_updated = datetime.utcnow()
    current.updated_by = "api_user"  # TODO: Get from auth
    
    # Create history record
    history = ConfigHistory(
        resource_type='agent',
        resource_id=agent_id,
        config_version=current.config_version,
        changed_fields=list(config_update.keys()),
        old_config=old_config,
        new_config=config_update,
        change_reason=reason,
        changed_by="api_user",
        change_source="api"
    )
    
    db.add(history)
    db.commit()
    
    # Hot reload agent in registry
    AgentRegistry.reload_from_database(agent_id)
    
    return {"status": "updated", "version": current.config_version}

@router.post("/{agent_id}/config/reset")
async def reset_agent_config(agent_id: str, db: Session = Depends(get_db)):
    """Reset to original YAML configuration"""
    
    current = db.query(AgentConfig).filter_by(
        agent_id=agent_id, is_active=True
    ).first()
    
    if not current:
        raise HTTPException(404, f"Agent {agent_id} not found")
    
    # Load original YAML
    yaml_path = Path(current.created_from_yaml)
    if not yaml_path.exists():
        raise HTTPException(400, "Original YAML file not found")
    
    with open(yaml_path) as f:
        yaml_config = yaml.safe_load(f)
    
    # Reset to YAML values
    current.agent_metadata = yaml_config.get('agent', {})
    current.model_config = yaml_config.get('model', {})
    current.settings = yaml_config.get('settings', {})
    current.tools = yaml_config.get('tools', [])
    current.instructions = yaml_config.get('instructions', '')
    current.config_version += 1
    current.last_updated = datetime.utcnow()
    current.updated_by = "yaml_reset"
    
    db.commit()
    
    # Hot reload
    AgentRegistry.reload_from_database(agent_id)
    
    return {"status": "reset", "version": current.config_version}

@router.get("/{agent_id}/config/history")
async def get_config_history(agent_id: str, db: Session = Depends(get_db)):
    """Get configuration change audit trail"""
    history = db.query(ConfigHistory).filter_by(
        resource_type='agent',
        resource_id=agent_id
    ).order_by(ConfigHistory.changed_at.desc()).limit(50).all()
    
    return [
        {
            "version": h.config_version,
            "changed_at": h.changed_at,
            "changed_by": h.changed_by,
            "change_reason": h.change_reason,
            "changed_fields": h.changed_fields,
            "source": h.change_source
        }
        for h in history
    ]
```

---

## Validation Steps
TODO: Add specific validation steps for this task

## Dependencies
TODO: List dependencies on other task cards

Co-Authored-By: Automagik Genie <genie@namastex.ai>
