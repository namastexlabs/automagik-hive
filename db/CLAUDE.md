# Database Layer - Component Context (Tier 2)

> **Note**: This is component-specific context. See root **CLAUDE.md** for master project context and coding standards.

## Purpose
The database layer provides persistent storage and data management for the Automagik Multi-Agent Framework. It implements a dual-database architecture with PostgreSQL (production) and SQLite (development), featuring vector similarity search, automated schema management, and seamless integration with the Agno framework's storage abstractions.

## Current Status: Production Ready ✅
- PostgreSQL with PgVector integration for vector similarity search
- SQLite automatic fallback for zero-config development environments  
- Agno framework storage abstractions for session and memory management
- Complete schema covering agents, teams, knowledge base, and monitoring
- Alembic migration system with environment-specific deployment patterns

## Component-Specific Development Guidelines
- **Database Technology**: PostgreSQL with PgVector extension for production, SQLite for development
- **Schema Management**: Alembic migrations with automated versioning and environment detection
- **Integration Pattern**: Agno framework storage abstractions with mode-specific configurations
- **Performance Strategy**: Connection pooling, vector indexing, and optimized query patterns
- **Quality Standards**: Database health checks, migration validation, and performance monitoring

## Key Component Structure

### Database Schema (`db/tables/`)
- **base.py** - SQLAlchemy declarative base and database engine configuration
- **agents.py** - Agent configuration storage with version management and active state tracking
- **teams.py** - Team composition and routing logic with member position management
- **knowledge_base.py** - Knowledge storage with PgVector embeddings for similarity search
- **monitoring.py** - Performance metrics and routing decision tracking

