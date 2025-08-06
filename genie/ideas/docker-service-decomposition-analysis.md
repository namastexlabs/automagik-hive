# Docker Service Decomposition Analysis

## Current State: docker_service.py (700 lines)

### Functional Analysis
The monolithic `DockerService` class contains distinct responsibility clusters:

**1. Docker Installation Detection (lines 31-88)**
- `is_docker_available()` - Check Docker installation
- `get_docker_status()` - Comprehensive installation status  
- `_get_docker_command()` - Platform-specific Docker command detection

**2. Docker Daemon Management (lines 89-171)**
- `is_docker_running()` - Check daemon status
- `get_docker_daemon_status()` - Comprehensive daemon status
- `_parse_docker_info()` - Parse Docker info output

**3. Platform-Specific Utilities (lines 172-302)**
- `get_platform_specific_installation_guide()` - Platform installation instructions
- `detect_wsl_environment()` - WSL environment detection
- `get_docker_compose_version()` - Docker Compose version detection
- `comprehensive_docker_check()` - Complete environment analysis

**4. Workspace Validation (lines 365-467)**
- `validate_workspace_after_creation()` - Post-creation validation
- `_validate_workspace()` - Core workspace validation logic

**5. Service Management (lines 469-657)**
- Service lifecycle operations (start/stop/restart)
- Service status reporting
- Service logs management
- Bulk service operations

**6. Docker Compose Integration (lines 658-701)**
- `validate_compose_file()` - Compose file validation
- `get_available_services()` - Service discovery

## Decomposition Strategy

### Target Modules (<350 lines each)

#### 1. `docker_status.py` (~180 lines)
**Responsibility**: Docker installation and daemon status detection
**Functions**:
- `DockerStatusChecker` class
- `is_docker_available()`, `get_docker_status()`
- `is_docker_running()`, `get_docker_daemon_status()`
- `_get_docker_command()`, `_parse_docker_info()`

#### 2. `docker_platform.py` (~200 lines)  
**Responsibility**: Platform-specific Docker utilities and environment detection
**Functions**:
- `DockerPlatformUtils` class
- `get_platform_specific_installation_guide()`
- `detect_wsl_environment()`
- `get_docker_compose_version()`
- `comprehensive_docker_check()`

#### 3. `docker_workspace.py` (~150 lines)
**Responsibility**: Workspace validation and Docker-related checks
**Functions**:
- `DockerWorkspaceValidator` class  
- `validate_workspace_after_creation()`
- `_validate_workspace()`
- `validate_compose_file()`

#### 4. `docker_service.py` (core, ~170 lines)
**Responsibility**: High-level Docker service orchestration and primary API
**Functions**:
- `DockerService` class (simplified)
- Service lifecycle management (start/stop/restart)
- Service status and logs
- Integration with compose_manager
- Public API facade

## Architecture Benefits

### Single Responsibility Principle
- **docker_status**: Pure status checking, no side effects
- **docker_platform**: Platform detection and environment analysis
- **docker_workspace**: Workspace validation logic
- **docker_service**: Service orchestration and public API

### Dependency Reduction
- Status checking independent of service management
- Platform utilities isolated from core operations
- Workspace validation separate from service lifecycle

### Testability Improvement
- Mock platform detection separately from service operations
- Test workspace validation without Docker daemon
- Isolate status checking from compose operations

## Import Strategy

### New Module Structure
```python
# docker_status.py
class DockerStatusChecker:
    def is_docker_available(self) -> bool
    def get_docker_status(self) -> tuple[bool, str, str | None]
    def is_docker_running(self) -> bool
    def get_docker_daemon_status(self) -> tuple[bool, str, dict | None]

# docker_platform.py  
class DockerPlatformUtils:
    def get_platform_specific_installation_guide(self) -> dict[str, str]
    def detect_wsl_environment(self) -> tuple[bool, str | None]
    def get_docker_compose_version(self) -> tuple[bool, str | None, str | None]
    def comprehensive_docker_check(self) -> dict[str, any]

# docker_workspace.py
class DockerWorkspaceValidator:
    def validate_workspace_after_creation(self, workspace_path: Path) -> tuple[bool, list[str], list[str]]
    def validate_compose_file(self, workspace_path: str) -> bool

# docker_service.py (core)
class DockerService:
    def __init__(self):
        self.status_checker = DockerStatusChecker()
        self.platform_utils = DockerPlatformUtils() 
        self.workspace_validator = DockerWorkspaceValidator()
        self.compose_manager = DockerComposeManager()
```

### Backward Compatibility
The main `DockerService` class will delegate to specialized modules while maintaining the same public API, ensuring zero breaking changes for dependent files.

## Validation Criteria

### Line Count Targets
- ✅ `docker_status.py`: ~180 lines (target <350)
- ✅ `docker_platform.py`: ~200 lines (target <350)  
- ✅ `docker_workspace.py`: ~150 lines (target <350)
- ✅ `docker_service.py`: ~170 lines (target <350)
- **Total**: ~700 lines (preserved functionality)

### Quality Gates
- All modules pass Ruff linting
- All modules pass MyPy type checking  
- Existing tests continue to pass
- No changes to public DockerService API
- All dependent imports continue to work

## Implementation Priority

1. **docker_status.py** - Foundation for other modules
2. **docker_platform.py** - Independent platform utilities  
3. **docker_workspace.py** - Independent validation logic
4. **docker_service.py** - Core integration and public API
5. **Update imports** - core/__init__.py and dependent files
6. **Validation** - Ensure all CLI commands still work

This decomposition follows SOLID principles while maintaining complete backward compatibility and achieving the <350 lines per file target for Phase 2 CLI cleanup.