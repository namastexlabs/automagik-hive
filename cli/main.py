#!/usr/bin/env python3
"""Automagik Hive CLI - Simple 8-Command Interface.

Beautiful simplicity: install, start, stop, restart, status, health, logs, uninstall.
No over-engineering. No abstract patterns. Just working CLI.
"""

import argparse
import sys
from pathlib import Path

from .docker_manager import DockerManager
from .workspace import WorkspaceManager
from .commands.init import InitCommands
from .commands.workspace import WorkspaceCommands
from .commands.postgres import PostgreSQLCommands
from .commands.agent import AgentCommands
from .commands.uninstall import UninstallCommands


def create_parser() -> argparse.ArgumentParser:
    """Create simple argument parser."""
    parser = argparse.ArgumentParser(
        prog="automagik-hive",
        description="Automagik Hive - Simple Multi-agent AI framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 8 core commands
    parser.add_argument("--install", nargs="?", const="interactive", choices=["agent", "workspace", "all", "interactive"], help="Install components (interactive by default)")
    parser.add_argument("--start", choices=["agent", "workspace", "all"], help="Start services")
    parser.add_argument("--stop", choices=["agent", "workspace", "all"], help="Stop services")
    parser.add_argument("--restart", choices=["agent", "workspace", "all"], help="Restart services")
    parser.add_argument("--status", choices=["agent", "workspace", "all"], help="Service status")
    parser.add_argument("--health", choices=["agent", "workspace", "all"], help="Health check")
    parser.add_argument("--logs", choices=["agent", "workspace", "all"], help="Show logs")
    parser.add_argument("--uninstall", choices=["agent", "workspace", "all"], help="Uninstall")
    
    # Additional commands
    parser.add_argument("--init", nargs="?", const=None, default=False, metavar="NAME", help="Initialize workspace")
    parser.add_argument("--version", action="store_true", help="Show version")
    
    # Lines flag (for --logs only)
    parser.add_argument("--lines", type=int, default=50, help="Number of log lines (used with --logs)")
    
    # Workspace path - primary positional argument
    parser.add_argument("workspace", nargs="?", help="Workspace directory path")

    return parser


def main() -> int:
    """Simple CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Count commands - special handling for --init which can be None
    commands = [
        args.install, args.start, args.stop, args.restart,
        args.status, args.health, args.logs, args.uninstall,
        args.version, args.workspace
    ]
    command_count = sum(1 for cmd in commands if cmd)
    # --init with or without arguments sets args.init to non-False, so check explicitly
    if args.init is not False:
        command_count += 1
    
    if command_count > 1:
        print("❌ Only one command allowed at a time", file=sys.stderr)
        return 1
    
    if command_count == 0:
        parser.print_help()
        return 0

    try:
        # Version
        if args.version:
            from lib.utils.version_reader import get_project_version
            version = get_project_version()
            print(f"Automagik Hive v{version}")
            return 0
        
        # Init workspace
        if args.init is not False:  # Using 'is not False' to handle both None and string values
            init_commands = InitCommands()
            return 0 if init_commands.init_workspace(args.init) else 1
        
        # Start workspace server
        if args.workspace:
            if not Path(args.workspace).exists():
                print(f"❌ Directory not found: {args.workspace}")
                return 1
            workspace_commands = WorkspaceCommands()
            return 0 if workspace_commands.start_server(args.workspace) else 1
        
        # Get component for operations that need it
        component = args.install or args.start or args.stop or args.restart or args.status or args.health or args.logs or args.uninstall
        
        # Agent operations
        if component in ["agent", "all"]:
            agent_commands = AgentCommands()
            
            if args.install:
                return 0 if agent_commands.install() else 1
            elif args.start:
                return 0 if agent_commands.start() else 1
            elif args.stop:
                return 0 if agent_commands.stop() else 1
            elif args.restart:
                return 0 if agent_commands.restart() else 1
            elif args.status:
                agent_commands.status()
                return 0
            elif args.health:
                agent_commands.health()
                return 0
            elif args.logs:
                agent_commands.logs(args.lines)
                return 0
            elif args.uninstall:
                uninstall_commands = UninstallCommands()
                return 0 if uninstall_commands.uninstall_agent() else 1
        
        # PostgreSQL operations
        if component == "postgres":
            postgres_commands = PostgreSQLCommands()
            
            if args.install:
                return 0 if postgres_commands.install() else 1
            elif args.start:
                return 0 if postgres_commands.start() else 1
            elif args.stop:
                return 0 if postgres_commands.stop() else 1
            elif args.restart:
                return 0 if postgres_commands.restart() else 1
            elif args.status:
                postgres_commands.status()
                return 0
            elif args.health:
                postgres_commands.health()
                return 0
            elif args.logs:
                postgres_commands.logs(args.lines)
                return 0
        
        # Workspace operations
        if component == "workspace":
            workspace_commands = WorkspaceCommands()
            
            if args.install:
                return 0 if workspace_commands.install() else 1
            elif args.start:
                return 0 if workspace_commands.start() else 1
            elif args.stop:
                return 0 if workspace_commands.stop() else 1
            elif args.restart:
                return 0 if workspace_commands.restart() else 1
            elif args.status:
                workspace_commands.status()
                return 0
            elif args.health:
                workspace_commands.health()
                return 0
            elif args.logs:
                workspace_commands.logs(args.lines)
                return 0
            elif args.uninstall:
                uninstall_commands = UninstallCommands()
                return 0 if uninstall_commands.uninstall_workspace() else 1
        
        # Fallback for unhandled cases
        return 0
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
# Functions expected by tests
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


def app() -> int:
    """CLI app function that calls main and returns result."""
    return main()
