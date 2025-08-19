# Technical Specification Document: CLI Folder Reorganization

## Executive Summary

This TSD defines the complete refactoring of the Automagik Hive CLI folder structure to follow Python best practices, improve maintainability, enhance testability, and provide an exceptional Developer Experience (DX). This is a clean-break refactor - no backward compatibility, no legacy code, just modern CLI patterns.

## Problem Analysis

### Current Structure Issues

```
cli/
├── main.py (310+ lines, monolithic argument parsing)
├── commands/ (mixed responsibilities, inconsistent patterns)
├── core/ (services mixed with stubs)  
├── docker_manager.py (singleton utility)
├── utils.py (utility functions)
└── workspace.py (DUPLICATE of commands/workspace.py)
```

### Identified Problems

1. **Monolithic main.py**: 310+ lines handling argument parsing, command routing, and execution
2. **Mixed Responsibilities**: `commands/` contains both command handlers and business logic
3. **Code Duplication**: `workspace.py` exists both at root and in `commands/`
4. **Inconsistent Patterns**: Different command files follow different architectures
5. **Poor Testability**: Tightly coupled components make unit testing difficult
6. **Violation of SRP**: Single files handling multiple concerns
7. **Import Complexity**: Complex cross-dependencies between modules
8. **Service Layer Confusion**: `core/` mixes actual services with stubs
9. **Poor DX**: Current `--command` style (e.g., `--agent-install`) less intuitive than direct commands
10. **Confusing Command Style**: Mix of flags (`--help`), double-dash commands (`--agent-install`), and subcommands
11. **Fake Workspace Parameters**: Every command accepts `[WORKSPACE]` but ignores it:
    - Agent/Genie are Docker-only (no workspace concept)
    - PostgreSQL is single instance (no per-workspace DB)
    - Install/uninstall are system-wide operations
    - Serve/dev always use current directory
12. **Misleading "Global" Flags**: `--tail`, `--host`, `--port` only work with specific commands

### Test Dependencies Analysis

**Complete list of 35 test files** that depend on CLI structure (20,800+ lines total):

#### Unit Tests - CLI Commands (12 files, ~6,000 lines)
- `tests/cli/commands/test_agent_commands.py` (631 lines) - AgentCommands, AgentService
- `tests/cli/commands/test_agent_coverage.py` (580 lines) - AgentCommands
- `tests/cli/commands/test_genie.py` (977 lines) - GenieCommands  
- `tests/cli/commands/test_genie_cli_command.py` (126 lines) - GenieCommands
- `tests/cli/commands/test_health.py` (45 lines) - HealthChecker
- `tests/cli/commands/test_init.py` (281 lines) - InitCommands
- `tests/cli/commands/test_orchestrator.py` (45 lines) - WorkflowOrchestrator
- `tests/cli/commands/test_postgres.py` (740 lines) - PostgreSQLCommands
- `tests/cli/commands/test_service.py` (467 lines) - ServiceManager
- `tests/cli/commands/test_uninstall.py` (443 lines) - UninstallCommands
- `tests/cli/commands/test_workspace_commands.py` (614 lines) - WorkspaceCommands

#### Unit Tests - CLI Core Services (4 files, ~3,500 lines)
- `tests/cli/core/test_agent_environment.py` (641 lines) - AgentEnvironment
- `tests/cli/core/test_agent_service.py` (1,139 lines) - AgentService
- `tests/cli/core/test_main_service.py` (1,238 lines) - MainService  
- `tests/cli/core/test_postgres_service.py` (447 lines) - PostgreSQLService

#### Unit Tests - CLI Root (4 files, ~3,000 lines)
- `tests/cli/test_main.py` (85 lines) - main, create_parser
- `tests/cli/test_utils.py` (515 lines) - cli.utils functions
- `tests/cli/test_workspace.py` (758 lines) - WorkspaceManager
- `tests/cli/test_docker_manager.py` (1,606 lines) - DockerManager

#### Integration Tests - CLI (7 files, ~4,000 lines)
- `tests/integration/cli/test_cli_integration.py` (695 lines) - main, create_parser
- `tests/integration/cli/test_cli_argument_validation.py` (327 lines) - create_parser
- `tests/integration/cli/test_cli_workspace_path_lines_conflict.py` (417 lines) - create_parser
- `tests/integration/cli/test_argument_parsing_edge_cases.py` (381 lines) - create_parser
- `tests/integration/cli/test_coverage_validation.py` (952 lines) - all command imports
- `tests/integration/cli/test_health_system.py` (282 lines) - HealthChecker
- `tests/integration/cli/test_main_cli.py` (934 lines) - app, main

