"""Environment validation and system checks for UVX Automagik Hive.

Provides comprehensive validation of system requirements:
- Python 3.12+ compatibility
- UVX environment detection
- Docker installation and daemon status
- Port availability checks
- PostgreSQL image pre-pulling
- Cross-platform installation guidance
"""

import platform
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class EnvironmentCheck:
    """Result of an environment validation check."""

    name: str
    passed: bool
    message: str
    guidance: str | None = None
    critical: bool = True


@dataclass
class EnvironmentValidation:
    """Complete environment validation results."""

    checks: list[EnvironmentCheck]
    overall_passed: bool
    summary: str

    @property
    def critical_failures(self) -> list[EnvironmentCheck]:
        """Get list of critical failures that block execution."""
        return [check for check in self.checks if not check.passed and check.critical]

    @property
    def warnings(self) -> list[EnvironmentCheck]:
        """Get list of non-critical warnings."""
        return [
            check for check in self.checks if not check.passed and not check.critical
        ]


class EnvironmentValidator:
    """Comprehensive environment validation for UVX Automagik Hive."""

    def __init__(self):
        self.platform_system = platform.system().lower()
        self.checks: list[EnvironmentCheck] = []

    def validate_all(
        self, required_ports: list[int] | None = None
    ) -> EnvironmentValidation:
        """Run complete environment validation.

        Args:
            required_ports: List of ports to check for availability

        Returns:
            EnvironmentValidation with all check results
        """
        self.checks = []

        # Core system checks
        self.checks.append(self._check_python_version())
        self.checks.append(self._check_uvx_environment())

        # Docker ecosystem checks
        docker_check = self._check_docker_installation()
        self.checks.append(docker_check)

        if docker_check.passed:
            self.checks.append(self._check_docker_daemon())
            self.checks.append(self._check_postgresql_image())

        # Port availability checks
        if required_ports:
            for port in required_ports:
                self.checks.append(self._check_port_availability(port))

        # Determine overall status
        critical_failures = [c for c in self.checks if not c.passed and c.critical]
        overall_passed = len(critical_failures) == 0

        # Generate summary
        if overall_passed:
            summary = "✅ Environment validation passed - ready for UVX Automagik Hive"
        else:
            failure_count = len(critical_failures)
            summary = f"❌ {failure_count} critical issue(s) found - see guidance below"

        return EnvironmentValidation(
            checks=self.checks, overall_passed=overall_passed, summary=summary
        )

    def _check_python_version(self) -> EnvironmentCheck:
        """Validate Python 3.12+ requirement for UVX compatibility."""
        try:
            version = sys.version_info
            if version >= (3, 12):
                return EnvironmentCheck(
                    name="Python Version",
                    passed=True,
                    message=f"Python {version.major}.{version.minor}.{version.micro} ✓",
                )
            return EnvironmentCheck(
                name="Python Version",
                passed=False,
                message=f"Python {version.major}.{version.minor}.{version.micro} (requires 3.12+)",
                guidance=self._get_python_upgrade_guidance(),
                critical=True,
            )
        except Exception as e:
            return EnvironmentCheck(
                name="Python Version",
                passed=False,
                message=f"Failed to check Python version: {e}",
                critical=True,
            )

    def _check_uvx_environment(self) -> EnvironmentCheck:
        """Detect UVX execution context and compatibility."""
        # Check for UVX-specific environment indicators
        uvx_indicators = ["UVX_PROJECT", "UV_PROJECT_ENVIRONMENT", "VIRTUAL_ENV"]

        uvx_detected = any(indicator in os.environ for indicator in uvx_indicators)

        # Check if uvx command is available
        uvx_available = shutil.which("uvx") is not None

        if uvx_available:
            message = "UVX environment detected and available ✓"
            guidance = None
        elif uvx_detected:
            message = "UVX environment detected but command not available"
            guidance = "Install uv: pip install uv"
        else:
            message = "UVX environment not detected (may be direct Python execution)"
            guidance = "Consider using: uvx automagik-hive for better experience"

        return EnvironmentCheck(
            name="UVX Environment",
            passed=uvx_available or uvx_detected,
            message=message,
            guidance=guidance,
            critical=False,  # Non-critical, can run without UVX
        )

    def _check_docker_installation(self) -> EnvironmentCheck:
        """Check Docker installation with platform-specific guidance."""
        if not shutil.which("docker"):
            return EnvironmentCheck(
                name="Docker Installation",
                passed=False,
                message="Docker not found",
                guidance=self._get_docker_install_guidance(),
                critical=True,
            )

        return EnvironmentCheck(
            name="Docker Installation",
            passed=True,
            message="Docker command available ✓",
        )

    def _check_docker_daemon(self) -> EnvironmentCheck:
        """Check if Docker daemon is running and accessible."""
        try:
            subprocess.run(
                ["docker", "info"], capture_output=True, check=True, timeout=10
            )
            return EnvironmentCheck(
                name="Docker Daemon", passed=True, message="Docker daemon running ✓"
            )
        except subprocess.CalledProcessError:
            return EnvironmentCheck(
                name="Docker Daemon",
                passed=False,
                message="Docker daemon not running",
                guidance=self._get_docker_start_guidance(),
                critical=True,
            )
        except subprocess.TimeoutExpired:
            return EnvironmentCheck(
                name="Docker Daemon",
                passed=False,
                message="Docker daemon not responding (timeout)",
                guidance="Check Docker service status and restart if needed",
                critical=True,
            )
        except Exception as e:
            return EnvironmentCheck(
                name="Docker Daemon",
                passed=False,
                message=f"Docker daemon check failed: {e}",
                critical=True,
            )

    def _check_postgresql_image(self) -> EnvironmentCheck:
        """Check if PostgreSQL image is available and pre-pull if needed."""
        image_name = "agnohq/pgvector:16"

        try:
            # Check if image exists locally
            result = subprocess.run(
                ["docker", "images", "-q", image_name],
                capture_output=True,
                check=True,
                timeout=5,
            )

            if result.stdout.strip():
                return EnvironmentCheck(
                    name="PostgreSQL Image",
                    passed=True,
                    message=f"{image_name} available locally ✓",
                )
            # Attempt to pull image
            try:
                subprocess.run(
                    ["docker", "pull", image_name],
                    capture_output=True,
                    check=True,
                    timeout=120,  # 2 minutes for image pull
                )
                return EnvironmentCheck(
                    name="PostgreSQL Image",
                    passed=True,
                    message=f"{image_name} pulled successfully ✓",
                )
            except subprocess.TimeoutExpired:
                return EnvironmentCheck(
                    name="PostgreSQL Image",
                    passed=False,
                    message=f"Timeout pulling {image_name}",
                    guidance="Check internet connection and Docker Hub access",
                    critical=False,
                )
            except subprocess.CalledProcessError:
                return EnvironmentCheck(
                    name="PostgreSQL Image",
                    passed=False,
                    message=f"Failed to pull {image_name}",
                    guidance="Image will be pulled on first use",
                    critical=False,
                )

        except Exception as e:
            return EnvironmentCheck(
                name="PostgreSQL Image",
                passed=False,
                message=f"Image check failed: {e}",
                guidance="Image will be pulled on first use",
                critical=False,
            )

    def _check_port_availability(self, port: int) -> EnvironmentCheck:
        """Check if a specific port is available for binding."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("localhost", port))
                return EnvironmentCheck(
                    name=f"Port {port}", passed=True, message=f"Port {port} available ✓"
                )
        except OSError:
            return EnvironmentCheck(
                name=f"Port {port}",
                passed=False,
                message=f"Port {port} already in use",
                guidance=f"Stop service using port {port} or choose different port",
                critical=True,
            )

    def _get_python_upgrade_guidance(self) -> str:
        """Get platform-specific Python upgrade guidance."""
        if self.platform_system == "linux":
            return (
                "Ubuntu/Debian: sudo apt update && sudo apt install python3.12\n"
                "RHEL/CentOS: sudo dnf install python3.12\n"
                "Or use pyenv: pyenv install 3.12 && pyenv global 3.12"
            )
        if self.platform_system == "darwin":
            return (
                "macOS: brew install python@3.12\n"
                "Or download from: https://www.python.org/downloads/"
            )
        if self.platform_system == "windows":
            return (
                "Windows: Download Python 3.12+ from https://www.python.org/downloads/\n"
                "Or use winget: winget install Python.Python.3.12"
            )
        return "Visit https://www.python.org/downloads/ for Python 3.12+"

    def _get_docker_install_guidance(self) -> str:
        """Get platform-specific Docker installation guidance."""
        if self.platform_system == "linux":
            return (
                "Linux: curl -fsSL https://get.docker.com | sh\n"
                "Ubuntu/Debian: sudo apt install docker.io\n"
                "RHEL/CentOS: sudo dnf install docker\n"
                "Don't forget: sudo usermod -aG docker $USER (then logout/login)"
            )
        if self.platform_system == "darwin":
            return (
                "macOS: Download Docker Desktop from https://docker.com/products/docker-desktop\n"
                "Or use Homebrew: brew install --cask docker"
            )
        if self.platform_system == "windows":
            return (
                "Windows: Download Docker Desktop from https://docker.com/products/docker-desktop\n"
                "Requires WSL2 for optimal performance"
            )
        return "Visit https://docs.docker.com/get-docker/ for installation instructions"

    def _get_docker_start_guidance(self) -> str:
        """Get platform-specific Docker daemon start guidance."""
        if self.platform_system == "linux":
            return (
                "Start Docker service:\n"
                "systemd: sudo systemctl start docker\n"
                "service: sudo service docker start\n"
                "Enable on boot: sudo systemctl enable docker"
            )
        if self.platform_system == "darwin":
            return "Start Docker Desktop application from Applications folder"
        if self.platform_system == "windows":
            return "Start Docker Desktop from Start menu or desktop shortcut"
        return "Start Docker service for your system"


# Convenience functions for common validation scenarios
def validate_workspace_environment(
    workspace_ports: list[int] | None = None,
) -> EnvironmentValidation:
    """Validate environment for workspace operations."""
    if workspace_ports is None:
        workspace_ports = [8886, 5532]  # Main workspace ports

    validator = EnvironmentValidator()
    return validator.validate_all(required_ports=workspace_ports)


def validate_full_environment() -> EnvironmentValidation:
    """Validate environment for full UVX system (all services)."""
    all_ports = [8886, 5532, 48886, 35532]  # All service ports
    validator = EnvironmentValidator()
    return validator.validate_all(required_ports=all_ports)


def print_validation_results(validation: EnvironmentValidation) -> None:
    """Print formatted validation results to console."""
    # Print individual check results
    for check in validation.checks:
        if check.guidance and not check.passed:
            pass

    # Print summary sections
    if validation.critical_failures:
        for check in validation.critical_failures:
            if check.guidance:
                pass

    if validation.warnings:
        for check in validation.warnings:
            if check.guidance:
                pass


# Import fix for os module
import os
