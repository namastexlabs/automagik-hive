# 🏗️ Environment Variable Architecture Cleanup - Detailed Design Document (DDD)

*Created: 2025-08-15*  
*Agent: hive-dev-designer*  
*Complexity Score: 9/10*  
*Source TSD: /genie/wishes/environment-variable-cleanup-2025.md*

## 🎯 Executive Summary

This DDD defines the complete architectural redesign for eliminating Python code violations of the environment variable separation principle. The current system suffers from critical architectural boundary violations where application code inappropriately manages infrastructure configuration, creating a brittle, complex, and unmaintainable system.

**Core Problem**: 15 Python files with 50+ violations inappropriately generate, modify, or hardcode environment variables, violating Clean Architecture principles.

**Target Architecture**: Pure separation where Python handles application logic only, Docker Compose manages infrastructure declaratively, and .env contains application configuration exclusively.

## 🔍 Current Architecture Analysis

### **Critical Violations Confirmed**

**Category 1: Environment Variable Generation (CRITICAL)**
- `docker/lib/compose_service.py`: Generates POSTGRES_* variables in Docker templates
- `lib/auth/credential_service.py`: Creates complete .env files with infrastructure variables  
- `cli/docker_manager.py`: Duplicates .env generation for Docker containers
- `docker/lib/postgres_manager.py`: Sets environment variables programmatically

**Category 2: Hardcoded Fallbacks (HIGH PRIORITY)**
- `api/serve.py`: `os.getenv('HIVE_API_PORT', '8886')` pattern
- `lib/config/server_config.py`: Default port assumptions
- Multiple CLI utilities with hardcoded infrastructure defaults

**Category 3: Invented Infrastructure Variables (MASSIVE VIOLATIONS)**
- `cli/core/agent_environment.py`: 25+ violations with invented HIVE_*_PORT variables
- Complex port mapping logic that belongs in Docker Compose
- Non-standard configuration validation for infrastructure concerns

**Category 4: CLI Infrastructure Logic (MEDIUM PRIORITY)**
- CLI commands with hardcoded port validation
- Service management through environment variable inspection
- Infrastructure assumptions scattered across commands

### **Existing Correct Architecture (Being Violated)**

**✅ ALREADY CORRECT PATTERNS:**
- `.env.example`: Clean application-level configuration
- `docker/main/docker-compose.yml`: Proper `${VAR:-default}` infrastructure patterns
- Environment inheritance from root .env to containers

**🚨 VIOLATION INSIGHT**: The target architecture already exists in Docker templates but is being corrupted by Python code adding unnecessary complexity.

## 🏛️ Clean Architecture Design

### **Layer Separation Principles**

```yaml
Application Layer (Python):
  Responsibility: Business logic, API endpoints, agent orchestration
  Configuration: Read-only access to application settings
  Environment Access: Centralized, validated, fail-fast configuration loading
  Prohibited: Any .env file generation or modification

Infrastructure Layer (Docker Compose):
  Responsibility: Container orchestration, port mapping, volume management
  Configuration: Declarative YAML with ${VAR:-default} substitution
  Environment Access: Inherits from .env, overrides with docker-compose patterns
  Management: Docker API for health checks and status

Configuration Layer (.env):
  Responsibility: Application runtime configuration only
  Contents: Database URLs, API keys, application settings
  Prohibited: Infrastructure variables (ports, UIDs, container settings)
  Source: Copied from .env.example template by developers
```

### **Architectural Boundaries**

```mermaid
graph TB
    A[.env File] --> B[Docker Compose]
    A --> C[Python Application]
    B --> D[Container Runtime]
    C --> E[Business Logic]
    
    A -.->|"❌ NO GENERATION"| C
    C -.->|"❌ NO MODIFICATION"| A
    C -.->|"✅ READ ONLY"| A
    B -.->|"✅ INHERITS + OVERRIDES"| A
```

## 🔧 Refactoring Patterns

### **Pattern 1: Configuration Service Redesign**

