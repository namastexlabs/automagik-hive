# Agent Environment Docker Configuration

This directory contains the Docker configuration for the agent development environment - an isolated environment for AI agent operations.

## Environment Details
- **API Port**: 38886
- **Database Port**: 35532
- **Container Names**: `hive-agent-api`, `hive-agent-postgres`
- **Network**: `automagik-hive_agent_default`

## Files
- `Dockerfile` - Agent all-in-one container
- `docker-compose.yml` - Agent services orchestration

## Usage
```bash
# Start agent environment services
docker compose -f docker/agent/docker-compose.yml up -d

# Stop agent environment
docker compose -f docker/agent/docker-compose.yml down

# View logs
docker compose -f docker/agent/docker-compose.yml logs -f
```

## Make Integration
Use agent-specific Makefile commands:

```bash
make install-agent  # Set up agent environment
make agent          # Start agent server
make agent-status   # Check agent environment
make agent-logs     # View agent logs
```

## Environment Variables
The agent environment inherits from the main `.env` file and overrides only agent-specific settings (ports, database) directly in docker-compose.yml.