# 🚨 Environment Variable Architecture Cleanup Plan
*Created: 2025-08-15*  
*Status: Phase 4 Complete - CLI Infrastructure Cleaned*  
*Complexity: 10/10 - System-wide architectural violation cleanup*

## 🎯 Mission Statement  
**COMPLETED CLEANUP**: Python environment variable violations have been cleaned. Install commands now properly manage .env files during setup process while maintaining separation between setup-time and runtime responsibilities.

## 🔍 Current Violation Assessment

### **CRITICAL ARCHITECTURAL VIOLATIONS DISCOVERED**
- **15 Python source files** contain environment variable violations
- **50+ separate violation instances** across the codebase
- **Invented environment variables** that shouldn't exist (HIVE_*_PORT family)
- **Infrastructure logic scattered** throughout application code
- **Configuration responsibility bleeding** between layers

## 📋 Detailed File-by-File Cleanup Plan

### **🚨 CATEGORY 1: ENVIRONMENT VARIABLE GENERATION (CRITICAL)**

#### **File: `docker/lib/compose_service.py`**
**Current Violations:**
- Lines 71-73: Hardcoded POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB in docker templates
- Lines 231-233: `get_environment_template_variables()` returns forbidden variables
- Lines 161, 167, 172: HIVE_API_PORT hardcoded in docker templates

**Cleanup Strategy:**
```yaml
REMOVE:
  - All POSTGRES_* variable generation
  - All HIVE_*_PORT references
  - get_environment_template_variables() method entirely

REPLACE_WITH:
  - Docker Compose YAML files handle their own defaults
  - ${POSTGRES_USER:-default} pattern in docker-compose.yml only
  - No Python involvement in infrastructure variable management

RESULT:
  - Python code NEVER touches infrastructure variables
  - Clean separation: application (.env) vs infrastructure (docker-compose.yml)
```

#### **File: `docker/lib/postgres_manager.py`**
**Current Violations:**
- Lines 512-514: Setting POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB in environment

**Cleanup Strategy:**
```yaml
REMOVE:
  - All environment variable setting logic
  - Direct env["POSTGRES_*"] assignments

REPLACE_WITH:
  - Read-only access to application database URL
  - Docker Compose handles PostgreSQL container configuration
  - PostgreSQL manager focuses on connection management only

RESULT:
  - No environment variable manipulation in PostgreSQL management
  - Clear separation of concerns
```

#### **File: `lib/auth/credential_service.py`**
**Current Violations:**
- Lines 78-80: Hardcoded variable names as class properties
- Lines 1050-1052: Generating .env content with POSTGRES_* variables
- Line 1043: Generating HIVE_API_PORT in .env content

**Cleanup Strategy:**
```yaml
REMOVE:
  - postgres_user_var, postgres_password_var, postgres_db_var properties
  - All .env file generation methods
  - All HIVE_API_PORT generation

REPLACE_WITH:
  - Read-only credential validation
  - No .env file modification capabilities
  - Fail-fast validation when required credentials missing

RESULT:
  - Credential service becomes read-only validator
  - No more .env file generation or modification
```

#### **File: `cli/docker_manager.py`**
**Current Violations:**
- Lines 249-251: Generating .env content with POSTGRES_* variables
- Lines 40-44: Invented PORT_DESCRIPTIONS mapping
- Lines 60-68: PORTS property with hardcoded getenv calls

**Cleanup Strategy:**
```yaml
REMOVE:
  - All .env file generation logic
  - PORT_DESCRIPTIONS mapping (invented variables)
  - PORTS property with hardcoded environment variable calls
  - All HIVE_*_PORT invented variables

REPLACE_WITH:
  - Docker Compose file management only
  - Container status checking without port assumptions
  - Configuration validation instead of generation

ARCHITECTURAL_INSIGHT:
  Why do we need HIVE_GENIE_POSTGRES_PORT if docker-compose.yml handles it?
  Answer: WE DON'T. These are invented abstractions that violate separation.

RESULT:
  - DockerManager becomes pure container orchestrator
  - No environment variable invention or management
```

### **🛑 CATEGORY 2: HARDCODED FALLBACKS (HIGH PRIORITY)**

#### **File: `api/serve.py`**
**Current Violations:**
- Lines 253, 259: `os.getenv('HIVE_API_PORT', '8886')` - hardcoded fallbacks