**Current (Violated):**
```python
# lib/auth/credential_service.py - VIOLATION
def create_environment_file(self, credentials: dict) -> None:
    env_content = f"""
POSTGRES_USER={credentials['postgres_user']}
POSTGRES_PASSWORD={credentials['postgres_password']}
HIVE_API_PORT={credentials['api_port']}
"""
    env_file.write_text(env_content)  # ❌ FORBIDDEN
```

**Target (Clean Architecture):**
```python
# lib/config/settings.py - NEW CENTRALIZED CONFIG
from pydantic import BaseSettings, validator
from typing import Optional

class HiveSettings(BaseSettings):
    # Application Configuration Only
    hive_api_port: int
    hive_database_url: str
    hive_api_key: str
    
    @validator('hive_api_port')
    def validate_port(cls, v):
        if not (1024 <= v <= 65535):
            raise ValueError('Port must be between 1024-65535')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Usage throughout application
settings = HiveSettings()  # Fails fast if .env misconfigured
```

### **Pattern 2: Docker Service Management**

**Current (Violated):**
```python
# cli/core/agent_environment.py - VIOLATION
def _validate_required_env_vars(self) -> None:
    required_vars = [
        "HIVE_AGENT_API_PORT",           # ❌ INVENTED
        "HIVE_AGENT_POSTGRES_PORT",      # ❌ INVENTED
    ]
    # Complex port mapping logic that belongs in Docker
```

**Target (Container-First):**
```python
# lib/services/container_service.py - NEW APPROACH
import docker
from typing import Dict, Optional

class ContainerHealthService:
    def __init__(self):
        self.client = docker.from_env()
    
    def check_service_health(self, container_name: str) -> bool:
        """Check container health via Docker API, not environment variables."""
        try:
            container = self.client.containers.get(container_name)
            return container.attrs['State']['Health']['Status'] == 'healthy'
        except docker.errors.NotFound:
            return False
    
    def get_service_status(self, container_name: str) -> Dict[str, str]:
        """Get comprehensive service status."""
        try:
            container = self.client.containers.get(container_name)
            return {
                'status': container.status,
                'health': container.attrs['State']['Health']['Status'],
                'ports': container.attrs['NetworkSettings']['Ports']
            }
        except docker.errors.NotFound:
            return {'status': 'not_found'}
```

### **Pattern 3: Environment Variable Elimination**

**Remove Entirely:**
```python
# ALL THESE PATTERNS MUST BE ELIMINATED:
os.getenv("HIVE_AGENT_API_PORT")           # ❌ INVENTED
os.getenv("HIVE_WORKSPACE_POSTGRES_PORT")  # ❌ INVENTED
os.getenv("HIVE_GENIE_POSTGRES_PORT")      # ❌ INVENTED

# Hardcoded fallbacks
os.getenv("HIVE_API_PORT", "8886")         # ❌ MASKS ISSUES
```

**Replace With:**
```python
# Centralized configuration access
from lib.config.settings import settings

# Fail-fast configuration loading
api_port = settings.hive_api_port  # ✅ VALIDATED
database_url = settings.hive_database_url  # ✅ VALIDATED
```

## 🐳 Docker Compose Integration Patterns

### **Environment Variable Inheritance**

**Root .env (Application Configuration):**
```bash
# Application-level configuration only
HIVE_API_PORT=8886
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive
HIVE_API_KEY=your-api-key-here
```

**docker-compose.yml (Infrastructure Management):**
```yaml
services:
  postgres:
    image: agnohq/pgvector:16
    ports:
      - "${HIVE_WORKSPACE_POSTGRES_PORT:-5532}:5432"  # ✅ DOCKER HANDLES DEFAULTS
    user: "${POSTGRES_UID:-1000}:${POSTGRES_GID:-1000}"  # ✅ INFRASTRUCTURE VARIABLE
    environment:
      - POSTGRES_USER=${POSTGRES_USER:-hive_user}        # ✅ DOCKER DEFAULT
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}           # ✅ FROM .env OR SHELL
      - POSTGRES_DB=${POSTGRES_DB:-hive}                 # ✅ DOCKER DEFAULT
  
  app:
    ports:
      - "${HIVE_API_PORT}:${HIVE_API_PORT}"              # ✅ INHERITS FROM .env
    env_file:
      - .env                                              # ✅ APPLICATION CONFIG
```

