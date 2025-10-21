# 🧞 PGLITE MIGRATION - DROP DOCKER COMPLEXITY FOR NATIVE DEVELOPMENT

**Status:** READY_FOR_REVIEW
**Branch:** wish/pglite-migration
**Issue:** #72

## Executive Summary
Replace Docker-based PostgreSQL setup with PGlite (WebAssembly PostgreSQL) to eliminate Docker as a development dependency while maintaining full PostgreSQL + pgvector compatibility and preserving Docker option for production cloud deployments.

## Current State Analysis
**What exists:**
- Docker PostgreSQL container managed via `docker-compose.yml`
- ~500 lines of Docker orchestration across Makefile + scripts
- PostgreSQL credential extraction via bash scripts
- Docker detection and validation in installation flow
- PostgreSQL port mapping (5532 → 5432)
- Docker-based production deployment

**Gap identified:**
- Docker dependency creates onboarding friction
- 16 RC iterations fixing installation issues
- Silent PostgreSQL setup failures
- Complex credential management across multiple files
- Large installation footprint (Docker Desktop 500MB+)
- Permission management complexity (UID/GID mapping)

**Solution approach:**
- Implement pluggable database backend system
- Create lightweight Node.js PGlite bridge server
- Remove Docker orchestration code from development path
- Keep simplified Docker option for cloud deployments only
- Maintain PostgreSQL wire protocol compatibility

## Change Isolation Strategy
- **Isolation principle:** Backend factory pattern with provider swapping
- **Extension pattern:** Add PGlite provider alongside existing PostgreSQL/SQLite
- **Stability assurance:**
  - Default behavior preserves PostgreSQL connection string format
  - Docker deployment path remains available via separate flag
  - Existing `.env` credentials work unchanged
  - Zero impact on production cloud deployments

## Success Criteria
✅ `make install` completes without Docker requirement
✅ `make dev` starts PGlite bridge + FastAPI in <10 seconds
✅ Full pgvector extension support working
✅ Database URL format unchanged (`postgresql+psycopg://...`)
✅ Docker option available via `--use-docker` flag for cloud
✅ Codebase reduced by ~500 lines (Docker scripts removed)
✅ Installation works on Windows/Mac/Linux without Docker
✅ Existing `.env` files migrate cleanly

## Never Do (Protection Boundaries)
❌ Remove PostgreSQL support entirely (cloud needs it)
❌ Break existing database connection strings
❌ Hardcode PGlite as only option (keep pluggable)
❌ Leave Docker remnants in default development flow
❌ Skip migration path for existing installations
❌ Introduce Node.js as hard Python dependency

## Technical Architecture

### Component Structure
```
PGlite Bridge (New):
├── tools/pglite-bridge/
│   ├── server.js              # PostgreSQL wire protocol proxy
│   ├── package.json           # PGlite + pg dependencies
│   ├── start.sh               # Bridge startup script
│   └── README.md              # Bridge documentation

Database Abstraction (New):
├── lib/database/
│   ├── __init__.py            # Backend factory exports
│   ├── backend_factory.py     # Pluggable backend system
│   └── providers/
│       ├── __init__.py
│       ├── pglite.py          # PGlite connection provider
│       ├── postgresql.py      # Native PostgreSQL provider
│       └── sqlite.py          # SQLite fallback provider

CLI Integration (Modified):
├── cli/core/main_service.py   # Add PGlite bridge lifecycle
├── cli/commands/service.py    # Remove Docker detection
├── cli/commands/postgres.py   # Add backend selection logic
└── cli/main.py                # Update help text

Configuration (Modified):
├── .env.example               # Add HIVE_DATABASE_BACKEND
├── lib/config/settings.py     # Backend selection setting
└── Makefile                   # Replace Docker with PGlite setup

Docker Removal (Deleted):
├── docker/main/extract_db_credentials.sh  # 26 lines removed
├── docker/scripts/validate.sh             # Docker validation removed
├── Makefile                                # ~100 lines of Docker setup removed
└── docker/main/docker-compose.yml         # PostgreSQL service removed

Docker Cloud (Kept):
└── docker/cloud/              # Simplified cloud deployment only
    └── docker-compose.yml     # App-only container → managed PostgreSQL
```

