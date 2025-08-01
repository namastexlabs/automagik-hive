# Migration Strategy: Separate to Unified Container Architecture

## Overview

Migrate from current failing separate PostgreSQL + FastAPI containers to unified all-in-one containers with supervisord orchestration, addressing the "Container hive-postgres-agent is unhealthy" issue.

## Current State Analysis

### Failing Architecture
```
docker/templates/agent.yml:
├── app-agent (FastAPI) - FAILS to start
│   └── depends_on: postgres-agent (service_healthy)
└── postgres-agent (PostgreSQL) - UNHEALTHY
    └── Health check failing - blocks entire stack
```

### Working Architecture (Keep)
```
docker/templates/workspace.yml:
└── postgres (PostgreSQL only) - WORKING
    └── Main workspace uses separate containers - keep as-is
```

## Migration Plan

### Phase 1: Create Unified Container Infrastructure

#### Step 1.1: Create Directory Structure
```bash
# Create unified container directories
mkdir -p docker/genie/{configs,scripts}
mkdir -p docker/agent/{configs,scripts}

# Create configuration templates
touch docker/genie/{Dockerfile.genie,supervisord.conf,postgresql.conf,pg_hba.conf}
touch docker/agent/{Dockerfile.agent,supervisord.conf,postgresql.conf,pg_hba.conf}
```

#### Step 1.2: Implement Dockerfiles
- Create `docker/genie/Dockerfile.genie` with multi-stage unified build
- Create `docker/agent/Dockerfile.agent` with multi-stage unified build
- Base on existing successful patterns from main workspace

#### Step 1.3: Implement Supervisord Configurations
- PostgreSQL process management (priority 100)
- FastAPI application management (priority 200)
- Health monitoring (priority 300)
- Proper logging and error handling

### Phase 2: Create New Docker Compose Files

#### Step 2.1: Unified Genie Container
```yaml
# docker/genie/docker-compose.yml
services:
  genie-unified:
    build:
      context: ../..
      dockerfile: docker/genie/Dockerfile.genie
    container_name: hive-genie-unified
    ports:
      - "48886:48886"
    volumes:
      - ./data/postgres-genie:/var/lib/postgresql/data
    # No depends_on - self-contained
```

#### Step 2.2: Unified Agent Container
```yaml
# docker/agent/docker-compose.yml
services:
  agent-unified:
    build:
      context: ../..
      dockerfile: docker/agent/Dockerfile.agent
    container_name: hive-agent-unified
    ports:
      - "38886:38886"
    volumes:
      - ./data/postgres-agent:/var/lib/postgresql/data
    # No depends_on - self-contained
```

### Phase 3: Backward Compatibility & Migration

#### Step 3.1: Preserve Existing Templates
- Keep `docker/templates/agent.yml` as `agent-legacy.yml`
- Keep `docker/templates/genie.yml` as `genie-legacy.yml`
- Maintain backward compatibility during transition

#### Step 3.2: Update Template System
```yaml
# docker/templates/agent.yml (NEW - Unified)
services:
  agent-all-in-one:
    build:
      context: ../
      dockerfile: docker/agent/Dockerfile.agent
    # Single unified service
    
# docker/templates/genie.yml (NEW - Unified)
services:
  genie-all-in-one:
    build:
      context: ../
      dockerfile: docker/genie/Dockerfile.genie
    # Single unified service
```

#### Step 3.3: Data Migration Strategy
```bash
# Migrate existing PostgreSQL data to unified containers
# 1. Stop current failing containers
docker-compose -f docker/templates/agent.yml down

# 2. Backup existing data (if any)
cp -r data/postgres-agent data/postgres-agent-backup

# 3. Start unified container
docker-compose -f docker/templates/agent.yml up -d

# 4. Verify data integrity
docker exec hive-agent-unified psql -U agent -d hive_agent -c "SELECT count(*) FROM information_schema.tables;"
```

### Phase 4: Update CLI Integration

#### Step 4.1: Update Make Commands
```makefile
# Update Makefile agent commands to use unified containers
agent:
	@echo "🚀 Starting unified agent development environment..."
	docker-compose -f docker/templates/agent.yml up -d agent-all-in-one

agent-stop:
	@echo "🛑 Stopping unified agent environment..."
	docker-compose -f docker/templates/agent.yml down

agent-logs:
	@echo "📋 Showing unified agent logs..."
	docker-compose -f docker/templates/agent.yml logs -f agent-all-in-one
```

