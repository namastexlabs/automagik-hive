# Agent CLI Commands Architecture - Detailed Design Document

## 🏛️ System Architecture Overview

### Document Metadata
- **TSD Reference**: uvx-agent-management-complete.md
- **Created By**: genie-dev-designer
- **Version**: 1.0
- **Architecture Pattern**: Clean Architecture with Service Layer Pattern
- **Framework Integration**: Automagik Hive CLI Foundation

### Strategic Context
This DDD provides the comprehensive architectural design for implementing complete `--agent-*` CLI commands that fully replace the existing `make agent` functionality through Docker container orchestration and isolated environment management.

## 🏗️ Clean Architecture Design

### Layer Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│  cli/main.py: ArgumentParser Integration                    │
│  cli/commands/agent.py: AgentCommands Class                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ 
┌─────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                         │
│  cli/core/agent_service.py: AgentService                    │
│  cli/core/agent_environment.py: AgentEnvironment            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     DOMAIN LAYER                            │
│  Agent Lifecycle States: STOPPED, STARTING, RUNNING,       │
│  Agent Container Configuration, Port Management             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                       │
│  docker.lib.compose_manager: DockerComposeManager           │
│  lib.auth.credential_service: CredentialService             │
└─────────────────────────────────────────────────────────────┘
```

### Dependency Rules
- **Presentation Layer** → Application Layer only
- **Application Layer** → Domain Layer only  
- **Domain Layer** → No dependencies on outer layers
- **Infrastructure Layer** → Implements Domain interfaces

## 🧩 Component Design

### Core Components Structure

#### 1. AgentCommands (Presentation Layer)
```python
# cli/commands/agent.py
class AgentCommands:
    """Agent CLI command implementations.
    
    Provides complete agent container lifecycle management
    commands matching make agent functionality.
    """
    
    def __init__(self):
        self.agent_service = AgentService()
    
    # Command Interface Methods
    def agent_install(self, interactive: bool = True) -> bool
    def agent_serve(self, host: str = "0.0.0.0", port: int = 38886) -> bool
    def agent_logs(self, tail: int = 50, follow: bool = False) -> bool
    def agent_status(self, verbose: bool = False) -> bool
    def agent_stop(self, graceful: bool = True) -> bool
    def agent_restart(self, graceful: bool = True) -> bool
    def agent_reset(self, confirm: bool = False) -> bool
```

#### 2. AgentService (Application Layer)
```python
# cli/core/agent_service.py
class AgentService:
    """High-level agent service operations for CLI.
    
    Orchestrates agent container lifecycle management
    with integrated environment handling and validation.
    """
    
    def __init__(self):
        self.agent_environment = AgentEnvironment()
        self.docker_service = DockerService()
        self.credential_service = CredentialService()
        
    # Service Operation Methods
    def setup_agent_environment(self, interactive: bool) -> bool
    def start_agent_container(self, host: str, port: int) -> bool
    def stop_agent_container(self, graceful: bool) -> bool
    def restart_agent_container(self, graceful: bool) -> bool
    def get_agent_status(self) -> AgentStatus
    def show_agent_logs(self, tail: int, follow: bool) -> bool
    def reset_agent_environment(self, confirm: bool) -> bool
    def validate_agent_health(self) -> bool
```

#### 3. AgentEnvironment (Application Layer)
```python
# cli/core/agent_environment.py
class AgentEnvironment:
    """Agent environment configuration management.
    
    Handles .env.agent generation, port management,
    and data directory setup for agent containers.
    """
    
    def __init__(self):
        self.base_dir = Path.cwd()
        self.agent_env_file = self.base_dir / ".env.agent"
        self.agent_data_dir = self.base_dir / "data" / "postgres-agent"
        
    # Environment Management Methods
    def generate_agent_env_file(self) -> bool
    def ensure_agent_data_directory(self) -> bool
    def get_agent_ports(self) -> AgentPortConfig
    def validate_port_availability(self, ports: list[int]) -> bool
    def backup_existing_environment(self) -> Path | None
    def restore_environment_backup(self, backup_path: Path) -> bool
    def cleanup_agent_environment(self) -> bool
