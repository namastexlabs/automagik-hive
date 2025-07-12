# Database Directory - Schema and Data Management

**Purpose**: Database schema, migrations, and data access patterns for the PagBank Multi-Agent System
**Location**: `/db/` - Database configuration and models  
**Reference**: PostgreSQL with PgVector for agent/team storage, SQLite fallback
**Navigation**: [← Config CLAUDE](@config/CLAUDE.md) | [THIS FILE] | [Workflows CLAUDE →](@workflows/CLAUDE.md)

---

## Architecture Overview

The PagBank Multi-Agent System uses a dual-database approach:
- **PostgreSQL with PgVector**: Primary database for production with vector similarity search
- **SQLite**: Automatic fallback for development and testing environments
- **Agno Framework Integration**: Leverages Agno's built-in storage abstractions for session management
- **Database-Driven Configuration**: YAML → Database → Runtime configuration pattern

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

## Agno Storage Integration

### PostgreSQL Configuration (Production)
```python
# config/postgres_config.py
from agno.storage.postgres import PostgresStorage

def get_postgres_storage(
    table_name: str = "pagbank_sessions",
    mode: str = "team"
) -> Optional[PostgresStorage]:
    """
    Get PostgreSQL storage using Agno's built-in PostgresStorage.
    Falls back to None if DATABASE_URL is not set (will use SQLite).
    """
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        return None
    
    # Agno handles everything - table creation, schema management, etc.
    return PostgresStorage(
        table_name=table_name,
        db_url=db_url,
        mode=mode,
        auto_upgrade_schema=True
    )
```

### Database Configuration Class
```python
# config/database.py
class DatabaseConfig:
    """PostgreSQL with PgVector configuration."""
    
    def __init__(self):
        self.url = DATABASE_URL
        self.engine = None
        self.session_factory = None
        self.base = declarative_base()
    
    def create_engine(self):
        """Create SQLAlchemy engine with optimized settings."""
        if not self.engine:
            self.engine = create_engine(
                self.url,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # Set to True for SQL debugging
            )
        return self.engine
    
    def init_pgvector(self):
        """Initialize PgVector extension."""
        with self.get_session() as session:
            session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            session.commit()
    
    def test_pgvector(self) -> bool:
        """Test PgVector functionality."""
        try:
            with self.get_session() as session:
                result = session.execute(text("SELECT vector_dims(vector '[1,2,3]');"))
                return result.fetchone()[0] == 3
        except Exception:
            return False
```

### Health Check Implementation
```python
def health_check() -> dict:
    """Check database health for monitoring."""
    return {
        "connection": db_config.test_connection(),
        "pgvector": db_config.test_pgvector(),
        "url": DATABASE_URL.replace(DATABASE_URL.split("@")[0].split("//")[1], "***")
    }
```

## Migration Strategies

### Alembic Integration (From agno-demo-app)
```bash
# Create database revision
alembic -c db/alembic.ini revision --autogenerate -m "Add new feature tables"

# Apply migrations
alembic -c db/alembic.ini upgrade head

# Production migration with environment variable
MIGRATE_DB=True  # Runs migrations automatically at startup
```

### Migration Configuration
```python
# db/alembic.ini configuration
[alembic]
script_location = db/migrations
sqlalchemy.url = driver://user:pass@localhost/dbname

# db/migrations/env.py
from db.tables.base import Base
target_metadata = Base.metadata
```

### Environment-Specific Migration
```bash
# Development (Docker)
docker exec -it pagbank-api alembic -c db/alembic.ini upgrade head

# Production (ECS)
aws ecs execute-command --cluster pagbank-cluster \
    --task $TASK_ARN \
    --container pagbank-api \
    --command "alembic -c db/alembic.ini upgrade head"
```

## Performance Optimization Patterns

### Connection Pooling
```python
# Optimized engine configuration
engine = create_engine(
    DATABASE_URL,
    pool_size=20,           # Base pool size
    max_overflow=30,        # Additional connections
    pool_pre_ping=True,     # Validate connections
    pool_recycle=3600,      # Recycle connections every hour
    echo=False              # Disable SQL logging in production
)
```

### Vector Index Optimization
```sql
-- PgVector index for fast similarity search
CREATE INDEX idx_embedding ON knowledge_base 
USING ivfflat (embedding) 
WITH (lists = 100);

-- Analyze table for query optimization
ANALYZE knowledge_base;
```