### **Multi-Environment Pattern**

**Agent Environment (docker/agent/docker-compose.yml):**
```yaml
services:
  postgres-agent:
    extends:
      file: ../main/docker-compose.yml
      service: postgres
    container_name: hive-agent-postgres
    ports:
      - "${HIVE_AGENT_POSTGRES_PORT:-35532}:5432"        # ✅ DIFFERENT DEFAULT
    volumes:
      - ../../data/postgres-agent:/var/lib/postgresql/data
  
  app-agent:
    extends:
      file: ../main/docker-compose.yml  
      service: app
    container_name: hive-agent-app
    ports:
      - "${HIVE_AGENT_API_PORT:-38886}:${HIVE_API_PORT}" # ✅ MAPS TO DIFFERENT PORT
```

## 🧪 Test Strategy Integration

### **Test Impact Analysis**

**Current Testing Challenges:**
- Infrastructure concerns mixed with business logic make unit testing complex
- Environment variable generation requires mocking file system operations
- Port validation logic scattered across multiple layers
- Hardcoded defaults mask actual configuration requirements in tests

**Target Testing Architecture:**

**Unit Tests (Isolated):**
```python
# tests/lib/config/test_settings.py
def test_settings_validation():
    """Test configuration validation without infrastructure concerns."""
    with pytest.raises(ValidationError):
        HiveSettings(hive_api_port=99999)  # Invalid port
    
def test_fail_fast_behavior():
    """Test that missing required config causes immediate failure."""
    with mock.patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValidationError):
            HiveSettings()  # Should fail fast
```

**Integration Tests (Container-Aware):**
```python
# tests/integration/test_container_health.py
@pytest.mark.docker
def test_container_health_service():
    """Test container health checking without environment variable dependencies."""
    health_service = ContainerHealthService()
    assert health_service.check_service_health('hive-postgres')
    
@pytest.mark.docker  
def test_multi_environment_isolation():
    """Test that agent and main environments don't interfere."""
    # Verify main postgres on 5532, agent postgres on 35532
    # No Python port mapping logic to test
```

**Test-Friendly Design Principles:**
- **Dependency Injection**: Configuration injected into services, not pulled from environment
- **Container Isolation**: Each test environment uses isolated Docker Compose stacks
- **Mock-Free Configuration**: Tests use real configuration objects, not environment mocking
- **Clear Test Boundaries**: Infrastructure tests separate from business logic tests

### **Test Architecture Components**

```python
# tests/conftest.py - Test Configuration
@pytest.fixture
def test_settings():
    """Provide test configuration without environment variable dependencies."""
    return HiveSettings(
        hive_api_port=8887,  # Test port
        hive_database_url="postgresql://test:test@localhost:5433/test_hive",
        hive_api_key="test-key"
    )

@pytest.fixture
def isolated_container_env():
    """Provide isolated Docker environment for integration tests."""
    # Spin up test-specific Docker Compose stack
    # Return container management interface
    pass
```

## 🔄 Implementation Architecture

### **Phase 1: Environment Variable Generation Elimination**

**Target Files:**
- `docker/lib/compose_service.py`
- `lib/auth/credential_service.py` 
- `cli/docker_manager.py`
- `docker/lib/postgres_manager.py`

**Refactoring Strategy:**
```python
# BEFORE: credential_service.py
def create_environment_file(self, credentials):
    # Generate .env content - VIOLATION
    
# AFTER: credential_service.py  
def validate_credentials(self) -> bool:
    """Read-only credential validation."""
    try:
        settings = HiveSettings()  # Loads from .env
        return self._validate_database_connection(settings.hive_database_url)
    except ValidationError:
        return False
```

### **Phase 2: Hardcoded Fallback Elimination**

**Pattern Replacement:**
```python
# BEFORE: Scattered throughout codebase
port = os.getenv('HIVE_API_PORT', '8886')  # ❌ MASKED FAILURE

# AFTER: Centralized configuration
from lib.config.settings import settings
port = settings.hive_api_port  # ✅ VALIDATED, FAILS FAST
```

