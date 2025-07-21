# Database Migrations - Automatic Startup Implementation

This document describes the implementation of automatic database migrations in the Automagik Hive system.

## Overview

The system now automatically runs Alembic migrations on application startup, ensuring the database schema is always up-to-date without manual intervention.

## Architecture

### Hybrid Database Strategy

The system uses a **hybrid approach** combining the best of both worlds:

| **Component** | **Technology** | **Purpose** |
|---------------|----------------|-------------|
| **Runtime Operations** | Pure psycopg3 | Fast, direct database control |
| **Schema Management** | SQLAlchemy Models | Alembic migration compatibility |
| **Migration Tool** | Alembic | Professional schema versioning |

### Schema Organization

- **`agno` schema**: Agno framework native components (PgVector, memory, agents)
- **`hive` schema**: Custom business logic (metrics, versioning, components)

## Implementation Details

### 1. Migration Service (`lib/services/migration_service.py`)

**Key Features:**
- ✅ Async-compatible integration with FastAPI
- ✅ Proper error handling and logging
- ✅ Environment-aware behavior (dev vs production)
- ✅ Integration with existing psycopg3 patterns
- ✅ Thread-safe execution of sync Alembic operations

**Core Methods:**
```python
# Check if migrations are needed
await migration_service.check_migration_status()

# Run migrations to latest
await migration_service.run_migrations() 

# Ensure database is ready (check + migrate if needed)
await migration_service.ensure_database_ready()
```

### 2. Startup Integration (`api/serve.py`)

**Integration Point:** Line 169, right after database initialization comment

**Behavior:**
- **Development**: Runs migrations with warnings on failure
- **Production**: Fails fast if migrations fail
- **Error Handling**: Graceful degradation with proper logging

### 3. Startup Display (`lib/utils/startup_display.py`)

**Enhanced Features:**
- ✅ Migration status display in startup table
- ✅ Success/failure indicators
- ✅ Current revision display
- ✅ Error message display for failures

## Usage

### Automatic Execution

Migrations run automatically when the application starts. No manual intervention required.

**Startup Output Example:**
```
🔧 Database Migration Status:
  ✅ Up to date - Revision: db3d380b

🚀 Automagik Hive System Status
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Type          ┃ ID                            ┃ Name                                     ┃ Version      ┃ Status    ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ 🏢 Team       │ ana                           │ Ana - Enterprise Analysis Team           │ v6           │ ✅         │
└───────────────┴───────────────────────────────┴──────────────────────────────────────────┴──────────────┴───────────┘
```

### Manual Testing

Test migrations independently:
```bash
# Test migration service
python scripts/test_migrations.py

# Or run Alembic manually
alembic upgrade head
alembic current
alembic history
```

### Environment Configuration

**Required Environment Variable:**
```bash
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@host:port/dbname
```

**Optional Environment Variables:**
```bash
HIVE_ENVIRONMENT=production  # Controls failure behavior
```

## Error Handling

### Development Mode
- ⚠️ **Warns** on migration failures
- ✅ **Continues** application startup 
- 📝 **Logs** detailed error information

### Production Mode  
- ❌ **Fails fast** on migration failures
- 🛑 **Stops** application startup
- 🚨 **Raises** ComponentLoadingError

### Error Types

| **Error** | **Cause** | **Resolution** |
|-----------|-----------|----------------|
| `HIVE_DATABASE_URL not set` | Missing environment variable | Set database URL |
| `Alembic config not found` | Missing alembic.ini | Check project structure |
| `Migration execution failed` | Database connectivity/permissions | Check database access |
| `Schema version conflict` | Manual database changes | Review and resolve conflicts |

## Integration with Existing Systems

### ✅ Compatible Components
- **Database Service**: Uses same psycopg3 connection patterns
- **Logging System**: Integrates with unified Loguru logging
- **Startup Display**: Shows migration status in system table
- **Error Handling**: Uses existing ComponentLoadingError patterns

### ✅ Schema Management
- **Alembic Migrations**: Professional database versioning
- **Schema Isolation**: Proper `hive` vs `agno` schema separation
- **Version Tracking**: Automatic migration version management

## Files Modified/Created

### New Files
- `lib/services/migration_service.py` - Core migration service
- `scripts/test_migrations.py` - Migration testing script
- `docs/database-migrations.md` - This documentation

### Modified Files
- `api/serve.py` - Added migration integration to startup
- `lib/utils/startup_display.py` - Added migration status display

## Migration Development Workflow

### Creating New Migrations
```bash
# Generate new migration
alembic revision --autogenerate -m "Description of changes"

# Review generated migration file
vim alembic/versions/[hash]_description.py

# Test migration
alembic upgrade head
```

### Schema Changes
1. Update SQLAlchemy models in `lib/models/`
2. Generate migration: `alembic revision --autogenerate`
3. Review and test migration
4. Commit both model and migration files

## Best Practices

### ✅ Do's
- Always review auto-generated migrations
- Use descriptive migration messages
- Test migrations on staging before production
- Keep migrations small and focused
- Use transactions for complex migrations

### ❌ Don'ts  
- Don't edit existing migration files after deployment
- Don't skip migration testing
- Don't make manual database schema changes
- Don't mix data changes with schema changes

## Troubleshooting

### Common Issues

**Migration Fails on Startup:**
```bash
# Check database connectivity
psql $HIVE_DATABASE_URL -c "SELECT 1;"

# Check current migration status
alembic current

# Check pending migrations
alembic heads
```

**Schema Conflicts:**
```bash
# Reset migration tracking (dangerous!)
alembic stamp head

# Or resolve conflicts manually
alembic history --verbose
```

### Debug Mode
Enable detailed migration logging by setting environment variable:
```bash
ALEMBIC_LOG_LEVEL=DEBUG
```

## Future Enhancements

### Planned Features
- [ ] Migration rollback support
- [ ] Database backup before migrations
- [ ] Migration dry-run mode
- [ ] Multiple environment migration configs
- [ ] Migration performance monitoring

### Considerations
- **Backup Strategy**: Consider automated backups before migrations
- **Zero-Downtime**: Plan for zero-downtime migration strategies
- **Monitoring**: Add migration performance metrics
- **Alerting**: Integration with notification systems for failures

## Conclusion

The automatic migration system provides:
- ✅ **Zero-configuration** database schema management  
- ✅ **Production-ready** error handling and logging
- ✅ **Developer-friendly** startup integration
- ✅ **Enterprise-grade** migration versioning

This implementation ensures database schemas stay synchronized across all environments while maintaining the project's clean architecture principles.