#!/usr/bin/env python3
"""
Automagik Hive CLI - Main Entry Point

PHASE 3 FINALIZED - Simplified 8-command structure for managing Automagik Hive components:
- Exactly 8 core commands: install, init, start, stop, restart, status, health, logs, uninstall
- Consistent component parameter handling: all|workspace|agent|genie
- Streamlined implementation without complex variations
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from cli.commands import LazyCommandLoader


def create_parser() -> argparse.ArgumentParser:
    """Create streamlined argument parser for exactly 8 core commands."""
    parser = argparse.ArgumentParser(
        prog="automagik-hive",
        description="Automagik Hive - Multi-agent AI framework CLI (Phase 3 Finalized)",
        epilog="""
Examples:
  %(prog)s --install                    # Install all components
  %(prog)s --install agent             # Install agent services only
  %(prog)s --init my-project           # Initialize new workspace
  %(prog)s ./my-workspace              # Start existing workspace server
  %(prog)s --start agent               # Start agent services only
  %(prog)s --logs genie 100            # Show genie logs (100 lines)
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # THE 8 CORE COMMANDS - NO COMPLEX VARIATIONS

    parser.add_argument(
        "--install",
        nargs="?",
        const="all",
        choices=["all", "workspace", "agent", "genie"],
        help="Install and start services (default: all)",
    )

    parser.add_argument(
        "--init",
        nargs="?",
        const=None,
        metavar="WORKSPACE_NAME",
        help="Initialize workspace (prompts for name if not provided)",
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
        help="Show service status (default: all)",
    )

    parser.add_argument(
        "--health",
        nargs="?",
        const="all",
        choices=["all", "workspace", "agent", "genie"],
        help="Run health checks (default: all)",
    )

    parser.add_argument(
        "--logs",
        nargs="*",
        default=None,
        metavar=("COMPONENT", "LINES"),
        help="Show service logs: --logs [component] [lines] (default: all, 50 lines)",
    )

    parser.add_argument(
        "--uninstall",
        nargs="?",
        const="all",
        choices=["all", "workspace", "agent", "genie"],
        help="Uninstall components (default: all)",
    )

    # Positional argument for workspace path
    parser.add_argument(
        "workspace",
        nargs="?",
        default=None,
        help="Path to workspace directory for server startup",
    )

    return parser


def validate_arguments(args: argparse.Namespace) -> tuple[bool, Optional[str]]:
    """Simplified argument validation - Phase 3 finalized."""

    # Count active commands
    commands = [
        args.install,
        args.init,
        args.start,
        args.stop,
        args.restart,
        args.status,
        args.health,
        args.logs is not None,
        args.uninstall,
    ]
    command_count = sum(1 for cmd in commands if cmd)

    # Only one command allowed
    if command_count > 1:
        return False, "Only one command allowed at a time"

    # Simple logs validation
    if args.logs is not None:
        if len(args.logs) > 2:
            return False, "--logs [component] [lines] format expected"
        if args.logs and args.logs[0] not in ["all", "workspace", "agent", "genie"]:
            return False, f"Invalid component: {args.logs[0]}"
        if len(args.logs) > 1 and not args.logs[1].isdigit():
            return False, f"Lines must be a number: {args.logs[1]}"

    # Workspace path validation
    if args.workspace:
        if command_count > 0:
            return False, "Workspace path conflicts with commands"
        if not Path(args.workspace).exists():
            return False, f"Path not found: {args.workspace}"

    return True, None


def main() -> int:
    """Simplified main CLI entry point - Phase 3 finalized."""
    parser = create_parser()
    args = parser.parse_args()

    # Validate arguments
    is_valid, error_msg = validate_arguments(args)
    if not is_valid:
        print(f"Error: {error_msg}", file=sys.stderr)
        return 1

    # Initialize command loader
    try:
        commands = LazyCommandLoader()
    except Exception as e:
        print(f"CLI initialization failed: {e}", file=sys.stderr)
        return 1

    try:
        # Route to command handlers - simplified logic

        # Workspace path (positional)
        if args.workspace:
            return (
                0
                if commands.workspace_manager.start_workspace_server(args.workspace)
                else 1
            )

        # The 8 core commands
        elif args.install:
            return (
                0
                if commands.unified_installer.install_with_workflow(args.install)
                else 1
            )

        elif args.init is not None:
            return (
                0 if commands.workspace_manager.initialize_workspace(args.init) else 1
            )

        elif args.start:
            return 0 if commands.service_manager.start_services(args.start) else 1

        elif args.stop:
            return 0 if commands.service_manager.stop_services(args.stop) else 1

        elif args.restart:
            return 0 if commands.service_manager.restart_services(args.restart) else 1

        elif args.status:
            status = commands.service_manager.get_status(args.status)
            for component, state in status.items():
                print(f"{component}: {state}")
            return 0 if all(v == "healthy" for v in status.values()) else 1

        elif args.health:
            health = commands.unified_installer.health_check(args.health)
            for component, is_healthy in health.items():
                print(f"{component}: {'✅ healthy' if is_healthy else '❌ unhealthy'}")
            return 0 if all(health.values()) else 1

        elif args.logs is not None:
            component = args.logs[0] if args.logs else "all"
            lines = int(args.logs[1]) if len(args.logs) > 1 else 50
            return 0 if commands.service_manager.show_logs(component, lines) else 1

        elif args.uninstall:
            return 0 if commands.service_manager.uninstall(args.uninstall) else 1

        # No command - show help
        else:
            parser.print_help()
            return 0

    except KeyboardInterrupt:
        print("\nCancelled", file=sys.stderr)
        return 130

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
