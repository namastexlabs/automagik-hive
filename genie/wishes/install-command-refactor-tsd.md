# Technical Specification Document: --install Command Refactor

**Version**: 2.0 - REFACTORING APPROACH
**Status**: PLANNING  
**Target Release**: MVP  
**Created**: 2025-08-15  
**Last Updated**: 2025-08-15  

---

## 🎯 Executive Summary

**Mission**: Refactor the existing `--install` command to support deployment choice between local main + PostgreSQL Docker and full Docker deployment, with intelligent credential management and .env file handling.

**Current State**: The `--install` command only supports Docker mode deployment with a missing `_generate_postgres_credentials()` method causing installation failure.

**Target State**: Enhanced existing ServiceManager with deployment mode selection, leveraging existing CredentialService for comprehensive environment setup.

**Key Insight**: Extensive existing infrastructure (CredentialService.install_all_modes, MainService) eliminates need for new files - pure refactoring approach.

---

## 📋 Requirements Analysis

### 1. User-Specified Requirements

**R1: Deployment Mode Choice**
- User selects deployment mode within --install itself
- Option A: Local main + PostgreSQL Docker  
- Option B: Main + PostgreSQL in 2 separate containers (current behavior)
- No external configuration required - choice made interactively

**R2: Environment File Management**
- If .env exists with credentials: use existing credentials
- If .env exists but missing/placeholder (as per .env.example) credentials: generate and update .env  
- If .env doesn't exist: generate from .env.example as base with real credentials

**R3: Command Scope**
- Focus ONLY on --install command refactor (workspace/main installation)
- Agent and genie installs remain separate (--agent-install, --genie-install)
- NO unification of agent/genie - they are separate systems with different ports/containers

### 2. Derived Requirements

**R4: Existing Infrastructure Reuse**
- Leverage existing CredentialService.install_all_modes() method (line 829-886)
- Enhance existing ServiceManager.install_full_environment() (line 70-87)
- Use existing MainService deployment logic with mode parameter

**R5: Dead Code Removal**
- Remove call to non-existent self._generate_postgres_credentials() (line 139)
- Remove false comment claiming method exists (line 150)
- Eliminate redundant credential patterns

**R6: User Experience Requirements**  
- Clear interactive prompts for deployment choice
- Progress indicators during installation
- Validation feedback for all operations
- Rollback capability on failures

**R7: Architecture Integration**
- Maintain compatibility with existing ServiceManager interface
- No new files creation - pure enhancement approach
- Support both deployment configurations

---

## 🏗️ Refactoring Architecture

### 1. Enhanced Components (No New Files)

#### A. ServiceManager.install_full_environment() - ENHANCED
**Responsibility**: Main installation coordination with deployment choice
**Location**: `cli/commands/service.py:70-87` - **EXISTING FILE**

```python
def install_full_environment(self, workspace: str = ".") -> bool:
    """Complete environment setup with deployment choice."""
    try:
        print(f"🛠️ Setting up Automagik Hive environment in: {workspace}")
        
        # 1. DEPLOYMENT CHOICE SELECTION
        deployment_mode = self._prompt_deployment_choice()
        
        # 2. USE EXISTING CredentialService.install_all_modes() 
        from lib.auth.credential_service import CredentialService
        credential_service = CredentialService(project_root=Path(workspace))
        
        # Generate workspace credentials using existing comprehensive service
        all_credentials = credential_service.install_all_modes(modes=["workspace"])
        
        # 3. DEPLOYMENT-SPECIFIC SETUP
        if deployment_mode == "local_hybrid":
            return self._setup_local_hybrid_deployment(workspace)
        else:  # full_docker
            return self.main_service.install_main_environment(workspace)
            
    except Exception as e:
        print(f"❌ Failed to install environment: {e}")
        return False

def _prompt_deployment_choice(self) -> str:
    """Interactive deployment choice selection."""
    print("\n🚀 Automagik Hive Installation")
    print("\nChoose your deployment mode:")
    print("\nA) Local Development + PostgreSQL Docker")
    print("   • Main server runs locally (faster development)")
    print("   • PostgreSQL runs in Docker (persistent data)")
    print("   • Recommended for: Development, testing, debugging")
    print("   • Access: http://localhost:8886")
    print("\nB) Full Docker Deployment")
    print("   • Both main server and PostgreSQL in containers")
    print("   • Recommended for: Production-like testing, deployment preparation")
    print("   • Access: http://localhost:8886")
    
    while True:
        try:
            choice = input("\nEnter your choice (A/B) [default: A]: ").strip().upper()
            if choice == "" or choice == "A":
                return "local_hybrid"
            elif choice == "B":
                return "full_docker"
            else:
                print("❌ Please enter A or B")
        except (EOFError, KeyboardInterrupt):
            return "local_hybrid"  # Default for automated scenarios

def _setup_local_hybrid_deployment(self, workspace: str) -> bool:
    """Setup local main + PostgreSQL docker only."""
    try:
        print("🐳 Starting PostgreSQL container only...")
        # Use MainService to start PostgreSQL container only
        return self.main_service.start_postgres_only(workspace)
    except Exception as e:
        print(f"❌ Local hybrid deployment failed: {e}")
        return False
```