#### Integration Tests - Other (8 files, ~4,500 lines)
- `tests/integration/cli/core/test_agent_environment_integration.py` (1,152 lines)
- `tests/integration/cli/core/test_agent_service_integration.py` (1,282 lines)
- `tests/integration/docker/test_docker_manager_integration.py` (47 lines)
- `tests/integration/auth/test_cli_credential_integration.py` (70 lines)
- `tests/integration/auth/test_single_credential_integration.py` (178 lines)
- `tests/integration/e2e/test_agent_commands_integration.py` (1,090 lines)
- `tests/integration/e2e/test_uv_run_workflow_e2e.py` (947 lines)
- `tests/integration/e2e/test_version_sync.py` (145 lines)

## Proposed Solution

### New Folder Structure (CLI-Only Refactor)

**CLI Migration to automagik_hive/cli/ - Phase 1 of Package Structure:**

This refactor focuses ONLY on CLI reorganization:
- CLI moves to `automagik_hive/cli/` for future PyPI readiness
- Other modules (ai/, api/, lib/) remain at root for now (separate wish)
- Clean break refactor - no backward compatibility
- All CLI imports updated to use `automagik_hive.cli.*`

```
# Project structure after CLI-only migration
automagik_hive/                    # Package directory (CLI only for now)
├── __init__.py                    # Package initialization
└── cli/                           # Refactored CLI module
    ├── __init__.py
    ├── main.py                    # Entry point + routing (~130 lines)
    ├── parser.py                  # Unified argument parser
    ├── commands/
    │   ├── __init__.py
    │   ├── base.py                # Base command interface
    │   ├── agent.py               # All agent commands
    │   ├── genie.py               # All genie commands
    │   ├── postgres.py            # All postgres commands
    │   ├── serve.py               # Production server commands
    │   ├── dev.py                 # Development server commands
    │   ├── workspace.py           # Workspace management
    │   ├── install.py             # System installation
    │   ├── uninstall.py           # System cleanup
    │   └── health.py              # Health checks
    ├── services/
    │   ├── __init__.py
    │   ├── base.py                # Base service class
    │   ├── agent.py               # Agent service
    │   ├── genie.py               # Genie service
    │   ├── postgres.py            # Postgres service
    │   ├── docker.py              # Docker operations
    │   └── workspace.py           # Workspace service
    ├── utils/
    │   ├── __init__.py
    │   ├── console.py             # Rich console output
    │   ├── process.py             # Subprocess utilities
    │   ├── validation.py          # Input validation
    │   └── paths.py               # Path utilities
    ├── exceptions.py              # Custom exceptions
    └── CLAUDE.md                  # CLI architectural documentation for future agents

# These remain at root (unchanged for now - separate wish)
ai/                                # Multi-agent system (stays at root)
api/                               # API layer (stays at root)
lib/                               # Shared services (stays at root)
tests/                             # Tests (stays at root)

# Project root files
pyproject.toml                     # Package configuration
README.md                          # Project documentation
.gitignore                         # Git ignore patterns
```

### Import Changes After CLI Migration

**Before (current flat structure):**
```python
# Current CLI imports
from cli.main import main
from cli.commands.agent import AgentCommands
from cli.core.agent_service import AgentService
from cli.docker_manager import DockerManager
from cli.workspace import WorkspaceManager

# Other module imports (unchanged)
from lib.auth.service import AuthService
from ai.agents.registry import AgentRegistry
from api.serve import app
```

**After (CLI-only migration):**
```python
# New CLI imports with package namespace
from automagik_hive.cli.main import main
from automagik_hive.cli.commands.agent import AgentCommand
from automagik_hive.cli.services.agent import AgentService
from automagik_hive.cli.services.docker import DockerService
from automagik_hive.cli.services.workspace import WorkspaceService

# Other module imports (remain unchanged for now)
from lib.auth.service import AuthService  # Still at root
from ai.agents.registry import AgentRegistry  # Still at root
from api.serve import app  # Still at root
```

### PyPI Package Configuration