### Query Optimization Examples
```python
# Optimized knowledge search with filtering
def search_knowledge_optimized(
    db: Session, 
    query_embedding: List[float], 
    business_unit: str, 
    limit: int = 5
):
    return db.query(KnowledgeBase)\
        .filter(KnowledgeBase.business_unit == business_unit)\
        .order_by(KnowledgeBase.embedding.l2_distance(query_embedding))\
        .limit(limit)\
        .options(defer(KnowledgeBase.embedding))  # Don't load vectors in result
```

### Monitoring Queries
```python
# Performance monitoring for agent responses
def log_agent_metrics(agent_id: str, response_time: int, tokens: int, success: bool):
    with get_db() as db:
        metric = AgentMetrics(
            agent_id=agent_id,
            response_time_ms=response_time,
            tokens_used=tokens,
            success=success,
            created_at=datetime.utcnow()
        )
        db.add(metric)
        db.commit()
```

## Database-Driven Configuration Management

### YAML to Database Pattern
```python
# Load agent configuration from YAML into database
def load_agent_config(yaml_path: str):
    with open(yaml_path) as f:
        config = yaml.safe_load(f)
    
    with get_db() as db:
        agent = Agent(
            agent_id=config["agent_id"],
            name=config["name"],
            version=config["version"],
            model_provider=config["model"]["provider"],
            model_name=config["model"]["name"],
            system_prompt=config["system_prompt"],
            instructions=config["instructions"],
            tools=config["tools"],
            is_active=True
        )
        db.add(agent)
        db.commit()
```

### Runtime Configuration Retrieval
```python
# Get active agent configuration at runtime
def get_active_agent_config(agent_id: str) -> dict:
    with get_db() as db:
        agent = db.query(Agent).filter(
            Agent.agent_id == agent_id,
            Agent.is_active == True
        ).first()
        
        if agent:
            return {
                "name": agent.name,
                "model": {
                    "provider": agent.model_provider,
                    "name": agent.model_name
                },
                "system_prompt": agent.system_prompt,
                "instructions": agent.instructions,
                "tools": agent.tools
            }
```

**Navigation**: [← Agno Patterns](@genie/reference/agno-patterns.md) | [THIS FILE] | [YAML Configuration →](@genie/reference/yaml-configuration.md)


## Storage Patterns (From Reference)

# Agno Storage Validation

**Status**: ✅ CONSOLIDATED REFERENCE ✅  
**Library**: `/context7/agno` (2552 code snippets)  
**Description**: Storage backends and parameter validation rules  
**Parent**: [Agno Patterns Index](@genie/reference/agno-patterns-index.md)  
**Consolidated from**:
- agno-storage-configuration.md
- agno-validation-rules.md

---


## Storage Configuration ✅ VERIFIED

> **See Also**: For SQL table schemas created by these storage backends, see [Database Schema](@genie/reference/database-schema.md)


### SQLite Storage (Default)
```yaml
sqlite_storage:
  # CLASS: SqliteStorage
  table_name: str                               # Required - Table name for sessions
  db_url: Optional[str]                         # Database URL
  db_file: Optional[str]                        # Database file path (if db_url not provided)
  db_engine: Optional[Engine]                   # Existing SQLAlchemy engine
  schema_version: int                           # Default: 1
  auto_upgrade_schema: bool                     # Default: False
  mode: Optional[Literal["agent", "team", "workflow"]] # Default: "agent"
  
  # NOTE: If none of db_url, db_file, db_engine provided, uses in-memory SQLite
```


### PostgreSQL Storage
```yaml
postgres_storage:
  # CLASS: PostgresStorage
  table_name: str                               # Required - Table name for sessions
  schema: Optional[str]                         # Default: "ai"
  db_url: Optional[str]                         # Database URL (required if no db_engine)
  db_engine: Optional[Engine]                   # Existing SQLAlchemy engine
  schema_version: int                           # Default: 1
  auto_upgrade_schema: bool                     # Default: False
  mode: Optional[Literal["agent", "team", "workflow"]] # Default: "agent"
  
  # NOTE: Either db_url or db_engine must be provided
```


