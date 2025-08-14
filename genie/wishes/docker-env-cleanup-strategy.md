# Docker Environment Configuration Cleanup Strategy

## 🎯 WISH: Clean Docker .env Configuration Violations

**Original Request**: "we recently refactored all the docker stuff, where the agent instance came first then main.. where my objective was to use the main .env and only override the needed parameters, however i notice the codebase still has .env and .env.* inside these folders, where they shouldnt.... investigate the whole docker folder, and lets plan this fix."

## 🔍 Investigation Results

**Current Violations Found**:
- `docker/agent/.env` - Contains orphaned agent-specific config
- `docker/main/.env` - Contains orphaned main-specific config  
- `docker/genie/.env` - Contains orphaned genie-specific config
- Various `.env.template` files scattered in subdirectories

**Correct Implementation Pattern** (from docker/agent):
- Inherits from `../../.env` via `env_file`
- Overrides only necessary values in `environment:` section
- No local .env files needed

## 📋 PROPOSED PLAN

### Phase 1: Cleanup
**Agent**: hive-dev-fixer
**Task**: Remove all orphaned .env files from docker subdirectories
**Files to Remove**:
- `docker/agent/.env`
- `docker/main/.env` 
- `docker/genie/.env`
- All `.env.template` files in docker/

### Phase 2: Validation
**Agent**: Direct validation via Bash
**Task**: Verify all docker-compose.yml files properly inherit from root .env
**Expected Pattern**:
```yaml
env_file:
  - ../../.env  # Inherit from root
environment:
  - SPECIFIC_OVERRIDE=value  # Override only what's needed
```

### Phase 3: Testing
**Agent**: Direct testing via Docker commands
**Task**: Ensure all containers can start with unified .env approach

## 🎯 EXPECTED OUTCOME
- Only root `.env.example` and `.env` exist
- All docker-compose.yml files inherit from root and override minimally
- Clean unified configuration without duplicated files

## 📊 SUCCESS CRITERIA
- Zero orphaned .env files in docker subdirectories
- All containers start successfully with unified configuration
- Configuration inheritance properly validated

**STATUS**: AWAITING USER APPROVAL