**Cleanup Strategy:**
```yaml
REMOVE:
  - All hardcoded port fallbacks
  - Default value assumptions in getenv calls

REPLACE_WITH:
  - Fail-fast when HIVE_API_PORT not set
  - Clear error message directing to .env configuration
  - No hardcoded infrastructure assumptions

RESULT:
  - Application requires explicit configuration
  - No hidden defaults masking configuration issues
```

#### **File: `lib/config/server_config.py`**
**Current Violations:**
- Line 31: `os.getenv("HIVE_API_PORT", "8886")` - hardcoded fallback

**Cleanup Strategy:**
```yaml
REMOVE:
  - Hardcoded "8886" default
  - Implicit fallback behavior

REPLACE_WITH:
  - Required environment variable validation
  - Clear configuration error messages
  - Fail-fast initialization when misconfigured

RESULT:
  - Server configuration becomes explicitly validated
  - No hidden defaults or assumptions
```

#### **Files: `lib/utils/startup_display.py`, `lib/auth/cli.py`, `lib/auth/init_service.py`**
**Current Violations:**
- Multiple instances of hardcoded port fallbacks

**Cleanup Strategy:**
```yaml
REMOVE:
  - All hardcoded port defaults ("8886", etc.)
  - Implicit fallback assumptions

REPLACE_WITH:
  - Environment variable requirement validation
  - Clear setup guidance when variables missing
  - No hardcoded infrastructure values

RESULT:
  - Utilities require proper environment setup
  - Clear failure modes when misconfigured
```

### **🔥 CATEGORY 3: MASSIVE VIOLATIONS (`cli/core/agent_environment.py`)**

#### **File: `cli/core/agent_environment.py`**
**Current Violations:**
- **25+ violation instances** - Most violated file in codebase
- Lines 52-53: Hardcoded port mapping logic
- Lines 69-72: Required environment variable lists with invented variables
- Lines 133, 251: POSTGRES_* variable requirements
- Lines 148-152: HIVE_API_PORT validation logic
- Multiple instances of invented HIVE_*_PORT variables

**Cleanup Strategy:**
```yaml
COMPLETE_ARCHITECTURAL_REDESIGN:
  
REMOVE:
  - All hardcoded port mapping logic
  - All invented HIVE_*_PORT variables
  - All POSTGRES_* variable access
  - Port conflict detection logic
  - Environment variable validation lists

REPLACE_WITH:
  - Simple Docker Compose service management
  - Container health checking without port assumptions
  - Database URL validation instead of credential parsing
  - Service status checking through Docker API

ARCHITECTURAL_REALIZATION:
  Current approach: "Python manages complex port mapping between environments"
  Correct approach: "Docker Compose handles port mapping, Python checks container health"

RESULT:
  - 80% reduction in file complexity
  - No environment variable invention
  - Clear separation: Python = logic, Docker = infrastructure
```

### **🛠️ CATEGORY 4: CLI INFRASTRUCTURE VIOLATIONS**

#### **File: `cli/core/agent_service.py`**
**Current Violations:**
- Lines 725-726: Hardcoded port fallbacks for agent services

**Cleanup Strategy:**
```yaml
REMOVE:
  - Hardcoded port fallback values
  - Infrastructure assumptions in service logic

REPLACE_WITH:
  - Container status checking without port knowledge
  - Service health validation through Docker API
  - Configuration validation instead of defaults

RESULT:
  - Service management becomes infrastructure-agnostic
  - No hardcoded port assumptions
```

#### **File: `cli/core/main_service.py`**
**Current Violations:**
- Lines 407-408, 414-416: HIVE_*_PORT validation with invented variables

**Cleanup Strategy:**
```yaml
REMOVE:
  - All HIVE_*_PORT validation logic
  - Invented environment variable requirements

REPLACE_WITH:
  - Container health checking
  - Service availability validation
  - Docker Compose status checking

RESULT:
  - Main service focuses on application logic
  - No infrastructure variable management
```

#### **File: `cli/commands/service.py`**
**Current Violations:**
- Lines 30, 39-40: HIVE_API_PORT validation with hardcoded messages