#### B. CredentialService.install_all_modes() - REUSE EXISTING
**Responsibility**: All credential generation and .env management
**Location**: `lib/auth/credential_service.py:829-886` - **EXISTING FILE**
**Status**: ✅ **PERFECT REUSE** - Already implements everything needed

**Existing Capabilities:**
- Master credential generation with mode derivation
- Automatic .env file creation from templates
- Placeholder credential detection and replacement
- Force regeneration and validation logic
- Multi-mode support (workspace, agent, genie)

#### C. MainService - MINOR ENHANCEMENT
**Responsibility**: Docker orchestration with deployment mode support
**Location**: `cli/core/main_service.py` - **EXISTING FILE**

```python
def start_postgres_only(self, workspace_path: str) -> bool:
    """Start only PostgreSQL container for local hybrid deployment."""
    try:
        # Use existing Docker compose logic but only start postgres service
        import subprocess
        docker_compose_path = Path(workspace_path) / "docker" / "main"
        
        result = subprocess.run([
            "docker-compose", "-f", str(docker_compose_path / "docker-compose.yml"),
            "up", "-d", "postgres"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ PostgreSQL container started successfully")
            print("💡 Start main server locally with: uv run automagik-hive --dev")
            return True
        else:
            print(f"❌ Failed to start PostgreSQL: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ PostgreSQL startup failed: {e}")
        return False
```

### 2. Dead Code Removal

#### Remove From ServiceManager (cli/commands/service.py)
```python
# LINE 139 - REMOVE THIS CALL
if not self._generate_postgres_credentials():  # ❌ DELETE
    return False

# LINE 150 - REMOVE THIS COMMENT  
# Method implementation moved to _generate_postgres_credentials() below  # ❌ DELETE
```

#### Replace _setup_postgresql_interactive() Logic
```python
def _setup_postgresql_interactive(self, workspace: str) -> bool:
    """Simplified PostgreSQL setup - credential generation handled by CredentialService."""
    # Credential generation now handled by CredentialService.install_all_modes()
    # This method can be simplified or removed entirely
    return True
```
---

## 🔄 Installation Workflow

### Refactored Installation Flow

```
1. User runs: uv run automagik-hive --install
2. ServiceManager.install_full_environment() called
3. Interactive deployment choice prompt displayed
4. CredentialService.install_all_modes(modes=["workspace"]) called
   - Detects .env state automatically
   - Generates credentials if missing/placeholder
   - Creates .env from .env.example if needed
5. Deployment-specific setup:
   - Option A: MainService.start_postgres_only() 
   - Option B: MainService.install_main_environment()
6. Success feedback and next steps displayed
```

### Detailed Phase Breakdown

**Phase 1: User Choice & Prerequisites**
```
1. ServiceManager.install_full_environment() called
2. _prompt_deployment_choice() displays interactive menu
3. User selects Option A (local_hybrid) or B (full_docker)
4. Basic workspace validation performed
```

**Phase 2: Credential Management (Automated)**
```
1. CredentialService.install_all_modes(modes=["workspace"]) called
2. Automatic .env file detection and handling:
   - Missing .env: Create from .env.example with real credentials
   - Existing .env with valid credentials: Use as-is
   - Existing .env with placeholders: Generate and update missing credentials
3. All credential generation handled by existing comprehensive service
```

**Phase 3: Deployment-Specific Setup**
```
Option A - Local Hybrid:
1. _setup_local_hybrid_deployment() called
2. MainService.start_postgres_only() starts PostgreSQL container only
3. Instructions displayed for starting local server: uv run automagik-hive --dev

Option B - Full Docker:
1. MainService.install_main_environment() called (existing behavior)
2. Both PostgreSQL and main app containers started
3. Service endpoints displayed
```

