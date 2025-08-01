# Technical Specification Document: Phase 1 Core Infrastructure

## 1. OVERVIEW

**Objective**: Implement unified deployment architecture with profile-based service management, automated workflows, and component-specific control for Automagik Hive platform.

**Success Metrics**: 
- Single command deployment (`--install`) with 100% automation
- Profile-based Docker service isolation (agent, genie, workspace, all)
- Sub-5-second service startup with health validation
- Zero-prompt automation for agent/genie installs
- 8-command CLI interface with consistent UX patterns

## 2. FUNCTIONAL REQUIREMENTS

### Core Features

#### FR-1: Unified Installation Workflow
- **Description**: Execute install → start → health → workspace workflow in single command
- **Acceptance Criteria**:
  - `uvx automagik-hive --install` completes full setup in under 60 seconds
  - All Docker services start with proper dependency ordering
  - Health checks validate all endpoints before workspace prompt
  - Agent/genie installs skip interactive prompts for automation compatibility

#### FR-2: Profile-Based Service Management
- **Description**: Docker Compose profiles enable selective service deployment
- **Acceptance Criteria**:
  - `agent` profile starts only agent-related services (ports 38886, 35532)
  - `genie` profile starts only genie-related services (ports 48886, 48532)
  - `workspace` profile starts local UVX development server
  - `all` profile combines agent + genie + workspace with proper orchestration

#### FR-3: Component-Specific Operations
- **Description**: All CLI commands accept component parameters for targeted control
- **Acceptance Criteria**:
  - Every command supports [all|workspace|agent|genie] parameter
  - Default behavior targets 'all' components when parameter omitted
  - Service isolation maintained - agent operations don't affect genie services
  - Status reporting provides per-component health information

#### FR-4: Health Check Integration
- **Description**: Comprehensive service health validation with dependency tracking
- **Acceptance Criteria**:
  - Database connectivity validation (PostgreSQL on designated ports)
  - API endpoint response validation with timeout handling
  - Service interdependency verification before declaring healthy
  - Resource usage validation with configurable thresholds

### User Stories

- As a **developer**, I want to start only agent services so that I can focus on agent development without genie overhead
- As a **system administrator**, I want health checks to validate all dependencies so that I can trust service status reports
- As a **CI/CD pipeline**, I want automation-friendly installs so that I can deploy without interactive prompts
- As a **workspace user**, I want auto-detection of missing dependencies so that workspace startup guides me through setup

## 3. NON-FUNCTIONAL REQUIREMENTS

### Performance
- **Service Startup Time**: Docker services must be healthy within 30 seconds
- **CLI Response Time**: All status/health commands respond within 2 seconds
- **Resource Efficiency**: Unused profiles consume zero system resources
- **Concurrent Operations**: Multiple component operations execute in parallel

### Security
- **Port Isolation**: Service profiles use dedicated port ranges without conflicts
- **Environment Separation**: Agent and genie environments isolated with separate .env files
- **Authentication**: API keys generated per component with component-specific scope
- **Resource Limits**: Docker containers have memory/CPU limits to prevent resource exhaustion

### Reliability
- **Graceful Degradation**: Partial component failures don't prevent other components from functioning
- **Automatic Recovery**: Health checks trigger service restart on failure detection
- **State Persistence**: Service state maintained across restart operations
- **Error Handling**: All failure modes provide actionable error messages with resolution guidance

### Scalability
- **Profile Extensibility**: New service profiles can be added without modifying core CLI logic
- **Command Extensibility**: New commands follow consistent parameter patterns
- **Configuration Flexibility**: Component-specific configuration without cross-contamination

## 4. TECHNICAL ARCHITECTURE

### System Components

#### A. UnifiedInstaller Class
**Responsibilities**: Orchestrate complete installation workflow with health validation
**Interfaces**: ServiceManager, HealthChecker, WorkspaceManager, DockerComposeManager

```python
class UnifiedInstaller:
    def __init__(self):
        self.service_manager = ServiceManager()
        self.health_checker = HealthChecker()
        self.workspace_manager = WorkspaceManager()
        self.docker_manager = DockerComposeManager()
    
    def install_with_workflow(self, component: str = "all") -> InstallResult:
        """Execute install → start → health → workspace workflow."""
        
    def setup_docker_infrastructure(self, component: str) -> bool:
        """Pull images, create networks, generate configs."""
        
    def execute_health_validation(self, component: str) -> dict[str, HealthStatus]:
        """Comprehensive health check with dependency validation."""
        
    def handle_interactive_workspace_setup(self, component: str) -> WorkspaceResult:
        """Interactive workspace setup with automation skip for agent/genie."""
```

