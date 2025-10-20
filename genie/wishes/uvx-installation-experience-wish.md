# 🧞 UVX INSTALLATION EXPERIENCE WISH

**Status:** APPROVED

## Executive Summary
Transform the UVX installation from a frustrating 16-iteration multi-step process into a seamless one-command experience with comprehensive debugging and intelligent fallbacks.

## Current State Analysis

**What exists:**
- Three-stage CLI workflow (`uvx automagik-hive init → install → postgres-start → dev`)
- Silent failures swallowed by exception handlers
- Python docker package conflicting with Docker Compose config downloads
- No visibility into what's happening during installation
- PostgreSQL failures treated as warnings (return True anyway)
- 16 release candidates trying to fix installation issues

**Gap identified:**
- **Command chaining:** Users must remember and execute 4+ separate commands
- **Silent failures:** PostgreSQL setup returns success even when failing
- **Missing diagnostics:** No way to debug what went wrong
- **Docker conflict:** Init downloads Python's `docker` package instead of compose files when run via UVX
- **Poor UX:** No progress indicators, no helpful error messages, no recovery guidance
- **Testing gap:** Installation never tested locally before RC releases

**Solution approach:**
- Unified `uvx automagik-hive quickstart` command
- Comprehensive diagnostic mode (`--debug` flag)
- Smart dependency detection and installation
- Rich progress indicators with actionable failures
- Local testing harness before releases
- Separation of package dependencies from runtime assets

## Change Isolation Strategy

- **Isolation principle:** New quickstart command wraps existing services without modifying them
- **Extension pattern:** Add diagnostic layer around MainService/ServiceManager calls
- **Stability assurance:** Existing `init`, `install`, `postgres-start` commands unchanged for backwards compatibility

## Success Criteria

✅ `uvx automagik-hive quickstart my-project` completes end-to-end without user intervention
✅ Clear progress indicators show each step (templates → credentials → PostgreSQL → dev server)
✅ `--debug` flag reveals all subprocess output, file operations, and decision points
✅ PostgreSQL failures surface actual Docker errors with recovery guidance
✅ Docker Compose files downloaded correctly even when Python docker package is installed
✅ Local test suite validates installation before RC releases
✅ Installation time reduced from 4+ manual steps to <2 minutes automated
✅ Error messages provide actionable next steps (e.g., "Docker not running? Try: sudo systemctl start docker")

## Never Do (Protection Boundaries)

❌ Modify existing `init`, `install`, `postgres-start` commands (backwards compatibility)
❌ Swallow exceptions without logging diagnostic context
❌ Return success when critical steps fail
❌ Skip Docker Compose file validation after download
❌ Release RCs without local installation testing

## Technical Architecture

### Component Structure

```
CLI:
├── cli/main.py                        # Add quickstart subcommand
├── cli/commands/
│   ├── quickstart.py                  # NEW: Unified installation orchestrator
│   ├── service.py                     # MODIFY: Add diagnostic mode
│   └── postgres.py                    # MODIFY: Surface actual errors
├── cli/core/
│   ├── main_service.py                # MODIFY: Return error details
│   └── diagnostics.py                 # NEW: Diagnostic utilities
└── cli/utils/
    ├── progress.py                    # NEW: Rich progress indicators
    └── docker_validator.py            # NEW: Docker environment validation

Testing:
├── tests/cli/
│   ├── test_quickstart_command.py     # NEW: Full quickstart flow
│   ├── test_diagnostic_mode.py        # NEW: Debug output validation
│   └── test_installation_local.py     # NEW: Local pre-release testing
└── tests/integration/
    └── test_uvx_installation_e2e.py   # NEW: End-to-end UVX simulation
```

### Naming Conventions

- **CLI Commands:** `QuickstartCommands`, `DiagnosticCommands`
- **Services:** `DiagnosticService`, `ProgressIndicator`, `DockerValidator`
- **Utilities:** `check_docker_availability()`, `validate_compose_files()`, `display_rich_progress()`
- **Tests:** `test_quickstart_*.py`, `test_diagnostic_*.py`, `test_uvx_*.py`

