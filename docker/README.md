# Docker Architecture Overview

> **⚠️ IMPORTANT: Docker is OPTIONAL with Automagik Hive**
>
> **Docker is only required for the PostgreSQL backend.**
>
> **PGlite (default) and SQLite backends work without Docker.**
>
> See [PGlite Migration Guide](../docs/MIGRATION_PGLITE.md) for backend selection details.

This directory contains all Docker-related files for the Automagik Hive multi-agent system.

## When Do You Need Docker?

Docker is **only required** if you choose the **PostgreSQL backend**:

- ✅ **PGlite Backend** (default) - No Docker needed
- ✅ **SQLite Backend** - No Docker needed
- ⚠️ **PostgreSQL Backend** - Docker required

**For most users:** You can skip Docker entirely and use PGlite or SQLite.

**Backend Selection:**
```bash
# No Docker required
make install-pglite   # Default - WebAssembly PostgreSQL
make install-sqlite   # Minimal dependencies

# Docker required
make install-postgres # Full PostgreSQL with Docker
```

See [Backend Comparison](../docs/MIGRATION_PGLITE.md#backend-comparison) for detailed feature comparison.

## Directory Structure

```
docker/
├── main/                       # Main workspace environment
│   ├── Dockerfile             # Main application container
│   ├── docker-compose.yml     # Main services orchestration
│   ├── .dockerignore          # Main-specific ignore patterns
│   └── README.md              # Main environment documentation
├── templates/                  # Reusable Docker templates
│   └── workspace.yml          # Generic workspace template
├── scripts/                    # Docker-related scripts
│   └── validate.sh            # Validation script
├── lib/                        # Docker service libraries
│   ├── compose_manager.py     # Compose management utilities
│   ├── compose_service.py     # Service orchestration
│   └── postgres_manager.py    # PostgreSQL management
└── README.md                   # This file
```

## PostgreSQL Backend Setup (Optional)

**Only follow these steps if you explicitly chose PostgreSQL backend.**

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Installation

```bash
# Install with PostgreSQL backend
make install-postgres

# This automatically:
# - Checks for Docker
# - Generates secure credentials
# - Starts PostgreSQL container
# - Configures application
```

### Environment (docker/main/)

- **Ports**: API 8886, PostgreSQL 5532
- **Usage**: PostgreSQL backend deployments only
- **Integration**: Used by `make postgres-*` commands

### Quick Commands

```bash
# PostgreSQL management
make postgres-start    # Start PostgreSQL container
make postgres-stop     # Stop PostgreSQL container
make postgres-status   # Check PostgreSQL status
make postgres-logs     # View PostgreSQL logs
make postgres-health   # Health check

# Docker Compose (manual)
docker compose -f docker/main/docker-compose.yml up -d postgres
docker compose -f docker/main/docker-compose.yml down

# Validate environment
bash docker/scripts/validate.sh
```

## Runtime Surfaces

- **Agno Playground**: Enabled by default inside the Hive API when `HIVE_EMBED_PLAYGROUND=true` (default). Access it at `http://<HIVE_API_HOST>:<HIVE_API_PORT>/playground` (defaults to `http://localhost:8886/playground`).
- **AgentOS Control Pane**: Point control pane tooling at the Hive server base URL (`HIVE_CONTROL_PANE_BASE_URL`, default is the API base). The AgentOS config endpoint lives at `/api/v1/agentos/config`.
- **Authentication**: Playground honours the API key guard; disable authentication only for local development.

Set `HIVE_EMBED_PLAYGROUND=false` to run the API without mounting the Playground. Override the mount path with `HIVE_PLAYGROUND_MOUNT_PATH` when reverse proxies require a different location.

> Compose deployments should now proxy the Hive API directly instead of exposing a separate `localhost:8000` Playground stack. The optional compose services remain available for local infrastructure, but the authoritative routes live inside the Hive server.

## Migrating Away from Docker

If you previously used PostgreSQL with Docker and want to simplify:

### Option 1: Switch to PGlite (Recommended)

```bash
# Stop PostgreSQL
make postgres-stop

# Update .env
HIVE_DATABASE_BACKEND=pglite
HIVE_DATABASE_URL=pglite://./data/automagik_hive.db

# Restart with PGlite
make dev
```

### Option 2: Switch to SQLite

```bash
# Stop PostgreSQL
make postgres-stop

# Update .env
HIVE_DATABASE_BACKEND=sqlite
HIVE_DATABASE_URL=sqlite:///./data/automagik_hive.db

# Restart with SQLite
make dev
```

**Note:** Session history will reset. Agent configurations and knowledge base (CSV) remain unchanged.

**Full migration guide:** [PGlite Migration Guide](../docs/MIGRATION_PGLITE.md)

## Migration Notes

This structure was created by consolidating Docker files from the root directory:
- All Dockerfile.* files moved to environment-specific directories
- All docker-compose*.yml files organized by environment
- Templates consolidated from /templates/ directory
- Docker libraries moved from /lib/docker/ to /docker/lib/
- All references updated throughout the codebase
- Docker is now **optional** (PGlite migration, v0.2.0+)