```

### Domain Entities

#### 4. Agent Domain Objects
```python
# Domain Value Objects and Entities
@dataclass
class AgentPortConfig:
    """Agent port configuration."""
    api_port: int = 38886
    postgres_port: int = 35532
    
    def validate_ports(self) -> bool:
        """Validate port numbers are in valid range."""
        return all(1024 <= port <= 65535 for port in [self.api_port, self.postgres_port])

@dataclass 
class AgentStatus:
    """Agent container status information."""
    container_running: bool
    postgres_healthy: bool
    api_accessible: bool
    uptime: str | None
    ports: AgentPortConfig
    data_directory_exists: bool
    env_file_exists: bool

class AgentLifecycleState(Enum):
    """Agent container lifecycle states."""
    STOPPED = "stopped"
    STARTING = "starting" 
    RUNNING = "running"
    RESTARTING = "restarting"
    UNHEALTHY = "unhealthy"
    ERROR = "error"
```

## 🔄 Data Architecture

### Environment Configuration Flow
```yaml
Main .env → Agent Environment Generator → .env.agent
├── POSTGRES_USER          → POSTGRES_USER (same)
├── POSTGRES_PASSWORD      → POSTGRES_PASSWORD (same)  
├── POSTGRES_DB=hive       → POSTGRES_DB=hive_agent
├── POSTGRES_PORT=5532     → POSTGRES_PORT=35532
├── HIVE_API_KEY          → HIVE_API_KEY (same)
├── API_PORT=8886         → API_PORT=38886
└── Additional agent-specific variables
```

### File System Structure
```
project-root/
├── .env                          # Main environment file
├── .env.agent                    # Generated agent environment
├── data/
│   ├── postgres/                 # Main PostgreSQL data
│   └── postgres-agent/           # Agent PostgreSQL data
├── docker-compose.yml            # Main compose file
├── docker-compose-agent.yml      # Agent compose file (generated)
├── logs/
│   ├── agent-server.log         # Agent server logs
│   └── agent-server.pid         # Agent server PID
└── cli/
    ├── commands/
    │   └── agent.py             # Agent CLI commands
    └── core/
        ├── agent_service.py     # Agent service layer
        └── agent_environment.py # Agent environment management
```

### Database Schema Design
```sql
-- Agent database isolation
-- Main database: postgresql://localhost:5532/hive
-- Agent database: postgresql://localhost:35532/hive_agent

-- Agent-specific schemas
CREATE SCHEMA IF NOT EXISTS agent_dev;
CREATE SCHEMA IF NOT EXISTS agent_testing;