**pyproject.toml updates:**
```toml
[project]
name = "automagik-hive"
version = "0.1.0"
description = "Enterprise Multi-Agent AI Framework"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "agno>=0.0.35",
    "rich>=13.0.0",
    "docker>=6.0.0",
    # ... other dependencies
]

[project.scripts]
automagik-hive = "automagik_hive.cli.main:main"
hive = "automagik_hive.cli.main:main"  # Short alias

[tool.setuptools]
packages = ["automagik_hive"]
package-dir = {"": "."}

[tool.setuptools.package-data]
automagik_hive = [
    "**/*.yaml",
    "**/*.yml",
    "**/*.md",
    "**/*.csv",
]
```

### Command Style Migration (DX Improvement)

#### Current Style (Confusing Mix)
```bash
# Double-dash commands (unintuitive)
automagik-hive --agent-install
automagik-hive --agent-start
automagik-hive --postgres-status

# Subcommands (inconsistent)
automagik-hive install
automagik-hive genie
```

#### New Style (Direct Commands - No Fake Parameters)
```bash
# Clean, honest command structure (using full package name for consistency)
automagik-hive agent install      # Docker containers - no workspace
automagik-hive agent start        # Docker containers - no workspace
automagik-hive agent stop         # Docker containers - no workspace
automagik-hive agent status       # Docker containers - no workspace
automagik-hive agent logs --tail 50
automagik-hive agent reset

automagik-hive genie install      # Docker containers - no workspace
automagik-hive genie start        # Docker containers - no workspace
automagik-hive genie              # Launches claude with GENIE.md (direct, like current)
automagik-hive genie -- --model opus  # Pass args to claude after --

automagik-hive postgres start     # Single main instance - no workspace
automagik-hive postgres status    # Single main instance - no workspace
automagik-hive postgres health    # Single main instance - no workspace

automagik-hive serve              # Current directory - no workspace param
automagik-hive dev                # Current directory - no workspace param
automagik-hive install            # System-wide - no workspace param
automagik-hive uninstall          # System-wide - no workspace param
automagik-hive init [name]        # Only command that needs optional param

# Standard flags only for actual flags
automagik-hive --help
automagik-hive --version
automagik-hive agent --help       # Context-aware help

# Users can create shell alias: alias hive=automagik-hive
# Or use with uvx: uvx automagik-hive agent install
```

### Architectural Patterns

#### 1. Direct Command Pattern with argparse subparsers
```python
# cli/commands/base_command.py
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseCommand(ABC):
    """Base command interface following Command pattern."""
    
    @abstractmethod
    def execute(self, args: Dict[str, Any]) -> bool:
        """Execute the command with given arguments."""
        pass
    
    @abstractmethod
    def validate_args(self, args: Dict[str, Any]) -> bool:
        """Validate command arguments."""
        pass
```

#### 2. Service Layer Pattern
```python
# cli/services/base_service.py
from abc import ABC, abstractmethod

class BaseService(ABC):
    """Base service for business logic separation."""
    
    @abstractmethod
    def install(self, workspace_path: str) -> bool:
        """Install service components."""
        pass
    
    @abstractmethod
    def start(self, workspace_path: str) -> bool:
        """Start service."""
        pass
```