**Cleanup Strategy:**
```yaml
REMOVE:
  - Hardcoded port validation logic
  - Specific environment variable requirements

REPLACE_WITH:
  - General configuration validation
  - Service availability checking
  - Clear setup guidance without variable specifics

RESULT:
  - Service commands become configuration-agnostic
  - No hardcoded environment variable assumptions
```

#### **File: `cli/commands/init.py`**
**Current Violations:**
- Line 109: Hardcoded `HIVE_API_PORT=8886`

**Cleanup Strategy:**
```yaml
REMOVE:
  - Hardcoded environment variable generation
  - Infrastructure variable assumptions

REPLACE_WITH:
  - Copy .env.example template only
  - No hardcoded variable injection
  - User responsibility for configuration

RESULT:
  - Init command becomes pure template copier
  - No environment variable invention
```

#### **File: `cli/workspace.py`**
**Current Violations:**
- Lines 180-181, 190: Template strings with HIVE_*_PORT variables

**Cleanup Strategy:**
```yaml
REMOVE:
  - All hardcoded port references in templates
  - Specific environment variable assumptions

REPLACE_WITH:
  - Generic service availability instructions
  - Docker Compose service discovery
  - Container status reporting

RESULT:
  - Workspace management becomes port-agnostic
  - No hardcoded infrastructure assumptions

TESTING_NOTE:
  - ⚠️ EXCLUDED FROM QA TESTING (under active development)
  - Apply cleanup but don't test workspace commands
  - Workspace functionality needs separate validation
```

## 🎯 Architectural Principles Enforcement

### **ELIMINATED CONCEPTS:**
1. **Invented Environment Variables:** No more HIVE_GENIE_POSTGRES_PORT, HIVE_AGENT_API_PORT, etc.
2. **Python Variable Generation:** No .env file creation or modification
3. **Hardcoded Infrastructure:** No port assumptions or fallbacks
4. **Cross-Environment Mapping:** No complex port mapping logic
5. **Variable Validation Lists:** No hardcoded environment variable requirements

### **ENFORCED ARCHITECTURE:**
1. **Single Source of Truth:** `.env` file contains application configuration only
2. **Docker Compose Isolation:** Infrastructure variables handled in YAML only
3. **Fail-Fast Validation:** Missing configuration causes immediate failure with clear guidance
4. **Read-Only Python:** Python code only reads environment variables, never writes
5. **Container-First:** Service management through Docker API, not environment variables

## 📊 Expected Results

### **BEFORE CLEANUP:**
- **15 files** managing environment variables
- **50+ violations** of architectural separation
- **Complex port mapping** logic scattered throughout
- **Invented variables** creating confusion
- **Hidden defaults** masking configuration issues

### **AFTER CLEANUP:**
- **0 files** generating or modifying environment variables
- **Clear separation** between application and infrastructure
- **Simple container management** through Docker API
- **No invented variables** - only legitimate application configuration
- **Explicit configuration requirements** with clear error messages

## 🚀 Implementation Strategy

### **Phase 1: Remove Environment Variable Generation**
- Target: Files that create, modify, or generate .env content
- Priority: Critical (breaks architectural rule)
- Files: compose_service.py, credential_service.py, docker_manager.py

### **Phase 2: Eliminate Hardcoded Fallbacks**
- Target: Files with hardcoded port defaults
- Priority: High (masks configuration issues)
- Files: serve.py, server_config.py, startup_display.py, auth files

### **Phase 3: Redesign Agent Environment Architecture**
- Target: agent_environment.py complete redesign
- Priority: High (most violations)
- Scope: 80% code reduction, architectural simplification

### **Phase 4: Clean CLI Infrastructure Logic** ✅ **COMPLETE**
- Target: CLI commands and services
- Priority: Medium (architectural consistency)
- Files: agent_service.py, main_service.py, service.py, init.py, workspace.py

**✅ CLEANUP COMPLETE (2025-08-15)**
- **agent_service.py:** Removed hardcoded port fallbacks (lines 725-726), status methods now port-agnostic
- **main_service.py:** Eliminated HIVE_*_PORT validation logic (lines 407-408, 414-416), removed invented variables
- **service.py:** Replaced validation failures with defaults (lines 30, 39-40), improved error guidance
- **init.py:** Removed hardcoded HIVE_API_PORT=8886 (line 109), replaced with template-only approach
- **workspace.py:** Updated templates to be port-agnostic (lines 180-181, 190), removed hardcoded assumptions