-- Component versions tracking for agent environment
CREATE TABLE agent_dev.component_versions (
    id SERIAL PRIMARY KEY,
    component_type VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent_instance VARCHAR(50) DEFAULT 'default'
);
```

## 🔧 Implementation Blueprint

### File Structure Implementation
```
cli/
├── commands/
│   ├── __init__.py
│   ├── agent.py                    # NEW: Complete agent command implementation
│   ├── postgres.py                 # EXISTING: Pattern reference
│   ├── init.py                     # EXISTING: Integration point
│   └── workspace.py                # EXISTING: Integration point
│
├── core/
│   ├── __init__.py
│   ├── agent_service.py            # NEW: Agent service layer
│   ├── agent_environment.py        # NEW: Agent environment management
│   ├── postgres_service.py         # EXISTING: Pattern reference
│   ├── docker_service.py           # EXISTING: Used by agent service
│   ├── container_strategy.py       # EXISTING: Integration pattern
│   └── templates.py                # EXISTING: Template generation
│
└── main.py                         # MODIFIED: Add agent command parsing
```

### Interface Definitions

#### 1. AgentCommands Interface
```python
# cli/commands/agent.py interface signatures
class AgentCommands:
    """Complete agent management command interface."""
    
    def agent_install(self, interactive: bool = True) -> bool:
        """Install agent development environment from scratch.
        
        Equivalent to: make install-agent
        
        Creates:
        - .env.agent file with proper port configuration
        - data/postgres-agent/ directory with permissions
        - docker-compose-agent.yml for isolated container
        
        Args:
            interactive: Whether to prompt for user confirmation
            
        Returns:
            True if installation successful, False otherwise
        """
        
    def agent_serve(self, host: str = "0.0.0.0", port: int = 38886) -> bool:
        """Start agent development server in background.
        
        Equivalent to: make agent
        
        Starts:
        - Agent API server on port 38886
        - Agent PostgreSQL on port 35532
        - Background process with PID tracking
        
        Args:
            host: Host to bind server to
            port: Port to bind API server to
            
        Returns:
            True if server started successfully, False otherwise
        """
        
    def agent_logs(self, tail: int = 50, follow: bool = False) -> bool:
        """Show or stream agent container logs.
        
        Equivalent to: make agent-logs
        
        Args:
            tail: Number of recent log lines to show
            follow: Whether to stream logs continuously
            
        Returns:
            True if logs displayed, False if error
        """
        
    def agent_status(self, verbose: bool = False) -> bool:
        """Check agent container and service health.
        
        Equivalent to: make agent-status
        
        Checks:
        - Container running status
        - PostgreSQL connectivity on port 35532
        - API accessibility on port 38886
        - Data directory integrity
        
        Args:
            verbose: Whether to show detailed status information
            
        Returns:
            True if agent is healthy, False otherwise
        """
        
    def agent_stop(self, graceful: bool = True) -> bool:
        """Stop agent development server and containers.
        
        Equivalent to: make agent-stop
        
        Args:
            graceful: Whether to allow graceful shutdown (30s timeout)
            
        Returns:
            True if stopped successfully, False otherwise
        """
        
    def agent_restart(self, graceful: bool = True) -> bool:
        """Restart agent development server and containers.
        
        Equivalent to: make agent-restart
        
        Args:
            graceful: Whether to use graceful restart
            
        Returns:
            True if restarted successfully, False otherwise
        """
        
    def agent_reset(self, confirm: bool = False) -> bool:
        """Destroy and recreate agent environment completely.
        
        NEW FUNCTIONALITY: Complete environment reset
        
        Destroys:
        - Agent containers and volumes
        - Agent database data
        - .env.agent file
        
        Recreates:
        - Fresh agent environment
        - Clean database state
        - New credentials if needed
        
        Args:
            confirm: Whether user has confirmed destructive action
            
        Returns:
            True if reset successful, False otherwise
        """
```

#### 2. AgentService Interface  
```python
# cli/core/agent_service.py interface signatures
class AgentService:
    """Agent service layer interface."""
    
    def setup_agent_environment(self, interactive: bool = True) -> bool:
        """Setup complete agent development environment."""
        
    def start_agent_container(self, host: str = "0.0.0.0", port: int = 38886) -> bool:
        """Start agent container with API and PostgreSQL services."""
        
    def stop_agent_container(self, graceful: bool = True) -> bool:
        """Stop agent container gracefully or forcefully."""
        
    def restart_agent_container(self, graceful: bool = True) -> bool:
        """Restart agent container with optional graceful shutdown."""
        
    def get_agent_status(self) -> AgentStatus:
        """Get comprehensive agent status information."""
        
    def show_agent_logs(self, tail: int = 50, follow: bool = False) -> bool:
        """Display agent container logs with optional streaming."""
        
    def reset_agent_environment(self, confirm: bool = False) -> bool:
        """Reset agent environment completely (destructive operation)."""
        
    def validate_agent_health(self) -> bool:
        """Validate agent health including API and database connectivity."""
```

#### 3. AgentEnvironment Interface
```python
# cli/core/agent_environment.py interface signatures  
class AgentEnvironment:
    """Agent environment management interface."""
    
    def generate_agent_env_file(self) -> bool:
        """Generate .env.agent from main .env with port adjustments."""
        
    def ensure_agent_data_directory(self) -> bool:
        """Create and set permissions for agent data directory."""
        
    def get_agent_ports(self) -> AgentPortConfig:
        """Get agent port configuration from environment."""
        
    def validate_port_availability(self, ports: list[int]) -> bool:
        """Check if required ports are available for agent use."""
        
    def backup_existing_environment(self) -> Path | None:
        """Create backup of existing agent environment files."""
        
    def restore_environment_backup(self, backup_path: Path) -> bool:
        """Restore agent environment from backup."""
        
    def cleanup_agent_environment(self) -> bool:
        """Clean up agent environment files and directories."""