#### Step 4.2: Update CLI Commands (Future UVX Integration)
```python
# cli/commands/agent.py
def start_agent():
    """Start unified agent development container"""
    run_command([
        "docker-compose", 
        "-f", "docker/templates/agent.yml", 
        "up", "-d", "agent-all-in-one"
    ])

def stop_agent():
    """Stop unified agent development container"""
    run_command([
        "docker-compose",
        "-f", "docker/templates/agent.yml",
        "down"
    ])
```

## Implementation Details

### Health Check Strategy

#### Current Problem
```yaml
# FAILING - Inter-container dependency
app-agent:
  depends_on:
    postgres-agent:
      condition: service_healthy  # FAILS HERE
```

#### Unified Solution
```yaml
# WORKING - Internal health check
agent-all-in-one:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:38886/api/v1/health"]
    # Internal PostgreSQL always available - no external dependencies
```

### Process Management

#### Supervisord Process Coordination
```ini
# PostgreSQL starts first (priority 100)
[program:postgresql]
priority=100
command=/usr/lib/postgresql/16/bin/postgres ...

# FastAPI starts after PostgreSQL (priority 200)
[program:hive-agent]
priority=200
command=python -m uvicorn api.serve:app ...
```

#### Service Dependencies
```bash
# Internal process dependencies managed by supervisord
# No Docker depends_on needed - single container
# PostgreSQL available on localhost:5432 internally
# FastAPI connects to localhost:5432 - no network latency
```

### Security & User Management

#### Non-Root Execution
```dockerfile
# Create application user
RUN useradd -m -u 1000 -s /bin/bash agent

# All processes run as application user
USER 1000:1000

# Supervisord manages processes as non-root user
```

#### Database Security
```bash
# Dedicated database user per container
# Genie: hive user -> hive_genie database
# Agent: agent user -> hive_agent database
# Isolated credentials per container
```

## Migration Timeline

### Week 1: Infrastructure Setup
- [ ] Create unified Dockerfile templates
- [ ] Implement supervisord configurations
- [ ] Create PostgreSQL configuration files
- [ ] Build and test unified containers locally

### Week 2: Docker Compose Integration
- [ ] Update docker/templates/ files
- [ ] Test unified container startup/shutdown
- [ ] Validate health checks and monitoring
- [ ] Document migration procedures

### Week 3: CLI Integration
- [ ] Update Makefile commands
- [ ] Test agent/genie commands with unified containers
- [ ] Validate data persistence and migrations
- [ ] Performance testing and optimization

### Week 4: Production Readiness
- [ ] Comprehensive testing across platforms
- [ ] Documentation updates
- [ ] Rollback procedures
- [ ] Production deployment validation

## Risk Mitigation

### Rollback Strategy
```bash
# If unified containers fail, revert to legacy (if working)
cp docker/templates/agent-legacy.yml docker/templates/agent.yml
cp docker/templates/genie-legacy.yml docker/templates/genie.yml
docker-compose -f docker/templates/agent.yml up -d
```

### Data Protection
```bash
# Always backup data before migration
tar -czf postgres-backup-$(date +%Y%m%d).tar.gz data/
```

### Testing Strategy
```bash
# Test unified containers in isolation
docker build -f docker/agent/Dockerfile.agent . -t hive-agent-test
docker run -p 38886:38886 hive-agent-test

# Validate health endpoints
curl http://localhost:38886/api/v1/health
```

## Success Criteria

### Functional Requirements
- [ ] Agent container starts without "unhealthy" errors
- [ ] Genie container starts without dependency failures
- [ ] Both containers serve API endpoints correctly
- [ ] PostgreSQL with pgvector works in both containers
- [ ] Data persists across container restarts

### Performance Requirements
- [ ] Container startup time < 60 seconds
- [ ] API response time < 500ms after startup
- [ ] Database queries perform at acceptable levels
- [ ] Resource usage within reasonable limits

### Operational Requirements
- [ ] Health checks work reliably
- [ ] Logging provides adequate debugging information
- [ ] Container updates don't lose data
- [ ] Backup and restore procedures work
- [ ] Cross-platform compatibility (Linux/macOS/Windows/WSL)

## Post-Migration Cleanup

### Remove Legacy Files
```bash
# After successful migration and testing
rm docker/templates/agent-legacy.yml
rm docker/templates/genie-legacy.yml

# Clean up unused Docker images
docker image prune -f
```

### Documentation Updates
- Update README.md with new container architecture
- Update docker/README.md with unified container instructions
- Update Makefile documentation
- Create migration guide for existing users

This migration strategy addresses the core issue of separate container health check failures by eliminating inter-container dependencies through unified all-in-one containers, while maintaining compatibility with existing data and workflows.