#### 3. Unified Parser with Subcommands
```python
# cli/parser.py
def create_parser() -> argparse.ArgumentParser:
    """Create parser with direct command approach."""
    parser = argparse.ArgumentParser(
        prog='automagik-hive',
        description='Automagik Hive - Multi-Agent AI Framework'
    )
    
    # Global flags
    parser.add_argument('--version', action='version')
    parser.add_argument('--verbose', '-v', action='store_true')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Agent commands (Docker-only, no workspace)
    agent = subparsers.add_parser('agent', help='Agent Docker management')
    agent_sub = agent.add_subparsers(dest='action')
    agent_sub.add_parser('install', help='Install agent Docker containers')
    agent_sub.add_parser('start', help='Start agent containers')
    agent_sub.add_parser('stop', help='Stop agent containers')
    agent_sub.add_parser('restart', help='Restart agent containers')
    agent_sub.add_parser('status', help='Check container status')
    agent_logs = agent_sub.add_parser('logs', help='View container logs')
    agent_logs.add_argument('--tail', type=int, default=20)
    agent_sub.add_parser('reset', help='Reset Docker environment')
    
    # Genie commands (Docker-only, no workspace)
    genie = subparsers.add_parser('genie', help='Genie Docker management / Launch Claude with GENIE.md')
    genie.add_argument('claude_args', nargs='*', help='Arguments to pass to claude')
    genie_sub = genie.add_subparsers(dest='action')
    genie_sub.add_parser('install', help='Install genie Docker containers')
    genie_sub.add_parser('start', help='Start genie containers')
    genie_sub.add_parser('stop', help='Stop genie containers')
    genie_sub.add_parser('restart', help='Restart genie containers')
    genie_sub.add_parser('status', help='Check container status')
    genie_logs = genie_sub.add_parser('logs', help='View container logs')
    genie_logs.add_argument('--tail', type=int, default=20)
    genie_sub.add_parser('reset', help='Reset Docker environment')
    # Note: Direct 'genie' command (without subcommand) launches Claude with GENIE.md
    # This is handled in the main routing logic, not as a subparser
    
    # PostgreSQL commands (Single instance, no workspace)
    postgres = subparsers.add_parser('postgres', help='Main PostgreSQL management')
    postgres_sub = postgres.add_subparsers(dest='action')
    postgres_sub.add_parser('start', help='Start main PostgreSQL')
    postgres_sub.add_parser('stop', help='Stop main PostgreSQL')
    postgres_sub.add_parser('restart', help='Restart main PostgreSQL')
    postgres_sub.add_parser('status', help='Check PostgreSQL status')
    postgres_logs = postgres_sub.add_parser('logs', help='View PostgreSQL logs')
    postgres_logs.add_argument('--tail', type=int, default=20)
    postgres_sub.add_parser('health', help='Check database health')
    
    # Direct commands (no subcommands, no workspace params)
    serve = subparsers.add_parser('serve', help='Start production server')
    serve.add_argument('--host', default='0.0.0.0', help='Host to bind')
    serve.add_argument('--port', type=int, default=8886, help='Port to bind')
    
    dev = subparsers.add_parser('dev', help='Start development server')
    dev.add_argument('--host', default='0.0.0.0', help='Host to bind')
    dev.add_argument('--port', type=int, default=8886, help='Port to bind')
    
    subparsers.add_parser('install', help='Install automagik-hive system')
    subparsers.add_parser('uninstall', help='Uninstall entire system')
    
    init = subparsers.add_parser('init', help='Initialize workspace')
    init.add_argument('name', nargs='?', help='Workspace name (current dir if omitted)')
    
    subparsers.add_parser('health', help='System health check')
    
    return parser
```

#### 4. Simplified Main Entry with Routing
```python
# cli/main.py (~130 lines - entry point + routing)
import sys
from cli.parser import create_parser
from cli.commands import get_command

def route_command(args):
    """Route parsed args to appropriate command."""
    # Handle subcommands
    if args.command == 'agent' and args.action:
        from cli.commands.agent import AgentCommand
        command = AgentCommand()
        return command.execute(args.action, args)
    
    if args.command == 'genie':
        from cli.commands.genie import GenieCommand
        command = GenieCommand()
        if args.action:
            # Handle genie subcommands (install, start, stop, etc.)
            return command.execute(args.action, args)
        else:
            # Direct 'genie' command launches Claude
            return command.launch_claude(args.claude_args)
    
    if args.command == 'postgres' and args.action:
        from cli.commands.postgres import PostgresCommand
        command = PostgresCommand()
        return command.execute(args.action, args)
    
    # Handle direct commands
    if args.command in ['serve', 'dev', 'install', 'uninstall', 'init', 'health']:
        command = get_command(args.command)
        return command.execute(args)
    
    return None

def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Route to appropriate command
    result = route_command(args)
    if result is None:
        parser.print_help()
        return 1
    
    return 0 if result else 1

if __name__ == '__main__':
    sys.exit(main())
```

### Migration Strategy (CLI-Only Clean Break Refactor)

#### Phase 1: CLI Package Directory Creation
- Create `automagik_hive/` directory at project root
- Create `automagik_hive/cli/` subdirectory structure
- Add `__init__.py` files for proper package initialization
- Keep ai/, api/, lib/ at root (unchanged for now)
- Keep tests/ at project root

#### Phase 2: CLI Structure Creation (Clean Slate)
- Create new folder structure under automagik_hive/cli/
- Implement base command and service classes
- Build service layer separating business logic from CLI
- Create utils subdirectory for shared utilities
- Add exceptions.py for custom CLI exceptions
- Create CLAUDE.md documenting CLI architecture for future agents