## Task Decomposition

### Dependency Graph

```
A[Diagnostic Infrastructure] ---> B[Enhanced Services]
B ---> C[Quickstart Command]
C ---> D[Testing Harness]
D ---> E[Documentation]
```

### Group A: Diagnostic Infrastructure (Parallel Tasks)
Dependencies: None | Execute simultaneously

**A1-diagnostic-utilities**: Diagnostic helper utilities
@cli/core/ [context]
Creates: `cli/core/diagnostics.py` with system checks
Exports: `check_docker_running()`, `check_compose_available()`, `get_system_info()`
Success: Unit tests validate Docker detection logic.

**A2-progress-indicators**: Rich progress display
@cli/utils/ [context]
Creates: `cli/utils/progress.py` using rich library
Exports: `ProgressIndicator` context manager for multi-step operations
Success: Visual progress bars render correctly in terminal.

**A3-docker-validator**: Docker environment validation
@cli/utils/ [context]
Creates: `cli/utils/docker_validator.py`
Exports: `DockerValidator.validate_environment()` → returns diagnostics dict
Success: Detects Docker daemon state, Compose availability, network issues.

### Group B: Enhanced Services (After A)
Dependencies: A1-diagnostic-utilities, A3-docker-validator

**B1-main-service-diagnostics**: Add diagnostic mode to MainService
@cli/core/main_service.py [context]
Modifies: `start_postgres_only()` → return (success: bool, error_details: dict)
Changes: Capture subprocess stderr, check Docker daemon, validate compose files
Success: PostgreSQL failures return structured error information.

**B2-service-manager-debug**: Add debug flag to ServiceManager
@cli/commands/service.py [context]
Modifies: Add `debug_mode: bool = False` parameter throughout
Changes: When debug=True, print subprocess output, file paths, decisions
Success: `--debug` flag exposes full installation trace.

**B3-postgres-command-errors**: Surface PostgreSQL errors
@cli/commands/postgres.py [context]
Modifies: Stop swallowing exceptions in postgres_start/status methods
Changes: Print actual Docker errors with recovery guidance
Success: User sees "Container hive-postgres not found" instead of silent warning.

### Group C: Quickstart Command (After B)
Dependencies: All tasks in B

**C1-quickstart-implementation**: Unified installation command
@cli/commands/quickstart.py [context]
Creates: New command module orchestrating init → install → postgres-start → dev
Exports: `QuickstartCommands` class with progress tracking
Success: Single command completes full installation.

**C2-quickstart-cli-wiring**: Wire quickstart into CLI
@cli/main.py [context]
Modifies: Add `quickstart` subparser with `--debug` and `--skip-postgres` flags
Changes: Dispatch to QuickstartCommands.execute()
Success: `uvx automagik-hive quickstart --help` displays usage.

**C3-docker-compose-fix**: Prevent Python docker package conflicts
@cli/commands/service.py [context]
Modifies: `init_workspace()` → validate downloaded compose files exist
Changes: Check file size > 100 bytes, contains "services:" keyword
Success: Init fails fast if docker/ contains Python package instead of configs.

### Group D: Testing Harness (After C)
Dependencies: Complete C integration

**D1-quickstart-tests**: Test unified command flow
@tests/cli/ [context]
Creates: `tests/cli/test_quickstart_command.py`
Covers: Full init → install → postgres → dev sequence
Success: pytest passes with mocked Docker calls.

**D2-diagnostic-tests**: Validate debug mode output
@tests/cli/ [context]
Creates: `tests/cli/test_diagnostic_mode.py`
Covers: Debug flag prints subprocess commands, file paths, decisions
Success: Captured output contains expected diagnostic markers.

**D3-local-installation-tests**: Pre-release validation suite
@tests/cli/ [context]
Creates: `tests/cli/test_installation_local.py`
Covers: Run actual installation in temp directory, verify files created
Success: Test creates real workspace, starts real PostgreSQL container.

