# 🐳 Automagik Hive Docker Compose Architecture

## 🏗️ Multi-Container Architecture Overview

This document describes the complete Docker Compose architecture for Automagik Hive's UVX Phase 1 implementation, featuring a sophisticated multi-container orchestration strategy.

### 🎯 Architecture Strategy

**Three-Tier Container Architecture:**
- **Main Workspace**: UVX CLI + Docker PostgreSQL (ports 8886, 5532)
- **Genie Container**: All-in-one PostgreSQL + FastAPI (port 48886)
- **Agent Container**: All-in-one PostgreSQL + FastAPI (port 35532)

## 📊 Container Service Matrix

| Service | Compose File | Port | Database | Purpose |
|---------|-------------|------|----------|---------|
| **Main Workspace** | `docker-compose.yml` | 8886 | postgres:5532 | Primary workspace server |
| **Genie Consultation** | `docker-compose-genie.yml` | 48886 | internal:5432 | Wish fulfillment orchestration |
| **Agent Development** | `docker-compose-agent.yml` | 35532 | internal:5432 | Isolated agent testing |

## 🔧 Service Configurations

### Main Workspace (`docker-compose.yml`)
**Multi-Service Setup:**
- **app**: FastAPI application (port 8886)
- **postgres**: Shared PostgreSQL with pgvector (port 5532)
- **Networks**: `app_network` (bridge)
- **Volumes**: `app_logs`, `app_data`, `./data/postgres`

**Usage:**
```bash
# Start main workspace services
docker-compose up -d

# Start only PostgreSQL for external connections
docker-compose up postgres

# View main application logs
docker-compose logs -f app
```

### Genie Container (`docker-compose-genie.yml`)
**All-in-One Architecture:**
- **genie-server**: PostgreSQL + FastAPI in single container
- **Port**: 48886 (external FastAPI access)
- **Database**: Internal PostgreSQL on port 5432
- **Database Name**: `hive_genie`
- **Process Management**: Supervisord coordination
- **Networks**: `genie_network` (isolated)
- **Volumes**: `./data/postgres-genie`, `genie_app_logs`, `genie_app_data`

**Features:**
- Complete isolation from main workspace
- Internal PostgreSQL with pgvector extension
- Multi-service health checks (PostgreSQL + FastAPI)
- Supervisor-managed process lifecycle
- Persistent data storage

**Usage:**
```bash
# Start Genie consultation container
docker-compose -f docker-compose-genie.yml up -d

# View Genie logs
docker-compose -f docker-compose-genie.yml logs -f

# Stop Genie container
docker-compose -f docker-compose-genie.yml down
```

### Agent Container (`docker-compose-agent.yml`)
**All-in-One Architecture:**
- **agent-dev-server**: PostgreSQL + FastAPI in single container
- **Port**: 35532 (external FastAPI access)
- **Database**: Internal PostgreSQL on port 5432
- **Database Name**: `hive_agent`
- **Process Management**: Supervisord coordination
- **Networks**: `agent_network` (isolated)
- **Volumes**: `./data/postgres-agent`, `agent_app_logs`, `agent_app_data`

**Features:**
- Complete isolation for agent development
- Internal PostgreSQL with pgvector extension
- Multi-service health checks (PostgreSQL + FastAPI)
- Supervisor-managed process lifecycle
- Persistent data storage

**Usage:**
```bash
# Start Agent development container
docker-compose -f docker-compose-agent.yml up -d

# View Agent logs
docker-compose -f docker-compose-agent.yml logs -f

# Stop Agent container
docker-compose -f docker-compose-agent.yml down
```

## 🚀 UVX CLI Integration

### Command Mapping
The Docker Compose services integrate seamlessly with the UVX CLI commands:

```bash
# Core workspace commands (uses docker-compose.yml)
uvx automagik-hive ./my-workspace    # Starts postgres + app services
uvx automagik-hive --init            # Creates docker-compose.yml + .env

# Genie commands (uses docker-compose-genie.yml)
uvx automagik-hive --genie-serve     # docker-compose -f docker-compose-genie.yml up -d
uvx automagik-hive --genie-logs      # docker-compose -f docker-compose-genie.yml logs -f
uvx automagik-hive --genie-stop      # docker-compose -f docker-compose-genie.yml down

# Agent commands (uses docker-compose-agent.yml)
uvx automagik-hive --agent-serve     # docker-compose -f docker-compose-agent.yml up -d
uvx automagik-hive --agent-logs      # docker-compose -f docker-compose-agent.yml logs -f
uvx automagik-hive --agent-stop      # docker-compose -f docker-compose-agent.yml down
```

## 🗂️ Directory Structure

