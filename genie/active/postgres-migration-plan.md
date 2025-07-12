# PostgreSQL Migration Plan - PagBank Multi-Agent System

## Overview
Migrate from multiple SQLite databases to a single PostgreSQL database with proper schema design for the multi-agent system.

## Current State Analysis

### SQLite Usage
1. **Team Storage** (`data/pagbank.db`)
   - Table: `team_sessions` - Stores team conversation history
   - Table: `agent_sessions` - Stores individual agent sessions

2. **Memory System** (`data/memory/pagbank_memory_dev.db`)
   - Agno Memory v2 with SqliteMemoryDb
   - Pattern detection and user context persistence

3. **Session Management** (`data/pagbank.db`)
   - Table: `sessions` - User session tracking
   - Session state and interaction counts

4. **Ana's Memory** (`data/ana_memory.db`)
   - User memories for Ana's personalization

## PostgreSQL Schema Design

### Database: `ai` (existing)
Connection: `postgresql+psycopg://ai:ai@localhost:5532/ai`

### Tables Structure

#### 1. `team_sessions` (Agno PostgresStorage)
```sql
-- Managed by Agno PostgresStorage - auto schema
CREATE TABLE team_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    team_id VARCHAR(255) NOT NULL,
    team_name VARCHAR(255),
    user_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    messages JSONB DEFAULT '[]'::jsonb,
    team_session_state JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(session_id, team_id)
);

CREATE INDEX idx_team_sessions_user ON team_sessions(user_id);
CREATE INDEX idx_team_sessions_team ON team_sessions(team_id);
CREATE INDEX idx_team_sessions_created ON team_sessions(created_at);
```

#### 2. `agent_sessions` (Agno PostgresStorage)
```sql
-- Managed by Agno PostgresStorage - auto schema
CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(255),
    user_id VARCHAR(255),
    business_unit VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    messages JSONB DEFAULT '[]'::jsonb,
    agent_session_state JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(session_id, agent_id)
);

CREATE INDEX idx_agent_sessions_user ON agent_sessions(user_id);
CREATE INDEX idx_agent_sessions_agent ON agent_sessions(agent_id);
CREATE INDEX idx_agent_sessions_unit ON agent_sessions(business_unit);
```

#### 3. `user_memories` (Agno Memory v2 Compatible)
```sql
CREATE TABLE user_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    memory TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    memory_tags TEXT[],
    business_units TEXT[],
    importance_score FLOAT DEFAULT 0.5
);

CREATE INDEX idx_user_memories_user ON user_memories(user_id);
CREATE INDEX idx_user_memories_created ON user_memories(created_at);
CREATE INDEX idx_user_memories_tags ON user_memories USING GIN(memory_tags);
```

#### 4. `user_sessions` (Custom Session Management)
```sql
CREATE TABLE user_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    team_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    interaction_count INTEGER DEFAULT 0,
    session_context JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_active ON user_sessions(is_active, last_activity);
```

#### 5. `interaction_patterns` (Pattern Detection)
```sql
CREATE TABLE interaction_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(100) NOT NULL,
    pattern_data JSONB NOT NULL,
    occurrence_count INTEGER DEFAULT 1,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_ids TEXT[],
    business_units TEXT[],
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_patterns_type ON interaction_patterns(pattern_type);
CREATE INDEX idx_patterns_count ON interaction_patterns(occurrence_count DESC);
```

#### 6. `escalation_history` (Human Handoff Tracking)
```sql
CREATE TABLE escalation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    escalation_reason VARCHAR(255),
    escalation_type VARCHAR(50), -- 'explicit_request', 'frustration_language', 'caps_lock_yelling'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    whatsapp_notification_sent BOOLEAN DEFAULT FALSE,
    conversation_context JSONB,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_escalation_session ON escalation_history(session_id);
CREATE INDEX idx_escalation_user ON escalation_history(user_id);
CREATE INDEX idx_escalation_created ON escalation_history(created_at);
```

## Implementation Steps

### Phase 1: Create PostgreSQL Storage Classes