### Naming Conventions
- Backend providers: `{Provider}Backend` classes in `lib/database/providers/{provider}.py`
- CLI commands: `{Feature}Commands` in `cli/commands/{feature}.py`
- Configuration settings: `hive_database_backend` in `.env`
- Bridge scripts: kebab-case in `tools/pglite-bridge/`
- Tests: `test_pglite_*.py` in `tests/lib/database/`

## Task Decomposition

### Dependency Graph
```
A[Backend Abstraction] ---> B[PGlite Bridge]
A ---> C[Provider Implementation]
B & C ---> D[CLI Integration]
D ---> E[Docker Removal]
E ---> F[Testing & Documentation]
```

### Group A: Backend Abstraction (Parallel Tasks)
Dependencies: None | Execute simultaneously

**A1-backend-factory**: Create pluggable database backend system
@lib/config/settings.py [context] @lib/database/ [creates]
Creates: `lib/database/backend_factory.py` with provider detection logic
Exports: `get_database_backend()` factory selecting PGlite/PostgreSQL/SQLite
Success: Factory loads without errors, can detect backend from URL format.

**A2-provider-interface**: Define backend provider contract
@lib/database/providers/ [creates]
Creates: `lib/database/providers/base.py` with `BaseDatabaseBackend` ABC
Exports: Abstract methods `start()`, `stop()`, `health_check()`, `get_connection_url()`
Success: Interface documented with type hints and docstrings.

**A3-settings-extension**: Add backend selection configuration
@lib/config/settings.py [context]
Modifies: Add `hive_database_backend` field (pglite|postgresql|sqlite)
Exports: Validated enum field with default detection from `HIVE_DATABASE_URL`
Success: Settings load with backend selection validated.

### Group B: PGlite Bridge (After A2)
Dependencies: A2-provider-interface

**B1-pglite-server**: Implement Node.js PostgreSQL wire protocol bridge
@tools/pglite-bridge/ [creates]
Creates: `tools/pglite-bridge/server.js` with PGlite → PostgreSQL wire proxy
Dependencies: `@electric-sql/pglite`, `pg`, `pgvector` npm packages
Exports: HTTP server on port 5532 mimicking PostgreSQL wire protocol
Success: Bridge accepts psycopg connections and executes queries via PGlite.

**B2-bridge-lifecycle**: Create bridge startup/shutdown scripts
@tools/pglite-bridge/ [creates]
Creates: `start.sh`, `stop.sh`, `health.sh` bash helpers
Exports: Scripts callable from Python subprocess
Success: Scripts tested on Linux/Mac/WSL with proper exit codes.

**B3-npm-integration**: Configure Node.js package management
@tools/pglite-bridge/ [creates]
Creates: `package.json` with PGlite 0.2.x dependencies
Exports: `npm install` produces working node_modules
Success: `npm install && node server.js` starts bridge successfully.

### Group C: Provider Implementation (After A2, B1)
Dependencies: A2-provider-interface, B1-pglite-server

**C1-pglite-provider**: Implement PGlite backend provider
@lib/database/providers/pglite.py [creates] @lib/database/providers/base.py [context]
Creates: `PGliteBackend` class managing bridge lifecycle
Exports: Methods to start/stop bridge subprocess, check health
Success: Provider starts bridge, returns working connection URL.

**C2-postgresql-provider**: Extract existing PostgreSQL logic
@lib/database/providers/postgresql.py [creates] @cli/core/postgres_service.py [context]
Creates: `PostgreSQLBackend` wrapping existing Docker/native Postgres
Exports: Compatible interface with current Docker-based setup
Success: Existing PostgreSQL workflows unchanged.

**C3-sqlite-provider**: Create SQLite fallback provider
@lib/database/providers/sqlite.py [creates]
Creates: `SQLiteBackend` for environments without Node.js/Docker
Exports: File-based SQLite connection for testing/CI
Success: SQLite provider returns working connection string.

### Group D: CLI Integration (After A1, C1)
Dependencies: A1-backend-factory, C1-pglite-provider

**D1-service-manager**: Wire backend selection into CLI
@cli/core/main_service.py [context]
Modifies: Replace Docker Postgres calls with `backend_factory.start()`
Success: `make dev` starts appropriate backend based on settings.

**D2-postgres-commands**: Update PostgreSQL CLI commands
@cli/commands/postgres.py [context]
Modifies: Add `--backend` flag, delegate to backend factory
Success: `automagik-hive postgres-start --backend=pglite` works.

**D3-install-flow**: Remove Docker detection from install
@cli/main.py [context] @Makefile [context]
Modifies: Remove `check_docker`, `setup_docker_postgres` macros
Success: `make install` completes without Docker daemon check.