### **Phase 3: Agent Environment Redesign**

**Complete Architectural Overhaul:**
```python
# BEFORE: cli/core/agent_environment.py (200+ lines of violation)
class AgentEnvironment:
    def _validate_required_env_vars(self):
        # Complex validation of invented variables
    def _generate_docker_compose(self):
        # Port mapping logic that belongs in Docker

# AFTER: cli/core/agent_service.py (50 lines, clean)
class AgentService:
    def __init__(self, container_service: ContainerHealthService):
        self.container_service = container_service
    
    def start_agent_environment(self) -> bool:
        """Start agent environment using Docker Compose."""
        return self._execute_compose_command('up -d')
    
    def check_agent_health(self) -> Dict[str, bool]:
        """Check agent services via container health."""
        return {
            'postgres': self.container_service.check_service_health('hive-agent-postgres'),
            'api': self.container_service.check_service_health('hive-agent-app')
        }
```

### **Phase 4: CLI Infrastructure Cleanup**

**Service Command Redesign:**
```python
# BEFORE: Complex environment variable validation
def validate_environment():
    for var in REQUIRED_VARS:  # Invented variables
        if not os.getenv(var):
            raise ValueError(f"Missing {var}")

# AFTER: Container-first service management  
def check_service_status():
    container_service = ContainerHealthService()
    return {
        'main': container_service.get_service_status('hive-main-app'),
        'agent': container_service.get_service_status('hive-agent-app'),
        'genie': container_service.get_service_status('hive-genie-app')
    }
```

## 📊 Quality Assurance Architecture

### **Comprehensive Testing Strategy**

**Fresh Installation Testing:**
```bash
# Test complete workflow without Python environment generation
uv run automagik-hive --uninstall
uv run automagik-hive --install
uv run automagik-hive --agent-install
# Verify: No Python-generated .env files, only .env.example copying
```

**Service Lifecycle Testing:**
```bash
# Test Docker-first service management
uv run automagik-hive --serve
uv run automagik-hive --agent-serve
# Verify: Container health checks work, no port validation in Python
```

**Configuration Management Testing:**
```yaml
Test Scenarios:
  - Missing .env file: Application fails fast with clear error
  - Invalid configuration: Pydantic validation catches issues at startup
  - Environment isolation: Agent/main environments don't interfere
  - Docker defaults: ${VAR:-default} patterns work correctly
```

### **Expected Breakage Areas & Mitigation**

**High-Risk Breakages:**
- Service startup failures when Python stops generating environment variables
- Port configuration issues if .env.example missing required variables
- CLI commands failing due to removed hardcoded defaults

**Mitigation Strategies:**
1. **Pre-flight Configuration Check**: Validate .env.example completeness before cleanup
2. **Fallback Documentation**: Clear error messages directing users to configuration steps
3. **Incremental Rollout**: Test each phase independently before proceeding
4. **Automated Regression Testing**: Full workflow validation after each phase

## 🎯 Success Criteria & Validation

### **Architectural Purity Metrics**

```yaml
Zero Tolerance Validation:
  - Python files generating .env content: 0 instances
  - Hardcoded fallbacks in os.getenv(): 0 instances  
  - Invented HIVE_*_PORT variables: 0 references
  - Infrastructure logic in application code: 0 violations

Quality Gates:
  - All services start via Docker Compose exclusively
  - Configuration validation centralized in single module
  - Container health checks replace port validation
  - Development workflow preserved end-to-end
```

### **Test Strategy Validation**

**Test Coverage Requirements:**
- **Configuration Module**: 100% coverage of settings validation and fail-fast behavior
- **Container Service**: 100% coverage of Docker API integration and health checks
- **CLI Commands**: End-to-end testing of service management without environment generation
- **Integration Tests**: Multi-environment isolation and Docker Compose workflow validation

**Test Architecture Improvements:**
- Elimination of environment variable mocking in favor of real configuration objects
- Clear separation between unit tests (business logic) and integration tests (container orchestration)
- Proactive test strategy for architectural compliance validation