### SingleStore Storage
```yaml
singlestore_storage:
  # CLASS: SingleStoreStorage
  table_name: str                               # Required - Table name
  schema: Optional[str]                         # Default: "ai"
  db_url: Optional[str]                         # Database URL (required if no db_engine)
  db_engine: Optional[Engine]                   # Existing SQLAlchemy engine
  schema_version: int                           # Default: 1
  auto_upgrade_schema: bool                     # Default: False
  mode: Optional[Literal["agent", "team", "workflow"]] # Default: "agent"
```


### MongoDB Storage
```yaml
mongodb_storage:
  # CLASS: MongoDbStorage
  collection_name: str                          # Required - MongoDB collection name
  db_url: str                                   # Required - MongoDB connection URL
  db_name: str                                  # Required - Database name
```


### YAML File Storage
```yaml
yaml_storage:
  # CLASS: YamlStorage
  dir_path: str                                 # Required - Directory path for YAML files
```


### Required vs Optional Parameters
```yaml
required_parameters:
  Team:
    - members: List[Union[Agent, Team]]         # ONLY required Team parameter
  
  Agent:
    - None                                      # ALL Agent parameters are optional with defaults
  
  Workflow:
    - None                                      # ALL Workflow parameters are optional
  
  Storage:
    SqliteStorage:
      - table_name: str                         # Required
    PostgresStorage:
      - table_name: str                         # Required
      - db_url OR db_engine                     # One required
    MongoDbStorage:
      - collection_name: str                    # Required
      - db_url: str                            # Required
      - db_name: str                           # Required
    YamlStorage:
      - dir_path: str                          # Required
```


### Parameter Dependencies ✅ VERIFIED
```yaml
parameter_dependencies:
  knowledge_search:
    condition: "search_knowledge=True"
    requirement: "knowledge parameter must be provided"
    
  agentic_context:
    condition: "enable_agentic_context=True"
    applies_to: "Team only"
    effect: "Allows team leader to maintain and update team context"
    
  storage_engines:
    postgres_singlestore:
      requirement: "Either db_url OR db_engine must be provided (not both)"
    sqlite:
      fallback: "Uses in-memory SQLite if no db_url, db_file, or db_engine provided"
      
  tool_choice_logic:
    no_tools: "tool_choice defaults to 'none'"
    with_tools: "tool_choice defaults to 'auto'"
```