#### 1.1 Create Base PostgreSQL Manager
```python
# context/storage/postgres_manager.py
from typing import Optional
import os
from sqlalchemy import create_engine
from agno.storage.postgres import PostgresStorage

class PostgresManager:
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self.engine = create_engine(self.db_url)
        
    def get_team_storage(self) -> PostgresStorage:
        return PostgresStorage(
            table_name="team_sessions",
            db_url=self.db_url,
            auto_upgrade_schema=True
        )
    
    def get_agent_storage(self) -> PostgresStorage:
        return PostgresStorage(
            table_name="agent_sessions",
            db_url=self.db_url,
            auto_upgrade_schema=True
        )
```

#### 1.2 Update Memory Manager for PostgreSQL
```python
# context/memory/postgres_memory_manager.py
from agno.memory.v2.db.postgres import PostgresMemoryDb

class PostgresMemoryManager(MemoryManager):
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or get_memory_config()
        
        # Use PostgreSQL instead of SQLite
        self.memory_db = PostgresMemoryDb(
            table_name="user_memories",
            db_url=os.getenv("DATABASE_URL")
        )
        # ... rest of initialization
```

#### 1.3 Create PostgreSQL Session Manager
```python
# context/memory/postgres_session_manager.py
import psycopg2
from psycopg2.extras import RealDictCursor

class PostgresSessionManager:
    def __init__(self, db_url: str, session_timeout_minutes: int = 120):
        self.db_url = db_url
        self.session_timeout_minutes = session_timeout_minutes
        # Implementation using psycopg2 or SQLAlchemy
```

### Phase 2: Update Components

#### 2.1 Update playground.py
```python
from context.storage.postgres_manager import PostgresManager

# Replace SQLite with PostgreSQL
postgres_manager = PostgresManager()

# Configure storage for the orchestrator's routing team
orchestrator.routing_team.storage = postgres_manager.get_team_storage()

# Configure storage for individual agents
agent_storage = postgres_manager.get_agent_storage()
```

#### 2.2 Update main_orchestrator.py
```python
# Use PostgreSQL for Ana's memory
from agno.memory.v2.db.postgres import PostgresMemoryDb

ana_memory = Memory(
    model=Claude(id="claude-sonnet-4-20250514"),
    db=PostgresMemoryDb(
        table_name="user_memories",
        db_url=os.getenv("DATABASE_URL")
    ),
)
```

### Phase 3: Data Migration

#### 3.1 Create Migration Script
```python
# scripts/migrate_to_postgres.py
import sqlite3
import psycopg2
from psycopg2.extras import Json
import json
from datetime import datetime

def migrate_team_sessions():
    # Connect to SQLite
    sqlite_conn = sqlite3.connect('data/pagbank.db')
    sqlite_conn.row_factory = sqlite3.Row
    
    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    
    # Migrate team_sessions
    cursor = sqlite_conn.execute("SELECT * FROM team_sessions")
    # ... migration logic
```

### Phase 4: Testing & Validation

#### 4.1 Integration Tests
- Test team session persistence
- Test agent session isolation
- Test memory retrieval
- Test pattern detection
- Test escalation tracking

#### 4.2 Performance Tests
- Concurrent session handling
- Query performance with indexes
- Memory usage comparison

### Phase 5: Deployment

#### 5.1 Database Setup
```bash
# Create database schema
psql -h localhost -p 5532 -U ai -d ai -f schema/create_tables.sql

# Run migrations
uv run python scripts/migrate_to_postgres.py
```

#### 5.2 Environment Updates
- Ensure DATABASE_URL is set in production
- Update docker-compose if needed
- Configure connection pooling

## Benefits

1. **Centralized Data**: Single database for all components
2. **Better Performance**: PostgreSQL handles concurrent access better
3. **Rich Queries**: JSONB support for complex queries
4. **Scalability**: Easy to scale with read replicas
5. **Data Integrity**: Foreign keys and constraints
6. **Better Monitoring**: PostgreSQL has excellent monitoring tools

## Rollback Plan

1. Keep SQLite files as backup
2. Implement dual-write during migration
3. Test thoroughly in staging
4. Have rollback scripts ready

## Timeline

- **Week 1**: Create PostgreSQL storage classes
- **Week 2**: Update components and test
- **Week 3**: Data migration and validation
- **Week 4**: Production deployment

Co-Authored-By: Automagik Genie <genie@namastex.ai>