**D4-help-text**: Update CLI documentation
@cli/main.py [context]
Modifies: Remove Docker installation instructions from `--help`
Success: Help text mentions PGlite default, Docker cloud option.

### Group E: Docker Removal (After D1)
Dependencies: D1-service-manager

**E1-remove-credentials-script**: Delete credential extraction
@docker/main/extract_db_credentials.sh [deletes]
Removes: 26-line bash script no longer needed
Success: File deleted, no references in codebase.

**E2-remove-docker-validation**: Delete Docker detection logic
@docker/scripts/validate.sh [deletes]
Removes: Docker daemon validation script
Success: File deleted, validation calls removed from CLI.

**E3-simplify-makefile**: Remove Docker orchestration
@Makefile [context]
Removes: `check_docker`, `setup_docker_postgres`, ~100 lines
Adds: `setup_pglite` macro calling bridge startup
Success: Makefile reduced, `make dev` uses PGlite path.

**E4-remove-postgres-service**: Delete PostgreSQL from docker-compose
@docker/main/docker-compose.yml [context]
Removes: `hive-postgres` service definition
Keeps: `app` service for cloud deployments (connects to external DB)
Success: Docker Compose file simplified to app-only container.

**E5-env-cleanup**: Remove Docker-specific variables
@.env.example [context]
Removes: `POSTGRES_UID`, `POSTGRES_GID`, Docker port mappings
Adds: `HIVE_DATABASE_BACKEND=pglite` default
Success: `.env.example` clean, migration script created.

### Group F: Testing & Documentation (After E)
Dependencies: All tasks in E

**F1-backend-tests**: Test backend factory and providers
@tests/lib/database/ [creates]
Creates: `test_backend_factory.py`, `test_pglite_provider.py`
Success: `uv run pytest tests/lib/database/` passes.

**F2-cli-integration-tests**: Test CLI commands with PGlite
@tests/cli/ [creates]
Creates: `test_pglite_cli.py` exercising install → dev flow
Success: End-to-end test boots PGlite and connects.

**F3-migration-guide**: Document upgrade path
@genie/wishes/pglite-migration-wish.md [updates]
Adds: Migration section explaining existing install upgrade
Success: Existing users can transition without data loss.

**F4-readme-update**: Update repository documentation
@README.md [context]
Removes: Docker Desktop installation instructions
Adds: PGlite benefits, Node.js optional dependency note
Success: Quick Start section reflects new workflow.

**F5-docker-cloud-docs**: Document cloud deployment option
@docker/cloud/README.md [creates]
Creates: Separate guide for Docker cloud deployments
Success: Cloud deployment path clearly separated.

## Implementation Examples

### Backend Factory Pattern
```python
# lib/database/backend_factory.py
from typing import Optional
from lib.config.settings import Settings
from lib.database.providers.base import BaseDatabaseBackend
from lib.database.providers.pglite import PGliteBackend
from lib.database.providers.postgresql import PostgreSQLBackend
from lib.database.providers.sqlite import SQLiteBackend


def get_database_backend(settings: Optional[Settings] = None) -> BaseDatabaseBackend:
    """Get appropriate database backend based on configuration."""
    if settings is None:
        from lib.config.settings import get_settings
        settings = get_settings()

    backend_type = settings.hive_database_backend

    if backend_type == "pglite":
        return PGliteBackend(settings)
    elif backend_type == "postgresql":
        return PostgreSQLBackend(settings)
    elif backend_type == "sqlite":
        return SQLiteBackend(settings)
    else:
        raise ValueError(f"Unknown database backend: {backend_type}")
```