```

## 🔗 Integration Architecture

### CLI Main Integration
```python
# cli/main.py integration points
def create_parser() -> argparse.ArgumentParser:
    """Add agent commands to main CLI parser."""
    
    # Agent container management commands
    agent_group = parser.add_argument_group("Agent Development Environment")
    agent_group.add_argument("--agent-install", help="Install agent dev environment")
    agent_group.add_argument("--agent-serve", help="Start agent dev server")
    agent_group.add_argument("--agent-logs", help="Show agent container logs")  
    agent_group.add_argument("--agent-status", help="Check agent health")
    agent_group.add_argument("--agent-stop", help="Stop agent container")
    agent_group.add_argument("--agent-restart", help="Restart agent container")
    agent_group.add_argument("--agent-reset", help="Reset agent environment")

def main() -> int:
    """Route agent commands to AgentCommands class."""
    
    agent_commands = AgentCommands()
    
    if args.agent_install:
        return 0 if agent_commands.agent_install() else 1
    elif args.agent_serve:
        return 0 if agent_commands.agent_serve(args.host, args.port) else 1
    # ... additional agent command handling
```

### Docker Compose Template Integration
```yaml
# docker-compose-agent.yml template
version: '3.8'

services:
  app-agent:
    build:
      context: .
      dockerfile: docker/agent/Dockerfile
    ports:
      - "${AGENT_API_PORT:-38886}:8000"
    environment:
      - POSTGRES_URL=postgresql://postgres-agent:5432/hive_agent
      - HIVE_API_KEY=${HIVE_API_KEY}
    depends_on:
      - postgres-agent
    container_name: hive-agents-agent
    
  postgres-agent:
    image: postgres:15
    environment:  
      - POSTGRES_DB=hive_agent
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    ports:
      - "${AGENT_POSTGRES_PORT:-35532}:5432"
    volumes:
      - ./data/postgres-agent:/var/lib/postgresql/data
    container_name: hive-postgres-agent
```

### Existing Service Integration Patterns
```python
# Integration with existing CLI patterns
class AgentService:
    def __init__(self):
        # Reuse existing credential management
        self.credential_service = CredentialService()
        
        # Reuse existing Docker service patterns  
        self.docker_service = DockerService()
        
        # Reuse existing PostgreSQL management patterns
        self.postgres_patterns = PostgreSQLService()
        
        # New agent-specific environment management
        self.agent_environment = AgentEnvironment()
```

## 🛡️ Quality Gates & Validation

### Mandatory Design Validation

#### 1. Clean Architecture Gate
- ✅ **Layer Separation**: Strict dependency inversion between layers
- ✅ **Interface Segregation**: Clear boundaries between components  
- ✅ **Single Responsibility**: Each class has one clear purpose
- ✅ **Dependency Injection**: Services injected rather than instantiated

#### 2. Scalability Gate  
- ✅ **Horizontal Scaling**: Multiple agent instances possible
- ✅ **Port Management**: Dynamic port allocation support
- ✅ **Resource Isolation**: Complete environment separation
- ✅ **Container Orchestration**: Docker Compose scalability

#### 3. Maintainability Gate
- ✅ **Code Organization**: Clear modular structure following CLI patterns
- ✅ **Error Handling**: Comprehensive error scenarios covered
- ✅ **Logging**: Structured logging for debugging and monitoring
- ✅ **Configuration**: Environment-based configuration management

#### 4. Integration Gate
- ✅ **CLI Framework**: Perfect integration with existing argument parsing
- ✅ **Service Patterns**: Consistent with PostgreSQL and Docker services
- ✅ **Credential Management**: Reuses existing credential service
- ✅ **Template System**: Leverages existing template generation

#### 5. Implementation Gate
- ✅ **Make Command Parity**: Perfect functional equivalence
- ✅ **Container Lifecycle**: Complete Docker container management
- ✅ **Environment Management**: Robust .env.agent generation
- ✅ **Data Persistence**: Proper volume mounting and permissions
- ✅ **Error Recovery**: Graceful failure handling and recovery

## 🧪 Testing Strategy

### Test Coverage Architecture
```python
# tests/cli_agent/ - New test directory structure
tests/
├── cli_agent/
│   ├── __init__.py
│   ├── test_agent_commands.py       # AgentCommands integration tests
│   ├── test_agent_service.py        # AgentService unit tests  
│   ├── test_agent_environment.py    # AgentEnvironment unit tests
│   ├── test_agent_integration.py    # End-to-end agent tests
│   └── test_make_parity.py          # Make command equivalence tests
│
├── fixtures/
│   ├── agent_fixtures.py            # Agent test fixtures
│   └── mock_containers.py           # Docker container mocks
│
└── scenarios/
    ├── agent_lifecycle_scenarios.py  # Complete lifecycle tests
    └── agent_failure_scenarios.py    # Failure and recovery tests
