# PGlite Migration Guide

## Overview

Automagik Hive has migrated to **PGlite as the default database backend**, eliminating Docker as a hard requirement and significantly simplifying the installation and development experience.

### What Changed

**Before (v0.1.x):**
- PostgreSQL with Docker was required
- Docker setup was mandatory for all users
- Complex Docker compose orchestration
- Longer startup times

**Now (v0.2.0+):**
- PGlite is the default (no Docker needed)
- Three backend options: PGlite, SQLite, PostgreSQL
- Docker is optional (only for PostgreSQL)
- Faster installation and startup
- Browser-compatible database engine

### Why PGlite?

**PGlite** is a WebAssembly-based PostgreSQL engine that runs without Docker:
- ✅ **No Docker Required** - Pure Python/WebAssembly solution
- ✅ **Full PostgreSQL Compatibility** - Same SQL, same features
- ✅ **Fast Startup** - No container orchestration overhead
- ✅ **Browser-Compatible** - Can run in web environments
- ✅ **Simple Installation** - Single command setup
- ✅ **Development-Friendly** - Hot reload, easy debugging

## Backend Options

Automagik Hive supports three database backends:

### 1. PGlite (Default - Recommended)

**Best For:** Development, prototyping, small-to-medium deployments

**Advantages:**
- No Docker required
- Fast installation and startup
- Full PostgreSQL feature compatibility
- Browser-compatible for future web deployment
- Simple file-based storage

**Installation:**
```bash
# Default installation uses PGlite
make install

# Or explicit PGlite installation
make install-pglite
```

**Environment Configuration:**
```bash
HIVE_DATABASE_BACKEND=pglite
HIVE_DATABASE_URL=pglite://./data/automagik_hive.db
```

### 2. SQLite (Development/Testing Only)

⚠️ **CRITICAL LIMITATION**: SQLite backend **CANNOT persist agent sessions or user memory** due to Agno Framework's PostgreSQL-specific storage requirements. Use only for development/testing without memory needs.

**Best For:** Development testing, CI/CD pipelines (stateless agents only)

**What Works:**
- ✅ Database CRUD operations
- ✅ Knowledge base queries (without PgVector embeddings)
- ✅ Agent responses (stateless mode)
- ✅ Tool execution
- ✅ API endpoints

**What DOESN'T Work:**
- ❌ **Agent memory** (user context forgotten between requests)
- ❌ **Session persistence** (conversation history not saved)
- ❌ **Multi-turn conversations** (no context retention)
- ❌ **User preferences** (settings not persisted)
- ❌ **PgVector embeddings** (vector search unavailable)

