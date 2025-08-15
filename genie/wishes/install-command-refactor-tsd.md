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

### 1. Refactoring Approach Summary

**Key Principle**: Enhance existing components instead of creating new ones
- ✅ **Reuse**: CredentialService.install_all_modes() handles all credential logic
- ✅ **Enhance**: ServiceManager.install_full_environment() adds deployment choice
- ✅ **Extend**: MainService gets start_postgres_only() method
- ❌ **Remove**: Dead code and missing method references

### 2. Credential Management (Existing CredentialService)

**Leveraging Existing Capabilities**:
- ✅ Master credential generation with mode derivation
- ✅ Automatic .env file creation from .env.example templates
- ✅ Placeholder credential detection and replacement
- ✅ Force regeneration and validation logic
- ✅ Secure random generation with proper entropy

**Call Pattern**:
```python
credential_service = CredentialService(project_root=Path(workspace))
all_credentials = credential_service.install_all_modes(modes=["workspace"])
```

### 3. Deployment Mode Implementation

**Local Hybrid Mode (Option A)**:
```bash
# PostgreSQL container only via docker-compose
docker-compose -f docker/main/docker-compose.yml up -d postgres

# Main server runs locally
uv run automagik-hive --dev
```

**Full Docker Mode (Option B)**:
```bash
# Both containers via existing MainService logic
# Uses complete docker/main/docker-compose.yml setup
```

### 4. Dead Code Removal Strategy

**ServiceManager cleanup**:
```python
# REMOVE: Line 139 call to non-existent method
# BEFORE:
if not self._generate_postgres_credentials():
    return False

# AFTER: 
# (Remove entirely - handled by CredentialService)

# REMOVE: Line 150 false comment
# BEFORE:
# Method implementation moved to _generate_postgres_credentials() below

# AFTER:
# (Remove entirely - method doesn't exist)
```

### 5. Integration Points

**ServiceManager → CredentialService**:
```python
from lib.auth.credential_service import CredentialService
credential_service = CredentialService(project_root=Path(workspace))
```

**ServiceManager → MainService**:
```python
# Existing integration enhanced with new method
self.main_service.start_postgres_only(workspace)
```

---

## 🧪 Test Strategy Integration

### 1. Refactoring Test Approach

**Focus**: Test enhanced ServiceManager methods and MainService integration
- ✅ **Reuse**: Existing CredentialService tests already validate credential logic
- ✅ **Enhance**: ServiceManager tests for deployment choice logic
- ✅ **Add**: MainService.start_postgres_only() unit tests
- ✅ **Integration**: Full workflow tests for both deployment modes

### 2. Test Coverage Requirements

**Unit Tests (New)**:
```python
# ServiceManager enhancements
def test_prompt_deployment_choice_default():
    """Test deployment choice prompt with default selection."""
    
def test_prompt_deployment_choice_full_docker():
    """Test deployment choice prompt with full docker selection."""
    
def test_setup_local_hybrid_deployment():
    """Test local hybrid deployment setup."""

# MainService enhancements  
def test_start_postgres_only_success():
    """Test PostgreSQL-only container startup."""
    
def test_start_postgres_only_failure():
    """Test PostgreSQL startup failure handling."""
```

**Integration Tests (Enhanced)**:
```python
def test_install_full_environment_local_hybrid():
    """Test complete installation with local hybrid mode."""
    
def test_install_full_environment_full_docker():
    """Test complete installation with full docker mode."""
    
def test_credential_service_integration():
    """Test CredentialService.install_all_modes() integration."""
```

**Regression Tests**:
```python
def test_no_missing_postgres_credentials_error():
    """Ensure _generate_postgres_credentials() error is fixed."""
    
def test_dead_code_removed():
    """Verify dead code and comments are removed."""
```

### 3. TDD Implementation Strategy

**Red-Green-Refactor for Enhancements Only**:

**Cycle 1: Deployment Choice**
```python
# RED: Test deployment choice prompt
def test_prompt_deployment_choice():
    with patch('builtins.input', return_value='A'):
        result = service_manager._prompt_deployment_choice()
        assert result == "local_hybrid"

# GREEN: Implement basic prompt logic
# REFACTOR: Add error handling and validation
```

