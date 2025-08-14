# Genie Environment Docker Configuration

This directory contains the Docker configuration for the Genie consultation environment - a specialized container for Genie-specific operations.

## Environment Details
- **API Port**: 45886
- **Container Names**: `hive-genie-server`
- **Network**: `automagik-hive_genie_default`

## Files
- `Dockerfile` - Genie all-in-one container
- `docker-compose.yml` - Genie services orchestration

## Usage
```bash
# Start genie environment services
docker compose -f docker/genie/docker-compose.yml up -d

# Stop genie environment
docker compose -f docker/genie/docker-compose.yml down

# View logs
docker compose -f docker/genie/docker-compose.yml logs -f
```

## Integration
The Genie environment is typically used for specialized consultation workflows and advanced AI operations.