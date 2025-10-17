"""Simple CLI utilities."""

import subprocess


def run_command(cmd: list, capture_output: bool = False, cwd: str | None = None) -> str | None:
    """Run shell command with error handling."""
    try:
        if capture_output:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=cwd)
            return result.stdout.strip()
        subprocess.run(cmd, check=True, cwd=cwd)
        return None
    except subprocess.CalledProcessError as e:
        if capture_output:
            if e.stderr:
                pass
        return None
    except subprocess.TimeoutExpired:
        return None
    except PermissionError:
        return None
    except FileNotFoundError:
        return None


def check_docker_available() -> bool:
    """Check if Docker is available and running."""
    if not run_command(["docker", "--version"], capture_output=True):
        return False
    
    if not run_command(["docker", "ps"], capture_output=True):
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
    
    return f"{name:23} {status_text}"


def confirm_action(message: str, default: bool = False) -> bool:
    """Ask user for confirmation."""
    suffix = " (Y/n)" if default else " (y/N)"
    try:
        response = input(f"{message}{suffix}: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        # Handle Ctrl+C and Ctrl+D gracefully - return default value
        return default
    
    if not response:
        return default
    
    if response in ["y", "yes"]:
        return True
    if response in ["n", "no"]:
        return False
    # Invalid response - return default
    return default
