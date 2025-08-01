# Technical Specification Document: UVX Agent Management System - Complete Docker → UVX Replacement

## 1. OVERVIEW
**Objective**: Replace entire `make agent` Docker-based system with pure UVX command interface providing identical functionality through 7 comprehensive agent management commands.

**Success Metrics**: 
- 100% functional parity with existing make commands
- Complete container orchestration via UVX
- Isolated agent development environment (ports 38886/35532)
- Production-ready alpha release with comprehensive testing

## 2. FUNCTIONAL REQUIREMENTS

### Core Agent Management Commands
- **--agent-install**: Complete environment setup from scratch (replaces `make install-agent`)
  - Generate `.env.agent` with unified credentials from main `.env`
  - Create isolated PostgreSQL container on port 35532
  - Set up data persistence in `./data/postgres-agent/`
  - Configure agent-specific container networking
  - Apply proper file permissions and user/group ownership

- **--agent-serve**: Start agent development server (replaces `make agent`)
  - Launch agent server in background on port 38886
  - Manage PID tracking in `logs/agent-server.pid`
  - Stream startup logs to `logs/agent-server.log`
  - Validate service health and connectivity
  - Return terminal control immediately (non-blocking)

- **--agent-logs**: Display agent logs (replaces `make agent-logs`)
  - Show last 50 lines of agent server logs
  - Non-blocking output with immediate return
  - Handle missing log files gracefully
  - Provide helpful messages when no logs exist

- **--agent-status**: Comprehensive status check (replaces `make agent-status`)
  - Agent server status and PID tracking
  - PostgreSQL container health on port 35532
  - Network connectivity validation
  - Recent activity summary
  - Formatted table output matching make command style

- **--agent-stop**: Clean shutdown (replaces `make agent-stop`)
  - Graceful process termination with SIGTERM
  - PID file cleanup
  - Container health validation
  - Force kill after timeout if needed

- **--agent-restart**: Complete restart cycle (replaces `make agent-restart`)
  - Clean stop → wait → start sequence
  - Preserve data and configuration
  - Validate restart success
  - Handle restart failures gracefully

- **--agent-reset**: Complete environment reset (new functionality)
  - Stop all agent services
  - Remove containers and volumes
  - Clear data directories
  - Remove `.env.agent` and PID files
  - Provide confirmation prompts for destructive operations

### User Stories
- As a developer, I want to use `uvx automagik-hive --agent-install` to create an isolated agent development environment identical to `make install-agent`
- As a developer, I want to use `uvx automagik-hive --agent-serve` to start my agent development server with the exact same behavior as `make agent`
- As a developer, I want all UVX agent commands to provide the same user experience, output formatting, and functionality as their make equivalents
- As a developer, I want to gradually migrate from make to UVX commands without losing any functionality or data

## 3. NON-FUNCTIONAL REQUIREMENTS

### Performance
- Agent container startup time: <10 seconds
- Command response time: <2 seconds for status/logs
- Background service startup: <5 seconds with immediate terminal return
- PostgreSQL container ready time: <30 seconds with health checks

### Security
- Unified credential management from main `.env` file
- Secure random password generation for PostgreSQL
- API key reuse from main environment
- Container isolation from main workspace
- Proper file permissions (600 for .env.agent, 755 for data directories)

### Reliability
- Graceful handling of missing Docker daemon
- Recovery from corrupted PID files
- Container health monitoring and validation
- Proper cleanup on service failures
- Cross-platform compatibility (Linux, macOS, Windows/WSL)

### Compatibility
- Perfect functional parity with existing make commands
- Identical output formatting and messaging
- Same data directory structure and persistence
- Backwards compatibility with existing agent environments
- Seamless transition path from make to UVX

## 4. TECHNICAL ARCHITECTURE

### System Components
- **cli/commands/agent.py**: Main command interface implementing all 7 agent commands
  - AgentCommands class with dedicated methods for each command
  - Integration with existing CLI framework
  - Error handling and user feedback
  - Help documentation and usage examples

- **cli/core/agent_service.py**: Agent lifecycle management service
  - Container orchestration (start, stop, restart, health checks)
  - Background process management with PID tracking
  - Service status monitoring and validation
  - Integration with Docker and PostgreSQL services

- **cli/core/agent_environment.py**: Agent environment configuration management
  - `.env.agent` generation from main `.env` template
  - Port translation (8886→38886, 5532→35532, /hive→/hive_agent)
  - Unified credential extraction and application
  - Environment validation and consistency checks

