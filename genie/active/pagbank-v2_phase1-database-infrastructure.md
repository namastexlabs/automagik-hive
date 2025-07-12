# Task Card: Setup Database Infrastructure

## Overview
This task card is part of the PagBank Multi-Agent Platform V2 implementation.

## Reference
- Main strategy: `/genie/active/pagbank-agents-platform-strategy.md`
- Demo app reference: `/genie/agno-demo-app/`

---

## Task Details

**Priority**: HIGH - Required for configuration management  
**Risk**: MEDIUM - New infrastructure component

## Current State
- No centralized configuration storage
- Agents hardcoded in Python files
- No audit trail for changes
- No version management

## Target State (From Demo App Pattern)
- PostgreSQL with Alembic V2 implementations (like `genie/agno-demo-app/db/`)
- Configuration stored in database tables
- YAML files implement in V2 to DB on startup
- Complete audit trail

## Implementation Steps

### Step 1: Setup Database Structure 
Copy structure from demo app:

```bash
# Create database directories
mkdir -p db/{migrations/versions,tables}
touch db/__init__.py
touch db/session.py
touch db/settings.py
touch db/alembic.ini

# Copy from demo app and adapt
cp genie/agno-demo-app/db/session.py db/session.py
cp genie/agno-demo-app/db/settings.py db/settings.py
cp genie/agno-demo-app/db/alembic.ini db/alembic.ini
```

### Step 2: Create Configuration Tables 
Based on strategy document schema:

```python
# db/tables/base.py
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# db/tables/agents.py
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from db.tables.base import Base

class AgentConfig(Base):
    __tablename__ = "agent_configs"
    
    agent_id = Column(String(50), primary_key=True)
    config_version = Column(Integer, default=1)
    
    # Configuration
    agent_metadata = Column(JSONB)  # {id, name, role}
    model_config = Column(JSONB)    # {provider, id, max_tokens}
    settings = Column(JSONB)        # All agent settings
    tools = Column(JSONB)           # Tool list
    instructions = Column(Text)
    
    # Metadata
    created_from_yaml = Column(String(255))
    last_updated = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class AgentVersion(Base):
    __tablename__ = "agent_versions"
    
    agent_id = Column(String(50), primary_key=True)
    version = Column(Integer, primary_key=True)  # 25, 26, 27
    
    # Same structure as AgentConfig
    agent_metadata = Column(JSONB)
    model_config = Column(JSONB)
    settings = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    notes = Column(Text)
```

### Step 3: Setup Alembic V2 Implementations 
Initialize Alembic:

```bash
# Initialize alembic
cd db
alembic init migrations
cd ..

# Update alembic.ini
sed -i 's|sqlalchemy.url = .*|sqlalchemy.url = postgresql://pagbank:password@localhost/pagbank_agents|' db/alembic.ini
```

Create initial V2 implementation:
```python
# db/migrations/env.py
from db.tables.base import Base
from db.tables import agents, teams, workflows, config_history

target_metadata = Base.metadata
```

```bash
# Generate V2 implementation
alembic revision --autogenerate -m "Initial configuration tables"
alembic upgrade head
```

### Step 4: Build Config V2 Loader 
Create YAML to Database V2 loader:

```python
# db/config_loader.py
import yaml
from pathlib import Path
from sqlalchemy.orm import Session
from db.tables.agents import AgentConfig
from db.tables.config_history import ConfigHistory

class ConfigLoader:
    def __init__(self, db):
        self.db = db_session
    
    def load_all_configs(self):
        """Like docker-compose up - loads YAMLs to DB"""
        print("🔄 Migrating configurations...")
        self.load_agents()
        self.load_teams()
        print("✅ V2 Implementation complete!")
    
    def load_agents(self):
        """Load agent YAMLs into database"""
        agents_dir = Path("agents/specialists")
        
        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir() and (agent_dir / "config.yaml").exists():
                self._load_agent(agent_dir)
    
    def _load_agent(self, agent_dir: Path):
        config_path = agent_dir / "config.yaml"
        with open(config_path) as f:
            yaml_config = yaml.safe_load(f)
        
        agent_id = yaml_config['agent']['id']
        
        # Check if exists
        existing = self.db.query(AgentConfig).filter_by(
            agent_id=agent_id
        ).first()
        
        if existing:
            print(f"⏭️  Skipping {agent_id} (already in DB)")
            return
        
        # Create new record
        agent_config = AgentConfig(
            agent_id=agent_id,
            agent_metadata=yaml_config.get('agent'),
            model_config=yaml_config.get('model'),
            settings=yaml_config.get('settings'),
            tools=yaml_config.get('tools', []),
            instructions=yaml_config.get('instructions', ''),
            created_from_yaml=str(config_path)
        )
        
        self.db.add(agent_config)
        print(f"✅ Loaded {agent_id}")
```

### Step 5: Add to Application Startup 
Integrate with FastAPI lifespan:

```python
# api/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from db.session import db_engine, SessionLocal
from db.tables.base import Base
from db.config_loader import ConfigLoader

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=db_engine)
    
    # Implement in V2 YAMLs to database
    db = SessionLocal()
    try:
        loader = ConfigLoader(db)
        loader.load_all_configs()
    finally:
        db.close()
    
    yield
    
app = FastAPI(lifespan=lifespan)
```

### Step 6: Test V2 Implementation 
Create test script:

```python
# tests/test_db_implementation.py
def test_yaml_to_db_implementation():
    # Create test YAML
    test_yaml = {
        'agent': {'id': 'test_agent', 'name': 'Test'},
        'model': {'provider': 'anthropic', 'id': 'claude-haiku'},
        'settings': {'markdown': True}
    }
    
    # Run V2 implementation
    loader = ConfigLoader(test_db)
    loader._load_agent_config('test_agent', test_yaml)
    
    # Verify in database
    config = test_db.query(AgentConfig).filter_by(
        agent_id='test_agent'
    ).first()
    
    assert config is not None
    assert config.agent_metadata['name'] == 'Test'
    assert config.model_config['provider'] == 'anthropic'
```

## Database Schema Diagram
```
agent_configs              config_history
+------------------+       +------------------+
| agent_id (PK)    |       | id (PK)          |
| config_version   |       | resource_type    |
| agent_metadata   |       | resource_id      |
| model_config     |<------| old_config       |
| settings         |       | new_config       |
| instructions     |       | changed_by       |
| created_from_yaml|       | changed_at       |
+------------------+       +------------------+

agent_versions            team_configs
+------------------+      +------------------+
| agent_id (PK)    |      | team_id (PK)     |
| version (PK)     |      | config_version   |
| agent_metadata   |      | team_metadata    |
| model_config     |      | members          |
| created_by       |      | settings         |
+------------------+      +------------------+
```

## Validation Checklist
- [ ] PostgreSQL database created and accessible
- [ ] All tables created via Alembic V2 implementation
- [ ] Test YAML successfully implement in V2s to database
- [ ] Config V2 loader runs on startup
- [ ] No data loss on restart (skip existing)
- [ ] Audit trail records all changes
- [ ] Database connection pooling works
- [ ] Rollback V2 implementation tested

## Dependencies
- **Prerequisite**: PostgreSQL installed and running
- **Blocks**: Phase 2 configuration hot reload
- **Required by**: All API endpoints that read config

## Success Metrics
- Zero data loss during V2 implementation
- Startup time < 5 seconds with V2 implementation
- All YAMLs successfully implement in V2
- Database queries < 50ms

Co-Authored-By: Automagik Genie <genie@namastex.ai>
