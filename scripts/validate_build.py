#!/usr/bin/env python3
"""Build Validation Script for Automagik Hive.

This script validates the build configuration and package contents
without requiring PyPI tokens.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            pass
        return result
    except subprocess.CalledProcessError as e:
        if e.stderr:
            pass
        sys.exit(1)


def validate_pyproject() -> str:
    """Validate pyproject.toml configuration."""
    with open("pyproject.toml") as f:
        content = f.read()

    # Check entry points
    if 'automagik-hive = "cli.main:main"' not in content:
        sys.exit(1)

    # Check packages
    if '"cli"' not in content:
        sys.exit(1)

    # Get version
    for line in content.split("\n"):
        if line.startswith("version ="):
            return line.split("=")[1].strip().strip('"')

    sys.exit(1)


def build_and_validate() -> None:
    """Build package and validate contents."""
    # Clean and build
    run_command(["rm", "-rf", "dist"])
    run_command(["uv", "build"])

    # Check artifacts exist
    dist_path = Path("dist")
    wheel_files = list(dist_path.glob("*.whl"))
    tar_files = list(dist_path.glob("*.tar.gz"))

    if not wheel_files:
        sys.exit(1)

    if not tar_files:
        sys.exit(1)

    # Validate wheel contents
    wheel_file = wheel_files[0]

    result = run_command(
        ["uv", "run", "python", "-m", "zipfile", "-l", str(wheel_file)]
    )

    wheel_contents = result.stdout

    # Check CLI module
    if "cli/" not in wheel_contents:
        sys.exit(1)

    # Check entry points
    if "entry_points.txt" not in wheel_contents:
        sys.exit(1)

    # Extract and check entry points content
    run_command(
        [
            "uv",
            "run",
            "python",
            "-m",
            "zipfile",
            "-e",
            str(wheel_file),
            "/tmp/wheel_check",
        ]
    )

    entry_points_file = (
        Path("/tmp/wheel_check") / f"{wheel_file.stem}.dist-info" / "entry_points.txt"
    )

    if entry_points_file.exists():
        with open(entry_points_file) as f:
            entry_content = f.read()

            if "automagik-hive = cli.main:main" not in entry_content:
                sys.exit(1)

    else:
        sys.exit(1)


def main():
    """Main validation workflow."""
    validate_pyproject()
    build_and_validate()


if __name__ == "__main__":
    main()