#### Phase 3: Parser Revolution
- Create new unified parser.py with direct command structure
- Implement clean command routing in main.py (~130 lines)
- NO backward compatibility - clean break from old patterns
- Remove ALL fake workspace parameters
- Implement proper subcommand structure

#### Phase 4: Command Implementation
- Implement each command group in single file (agent.py, genie.py, etc.)
- Consolidate related commands into single files (<300 lines each)
- Create new import structure with package prefix
- Ensure all file names are descriptive and clean
- No aliases - explicit commands only

#### Phase 5: Service Layer Implementation
- Move business logic from commands to services
- Create AgentService, GenieService, PostgresService, etc.
- Implement DockerService replacing DockerManager
- Create WorkspaceService consolidating workspace logic
- Remove duplicate workspace.py file

#### Phase 6: CLI Import Updates
- Update ALL CLI imports to use `automagik_hive.cli.*` prefix
- Update test imports for CLI modules only
- Update entry point script (.venv/bin/automagik-hive)
- Fix any circular import issues in CLI
- Keep non-CLI imports unchanged (lib.*, ai.*, api.*)

#### Phase 7: Test Refactor (CLI Tests Only)
- Update all 35 test files that import CLI modules
- Reorganize CLI test structure to mirror new layout
- Remove test_agent_commands_improved.py (forbidden pattern)
- Ensure 95%+ coverage for CLI code
- Keep non-CLI tests unchanged

#### Phase 8: Final Polish and Validation
- Ensure all CLI tests pass with new structure
- Delete old cli/ directory after migration complete
- Update CLI documentation with new import patterns
- Validate all file names follow naming rules
- Test with `uv run automagik-hive` commands

### Import Replacement Map (CLI-Only Migration)

```python
# CLI-only import replacement map
# Only CLI imports get the automagik_hive prefix
{
    # CLI Command replacements (35 test files depend on these)
    "cli.commands.agent.AgentCommands": "automagik_hive.cli.commands.agent.AgentCommand",
    "cli.commands.postgres.PostgreSQLCommands": "automagik_hive.cli.commands.postgres.PostgresCommand",
    "cli.commands.genie.GenieCommands": "automagik_hive.cli.commands.genie.GenieCommand",
    "cli.commands.service.ServiceManager": "automagik_hive.cli.commands.serve.ServeCommand",
    "cli.commands.init.InitCommands": "automagik_hive.cli.commands.workspace.WorkspaceCommand",
    "cli.commands.uninstall.UninstallCommands": "automagik_hive.cli.commands.uninstall.UninstallCommand",
    "cli.commands.workspace.WorkspaceCommands": "automagik_hive.cli.commands.workspace.WorkspaceCommand",
    "cli.commands.health.HealthChecker": "automagik_hive.cli.commands.health.HealthCommand",
    "cli.commands.orchestrator.WorkflowOrchestrator": "DELETED - not needed",
    
    # CLI Service replacements
    "cli.core.agent_service.AgentService": "automagik_hive.cli.services.agent.AgentService",
    "cli.core.genie_service.GenieService": "automagik_hive.cli.services.genie.GenieService",
    "cli.core.postgres_service.PostgreSQLService": "automagik_hive.cli.services.postgres.PostgresService",
    "cli.core.main_service.MainService": "automagik_hive.cli.services.main.MainService",
    "cli.core.agent_environment.AgentEnvironment": "automagik_hive.cli.services.agent.AgentEnvironment",
    "cli.core.agent_service.DockerComposeManager": "automagik_hive.cli.services.docker.DockerComposeManager",
    
    # CLI Utility replacements
    "cli.docker_manager.DockerManager": "automagik_hive.cli.services.docker.DockerService",
    "cli.workspace.WorkspaceManager": "automagik_hive.cli.services.workspace.WorkspaceService",
    "cli.workspace.UnifiedWorkspaceManager": "automagik_hive.cli.services.workspace.WorkspaceService",
    
    # CLI Main entry point (critical for 20+ test files)
    "cli.main.main": "automagik_hive.cli.main.main",
    "cli.main.create_parser": "automagik_hive.cli.parser.create_parser",
    "cli.main.LazyCommandLoader": "DELETED - not needed",
    "cli.main.app": "automagik_hive.cli.main.main",  # app() was just calling main()
    
    # CLI Utils (used by test_utils.py)
    "cli.utils": "automagik_hive.cli.utils.*", # Split into console.py, process.py, validation.py, paths.py
    
    # Entry point script update
    ".venv/bin/automagik-hive": "from automagik_hive.cli.main import main",
    
    # NON-CLI imports remain unchanged (for now)
    "ai.agents.registry": "ai.agents.registry",  # Stays at root
    "ai.teams.registry": "ai.teams.registry",  # Stays at root  
    "ai.workflows.registry": "ai.workflows.registry",  # Stays at root
    "api.serve": "api.serve",  # Stays at root
    "api.main": "api.main",  # Stays at root
    "lib.auth.service": "lib.auth.service",  # Stays at root
    "lib.config.settings": "lib.config.settings",  # Stays at root
    "lib.knowledge.csv_hot_reload": "lib.knowledge.csv_hot_reload",  # Stays at root
    "lib.utils.agno_proxy": "lib.utils.agno_proxy",  # Stays at root
}
```

