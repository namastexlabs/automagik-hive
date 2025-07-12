# PostgreSQL Tables Analysis - What We Actually Need

## Current SQLite Usage

### 1. **data/pagbank.db**
- `team_sessions` - Agno's team conversation storage
- `agent_sessions` - Agno's individual agent storage  
- `sessions` - Custom session management (from session_manager.py)
- `pagbank_memories` - Agno Memory v2 storage

### 2. **data/ana_memory.db**
- `ana_user_memories` - Ana's user memory storage

## What Actually Exists in Code

### Real Components:
1. **Agno Storage** - Built-in storage for teams and agents
2. **Session Manager** - Custom session tracking (context/memory/session_manager.py)
3. **Memory Manager** - Uses Agno Memory v2
4. **Human Handoff Detection** - Simple boolean detection, no escalation system

### What DOESN'T Exist:
1. **No Escalation System** - Just templates and prompts, no actual ticket system
2. **No Pattern Detection System** - PatternDetector class exists but not used
3. **No Interaction Patterns Table** - Not implemented
4. **No Escalation History** - No ticket tracking

## Minimal PostgreSQL Schema Needed

Based on actual usage, we only need:

### 1. Agno-Managed Tables (Auto-created by Agno)
- `team_sessions` - Let Agno PostgresStorage manage this
- `agent_sessions` - Let Agno PostgresStorage manage this
- `user_memories` - Let Agno Memory v2 PostgresMemoryDb manage this

### 2. Custom Tables We Need to Create
- `user_sessions` - For session management (replaces SQLite sessions table)

That's it! Just 4 tables total, 3 managed by Agno.

## Simplified Schema

```sql
-- Only need to create this one table
-- Agno will create the others automatically

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

## Implementation Plan

### 1. Update playground.py
```python
from agno.storage.postgres import PostgresStorage
import os

db_url = os.getenv("DATABASE_URL")

# Configure storage for team
team_storage = PostgresStorage(
    table_name="team_sessions",
    db_url=db_url,
    auto_upgrade_schema=True
)

# Configure storage for agents
agent_storage = PostgresStorage(
    table_name="agent_sessions", 
    db_url=db_url,
    auto_upgrade_schema=True
)
```

### 2. Update memory_manager.py
```python
from agno.memory.v2.db.postgres import PostgresMemoryDb

self.memory_db = PostgresMemoryDb(
    table_name="user_memories",
    db_url=os.getenv("DATABASE_URL")
)
```

### 3. Update session_manager.py
- Replace SQLite with PostgreSQL queries
- Keep the same SessionState interface

### 4. Update main_orchestrator.py for Ana's memory
```python
ana_memory = Memory(
    model=Claude(id="claude-sonnet-4-20250514"),
    db=PostgresMemoryDb(
        table_name="ana_user_memories",
        db_url=os.getenv("DATABASE_URL")
    ),
)
```

## What We DON'T Need

1. **Escalation tables** - No escalation system exists
2. **Pattern tables** - Pattern detector not used
3. **Complex metrics views** - Keep it simple
4. **Resolution tracking** - No ticket system

## Benefits of This Approach

1. **Minimal Changes** - Only update storage configs
2. **Let Agno Handle It** - Use built-in PostgresStorage
3. **Single Database** - Everything in one place
4. **Simple Migration** - Just 1 custom table to migrate

Co-Authored-By: Automagik Genie <genie@namastex.ai>