## 🚀 Implementation Deployment Strategy

### **Phase-Gate Approach**

**Phase 1: Foundation (Configuration Service)**
- Create centralized settings module with Pydantic validation
- Replace scattered os.getenv() calls with centralized configuration access
- **Gate Criteria**: All hardcoded fallbacks eliminated, fail-fast validation working

**Phase 2: Infrastructure Separation (Docker Management)**
- Remove Python .env generation capabilities entirely
- Implement container health service for Docker API integration
- **Gate Criteria**: Zero Python files generate environment variables

**Phase 3: Agent Environment Redesign (Architectural Overhaul)**
- Complete rewrite of agent_environment.py eliminating invented variables
- Implement Docker-first service management throughout CLI
- **Gate Criteria**: Container-first management working, no port mapping in Python

**Phase 4: Validation & QA (Comprehensive Testing)**
- Execute full QA testing protocol with automagik-forge integration
- Deploy hotfixes for any critical issues discovered
- **Gate Criteria**: All critical functionality preserved, clean architecture compliance achieved

### **Rollback Strategy**

```yaml
Rollback Triggers:
  - Critical service startup failures
  - Complete development workflow breakdown
  - Data loss or corruption
  - Security vulnerabilities introduced

Rollback Mechanism:
  - Git branch strategy: feature/env-cleanup with atomic commits per phase
  - Docker image rollback: Previous working container images preserved
  - Configuration backup: .env and docker-compose.yml backups automated
  - Rapid deployment: Rollback deployment pipeline < 5 minutes
```

## 💀 Death Testament - Completion Criteria

**Mission Complete When:**
- [ ] **Zero Python files generate or modify environment variables**
- [ ] **Zero hardcoded fallbacks in application code**
- [ ] **Zero invented HIVE_*_PORT variables in codebase**
- [ ] **All service management uses Docker API exclusively**
- [ ] **Centralized configuration validation with fail-fast behavior**
- [ ] **Container health checking replaces port validation everywhere**
- [ ] **Complete development workflow preserved and validated**
- [ ] **All QA testing passed with critical issues resolved**
- [ ] **Test architecture improved with Clean Architecture compliance**

**Architectural Purity Achieved:**
- **Python Layer**: Pure application logic, read-only configuration access
- **Docker Layer**: Declarative infrastructure management with proper defaults
- **Configuration Layer**: Single source of truth in .env with validation
- **Test Layer**: Clean separation between unit and integration testing
- **No invented abstractions, no hidden defaults, no mixed concerns**

**Quality Assurance Validation:**
- Fresh installation workflow: ✅ Working
- Service lifecycle management: ✅ Working  
- Multi-environment isolation: ✅ Working
- Development workflow: ✅ Preserved
- Test suite: ✅ Enhanced and passing
- **System functionality preserved despite architectural cleanup**

---

## 🧠 Design Decisions & Rationale

### **Why Pydantic for Configuration?**
- **Type Safety**: Prevents configuration errors at runtime through compile-time validation
- **Fail-Fast**: Application won't start with invalid configuration
- **Documentation**: Configuration schema serves as living documentation
- **IDE Support**: Autocomplete and type hints improve developer experience

### **Why Docker API for Service Management?**
- **Reliability**: Docker's health check mechanism is more reliable than port inspection
- **Infrastructure Agnostic**: Works regardless of port mappings or container configuration
- **Standard Practice**: Aligns with industry-standard container orchestration patterns
- **Simplicity**: Reduces custom Python logic in favor of proven Docker tooling

### **Why Eliminate Invented Variables?**
- **Cognitive Load**: Reduces developer confusion about which variables matter
- **Maintainability**: Fewer abstractions mean fewer places for bugs to hide
- **Standards Compliance**: Aligns with Docker Compose standard practices
- **Debugging**: Easier to troubleshoot configuration issues with fewer layers

This DDD provides a comprehensive architectural blueprint for transforming the Automagik Hive's environment variable management from a violation-prone, complex system to a clean, maintainable, and scalable architecture that properly separates application and infrastructure concerns.