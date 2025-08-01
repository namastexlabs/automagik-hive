#!/usr/bin/env python3
"""PyPI Publishing Script for Automagik Hive.

This script handles the build and publishing process for PyPI with proper
token-based authentication and validation.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        if result.stdout:
            pass
        return result
    except subprocess.CalledProcessError as e:
        if e.stderr:
            pass
        if check:
            sys.exit(1)
        return e


def check_pypi_token() -> bool:
    """Check if PYPI_TOKEN is configured."""
    token = os.getenv("PYPI_TOKEN")
    if not token:
        return False

    return token.startswith("pypi-")


def validate_version() -> str:
    """Get and validate the current version."""
    # Read version from pyproject.toml
    try:
        with open("pyproject.toml") as f:
            content = f.read()
            for line in content.split("\n"):
                if line.startswith("version ="):
                    return line.split("=")[1].strip().strip('"')
    except Exception:
        sys.exit(1)

    sys.exit(1)


def clean_dist() -> None:
    """Clean the dist directory."""
    run_command(["rm", "-rf", "dist"])


def build_package() -> None:
    """Build the package."""
    run_command(["uv", "build"])


def validate_build() -> None:
    """Validate the built package."""
    dist_path = Path("dist")
    if not dist_path.exists():
        sys.exit(1)

    wheel_files = list(dist_path.glob("*.whl"))
    tar_files = list(dist_path.glob("*.tar.gz"))

    if not wheel_files:
        sys.exit(1)

    if not tar_files:
        sys.exit(1)

    # Check wheel contents for CLI module
    wheel_file = wheel_files[0]
    result = run_command(
        ["uv", "run", "python", "-m", "zipfile", "-l", str(wheel_file)], check=False
    )

    if "cli/" not in result.stdout:
        sys.exit(1)

    # Check entry points
    if "entry_points.txt" not in result.stdout:
        sys.exit(1)


def publish_to_testpypi() -> None:
    """Publish to Test PyPI first."""
    # Use uvx to run twine for publishing
    run_command(
        [
            "uvx",
            "twine",
            "upload",
            "--repository",
            "testpypi",
            "--username",
            "__token__",
            "--password",
            os.getenv("PYPI_TOKEN", ""),
            "dist/*",
        ]
    )


def publish_to_pypi() -> None:
    """Publish to production PyPI."""
    # Use uvx to run twine for publishing
    run_command(
        [
            "uvx",
            "twine",
            "upload",
            "--username",
            "__token__",
            "--password",
            os.getenv("PYPI_TOKEN", ""),
            "dist/*",
        ]
    )


def main():
    """Main publishing workflow."""
    # Check environment
    if not check_pypi_token():
        sys.exit(1)

    # Validate version
    version = validate_version()

    # Confirm publication
    env_arg = sys.argv[1] if len(sys.argv) > 1 else ""

    if env_arg == "--test":
        target = "Test PyPI"
        publisher = publish_to_testpypi
    elif env_arg == "--prod":
        target = "Production PyPI"
        publisher = publish_to_pypi
    else:
        sys.exit(1)

    confirm = input(f"📦 Publish version {version} to {target}? (y/N): ")
    if confirm.lower() != "y":
        sys.exit(0)

    # Build process
    clean_dist()
    build_package()
    validate_build()

    # Publish
    try:
        publisher()

        if env_arg == "--test":
            pass
        else:
            pass

    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
