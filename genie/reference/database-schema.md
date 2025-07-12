# V2 Database Schema Reference

**Navigation**: [← Agno Patterns](@genie/reference/agno-patterns.md) | [THIS FILE] | [YAML Configuration →](@genie/reference/yaml-configuration.md)

## Core Tables Overview

### 1. Configuration Tables
```sql
-- agents table
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,  -- v25, v26, v27
    model_provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(255) NOT NULL,
    system_prompt TEXT,
    instructions JSONB,  -- Array of instructions
    tools JSONB,         -- Array of tool names
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- teams table  
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    mode VARCHAR(50) NOT NULL,  -- 'route', 'parallel', 'sequential'
    version VARCHAR(50) NOT NULL,
    model_provider VARCHAR(50),
    model_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- team_members table (many-to-many)
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,  -- Order in team
    UNIQUE(team_id, agent_id)
);
```

### 2. Knowledge Base Tables
```sql
-- knowledge_base table (with pgvector)
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_unit VARCHAR(50) NOT NULL,
    category VARCHAR(255) NOT NULL,
    subcategory VARCHAR(255),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    embedding vector(1536),  -- For similarity search
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_business_unit (business_unit),
    INDEX idx_embedding (embedding)
);

-- typification_hierarchy table
CREATE TABLE typification_hierarchy (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level1 VARCHAR(255) NOT NULL,
    level2 VARCHAR(255) NOT NULL,
    level3 VARCHAR(255) NOT NULL,
    level4 VARCHAR(255) NOT NULL,
    level5 VARCHAR(255) NOT NULL,
    business_unit VARCHAR(50) NOT NULL,
    routing_keywords JSONB,  -- Array of keywords
    
    UNIQUE(level1, level2, level3, level4, level5)
);
```

### 3. Session Management Tables
```sql
-- sessions table (Agno managed)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    agent_id VARCHAR(255),
    team_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- messages table (Agno managed)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- memory table (Agno managed)
CREATE TABLE memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(session_id, key)
);
```

### 4. Monitoring Tables
```sql
-- agent_metrics table
CREATE TABLE agent_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    response_time_ms INTEGER,
    tokens_used INTEGER,
    success BOOLEAN,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_agent_created (agent_id, created_at)
);

-- routing_decisions table
CREATE TABLE routing_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    routed_to VARCHAR(255) NOT NULL,  -- agent_id
    confidence_score FLOAT,
    typification_result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## SQLAlchemy Models

### Base Configuration
```python
# db/tables/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

# db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
```

### Agent Model
```python
# db/tables/agents.py
from sqlalchemy import Column, String, Boolean, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from db.tables.base import Base
import uuid
from datetime import datetime

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    model_provider = Column(String(50), nullable=False)
    model_name = Column(String(255), nullable=False)
    system_prompt = Column(String)
    instructions = Column(JSON)
    tools = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Knowledge Base Model
```python
# db/tables/knowledge_base.py
from sqlalchemy import Column, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from db.tables.base import Base
import uuid

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_unit = Column(String(50), nullable=False, index=True)
    category = Column(String(255), nullable=False)
    subcategory = Column(String(255))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    embedding = Column(Vector(1536))
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_embedding', 'embedding', postgresql_using='ivfflat'),
    )
```

## Alembic Migrations

### Initial Migration
```python
# db/migrations/versions/001_initial_schema.py
"""Initial V2 schema

Revision ID: 001
Create Date: 2025-01-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

def upgrade():
    # Create pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create agents table
    op.create_table('agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', sa.String(255), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('model_provider', sa.String(50), nullable=False),
        sa.Column('model_name', sa.String(255), nullable=False),
        sa.Column('system_prompt', sa.Text()),
        sa.Column('instructions', postgresql.JSON()),
        sa.Column('tools', postgresql.JSON()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now())
    )
    
    # Create knowledge_base table with vector
    op.create_table('knowledge_base',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_unit', sa.String(50), nullable=False),
        sa.Column('category', sa.String(255), nullable=False),
        sa.Column('subcategory', sa.String(255)),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536)),
        sa.Column('metadata', postgresql.JSON()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now())
    )
    
    # Create indexes
    op.create_index('idx_business_unit', 'knowledge_base', ['business_unit'])
    op.create_index('idx_embedding', 'knowledge_base', ['embedding'], 
                    postgresql_using='ivfflat')

def downgrade():
    op.drop_table('knowledge_base')
    op.drop_table('agents')
```

## Query Examples

### Load Agent by ID
```python
def get_agent(db: Session, agent_id: str) -> Optional[Agent]:
    return db.query(Agent).filter(
        Agent.agent_id == agent_id,
        Agent.is_active == True
    ).first()
```

### Find Similar Knowledge
```python
from pgvector.sqlalchemy import Vector

def search_knowledge(db: Session, query_embedding: List[float], 
                    business_unit: str, limit: int = 5):
    return db.query(KnowledgeBase).filter(
        KnowledgeBase.business_unit == business_unit
    ).order_by(
        KnowledgeBase.embedding.l2_distance(query_embedding)
    ).limit(limit).all()
```

### Get Team with Members
```python
def get_team_with_members(db: Session, team_id: str):
    team = db.query(Team).filter(
        Team.team_id == team_id,
        Team.is_active == True
    ).first()
    
    if team:
        members = db.query(Agent).join(
            TeamMember, Agent.id == TeamMember.agent_id
        ).filter(
            TeamMember.team_id == team.id
        ).order_by(
            TeamMember.position
        ).all()
        
        return team, members
    return None, []
```

## Connection Management

### With Context Manager
```python
from contextlib import contextmanager

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Usage
with get_db() as db:
    agent = get_agent(db, "pagbank-specialist-v27")
```

### FastAPI Dependency
```python
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/agents/{agent_id}")
def read_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = get_agent(db, agent_id)
    return agent
```

**Navigation**: [← Agno Patterns](@genie/reference/agno-patterns.md) | [THIS FILE] | [YAML Configuration →](@genie/reference/yaml-configuration.md)