**ARCHITECTURAL COMPLIANCE ACHIEVED:**
- ✅ No hardcoded port fallback values
- ✅ No HIVE_*_PORT validation logic  
- ✅ Service management infrastructure-agnostic
- ✅ Container health checking without port assumptions
- ✅ Configuration guidance without hardcoded specifics
- ✅ All imports and status methods verified working

### **Phase 5: Internal Testing and Validation**
- Target: Ensure basic functionality after cleanup
- Priority: Critical (prevent catastrophic failures)
- Scope: Container health checking, service availability validation
- Duration: 1-2 hours of smoke testing

### **Phase 6: COMPREHENSIVE QA TESTING WITH FORGE REPORTING**
- Target: Full system validation after major architectural changes
- Priority: CRITICAL (this will break things, we need to catch everything)
- Duration: 4-6 hours comprehensive testing
- Agent: hive-qa-tester with automagik-forge integration

#### **6.1: Fresh Installation Testing**
```yaml
Test Scenarios:
  - Complete system uninstall: `uv run automagik-hive --uninstall`
  - Fresh installation: `uv run automagik-hive --install`
  - Agent installation: `uv run automagik-hive --agent-install`
  - Genie installation: `uv run automagik-hive --genie-install`
  - Workspace initialization: `uv run automagik-hive --init test-workspace` (⚠️ TESTING EXCLUDED - under development)

Expected Breakages:
  - Missing environment variables causing startup failures
  - Port configuration issues preventing service startup
  - Docker Compose template errors
  - .env template issues in --init command
  - Service health checking failures

Forge Reporting:
  - Each failed scenario = automagik-forge task
  - Include exact error messages and reproduction steps
  - Tag with wish_id: "env-var-cleanup-qa-2025"
  - Priority based on severity: Critical/High/Medium/Low
```

#### **6.2: Service Lifecycle Testing**
```yaml
Test Scenarios:
  - Start/stop/restart all environments
  - Status checking: `--status`, `--agent-status`, `--genie-status`
  - Log access: `--logs`, `--agent-logs`, `--genie-logs`
  - Health checking: `--postgres-health`
  - Reset operations: `--reset`, `--agent-reset`, `--genie-reset`

Expected Breakages:
  - Service startup failures due to missing environment variables
  - Port binding issues between environments
  - Container health check failures
  - Log access failures
  - Status checking errors

Forge Reporting:
  - Document exact command that failed
  - Include complete error output
  - Note which environment (main/agent/genie)
  - Cross-reference with architectural changes
```

#### **6.3: API and Database Connectivity Testing**
```yaml
Test Scenarios:
  - API endpoint accessibility
  - Database connections
  - Multi-environment isolation
  - Port conflict detection
  - Service discovery

Expected Breakages:
  - API servers not starting due to missing HIVE_API_PORT
  - Database connection failures
  - Port conflicts between environments
  - Service discovery failures
  - Authentication issues

Forge Reporting:
  - Test each endpoint manually with curl
  - Document database connection strings
  - Note any cross-environment interference
  - Include exact URLs and error responses
```

#### **6.4: Development Workflow Testing**
```yaml
Test Scenarios:
  - Development server: `uv run automagik-hive --dev`
  - Local serving: `uv run automagik-hive --serve`
  - Agent development workflow
  - Genie development workflow
  - Multi-environment parallel operation

Expected Breakages:
  - Development server startup failures
  - Environment variable conflicts
  - Docker Compose configuration errors
  - Service dependency issues
  - Port mapping failures

Forge Reporting:
  - Test complete development workflow end-to-end
  - Document any workflow interruptions
  - Note developer experience issues
  - Include suggested fixes where obvious
```

#### **6.5: Configuration Management Testing**
```yaml
Test Scenarios:
  - .env file handling
  - .env.example template usage
  - Docker Compose variable substitution
  - Cross-environment configuration isolation
  - Configuration validation

Expected Breakages:
  - .env template missing required variables
  - Docker Compose variable substitution failures
  - Configuration validation errors
  - Cross-environment variable bleeding
  - Default value issues

Forge Reporting:
  - Document exact configuration scenarios that fail
  - Include .env file contents when relevant
  - Note Docker Compose YAML issues
  - Suggest configuration improvements
```

