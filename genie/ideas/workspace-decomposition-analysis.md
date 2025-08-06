# Workspace.py Decomposition Analysis

## Current State Analysis

**File**: `cli/commands/workspace.py` (1,321 lines)
**Class**: `UnifiedWorkspaceManager`
**Status**: CRITICAL - Requires decomposition per CLI cleanup strategy

## Functional Area Breakdown

After analyzing the UnifiedWorkspaceManager class, I've identified these distinct functional areas:

### 1. Interactive Workspace Management (Lines 33-122)
**Target Module**: `workspace_interactive.py`
**Functions**:
- `prompt_workspace_choice()` - Interactive workspace selection
- `initialize_workspace()` - New workspace initialization  
- `initialize_existing_folder()` - Convert existing folder to workspace
- `_handle_new_workspace_choice()` - New workspace choice handler
- `_handle_existing_workspace_choice()` - Existing workspace choice handler
- `_validate_workspace_name()` - Workspace name validation

**Estimated Lines**: ~290 lines

### 2. Workspace Validation & Health (Lines 123-258)
**Target Module**: `workspace_validator.py`
**Functions**:
- `validate_existing_workspace()` - Workspace validation
- `diagnose_workspace_health()` - Comprehensive health diagnostics
- `_validate_workspace_health()` - Internal health validation

**Estimated Lines**: ~336 lines

### 3. Server Startup & Management (Lines 259-646)
**Target Module**: `workspace_server.py` 
**Functions**:
- `start_workspace_server()` - Main server startup logic
- `_validate_workspace_existence()` - Workspace existence validation
- `_load_configuration()` - Configuration loading
- `_validate_database()` - Database validation
- `_check_postgres_container()` - Container status checking
- `_test_database_connection()` - Database connection testing
- `_start_server()` - FastAPI server startup
- `_detect_missing_dependencies()` - Dependency detection
- `_check_database_connectivity()` - Database connectivity checks
- `_check_python_dependencies_missing()` - Python dependency checks
- `_install_missing_dependencies()` - Dependency installation

**Estimated Lines**: ~388 lines

### 4. Workspace Creation & Setup (Lines 807-1317)
**Target Module**: `workspace_creator.py`
**Functions**:
- `_create_new_workspace()` - New workspace creation
- `_create_workspace_structure()` - Workspace structure creation
- `_copy_template_files()` - Template file processing
- `_setup_mcp_integration()` - MCP integration setup
- `_create_fallback_files()` - Fallback file creation
- `_setup_agent_templates()` - Agent template setup
- `_create_config_files()` - Configuration file creation
- `_setup_docker_integration()` - Docker integration setup

**Estimated Lines**: ~307 lines

## Decomposition Strategy

### Module Dependencies
```
workspace_interactive.py
├── imports: workspace_validator.py (for validation)
└── imports: workspace_creator.py (for creation)

workspace_validator.py  
├── standalone validation logic
└── no external dependencies within workspace modules

workspace_server.py
├── imports: workspace_validator.py (for validation)
└── standalone server management

workspace_creator.py
├── imports: template_processor from cli.core
└── standalone creation logic
```

### Shared Components
**Target Module**: `workspace_common.py`
**Contents**:
- Common imports (Path, subprocess, etc.)
- Shared constants and configuration
- Common exception classes
- Utility functions used across modules

**Estimated Lines**: ~50 lines

### Main Coordinator
**Target Module**: `workspace.py` (updated)
**Contents**:
- UnifiedWorkspaceManager class (simplified)
- Import and coordinate other modules
- Maintain backward compatibility
- Public API facade

**Estimated Lines**: ~150 lines

## File Size Validation

**Total Original**: 1,321 lines
**Target Decomposition**:
- `workspace_common.py`: ~50 lines ✅
- `workspace.py` (main): ~150 lines ✅  
- `workspace_interactive.py`: ~290 lines ✅
- `workspace_validator.py`: ~336 lines ✅
- `workspace_server.py`: ~388 lines (needs optimization to <350) ⚠️
- `workspace_creator.py`: ~307 lines ✅

**Server module optimization needed**: Break `workspace_server.py` into:
- `workspace_server.py`: Core server logic (~250 lines)
- `workspace_dependencies.py`: Dependency management (~138 lines)

**Final Structure**:
- 6 modules, all <350 lines
- Total estimated: ~1,371 lines (slight increase due to module separation overhead)
- Meets <350 line requirement per file ✅

## Implementation Approach

1. **Extract Common Components First** - Create shared utilities
2. **Create Validator Module** - Self-contained validation logic  
3. **Create Creator Module** - Self-contained creation logic
4. **Split Server Module** - Core server + dependencies
5. **Create Interactive Module** - User interaction logic
6. **Update Main Module** - Coordinate and maintain compatibility
7. **Update Imports** - Fix all dependent files

## Validation Criteria

- [ ] All modules <350 lines
- [ ] Functionality preserved (all workspace commands work)
- [ ] No circular dependencies
- [ ] Clean module boundaries
- [ ] Backward compatibility maintained
- [ ] All imports resolved correctly