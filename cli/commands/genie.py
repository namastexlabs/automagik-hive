"""Minimal Genie Commands Implementation - GREEN PHASE.

Properly tested implementation following TDD principles.
"""

import subprocess
import sys
from pathlib import Path
from typing import List


class GenieCommands:
    """Minimal genie commands implementation."""
    
    def launch_claude(self, extra_args: List[str] = None) -> bool:
        """Launch claude with AGENTS.md as system prompt."""
        try:
            # Find AGENTS.md file
            agents_md_path = Path.cwd() / "AGENTS.md"
            if not agents_md_path.exists():
                # Try parent directories
                for parent in Path.cwd().parents:
                    candidate = parent / "AGENTS.md"
                    if candidate.exists():
                        agents_md_path = candidate
                        break
                else:
                    print("❌ AGENTS.md not found in current directory or parent directories", file=sys.stderr)
                    return False
            
            # Read AGENTS.md content
            try:
                with open(agents_md_path, 'r', encoding='utf-8') as f:
                    agents_content = f.read()
            except Exception as e:
                print(f"❌ Failed to read AGENTS.md: {e}", file=sys.stderr)
                return False
            
            # Build claude command
            claude_cmd = [
                "claude",
                "--append-system-prompt", agents_content,
                "--mcp-config", ".mcp.json",
                "--model", "sonnet",
                "--dangerously-skip-permissions"
            ]
            
            # Add any extra arguments passed by user
            if extra_args:
                claude_cmd.extend(extra_args)
            
            print(f"🤖 Launching claude with AGENTS personality...")
            print(f"📖 Using AGENTS.md from: {agents_md_path}")
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