## Test Strategy and Structure Refactor

### Test Folder Reorganization
```
tests/
├── unit/
│   └── cli/
│       ├── commands/
│       │   ├── test_agent.py
│       │   ├── test_genie.py
│       │   ├── test_postgres.py
│       │   ├── test_serve.py
│       │   ├── test_dev.py
│       │   ├── test_workspace.py
│       │   ├── test_install.py
│       │   └── test_uninstall.py
│       ├── services/
│       │   ├── test_agent_service.py
│       │   ├── test_genie_service.py
│       │   ├── test_postgres_service.py
│       │   ├── test_docker_service.py
│       │   └── test_workspace_service.py
│       ├── test_app.py
│       ├── test_parser.py
│       └── test_main.py
├── integration/
│   └── cli/
│       ├── test_agent_workflow.py
│       ├── test_genie_workflow.py
│       ├── test_postgres_workflow.py
│       ├── test_server_workflow.py
│       └── test_workspace_workflow.py
└── e2e/
    └── cli/
        ├── test_installation.py
        ├── test_full_workflow.py
        └── test_command_aliases.py
```

### Naming Rules Compliance
- **FORBIDDEN PATTERNS**: No files named with "improved", "better", "enhanced", "fixed", "new", "v2", "comprehensive"
- **CLEAN NAMES**: Use descriptive, purpose-based names only
- **EXAMPLES**: 
  - ❌ `test_cli_improved.py`
  - ❌ `test_agent_enhanced.py`
  - ✅ `test_agent.py`
  - ✅ `test_workflow.py`
- **ALREADY FIXED**: Renamed `test_agent_commands_improved.py` → `test_agent_commands.py` (kept the version with 40 tests vs 31)

### Test Coverage Requirements
- **Unit Tests**: 95%+ coverage for all new command and service classes
- **Integration Tests**: Rewrite all integration tests for new structure
- **End-to-End Tests**: Update all E2E tests for new CLI patterns
- **DX Tests**: Validate new command style works as expected
- **Alias Tests**: Ensure command aliases work properly
- **No Legacy Tests**: All old test patterns must be removed

### TDD Integration Points
- **Red Phase**: Create failing tests for each new command class before implementation
- **Green Phase**: Implement minimal functionality to pass tests
- **Refactor Phase**: Improve code quality while maintaining test coverage

## Risk Assessment

### High Risk Items
1. **Import Breaking**: Test files import specific command classes
2. **CLI Interface Changes**: Complete replacement of --command with direct commands
3. **Removing Workspace Parameters**: All fake workspace params must be removed

### Mitigation Strategies
1. **Clean Refactor**: Replace entire CLI structure in one coordinated change
2. **Remove Fake Parameters**: Eliminate all meaningless workspace params
3. **Test Update**: Update all tests to use new patterns immediately
4. **Comprehensive Testing**: Run full test suite after refactor
5. **Clear Documentation**: Document which commands are Docker-only
6. **No Legacy Code**: Remove all old patterns immediately

### Low Risk Items
1. **Internal Refactoring**: Changes to internal structure without import changes
2. **Code Organization**: Moving code within the same module
3. **Adding New Classes**: New base classes and interfaces

## Success Criteria

