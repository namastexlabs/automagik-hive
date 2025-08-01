#!/usr/bin/env python3
"""Simple build test to validate PyPI publishing readiness."""

import subprocess
import sys
from pathlib import Path


def main():
    # Clean and build
    subprocess.run(["rm", "-rf", "dist"], check=True)

    subprocess.run(["uv", "build"], check=True)

    # Check files exist
    wheel_files = list(Path("dist").glob("*.whl"))
    list(Path("dist").glob("*.tar.gz"))

    # Check wheel contents
    if wheel_files:
        wheel_file = wheel_files[0]
        result = subprocess.run(
            ["uv", "run", "python", "-m", "zipfile", "-l", str(wheel_file)],
            capture_output=True,
            text=True,
            check=True,
        )

        if "cli/" in result.stdout and "entry_points.txt" in result.stdout:
            pass
        else:
            return False

        # Check entry points content
        subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "zipfile",
                "-e",
                str(wheel_file),
                "/tmp/wheel_check",
            ],
            check=True,
        )

        entry_file = (
            Path("/tmp/wheel_check")
            / f"{wheel_file.stem}.dist-info"
            / "entry_points.txt"
        )
        if entry_file.exists():
            content = entry_file.read_text()
            if "automagik-hive = cli.main:main" in content:
                pass
            else:
                return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
