# Docker Compose Configuration Analysis Report - REVISED

## 🔍 DETAILED INVESTIGATION FINDINGS - UPDATED

**Request**: "reanalyze and update the file with updated findings and the action plan, per module"

**User Feedback**:
1. Main docker compose should use .env variables WITHOUT any override
2. Genie container should replicate Agent pattern exactly (newer pattern)  
3. Include Genie CLI commands review to match Agent pattern
4. Provide per-module action plan

---

## 📋 REVISED DETAILED FINDINGS

### 1. **Environment Variable Strategy Assessment**

#### ✅ REFERENCE PATTERN: Agent Container (`docker/agent/docker-compose.yml`)
```yaml
services:
  agent-postgres:
    env_file:
      - ../../.env  # ✅ Inherits from root
    environment:
      # ✅ Overrides for isolation
      - POSTGRES_USER=test_user
      - POSTGRES_PASSWORD=test_pass
      - POSTGRES_DB=hive_agent
  agent-api:
    env_file:
      - ../../.env  # ✅ Inherits from root  
    environment:
      # ✅ Service-specific overrides
      - HIVE_API_PORT=38886
      - HIVE_DATABASE_URL=postgresql+psycopg://test_user:test_pass@agent-postgres:5432/hive_agent
      - HIVE_API_KEY=agent-test-key-12345
```

#### ✅ CORRECT AS-IS: Main Container (`docker/main/docker-compose.yml`)
```yaml
services:
  postgres:
    env_file:
      - ../../.env  # ✅ Pure .env inheritance
    environment:
      - PGDATA=/var/lib/postgresql/data/pgdata  # ✅ Only structural config
  app:
    env_file:
      - ../../.env  # ✅ Pure .env inheritance
    environment:
      - RUNTIME_ENV=prd  # ✅ Only deployment flag
```
**Analysis**: Main container is CORRECT - uses pure .env inheritance as intended

#### ❌ VIOLATES PATTERN: Genie Container (`docker/genie/docker-compose.yml`)
```yaml
services:
  postgres-genie:
    env_file:
      - ../../.env  # ✅ Inherits from root
    environment:
      # ❌ Should follow Agent pattern but with different ports/credentials
      - POSTGRES_USER=genie_user    # Different from Agent pattern
      - POSTGRES_PASSWORD=genie_secure_pass  # Different from Agent pattern
      - POSTGRES_DB=hive_genie       # Different from Agent pattern
```

### 2. **Port Configuration Analysis**

#### Current Port Allocation:
- **Agent**: Hardcoded ports (`35532` postgres, `38886` API) ✅ **ISOLATED**
- **Main**: Variable ports (`${HIVE_DATABASE_PORT:-5532}`, `${HIVE_API_PORT:-8886}`) ✅ **CONFIGURABLE**
- **Genie**: Hardcoded ports (`48532` postgres, `48886` API) ✅ **ISOLATED**

**Analysis**: Port strategies are appropriate for each use case:
- Agent/Genie = Isolated development environments with fixed ports
- Main = Production deployment with configurable ports

### 3. **CLI Command Coverage Analysis**

#### ✅ Agent CLI Commands (Complete):
```bash
--agent-install   # Install and start agent services
--agent-serve     # Start agent services (if stopped) 
--agent-stop      # Stop agent services
--agent-restart   # Restart agent services
--agent-logs      # Show agent logs
--agent-status    # Check agent status
```

#### ❌ Genie CLI Commands (MISSING):
```bash
# EXPECTED but NOT FOUND:
--genie-install   # Should exist
--genie-serve     # Should exist
--genie-stop      # Should exist  
--genie-restart   # Should exist
--genie-logs      # Should exist
--genie-status    # Should exist
```

**Critical Gap**: Genie container has no CLI management commands despite having docker-compose setup

### 4. **Root .env Configuration Analysis**

#### Required Variables Missing from .env.example:
```bash
# Found in .env.example:
POSTGRES_UID=1000
POSTGRES_GID=1000

# MISSING - Required for main container:
POSTGRES_USER=hive_user
POSTGRES_PASSWORD=your-secure-password-here  
POSTGRES_DB=hive
```

**Issue**: Main container healthcheck will fail because .env.example doesn't define POSTGRES_* connection variables

---

## 🚨 CRITICAL ISSUES IDENTIFIED

### Issue #1: Genie Container Pattern Violation
**Severity**: HIGH  
**Impact**: Genie doesn't follow the established Agent pattern
**Root Cause**: Genie was not updated to match Agent pattern despite being newer

### Issue #2: Missing Genie CLI Commands
**Severity**: HIGH
**Impact**: No way to manage Genie container via CLI like Agent
**Root Cause**: CLI commands were never implemented for Genie

### Issue #3: Main Container Missing .env Variables 
**Severity**: MEDIUM
**Impact**: Main postgres healthcheck will fail with current .env.example
**Root Cause**: .env.example missing POSTGRES_* connection variables

### Issue #4: RUNTIME_ENV Mystery Variable ✅ RESOLVED
**Severity**: HIGH → **FIXED**
**Impact**: Unknown variable hardcoded in containers, not documented
**Root Cause**: RUNTIME_ENV=prd existed in main/agent/genie but served no purpose
**Resolution**: **WIPED** - Removed from all docker-compose files and docker/lib/compose_service.py

### Issue #5: Potential .env Path Corruption  
**Severity**: CRITICAL
**Impact**: Main container may not be loading correct .env file
**Root Cause**: Recent commit "docker configuration cleanup" may have altered .env paths
**Evidence**: User suspects recent override, needs verification

---

## 🔧 PER-MODULE ACTION PLAN

