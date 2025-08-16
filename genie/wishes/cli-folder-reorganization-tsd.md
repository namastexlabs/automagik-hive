# Technical Specification Document: CLI Folder Reorganization

## Executive Summary

This TSD defines the reorganization of the Automagik Hive CLI folder structure to follow Python best practices, improve maintainability, and enhance testability. The current structure suffers from mixed responsibilities, code duplication, and violation of single responsibility principles.

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

### Test Dependencies Analysis

Current test files that depend on CLI structure:
- `tests/integration/cli/test_cli_integration.py` (696 lines)
- `tests/integration/cli/test_cli_argument_validation.py`
- `tests/integration/cli/test_cli_workspace_path_lines_conflict.py`
- `tests/cli/commands/test_init.py`
- Multiple other integration tests

## Proposed Solution

### New Folder Structure

```
cli/
├── __init__.py
├── main.py (simplified entry point, ~50 lines)
├── parsers/
│   ├── __init__.py
│   ├── base_parser.py (base argument parser)
│   ├── subcommand_parsers/
│   │   ├── __init__.py
│   │   ├── agent_parser.py
│   │   ├── genie_parser.py
│   │   ├── postgres_parser.py
│   │   ├── production_parser.py
│   │   └── workspace_parser.py
│   └── parser_factory.py
├── commands/
│   ├── __init__.py
│   ├── base_command.py (base command interface)
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── command.py (agent command handler)
│   │   └── operations.py (agent operations)
│   ├── genie/
│   │   ├── __init__.py
│   │   ├── command.py
│   │   └── operations.py
│   ├── postgres/
│   │   ├── __init__.py
│   │   ├── command.py
│   │   └── operations.py
│   ├── production/
│   │   ├── __init__.py
│   │   ├── command.py
│   │   └── operations.py
│   ├── workspace/
│   │   ├── __init__.py
│   │   ├── command.py
│   │   └── operations.py
│   └── system/
│       ├── __init__.py
│       ├── health.py
│       ├── init.py
│       └── uninstall.py
├── services/
│   ├── __init__.py
│   ├── base_service.py
│   ├── agent_service.py
│   ├── genie_service.py
│   ├── postgres_service.py
│   ├── docker_service.py
│   └── workspace_service.py
├── utils/
│   ├── __init__.py
│   ├── common.py
│   ├── validation.py
│   └── output.py
└── exceptions.py
```

### Architectural Patterns

#### 1. Command Pattern Implementation
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

#### 3. Parser Factory Pattern
```python
# cli/parsers/parser_factory.py
class ParserFactory:
    """Factory for creating specialized argument parsers."""
    
    @staticmethod
    def create_parser() -> argparse.ArgumentParser:
        """Create the main CLI parser with all subcommands."""
        pass
```

### Migration Strategy

#### Phase 1: Structure Creation (No Breaking Changes)
- Create new folder structure alongside existing code
- Implement base classes and interfaces
- Create new service implementations that wrap existing functionality
- Ensure all existing imports continue to work

#### Phase 2: Gradual Migration (Command by Command)
- Migrate `agent` commands first (lowest risk)
- Update tests for migrated commands
- Migrate `postgres` commands
- Migrate `genie` commands
- Migrate `production` commands
- Migrate `workspace` commands
- Migrate `system` commands last

#### Phase 3: Main.py Refactoring
- Simplify main.py to use new parser factory
- Update command routing to use new command classes
- Maintain backward compatibility for all CLI interfaces

#### Phase 4: Cleanup
- Remove old command files after confirming all tests pass
- Remove duplicate workspace.py
- Clean up unused imports
- Update documentation

### Import Migration Map

