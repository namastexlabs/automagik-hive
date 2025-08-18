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

Current test files that depend on CLI structure:
- `tests/integration/cli/test_cli_integration.py` (696 lines)
- `tests/integration/cli/test_cli_argument_validation.py`
- `tests/integration/cli/test_cli_workspace_path_lines_conflict.py`
- `tests/cli/commands/test_init.py`
- Multiple other integration tests

## Proposed Solution

### New Folder Structure (Optimized for Direct Commands)

```
cli/
├── __init__.py
├── __main__.py (python -m automagik entry)
├── main.py (simplified entry point, ~30 lines)
├── app.py (main application class)
├── parser.py (unified argument parser)
├── commands/
│   ├── __init__.py
│   ├── base.py (base command interface)
│   ├── agent.py (all agent commands in one file)
│   ├── genie.py (all genie commands)
│   ├── postgres.py (all postgres commands)
│   ├── serve.py (production server commands)
│   ├── dev.py (development server commands)
│   ├── workspace.py (workspace management)
│   ├── install.py (system installation)
│   ├── uninstall.py (system cleanup)
│   └── health.py (health checks)
├── services/
│   ├── __init__.py
│   ├── base.py (base service class)
│   ├── agent.py (agent service)
│   ├── genie.py (genie service)
│   ├── postgres.py (postgres service)
│   ├── docker.py (docker operations)
│   └── workspace.py (workspace service)
├── utils/
│   ├── __init__.py
│   ├── console.py (rich console output)
│   ├── process.py (subprocess utilities)
│   ├── validation.py (input validation)
│   └── paths.py (path utilities)
└── exceptions.py (custom exceptions)
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
# Clean, honest command structure
hive agent install      # Docker containers - no workspace
hive agent start        # Docker containers - no workspace
hive agent stop         # Docker containers - no workspace
hive agent status       # Docker containers - no workspace
hive agent logs --tail 50
hive agent reset

hive genie install      # Docker containers - no workspace
hive genie start        # Docker containers - no workspace
hive genie launch       # Launches claude with GENIE.md

hive postgres start     # Single main instance - no workspace
hive postgres status    # Single main instance - no workspace
hive postgres health    # Single main instance - no workspace

hive serve              # Current directory - no workspace param
hive dev                # Current directory - no workspace param
hive install            # System-wide - no workspace param
hive uninstall          # System-wide - no workspace param
hive init [name]        # Only command that needs optional param

# Standard flags only for actual flags
hive --help
hive --version
hive agent --help       # Context-aware help
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
        prog='hive',
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
    genie = subparsers.add_parser('genie', help='Genie Docker management')
    genie_sub = genie.add_subparsers(dest='action')
    genie_sub.add_parser('install', help='Install genie Docker containers')
    genie_sub.add_parser('start', help='Start genie containers')
    genie_sub.add_parser('stop', help='Stop genie containers')
    genie_sub.add_parser('restart', help='Restart genie containers')
    genie_sub.add_parser('status', help='Check container status')
    genie_logs = genie_sub.add_parser('logs', help='View container logs')
    genie_logs.add_argument('--tail', type=int, default=20)
    genie_sub.add_parser('reset', help='Reset Docker environment')
    genie_launch = genie_sub.add_parser('launch', help='Launch Claude with GENIE.md')
    genie_launch.add_argument('claude_args', nargs='*', help='Args to pass to claude')
    
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

#### 4. Simplified Main Entry
```python
# cli/main.py (30 lines max)
import sys
from cli.app import Application

def main():
    """Main entry point."""
    app = Application()
    return app.run(sys.argv[1:])

if __name__ == '__main__':
    sys.exit(main())
```

#### 5. Application Class (Command Router)
```python
# cli/app.py
from cli.parser import create_parser
from cli.commands import COMMAND_MAP

class Application:
    """Main application that routes commands."""
    
    def run(self, args):
        parser = create_parser()
        parsed = parser.parse_args(args)
        
        # Route to appropriate command
        if parsed.command in COMMAND_MAP:
            command = COMMAND_MAP[parsed.command]()
            return command.execute(parsed)
        
        parser.print_help()
        return 1
```

### Migration Strategy (Clean Break Refactor)

#### Phase 1: Parser Revolution
- Create new unified parser.py with direct command structure
- Implement clean command routing in app.py
- NO backward compatibility - clean break from old patterns

#### Phase 2: Structure Creation (Clean Slate)
- Create simplified folder structure
- Implement base command and service classes
- Build new service implementations from scratch
- Delete old patterns immediately

#### Phase 3: Command Implementation
- Implement each command group in single file (agent.py, genie.py, etc.)
- Build clean command structure from scratch
- Create new import structure
- Ensure all file names are descriptive and clean
- No aliases - explicit commands only

#### Phase 4: Clean Entry Point
- Create new main.py with ~30 lines
- Implement app.py with clean routing logic
- Build parser.py with modern command structure
- Add rich console output for UX
- Validate naming rules compliance

#### Phase 5: Test Refactor
- Reorganize entire tests/ folder to mirror new CLI structure
- Update all test imports to use new paths
- Remove any test files with forbidden naming patterns
- Ensure 95%+ coverage with clean test names

#### Phase 6: Final Polish
- Ensure all tests pass with new structure
- Remove duplicate workspace.py
- Update all documentation with new command style
- Validate all file names follow naming rules

### Import Replacement Map

```python
# Complete replacement - no compatibility imports
# OLD imports will be DELETED, NEW imports will be the only option
{
    "cli.commands.agent.AgentCommands": "cli.commands.agent.AgentCommand",
    "cli.commands.postgres.PostgreSQLCommands": "cli.commands.postgres.PostgresCommand",
    "cli.commands.genie.GenieCommands": "cli.commands.genie.GenieCommand",
    "cli.commands.service.ServiceManager": "cli.commands.serve.ServeCommand",
    "cli.commands.init.InitCommands": "cli.commands.install.InstallCommand",
    "cli.commands.uninstall.UninstallCommands": "cli.commands.uninstall.UninstallCommand",
    "cli.docker_manager.DockerManager": "cli.services.docker.DockerService",
    "cli.workspace.WorkspaceManager": "cli.services.workspace.WorkspaceService",
    # Core service replacements
    "cli.core.agent_service.AgentService": "cli.services.agent.AgentService",
    "cli.core.genie_service.GenieService": "cli.services.genie.GenieService",
    "cli.core.postgres_service.PostgreSQLService": "cli.services.postgres.PostgresService"
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
- [ ] New direct command style works intuitively with `hive` command
- [ ] All tests updated to new command patterns
- [ ] Test folder reorganized to mirror new structure
- [ ] Import statements in tests updated to new structure
- [ ] Help text is clear and helpful for each command
- [ ] Zero legacy code remains after refactor
- [ ] All file names follow clean naming rules (no "improved", "better", etc.)
- [ ] Program executable renamed from `automagik-hive` to `hive`

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
- Main entry point: ~30 lines
- App.py: ~100 lines
- Parser.py: ~150 lines
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