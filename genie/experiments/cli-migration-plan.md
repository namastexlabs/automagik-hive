# CLI Migration Plan - Detailed Implementation

## 📋 Migration Overview

This document provides a step-by-step migration plan to reorganize the CLI folder structure without breaking any functionality. Each step includes exact file movements, import updates, and test adjustments.

## 🎯 Migration Phases

### Phase 1: Setup New Structure (Non-Breaking)
**Goal**: Create the new folder structure without affecting existing code

#### Step 1.1: Create Base Directories
```bash
# Create new directory structure
mkdir -p cli/commands/{workspace,server,agent,genie,postgres,system,production}
mkdir -p cli/services
mkdir -p cli/infrastructure  
mkdir -p cli/utils
```

#### Step 1.2: Create Base Classes
```python
# cli/commands/base.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any

class BaseCommand(ABC):
    """Base class for all CLI commands."""
    
    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path.cwd()
        self.service = self._create_service()
    
    @abstractmethod
    def _create_service(self):
        """Create the service instance for this command."""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> bool:
        """Execute the command."""
        pass
    
    def validate_args(self, **kwargs) -> bool:
        """Validate command arguments."""
        return True
```

```python
# cli/services/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseService(ABC):
    """Base class for all services."""
    
    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
    
    @abstractmethod
    def execute_operation(self, operation: str, **kwargs) -> bool:
        """Execute a service operation."""
        pass
```

### Phase 2: Migrate Infrastructure Layer
**Goal**: Move infrastructure components to dedicated folder

#### Step 2.1: Move Docker Manager
```bash
# Move docker_manager.py
mv cli/docker_manager.py cli/infrastructure/docker_manager.py
```

**Import Updates Required**:
```python
# OLD: cli/commands/postgres.py
from ..docker_manager import DockerManager

# NEW: cli/commands/postgres.py  
from ..infrastructure.docker_manager import DockerManager

# OLD: tests/cli/test_docker_manager.py
from cli.docker_manager import DockerManager

# NEW: tests/cli/test_docker_manager.py
from cli.infrastructure.docker_manager import DockerManager
```

#### Step 2.2: Move Utilities
```bash
# Move utils to dedicated folder
mv cli/utils.py cli/utils/console.py
```

**Create new utils/__init__.py**:
```python
# cli/utils/__init__.py
from .console import run_command, check_docker_available, format_status

# Maintain backward compatibility
__all__ = ['run_command', 'check_docker_available', 'format_status']
```

**Import Updates Required**:
```python
# No changes needed - imports remain the same
from cli.utils import run_command  # Still works
```

### Phase 3: Migrate Agent Commands
**Goal**: Reorganize agent commands into dedicated folder

#### Step 3.1: Split Agent Commands
```python
# cli/commands/agent/__init__.py
from .install import AgentInstallCommand
from .start import AgentStartCommand
from .stop import AgentStopCommand
from .restart import AgentRestartCommand
from .status import AgentStatusCommand
from .logs import AgentLogsCommand
from .reset import AgentResetCommand

# Backward compatibility
from .commands import AgentCommands

__all__ = [
    'AgentCommands',
    'AgentInstallCommand',
    'AgentStartCommand',
    'AgentStopCommand',
    'AgentRestartCommand',
    'AgentStatusCommand',
    'AgentLogsCommand',
    'AgentResetCommand',
]
```

```python
# cli/commands/agent/commands.py (renamed from agent.py)
"""Agent Commands Implementation - Backward Compatible."""

from pathlib import Path
from typing import Optional

from .service import AgentService

class AgentCommands:
    """Agent commands implementation."""
    
    def __init__(self, workspace_path: Path | None = None):
        self.workspace_path = workspace_path or Path()
        self.agent_service = AgentService(self.workspace_path)
    
    def install(self, workspace: str = ".") -> bool:
        """Install and start agent services."""
        from .install import AgentInstallCommand
        cmd = AgentInstallCommand(self.workspace_path)
        return cmd.execute(workspace=workspace)
    
    def start(self, workspace: str = ".") -> bool:
        """Start agent services."""
        from .start import AgentStartCommand
        cmd = AgentStartCommand(self.workspace_path)
        return cmd.execute(workspace=workspace)
    
    # ... other methods delegate to specific command classes
```

```python
# cli/commands/agent/install.py
from pathlib import Path
from typing import Optional

from ..base import BaseCommand
from .service import AgentService

class AgentInstallCommand(BaseCommand):
    """Agent install command implementation."""
    
    def _create_service(self):
        return AgentService(self.workspace_path)
    
    def execute(self, workspace: str = ".", **kwargs) -> bool:
        """Install and start agent services."""
        try:
            print(f"🚀 Installing and starting agent services in: {workspace}")
            if not self.service.install_agent_environment(workspace):
                return False
            return self.service.serve_agent(workspace)
        except Exception:
            return False
```

