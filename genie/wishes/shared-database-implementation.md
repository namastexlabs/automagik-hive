# Shared Database Implementation Plan

## Overview
Implement shared database approach with schema separation as specified in the technical requirements.

## Key Changes Required

### 1. CredentialService Updates

#### Database Configuration Changes
- Update `DATABASES` mapping: All modes use 'hive' database
- Update `PORT_PREFIXES`: All modes share postgres port 5532  
- Add `CONTAINERS` mapping for shared container approach

#### Connection String Updates
- Add schema-specific connection strings for agent/genie modes
- Workspace uses default public schema
- Agent/genie modes use `?options=-csearch_path={mode}` parameter

#### Port Calculation Updates  
- Shared postgres port 5532 for all modes
- Only API ports get prefixed (workspace: 8886, agent: 38886, genie: 48886)

### 2. Docker Management Updates

#### Container Naming
- Use shared postgres container: `hive-postgres-shared`
- Keep separate API containers per mode

#### Installation Logic
- Check for existing shared postgres container first
- Reuse existing container if found
- Create shared container if none exists

### 3. Schema Management

#### Automatic Schema Creation
- Ensure agent/genie schemas exist on first connection
- Integrate with Agno framework's database initialization

#### Migration Support
- Detect existing separate database setups
- Offer migration to shared approach
- Preserve existing data during migration

## Implementation Steps

1. Update CredentialService configuration constants
2. Modify port calculation logic for shared postgres
3. Update connection string generation with schema separation
4. Add schema management functions
5. Update Docker container management
6. Test backward compatibility
7. Add migration support

## Critical Requirements

- **Preserve backward compatibility**: Existing installations continue working
- **Automatic detection**: System detects and reuses existing postgres containers
- **Schema isolation**: Each mode gets its own schema namespace  
- **Single source of truth**: Both `make install` and `uv run install` use same database

## Testing Requirements

- Verify `make install` creates shared postgres container on port 5532
- Verify `uv run automagik-hive --install workspace` uses the same container
- Verify schema separation works correctly
- Verify existing installations can migrate smoothly