#### B. ServiceManager Class  
**Responsibilities**: Component-based service lifecycle management
**Interfaces**: DockerComposeManager, ProcessManager, StatusReporter

```python
class ServiceManager:
    def __init__(self):
        self.docker_manager = DockerComposeManager()
        self.process_manager = ProcessManager()
        self.status_reporter = StatusReporter()
    
    def start_services(self, component: str = "all") -> OperationResult:
        """Start services using profile-based Docker Compose activation."""
        
    def stop_services(self, component: str = "all") -> OperationResult:
        """Stop services with graceful shutdown handling."""
        
    def restart_services(self, component: str = "all") -> OperationResult:
        """Stop and start services with health validation."""
        
    def get_status(self, component: str = "all") -> dict[str, ServiceStatus]:
        """Real-time service status with dependency information."""
        
    def show_logs(self, component: str = "all", lines: int = 50) -> bool:
        """Stream logs with component filtering and line limits."""
        
    def uninstall(self, component: str = "all") -> OperationResult:
        """Remove components with data preservation options."""
```

#### C. DockerComposeManager Class
**Responsibilities**: Docker Compose profile management and service orchestration
**Interfaces**: Docker daemon, configuration files

```python
class DockerComposeManager:
    def __init__(self, compose_file: str = "docker-compose.unified.yml"):
        self.compose_file = compose_file
        self.profile_mapping = {
            "agent": ["agent"],
            "genie": ["genie"], 
            "workspace": ["workspace"],
            "all": ["agent", "genie", "workspace"]
        }
    
    def activate_profiles(self, component: str) -> list[str]:
        """Return Docker Compose profile list for component."""
        
    def execute_compose_command(self, command: str, profiles: list[str]) -> ComposeResult:
        """Execute docker-compose with profile activation."""
        
    def validate_service_dependencies(self, profiles: list[str]) -> bool:
        """Verify service dependency chains are satisfied."""
```

#### D. WorkspaceManager Class
**Responsibilities**: Interactive workspace initialization and management
**Interfaces**: File system, UVX process manager, user input

```python
class WorkspaceManager:
    def prompt_workspace_choice(self) -> tuple[WorkspaceAction, str]:
        """Interactive workspace selection with validation."""
        
    def initialize_workspace(self, name: str | None = None) -> WorkspaceResult:
        """Create new workspace with MCP integration."""
        
    def start_workspace_server(self, workspace_path: str) -> bool:
        """Start UVX server with dependency detection."""
        
    def validate_existing_workspace(self, path: str) -> ValidationResult:
        """Validate workspace structure and configuration."""
        
    def initialize_existing_folder(self, path: str) -> bool:
        """Convert existing folder to valid workspace."""
```

### Data Models

#### Configuration Models
```python
class ServiceConfig:
    name: str
    profiles: list[str]
    ports: list[int]
    environment_file: str
    depends_on: list[str]
    health_check: HealthCheckConfig

class HealthCheckConfig:
    endpoint: str
    timeout_seconds: int
    retry_count: int
    expected_status: int

class InstallResult:
    success: bool
    components_installed: list[str]
    services_started: list[str]
    health_status: dict[str, bool]
    workspace_result: WorkspaceResult | None
    errors: list[str]

class WorkspaceResult:
    action: str  # "new", "existing", "skip"
    path: str
    success: bool
    initialized: bool
```

### API Contracts

#### CLI Command Interface
```python
# Command execution pattern
def execute_command(command: str, component: str = "all", **kwargs) -> CommandResult:
    """
    Execute CLI command with component parameter.
    
    Args:
        command: install|start|stop|restart|status|health|logs|uninstall
        component: all|workspace|agent|genie
        **kwargs: Command-specific parameters
        
    Returns:
        CommandResult with success status and details
    """

# Health check interface  
def health_check(component: str = "all") -> dict[str, HealthStatus]:
    """
    Return comprehensive health status for component.
    
    Returns:
        {
            "database": HealthStatus(healthy=True, response_time=120ms),
            "api": HealthStatus(healthy=True, response_time=45ms),
            "dependencies": HealthStatus(healthy=True, details="all services reachable")
        }
    """
```