**Import Updates for main.py**:
```python
# OLD: cli/main.py
from .commands.agent import AgentCommands

# NEW: cli/main.py (no change needed due to __init__.py)
from .commands.agent import AgentCommands  # Still works
```

**Test Updates**:
```python
# OLD: tests/cli/commands/test_agent.py
from cli.commands.agent import AgentCommands

# NEW: tests/cli/commands/test_agent.py (no change)
from cli.commands.agent import AgentCommands  # Still works
```

### Phase 4: Migrate Services Layer
**Goal**: Move service implementations to dedicated folder

#### Step 4.1: Move Core Services
```bash
# Move services from core/ to services/
mv cli/core/agent_service.py cli/services/agent.py
mv cli/core/genie_service.py cli/services/genie.py
mv cli/core/main_service.py cli/services/main.py
mv cli/core/postgres_service.py cli/services/postgres.py
mv cli/core/agent_environment.py cli/services/environment.py
```

**Create services/__init__.py**:
```python
# cli/services/__init__.py
from .agent import AgentService
from .genie import GenieService
from .main import MainService
from .postgres import PostgreSQLService
from .environment import AgentEnvironment

# Backward compatibility mappings
__all__ = [
    'AgentService',
    'GenieService', 
    'MainService',
    'PostgreSQLService',
    'AgentEnvironment',
]
```

**Create core compatibility layer**:
```python
# cli/core/__init__.py (updated for backward compatibility)
"""Core module - backward compatibility layer."""

# Import from new locations and re-export
from ..services.agent import AgentService
from ..services.genie import GenieService
from ..services.main import MainService
from ..services.postgres import PostgreSQLService
from ..services.environment import AgentEnvironment

# Maintain backward compatibility
from ..services.agent import AgentService as agent_service
from ..services.genie import GenieService as genie_service
from ..services.main import MainService as main_service
from ..services.postgres import PostgreSQLService as postgres_service
from ..services.environment import AgentEnvironment as agent_environment

__all__ = [
    'AgentService',
    'GenieService',
    'MainService',
    'PostgreSQLService',
    'AgentEnvironment',
    'agent_service',
    'genie_service',
    'main_service',
    'postgres_service',
    'agent_environment',
]
```

### Phase 5: Refactor Entry Point
**Goal**: Split monolithic main.py into modular components

#### Step 5.1: Create Parser Module
```python
# cli/parser.py
"""Argument parser factory for CLI."""

import argparse
from pathlib import Path

def create_parser() -> argparse.ArgumentParser:
    """Create comprehensive argument parser with organized help."""
    parser = argparse.ArgumentParser(
        prog="automagik-hive",
        description="Automagik Hive - Multi-Agent AI Framework CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Add arguments (extracted from main.py)
    _add_core_arguments(parser)
    _add_agent_arguments(parser)
    _add_genie_arguments(parser)
    _add_postgres_arguments(parser)
    _add_production_arguments(parser)
    _add_subcommands(parser)
    
    return parser

def _add_core_arguments(parser):
    """Add core command arguments."""
    parser.add_argument("--init", nargs="?", const="__DEFAULT__", 
                       default=False, metavar="NAME", help="Initialize workspace")
    # ... other core arguments

# ... other helper functions
```

#### Step 5.2: Create CLI Class
```python
# cli/cli.py
"""Main CLI application class."""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

from .parser import create_parser
from .commands import CommandRegistry

class CLI:
    """Main CLI application."""
    
    def __init__(self):
        self.parser = create_parser()
        self.registry = CommandRegistry()
    
    def run(self, args=None) -> int:
        """Run the CLI with given arguments."""
        try:
            parsed_args = self.parser.parse_args(args)
            return self._execute_command(parsed_args)
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
            return 130
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return 1
    
    def _execute_command(self, args) -> int:
        """Execute the appropriate command based on arguments."""
        # Command routing logic (extracted from main.py)
        command = self.registry.get_command(args)
        if command:
            return 0 if command.execute(**vars(args)) else 1
        return 0
```

#### Step 5.3: Update main.py for Compatibility
```python
# cli/main.py (updated for backward compatibility)
"""CLI entry point - backward compatibility wrapper."""

import sys
from .cli import CLI
from .parser import create_parser

# Maintain old exports for compatibility
def main() -> int:
    """Simple CLI entry point."""
    cli = CLI()
    return cli.run()

def parse_args():
    """Parse arguments (stub for tests)."""
    return create_parser().parse_args()

class LazyCommandLoader:
    """Lazy command loader (stub for tests)."""
    
    def __init__(self):
        pass
    
    def load_command(self, command_name: str):
        """Load command stub."""
        return lambda: f"Command {command_name} loaded"

def app():
    """App function that calls main for compatibility."""
    return main()

# Provide parser for tests
parser = create_parser()

if __name__ == "__main__":
    sys.exit(main())
```

### Phase 6: Update All Tests
**Goal**: Update test imports to work with new structure

