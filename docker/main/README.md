# Main Environment Docker Configuration

This directory contains the Docker configuration for the main Automagik Hive workspace environment.

## Environment Details
- **API Port**: 8886
- **Database Port**: 5532
- **Container Names**: `hive-agents`, `hive-postgres`
- **Network**: `automagik-hive_default`

## Files
- `Dockerfile` - Main application container
- `docker-compose.yml` - Main services orchestration
- `.dockerignore` - Build context exclusions

## Usage
```bash
# Start main environment services
docker compose -f docker/main/docker-compose.yml up -d

# Stop main environment
docker compose -f docker/main/docker-compose.yml down

# View logs
docker compose -f docker/main/docker-compose.yml logs -f
```

## Make Integration
The Makefile automatically uses this configuration through the `DOCKER_COMPOSE_FILE` variable.

```bash
make prod     # Uses docker/main/docker-compose.yml
make status   # Shows main environment status
```