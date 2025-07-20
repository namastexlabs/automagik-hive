# Database Architecture - Clean Slate Implementation

## Overview

Clean database architecture with proper separation:
- **agno schema**: Agno framework tables (agents, teams, workflows, knowledge, memory)
- **hive schema**: Custom business logic (component_versions, version_history, agent_metrics)

## Schema Separation

### Agno Schema (`agno`)
All Agno framework components now use `schema="agno"`:
- PostgresStorage instances
- PostgresMemoryDb instances  
- PgVector instances
- CSVKnowledgeBase storage

### Hive Schema (`hive`)
Custom business logic with proper models:
- `component_versions` - Component configuration and versioning
- `version_history` - Audit trail for version changes
- `agent_metrics` - Agent execution metrics

## Database Services

### Clean Implementation
- **DatabaseService**: Base psycopg3 service with connection pooling
- **ComponentVersionService**: Replaces AgnoVersionService hack
- **MetricsService**: Replaces direct SQL table creation

### Drop-in Compatibility
- **AgnoVersionService**: Now uses ComponentVersionService internally
- **PostgresMetricsStorage**: Now uses MetricsService internally

## Migration Setup

### Alembic Configuration
- Configured for `hive` schema only
- Async support with psycopg3
- Auto-formatting with ruff
- Environment variable integration

### Initial Migration
File: `alembic/versions/db3d380b41d9_initial_hive_schema_with_component_.py`
- Creates hive schema
- Creates all 3 business tables with proper indexes
- Supports rollback with CASCADE cleanup

## Testing Fresh Container Startup

### Prerequisites
1. **Database URL**: `HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive`
2. **Clean slate**: Wipe existing container and database

### Expected Behavior
1. **Agno schema creation**: Automatic via `schema="agno"` parameter
2. **Hive schema creation**: Automatic via Alembic env.py
3. **Table creation**: 
   - Agno tables in `agno` schema
   - Business tables in `hive` schema via migration
4. **Service initialization**: All services use correct schemas

### Verification Commands
```bash
# Run migration
uv run alembic upgrade head

# Check schema creation
psql -c "\dn" 

# Check table ownership
psql -c "\dt agno.*"
psql -c "\dt hive.*"
```

## Architecture Benefits

1. **Clean Separation**: Framework vs business logic
2. **Proper Models**: SQLAlchemy models instead of raw SQL
3. **Connection Pooling**: Async psycopg3 with proper pooling
4. **Migration Support**: Alembic for business schema evolution
5. **Drop-in Compatibility**: No breaking changes to existing code

## Environment Variables

Single database URL for both schemas:
```bash
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@host:port/database
```

Both schemas use the same connection but are logically separated.