**Phase 4: Success Feedback**
```
1. Installation success confirmation
2. Service status display
3. Next steps guidance based on deployment mode
4. Access URLs and development commands
```

---

## 🔧 Implementation Details

### 1. Credential Generation Strategy

**PostgreSQL Credentials**:
- Username: Keep existing from .env.example (`hive_user`)
- Password: Generate 32-character secure random string
- Database: Keep existing from .env.example (`hive`)

**API Keys**:
- HIVE_API_KEY: Generate UUID4-based secure key
- Third-party keys (Anthropic, OpenAI): Keep as placeholders with clear instructions

**Security Requirements**:
- Use `secrets.SystemRandom()` for password generation
- Include uppercase, lowercase, digits, special characters
- Minimum 32 characters for database passwords
- Cryptographically secure random generation

### 2. Environment File Management Logic

```python
def manage_env_file(workspace_path: Path, deployment_mode: DeploymentMode) -> bool:
    """
    Environment file management with deployment mode consideration.
    
    Logic Flow:
    1. Check if .env exists
    2. If missing: Copy .env.example, generate all credentials
    3. If exists: Validate credentials, generate missing ones
    4. Update deployment-specific configuration
    5. Validate final configuration
    """
```

**Placeholder Detection Patterns**:
- `"your-*-here"` patterns  
- `"CHANGE_ME"` patterns
- `"TODO:"` prefixed values
- Empty string values for required credentials

### 3. Deployment Mode Configuration

**Local Hybrid Mode (Option A)**:
```yaml
# Uses docker/main/docker-compose.yml with postgres service only
services:
  postgres:
    # ... existing postgres configuration
    # Only start postgres container
    
# Main app runs locally via uvicorn:
# uv run uvicorn api.serve:app --host 0.0.0.0 --port 8886
```

**Full Docker Mode (Option B)**:
```yaml
# Uses complete docker/main/docker-compose.yml
services:
  postgres:
    # ... existing postgres configuration
  app:
    # ... existing app configuration
    # Both services run in containers
```

### 4. User Interaction Design

**Deployment Choice Prompt**:
```
🚀 Automagik Hive Installation

Choose your deployment mode:

A) Local Development + PostgreSQL Docker
   • Main server runs locally (faster development)
   • PostgreSQL runs in Docker (persistent data)
   • Recommended for: Development, testing, debugging
   • Access: http://localhost:8886

B) Full Docker Deployment  
   • Both main server and PostgreSQL in containers
   • Recommended for: Production-like testing, deployment preparation
   • Access: http://localhost:8886

Enter your choice (A/B) [default: A]: 
```

**Credential Generation Feedback**:
```
🔐 Environment Configuration
✅ .env file found
⚠️  Placeholder credentials detected: POSTGRES_PASSWORD, HIVE_API_KEY
🎲 Generating secure credentials...
✅ PostgreSQL password generated (32 characters)
✅ Hive API key generated
✅ Environment configuration complete
```

---

## 🧪 Test Strategy Integration

### 1. Test Coverage Requirements

**Unit Tests**:
- EnvironmentManager credential detection logic
- DeploymentManager configuration generation  
- InstallOrchestrator workflow coordination
- Credential generation security and randomness

**Integration Tests**:
- Full installation workflow for both deployment modes
- Environment file creation and modification
- Docker container management
- Service connectivity validation

**Edge Case Tests**:
- Missing Docker installation
- Permission denied scenarios
- Corrupted .env files
- Network connectivity issues
- Container startup failures

### 2. TDD Implementation Strategy

**Red-Green-Refactor Cycles**:

**Cycle 1: Environment Detection**
```python
# RED: Test for .env state detection
def test_detect_env_state_missing():
    assert env_manager.detect_env_state(workspace) == EnvState.MISSING

# GREEN: Implement minimal detection logic
def detect_env_state(self, workspace_path: Path) -> EnvState:
    if not (workspace_path / ".env").exists():
        return EnvState.MISSING

# REFACTOR: Add validation and edge cases
```

**Cycle 2: Credential Generation**
```python
# RED: Test secure credential generation
def test_generate_postgres_password():
    password = env_manager.generate_postgres_password()
    assert len(password) >= 32
    assert has_mixed_case_and_special_chars(password)

# GREEN: Implement basic generation
# REFACTOR: Add security requirements
```