```

### Test Categories

#### 1. Unit Tests
- **AgentCommands**: Each command method tested in isolation
- **AgentService**: Service layer business logic validation
- **AgentEnvironment**: Environment management functionality
- **Domain Objects**: Value objects and entity validation

#### 2. Integration Tests
- **CLI Integration**: Argument parsing and command routing
- **Docker Integration**: Container lifecycle management
- **Service Integration**: Cross-service communication
- **Database Integration**: Agent database operations

#### 3. End-to-End Tests
- **Make Parity Tests**: Compare uvx vs make command outputs
- **Complete Lifecycle**: Install → Serve → Status → Stop → Reset
- **Error Scenarios**: Handle container failures, port conflicts
- **Recovery Tests**: Validate recovery from various failure states

## 🚀 Deployment & Rollout Strategy

### Implementation Phases

#### Phase 1: Foundation (AgentEnvironment + AgentService)
1. Implement `AgentEnvironment` class with .env.agent generation
2. Implement `AgentService` class with container management
3. Create unit tests for both classes
4. Validate environment generation and port management

#### Phase 2: Command Implementation (AgentCommands)
1. Implement `AgentCommands` class with all 7 commands
2. Integrate with existing CLI argument parsing in `main.py`
3. Create integration tests for CLI command routing
4. Validate functional parity with make commands

#### Phase 3: Quality & Testing (Comprehensive Validation)
1. Create complete test suite covering all functionality
2. Implement end-to-end integration tests
3. Add make command parity validation tests
4. Resolve any bugs discovered during testing

#### Phase 4: Documentation & Release (Production Ready)
1. Update CLI help documentation and README
2. Create migration guide from make to uvx commands
3. Prepare alpha release with agent management
4. Validate backwards compatibility with existing make commands

### Rollout Configuration
```python
# Feature flags for gradual rollout
AGENT_CLI_FEATURES = {
    "agent_install": True,      # Phase 1
    "agent_serve": True,        # Phase 1  
    "agent_logs": True,         # Phase 2
    "agent_status": True,       # Phase 2
    "agent_stop": True,         # Phase 2
    "agent_restart": True,      # Phase 2
    "agent_reset": True,        # Phase 3 (new functionality)
}
```

## 📊 Success Metrics

### Technical Metrics
- **Command Coverage**: 7/7 agent commands implemented (100%)
- **Functional Parity**: 100% equivalence with make commands
- **Test Coverage**: >95% for all agent management code
- **Container Startup**: <10s from command to ready state
- **Error Recovery**: <30s for failure detection and recovery

### User Experience Metrics
- **Command Consistency**: Identical behavior to PostgreSQL commands
- **Error Messages**: Clear, actionable error messages for all failure modes
- **Help Documentation**: Complete --help output for all commands
- **Migration Path**: Smooth transition from make to uvx commands

### Quality Metrics
- **Code Quality**: 0 ruff violations, 0 mypy errors
- **Integration**: No breaking changes to existing CLI functionality
- **Backwards Compatibility**: All existing make commands remain functional
- **Cross-Platform**: Works on Linux, macOS, Windows/WSL

---

## 🎯 Implementation Summary

This DDD provides a complete architectural blueprint for implementing comprehensive `--agent-*` CLI commands that fully replace `make agent` functionality while maintaining perfect backwards compatibility and following established CLI patterns.

**Key Architectural Decisions:**
1. **Clean Architecture**: Strict layer separation with dependency inversion
2. **Service Layer Pattern**: High-level AgentService orchestrating container operations
3. **Environment Isolation**: Complete separation through .env.agent and dedicated ports
4. **Template Integration**: Leveraging existing Docker Compose template system
5. **Quality-First**: Comprehensive testing strategy with make command parity validation

**Implementation Priority:**
1. AgentEnvironment (environment management foundation)
2. AgentService (container orchestration layer)  
3. AgentCommands (CLI interface implementation)
4. Integration & Testing (quality assurance)
5. Documentation & Release (production readiness)

This architecture ensures the successful replacement of make agent functionality while maintaining the high-quality standards established in the existing CLI foundation.