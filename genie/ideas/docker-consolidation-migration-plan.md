# Docker Consolidation Migration Execution Plan

## CURRENT STATE ANALYSIS

### Files to Migrate
**Root Docker Files:**
- `Dockerfile` → `docker/main/Dockerfile`
- `Dockerfile.agent` → `docker/agent/Dockerfile`  
- `Dockerfile.genie` → `docker/genie/Dockerfile`
- `.dockerignore` → `docker/main/.dockerignore`

**Compose Files:**
- `docker-compose.yml` → `docker/main/docker-compose.yml`
- `docker-compose-agent.yml` → `docker/agent/docker-compose.yml`
- `docker-compose-genie.yml` → `docker/genie/docker-compose.yml`

**Templates Directory:**
- `templates/docker-compose-genie.yml` → `docker/templates/genie.yml`
- `templates/docker-compose-workspace.yml` → `docker/templates/workspace.yml`

**Docker Libraries:**
- `lib/docker/` → `docker/lib/`

**Scripts:**
- `scripts/validate-docker-compose.sh` → `docker/scripts/validate.sh`

### Reference Updates Required

**Makefile (33 references):**
- Line 33: `DOCKER_COMPOSE_FILE := docker-compose.yml` → `docker/main/docker-compose.yml`
- Line 299: `docker-compose-agent.yml` → `docker/agent/docker-compose.yml`
- Line 306: `docker-compose-agent.yml` → `docker/agent/docker-compose.yml`
- Line 459: `$(DOCKER_COMPOSE_FILE)` → uses variable (already correct)
- Line 626: `docker-compose-agent.yml` → `docker/agent/docker-compose.yml`

**Scripts (validate-docker-compose.sh):**
- Multiple references to compose files need updating

**Python Imports:**
- All `from lib.docker` → `from docker.lib`
- All `lib.docker` → `docker.lib`

## MIGRATION EXECUTION PHASES

### Phase 1: Create Target Structure & Backup
### Phase 2: Migrate Files with Atomic Operations  
### Phase 3: Update All References
### Phase 4: Comprehensive Validation

## ROLLBACK STRATEGY
- Complete backup in `docker-migration-backup-{timestamp}/`
- Git checkpoint before migration
- Atomic rollback procedure available