### Functional Requirements
- [ ] New direct command style works intuitively with `automagik-hive` command
- [ ] All CLI tests updated to new command patterns
- [ ] CLI test folder reorganized to mirror new structure
- [ ] CLI import statements in tests updated to use `automagik_hive.cli.*` imports
- [ ] Non-CLI imports remain unchanged (ai.*, api.*, lib.* stay at root)
- [ ] Help text is clear and helpful for each command
- [ ] Zero legacy CLI code remains after refactor
- [ ] All file names follow clean naming rules (no "improved", "better", etc.)
- [ ] CLI migrated to `automagik_hive/cli/` structure
- [ ] Other modules (ai/, api/, lib/) remain at root for future migration
- [ ] Entry point script works: `.venv/bin/automagik-hive`
- [ ] All 35 test files that import CLI modules updated
- [ ] Old cli/ directory deleted after successful migration
- [ ] CLAUDE.md created in automagik_hive/cli/ with complete architecture documentation
- [ ] Direct 'genie' command launches Claude with GENIE.md (no 'launch' subcommand)
- [ ] Genie command properly passes arguments to claude after --

### Quality Requirements  
- [ ] Single Responsibility Principle followed in all new classes
- [ ] Clear separation between command handling and business logic
- [ ] Consistent patterns across all command groups
- [ ] Improved testability with mockable service layer

### Performance Requirements
- [ ] CLI startup time remains under 50ms (improved from 100ms)
- [ ] Memory usage does not increase significantly
- [ ] All commands execute in same time or faster
- [ ] Subcommand parsing adds minimal overhead

### Maintainability Requirements
- [ ] Each command file under 300 lines (consolidated logic)
- [ ] Services under 200 lines each
- [ ] Main.py under 30 lines
- [ ] Clear separation between commands and services
- [ ] Easy to add new commands or subcommands
- [ ] Consistent patterns across all commands

## Orchestration Strategy

### Agent Execution Plan

#### Phase 1: Analysis and Base Structure (hive-dev-planner)
**Agent**: `hive-dev-planner`
**Execution**: Sequential
**Dependencies**: None
**Task**: 
```python
Task(
    subagent_type="hive-dev-planner",
    prompt="Analyze current CLI test dependencies and create detailed migration plan with import mapping"
)
```

#### Phase 2: Create Base Classes and Interfaces (hive-dev-coder)
**Agent**: `hive-dev-coder`
**Execution**: Sequential after Phase 1
**Dependencies**: Phase 1 completion
**Task**:
```python
Task(
    subagent_type="hive-dev-coder", 
    prompt="Create base classes: BaseCommand, BaseService, ParserFactory, and new folder structure with empty implementations"
)
```

#### Phase 3: Service Layer Implementation (hive-dev-coder)
**Agent**: `hive-dev-coder`
**Execution**: Parallel for different services
**Dependencies**: Phase 2 completion
**Tasks**:
```python
[
    Task(subagent_type="hive-dev-coder", prompt="Implement AgentService wrapping existing AgentCommands functionality"),
    Task(subagent_type="hive-dev-coder", prompt="Implement PostgresService wrapping existing PostgreSQLCommands functionality"),
    Task(subagent_type="hive-dev-coder", prompt="Implement GenieService wrapping existing GenieCommands functionality"),
    Task(subagent_type="hive-dev-coder", prompt="Implement WorkspaceService consolidating workspace functionality")
]
```

#### Phase 4: Command Migration (hive-dev-coder + hive-testing-fixer)
**Agents**: `hive-dev-coder`, `hive-testing-fixer`
**Execution**: Sequential by command group
**Dependencies**: Phase 3 completion
**Pattern**: For each command group:
```python
Task(
    subagent_type="hive-testing-fixer",
    prompt="Create unit tests for [command] following new structure patterns"
)
Task(
    subagent_type="hive-dev-coder", 
    prompt="Implement [command] using new BaseCommand pattern and service layer"
)
```

#### Phase 5: Test Validation and Compatibility (hive-testing-fixer)
**Agent**: `hive-testing-fixer`
**Execution**: Sequential after each command migration
**Dependencies**: Each Phase 4 command completion
**Task**:
```python
Task(
    subagent_type="hive-testing-fixer",
    prompt="Validate all existing integration tests pass with new command structure and fix any import issues"
)
```

#### Phase 6: Main.py Refactoring (hive-dev-coder)
**Agent**: `hive-dev-coder`
**Execution**: Sequential after all command migrations
**Dependencies**: Phase 4 and 5 completion
**Task**:
```python
Task(
    subagent_type="hive-dev-coder",
    prompt="Refactor main.py to use ParserFactory and new command routing while maintaining 100% CLI compatibility"
)
```