### PGlite Provider Pattern
```python
# lib/database/providers/pglite.py
import subprocess
from pathlib import Path
from typing import Optional

from lib.database.providers.base import BaseDatabaseBackend
from lib.config.settings import Settings
from lib.logging import logger


class PGliteBackend(BaseDatabaseBackend):
    """PGlite-based database backend via Node.js bridge."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.bridge_path = Path(__file__).parent.parent.parent.parent / "tools" / "pglite-bridge"
        self.process: Optional[subprocess.Popen] = None

    def start(self) -> bool:
        """Start PGlite bridge server."""
        try:
            # Check Node.js availability
            subprocess.run(["node", "--version"], capture_output=True, check=True)

            # Install dependencies if needed
            if not (self.bridge_path / "node_modules").exists():
                logger.info("Installing PGlite bridge dependencies...")
                subprocess.run(["npm", "install"], cwd=self.bridge_path, check=True)

            # Start bridge server
            logger.info("Starting PGlite bridge on port 5532...")
            self.process = subprocess.Popen(
                ["node", "server.js"],
                cwd=self.bridge_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for bridge to be ready
            import time
            time.sleep(2)

            if self.health_check():
                logger.info("PGlite bridge started successfully")
                return True
            else:
                logger.error("PGlite bridge health check failed")
                return False

        except Exception as e:
            logger.error(f"Failed to start PGlite bridge: {e}")
            return False

    def stop(self) -> bool:
        """Stop PGlite bridge server."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=10)
            logger.info("PGlite bridge stopped")
            return True
        return False

    def health_check(self) -> bool:
        """Check if PGlite bridge is responsive."""
        try:
            import psycopg
            conn_url = self.get_connection_url()
            with psycopg.connect(conn_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return cur.fetchone()[0] == 1
        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            return False

    def get_connection_url(self) -> str:
        """Return PostgreSQL connection URL for PGlite bridge."""
        # PGlite bridge exposes PostgreSQL wire protocol on localhost:5532
        return "postgresql+psycopg://pglite:pglite@localhost:5532/main"
```

### CLI Integration Pattern
```python
# cli/core/main_service.py
from lib.database.backend_factory import get_database_backend
from lib.logging import logger


class MainService:
    def __init__(self):
        self.backend = get_database_backend()

    def serve_local(self, host: str, port: int, reload: bool = True) -> bool:
        """Start local development server with appropriate database backend."""
        try:
            # Start database backend
            logger.info(f"Starting database backend: {self.backend.__class__.__name__}")
            if not self.backend.start():
                logger.error("Failed to start database backend")
                return False

            # Start FastAPI server
            logger.info(f"Starting FastAPI server on {host}:{port}")
            # ... existing server startup logic ...

            return True
        finally:
            # Cleanup on exit
            self.backend.stop()
```

### Makefile Simplification
```makefile
# Makefile - Simplified PGlite Setup
define setup_pglite
    $(call print_status,Setting up PGlite database...); \
    if ! command -v node >/dev/null 2>&1; then \
        $(call print_warning,Node.js not found - falling back to SQLite); \
        sed -i "s|^HIVE_DATABASE_BACKEND=.*|HIVE_DATABASE_BACKEND=sqlite|" .env; \
    else \
        $(call print_status,Node.js found - using PGlite backend); \
        sed -i "s|^HIVE_DATABASE_BACKEND=.*|HIVE_DATABASE_BACKEND=pglite|" .env; \
        cd tools/pglite-bridge && npm install; \
        $(call print_success,PGlite bridge ready!); \
    fi
endef

.PHONY: install
install: ## Complete environment setup (no Docker required)
	@$(call print_status,Installing Automagik Hive environment...)
	@$(call check_prerequisites)
	@$(call setup_python_env)
	@$(call check_env_file)
	@$(call setup_pglite)
	@$(call print_success,Environment ready!)
```

### PGlite Bridge Server
```javascript
// tools/pglite-bridge/server.js
const { PGlite } = require('@electric-sql/pglite');
const { vector } = require('@electric-sql/pglite/vector');
const net = require('net');

const db = new PGlite({
  dataDir: './pglite-data',
  extensions: { vector }
});

// PostgreSQL wire protocol server
const server = net.createServer((socket) => {
  console.log('Client connected');

  socket.on('data', async (data) => {
    try {
      // Parse PostgreSQL wire protocol message
      const query = parsePostgresMessage(data);

      // Execute via PGlite
      const result = await db.query(query);

      // Send PostgreSQL wire protocol response
      socket.write(formatPostgresResponse(result));
    } catch (err) {
      socket.write(formatPostgresError(err));
    }
  });

  socket.on('end', () => {
    console.log('Client disconnected');
  });
});

server.listen(5532, () => {
  console.log('PGlite bridge listening on port 5532');
});
```

