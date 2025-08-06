# Uninstall.py Decomposition Analysis

## Current State Analysis

**File**: cli/commands/uninstall.py
**Size**: 825 lines
**Target**: Break into focused modules <350 lines each

## Functional Analysis

### Core Components Identified

1. **Main UninstallCommands Class** (lines 18-46)
   - Service property management (docker_service, postgres_service)
   - Lazy loading pattern implementation

2. **Primary Uninstall Operations** (lines 47-98)
   - `uninstall_current_workspace()` - UVX-optimized workspace cleanup
   - `uninstall_global()` - Complete system cleanup orchestration

3. **Workspace Detection Logic** (lines 100-115)
   - `_is_automagik_workspace()` - Hive workspace identification
   - Environment file parsing and validation

4. **User Confirmation Systems** (lines 116-441)
   - `_confirm_uvx_uninstall()` - UVX workspace confirmation with detailed preview
   - `_confirm_workspace_destruction()` - Standard workspace confirmation
   - `_confirm_global_destruction()` - Global uninstall comprehensive warnings

5. **Workspace Cleanup Operations** (lines 442-529)
   - `_cleanup_uvx_workspace()` - UVX-specific cleanup implementation
   - `_remove_workspace_completely()` - Complete workspace removal
   - `_stop_workspace_containers()` - Container management

6. **System Discovery Functions** (lines 530-636)
   - `_find_all_workspaces()` - System-wide workspace scanning
   - `_find_automagik_containers()` - Docker container discovery

7. **Global Cleanup Operations** (lines 637-797)
   - `_remove_all_workspaces()` - Batch workspace removal
   - `_remove_all_containers()` - Docker container cleanup
   - `_remove_agent_environments()` - Agent data cleanup
   - `_remove_cached_data()` - Cache and temporary file cleanup

8. **CLI Compatibility Layer** (lines 799-826)
   - `uninstall_component()` - Legacy CLI wrapper

## Decomposition Strategy

### Module 1: uninstall.py (Core Operations)
**Estimated Lines**: ~200
**Responsibilities**:
- Main UninstallCommands class
- Primary uninstall operations (current workspace, global)
- Service property management
- CLI compatibility wrapper

**Key Functions**:
- `uninstall_current_workspace()`
- `uninstall_global()`
- `uninstall_component()`
- Service property getters

### Module 2: uninstall_workspace.py (Workspace Operations)
**Estimated Lines**: ~300
**Responsibilities**:
- Workspace detection and validation
- Individual workspace cleanup operations
- UVX-specific workspace handling

**Key Functions**:
- `_is_automagik_workspace()`
- `_cleanup_uvx_workspace()`
- `_remove_workspace_completely()`
- `_stop_workspace_containers()`

### Module 3: uninstall_confirmations.py (User Interface)
**Estimated Lines**: ~325
**Responsibilities**:
- All user confirmation dialogs
- Data preview and sizing calculations
- Safety warning displays

**Key Functions**:
- `_confirm_uvx_uninstall()`
- `_confirm_workspace_destruction()`
- `_confirm_global_destruction()`

### Module 4: uninstall_discovery.py (System Scanning)
**Estimated Lines**: ~200
**Responsibilities**:
- System-wide resource discovery
- Container and volume detection
- Workspace scanning logic

**Key Functions**:
- `_find_all_workspaces()`
- `_find_automagik_containers()`
- Docker volume discovery utilities

### Module 5: uninstall_global.py (Global Cleanup)
**Estimated Lines**: ~200
**Responsibilities**:
- Global cleanup operations
- Batch removal functions
- Cache and environment cleanup

**Key Functions**:
- `_remove_all_workspaces()`
- `_remove_all_containers()`
- `_remove_agent_environments()`
- `_remove_cached_data()`

## Import Dependencies Analysis

### External Dependencies
- `os`, `shutil`, `subprocess` - System operations
- `pathlib.Path` - Path manipulation
- `typing.TYPE_CHECKING` - Type checking optimization

### Internal Dependencies
- `cli.core.docker_service.DockerService` - Docker operations
- `cli.core.postgres_service.PostgreSQLService` - Database operations

### Cross-Module Dependencies (Post-Decomposition)
- Core module imports workspace, confirmation, discovery, and global modules
- Workspace module needs confirmation functions
- Global module needs discovery functions
- All modules need shared utilities

## Implementation Challenges

### 1. Circular Dependencies
- Core module orchestrates other modules
- Confirmation module needs access to discovery functions
- Solution: Use dependency injection pattern

### 2. Shared State Management
- Docker and Postgres service instances
- Solution: Pass services as parameters or use factory pattern

### 3. Method Visibility
- Many private methods become cross-module functions
- Solution: Create clear internal APIs with proper access controls

### 4. Testing Strategy
- Each module needs independent unit tests
- Integration tests for cross-module interactions
- Preserve existing CLI behavior

## Quality Assurance

### Validation Criteria
- All modules <350 lines
- Zero linting violations
- Type checking compliance
- Functionality preservation
- Performance maintenance

### Testing Requirements
- Unit tests for each module
- Integration tests for CLI commands
- Mock testing for external dependencies
- Cross-platform compatibility testing

## Implementation Priority

1. **High Priority**: Core uninstall.py (main entry points)
2. **High Priority**: Workspace operations (most complex logic)
3. **Medium Priority**: Confirmation dialogs (user experience)
4. **Medium Priority**: Discovery functions (system interaction)
5. **Low Priority**: Global cleanup (least complex)