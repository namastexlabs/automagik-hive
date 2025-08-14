# Docker Architecture Overview

This directory contains all Docker-related files for the Automagik Hive multi-agent system, organized by environment and purpose.

## Directory Structure

```
docker/
├── main/                       # Main workspace environment
│   ├── Dockerfile             # Main application container
│   ├── docker-compose.yml     # Main services orchestration
│   ├── .dockerignore          # Main-specific ignore patterns
│   └── README.md              # Main environment documentation
├── agent/                      # Agent development environment
│   ├── Dockerfile             # Agent all-in-one container
│   ├── docker-compose.yml     # Agent services (port 38886/35532)
│   └── README.md              # Agent environment documentation
├── genie/                      # Genie consultation environment
│   ├── Dockerfile             # Genie all-in-one container
│   ├── docker-compose.yml     # Genie services (port 45886)
│   └── README.md              # Genie environment documentation
├── templates/                  # Reusable Docker templates
│   ├── workspace.yml          # Generic workspace template
│   └── genie.yml             # Genie service template
├── scripts/                    # Docker-related scripts
│   └── validate.sh            # Validation script
├── lib/                        # Docker service libraries
│   ├── compose_manager.py     # Compose management utilities
│   ├── compose_service.py     # Service orchestration
│   └── postgres_manager.py    # PostgreSQL management
└── README.md                   # This file
```

## Environment Separation

### Main Environment (docker/main/)
- **Ports**: API 8886, PostgreSQL 5532
- **Usage**: Primary development and production workloads
- **Integration**: Used by `make prod`, `make dev`

### Agent Environment (docker/agent/)
- **Ports**: API 38886, PostgreSQL 35532
- **Usage**: Isolated agent development and testing
- **Integration**: Used by `make agent`, `make install-agent`

### Genie Environment (docker/genie/)
- **Ports**: API 45886
- **Usage**: Specialized Genie consultation workflows
- **Integration**: Manual or specialized workflows

## Quick Commands

```bash
# Main environment
docker compose -f docker/main/docker-compose.yml up -d

# Agent environment
docker compose -f docker/agent/docker-compose.yml up -d

# Genie environment
docker compose -f docker/genie/docker-compose.yml up -d

# Validate all environments
bash docker/scripts/validate.sh
```

## Migration Notes

This structure was created by consolidating Docker files from the root directory:
- All Dockerfile.* files moved to environment-specific directories
- All docker-compose*.yml files organized by environment
- Templates consolidated from /templates/ directory
- Docker libraries moved from /lib/docker/ to /docker/lib/
- All references updated throughout the codebase