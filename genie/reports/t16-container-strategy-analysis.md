# T1.6: Container Strategy & Environment Validation Analysis

## 🐳 Container Strategy Decision (FINAL)

Based on expert recommendation and analysis of existing patterns:

**CHOSEN STRATEGY: Docker Compose Multi-Container Architecture**

### Rationale
- **Multi-Service Excellence**: PostgreSQL, Genie API, Agent API management is exactly Docker Compose's strength
- **Existing Patterns**: Current `docker-compose.yml` and `docker-compose-agent.yml` prove this approach works
- **Superior Tooling**: Standard Docker ecosystem, better logging, service management
- **Scalability**: Clear separation of concerns, independent scaling
- **Development Experience**: Excellent integration with existing Makefile patterns

### Architecture Pattern
```
UVX Command Strategy:
├── Main Workspace (Port 8886) - UVX CLI + Docker PostgreSQL
│   ├── UVX CLI process execution (Python)
│   ├── Docker PostgreSQL container (agnohq/pgvector:16) on port 5532  
│   ├── FastAPI application connects to PostgreSQL
│   └── Complete workspace validation and startup
├── Genie Container (Port 48886) - Optional Docker container
│   ├── All-in-one: PostgreSQL + FastAPI in single container
│   ├── On-demand activation via --genie-serve
│   └── Independent service for consultation workflows
└── Agent Container (Port 35532) - Optional Docker container  
    ├── All-in-one: PostgreSQL + FastAPI in single container
    ├── On-demand activation via --agent-serve
    └── Isolated development environment
```

### Rejected Alternative: All-in-One Containers
- **Issues**: Complex process management, brittle multi-service containers
- **Conclusion**: Docker Compose is superior for multi-service orchestration

## 🔍 Environment Validation System

### Required Environment Checks
1. **Python 3.12+** - Version validation for UVX compatibility
2. **UVX Environment** - Detect UVX execution context and compatibility  
3. **Docker Availability** - Installation detection with guided installation
4. **Docker Daemon** - Health check and service status
5. **PostgreSQL Image** - Pre-pull agnohq/pgvector:16 for faster startup
6. **Port Availability** - Check 8886, 5532, 48886, 35532 conflicts

### Docker Installation Detection
```python
# Multi-platform Docker detection
def check_docker_installation():
    """Check Docker installation and provide platform-specific guidance"""
    if not shutil.which("docker"):
        return {
            "installed": False,
            "guidance": get_platform_install_guidance()
        }
    
    # Test daemon connectivity
    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)
        return {"installed": True, "daemon_running": True}
    except subprocess.CalledProcessError:
        return {
            "installed": True, 
            "daemon_running": False,
            "guidance": "Start Docker service"
        }
```

### Platform-Specific Installation Guidance
- **Linux**: `curl -fsSL https://get.docker.com | sh`
- **macOS**: Download Docker Desktop or use Homebrew  
- **Windows**: Docker Desktop installer
- **WSL2**: Docker Desktop with WSL2 backend

## 📁 Container Template Creation

### Docker Compose Templates

#### Main Workspace Template (docker-compose.yml)
- **Based on**: Existing excellent `docker-compose.yml` patterns
- **Services**: PostgreSQL only (UVX CLI runs Python process directly)
- **Port**: 5532 external → 5432 container
- **Image**: agnohq/pgvector:16
- **Persistence**: ./data/postgres volume

#### Genie Container Template (docker-compose-genie.yml)  
- **Pattern**: All-in-one PostgreSQL + FastAPI container
- **Port**: 48886 external
- **Base**: Multi-stage Dockerfile (PostgreSQL + Application)
- **Database**: Internal PostgreSQL on 5432
- **Persistence**: ./data/postgres-genie volume
- **Process Management**: Supervisord for multi-process coordination

#### Agent Container Template (docker-compose-agent.yml)
- **Existing Excellence**: Current `docker-compose-agent.yml` is perfect
- **Minor Updates**: Ensure compatibility with UVX CLI integration
- **Port**: 35532 external  
- **Pattern**: PostgreSQL + FastAPI services
- **Persistence**: ./data/postgres-agent volume

### Template Generation Strategy
```python
def generate_container_templates(workspace_path, credentials):
    """Generate Docker Compose templates with secure credentials"""
    templates = {
        "docker-compose.yml": generate_main_workspace_compose(credentials),
        "docker-compose-genie.yml": generate_genie_compose(credentials), 
        "docker-compose-agent.yml": copy_existing_agent_template(credentials)
    }
    
    for filename, content in templates.items():
        write_template(workspace_path / filename, content)
```

## 🔧 Implementation Plan

### Phase 1: Environment Validation System
1. Create `cli/core/environment.py` with comprehensive environment checks
2. Multi-platform Docker detection and installation guidance
3. Python, UVX, port availability validation
4. PostgreSQL image pre-pulling for faster startup

### Phase 2: Container Template System  
1. Leverage existing `docker-compose.yml` excellence for main workspace
2. Create `docker-compose-genie.yml` all-in-one template
3. Enhance existing `docker-compose-agent.yml` for UVX integration
4. Template generation with secure credential injection

### Phase 3: CLI Integration
1. `--init` command environment validation before workspace creation
2. `./workspace` command dependency checking and container orchestration
3. Clear error messages and installation guidance
4. Graceful fallback handling for missing dependencies

## 🎯 Success Criteria

✅ **Container Strategy Decided**: Docker Compose multi-container approach chosen
✅ **Environment Validation**: Comprehensive checks for Python, UVX, Docker, ports  
✅ **Template System**: Docker Compose templates for all three service patterns
✅ **Integration Ready**: Foundation prepared for T1.7 and T1.8 implementation
✅ **UVX Compatible**: All Docker operations work within UVX environment
✅ **Cross-Platform**: Works on Linux, macOS, Windows, WSL2

## 🚨 Critical Dependencies

**Blocks**: T1.7 (Foundational Services), T1.8 (Application Services), T1.9 (Integration)
**Requires**: T1.5 (command scaffolding) - COMPLETED
**Architecture Impact**: Enables all subsequent container orchestration work