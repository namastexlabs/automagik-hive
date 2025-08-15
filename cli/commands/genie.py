"""Genie Commands Implementation.

Real implementation connecting to GenieService for actual functionality.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional, List

from cli.core.genie_service import GenieService


class GenieCommands:
    """Genie commands implementation."""
    
    def __init__(self, workspace_path: Path | None = None):
        self.workspace_path = workspace_path or Path()
        self.genie_service = GenieService(self.workspace_path)
    
    def install(self, workspace: str = ".") -> bool:
        """Install and start genie services."""
        try:
            print(f"🧞 Installing and starting genie services in: {workspace}")
            # Install and then start services
            if not self.genie_service.install_genie_environment(workspace):
                return False
            # After installation, start the services
            return self.genie_service.serve_genie(workspace)
        except Exception:
            return False
    
    def start(self, workspace: str = ".") -> bool:
        """Start genie services."""
        try:
            print(f"🧞 Starting genie services in: {workspace}")
            result = self.genie_service.serve_genie(workspace)
            return bool(result)
        except Exception:
            return False
    
    
    def stop(self, workspace: str = ".") -> bool:
        """Stop genie services."""
        try:
            print(f"🛑 Stopping genie services in: {workspace}")
            return self.genie_service.stop_genie(workspace)
        except Exception:
            return False
    
    def restart(self, workspace: str = ".") -> bool:
        """Restart genie services (stop + start)."""
        try:
            print(f"🔄 Restarting genie services in: {workspace}")
            if not self.stop(workspace):
                return False
            return self.start(workspace)
        except Exception:
            return False
    
    def logs(self, workspace: str = ".", tail: int = 50) -> bool:
        """Show genie logs."""
        try:
            print(f"📋 Showing genie logs for: {workspace}")
            return self.genie_service.logs_genie(workspace, tail)
        except Exception:
            return False
    
    def status(self, workspace: str = ".") -> bool:
        """Check genie status."""
        try:
            print(f"🔍 Checking genie status in: {workspace}")
            return self.genie_service.status_genie(workspace)
        except Exception:
            return False
    
    def reset(self, workspace: str = ".") -> bool:
        """Reset genie environment (destroy all + reinstall + start)."""
        try:
            print(f"🔄 Resetting genie environment in: {workspace}")
            # Stop, uninstall, reinstall, start
            self.stop(workspace)  # Don't fail if already stopped
            if not self.genie_service.uninstall_genie_environment(workspace):
                return False
            return self.install(workspace)
        except Exception:
            return False
    
    def uninstall(self, workspace: str = ".") -> bool:
        """Uninstall genie environment (destroy all + remove - NO reinstall)."""
        try:
            print(f"🗑️ Uninstalling genie environment in: {workspace}")
            print("This will destroy all containers and data permanently...")
            # Stop and uninstall only - NO reinstall, NO restart
            self.stop(workspace)  # Don't fail if already stopped
            return self.genie_service.uninstall_genie_environment(workspace)
        except Exception:
            return False
    
    def launch_claude(self, extra_args: List[str] = None) -> bool:
        """Launch claude with GENIE.md as system prompt."""
        try:
            # Find GENIE.md file
            genie_md_path = Path.cwd() / "GENIE.md"
            if not genie_md_path.exists():
                # Try parent directories
                for parent in Path.cwd().parents:
                    candidate = parent / "GENIE.md"
                    if candidate.exists():
                        genie_md_path = candidate
                        break
                else:
                    print("❌ GENIE.md not found in current directory or parent directories", file=sys.stderr)
                    return False
            
            # Read GENIE.md content
            try:
                with open(genie_md_path, 'r', encoding='utf-8') as f:
                    genie_content = f.read()
            except Exception as e:
                print(f"❌ Failed to read GENIE.md: {e}", file=sys.stderr)
                return False
            
            # Build claude command
            claude_cmd = [
                "claude",
                "--append-system-prompt", genie_content,
                "--mcp-config", ".mcp.json",
                "--model", "sonnet",
                "--dangerously-skip-permissions"
            ]
            
            # Add any extra arguments passed by user
            if extra_args:
                claude_cmd.extend(extra_args)
            
            print(f"🧞 Launching claude with GENIE personality...")
            print(f"📖 Using GENIE.md from: {genie_md_path}")
            print(f"🚀 Command: {' '.join(claude_cmd)}")
            print()
            
            # Launch claude
            result = subprocess.run(claude_cmd)
            return result.returncode == 0
            
        except FileNotFoundError:
            print("❌ claude command not found. Please ensure claude is installed and in PATH", file=sys.stderr)
            return False
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
            return True  # Not really an error
        except Exception as e:
            print(f"❌ Failed to launch claude: {e}", file=sys.stderr)
            return False