#### Test Import Mapping Table

| Old Import | New Import | Notes |
|------------|------------|-------|
| `from cli.docker_manager import DockerManager` | `from cli.infrastructure.docker_manager import DockerManager` | Infrastructure layer |
| `from cli.commands.agent import AgentCommands` | `from cli.commands.agent import AgentCommands` | No change (compatibility) |
| `from cli.core.agent_service import AgentService` | `from cli.services.agent import AgentService` | Service layer |
| `from cli.utils import run_command` | `from cli.utils import run_command` | No change (compatibility) |
| `from cli.main import main, parse_args` | `from cli.main import main, parse_args` | No change (compatibility) |

#### Step 6.1: Update Integration Tests
```python
# tests/integration/cli/test_cli_integration.py
# OLD
from cli.main import main, create_parser
from cli.commands.agent import AgentCommands

# NEW (no changes needed due to compatibility layers)
from cli.main import main, create_parser
from cli.commands.agent import AgentCommands
```

#### Step 6.2: Create Migration Script for Tests
```python
# scripts/migrate_test_imports.py
import re
from pathlib import Path

IMPORT_MAPPINGS = {
    r'from cli\.docker_manager import': 'from cli.infrastructure.docker_manager import',
    r'from cli\.core\.agent_service import': 'from cli.services.agent import',
    r'from cli\.core\.genie_service import': 'from cli.services.genie import',
    r'from cli\.core\.main_service import': 'from cli.services.main import',
    r'from cli\.core\.postgres_service import': 'from cli.services.postgres import',
    r'from cli\.core\.agent_environment import': 'from cli.services.environment import',
}

def update_test_imports():
    """Update all test imports to new structure."""
    test_dir = Path('tests')
    for test_file in test_dir.rglob('*.py'):
        content = test_file.read_text()
        original = content
        
        for old_pattern, new_import in IMPORT_MAPPINGS.items():
            content = re.sub(old_pattern, new_import, content)
        
        if content != original:
            test_file.write_text(content)
            print(f"Updated: {test_file}")

if __name__ == "__main__":
    update_test_imports()
```

### Phase 7: Final Cleanup
**Goal**: Remove old structure and validate everything works

#### Step 7.1: Run All Tests
```bash
# Ensure all tests pass with new structure
uv run pytest tests/cli -v
uv run pytest tests/integration/cli -v
```

#### Step 7.2: Remove Old Core Directory
```bash
# After confirming all tests pass
rm -rf cli/core/*.py  # Keep __init__.py for compatibility
```

#### Step 7.3: Update Documentation
```python
# Update CLI documentation
# Update CLAUDE.md with new structure
# Update README with new CLI organization
```

## 🔄 Rollback Plan

If any issues arise during migration:

1. **Git Stash Changes**: `git stash` to save work
2. **Revert to Main**: `git checkout main`
3. **Apply Fixes**: Address specific issues
4. **Retry Migration**: Apply changes incrementally

## ✅ Validation Checklist

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] CLI commands work as expected
- [ ] No import errors
- [ ] Documentation updated
- [ ] Backward compatibility maintained
- [ ] Performance not degraded

## 🎯 Success Criteria

1. **Zero Breaking Changes**: All existing code continues to work
2. **Improved Organization**: Clear command grouping and structure
3. **Better Testability**: Each component can be tested in isolation
4. **Enhanced Maintainability**: Easy to add new commands
5. **Clear Documentation**: Structure is self-documenting

## 📊 Migration Timeline

| Phase | Duration | Risk Level | Rollback Time |
|-------|----------|------------|---------------|
| Phase 1: Setup | 1 hour | Low | 5 min |
| Phase 2: Infrastructure | 2 hours | Medium | 15 min |
| Phase 3: Agent Commands | 3 hours | Medium | 30 min |
| Phase 4: Services | 2 hours | Medium | 20 min |
| Phase 5: Entry Point | 2 hours | High | 30 min |
| Phase 6: Tests | 3 hours | Low | 10 min |
| Phase 7: Cleanup | 1 hour | Low | 5 min |
| **Total** | **14 hours** | **Medium** | **< 2 hours** |

## 🚀 Execution Commands

```bash
# 1. Create feature branch
git checkout -b feature/cli-reorganization

# 2. Run migration phases
python scripts/migrate_cli_structure.py --phase 1
python scripts/migrate_cli_structure.py --phase 2
# ... etc

# 3. Run tests after each phase
uv run pytest tests/cli -v

# 4. Commit after successful migration
git add -A
git commit -m "refactor: reorganize CLI structure for better maintainability

- Organized commands into logical groups
- Separated concerns (commands/services/infrastructure)
- Improved testability and discoverability
- Maintained backward compatibility"

# 5. Create PR for review
gh pr create --title "Reorganize CLI Structure" --body "See migration plan"
```

This migration plan ensures a smooth transition with minimal risk and complete backward compatibility.