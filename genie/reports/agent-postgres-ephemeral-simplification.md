# Agent PostgreSQL Ephemeral Storage Simplification

## Problem Statement
The agent PostgreSQL setup was unnecessarily complex with external data folder mapping, creating complications for testing and reset operations.

## Solution Implemented
Made PostgreSQL completely ephemeral by removing external data folder dependencies.

## Changes Made

### 1. Docker Compose Simplification
**File**: `docker/agent/docker-compose.yml`
- **Removed**: External volume mapping `../../data/postgres-agent:/var/lib/postgresql/data`
- **Added**: Clear documentation that PostgreSQL uses ephemeral storage
- **Result**: Each container restart creates a fresh database

### 2. Agent Service Code Cleanup  
**File**: `cli/core/agent_service.py`
- **Removed**: Complex data directory creation logic (lines 190-216)
- **Removed**: Data directory cleanup logic in reset process (lines 643-651)
- **Simplified**: PostgreSQL setup now just starts the container
- **Result**: No external directory management needed

## Benefits Achieved

### ✅ Simplicity
- No external data folder creation or permission management
- Cleaner Docker Compose configuration
- Simplified reset process

### ✅ Testing Optimized
- Each container restart = fresh database (perfect for agent testing)
- No state pollution between test runs
- No cleanup of external directories needed

### ✅ Reliability
- Eliminated permission issues with external directories
- No dependency on host filesystem permissions
- Consistent behavior across different environments

## Technical Validation

### Docker Compose Validation
```bash
$ docker compose config --quiet
# ✅ Configuration is valid

$ docker compose config | grep -A 10 postgres-agent
# ✅ No volume mappings present
```

### Python Syntax Validation
```bash
$ python -m py_compile cli/core/agent_service.py
# ✅ Syntax is valid
```

## Expected Behavior Changes

### Before (Complex)
1. Create external `data/postgres-agent` directory
2. Set correct permissions (1000:1000)
3. Start PostgreSQL with external volume
4. Reset = stop + cleanup directory + recreate + restart

### After (Simple) 
1. Start PostgreSQL with ephemeral storage
2. Reset = simple container restart
3. Fresh database every time

## Migration Notes
- Existing `data/postgres-agent` directories can be safely deleted
- No data loss concerns since this is for agent testing (ephemeral by design)
- Agent development workflows remain exactly the same

## Conclusion
Successfully simplified the agent PostgreSQL architecture while maintaining full functionality. The system is now cleaner, more reliable, and perfectly suited for agent testing with fresh databases on each reset.