**Cycle 3: Deployment Configuration**
```python
# RED: Test deployment mode configuration
def test_configure_local_hybrid():
    result = deployment_manager.configure_local_hybrid_deployment(".")
    assert result == True
    assert postgres_container_only_running()

# GREEN: Implement basic configuration
# REFACTOR: Add error handling and validation
```

### 3. Test Milestones

- **Milestone 1**: Environment detection and credential validation (75% coverage)
- **Milestone 2**: Deployment mode selection and configuration (85% coverage)  
- **Milestone 3**: Full installation workflow integration (95% coverage)
- **Milestone 4**: Edge cases and error handling (98% coverage)

---

## 🚨 Error Handling & Recovery

### 1. Failure Scenarios & Recovery

**Docker Not Available**:
```python
def _validate_docker_availability(self) -> bool:
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ Docker not found. Please install Docker and try again.")
        print("💡 Visit: https://docs.docker.com/get-docker/")
        return False
```

**Environment File Corruption**:
```python
def _handle_corrupted_env_file(self, workspace_path: Path) -> bool:
    """Handle corrupted .env files by backing up and recreating."""
    env_file = workspace_path / ".env"
    backup_file = workspace_path / f".env.backup.{int(time.time())}"
    
    try:
        shutil.copy2(env_file, backup_file)
        print(f"📋 Corrupted .env backed up to: {backup_file.name}")
        return self._create_env_from_template(workspace_path)
    except Exception as e:
        print(f"❌ Failed to handle corrupted .env: {e}")
        return False
```

**Container Startup Failures**:
```python
def _handle_container_startup_failure(self, service_name: str) -> bool:
    """Handle container startup failures with retry logic."""
    max_retries = 3
    for attempt in range(max_retries):
        print(f"🔄 Retry {attempt + 1}/{max_retries}: Starting {service_name}...")
        if self._start_service_with_logs(service_name):
            return True
        time.sleep(5)
    
    print(f"❌ Failed to start {service_name} after {max_retries} attempts")
    return self._cleanup_partial_installation()
```

### 2. Rollback Strategy

**Partial Installation Cleanup**:
```python
def _cleanup_partial_installation(self) -> bool:
    """Clean up partial installation state."""
    cleanup_tasks = [
        ("Stop containers", self._stop_all_containers),
        ("Remove volumes", self._remove_installation_volumes),
        ("Reset .env file", self._restore_env_backup),
    ]
    
    success_count = 0
    for task_name, task_func in cleanup_tasks:
        try:
            if task_func():
                print(f"✅ {task_name}")
                success_count += 1
            else:
                print(f"⚠️ {task_name} had issues")
        except Exception as e:
            print(f"❌ {task_name} failed: {e}")
    
    return success_count == len(cleanup_tasks)
```

---

## 🔗 Integration Points

### 1. ServiceManager Integration

**Compatibility Requirements**:
- Maintain existing interface for `install_full_environment()`
- Extend functionality without breaking existing callers
- Preserve Docker container naming conventions

**Integration Strategy**:
```python
class ServiceManager:
    def __init__(self, workspace_path: Path | None = None):
        self.workspace_path = workspace_path or Path()
        self.install_orchestrator = InstallOrchestrator(self.workspace_path)
    
    def install_full_environment(self, workspace: str) -> bool:
        """Enhanced installation with deployment choice."""
        # Delegate to new orchestrator while maintaining compatibility
        return self.install_orchestrator.install_with_deployment_choice(workspace)
```

### 2. MainService Integration

**Requirements**:
- Support partial service startup (PostgreSQL only for local hybrid)
- Maintain existing container management logic
- Add local development server integration

**Implementation Approach**:
```python
class MainService:
    def start_postgres_only(self, workspace_path: str) -> bool:
        """Start only PostgreSQL container for local hybrid deployment."""
        return self._setup_postgres_container(workspace_path)
    
    def prepare_local_development(self, workspace_path: str) -> Dict[str, str]:
        """Prepare configuration for local main server."""
        return {
            "database_url": self._get_postgres_connection_string(),
            "api_port": os.getenv("HIVE_API_PORT", "8886"),
            "host": os.getenv("HIVE_API_HOST", "0.0.0.0")
        }
```

---

## 📈 Success Criteria

### 1. Functional Requirements