## Testing Protocol
```bash
# Backend factory and provider tests
uv run pytest tests/lib/database/test_backend_factory.py -v
uv run pytest tests/lib/database/test_pglite_provider.py -v

# CLI integration tests
uv run pytest tests/cli/test_pglite_cli.py -v

# End-to-end smoke test
make clean
make install  # Should complete without Docker
make dev      # Should start PGlite bridge + API

# Verify pgvector extension
uv run python -c "
import psycopg
conn = psycopg.connect('postgresql+psycopg://pglite:pglite@localhost:5532/main')
cur = conn.cursor()
cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
cur.execute('SELECT extname FROM pg_extension WHERE extname = \\'vector\\'')
print('pgvector available:', cur.fetchone()[0] == 'vector')
"

# Cloud deployment path (optional)
cd docker/cloud
docker-compose up -d  # App-only container → external PostgreSQL
```

## Validation Checklist
- [ ] PGlite bridge starts without Docker installed
- [ ] pgvector extension loads successfully
- [ ] Existing `.env` files work unchanged (URL format preserved)
- [ ] `make install` completes in <2 minutes
- [ ] Docker removed from default development path
- [ ] Cloud deployment option documented separately
- [ ] All database operations work via PGlite bridge
- [ ] Migration guide covers existing installations
- [ ] Codebase reduced by ~500 lines
- [ ] Node.js as optional dependency clearly documented
- [ ] SQLite fallback works when Node.js absent

## Migration Path for Existing Users

### Automatic Upgrade
```bash
# For existing installations - automatic migration
cd /path/to/automagik-hive
git pull origin dev
make install  # Detects existing .env, migrates to PGlite

# Backend automatically selected:
# - Node.js found → PGlite backend
# - Node.js missing → SQLite fallback
# - Docker flag → PostgreSQL backend
```

### Manual Migration Steps
```bash
# 1. Backup existing data (optional)
docker exec hive-postgres pg_dump -U $USER -d hive > backup.sql

# 2. Update .env file
echo "HIVE_DATABASE_BACKEND=pglite" >> .env

# 3. Remove Docker-specific variables (optional)
sed -i '/POSTGRES_UID/d' .env
sed -i '/POSTGRES_GID/d' .env

# 4. Install PGlite dependencies
cd tools/pglite-bridge && npm install

# 5. Start with PGlite
make dev

# 6. Restore data (optional)
cat backup.sql | psql postgresql://pglite:pglite@localhost:5532/main
```

### Rollback to Docker (if needed)
```bash
# Temporary rollback during transition period
echo "HIVE_DATABASE_BACKEND=postgresql" >> .env
make postgres-start  # Still works via existing Docker path
```

## Performance Targets
- **Installation time:** 4+ manual steps → <2 minutes automated
- **Startup time:** ~5s Docker orchestration → ~1s PGlite bridge
- **Developer onboarding:** Docker setup required → `git clone && make install`
- **Codebase complexity:** 500+ lines Docker → ~200 lines PGlite bridge
- **Memory footprint:** ~500MB Docker Desktop → ~50MB PGlite
- **Cross-platform:** Docker daemon issues → WASM consistency

## Risk Mitigation

### Node.js Dependency
**Risk:** Adds Node.js as requirement
**Mitigation:** SQLite fallback when Node.js unavailable, clear docs

### PostgreSQL Wire Protocol Compatibility
**Risk:** PGlite bridge may not support all PostgreSQL features
**Mitigation:** Test suite covers Agno's actual DB usage patterns

### Production Deployments
**Risk:** Cloud still needs real PostgreSQL
**Mitigation:** Docker cloud path preserved, clearly documented

### Existing Data Migration
**Risk:** Users lose data during upgrade
**Mitigation:** Migration guide with backup/restore steps, rollback option

## Success Metrics
- Installation friction: Docker required → Optional
- Setup time: ~5 minutes → <2 minutes
- First-time success rate: 70% (Docker issues) → 95% (PGlite)
- Codebase complexity: -500 lines Docker orchestration
- Developer questions: "Docker won't start" → "Works immediately"
- RC iterations: 16 (installation issues) → Validate locally before release

## Future Enhancements (Out of Scope)
- PGlite persistence → cloud storage sync
- Multi-tenant PGlite instances
- PGlite ↔ Cloud PostgreSQL migration tools
- Browser-based PGlite for AgentOS UI
- PGlite replication for HA development

---

**Current Status:** READY_FOR_REVIEW
**Branch Status:** Committed to wish/pglite-migration for human analysis
**Next Actions:**
- Review the wish specification in the dedicated branch
- Respond with: APPROVE (to proceed) | REVISE (to modify)
- Once approved, execute via `/forge /genie/wishes/pglite-migration-wish.md`