### 🎯 MODULE 1: Main Container (`docker/main/`) - ⚠️ CRITICAL REVIEW NEEDED
**Status**: ❌ **REQUIRES VERIFICATION** - Potential corruption detected  
**Critical Issues**:

#### Issue 1.1: Verify .env Path Correctness
**Current**: `../../.env` (Lines 14, 46)
**Question**: Is this the correct path or was it corrupted in recent commits?
**Action**: VERIFY this should be `../../.env` and not something else

#### Issue 1.2: RUNTIME_ENV Mystery Variable  
**Current**: `- RUNTIME_ENV=prd` (Line 48)
**Issues**: 
- Not in .env.example
- Not documented what it does  
- Hardcoded to "prd" - should this be configurable?
- Why does main container need deployment environment flag?

#### Issue 1.3: Add Missing Variables to .env.example
```bash
# Add to .env.example:
POSTGRES_USER=hive_user
POSTGRES_PASSWORD=your-secure-password-here  
POSTGRES_DB=hive
RUNTIME_ENV=development  # Or remove from docker-compose entirely?
```

### 🎯 MODULE 2: Genie Container (`docker/genie/`) - HIGH PRIORITY
**Status**: ❌ **REQUIRES COMPLETE RESTRUCTURE** to match Agent pattern

#### Action 2.1: Update Genie Docker Compose
**Target Pattern**: Replicate Agent structure exactly with different ports/credentials
```yaml
# docker/genie/docker-compose.yml - COMPLETE REWRITE NEEDED
services:
  genie-postgres:  # Rename from postgres-genie
    image: agnohq/pgvector:16
    container_name: hive-genie-postgres  # Match Agent naming
    ports:
      - "48532:5432"  # Keep different port
    env_file:
      - ../../.env
    environment:
      # Follow Agent pattern exactly:
      - POSTGRES_USER=genie_test_user
      - POSTGRES_PASSWORD=genie_test_pass  
      - POSTGRES_DB=hive_genie
      - PGDATA=/var/lib/postgresql/data/pgdata
    # Remove: user: "1000:1000" (like Agent - no user restrictions)
    # Remove: volumes (like Agent - ephemeral storage)
    
  genie-api:  # Rename from genie-server
    container_name: hive-genie-api  # Match Agent naming
    ports:
      - "48886:48886"  # Keep different port
    environment:
      # Follow Agent pattern exactly:
      - HIVE_API_PORT=48886
      - HIVE_DATABASE_URL=postgresql+psycopg://genie_test_user:genie_test_pass@genie-postgres:5432/hive_genie
      - HIVE_API_KEY=genie-test-key-12345
      - RUNTIME_ENV=prd
```

#### Action 2.2: Implement Missing Genie CLI Commands
**Target**: Create complete CLI command suite matching Agent pattern
```python
# cli/main.py - ADD THESE ARGUMENTS:
parser.add_argument("--genie-install", nargs="?", const=".", metavar="WORKSPACE", help="Install and start genie services")
parser.add_argument("--genie-serve", nargs="?", const=".", metavar="WORKSPACE", help="Start genie services")  
parser.add_argument("--genie-stop", nargs="?", const=".", metavar="WORKSPACE", help="Stop genie services")
parser.add_argument("--genie-restart", nargs="?", const=".", metavar="WORKSPACE", help="Restart genie services")
parser.add_argument("--genie-logs", nargs="?", const=".", metavar="WORKSPACE", help="Show genie logs")
parser.add_argument("--genie-status", nargs="?", const=".", metavar="WORKSPACE", help="Check genie status")
```

**Required**: Create `cli/commands/genie.py` - EXACT copy of `cli/commands/agent.py` with port changes

### 🎯 MODULE 3: Agent Container (`docker/agent/`) - REFERENCE STANDARD  
**Status**: ✅ **PERFECT** - This is the pattern to replicate
**Action**: No changes needed - this is the reference implementation

---

## 🚀 IMPLEMENTATION PRIORITY

### Phase 1: Fix .env.example (IMMEDIATE)
- Add missing POSTGRES_* variables to support main container

### Phase 2: Restructure Genie Container (HIGH PRIORITY)  
- Rewrite genie docker-compose.yml to match Agent pattern exactly
- Remove persistent volumes (use ephemeral like Agent)
- Remove hardcoded user permissions
- Rename services to match Agent convention

### Phase 3: Implement Genie CLI Commands (HIGH PRIORITY)
- Create cli/commands/genie.py based on agent.py
- Add CLI argument parsing for all genie commands
- Test complete genie lifecycle management

### Phase 4: Validation Testing (FINAL)
- Test all three containers start/stop correctly
- Verify CLI commands work for both agent and genie  
- Validate unified .env inheritance works across all modules

---

## 🧪 DETAILED TESTING PLAN

### Test 1: .env.example Validation
```bash
# Copy .env.example to .env and test main container
cp .env.example .env
cd docker/main && docker compose up -d
docker compose ps  # Should show healthy
```

### Test 2: Genie Pattern Compliance  
```bash
# After genie restructure, test matches agent behavior
cd docker/genie && docker compose up -d
cd docker/agent && docker compose up -d  
# Both should behave identically (different ports)
```

### Test 3: CLI Command Parity
```bash
# Test both agent and genie CLI commands work identically
uv run automagik-hive --agent-status
uv run automagik-hive --genie-status  # Should work after implementation
```

---

## 📊 REVISED SUMMARY

**Critical Finding**: Genie container is incomplete - missing CLI commands and doesn't follow the established Agent pattern despite being newer.

**Recommendation**: Complete Genie implementation to match Agent pattern exactly, then validate all three containers work with unified .env strategy.

**Impact**: High-impact changes needed for Genie module to achieve consistency and CLI management capability.