**Installation Success Metrics**:
- [ ] User can choose between local hybrid and full Docker deployment
- [ ] .env file is created or updated with secure credentials  
- [ ] PostgreSQL container starts and accepts connections
- [ ] Main service (local or Docker) responds to health checks
- [ ] Installation completes within 60 seconds for normal cases

**User Experience Metrics**:
- [ ] Clear deployment mode explanation and selection
- [ ] Progress feedback throughout installation process  
- [ ] Helpful error messages with actionable guidance
- [ ] Successful installations require no manual intervention

### 2. Technical Requirements

**Code Quality Gates**:
- [ ] 95%+ test coverage for new components
- [ ] All tests pass in CI/CD pipeline
- [ ] Static analysis (mypy, ruff) passes without errors
- [ ] Architecture follows existing patterns and constraints

**Performance Requirements**:
- [ ] Installation completes within 60 seconds (normal case)
- [ ] Memory usage stays under 100MB during installation
- [ ] No resource leaks after installation completion
- [ ] Graceful handling of slow Docker operations

### 3. Security Requirements

**Credential Security**:
- [ ] Generated passwords meet security complexity requirements
- [ ] No credentials logged or exposed in plain text
- [ ] .env file has appropriate file permissions (600)
- [ ] Secure random number generation for all credentials

---

## 🎯 Implementation Plan

### Development Phases

**Phase 1: Core Infrastructure (Week 1)**
- Create EnvironmentManager with credential detection
- Implement DeploymentManager with mode configuration
- Set up basic InstallOrchestrator structure
- Write comprehensive unit tests

**Phase 2: Integration & Workflow (Week 2)**  
- Integrate with existing ServiceManager
- Implement complete installation workflow
- Add user interaction and progress feedback
- Integration testing with both deployment modes

**Phase 3: Error Handling & Polish (Week 3)**
- Comprehensive error handling and recovery
- User experience improvements
- Documentation and help text
- Performance optimization and testing

**Phase 4: Validation & Release (Week 4)**
- Full system testing across environments
- Security review and validation
- Final integration with CLI command structure
- Release preparation and deployment

---

## 🔍 Validation Strategy

### 1. Test Environments

**Local Development Testing**:
- macOS with Docker Desktop
- Ubuntu 22.04 with Docker CE
- Windows 11 with WSL2 and Docker Desktop

**CI/CD Pipeline Testing**:
- Automated testing in GitHub Actions
- Container builds and integration tests
- Security scanning and dependency checks

### 2. Acceptance Criteria Validation

**User Acceptance Tests**:
```gherkin
Scenario: First-time installation with deployment choice
  Given user runs `uv run automagik-hive --install`
  And no .env file exists in workspace
  When user selects deployment mode A (local hybrid)
  Then system generates .env file with secure credentials
  And PostgreSQL container starts successfully
  And user receives next steps guidance

Scenario: Installation with existing .env file
  Given user has .env file with placeholder credentials  
  When user runs installation process
  Then system detects placeholder credentials
  And generates secure replacements
  And preserves existing valid credentials
  And installation completes successfully
```

---

## 📚 Documentation Requirements

### 1. User Documentation

**Installation Guide Updates**:
- Clear explanation of deployment mode differences
- Prerequisites and system requirements
- Troubleshooting guide for common issues
- Migration guide from existing installations

### 2. Developer Documentation

**Code Documentation**:
- Comprehensive docstrings for all new classes and methods
- Architecture decision records for major design choices
- Integration guide for extending deployment modes
- Testing guide and coverage requirements

---

## ⚡ Conclusion

This Technical Specification Document provides a comprehensive blueprint for refactoring the `--install` command to meet the user's exact requirements. The solution maintains compatibility with existing architecture while adding the requested deployment choice functionality and intelligent credential management.

**Key Success Factors**:
1. **User-Centric Design**: Interactive deployment mode selection puts control in user hands
2. **Intelligent Automation**: Automatic credential detection and generation reduces manual work
3. **Robust Error Handling**: Comprehensive failure recovery ensures reliable installation experience  
4. **Architectural Compatibility**: Seamless integration with existing ServiceManager and Docker infrastructure
5. **Comprehensive Testing**: TDD approach ensures reliability and maintainability

**Next Steps**:
1. Review and validate this specification with stakeholders
2. Begin implementation starting with EnvironmentManager core functionality
3. Follow TDD approach with incremental feature delivery
4. Maintain focus on user requirements without architectural gold-plating

---

**Implementation Ready**: ✅ This specification provides complete technical guidance for implementing the enhanced `--install` command according to user requirements.