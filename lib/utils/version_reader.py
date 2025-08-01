"""
Dynamic version reader for Automagik Hive.

Provides a single source of truth for version information across CLI and API components.
Uses pyproject.toml as the authoritative source with multiple fallback strategies.
"""

import re
from pathlib import Path


def get_project_version() -> str:
    """
    Get the current project version from multiple sources.

    Priority order:
    1. importlib.metadata (when package is installed)
    2. pyproject.toml file parsing
    3. Fallback version

    Returns:
        Version string (e.g., "0.1.2", "0.1.0-test1")
    """
    # Try importlib.metadata first (works when package is installed)
    try:
        import importlib.metadata

        return importlib.metadata.version("automagik-hive")
    except Exception:
        pass

    # Fall back to parsing pyproject.toml
    try:
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"

        if pyproject_path.exists():
            content = pyproject_path.read_text(encoding="utf-8")

            # Look for version = "x.y.z" pattern
            version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if version_match:
                return version_match.group(1)
    except Exception:
        pass

    # Ultimate fallback
    return "0.1.0-dev"


def get_cli_version_string() -> str:
    """
    Get formatted CLI version string for argparse.

    Returns:
        Formatted version string for CLI display
    """
    version = get_project_version()
    return f"automagik-hive CLI v{version} (UVX System)"


def get_api_version() -> str:
    """
    Get API version for FastAPI app configuration.

    Returns:
        Version string for API
    """
    return get_project_version()


def get_version_info() -> dict[str, str]:
    """
    Get comprehensive version information for debugging.

    Returns:
        Dictionary with version details
    """
    version = get_project_version()

    return {
        "version": version,
        "cli_version": get_cli_version_string(),
        "api_version": get_api_version(),
        "source": _get_version_source(),
    }


def _get_version_source() -> str:
    """
    Determine which method was used to get the version.

    Returns:
        Source description
    """
    # Try importlib.metadata
    try:
        import importlib.metadata

        importlib.metadata.version("automagik-hive")
        return "importlib.metadata"
    except Exception:
        pass

    # Try pyproject.toml
    try:
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"

        if pyproject_path.exists():
            content = pyproject_path.read_text(encoding="utf-8")
            if re.search(r'version\s*=\s*["\']([^"\']+)["\']', content):
                return "pyproject.toml"
    except Exception:
        pass

    return "fallback"


if __name__ == "__main__":
    # CLI for testing version detection
    pass