### Data Models
```python
# Agent Environment Configuration
class AgentEnvironment:
    api_port: int = 38886
    postgres_port: int = 35532
    database_name: str = "hive_agent"
    env_file_path: str = ".env.agent"
    data_directory: str = "./data/postgres-agent/"
    
    def generate_from_main_env(self) -> bool:
        """Generate .env.agent from main .env with port adjustments"""
    
    def validate_configuration(self) -> bool:
        """Validate agent environment configuration"""

# Agent Service Status
class AgentStatus:
    server_running: bool
    server_pid: int | None
    postgres_running: bool
    postgres_container_id: str | None
    api_accessible: bool
    recent_activity: list[str]
    
    def format_status_table(self) -> str:
        """Generate formatted status table matching make command output"""

# Container Management
class AgentContainer:
    name: str = "hive-agents-agent"
    postgres_name: str = "hive-postgres-agent"
    compose_file: str = "docker/agent/docker-compose.yml"
    
    def start_containers(self) -> bool:
        """Start agent and PostgreSQL containers"""
    
    def stop_containers(self) -> bool:
        """Stop agent and PostgreSQL containers"""
    
    def get_container_status(self) -> dict:
        """Get detailed container status information"""
```

### API Contracts
```python
# Command Interface
@click.command()
@click.option("--agent-install", is_flag=True, help="Install agent development environment")
@click.option("--agent-serve", is_flag=True, help="Start agent development server")
@click.option("--agent-logs", is_flag=True, help="Show agent server logs")
@click.option("--agent-status", is_flag=True, help="Show agent environment status")
@click.option("--agent-stop", is_flag=True, help="Stop agent development server")
@click.option("--agent-restart", is_flag=True, help="Restart agent development server") 
@click.option("--agent-reset", is_flag=True, help="Reset agent environment completely")
def agent_management(agent_install, agent_serve, agent_logs, agent_status, agent_stop, agent_restart, agent_reset):
    """Agent development environment management commands"""

# Service Integration Points
class AgentCommands:
    def __init__(self):
        self.docker_service = DockerService()
        self.postgres_service = PostgreSQLService()
        self.agent_service = AgentService()
        self.agent_environment = AgentEnvironment()
    
    def install(self) -> bool:
        """Complete agent environment installation"""
        
    def serve(self) -> bool:
        """Start agent development server in background"""
        
    def logs(self) -> bool:
        """Display agent server logs"""
        
    def status(self) -> bool:
        """Show comprehensive agent status"""
        
    def stop(self) -> bool:
        """Stop agent development server"""
        
    def restart(self) -> bool:
        """Restart agent development server"""
        
    def reset(self) -> bool:
        """Reset agent environment completely"""
```

## 5. TEST-DRIVEN DEVELOPMENT STRATEGY

### Red-Green-Refactor Integration
- **Red Phase**: Write failing tests for each agent command before implementation
  - Unit tests for command parsing and validation
  - Integration tests for Docker container management
  - End-to-end tests comparing make vs UVX command outputs
  - Error handling tests for edge cases and failures

- **Green Phase**: Implement minimal functionality to pass tests
  - Basic command structure and argument parsing
  - Core Docker container operations
  - Environment file generation and management
  - Service lifecycle management

- **Refactor Phase**: Optimize and enhance implementation
  - Code quality improvements and error handling
  - Performance optimizations for container operations
  - User experience enhancements and better messaging
  - Cross-platform compatibility refinements

### Test Categories
- **Unit Tests**: Individual command functionality and business logic
  - Environment file generation accuracy
  - Container orchestration logic
  - Status reporting and formatting
  - Error handling and edge cases

- **Integration Tests**: System interactions and Docker operations
  - Full agent installation and setup process
  - Container lifecycle management (start, stop, restart)
  - PostgreSQL database connectivity and health
  - File system operations and permissions

- **End-to-End Tests**: Complete workflow validation
  - Make vs UVX command output comparison
  - Full agent development environment lifecycle
  - Cross-platform compatibility validation
  - Migration path from make to UVX commands

### Test Coverage Requirements
- Minimum 95% code coverage for all agent management modules
- 100% coverage for critical paths (install, serve, stop operations)
- Comprehensive error scenario testing
- Performance benchmarking for container operations

## 6. IMPLEMENTATION PHASES

### Phase 1: Foundation and Architecture (Week 1)
- **Deliverable 1**: Technical specification analysis and validation
  - Complete make command behavior analysis
  - Docker container configuration mapping
  - Environment file generation patterns
  - User experience requirements documentation

- **Deliverable 2**: Agent command architecture design  
  - CLI command interface design
  - Service layer architecture
  - Container orchestration patterns
  - Error handling and recovery strategies

### Phase 2: Core Implementation (Week 1-2)
- **Deliverable 3**: Agent service foundation
  - cli/core/agent_service.py implementation
  - Container lifecycle management
  - Background process handling
  - PID tracking and management

- **Deliverable 4**: Environment management system
  - cli/core/agent_environment.py implementation
  - .env.agent generation from main .env
  - Port translation and credential management
  - Configuration validation and consistency

### Phase 3: Command Implementation (Week 2)
- **Deliverable 5**: Install and serve commands
  - --agent-install complete implementation
  - --agent-serve background server management
  - Data directory and permissions handling
  - Container health validation

- **Deliverable 6**: Monitoring and control commands
  - --agent-logs with proper formatting
  - --agent-status comprehensive reporting
  - --agent-stop graceful shutdown
  - --agent-restart complete cycle