### Migration System (`db/migrations/`)
- **env.py** - Alembic environment configuration with automatic schema detection  
- **versions/** - Database schema migrations with PostgreSQL and SQLite compatibility
- **alembic.ini** - Migration configuration with environment-specific database URLs

### Storage Integration (`db/storage/`)
- **postgres_config.py** - PostgreSQL connection management with Agno storage abstractions
- **sqlite_fallback.py** - SQLite automatic fallback for development environments
- **session_manager.py** - Database session lifecycle and connection pooling

## Implementation Highlights

### Dual Database Architecture
- **PostgreSQL Production**: Primary database with PgVector extension for vector similarity search
- **SQLite Development**: Automatic fallback for zero-configuration development environments
- **Environment Detection**: Seamless switching based on DATABASE_URL environment variable
- **Schema Compatibility**: Unified schema design supporting both database engines

### Vector Similarity Search
- **PgVector Integration**: 1536-dimension embeddings for knowledge base similarity matching
- **Optimized Indexing**: IVFFlat indexes for fast vector distance calculations  
- **Domain Filtering**: Combined vector search with categorical filtering for accuracy
- **Performance Tuning**: Connection pooling and query optimization for production workloads

### Agno Framework Integration
- **Storage Abstractions**: Built-in PostgreSQL and SQLite storage with automatic table creation
- **Session Management**: Automatic session lifecycle with metadata persistence and retrieval
- **Schema Versioning**: Automated schema upgrades with version detection and migration
- **Mode Configuration**: Agent, team, and workflow storage modes with specialized schemas

## Critical Implementation Details

### Database Configuration Pattern
**Dual Database Detection**: Automatic PostgreSQL/SQLite selection based on environment

```python
# Database configuration with automatic fallback
import os
from sqlalchemy import create_engine
from agno.storage.postgres import PostgresStorage
from agno.storage.sqlite import SqliteStorage

def get_database_storage(table_name: str = "automagik_sessions") -> Union[PostgresStorage, SqliteStorage]:
    """
    Get appropriate storage based on environment configuration.
    Falls back to SQLite if PostgreSQL is not available.
    """
    db_url = os.getenv("DATABASE_URL")
    
    if db_url and "postgresql" in db_url:
        # PostgreSQL with Agno's built-in abstractions
        return PostgresStorage(
            table_name=table_name,
            db_url=db_url,
            auto_upgrade_schema=True,
            mode="team"  # Support multi-agent team storage
        )
    else:
        # SQLite fallback for development
        return SqliteStorage(
            table_name=table_name,
            auto_upgrade_schema=True,
            mode="team"
        )
```

### Vector Search Implementation  
**PgVector Knowledge Retrieval**: Optimized similarity search with domain filtering

```python
# Vector similarity search with categorical filtering
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Session

def search_knowledge_with_vector(
    db: Session, 
    query_embedding: List[float], 
    domain: str, 
    limit: int = 5
) -> List[KnowledgeBase]:
    """
    Search knowledge base using vector similarity with domain filtering.
    Combines semantic search with categorical precision.
    """
    return db.query(KnowledgeBase)\
        .filter(KnowledgeBase.domain == domain)\
        .order_by(KnowledgeBase.embedding.l2_distance(query_embedding))\
        .limit(limit)\
        .options(defer(KnowledgeBase.embedding))  # Optimize query performance
```

### Migration Strategy
**Environment-Specific Schema Management**: Alembic integration with automatic deployment

```python
# Migration with environment detection and PostgreSQL extension management
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

def upgrade():
    """
    Apply database migrations with PostgreSQL/SQLite compatibility.
    Automatically handles PgVector extension and index creation.
    """
    # Check if PostgreSQL and enable vector extension
    bind = op.get_bind()
    if "postgresql" in str(bind.dialect):
        op.execute('CREATE EXTENSION IF NOT EXISTS vector')
        
        # Create knowledge base with vector support
        op.create_table('knowledge_base',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('domain', sa.String(50), nullable=False),
            sa.Column('question', sa.Text(), nullable=False),
            sa.Column('answer', sa.Text(), nullable=False),
            sa.Column('embedding', Vector(1536)),  # OpenAI embedding dimensions
            sa.Column('created_at', sa.DateTime(), default=sa.func.now())
        )
        
        # Create optimized vector index
        op.create_index('idx_embedding', 'knowledge_base', ['embedding'], 
                        postgresql_using='ivfflat', postgresql_with={'lists': 100})
    else:
        # SQLite-compatible schema without vector support
        op.create_table('knowledge_base',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('domain', sa.String(50), nullable=False),
            sa.Column('question', sa.Text(), nullable=False),
            sa.Column('answer', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), default=sa.func.now())
        )
```

## Development Notes

### Current Challenges
- **Vector Index Optimization**: Tuning IVFFlat parameters for optimal query performance across knowledge base sizes
- **Schema Evolution**: Managing database schema changes across PostgreSQL and SQLite with unified migration scripts

### Future Considerations  
- **Horizontal Scaling**: Implementing read replicas and connection pooling for high-traffic production environments
- **Vector Search Enhancement**: Exploring HNSW indexes and advanced similarity algorithms for improved knowledge retrieval

### Performance Metrics
- **Connection Pool Utilization**: Monitoring active connections and optimizing pool size based on concurrent agent usage
- **Vector Query Performance**: Tracking similarity search response times and optimizing embedding index parameters

---

*This component documentation provides context for AI-assisted development within the Database Layer. For system-wide patterns and standards, reference the master CLAUDE.md file.*

## Essential Development Commands

### Database Setup and Migration
```bash
# Initialize PostgreSQL with PgVector (production)
export DATABASE_URL="postgresql://ai:ai@localhost:5532/ai"
uv run alembic -c db/alembic.ini upgrade head

# Development (SQLite fallback - zero configuration)
uv run python api/playground.py  # Automatic SQLite initialization

# Generate new migration
uv run alembic -c db/alembic.ini revision --autogenerate -m "Add feature tables"

# Database health check
uv run python -c "from config.database import health_check; print(health_check())"
```

### Agno Storage Patterns
```python
# Essential storage configuration for Automagik Multi-Agent Framework
from agno.storage.postgres import PostgresStorage
from agno.storage.sqlite import SqliteStorage

# Production PostgreSQL with automatic fallback
storage = PostgresStorage(
    table_name="automagik_sessions",
    db_url=os.getenv("DATABASE_URL"),
    auto_upgrade_schema=True,
    mode="team"  # Multi-agent team support
) if os.getenv("DATABASE_URL") else SqliteStorage(
    table_name="automagik_sessions",
    auto_upgrade_schema=True,
    mode="team"
)
```


