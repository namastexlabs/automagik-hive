# 🎯 CLI Folder Reorganization Plan

## 📊 Current State Analysis

### 🔍 Current Structure Overview
```
cli/
├── __init__.py              # Package initialization
├── main.py                  # Main entry point (266 lines, complex argument parsing)
├── commands/                # Command implementations (mixed responsibilities)
│   ├── __init__.py
│   ├── agent.py            # Agent-related commands
│   ├── genie.py            # Genie-related commands  
│   ├── health.py           # Health check commands
│   ├── init.py             # Workspace initialization
│   ├── orchestrator.py     # Orchestration commands
│   ├── postgres.py         # PostgreSQL commands
│   ├── service.py          # Service management
│   ├── uninstall.py        # Uninstall commands
│   └── workspace.py        # Workspace commands
├── core/                    # Core services (mixed with stubs)
│   ├── __init__.py
│   ├── agent_environment.py # Agent environment management
│   ├── agent_service.py    # Agent service management
│   ├── genie_service.py    # Genie service management
│   ├── main_service.py     # Main service management
│   └── postgres_service.py # PostgreSQL service management
├── docker_manager.py        # Docker operations
├── utils.py                 # CLI utilities
└── workspace.py             # Workspace manager (duplicates commands/workspace.py?)
```

### 🔴 Issues Identified

1. **Mixed Responsibilities**: Commands folder contains both command handlers and business logic
2. **Unclear Separation**: `core/` contains both services and environment management
3. **Duplicate Functionality**: `workspace.py` at root level and `commands/workspace.py`
4. **Monolithic main.py**: 266+ lines handling all argument parsing
5. **Stub Implementations**: Mixed with real implementations in core/
6. **No Clear Domain Separation**: Commands grouped by type rather than feature domain
7. **Import Complexity**: Cross-imports between commands and core
8. **Testing Difficulty**: Current structure makes isolated testing harder

## 🚀 Proposed New Structure

### 📁 Improved Organization
```
cli/
├── __init__.py                      # Package initialization
├── __main__.py                      # Entry point (python -m cli)
├── main.py                          # Slim main entry (delegates to app)
│
├── app/                             # Application core
│   ├── __init__.py
│   ├── cli.py                      # Main CLI application class
│   ├── parser.py                   # Argument parser factory
│   └── router.py                   # Command routing logic
│
├── commands/                        # Command interfaces only
│   ├── __init__.py
│   ├── base.py                     # BaseCommand abstract class
│   │
│   ├── workspace/                  # Workspace domain commands
│   │   ├── __init__.py
│   │   ├── init.py                # Init workspace command
│   │   ├── list.py                # List workspaces
│   │   └── delete.py              # Delete workspace
│   │
│   ├── agent/                      # Agent domain commands
│   │   ├── __init__.py
│   │   ├── install.py             # Install agent
│   │   ├── start.py               # Start agent
│   │   ├── stop.py                # Stop agent
│   │   ├── restart.py             # Restart agent
│   │   ├── status.py              # Agent status
│   │   ├── logs.py                # View agent logs
│   │   └── reset.py               # Reset agent
│   │
│   ├── genie/                      # Genie domain commands
│   │   ├── __init__.py
│   │   ├── install.py             # Install genie
│   │   ├── start.py               # Start genie
│   │   ├── stop.py                # Stop genie
│   │   ├── restart.py             # Restart genie
│   │   ├── status.py              # Genie status
│   │   ├── logs.py                # View genie logs
│   │   └── reset.py               # Reset genie
│   │
│   ├── postgres/                   # PostgreSQL domain commands
│   │   ├── __init__.py
│   │   ├── start.py               # Start PostgreSQL
│   │   ├── stop.py                # Stop PostgreSQL
│   │   ├── restart.py             # Restart PostgreSQL
│   │   ├── status.py              # PostgreSQL status
│   │   ├── logs.py                # View PostgreSQL logs
│   │   └── health.py              # Health check
│   │
│   ├── server/                     # Server domain commands
│   │   ├── __init__.py
│   │   ├── serve.py               # Start production server
│   │   ├── dev.py                 # Start dev server
│   │   ├── stop.py                # Stop server
│   │   ├── restart.py             # Restart server
│   │   ├── status.py              # Server status
│   │   └── logs.py                # View server logs
│   │
│   └── system/                     # System-level commands
│       ├── __init__.py
│       ├── install.py             # Full system install
│       ├── uninstall.py           # Full system uninstall
│       ├── health.py              # System health check
│       └── version.py             # Version info
│
├── services/                        # Business logic services
│   ├── __init__.py
│   ├── base.py                     # BaseService abstract class
│   │
│   ├── agent/                      # Agent service implementation
│   │   ├── __init__.py
│   │   ├── service.py             # AgentService class
│   │   ├── environment.py         # Environment management
│   │   └── config.py              # Agent configuration
│   │
│   ├── genie/                      # Genie service implementation
│   │   ├── __init__.py
│   │   ├── service.py             # GenieService class
│   │   ├── environment.py         # Environment management
│   │   └── config.py              # Genie configuration
│   │
│   ├── postgres/                   # PostgreSQL service
│   │   ├── __init__.py
│   │   ├── service.py             # PostgreSQLService class
│   │   ├── health.py              # Health checks
│   │   └── config.py              # PostgreSQL configuration
│   │
│   ├── docker/                     # Docker service
│   │   ├── __init__.py
│   │   ├── manager.py             # DockerManager class
│   │   ├── compose.py             # Docker Compose operations
│   │   └── utils.py               # Docker utilities
│   │
│   └── workspace/                  # Workspace service
│       ├── __init__.py
│       ├── manager.py             # WorkspaceManager class
│       ├── template.py            # Workspace templates
│       └── config.py              # Workspace configuration
│
├── utils/                           # Shared utilities
│   ├── __init__.py
│   ├── console.py                 # Console output formatting
│   ├── process.py                 # Process management utilities
│   ├── validation.py              # Input validation
│   ├── paths.py                   # Path handling utilities
│   └── errors.py                  # Custom exceptions
│
└── config/                         # Configuration
    ├── __init__.py
    ├── settings.py                 # Global settings
    ├── defaults.py                 # Default values
    └── constants.py                # Constants
```

