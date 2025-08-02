#!/usr/bin/env python3
"""Automagik Hive CLI - UVX Master Plan Implementation.

Simple 2-command UVX interface:
- uvx automagik-hive --init - Interactive workspace creation with Docker installation
- uvx automagik-hive ./my-workspace - Start existing workspace server

Interactive Docker installation, excellent DX, guided setup flow.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from cli.commands import LazyCommandLoader


def create_parser() -> argparse.ArgumentParser:
    """Create UVX-compliant argument parser with 2-command interface."""
    parser = argparse.ArgumentParser(
        prog="automagik-hive",
        description="Automagik Hive - Multi-agent AI framework (UVX Interface)",
        epilog="""
Examples:
  %(prog)s --init                     # Interactive workspace creation
  %(prog)s --init my-project          # Create workspace in specific directory
  %(prog)s ./my-workspace             # Start existing workspace server
  %(prog)s --help                     # Show this help
  %(prog)s --version                  # Show version information
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Primary UVX commands
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

    # Positional argument for workspace path
    parser.add_argument(
        "workspace",
        nargs="?",
        default=None,
        help="Path to workspace directory for server startup",
    )

    return parser


def validate_arguments(args: argparse.Namespace) -> tuple[bool, Optional[str]]:
    """Validate UVX argument structure."""
    # Count active commands
    commands = [
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
    print("Multi-agent AI framework with UVX interface")
    print("Documentation: https://github.com/namastex/automagik-hive")


def main() -> int:
    """UVX-compliant main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Validate arguments
    is_valid, error_msg = validate_arguments(args)
    if not is_valid:
        print(f"❌ Error: {error_msg}", file=sys.stderr)
        return 1

    try:
        # Route to command handlers - UVX interface

        # Version command
        if args.version:
            show_version()
            return 0

        # Interactive initialization
        if args.init is not None:
            commands = LazyCommandLoader()
            workspace_name = args.init if args.init else None
            success = commands.interactive_initializer.initialize_workspace(workspace_name)
            return 0 if success else 1

        # Workspace startup
        if args.workspace:
            commands = LazyCommandLoader()
            success = commands.workspace_manager.start_workspace_server(args.workspace)
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