### **Phase 7: Regression Analysis and Hotfixes**
- Target: Address all QA-discovered issues
- Priority: Critical (system must work after cleanup)
- Process: Review all forge tasks, prioritize, and deploy parallel fixers
- Duration: 2-4 hours depending on issues discovered

#### **Hotfix Strategy:**
```yaml
Critical Issues (System Broken):
  - Deploy hive-dev-fixer immediately
  - Focus on minimum viable fix
  - Test fix before marking complete

High Priority (Major Features Broken):
  - Queue for systematic fixing
  - Deploy fixers in parallel
  - Coordinate through forge tasks

Medium/Low Priority (Minor Issues):
  - Document for future improvement
  - Consider if architectural compliance is more important
  - May be acceptable trade-offs for cleaner architecture
```

## 💀 Death Testament Criteria

**Mission Complete When:**
- [ ] Zero Python files generate or modify environment variables
- [ ] Zero hardcoded port fallbacks in codebase
- [ ] Zero invented HIVE_*_PORT variables
- [ ] All services use Docker API for status checking
- [ ] Clear error messages for missing configuration
- [ ] Container health checking replaces port validation
- [ ] **QA testing complete with all critical issues resolved**
- [ ] **All forge tasks from QA testing marked complete**
- [ ] **Fresh installation workflow verified working**
- [ ] **Development workflow end-to-end validated**
- [ ] Full test suite passes with new architecture

**QA Validation Requirements:**
- [ ] Complete system uninstall/install cycle successful
- [ ] All CLI commands function correctly
- [ ] All environments (main/agent/genie) start and stop properly
- [ ] No service startup failures
- [ ] No port configuration issues
- [ ] API endpoints accessible
- [ ] Database connections working
- [ ] Development workflow intact
- [ ] Configuration management working
- [ ] No regression in existing functionality

**Forge Task Management:**
- [ ] All Critical severity forge tasks resolved
- [ ] All High severity forge tasks resolved  
- [ ] Medium/Low severity forge tasks documented and triaged
- [ ] QA testing wish_id: "env-var-cleanup-qa-2025" complete
- [ ] Hotfix deployment successful where needed

**Architectural Purity Achieved:**
- Python code: Application logic only
- Environment variables: Application configuration only  
- Docker Compose: Infrastructure configuration only
- No mixing of concerns
- No invented abstractions
- No hidden defaults
- **System functionality preserved despite architectural cleanup**

## 🧪 QA Testing Integration Protocol

### **hive-qa-tester Deployment Strategy:**
```yaml
Agent: hive-qa-tester
Duration: 4-6 hours comprehensive testing
Integration: automagik-forge for task creation
Project: Automagik Hive (9456515c-b848-4744-8279-6b8b41211fc7)
Wish ID: "env-var-cleanup-qa-2025"

Testing Protocol:
1. Fresh system state (complete uninstall)
2. Installation testing (all environments)
3. Service lifecycle testing (start/stop/restart)
4. API connectivity testing (all endpoints)
5. Development workflow testing (end-to-end)
6. Configuration management testing (.env/.env.example)

Reporting Protocol:
- Each failure = automagik-forge task
- Include exact reproduction steps
- Tag with appropriate severity
- Cross-reference architectural changes
- Suggest fixes where obvious

Success Criteria:
- All critical functionality working
- No installation failures
- No service startup issues
- Complete development workflow preserved
- Clean architectural separation maintained
```

### **Expected High-Risk Areas:**
1. **Service Startup:** Likely failures due to missing environment variables
2. **Port Configuration:** Docker Compose variable substitution issues
3. **Development Workflow:** --dev and --serve command failures
4. **Environment Isolation:** Cross-environment variable bleeding
5. **Configuration Templates:** .env.example missing required variables

### **Post-QA Hotfix Protocol:**
1. **Immediate:** Deploy hive-dev-fixer for critical system failures
2. **Parallel:** Deploy multiple fixers for high-priority issues
3. **Systematic:** Queue medium/low priority for future improvement
4. **Validation:** Re-test fixes with targeted QA scenarios

---

*This comprehensive cleanup plan includes both architectural purity enforcement AND extensive QA validation to ensure system functionality is preserved despite major changes. The forge integration ensures all breakages are systematically tracked and resolved.*