#### Docker Compose Profile Structure
```yaml
# docker-compose.unified.yml
services:
  # Agent Stack
  hive-agent-postgres:
    image: postgres:15
    profiles: ["agent", "all"]
    ports: ["35532:5432"]
    environment:
      - POSTGRES_DB=hive_agent
    volumes:
      - agent_db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  hive-agent-api:
    build: .
    profiles: ["agent", "all"]
    ports: ["38886:8000"]
    environment:
      - DATABASE_URL=postgresql://postgres:password@hive-agent-postgres:5432/hive_agent
    depends_on:
      hive-agent-postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 15s
      timeout: 10s
      retries: 3

  # Genie Stack  
  hive-genie-postgres:
    image: postgres:15
    profiles: ["genie", "all"]
    ports: ["48532:5432"]
    environment:
      - POSTGRES_DB=hive_genie
    volumes:
      - genie_db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  hive-genie-api:
    build: .
    profiles: ["genie", "all"]
    ports: ["48886:8000"]
    environment:
      - DATABASE_URL=postgresql://postgres:password@hive-genie-postgres:5432/hive_genie
    depends_on:
      hive-genie-postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 15s
      timeout: 10s
      retries: 3

volumes:
  agent_db_data:
  genie_db_data:

networks:
  default:
    name: automagik-hive-network
```

## 5. TEST-DRIVEN DEVELOPMENT STRATEGY

### Red-Green-Refactor Integration

#### Red Phase: Write Failing Tests First
**Component Testing Strategy**:
```python
# tests/test_unified_installer.py
def test_install_workflow_with_all_components():
    """Test complete install workflow for 'all' component."""
    installer = UnifiedInstaller()
    
    # Should fail - no Docker services running
    result = installer.install_with_workflow("all")
    assert not result.success
    assert "docker not available" in result.errors

def test_component_isolation():
    """Test that agent installation doesn't affect genie services."""
    installer = UnifiedInstaller()
    
    # Install agent only
    result = installer.install_with_workflow("agent")
    
    # Genie ports should be unused
    assert not port_is_open(48886)  # genie API
    assert not port_is_open(48532)  # genie DB
    
    # Agent ports should be active
    assert port_is_open(38886)  # agent API
    assert port_is_open(35532)  # agent DB

def test_health_check_validation():
    """Test comprehensive health checking with service dependencies."""
    health_checker = HealthChecker()
    
    # Should fail - services not started
    status = health_checker.check_component_health("agent")
    assert not status["database"].healthy
    assert not status["api"].healthy
```

#### Green Phase: Minimal Implementation
**Implementation Order**:
1. **DockerComposeManager**: Basic profile activation
2. **ServiceManager**: Start/stop with profiles
3. **HealthChecker**: Service endpoint validation
4. **UnifiedInstaller**: Workflow orchestration
5. **CLI Integration**: Command parsing and execution

#### Refactor Phase: Quality Improvements
**Refactoring Targets**:
- **Error Handling**: Comprehensive error types with recovery guidance
- **Performance**: Parallel service operations where possible
- **Logging**: Structured logging with component correlation
- **Configuration**: Environment-specific defaults with validation

### Test Categories

#### Unit Tests
**Scope**: Individual class methods with mocked dependencies
```python
# Test ServiceManager.start_services() with mocked DockerComposeManager
# Test HealthChecker.validate_endpoint() with mocked HTTP client
# Test WorkspaceManager.initialize_workspace() with mocked file system
```

#### Integration Tests  
**Scope**: Component interaction with real Docker services
```python
# Test complete install workflow with actual Docker Compose
# Test service health checks with running containers
# Test workspace initialization with real file system operations
```

#### End-to-End Tests
**Scope**: Full CLI command execution from user perspective
```python
# Test: uvx automagik-hive --install agent
# Test: uvx automagik-hive --health all
# Test: uvx automagik-hive --logs genie 100
```

## 6. IMPLEMENTATION PHASES

### Phase 1: Docker Infrastructure (Week 1)
#### Deliverables:
- **Docker Compose Configuration**: Unified compose file with profiles
  - Timeline: 2 days
  - Acceptance: All 4 profiles (agent, genie, workspace, all) start correctly
- **DockerComposeManager Class**: Profile management and service orchestration
  - Timeline: 2 days  
  - Acceptance: Profile activation and command execution with error handling
- **Health Check System**: Service validation with dependency checking
  - Timeline: 1 day
  - Acceptance: Database and API health validation with timeout handling

### Phase 2: Service Management (Week 2)
#### Deliverables:
- **ServiceManager Class**: Complete service lifecycle management
  - Timeline: 3 days
  - Acceptance: Start, stop, restart, status, logs operations for all components
- **CLI Argument Parser**: 8-command interface with component parameters
  - Timeline: 2 days
  - Acceptance: All commands accept component parameters with validation

### Phase 3: Workflow Integration (Week 3)
#### Deliverables:
- **UnifiedInstaller Class**: Complete install workflow orchestration
  - Timeline: 3 days
  - Acceptance: Single-command installation with health validation and workspace setup