**Cycle 2: Local Hybrid Setup**
```python
# RED: Test local hybrid deployment
def test_setup_local_hybrid():
    result = service_manager._setup_local_hybrid_deployment(".")
    assert result == True
    # Verify only PostgreSQL container running

# GREEN: Implement MainService.start_postgres_only()
# REFACTOR: Add error handling and feedback
```

---

## 🚨 Error Handling & Recovery

### 1. Enhanced Error Handling (Refactoring Focus)

**Leverage Existing CredentialService Error Handling**:
- ✅ CredentialService already handles .env corruption, missing files, permission issues
- ✅ Comprehensive error recovery and backup strategies already implemented
- ➕ Add deployment-specific error handling for new functionality

**ServiceManager Enhanced Error Handling**:
```python
def install_full_environment(self, workspace: str = ".") -> bool:
    """Enhanced with deployment choice error handling."""
    try:
        # Deployment choice with error handling
        deployment_mode = self._prompt_deployment_choice()
        
        # Leverage existing CredentialService error handling
        credential_service = CredentialService(project_root=Path(workspace))
        all_credentials = credential_service.install_all_modes(modes=["workspace"])
        
        # Deployment-specific error handling
        if deployment_mode == "local_hybrid":
            return self._setup_local_hybrid_deployment(workspace)
        else:
            return self.main_service.install_main_environment(workspace)
            
    except KeyboardInterrupt:
        print("\n🛑 Installation cancelled by user")
        return False
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False
```

**MainService Error Handling Enhancement**:
```python
def start_postgres_only(self, workspace_path: str) -> bool:
    """PostgreSQL-only startup with error handling."""
    try:
        # Docker availability check
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        
        # Container startup with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            if self._start_postgres_container(workspace_path):
                return True
            if attempt < max_retries - 1:
                print(f"🔄 Retry {attempt + 2}/{max_retries}...")
                time.sleep(5)
        
        return False
    except FileNotFoundError:
        print("❌ Docker not found. Please install Docker and try again.")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL startup failed: {e}")
        return False
```

---

## 🔗 Integration Strategy

### 1. Zero New Dependencies

**Reuse Existing Infrastructure**:
- ✅ ServiceManager existing interface maintained
- ✅ MainService existing container logic leveraged  
- ✅ CredentialService comprehensive functionality reused
- ✅ No new external dependencies required

### 2. Backward Compatibility

**Interface Preservation**:
```python
# Existing callers continue to work unchanged
service_manager.install_full_environment(".")  # ✅ Still works
service_manager.install_full_environment("/path")  # ✅ Still works

# New functionality added transparently
# User gets deployment choice prompt automatically
```

### 3. Configuration Compatibility

**Docker Compose Reuse**:
- ✅ Existing `docker/main/docker-compose.yml` used for both modes
- ✅ PostgreSQL service configuration unchanged
- ✅ App service configuration unchanged
- ➕ Deployment mode determines which services start

---

## 📈 Success Criteria (Refactoring Focus)

### 1. Functional Requirements

**Installation Success Metrics**:
- [ ] User can choose between local hybrid and full Docker deployment via interactive prompt
- [ ] CredentialService.install_all_modes() handles all .env file creation/updates
- [ ] Missing `_generate_postgres_credentials()` method error is resolved
- [ ] PostgreSQL container starts correctly for both deployment modes
- [ ] Main service (local or Docker) responds appropriately based on mode
- [ ] Installation completes within 60 seconds for normal cases
- [ ] No new files created - pure refactoring approach

**User Experience Metrics**:
- [ ] Clear deployment mode explanation and selection (interactive prompt)
- [ ] Seamless integration with existing installation flow
- [ ] Helpful error messages with actionable guidance
- [ ] Successful installations require no manual intervention
- [ ] Agent and genie installations remain unaffected

### 2. Technical Requirements (Refactoring)