**D4-uvx-simulation-tests**: End-to-end UVX installation
@tests/integration/ [context]
Creates: `tests/integration/test_uvx_installation_e2e.py`
Covers: Simulate UVX environment (isolated venv, package install, quickstart)
Success: E2E test validates complete UVX user experience.

### Group E: Documentation & Polish (After D)
Dependencies: All tasks in D

**E1-quickstart-docs**: Document new command
@README.md [context]
Modifies: Add quickstart command to installation section
Changes: Replace multi-step instructions with single quickstart command
Success: README shows `uvx automagik-hive quickstart` as primary flow.

**E2-troubleshooting-guide**: Debug guidance documentation
@docs/ [context]
Creates: `docs/troubleshooting/installation-issues.md`
Content: Common errors (Docker not running, permissions, ports) with fixes
Success: Each error code links to specific resolution steps.

**E3-changelog-update**: Record improvements
@CHANGELOG.md [context]
Modifies: Add entry for v0.2.0rc17 with quickstart feature
Changes: List breaking changes (if any) and migration guide
Success: Changelog explains new vs old installation methods.

## Implementation Examples

### Diagnostic Utilities Pattern

```python
# cli/core/diagnostics.py
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class DockerDiagnostics:
    daemon_running: bool
    compose_available: bool
    version: Optional[str]
    error: Optional[str]


def check_docker_environment() -> DockerDiagnostics:
    """Check Docker daemon and Compose availability with diagnostics."""

    # Check Docker daemon
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=5
        )
        daemon_running = result.returncode == 0
        error = None if daemon_running else result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        daemon_running = False
        error = str(e)

    # Check Docker Compose
    compose_available = shutil.which("docker") is not None
    if compose_available:
        try:
            result = subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            version = result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            version = None
    else:
        version = None

    return DockerDiagnostics(
        daemon_running=daemon_running,
        compose_available=compose_available,
        version=version,
        error=error
    )
```

### Progress Indicator Pattern

```python
# cli/utils/progress.py
from contextlib import contextmanager
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn


class ProgressIndicator:
    """Rich progress display for multi-step operations."""

    def __init__(self, title: str):
        self.console = Console()
        self.title = title
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        )

    @contextmanager
    def step(self, description: str):
        """Context manager for a single step with status reporting."""
        task_id = self.progress.add_task(description, total=None)
        try:
            with self.progress:
                yield
            self.progress.update(task_id, description=f"✅ {description}")
        except Exception as e:
            self.progress.update(task_id, description=f"❌ {description}")
            self.console.print(f"[red]Error: {e}[/red]")
            raise
```

### Enhanced MainService Pattern

```python
# cli/core/main_service.py
from dataclasses import dataclass
from typing import Tuple


@dataclass
class PostgreSQLResult:
    success: bool
    error_type: Optional[str] = None  # "docker_not_running", "compose_missing", "timeout", "unknown"
    error_message: Optional[str] = None
    stderr: Optional[str] = None


def start_postgres_only(self, workspace_path: str, debug: bool = False) -> PostgreSQLResult:
    """Start PostgreSQL with comprehensive error reporting."""

    # Pre-flight checks
    diagnostics = check_docker_environment()
    if not diagnostics.daemon_running:
        return PostgreSQLResult(
            success=False,
            error_type="docker_not_running",
            error_message="Docker daemon is not running. Start Docker and try again.",
            stderr=diagnostics.error
        )

    if not diagnostics.compose_available:
        return PostgreSQLResult(
            success=False,
            error_type="compose_missing",
            error_message="Docker Compose not found. Install Docker Compose and try again."
        )

    # Validate compose file exists and is valid
    compose_file = self._resolve_compose_file(workspace_path)
    if compose_file is None:
        return PostgreSQLResult(
            success=False,
            error_type="compose_missing",
            error_message=f"No docker-compose.yml found in {workspace_path}"
        )

    # Validate file is actual compose config, not Python package
    if not self._validate_compose_file(compose_file):
        return PostgreSQLResult(
            success=False,
            error_type="invalid_compose",
            error_message=f"Invalid compose file at {compose_file} (may be Python docker package)"
        )

    # Execute docker compose with error capture
    try:
        result = subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "up", "-d", "hive-postgres"],
            capture_output=True,
            text=True,
            timeout=120
        )

        if debug:
            print(f"[DEBUG] Command: docker compose -f {compose_file} up -d hive-postgres")
            print(f"[DEBUG] Return code: {result.returncode}")
            print(f"[DEBUG] STDOUT: {result.stdout}")
            print(f"[DEBUG] STDERR: {result.stderr}")

        if result.returncode == 0:
            return PostgreSQLResult(success=True)
        else:
            return PostgreSQLResult(
                success=False,
                error_type="docker_error",
                error_message="Docker Compose failed to start PostgreSQL",
                stderr=result.stderr
            )

    except subprocess.TimeoutExpired:
        return PostgreSQLResult(
            success=False,
            error_type="timeout",
            error_message="PostgreSQL startup timed out after 120 seconds"
        )
    except Exception as e:
        return PostgreSQLResult(
            success=False,
            error_type="unknown",
            error_message=str(e)
        )


def _validate_compose_file(self, compose_file: Path) -> bool:
    """Validate compose file is not Python docker package."""
    try:
        content = compose_file.read_text()
        # Docker Compose files contain "services:" keyword
        # Python docker package contains "import docker"
        return "services:" in content and "import docker" not in content
    except Exception:
        return False
```

