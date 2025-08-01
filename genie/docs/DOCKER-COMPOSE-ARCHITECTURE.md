# Docker Compose Architecture

This document describes the multi-environment Docker Compose architecture for Automagik Hive.

## Architecture Overview

The Automagik Hive system uses a multi-environment Docker architecture with three isolated environments:

### 1. Main Environment (`docker/main/`)
- **Purpose**: Primary development and production workloads
- **API Port**: 8886
- **Database Port**: 5532
- **Containers**: `hive-agents`, `hive-postgres`
- **Network**: `automagik-hive_default`

### 2. Agent Environment (`docker/agent/`)
- **Purpose**: Isolated agent development and testing
- **API Port**: 38886  
- **Database Port**: 35532
- **Containers**: `hive-agents-agent`, `hive-postgres-agent`
- **Network**: `automagik-hive_agent_default`

### 3. Genie Environment (`docker/genie/`)
- **Purpose**: Specialized Genie consultation workflows
- **API Port**: 48886
- **Containers**: `hive-genie-server`
- **Network**: `automagik-hive_genie_default`

## Environment Isolation

Each environment is completely isolated with:
- Dedicated Docker networks
- Separate port ranges to prevent conflicts
- Independent PostgreSQL databases
- Environment-specific configuration files

## Directory Structure

```
docker/
├── main/                       # Main workspace environment
├── agent/                      # Agent development environment  
├── genie/                      # Genie consultation environment
├── templates/                  # Reusable Docker templates
├── scripts/                    # Docker utilities
└── lib/                        # Docker service libraries
```

## Usage Patterns

### Development Workflow
```bash
# Main development
make dev                        # Local development server
make prod                       # Docker production stack

# Agent development
make install-agent              # Set up agent environment
make agent                      # Start agent server

# Manual container management
docker compose -f docker/main/docker-compose.yml up -d
docker compose -f docker/agent/docker-compose.yml up -d
docker compose -f docker/genie/docker-compose.yml up -d
```

### Integration Points

- **Makefile**: Automatically uses correct compose files through variables
- **CLI Tools**: Integration with UVX CLI for workspace management
- **Validation**: Comprehensive validation script at `docker/scripts/validate.sh`
- **Libraries**: Shared Docker management libraries in `docker/lib/`

## Migration History

This architecture was created by consolidating Docker files from the root directory into a unified structure while maintaining complete environment separation and zero downtime migration.