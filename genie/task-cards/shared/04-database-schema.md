# Task Card: Database Schema Definitions

## Overview
This task card is part of the PagBank Multi-Agent Platform V2 implementation.

## Reference
- Main strategy: `/genie/active/pagbank-agents-platform-strategy.md`
- Demo app reference: `/genie/agno-demo-app/`

---

### NEW: Configuration Management Database Schema

```python
# db/tables/agents.py
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class AgentVersion(Base):
    """Simple agent version storage"""
    __tablename__ = "agent_versions"
    
    # Composite primary key: agent_id + version
    agent_id = Column(String(50), primary_key=True)
    version = Column(Integer, primary_key=True)  # 25, 26, 27, etc.
    
    # Core configuration (JSON storage for flexibility)
    agent_metadata = Column(JSONB)  # {id, name, role}
    model_config = Column(JSONB)    # {provider, id, max_tokens, temperature}
    settings = Column(JSONB)        # All agent settings
    tools = Column(JSONB)           # Tool configurations
    instructions = Column(Text)     # Agent instructions
    
    # Simple metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    notes = Column(Text)  # What changed

class TeamConfig(Base):
    """Runtime team configuration"""
    __tablename__ = "team_configs"
    
    team_id = Column(String(50), primary_key=True)
    config_version = Column(Integer, default=1)
    
    # Core configuration
    team_metadata = Column(JSONB)   # {id, name, role, mode}
    model_config = Column(JSONB)    # Model settings
    settings = Column(JSONB)        # All team settings
    members = Column(JSONB)         # List of member agent IDs
    storage_config = Column(JSONB)  # Storage configuration
    instructions = Column(Text)     # Team instructions
    
    # Metadata
    created_from_yaml = Column(String(255))
    last_updated = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(String(100))
    is_active = Column(Boolean, default=True)
```

```python
# db/tables/config_history.py
class ConfigHistory(Base):
    """Audit trail for all configuration changes"""
    __tablename__ = "config_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_type = Column(String(20))  # 'agent', 'team', 'workflow'
    resource_id = Column(String(50))
    config_version = Column(Integer)
    
    # Change tracking
    changed_fields = Column(JSONB)      # Which fields were modified
    old_config = Column(JSONB)          # Previous configuration
    new_config = Column(JSONB)          # New configuration
    change_reason = Column(String(255)) # Why the change was made
    
    # Metadata
    changed_at = Column(DateTime, default=datetime.utcnow)
    changed_by = Column(String(100))
    change_source = Column(String(50))  # 'api', 'yaml_V2 implementation', 'admin'
```

---

## Validation Steps
TODO: Add specific validation steps for this task

## Dependencies
TODO: List dependencies on other task cards

Co-Authored-By: Automagik Genie <genie@namastex.ai>