### Data Persistence Strategy
```
./my-workspace/
├── docker-compose.yml              # Main workspace services
├── docker-compose-genie.yml        # Genie container (optional)
├── docker-compose-agent.yml        # Agent container (optional)
├── .env                            # Shared environment variables
├── data/                           # Persistent data volumes
│   ├── postgres/                   # Main PostgreSQL data (port 5532)
│   ├── postgres-genie/             # Genie PostgreSQL data (internal)
│   └── postgres-agent/             # Agent PostgreSQL data (internal)
├── .claude/                        # Claude Code integration
└── ai/                             # User AI components
    ├── agents/                     # Custom user agents
    ├── teams/                      # Custom user teams
    ├── workflows/                  # Custom user workflows
    └── tools/                      # Custom user tools
```

## 🔄 Multi-Stage Docker Builds

### Build Architecture
All containers use sophisticated multi-stage builds:

**Stage 1: UV Dependencies Builder**
- Base: `python:3.12-slim`
- UV package manager from `ghcr.io/astral-sh/uv:latest`
- Production dependencies only (`uv sync --frozen --no-dev`)
- BuildKit cache optimization

**Stage 2: PostgreSQL Base** (Genie/Agent only)
- Base: `agnohq/pgvector:16`
- PostgreSQL client tools
- pgvector extension support

**Stage 3: Production Runtime**
- **Main**: Python application with external PostgreSQL
- **Genie/Agent**: Unified PostgreSQL + Python with Supervisord

### Dockerfile Patterns
- **Dockerfile**: Main workspace application
- **Dockerfile.genie**: All-in-one Genie container
- **Dockerfile.agent**: All-in-one Agent container

## 🌐 Network Architecture

### Network Isolation Strategy
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Main Network  │    │  Genie Network  │    │  Agent Network  │
│  (app_network)  │    │(genie_network)  │    │(agent_network)  │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ app:8886        │    │ genie:48886     │    │ agent:35532     │
│ postgres:5532   │    │ postgres:5432   │    │ postgres:5432   │
│                 │    │ (internal)      │    │ (internal)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Network Benefits:**
- **Isolation**: Each container network is completely isolated  
- **Security**: No cross-container network access
- **Scalability**: Independent scaling per service
- **Development**: Safe testing without interference

## 🛡️ Security & Resource Management

### Security Features
- **Non-root users**: All applications run as `hive:1000`
- **Network isolation**: Bridge networks with no external access
- **Credential management**: Secure environment variable injection
- **File permissions**: Proper ownership and access controls

### Resource Limits
```yaml
# Resource limits for all-in-one containers
deploy:
  resources:
    limits:
      memory: 2G      # Maximum memory usage
      cpus: '1.0'     # Maximum CPU usage
    reservations:
      memory: 512M    # Guaranteed memory
      cpus: '0.25'    # Guaranteed CPU
```

## 🩺 Health Monitoring

### Multi-Service Health Checks
**Main Workspace:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8886/api/v1/health"]
  interval: 30s
  timeout: 10s
```

**Genie/Agent Containers:**
```yaml
healthcheck:
  test: |
    pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB} &&
    curl -f http://localhost:${API_PORT}/api/v1/health
  interval: 30s
  timeout: 15s      # Longer timeout for dual-service check
  start_period: 90s # Extra time for PostgreSQL + app startup
```

## 🔧 Development Workflow

### Local Development
```bash
# Full development environment
docker-compose up -d                    # Main workspace
docker-compose -f docker-compose-genie.yml up -d    # Genie consultation
docker-compose -f docker-compose-agent.yml up -d     # Agent development

# Access services
curl http://localhost:8886/api/v1/health     # Main workspace
curl http://localhost:48886/api/v1/health    # Genie consultation  
curl http://localhost:35532/api/v1/health    # Agent development
```

### Production Deployment
```bash
# Selective service deployment
docker-compose up -d postgres app       # Core workspace only
docker-compose -f docker-compose-genie.yml up -d  # Add Genie when needed

# Health monitoring
docker-compose ps                        # Service status
docker-compose logs -f --tail=50        # Live logs
```

## 📈 Performance Optimizations

### Build Optimizations
- **BuildKit cache**: UV dependency caching across builds
- **Layer optimization**: Rarely changing files copied first
- **Multi-stage builds**: Minimal production images
- **Platform targeting**: `linux/amd64` for consistent builds

### Runtime Optimizations
- **UV ecosystem**: Fast Python package management
- **Supervisord**: Efficient multi-process management
- **Health checks**: Smart failure detection and recovery
- **Volume persistence**: Data survives container restarts

## 🎯 Integration Points

### Existing System Integration
- **FastAPI Server**: Reuses existing `api/serve.py` patterns
- **Agno Framework**: Compatible with existing agent architecture
- **MCP Tools**: Works with existing tool ecosystem
- **Authentication**: Maintains existing auth service patterns
- **Logging**: Integrates with existing logging infrastructure

### Future Extension Points
- **Kubernetes**: Docker Compose patterns translate to K8s
- **Monitoring**: Prometheus/Grafana integration ready
- **Load Balancing**: NGINX proxy integration planned
- **CI/CD**: GitHub Actions integration with multi-stage builds

---

This architecture provides a robust, scalable foundation for the UVX transformation while maintaining compatibility with existing patterns and enabling future enterprise deployment scenarios.