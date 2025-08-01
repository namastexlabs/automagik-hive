#!/usr/bin/env python3
"""PyPI Publishing Script for Automagik Hive

This script handles the build and publishing process for PyPI with proper
token-based authentication and validation.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"🚀 Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return e


def check_pypi_token() -> bool:
    """Check if PYPI_TOKEN is configured."""
    token = os.getenv("PYPI_TOKEN")
    if not token:
        print("❌ PYPI_TOKEN not found in environment")
        print("💡 Add PYPI_TOKEN to your .env file")
        return False

    if not token.startswith("pypi-"):
        print("❌ Invalid PYPI_TOKEN format (should start with 'pypi-')")
        return False

    print("✅ PYPI_TOKEN configured")
    return True


def validate_version() -> str:
    """Get and validate the current version."""
    # Read version from pyproject.toml
    try:
        with open("pyproject.toml") as f:
            content = f.read()
            for line in content.split("\n"):
                if line.startswith("version ="):
                    version = line.split("=")[1].strip().strip('"')
                    print(f"📦 Version: {version}")
                    return version
    except Exception as e:
        print(f"❌ Could not read version: {e}")
        sys.exit(1)

    print("❌ Version not found in pyproject.toml")
    sys.exit(1)


def clean_dist() -> None:
    """Clean the dist directory."""
    print("🧹 Cleaning dist directory...")
    run_command(["rm", "-rf", "dist"])


def build_package() -> None:
    """Build the package."""
    print("🏗️ Building package...")
    run_command(["uv", "build"])


def validate_build() -> None:
    """Validate the built package."""
    print("🔍 Validating build artifacts...")

    dist_path = Path("dist")
    if not dist_path.exists():
        print("❌ dist directory not found")
        sys.exit(1)

    wheel_files = list(dist_path.glob("*.whl"))
    tar_files = list(dist_path.glob("*.tar.gz"))

    if not wheel_files:
        print("❌ No wheel files found")
        sys.exit(1)

    if not tar_files:
        print("❌ No source distribution found")
        sys.exit(1)

    print(
        f"✅ Found {len(wheel_files)} wheel(s) and {len(tar_files)} source distribution(s)"
    )

    # Check wheel contents for CLI module
    wheel_file = wheel_files[0]
    result = run_command(
        ["uv", "run", "python", "-m", "zipfile", "-l", str(wheel_file)], check=False
    )

    if "cli/" not in result.stdout:
        print("❌ CLI module not found in wheel")
        sys.exit(1)

    print("✅ CLI module included in wheel")

    # Check entry points
    if "entry_points.txt" not in result.stdout:
        print("❌ Entry points not found in wheel")
        sys.exit(1)

    print("✅ Entry points configured in wheel")


def publish_to_testpypi() -> None:
    """Publish to Test PyPI first."""
    print("🧪 Publishing to Test PyPI...")

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

    print("✅ Published to Test PyPI")


def publish_to_pypi() -> None:
    """Publish to production PyPI."""
    print("🚀 Publishing to PyPI...")

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

    print("✅ Published to PyPI")


def main():
    """Main publishing workflow."""
    print("🧞 Automagik Hive - PyPI Publishing")
    print("=" * 50)

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
        print("Usage:")
        print("  python scripts/publish.py --test   # Publish to Test PyPI")
        print("  python scripts/publish.py --prod   # Publish to Production PyPI")
        sys.exit(1)

    confirm = input(f"📦 Publish version {version} to {target}? (y/N): ")
    if confirm.lower() != "y":
        print("❌ Publishing cancelled")
        sys.exit(0)

    # Build process
    clean_dist()
    build_package()
    validate_build()

    # Publish
    try:
        publisher()
        print(f"🎉 Successfully published {version} to {target}!")

        if env_arg == "--test":
            print("\n💡 Test installation with:")
            print("   uvx --index-url https://test.pypi.org/simple/ automagik-hive")
        else:
            print("\n💡 Install with:")
            print("   uvx automagik-hive")

    except Exception as e:
        print(f"❌ Publishing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