### Validation Rules ✅ VERIFIED
```yaml
validation_rules:
  team_mode:
    type: "Literal['route', 'coordinate', 'collaborate']"
    validation: "Must be exactly one of these three values"
    
  references_format:
    type: "Literal['json', 'yaml']"
    validation: "Must be exactly 'json' or 'yaml'"
    
  storage_mode:
    type: "Literal['agent', 'team', 'workflow']"
    validation: "Must be exactly one of these three values"
    
  reasoning_steps:
    reasoning_min_steps: "Must be >= 1 (default: 1)"
    reasoning_max_steps: "Must be >= reasoning_min_steps (default: 10)"
    
  num_history_runs:
    type: "int"
    default: 3
    validation: "Must be positive integer"
    
  boolean_defaults:
    rule: "All boolean parameters default to False unless explicitly stated"
    exceptions:
      - "create_default_system_message: defaults to True"
      - "add_member_tools_to_system_message: defaults to True"
      - "resolve_context: defaults to True"
      - "parse_response: defaults to True"
      - "show_tool_calls: defaults to True"
      - "search_knowledge: defaults to True (only if knowledge provided)"

---

**Navigation**: [Index](@genie/reference/agno-patterns-index.md)

---

## Review Task for Context Transfer ✅ COMPREHENSIVE VALIDATION

### Content Verification Checklist - Database Schema and Management Domain
**Before proceeding to api/CLAUDE.md, validate this db/ documentation:**

#### ✅ Core Database Patterns Documented
1. ✅ **PostgreSQL with PgVector setup** for vector similarity search and production deployment
2. ✅ **SQLite automatic fallback** for development environments without PostgreSQL
3. ✅ **Agno storage integration** with built-in abstractions for session management
4. ✅ **Complete database schema** covering agents, teams, knowledge base, and monitoring
5. ✅ **Migration strategy** with Alembic integration and environment-specific deployment
6. ✅ **Performance optimization** patterns including connection pooling and vector indexing
7. ✅ **Database-driven configuration** management with YAML → Database → Runtime pattern

#### ✅ Cross-Reference Validation with Other CLAUDE.md Files
- **agents/CLAUDE.md**: Agent storage configurations should match documented schema and patterns
- **teams/CLAUDE.md**: Team storage and routing tables should support documented team patterns
- **workflows/CLAUDE.md**: Workflow execution tracking should match documented monitoring schema
- **config/CLAUDE.md**: Database connection patterns should align with global configuration
- **api/CLAUDE.md**: Database health checks and FastAPI dependencies should match patterns
- **tests/CLAUDE.md**: Database testing patterns should cover all documented schema and operations

#### ✅ Missing Content Identification
**Content that should be transferred TO other CLAUDE.md files:**
- API database dependencies → Transfer to `api/CLAUDE.md`
- Database testing patterns → Transfer to `tests/CLAUDE.md`
- Global database configuration → Already documented in `config/CLAUDE.md` ✅
- Agent storage patterns → Already documented in `agents/CLAUDE.md` ✅

**Content that should be transferred FROM other CLAUDE.md files:**
- Configuration management FROM `config/CLAUDE.md` ✅ Already integrated
- Agent schema requirements FROM `agents/CLAUDE.md` ✅ Already documented
- Team storage requirements FROM `teams/CLAUDE.md` ✅ Already documented
- ❌ No other database-specific content found requiring transfer here

#### ✅ Duplication Prevention
**Content properly separated to avoid overlap:**
- ✅ Database schema and models documented here, NOT scattered across component files
- ✅ Agno storage integration patterns here, NOT duplicated in agent/team files
- ✅ Migration and deployment strategies here, NOT repeated in configuration files
- ✅ Performance optimization here, NOT mixed with application logic

#### ✅ Context Transfer Requirements for Future Development
**Essential database context that must be preserved:**
1. **Dual Database Strategy**: PostgreSQL for production, SQLite for development with automatic detection
2. **PgVector Integration**: Vector similarity search for knowledge base with proper indexing
3. **Agno Storage Abstraction**: Use framework's built-in storage with mode-specific configurations
4. **Schema Versioning**: Alembic migrations with automatic schema upgrades in development
5. **Performance Patterns**: Connection pooling, vector indexing, and query optimization
6. **Health Monitoring**: Database connectivity and feature validation for production readiness

#### ✅ Integration Validation Requirements
**Validate these integration points when implementing:**
- **Database → Agent Integration**: Verify agent storage patterns work with documented schema
- **Database → Team Integration**: Confirm team storage and routing tables support team operations
- **Database → Workflow Integration**: Test workflow execution tracking and monitoring storage
- **Database → Config Integration**: Ensure database configurations align with global settings
- **Database → API Integration**: Validate FastAPI dependencies and health check endpoints
- **Database → Testing Integration**: Confirm test patterns cover all schema and operations

### ✅ Content Successfully Organized in db/CLAUDE.md
- ✅ **Database Architecture**: PostgreSQL/SQLite dual approach with automatic fallback
- ✅ **Complete Schema**: Agents, teams, knowledge base, sessions, and monitoring tables
- ✅ **Agno Integration**: Storage abstractions with mode-specific configurations
- ✅ **Migration Strategy**: Alembic patterns with environment-specific deployment
- ✅ **Performance Optimization**: Connection pooling, vector indexing, and query patterns
- ✅ **Health Monitoring**: Connection validation and feature testing patterns

### ✅ Key Patterns Documented for Multi-Agent System
1. **PostgreSQL with PgVector Setup**: Full configuration with vector similarity search capabilities
2. **Agno Storage Integration**: Built-in storage abstractions for seamless session management
3. **SQLite Fallback Pattern**: Automatic development environment fallback for zero-config setup
4. **Migration Strategy**: Alembic integration with environment-specific deployment patterns
5. **Performance Optimization**: Connection pooling, vector indexing, and query optimization
6. **Database-Driven Configuration**: YAML → Database → Runtime configuration pattern
7. **Health Check Implementation**: Connection and PgVector validation for production readiness
8. **Schema Management**: Automated table creation and upgrades with version control

### ✅ Validation Completed - Ready for api/CLAUDE.md Review

---

## Database Schema (From Reference)

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