- **WorkspaceManager Class**: Interactive workspace management
  - Timeline: 2 days
  - Acceptance: New/existing workspace handling with dependency detection

### Phase 4: Polish & Validation (Week 4)  
#### Deliverables:
- **End-to-End Testing**: Complete CLI command validation
  - Timeline: 2 days
  - Acceptance: All 8 commands work correctly with all 4 component options
- **Performance Optimization**: Service startup time optimization
  - Timeline: 1 day
  - Acceptance: <30 second startup time for all components
- **Documentation & Examples**: Usage documentation with common scenarios
  - Timeline: 2 days
  - Acceptance: Complete usage examples for all deployment scenarios

## 7. EDGE CASES & ERROR HANDLING

### Boundary Conditions

#### EC-1: Docker Service Port Conflicts
- **Scenario**: User has existing services on required ports (35532, 38886, 48532, 48886)
- **Handling Strategy**: 
  - Port availability check before service startup
  - Configurable port ranges via environment variables
  - Clear error messages with resolution steps

#### EC-2: Partial Service Failures
- **Scenario**: Database starts successfully but API container fails
- **Handling Strategy**:
  - Health check dependency validation
  - Automatic retry with exponential backoff
  - Rollback to previous state on failure

#### EC-3: Workspace Path Conflicts
- **Scenario**: Target workspace path exists but contains conflicting files
- **Handling Strategy**:
  - Workspace structure validation before initialization
  - Backup existing files before modification
  - Prompt for conflict resolution strategy

### Error Scenarios

#### ES-1: Docker Daemon Unavailable  
- **Recovery Strategy**: 
  - Check Docker installation status
  - Provide Docker installation instructions
  - Fallback to local-only development mode

#### ES-2: Network Connectivity Issues
- **Recovery Strategy**:
  - Image pull retry with timeout handling
  - Local image build fallback
  - Offline mode with pre-cached images

#### ES-3: Insufficient System Resources
- **Recovery Strategy**:
  - Resource requirement validation before startup
  - Graceful degradation with reduced service count
  - Memory/CPU limit configuration recommendations

## 8. ACCEPTANCE CRITERIA

### Definition of Done

#### Primary Success Criteria
- [ ] **Single Command Deployment**: `uvx automagik-hive --install` completes full setup successfully
- [ ] **Component Isolation**: Agent and genie installations operate independently without interference  
- [ ] **Profile-Based Management**: All 4 profiles (agent, genie, workspace, all) function correctly
- [ ] **Health Validation**: Health checks validate all services before declaring success
- [ ] **CLI Consistency**: All 8 commands follow consistent parameter patterns and error handling
- [ ] **Automation Compatibility**: Agent/genie installs complete without interactive prompts
- [ ] **Performance Target**: Service startup completes within 30 seconds for all components
- [ ] **Error Resilience**: All error scenarios provide actionable recovery guidance

#### Quality Gates
- [ ] **Test Coverage**: >90% test coverage for all core classes and CLI commands
- [ ] **Integration Validation**: End-to-end tests pass for all component combinations
- [ ] **Performance Benchmarks**: Service startup time <30s, CLI response time <2s
- [ ] **Documentation Completeness**: All commands documented with examples and troubleshooting
- [ ] **Security Validation**: Component isolation verified, no credential leakage between environments

### Validation Steps

#### Installation Validation
1. **Clean Environment Test**: Install on system with no existing Docker containers
2. **Port Conflict Test**: Install with conflicting services on required ports
3. **Component Isolation Test**: Install agent only, verify genie services remain unused
4. **Full Stack Test**: Install all components, verify complete service mesh functionality

#### Service Management Validation  
1. **Lifecycle Testing**: Start, stop, restart all component combinations
2. **Status Accuracy**: Verify status reporting matches actual service states
3. **Log Aggregation**: Validate log streaming with component filtering and line limits
4. **Health Monitoring**: Confirm health checks detect service failures and recovery

#### Workspace Integration Validation
1. **New Workspace Creation**: Test interactive and direct workspace initialization
2. **Existing Workspace Detection**: Validate existing workspace structure recognition
3. **Dependency Auto-Detection**: Verify workspace startup detects missing services and prompts installation
4. **Workspace Server Startup**: Confirm UVX server starts correctly with all dependencies

This Technical Specification Document provides a comprehensive blueprint for implementing Phase 1 Core Infrastructure with profile-based architecture, unified workflow management, and comprehensive testing strategy. The embedded context integration ensures all specifications align with project requirements and forge task completion criteria.