### Quickstart Command Pattern

```python
# cli/commands/quickstart.py
from pathlib import Path
from cli.commands.service import ServiceManager
from cli.utils.progress import ProgressIndicator
from cli.core.diagnostics import check_docker_environment


class QuickstartCommands:
    """Unified installation command with progress tracking."""

    def execute(self, workspace_name: str, debug: bool = False, skip_postgres: bool = False) -> bool:
        """Execute complete quickstart flow."""

        progress = ProgressIndicator(title="Automagik Hive Quickstart")
        service_manager = ServiceManager()

        # Step 1: Environment validation
        with progress.step("Validating environment"):
            diagnostics = check_docker_environment()
            if not diagnostics.daemon_running and not skip_postgres:
                print("\n⚠️  Docker daemon not running")
                print("    • Start Docker: sudo systemctl start docker")
                print("    • Or skip PostgreSQL: automagik-hive quickstart --skip-postgres")
                return False

        # Step 2: Initialize workspace
        with progress.step(f"Initializing workspace: {workspace_name}"):
            if not service_manager.init_workspace(workspace_name, force=False):
                return False

        # Step 3: Install credentials
        with progress.step("Generating credentials"):
            workspace_path = Path(workspace_name).resolve()
            from lib.auth.credential_service import CredentialService
            credential_service = CredentialService(project_root=workspace_path)
            credential_service.install_all_modes(modes=["workspace"])

        # Step 4: Start PostgreSQL (if not skipped)
        if not skip_postgres:
            with progress.step("Starting PostgreSQL container"):
                result = service_manager.main_service.start_postgres_only(
                    str(workspace_path),
                    debug=debug
                )
                if not result.success:
                    print(f"\n❌ PostgreSQL setup failed: {result.error_message}")
                    if result.error_type == "docker_not_running":
                        print("    💡 Start Docker and run: automagik-hive postgres-start")
                    if result.stderr and debug:
                        print(f"\n[DEBUG] Docker error:\n{result.stderr}")
                    return False

        # Step 5: Success summary
        print("\n" + "=" * 60)
        print("✅ Quickstart Complete!")
        print("=" * 60)
        print(f"\n📋 Next Steps:")
        print(f"   1. cd {workspace_name}")
        print(f"   2. Edit .env with your API keys")
        print(f"   3. automagik-hive dev")
        print(f"\n🌐 Then visit: http://localhost:8886/docs")
        print("=" * 60 + "\n")

        return True
```

### CLI Integration Pattern