## 🔄 Migration Plan

### Phase 1: Create New Structure (Non-Breaking)
1. Create all new directories
2. Create base classes and interfaces
3. Move utilities to new locations with compatibility imports

### Phase 2: Refactor Commands (Incremental)
1. Extract command logic into service layer
2. Create thin command handlers that delegate to services
3. Maintain backward compatibility with existing imports

### Phase 3: Update Imports (Systematic)
1. Update all internal imports to use new structure
2. Update test imports
3. Add deprecation warnings to old locations

### Phase 4: Clean Up (Final)
1. Remove old files
2. Remove compatibility imports
3. Update documentation

## 📝 Key Design Principles

### 1. **Single Responsibility**
- Commands: Parse arguments and delegate to services
- Services: Business logic and operations
- Utils: Reusable helper functions

### 2. **Domain-Driven Structure**
- Group by feature domain (agent, genie, postgres, etc.)
- Each domain is self-contained with its own commands and services

### 3. **Dependency Injection**
- Commands receive services through constructor
- Services are configurable and testable

### 4. **Clear Separation of Concerns**
- Presentation layer (commands) separate from business logic (services)
- Infrastructure concerns (Docker, process management) isolated

### 5. **Testability First**
- Each component independently testable
- Mock-friendly interfaces
- No direct file system or process calls in commands

## 🧪 Testing Strategy

### Test Structure Mirror
```
tests/
├── unit/
│   ├── cli/
│   │   ├── commands/
│   │   │   ├── agent/
│   │   │   ├── genie/
│   │   │   └── ...
│   │   ├── services/
│   │   │   ├── agent/
│   │   │   ├── genie/
│   │   │   └── ...
│   │   └── utils/
│   └── ...
├── integration/
│   └── cli/
│       ├── test_agent_workflow.py
│       ├── test_genie_workflow.py
│       └── ...
└── e2e/
    └── cli/
        └── test_full_workflow.py
```

## 🎯 Benefits of New Structure

1. **Better Organization**: Clear separation by domain and responsibility
2. **Improved Testability**: Each component can be tested in isolation
3. **Easier Navigation**: Developers can quickly find relevant code
4. **Scalability**: Easy to add new commands and services
5. **Maintainability**: Changes are localized to specific domains
6. **Reduced Coupling**: Services don't depend on command structure
7. **Better IDE Support**: Clear module structure improves autocomplete
8. **Parallel Development**: Teams can work on different domains independently

## 📊 Import Dependency Fix Examples

### Before (Current)
```python
# cli/commands/agent.py
from cli.core.agent_service import AgentService
from cli.docker_manager import DockerManager
from cli.utils import run_command
```

### After (Improved)
```python
# cli/commands/agent/start.py
from cli.services.agent import AgentService
from cli.commands.base import BaseCommand

class StartAgentCommand(BaseCommand):
    def __init__(self, agent_service: AgentService):
        self.agent_service = agent_service
    
    def execute(self, args):
        return self.agent_service.start(args.workspace)
```

## 🚀 Implementation Order

1. **Week 1**: Create base structure and interfaces
2. **Week 2**: Migrate utilities and services
3. **Week 3**: Refactor commands incrementally
4. **Week 4**: Update tests and documentation
5. **Week 5**: Remove old code and compatibility layers

## 🔧 Backward Compatibility

During migration, maintain compatibility:
```python
# cli/core/agent_service.py (old location)
# Compatibility import
from cli.services.agent import AgentService
__all__ = ['AgentService']

import warnings
warnings.warn(
    "Importing from cli.core.agent_service is deprecated. "
    "Use cli.services.agent instead.",
    DeprecationWarning,
    stacklevel=2
)
```

## ✅ Success Criteria

- [ ] All tests pass with new structure
- [ ] No breaking changes for existing users
- [ ] Improved code coverage (target: 85%+)
- [ ] Reduced cyclomatic complexity
- [ ] Clear documentation for new structure
- [ ] Performance benchmarks show no regression