# CLI Uninstall Module Decomposition Plan

## Current State Analysis
- Single file: `cli/commands/uninstall.py` (798 lines)
- Single class: `UninstallCommands` with multiple responsibilities
- Clear logical separations already exist in method groupings

## Decomposition Strategy

### 1. Core Uninstall Controller (`cli/commands/uninstall.py`)
**Lines: ~150-200**
- Main UninstallCommands class (streamlined)
- Public API methods: uninstall_current_workspace(), uninstall_global(), uninstall_component()
- Service initialization and lazy loading
- High-level orchestration logic

### 2. Workspace Detection Module (`cli/commands/uninstall/workspace_detector.py`)
**Lines: ~100-150**
- Workspace identification logic
- `_is_automagik_workspace()`
- `_find_all_workspaces()`
- Validation and filtering logic

### 3. Confirmation Handler (`cli/commands/uninstall/confirmation_handler.py`)
**Lines: ~200-250**
- User confirmation dialogs
- `_confirm_uvx_uninstall()`, `_confirm_workspace_destruction()`, `_confirm_global_destruction()`
- Preview generation and user interaction
- Safety validation

### 4. Docker Operations (`cli/commands/uninstall/docker_operations.py`)
**Lines: ~150-200**
- Container discovery and management
- `_find_automagik_containers()`
- `_stop_workspace_containers()`
- `_remove_all_containers()`
- Volume cleanup

### 5. Filesystem Cleanup (`cli/commands/uninstall/filesystem_cleanup.py`)
**Lines: ~100-150**
- File and directory removal
- `_cleanup_uvx_workspace()`
- `_remove_all_workspaces()`
- `_remove_agent_environments()`
- `_remove_cached_data()`

## Benefits
- Each module <350 lines per requirement
- Clear single responsibility per module
- Maintains complete functionality
- Improves testability and maintainability
- Easier to debug and extend individual components