```python
# cli/main.py
from cli.commands.quickstart import QuickstartCommands

# Add quickstart subparser
quickstart_parser = subparsers.add_parser(
    "quickstart",
    help="Complete installation in one command (init + install + postgres)"
)
quickstart_parser.add_argument(
    "workspace",
    nargs="?",
    default="my-hive-workspace",
    help="Workspace directory name"
)
quickstart_parser.add_argument(
    "--debug",
    action="store_true",
    help="Enable diagnostic output (subprocess commands, file paths, decisions)"
)
quickstart_parser.add_argument(
    "--skip-postgres",
    action="store_true",
    help="Skip PostgreSQL setup (use for SQLite or manual Docker)"
)

# Handle quickstart command
if args.command == "quickstart":
    quickstart_cmd = QuickstartCommands()
    workspace = getattr(args, "workspace", "my-hive-workspace") or "my-hive-workspace"
    debug = getattr(args, "debug", False)
    skip_postgres = getattr(args, "skip_postgres", False)
    return 0 if quickstart_cmd.execute(workspace, debug, skip_postgres) else 1
```

## Testing Protocol

```bash
# Diagnostic utilities
uv run pytest tests/cli/test_diagnostic_utilities.py -v

# Enhanced services with error handling
uv run pytest tests/cli/test_main_service_diagnostics.py -v

# Quickstart command flow
uv run pytest tests/cli/test_quickstart_command.py -v

# Local installation validation (creates real workspace)
uv run pytest tests/cli/test_installation_local.py -v --log-cli-level=DEBUG

# Full UVX simulation (end-to-end)
uv run pytest tests/integration/test_uvx_installation_e2e.py -v

# Manual smoke test
cd /tmp && uvx automagik-hive quickstart test-workspace --debug
```

## Validation Checklist

- [ ] Quickstart command completes in <2 minutes
- [ ] Debug mode reveals all subprocess output
- [ ] PostgreSQL failures show actual Docker errors
- [ ] Docker Compose files validated after download
- [ ] Progress indicators display for each step
- [ ] Error messages include actionable recovery steps
- [ ] Local test suite runs before RC releases
- [ ] UVX simulation test covers package installation
- [ ] Backwards compatibility: old commands still work
- [ ] Documentation updated with quickstart flow

## Known Issues Addressed

1. **RC16 Silent Failures:**
   - PostgreSQL setup returned True even when failing
   - No visibility into Docker daemon state
   - Exception handlers swallowed useful errors

2. **Docker Package Conflict:**
   - Init downloads Python `docker` package instead of Compose files
   - No validation that downloaded files are actual configs
   - Compose commands fail silently

3. **Poor UX:**
   - Users must chain 4+ commands manually
   - No progress indicators during operations
   - No guidance when things fail

4. **Testing Gap:**
   - Installation never tested locally before RC
   - No simulation of UVX environment
   - 16 iterations trying to fix without proper testing

## Migration Guide

**Old workflow (deprecated but still works):**
```bash
uvx automagik-hive init my-project
cd my-project
cp .env.example .env
# Edit .env...
uvx automagik-hive install
uvx automagik-hive postgres-start
uvx automagik-hive dev
```

**New workflow (recommended):**
```bash
uvx automagik-hive quickstart my-project
cd my-project
# Edit .env with API keys
uvx automagik-hive dev
```

**Debug failing installation:**
```bash
uvx automagik-hive quickstart my-project --debug
```

**Skip PostgreSQL (use SQLite):**
```bash
uvx automagik-hive quickstart my-project --skip-postgres
```

## Success Metrics

- Installation time: 4+ steps → 1 command
- Time to first run: ~5 minutes → <2 minutes
- User questions: "What's wrong?" → Clear error messages
- RC iterations: 16 → validate locally before release
- PostgreSQL failure rate: Hidden → Surfaced with fixes
- Debug capability: None → Full trace with --debug

---

**Status:** APPROVED → Ready for Forge execution

## Approval Notes

Approved by user on 2025-10-20. Ready for parallel task execution via Forge.

**Execution Command:**
```bash
/forge genie/wishes/uvx-installation-experience-wish.md
```

This will create task-specific branches from `dev` for each parallel group.