**Code Quality Gates**:
- [ ] Enhanced ServiceManager methods tested (95%+ coverage for new code)
- [ ] All existing tests continue to pass (backward compatibility)
- [ ] Dead code removed (lines 139, 150 in ServiceManager)
- [ ] Static analysis (mypy, ruff) passes without errors
- [ ] Zero new file creation - enhancement-only approach

**Performance Requirements**:
- [ ] Installation performance unchanged or improved
- [ ] Memory usage unchanged - no new object creation overhead
- [ ] Leverage existing CredentialService performance optimizations
- [ ] Docker startup times unchanged

### 3. Integration Requirements

**Reuse Validation**:
- [ ] CredentialService.install_all_modes() correctly integrated
- [ ] ServiceManager interface backward compatibility maintained
- [ ] MainService.start_postgres_only() properly implemented
- [ ] All existing credential security features preserved

---

## 🎯 Implementation Plan (Refactoring)

### Development Phases

**Phase 1: ServiceManager Enhancement **
- Remove dead code (lines 139, 150) causing the installation error
- Add `_prompt_deployment_choice()` method to ServiceManager
- Integrate `CredentialService.install_all_modes(modes=["workspace"])`
- Add `_setup_local_hybrid_deployment()` method
- Write unit tests for new ServiceManager methods

**Phase 2: MainService Enhancement **  
- Implement `MainService.start_postgres_only()` method
- Add error handling and retry logic for PostgreSQL-only startup
- Integration testing with ServiceManager deployment choice
- Test both deployment modes end-to-end

**Phase 3: Polish & Validation **
- Comprehensive error handling and user feedback
- Performance validation (ensure no regression)
- Backward compatibility testing
- Documentation updates for deployment modes

**Phase 4: Final Integration **
- Full system testing across environments  
- Regression testing to ensure agent/genie installs unaffected
- User acceptance testing with deployment choice
- Release preparation

---

## 🔍 Validation Strategy (Refactoring)

### 1. Regression Testing Focus

**Backward Compatibility Validation**:
- Existing `install_full_environment()` callers continue to work
- Agent and genie installation commands remain functional
- Docker container configurations unchanged
- Credential generation maintains security standards

### 2. Enhancement Testing

**New Functionality Validation**:
```gherkin
Scenario: Enhanced installation with deployment choice
  Given user runs `uv run automagik-hive --install`
  When deployment choice prompt appears
  And user selects local hybrid mode
  Then CredentialService handles .env file automatically
  And only PostgreSQL container starts
  And user receives local development instructions

Scenario: Dead code bug fix validation
  Given the missing _generate_postgres_credentials() method
  When installation process runs
  Then no AttributeError occurs
  And credential generation works via CredentialService
```

---

## ⚡ Conclusion (Refactoring Approach)

This Technical Specification Document provides a comprehensive blueprint for refactoring the `--install` command through pure enhancement of existing components. The solution leverages extensive existing infrastructure while adding the requested deployment choice functionality.

**Key Success Factors**:
1. **Zero New Files**: Pure refactoring approach leverages existing comprehensive CredentialService
2. **Reuse Over Recreation**: CredentialService.install_all_modes() eliminates need for new credential logic
3. **Surgical Enhancement**: Targeted improvements to ServiceManager and MainService only
4. **Dead Code Elimination**: Fixes the missing method error while removing redundant patterns
5. **Backward Compatibility**: Existing interfaces preserved, new functionality added transparently

**Architecture Wins**:
- ✅ **1068-line CredentialService reused** instead of creating new EnvironmentManager
- ✅ **ServiceManager enhanced** instead of creating new InstallOrchestrator  
- ✅ **MainService extended** instead of creating new DeploymentManager
- ✅ **Zero new dependencies** - pure enhancement approach
- ✅ **Agent/genie separation respected** - no unwanted unification

**Next Steps**:
1. Begin implementation with ServiceManager dead code removal
2. Add deployment choice prompt and CredentialService integration
3. Implement MainService.start_postgres_only() method
4. Focus on user requirements without architectural over-engineering

---

**Implementation Ready**: ✅ This specification provides complete technical guidance for implementing the enhanced `--install` command through surgical refactoring of existing components.