- **Deliverable 7**: Reset functionality
  - --agent-reset destructive operations
  - Confirmation prompts and safety checks
  - Complete environment cleanup
  - Data preservation options

### Phase 4: Testing and Quality Assurance (Week 2-3)
- **Deliverable 8**: Comprehensive test suite
  - Unit tests for all agent commands
  - Integration tests for Docker operations
  - End-to-end workflow validation
  - Make vs UVX comparison tests

- **Deliverable 9**: Code quality validation
  - Ruff formatting and linting compliance
  - MyPy type checking resolution
  - Performance optimization
  - Cross-platform compatibility testing

### Phase 5: Documentation and Release (Week 3)
- **Deliverable 10**: Documentation updates
  - README.md agent management section
  - Help system and usage examples
  - Migration guide from make to UVX
  - Troubleshooting and FAQ section

- **Deliverable 11**: Alpha release preparation
  - Version bump and changelog
  - Release testing and validation
  - Distribution package updates
  - Installation and upgrade procedures

## 7. EDGE CASES & ERROR HANDLING

### Boundary Conditions
- **Docker daemon not running**: Graceful failure with installation instructions
- **Port conflicts (38886/35532 in use)**: Detection and alternative port suggestions
- **Insufficient disk space**: Pre-flight checks and clear error messages
- **Permission issues with data directories**: Automatic permission fixing with sudo prompts
- **Corrupted .env.agent file**: Regeneration from main .env with user confirmation
- **Missing main .env file**: Guided setup process or fallback to defaults

### Error Scenarios
- **Container startup failures**: Detailed error reporting and recovery suggestions
- **PostgreSQL connection failures**: Connection testing and troubleshooting guides
- **Background process crashes**: Automatic detection and restart options
- **Log file corruption**: Safe log rotation and recovery procedures
- **Network connectivity issues**: Health checks and port validation
- **Cross-platform compatibility**: OS-specific handling for Windows/WSL, macOS, Linux

### Recovery Strategies
- **Automatic retry mechanisms**: For transient Docker and network failures
- **Safe cleanup procedures**: For partial installation failures
- **Data preservation**: During reset operations with user confirmation
- **Configuration restoration**: From main .env file when agent config is corrupted
- **Manual recovery guidance**: Step-by-step troubleshooting instructions
- **Support channel information**: Links to documentation and community help

## 8. ACCEPTANCE CRITERIA

### Definition of Done
- [ ] All 7 agent commands implemented and fully functional
- [ ] Perfect functional parity with existing make commands
- [ ] 100% test coverage for critical paths, >95% overall
- [ ] Zero ruff violations and zero mypy errors
- [ ] Cross-platform compatibility validated (Linux, macOS, Windows/WSL)
- [ ] Complete documentation with migration guide
- [ ] Alpha release published and installation tested
- [ ] End-to-end validation with real agent development workflow

### Quality Gates and Validation Requirements
- **Functional Validation**: Side-by-side comparison of make vs UVX commands
- **Performance Validation**: Container startup times within specified limits
- **Security Validation**: Credential handling and permission security review
- **Compatibility Validation**: Testing across all supported platforms
- **User Experience Validation**: Usability testing with developer feedback
- **Integration Validation**: Compatibility with existing workspace configurations
- **Documentation Validation**: Complete and accurate migration instructions

### Validation Steps
1. **Install and Setup Validation**
   ```bash
   # Test complete installation process
   uvx automagik-hive --agent-install
   # Verify: .env.agent created, containers running, ports accessible
   ```

2. **Service Management Validation**
   ```bash
   # Test all service operations
   uvx automagik-hive --agent-serve
   uvx automagik-hive --agent-status  
   uvx automagik-hive --agent-logs
   uvx automagik-hive --agent-restart
   uvx automagik-hive --agent-stop
   # Verify: Identical behavior to make equivalents
   ```

3. **Reset and Recovery Validation**
   ```bash
   # Test destructive operations and recovery
   uvx automagik-hive --agent-reset
   uvx automagik-hive --agent-install
   # Verify: Clean slate recreation and data handling
   ```

4. **Migration Path Validation**
   ```bash
   # Test migration from make to UVX
   make install-agent  # Setup with make
   uvx automagik-hive --agent-stop   # Control with UVX
   uvx automagik-hive --agent-serve  # Restart with UVX
   # Verify: Seamless transition and compatibility
   ```

5. **Performance and Reliability Validation**
   - Container startup times within acceptable limits
   - Graceful handling of all documented error scenarios
   - Resource usage monitoring and optimization
   - Long-running stability testing

6. **User Acceptance Testing**
   - Developer workflow testing with real agent development
   - Documentation accuracy and completeness verification
   - Support channel testing and response validation
   - Migration experience feedback collection

---

**CRITICAL SUCCESS REQUIREMENT**: This specification must result in a complete replacement system where developers can use `uvx automagik-hive --agent-*` commands instead of `make agent*` commands with zero loss of functionality and identical user experience. The implementation must be production-ready with comprehensive testing and quality assurance.