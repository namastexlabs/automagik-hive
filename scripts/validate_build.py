#!/usr/bin/env python3
"""
Build Validation Script for Automagik Hive

This script validates the build configuration and package contents
without requiring PyPI tokens.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"🚀 Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout.strip())
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        sys.exit(1)

def validate_pyproject() -> str:
    """Validate pyproject.toml configuration."""
    print("🔍 Validating pyproject.toml...")
    
    with open("pyproject.toml", "r") as f:
        content = f.read()
    
    # Check entry points
    if 'automagik-hive = "cli.main:main"' not in content:
        print("❌ CLI entry point not correctly configured")
        print("Expected: automagik-hive = \"cli.main:main\"")
        sys.exit(1)
    
    print("✅ Entry point correctly configured")
    
    # Check packages
    if '"cli"' not in content:
        print("❌ CLI package not included in hatchling config")
        sys.exit(1)
    
    print("✅ CLI package included in build config")
    
    # Get version
    for line in content.split("\n"):
        if line.startswith("version ="):
            version = line.split("=")[1].strip().strip('"')
            print(f"📦 Version: {version}")
            return version
    
    print("❌ Version not found")
    sys.exit(1)

def build_and_validate() -> None:
    """Build package and validate contents."""
    print("🏗️ Building package...")
    
    # Clean and build
    run_command(["rm", "-rf", "dist"])
    run_command(["uv", "build"])
    
    # Check artifacts exist
    dist_path = Path("dist")
    wheel_files = list(dist_path.glob("*.whl"))
    tar_files = list(dist_path.glob("*.tar.gz"))
    
    if not wheel_files:
        print("❌ No wheel files found")
        sys.exit(1)
    
    if not tar_files:
        print("❌ No source distribution found")  
        sys.exit(1)
    
    print(f"✅ Found {len(wheel_files)} wheel(s) and {len(tar_files)} source distribution(s)")
    
    # Validate wheel contents
    wheel_file = wheel_files[0]
    print(f"🔍 Validating wheel: {wheel_file.name}")
    
    result = run_command([
        "python", "-m", "zipfile", "-l", str(wheel_file)
    ])
    
    wheel_contents = result.stdout
    
    # Check CLI module
    if "cli/" not in wheel_contents:
        print("❌ CLI module not found in wheel")
        sys.exit(1)
    
    print("✅ CLI module included")
    
    # Check entry points
    if "entry_points.txt" not in wheel_contents:
        print("❌ Entry points file not found")
        sys.exit(1)
    
    print("✅ Entry points file included")
    
    # Extract and check entry points content
    run_command([
        "python", "-m", "zipfile", "-e", str(wheel_file), "/tmp/wheel_check"
    ])
    
    entry_points_file = Path("/tmp/wheel_check") / f"{wheel_file.stem}.dist-info" / "entry_points.txt"
    
    if entry_points_file.exists():
        with open(entry_points_file, "r") as f:
            entry_content = f.read()
            print(f"📋 Entry points content:\n{entry_content}")
            
            if "automagik-hive = cli.main:main" not in entry_content:
                print("❌ Entry point not correctly configured in wheel")
                sys.exit(1)
            
            print("✅ Entry point correctly configured in wheel")
    else:
        print("❌ Could not read entry points file")
        sys.exit(1)

def main():
    """Main validation workflow."""
    print("🧞 Automagik Hive - Build Validation")
    print("=" * 50)
    
    version = validate_pyproject()
    build_and_validate()
    
    print("\n🎉 Build validation complete!")
    print(f"📦 Version {version} is ready for publishing")
    print("\n📋 Next steps:")
    print("1. Test publish: python scripts/publish.py --test")
    print("2. Production publish: python scripts/publish.py --prod")
    print("3. Test install: uvx automagik-hive --help")

if __name__ == "__main__":
    main()