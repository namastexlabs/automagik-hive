"""Main CLI Entry Point for Automagik Hive.

This module provides the primary CLI interface for the UVX transformation,
with PostgreSQL container management integration as the foundation.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

# Lazy import typing for command classes
if TYPE_CHECKING:
    from cli.commands.agent import AgentCommands
    from cli.commands.init import InitCommands
    from cli.commands.mcp_test import MCPTestCommands
    from cli.commands.postgres import PostgreSQLCommands
    from cli.commands.uninstall import UninstallCommands
    from cli.commands.workspace import WorkspaceCommands

# Import only lightweight utilities at startup
from lib.utils.version_reader import get_cli_version_string


class LazyCommandLoader:
    """Lazy loader for CLI command classes to optimize startup performance."""
    
    def __init__(self):
        self._init_commands = None
        self._workspace_commands = None
        self._postgres_commands = None
        self._agent_commands = None
        self._uninstall_commands = None
        self._mcp_test_commands = None
    
    @property
    def init_commands(self) -> "InitCommands":
        """Lazy load InitCommands only when needed."""
        if self._init_commands is None:
            from cli.commands.init import InitCommands
            self._init_commands = InitCommands()
        return self._init_commands
    
    @property
    def workspace_commands(self) -> "WorkspaceCommands":
        """Lazy load WorkspaceCommands only when needed."""
        if self._workspace_commands is None:
            from cli.commands.workspace import WorkspaceCommands
            self._workspace_commands = WorkspaceCommands()
        return self._workspace_commands
    
    @property
    def postgres_commands(self) -> "PostgreSQLCommands":
        """Lazy load PostgreSQLCommands only when needed."""
        if self._postgres_commands is None:
            from cli.commands.postgres import PostgreSQLCommands
            self._postgres_commands = PostgreSQLCommands()
        return self._postgres_commands
    
    @property
    def agent_commands(self) -> "AgentCommands":
        """Lazy load AgentCommands only when needed."""
        if self._agent_commands is None:
            from cli.commands.agent import AgentCommands
            self._agent_commands = AgentCommands()
        return self._agent_commands
    
    @property
    def uninstall_commands(self) -> "UninstallCommands":
        """Lazy load UninstallCommands only when needed."""
        if self._uninstall_commands is None:
            from cli.commands.uninstall import UninstallCommands
            self._uninstall_commands = UninstallCommands()
        return self._uninstall_commands
    
    @property
    def mcp_test_commands(self) -> "MCPTestCommands":
        """Lazy load MCPTestCommands only when needed."""
        if self._mcp_test_commands is None:
            from cli.commands.mcp_test import MCPTestCommands
            self._mcp_test_commands = MCPTestCommands()
        return self._mcp_test_commands


def create_parser() -> argparse.ArgumentParser:
    """Create the main CLI argument parser.

    Returns:
        ArgumentParser configured with core commands
    """
    parser = argparse.ArgumentParser(
        prog="automagik-hive",
        description="Automagik Hive CLI - UVX Development Environment (T1.5 Implementation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Core Commands:
  # Workspace initialization and startup
  uvx automagik-hive --init                    # Interactive workspace initialization
  uvx automagik-hive ./my-workspace             # Start existing workspace server
  uvx automagik-hive --help                    # Show this help message
  uvx automagik-hive --version                 # Show version information

  # PostgreSQL container management
  uvx automagik-hive --postgres-status         # Check PostgreSQL container status
  uvx automagik-hive --postgres-start          # Start PostgreSQL container
  uvx automagik-hive --postgres-stop           # Stop PostgreSQL container
  uvx automagik-hive --postgres-restart        # Restart PostgreSQL container
  uvx automagik-hive --postgres-logs           # Show PostgreSQL container logs
  uvx automagik-hive --postgres-health         # Check PostgreSQL health

  # Agent environment management (LLM-optimized)
  uvx automagik-hive --agent-install           # Install agent environment (ports 38886/35532)
  uvx automagik-hive --agent-serve             # Start agent server in background
  uvx automagik-hive --agent-stop              # Stop agent server cleanly
  uvx automagik-hive --agent-restart           # Restart agent server
  uvx automagik-hive --agent-logs              # Show agent server logs
  uvx automagik-hive --agent-status            # Check agent environment status
  uvx automagik-hive --agent-reset             # Reset agent environment

  # Uninstallation commands (DESTRUCTIVE)
  uvx automagik-hive --uninstall               # Remove current workspace data
  uvx automagik-hive --uninstall-global        # Remove ALL components (DANGEROUS)

  # With specific workspace
  uvx automagik-hive --postgres-status ./my-workspace
  uvx automagik-hive --postgres-logs ./my-workspace --tail 100
  uvx automagik-hive --agent-status ./my-workspace

Note: T1.5 Core Command Implementation - Essential UVX functionality ready.
        """,
    )

    # Core workspace commands (T1.5)
    core_group = parser.add_argument_group("Core Workspace Commands")
    core_group.add_argument(
        "--init",
        action="store_true",
        help="Interactive workspace initialization with API key collection",
    )
    core_group.add_argument(
        "--serve",
        action="store_true",
        help="Start FastAPI server directly (used internally)",
    )

    # PostgreSQL container management commands
    postgres_group = parser.add_argument_group("PostgreSQL Container Management")
    postgres_group.add_argument(
        "--postgres-status",
        action="store_true",
        help="Check PostgreSQL container status and connection info",
    )
    postgres_group.add_argument(
        "--postgres-start", action="store_true", help="Start PostgreSQL container"
    )
    postgres_group.add_argument(
        "--postgres-stop", action="store_true", help="Stop PostgreSQL container"
    )
    postgres_group.add_argument(
        "--postgres-restart", action="store_true", help="Restart PostgreSQL container"
    )
    postgres_group.add_argument(
        "--postgres-logs", action="store_true", help="Show PostgreSQL container logs"
    )
    postgres_group.add_argument(
        "--postgres-health",
        action="store_true",
        help="Check PostgreSQL health and connectivity",
    )

    # Agent environment management commands
    agent_group = parser.add_argument_group(
        "Agent Environment Management (LLM-Optimized)"
    )
    agent_group.add_argument(
        "--agent-install",
        action="store_true",
        help="Install agent environment with isolated ports (38886/35532)",
    )
    agent_group.add_argument(
        "--agent-serve",
        action="store_true",
        help="Start agent server in background (non-blocking)",
    )
    agent_group.add_argument(
        "--agent-stop", action="store_true", help="Stop agent server cleanly"
    )
    agent_group.add_argument(
        "--agent-restart", action="store_true", help="Restart agent server"
    )
    agent_group.add_argument(
        "--agent-logs", action="store_true", help="Show agent server logs"
    )
    agent_group.add_argument(
        "--agent-status", action="store_true", help="Check agent environment status"
    )
    agent_group.add_argument(
        "--agent-reset",
        action="store_true",
        help="Reset agent environment (destructive reinstall)",
    )

    # Uninstallation commands
    uninstall_group = parser.add_argument_group("Uninstallation Commands (DESTRUCTIVE)")
    uninstall_group.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove current workspace data and containers (DESTRUCTIVE)",
    )
    uninstall_group.add_argument(
        "--uninstall-global",
        action="store_true",
        help="Remove ALL Automagik Hive components globally (EXTREMELY DESTRUCTIVE)",
    )

    # Common options
    parser.add_argument(
        "workspace",
        nargs="?",
        default=None,
        help="Path to workspace directory (for startup) or workspace name (for init)",
    )
    parser.add_argument(
        "--tail", type=int, default=50, help="Number of log lines to show (default: 50)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port", type=int, default=8886, help="Port to bind server to (default: 8886)"
    )
    parser.add_argument("--version", action="version", version=get_cli_version_string())

    return parser


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = create_parser()
    args = parser.parse_args()

    # Initialize lazy command loader
    commands = LazyCommandLoader()

    # Handle core workspace commands (T1.5)
    if args.init:
        success = commands.init_commands.init_workspace(args.workspace)
        return 0 if success else 1

    # Handle direct server startup
    if args.serve:
        try:
            subprocess.run(
                [
                    "uv",
                    "run",
                    "uvicorn",
                    "api.serve:app",
                    "--host",
                    args.host,
                    "--port",
                    str(args.port),
                    "--reload",
                ],
                check=False,
            )
            return 0
        except KeyboardInterrupt:
            return 0
        except (OSError, subprocess.SubprocessError):
            return 1

    # Handle workspace startup command (T1.5)
    elif args.workspace and not any(
        [
            args.postgres_status,
            args.postgres_start,
            args.postgres_stop,
            args.postgres_restart,
            args.postgres_logs,
            args.postgres_health,
            args.agent_install,
            args.agent_serve,
            args.agent_stop,
            args.agent_restart,
            args.agent_logs,
            args.agent_status,
            args.agent_reset,
            args.uninstall,
            args.uninstall_global,
        ]
    ):
        # This is a workspace startup command
        workspace_path = args.workspace
        if Path(workspace_path).is_dir() or workspace_path.startswith(("./", "/")):
            success = commands.workspace_commands.start_workspace(workspace_path)
            return 0 if success else 1
        return 1

    # Handle PostgreSQL commands
    elif args.postgres_status:
        success = commands.postgres_commands.postgres_status(args.workspace or ".")
        return 0 if success else 1

    elif args.postgres_start:
        success = commands.postgres_commands.postgres_start(args.workspace or ".")
        return 0 if success else 1

    elif args.postgres_stop:
        success = commands.postgres_commands.postgres_stop(args.workspace or ".")
        return 0 if success else 1

    elif args.postgres_restart:
        success = commands.postgres_commands.postgres_restart(args.workspace or ".")
        return 0 if success else 1

    elif args.postgres_logs:
        success = commands.postgres_commands.postgres_logs(args.workspace or ".", args.tail)
        return 0 if success else 1

    elif args.postgres_health:
        success = commands.postgres_commands.postgres_health(args.workspace or ".")
        return 0 if success else 1

    # Handle Agent commands
    elif args.agent_install:
        success = commands.agent_commands.install(args.workspace or ".")
        return 0 if success else 1

    elif args.agent_serve:
        success = commands.agent_commands.serve(args.workspace or ".")
        return 0 if success else 1

    elif args.agent_stop:
        success = commands.agent_commands.stop(args.workspace or ".")
        return 0 if success else 1

    elif args.agent_restart:
        success = commands.agent_commands.restart(args.workspace or ".")
        return 0 if success else 1

    elif args.agent_logs:
        success = commands.agent_commands.logs(args.workspace or ".", args.tail)
        return 0 if success else 1

    elif args.agent_status:
        success = commands.agent_commands.status(args.workspace or ".")
        return 0 if success else 1

    elif args.agent_reset:
        success = commands.agent_commands.reset(args.workspace or ".")
        return 0 if success else 1

    # Handle Uninstallation commands
    elif args.uninstall:
        success = commands.uninstall_commands.uninstall_current_workspace()
        return 0 if success else 1

    elif args.uninstall_global:
        success = commands.uninstall_commands.uninstall_global()
        return 0 if success else 1

    else:
        # No command specified, show help
        parser.print_help()
        return 0


def app() -> int:
    """Main application entry point for typer integration.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    return main()


if __name__ == "__main__":
    sys.exit(main())
