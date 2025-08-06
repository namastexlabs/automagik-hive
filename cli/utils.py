"""Simple CLI utilities."""

import subprocess
import sys
from typing import Optional


def run_command(cmd: list, capture_output: bool = False, cwd: Optional[str] = None) -> Optional[str]:
    """Run shell command with error handling."""
    try:
        if capture_output:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=cwd)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, check=True, cwd=cwd)
            return None
    except subprocess.CalledProcessError as e:
        if capture_output:
            print(f"❌ Command failed: {' '.join(cmd)}")
            if e.stderr:
                print(f"Error: {e.stderr}")
        return None
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return None


def check_docker_available() -> bool:
    """Check if Docker is available and running."""
    if not run_command(["docker", "--version"], capture_output=True):
        print("❌ Docker not found. Please install Docker first.")
        return False
    
    if not run_command(["docker", "ps"], capture_output=True):
        print("❌ Docker daemon not running. Please start Docker.")
        return False
    
    return True


def format_status(name: str, status: str, details: str = "") -> str:
    """Format status line with consistent width."""
    status_icons = {
        "running": "🟢",
        "stopped": "🔴", 
        "missing": "❌",
        "healthy": "🟢",
        "unhealthy": "🟡"
    }
    
    icon = status_icons.get(status.lower(), "❓")
    status_text = f"{icon} {status.title()}"
    
    if details:
        status_text += f" - {details}"
    
    return f"{name:25} {status_text}"


def confirm_action(message: str, default: bool = False) -> bool:
    """Ask user for confirmation."""
    suffix = " (Y/n)" if default else " (y/N)"
    response = input(f"{message}{suffix}: ").strip().lower()
    
    if not response:
        return default
    
    return response in ['y', 'yes']