```python
# OLD -> NEW import mappings
{
    "cli.commands.agent.AgentCommands": "cli.commands.agent.AgentCommand",
    "cli.commands.postgres.PostgreSQLCommands": "cli.commands.postgres.PostgresCommand",
    "cli.commands.genie.GenieCommands": "cli.commands.genie.GenieCommand",
    "cli.commands.service.ServiceManager": "cli.commands.production.ProductionCommand",
    "cli.commands.init.InitCommands": "cli.commands.system.InitCommand",
    "cli.commands.uninstall.UninstallCommands": "cli.commands.system.UninstallCommand",
    "cli.docker_manager.DockerManager": "cli.services.docker_service.DockerService",
    "cli.workspace.WorkspaceManager": "cli.services.workspace_service.WorkspaceService"
}
```

## Enhanced Test Strategy

### Unit Test Structure
```
tests/
├── cli/
│   ├── commands/
│   │   ├── test_agent_command.py
│   │   ├── test_genie_command.py
│   │   ├── test_postgres_command.py
│   │   └── test_workspace_command.py
│   ├── services/
│   │   ├── test_agent_service.py
│   │   ├── test_docker_service.py
│   │   └── test_workspace_service.py
│   ├── parsers/
│   │   ├── test_parser_factory.py
│   │   └── test_subcommand_parsers.py
│   └── test_main.py
```

### Test Coverage Requirements
- **Unit Tests**: 95%+ coverage for all new command and service classes
- **Integration Tests**: Maintain existing integration test coverage
- **End-to-End Tests**: All CLI commands must pass existing E2E tests
- **Migration Tests**: Special tests to ensure import compatibility during migration

### TDD Integration Points
- **Red Phase**: Create failing tests for each new command class before implementation
- **Green Phase**: Implement minimal functionality to pass tests
- **Refactor Phase**: Improve code quality while maintaining test coverage

## Risk Assessment

### High Risk Items
1. **Import Breaking**: Test files import specific command classes
2. **CLI Interface Changes**: Any change to CLI arguments or behavior
3. **Service Dependencies**: Complex dependencies between services

### Mitigation Strategies
1. **Backward Compatibility**: Maintain all existing imports during migration
2. **Gradual Migration**: Migrate one command group at a time
3. **Comprehensive Testing**: Run full test suite after each migration step
4. **Rollback Plan**: Keep old structure until full migration is validated

### Low Risk Items
1. **Internal Refactoring**: Changes to internal structure without import changes
2. **Code Organization**: Moving code within the same module
3. **Adding New Classes**: New base classes and interfaces

## Success Criteria

### Functional Requirements
- [ ] All existing CLI commands work identically to current behavior
- [ ] All test files pass without modification
- [ ] No breaking changes to public CLI interface
- [ ] Import statements in tests continue to work

### Quality Requirements  
- [ ] Single Responsibility Principle followed in all new classes
- [ ] Clear separation between command handling and business logic
- [ ] Consistent patterns across all command groups
- [ ] Improved testability with mockable service layer

### Performance Requirements
- [ ] CLI startup time remains under 100ms
- [ ] Memory usage does not increase significantly
- [ ] All commands execute in same time as current implementation

### Maintainability Requirements
- [ ] Each file under 200 lines (except integration files)
- [ ] Clear domain boundaries between command groups
- [ ] Consistent naming and structure patterns
- [ ] Easy to add new commands following established patterns

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
1. **Command Pattern**: Separates command parsing from execution
2. **Service Layer**: Isolates business logic from CLI concerns  
3. **Factory Pattern**: Centralizes parser creation and configuration
4. **Domain Separation**: Groups related functionality by service domain

### File Size Targets
- Main entry point: ~50 lines
- Individual command files: <150 lines
- Service files: <200 lines  
- Parser files: <100 lines
- Utility files: <100 lines

### Testing Strategy Integration
- Unit tests for each command and service class
- Integration tests for parser factory and command routing
- End-to-end tests for complete CLI workflows
- Migration tests for import compatibility

This refactoring will create a maintainable, testable, and extensible CLI architecture that follows Python best practices while ensuring zero breaking changes to existing functionality.