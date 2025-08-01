# Docker Architecture Mismatch Analysis

## Current Architecture Issue

The agent container is failing with "Container hive-postgres-agent is unhealthy" because we're using separate PostgreSQL + FastAPI containers, but the UVX master plan T1.8 and T1.9 specify unified all-in-one containers.

## Architecture Comparison

### Current Architecture (INCORRECT)
```
docker/templates/agent.yml:
├── app-agent (FastAPI container)
└── postgres-agent (PostgreSQL container) 
    └── Health check failing - blocks app-agent startup

docker/templates/genie.yml:
├── genie-server (FastAPI container)  
└── genie-postgres (PostgreSQL container)
    └── Two separate containers - not unified approach

docker/templates/workspace.yml:
└── postgres (PostgreSQL container only) - CORRECT for main workspace
```

### Required Architecture (UVX Master Plan)
```
T1.8 Genie All-in-One Container:
└── genie-server (PostgreSQL + FastAPI in single container)
    ├── Internal PostgreSQL (port 5432)
    ├── FastAPI application
    ├── Supervisord process management
    └── External port 48886

T1.9 Agent All-in-One Container:  
└── agent-dev-server (PostgreSQL + FastAPI in single container)
    ├── Internal PostgreSQL (port 5432)
    ├── FastAPI application
    ├── Supervisord process management
    └── External port 38886

Main workspace (KEEP CURRENT):
├── app (FastAPI container)
└── postgres (PostgreSQL container) - Separate containers OK
```

## Root Cause Analysis

1. **Architecture Mismatch**: Current implementation uses 2-container approach (app + postgres) for Genie/Agent
2. **UVX Specification**: Master plan explicitly requires unified containers for T1.8/T1.9
3. **Health Check Failure**: postgres-agent container unhealthy blocks app-agent startup
4. **Process Dependencies**: Separate containers create startup order dependencies
5. **Complexity**: Managing 2 containers per service increases operational complexity

## Problem Details

### Agent Container Failure
- `hive-postgres-agent` container becomes unhealthy
- `app-agent` depends on postgres-agent health check
- Startup fails when PostgreSQL health check fails
- Two-container coordination adds complexity

### Master Plan Violation
- T1.8: "Genie All-in-One Container (PostgreSQL + FastAPI in single container with supervisord)"
- T1.9: "Agent All-in-One Container (PostgreSQL + FastAPI in single container with supervisord)"
- Current: Separate postgres + app containers for both Genie and Agent

## Required Transformation

### From Separate Containers
```yaml
services:
  app-agent:
    depends_on:
      postgres-agent:
        condition: service_healthy  # FAILURE POINT
  postgres-agent:
    healthcheck: [...] # FAILS - blocks startup
```

### To Unified Container
```yaml
services:
  agent-all-in-one:
    # PostgreSQL + FastAPI in single container
    # Internal process management with supervisord
    # No external dependencies
    # Self-contained health checking
```

## Architecture Benefits of Unified Approach

### Eliminated Dependencies
- No inter-container health check dependencies
- Single container startup/shutdown
- Simplified orchestration

### Improved Reliability  
- Internal PostgreSQL always available to application
- No network latency between app and database
- Atomic startup/shutdown operations

### Operational Simplicity
- One container per service instead of two
- Unified logging and monitoring
- Simplified backup and recovery

## Next Steps

1. Design unified Dockerfile architecture for Genie container
2. Design unified Dockerfile architecture for Agent container  
3. Implement supervisord process management
4. Create migration strategy from current separate containers
5. Maintain main workspace as separate containers (per plan)