**Limitations:**
- No agent session/memory support (Agno Framework incompatibility - Issue #77)
- No concurrent write support
- Limited vector search performance vs PostgreSQL
- No advanced PostgreSQL features

**Recommendation:** **Use PGlite instead** for development with full agent memory support.

**Installation:**
```bash
make install-sqlite
```

**Environment Configuration:**
```bash
HIVE_DATABASE_BACKEND=sqlite
HIVE_DATABASE_URL=sqlite:///./data/automagik_hive.db
```

### 3. PostgreSQL (Optional)

**Best For:** Production deployments, high concurrency, advanced features

**Advantages:**
- Production-grade reliability
- Best concurrent write performance
- Advanced indexing (HNSW, IVFFlat)
- Full pgvector optimization

**Requirements:**
- Docker and Docker Compose installed
- Additional setup complexity

**Installation:**
```bash
make install-postgres
```

**Environment Configuration:**
```bash
HIVE_DATABASE_BACKEND=postgresql
HIVE_DATABASE_URL=postgresql+psycopg://user:password@localhost:5532/hive
```

## Migration Paths

### For New Users

**Just install and go - PGlite is the default:**

```bash
# Clone repository
git clone https://github.com/namastexlabs/automagik-hive.git
cd automagik-hive

# Install (defaults to PGlite)
make install

# Start development server
make dev
```

That's it! No Docker setup, no complex configuration.

### For Existing PostgreSQL Users

You have two options:

#### Option A: Stay on PostgreSQL (Recommended for Production)

If you're already using PostgreSQL and Docker, you can continue without changes:

1. **Keep your existing `.env` configuration**
   ```bash
   HIVE_DATABASE_BACKEND=postgresql
   HIVE_DATABASE_URL=postgresql+psycopg://user:password@localhost:5532/hive
   ```

2. **Continue using Docker commands**
   ```bash
   make postgres-start  # Start PostgreSQL
   make dev             # Start development server
   ```

3. **Your data and workflows remain unchanged**

#### Option B: Migrate to PGlite (Simpler Development)

If you want to eliminate Docker for development:

**Step 1: Backup Your Data (Optional)**
```bash
# Export your knowledge base
cp lib/knowledge/knowledge_rag.csv ~/backup/

# Export environment configuration
cp .env ~/backup/
```

**Step 2: Update Backend Configuration**
```bash
# Edit .env file
HIVE_DATABASE_BACKEND=pglite
HIVE_DATABASE_URL=pglite://./data/automagik_hive.db
```

**Step 3: Stop PostgreSQL Container**
```bash
make postgres-stop
```

**Step 4: Restart with PGlite**
```bash
make dev
```

**Step 5: Verify Migration**
```bash
# Check health endpoint
curl http://localhost:8886/api/v1/health

# Test agent functionality
curl -X POST http://localhost:8886/agents/your-agent/run \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{"message": "test"}'
```

**Notes:**
- Schema migrations run automatically on startup
- Vector embeddings will regenerate from CSV files
- Session history starts fresh (previous sessions lost)
- Agent configurations remain unchanged

### Migrating from PostgreSQL to SQLite

For minimal dependency environments:

**Step 1: Update Configuration**
```bash
# Edit .env
HIVE_DATABASE_BACKEND=sqlite
HIVE_DATABASE_URL=sqlite:///./data/automagik_hive.db
```

**Step 2: Restart**
```bash
make postgres-stop  # Stop PostgreSQL
make dev            # Start with SQLite
```

**Limitations to Consider:**
- No concurrent write support
- Vector search performance may be slower
- Limited to single-node deployments

## Installation Instructions

### Quick Installation (PGlite - Recommended)

```bash
# One-command setup
make install

# Or explicit PGlite
make install-pglite

# Start development
make dev
```

### SQLite Installation

```bash
# Simple file-based database
make install-sqlite

# Start development
make dev
```

### PostgreSQL Installation (Docker Required)

**Prerequisites:**
- Docker 20.10+
- Docker Compose 2.0+

**Installation:**
```bash
# Install with PostgreSQL
make install-postgres

# This will:
# 1. Check for Docker
# 2. Generate secure credentials
# 3. Start PostgreSQL container
# 4. Configure application

# Start development
make dev
```

### Using CLI Backend Flag

The Automagik Hive CLI supports a `--backend` flag:

```bash
# Install with specific backend
automagik-hive install --backend pglite
automagik-hive install --backend sqlite
automagik-hive install --backend postgresql

# The flag sets HIVE_DATABASE_BACKEND and updates .env
```

## Configuration

### Environment Variables

**Backend Selection:**
```bash
# Primary backend configuration
HIVE_DATABASE_BACKEND=pglite|sqlite|postgresql

# Database URL (auto-configured during install)
HIVE_DATABASE_URL=<backend-specific-url>
```

### .env.example Updates

The `.env.example` file now includes:

```bash
# Database backend type (auto-generated during install)
# Options: pglite, sqlite, postgresql
# - pglite: WebAssembly PostgreSQL bridge (RECOMMENDED - no Docker needed)
# - sqlite: Simple file-based database (minimal dependencies)
# - postgresql: Full PostgreSQL with Docker (requires Docker installation)
HIVE_DATABASE_BACKEND=pglite

# Connection URL for local development
# PGlite example (RECOMMENDED - no Docker required):
HIVE_DATABASE_URL=pglite://./data/automagik_hive.db
# SQLite example (alternative - no Docker required):
# HIVE_DATABASE_URL=sqlite:///./data/automagik_hive.db
# PostgreSQL example (optional - requires Docker):
# HIVE_DATABASE_URL=postgresql+psycopg://hive_user:password@localhost:5532/hive
```

### Database URL Formats

**PGlite:**
```bash
pglite://./data/automagik_hive.db
pglite:///absolute/path/to/database.db
```

**SQLite:**
```bash
sqlite:///./data/automagik_hive.db
sqlite:////absolute/path/to/database.db
```

**PostgreSQL:**
```bash
postgresql+psycopg://user:password@localhost:5532/database
postgresql+psycopg://user:password@host:port/database?sslmode=require
```

## Troubleshooting

### Common Migration Issues

#### Docker Still Starting

**Problem:** Docker containers start even after switching to PGlite/SQLite

**Solution:**
```bash
# Stop all Docker services
make postgres-stop

# Verify backend in .env
grep HIVE_DATABASE_BACKEND .env
# Should show: HIVE_DATABASE_BACKEND=pglite

# Clean start
make dev
```

#### Database Connection Errors

**Problem:** `Connection refused` or `Database not found`

**Solution:**
```bash
# Check backend configuration
cat .env | grep HIVE_DATABASE

# For PGlite/SQLite - ensure data directory exists
mkdir -p data

# For PostgreSQL - check Docker status
make postgres-status

# Restart application
make dev
```

#### Schema Compatibility Issues

**Problem:** `Table does not exist` or schema mismatch errors

**Solution:**
```bash
# Remove database file and restart (PGlite/SQLite)
rm -f data/automagik_hive.db
make dev

# For PostgreSQL - check migrations
make postgres-logs
```

#### PGlite Bridge Not Found

**Problem:** `pglite-bridge not found` or bridge startup failures

**Solution:**
```bash
# Verify pglite-bridge installation
ls -la lib/database/pglite/bridge/

# Reinstall dependencies
uv sync

# Check bridge server logs
make dev  # Bridge errors appear in startup logs
```

#### Mixed Backend State

**Problem:** Application using wrong backend or credentials

**Solution:**
```bash
# Clean environment
make clean

# Regenerate .env from example
rm .env
cp .env.example .env

# Reinstall with desired backend
make install-pglite  # or install-sqlite, install-postgres

# Verify configuration
cat .env | grep -E "(BACKEND|DATABASE_URL)"
```

### Performance Issues

#### Slow Knowledge Base Loading

**PGlite/SQLite:**
- Initial embedding generation takes time
- Subsequent loads use cached embeddings
- Large CSV files (>10K rows) may be slow

**PostgreSQL:**
- HNSW indexing provides best performance
- Use PostgreSQL for large knowledge bases

#### Concurrent Access Errors

**SQLite Only:**
- SQLite locks on concurrent writes
- Switch to PGlite or PostgreSQL for concurrent access

**Solution:**
```bash
# Upgrade to PGlite
make install-pglite

# Or PostgreSQL for production
make install-postgres
```

### Data Recovery

#### Recovering PostgreSQL Data

If you migrated away from PostgreSQL but need old data:

```bash
# Restart PostgreSQL container
make postgres-start

# Access PostgreSQL directly
docker exec -it hive-postgres psql -U <user> -d hive

# Export specific tables
docker exec -it hive-postgres pg_dump -U <user> -d hive -t agno.knowledge_base > backup.sql

# Switch back to PostgreSQL backend
sed -i 's/^HIVE_DATABASE_BACKEND=.*/HIVE_DATABASE_BACKEND=postgresql/' .env

# Restart
make dev
```

#### CSV Knowledge Base Backup

Always maintain CSV backups:

```bash
# Backup knowledge base
cp lib/knowledge/knowledge_rag.csv ~/backups/knowledge_$(date +%Y%m%d).csv

# Restore knowledge base
cp ~/backups/knowledge_YYYYMMDD.csv lib/knowledge/knowledge_rag.csv
make dev  # Re-embedding happens automatically
```

### Debug Mode

Enable verbose logging to diagnose issues:

```bash
# In .env
HIVE_LOG_LEVEL=DEBUG

# Restart and monitor logs
make dev
```

### Getting Help

If migration issues persist:

1. **Check Logs:**
   ```bash
   make dev  # Observe startup logs
   make postgres-logs  # PostgreSQL-specific logs
   ```

2. **Verify Prerequisites:**
   ```bash
   # Python version
   python --version  # Should be 3.12+

   # Docker (for PostgreSQL only)
   docker --version
   docker compose version
   ```

3. **Community Support:**
   - GitHub Issues: https://github.com/namastexlabs/automagik-hive/issues
   - Discord: https://discord.gg/xcW8c7fF3R
   - Documentation: https://deepwiki.com/namastexlabs/automagik-hive

4. **Clean Install:**
   ```bash
   # Last resort - complete uninstall and reinstall
   make uninstall
   make clean
   make install-pglite
   ```

## FAQ

### Is PGlite production-ready?

**Development/Staging:** Yes, PGlite is excellent for development and staging environments.

**Production:** For high-concurrency production deployments, PostgreSQL is still recommended. PGlite works well for:
- Small-to-medium user bases
- Single-node deployments
- Development/testing environments
- Proof-of-concept projects

### Can I switch backends later?

Yes! Backend switching is designed to be seamless:

1. Update `HIVE_DATABASE_BACKEND` and `HIVE_DATABASE_URL` in `.env`
2. Restart the application
3. Schema migrations run automatically
4. Knowledge base re-embeds from CSV

**Note:** Session history and runtime data will not transfer between backends.

### Do I need to migrate existing data?

**For configuration and knowledge:**
- Agent/team/workflow YAML configs work unchanged
- CSV knowledge bases work across all backends
- Environment variables remain compatible

**For runtime data:**
- Session history does not transfer
- Agent memory is backend-specific
- Start fresh or export/import if needed

### Will my Docker setup still work?

Yes! If you prefer Docker and PostgreSQL:

1. Keep `HIVE_DATABASE_BACKEND=postgresql` in `.env`
2. Continue using Docker compose commands
3. No changes required to your workflow

Docker is still fully supported for PostgreSQL users.

### What about performance?

**PGlite:**
- Fast for most workloads
- Optimized for single-node
- Good vector search performance

**SQLite:**
- Fastest for small datasets
- Limited concurrent access
- Sufficient for testing/development

**PostgreSQL:**
- Best for production
- Optimal concurrent access
- Advanced indexing (HNSW, IVFFlat)
- Recommended for >1000 users

### Can I use PGlite in Docker?

Yes! PGlite works inside Docker containers:

```dockerfile
# Dockerfile
FROM python:3.12-slim
RUN pip install automagik-hive
ENV HIVE_DATABASE_BACKEND=pglite
ENV HIVE_DATABASE_URL=pglite://./data/hive.db
CMD ["automagik-hive", "dev"]
```

This gives you containerization benefits without Docker Compose orchestration.

### How do I upgrade from older versions?

**From v0.1.x to v0.2.0+:**

```bash
# Update repository
git pull origin main

# Reinstall dependencies
uv sync

# Choose your backend
make install-pglite  # or install-sqlite, install-postgres

# Start fresh
make dev
```

Schema compatibility is maintained, but runtime data may need migration.

## Summary

The PGlite migration makes Automagik Hive:
- **Simpler** - No Docker requirement
- **Faster** - Quick installation and startup
- **Flexible** - Three backend options
- **Backward Compatible** - PostgreSQL still works

Choose the backend that fits your needs:
- **PGlite** - Development, prototyping (recommended)
- **SQLite** - Minimal dependencies, embedded use
- **PostgreSQL** - Production, high concurrency

Docker is now **optional**, only required for PostgreSQL backend users.

---

**Next Steps:**
- [Installation Guide](../README.md#-quick-start)
- [Docker Documentation](../docker/README.md)
- [Development Guide](../CLAUDE.md)