#### Phase 7: Final Cleanup and Validation (hive-testing-fixer + hive-dev-coder)
**Agents**: `hive-testing-fixer`, `hive-dev-coder`
**Execution**: Sequential
**Dependencies**: Phase 6 completion
**Tasks**:
```python
Task(
    subagent_type="hive-testing-fixer",
    prompt="Run complete test suite validation and performance benchmarks"
)
Task(
    subagent_type="hive-dev-coder",
    prompt="Remove old duplicate files and clean up unused imports"
)
```

### Context Provision Requirements

Each agent will receive:
- **Current CLI Structure**: Full folder tree and file contents
- **Test Dependencies**: List of all test files that import CLI modules
- **Import Map**: Detailed mapping of old to new import paths
- **Backward Compatibility Requirements**: Strict requirements for maintaining existing interfaces
- **Success Criteria**: Specific validation requirements for each phase

### Dependency Mapping

```
Phase 1 (Analysis) 
    ↓
Phase 2 (Base Structure)
    ↓
Phase 3 (Services) [Parallel execution]
    ↓
Phase 4 (Commands) [Sequential by command group]
    ↓ [After each command]
Phase 5 (Test Validation)
    ↓ [After all commands]
Phase 6 (Main.py Refactoring)
    ↓
Phase 7 (Cleanup & Final Validation)
```

### Risk Mitigation in Orchestration

- **Rollback Points**: After each phase, system remains functional
- **Incremental Validation**: Tests run after each command migration
- **Parallel Safety**: Only independent services implemented in parallel
- **Import Compatibility**: Maintained throughout all phases until final cleanup

## CLI Architecture Documentation (CLAUDE.md)

### Purpose
Create a comprehensive CLAUDE.md file in the automagik_hive/cli/ directory that documents the CLI architecture for future agents and developers. This file will ensure consistent implementation patterns when adding new commands or maintaining existing ones.

### Content Requirements
The CLAUDE.md file should include:

1. **Architecture Overview**
   - Command pattern implementation
   - Service layer separation
   - Parser structure and routing logic
   - Import conventions and package structure

2. **Command Creation Guide**
   - How to add a new command group
   - BaseCommand interface requirements
   - Service layer integration patterns
   - Testing requirements for new commands

3. **Key Patterns**
   - Direct command style (no --flags for actions)
   - Subcommand organization (agent/genie/postgres groups)
   - Service layer for business logic separation
   - Utils organization for shared functionality

4. **Import Map**
   - Clear documentation of all import paths
   - Examples of correct imports from automagik_hive.cli.*
   - Common pitfalls to avoid

5. **Testing Guidelines**
   - How to test new commands
   - Mocking patterns for services
   - Integration test requirements

6. **Future Agent Instructions**
   - DO NOT add backward compatibility
   - DO NOT create files with forbidden naming patterns
   - DO NOT add fake workspace parameters
   - ALWAYS use the service layer for business logic
   - ALWAYS follow the established command patterns

## Implementation Notes

### Key Design Decisions
1. **Direct Commands**: Modern CLI patterns only - no legacy
2. **Clean Break**: No backward compatibility - fresh start
3. **Simplified Structure**: One file per command group
4. **Service Layer**: Clean separation of business logic from CLI
5. **Subparser Pattern**: Native argparse subcommands for logical grouping
6. **No Aliases**: Explicit commands only for clarity
7. **Rich Output**: Clean console output with rich library
8. **No Legacy Code**: Complete removal of old patterns
9. **Short Program Name**: `hive` instead of `automagik-hive`

### File Size Targets
- Main.py: ~130 lines (entry point + routing)
- Parser.py: ~150 lines (argument parsing)
- Command files: <300 lines each (consolidated)
- Service files: <200 lines each
- Utility files: <100 lines each
- Test files: <350 lines each (focused testing)

### Testing Strategy Integration
- Unit tests for each command and service class
- Integration tests for command workflows
- End-to-end tests for complete CLI scenarios
- All test files follow clean naming patterns
- Test structure mirrors source code structure

This refactoring will create a maintainable, testable, and extensible CLI architecture that follows Python best practices with a complete clean-break approach - no legacy code, no backward compatibility, just modern patterns and clean naming throughout both source and test files.