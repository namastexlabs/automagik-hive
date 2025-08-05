#!/usr/bin/env python3
"""Automagik Hive CLI - 8-Command UVX Interface.

Comprehensive CLI with install, start, stop, restart, status, health, logs, uninstall commands
supporting component-specific operations (all, workspace, agent, genie).

Interactive Docker installation, excellent DX, guided setup flow.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from cli.commands import LazyCommandLoader


def create_parser() -> argparse.ArgumentParser:
    """Create UVX-compliant argument parser with 8-command interface."""
    parser = argparse.ArgumentParser(
        prog="automagik-hive",
        description="Automagik Hive - Multi-agent AI framework (8-Command Interface)",
        epilog="""
Examples:
  %(prog)s --install agent                    # Interactive agent setup with Docker installation
  %(prog)s --start agent                      # Start agent services
  %(prog)s --stop agent                       # Stop agent services  
  %(prog)s --restart agent                    # Restart agent services
  %(prog)s --status agent                     # Check agent service status
  %(prog)s --health agent                     # Health check agent services
  %(prog)s --logs agent 100                   # Show agent logs (100 lines)
  %(prog)s --uninstall agent                  # Remove agent environment
  %(prog)s --init my-project                  # Initialize workspace
  %(prog)s ./my-workspace                     # Start existing workspace server
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Component management commands
    parser.add_argument(
        "--install",
        nargs="?",
        const="all",
        choices=["all", "workspace", "agent", "genie"],
        help="Interactive installation with Docker setup (default: all)",
    )
    
    parser.add_argument(
        "--start",
        nargs="?",
        const="all",
        choices=["all", "workspace", "agent", "genie"],
        help="Start services (default: all)",
    )
    
    parser.add_argument(
        "--stop",
        nargs="?",
        const="all",
        choices=["all", "workspace", "agent", "genie"],
        help="Stop services (default: all)",
    )
    
    parser.add_argument(
        "--restart",
        nargs="?",
        const="all",
        choices=["all", "workspace", "agent", "genie"],
        help="Restart services (default: all)",
    )
    
    parser.add_argument(
        "--status",
        nargs="?",
        const="all",
        choices=["all", "workspace", "agent", "genie"],
        help="Check service status (default: all)",
    )
    
    parser.add_argument(
        "--health",
        nargs="?",
        const="all",
        choices=["all", "workspace", "agent", "genie"],
        help="Health check services (default: all)",
    )
    
    parser.add_argument(
        "--logs",
        nargs="?",
        const="all",
        choices=["all", "workspace", "agent", "genie"],
        help="Show service logs (default: all)",
    )
    
    parser.add_argument(
        "--uninstall",
        nargs="?",
        const="all",
        choices=["all", "workspace", "agent", "genie"],
        help="Uninstall components (default: all)",
    )

    # Legacy UVX commands for backward compatibility
    parser.add_argument(
        "--init",
        nargs="?",
        const=None,
        metavar="WORKSPACE_NAME",
        help="Interactive workspace initialization (prompts for name if not provided)",
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information",
    )
    
    # Log lines argument (used with --logs)
    parser.add_argument(
        "lines",
        nargs="?",
        type=int,
        default=50,
        help="Number of log lines to show (default: 50, used with --logs)",
    )

    # Positional argument for workspace path
    parser.add_argument(
        "workspace",
        nargs="?",
        default=None,
        help="Path to workspace directory for server startup",
    )

    return parser


def validate_arguments(args: argparse.Namespace) -> tuple[bool, str | None]:
    """Validate 8-command argument structure."""
    # Count active commands
    commands = [
        args.install is not None,
        args.start is not None,
        args.stop is not None,
        args.restart is not None,
        args.status is not None,
        args.health is not None,
        args.logs is not None,
        args.uninstall is not None,
        args.init is not None,
        args.version,
        args.workspace is not None,
    ]
    command_count = sum(1 for cmd in commands if cmd)

    # Only one command allowed
    if command_count > 1:
        return False, "Only one operation allowed at a time"

    # No command provided - show help
    if command_count == 0:
        return True, None

    # Workspace path validation
    if args.workspace:
        workspace_path = Path(args.workspace)
        if not workspace_path.exists():
            return False, f"Directory not found: {args.workspace}\n💡 Run 'uvx automagik-hive --init' to create a new workspace."

    return True, None


def show_version():
    """Show version information."""
    try:
        from importlib.metadata import version
        pkg_version = version("automagik-hive")
    except ImportError:
        pkg_version = "unknown"
    
    print(f"Automagik Hive v{pkg_version}")
    print("Multi-agent AI framework with 8-command interface")
    print("Documentation: https://github.com/namastex/automagik-hive")


def main() -> int:
    """8-command CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Validate arguments
    is_valid, error_msg = validate_arguments(args)
    if not is_valid:
        print(f"❌ Error: {error_msg}", file=sys.stderr)
        return 1

    try:
        commands = LazyCommandLoader()

        # Route to command handlers - 8-command interface

        # Version command
        if args.version:
            show_version()
            return 0

        # Interactive initialization (legacy UVX compatibility)
        if args.init is not None:
            workspace_name = args.init if args.init else None
            success = commands.interactive_initializer.initialize_workspace(workspace_name)
            return 0 if success else 1

        # Workspace startup (legacy UVX compatibility)
        if args.workspace:
            success = commands.workspace_manager.start_workspace_server(args.workspace)
            return 0 if success else 1

        # Component management commands
        if args.install is not None:
            success = commands.workflow_orchestrator.execute_unified_workflow(args.install)
            return 0 if success else 1

        if args.start is not None:
            success = commands.service_manager.start_services(args.start)
            return 0 if success else 1

        if args.stop is not None:
            success = commands.service_manager.stop_services(args.stop)
            return 0 if success else 1

        if args.restart is not None:
            success = commands.service_manager.restart_services(args.restart)
            return 0 if success else 1

        if args.status is not None:
            status = commands.service_manager.get_status(args.status)
            commands.service_manager.display_status(status)
            return 0

        if args.health is not None:
            health = commands.health_checker.check_health(args.health)
            commands.health_checker.display_health(health)
            return 0

        if args.logs is not None:
            logs = commands.service_manager.get_logs(args.logs, args.lines)
            commands.service_manager.display_logs(logs)
            return 0

        if args.uninstall is not None:
            success = commands.uninstaller.uninstall_component(args.uninstall)
            return 0 if success else 1

        # No command - show help
        parser.print_help()
        return 0

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        return 130

    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
