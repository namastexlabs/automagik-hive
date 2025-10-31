"""Extract dependencies from main pyproject.toml for scaffolded projects.

This module provides utilities to dynamically extract dependency information
from the main Automagik Hive pyproject.toml file, ensuring scaffolded projects
always use the correct versions without hardcoding.
"""

import tomllib
from pathlib import Path


def get_hive_dependencies() -> dict[str, list[str]]:
    """Extract dependencies from main Hive pyproject.toml.

    Returns:
        Dict with 'core', 'api', 'database' dependency groups

    Raises:
        FileNotFoundError: If pyproject.toml cannot be found
        KeyError: If required dependency sections are missing
    """
    # Find main pyproject.toml (hive package root)
    hive_root = Path(__file__).parent.parent.parent
    pyproject_path = hive_root / "pyproject.toml"

    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    all_deps = pyproject["project"]["dependencies"]

    # Core dependencies (minimal for agents)
    # These are essential for any Hive project to function
    core_packages = ["agno", "pydantic", "pyyaml", "python-dotenv", "typer", "rich"]
    core = [dep for dep in all_deps if any(pkg in dep.lower() for pkg in core_packages)]

    # API dependencies (for dev server)
    # Required for FastAPI-based development servers
    api_packages = ["fastapi", "uvicorn", "httpx"]
    api = [dep for dep in all_deps if any(pkg in dep.lower() for pkg in api_packages)]

    # Database dependencies (for storage/RAG)
    # Required for persistent storage and RAG capabilities
    database_packages = ["sqlalchemy", "psycopg", "pgvector", "aiosqlite", "greenlet"]
    database = [dep for dep in all_deps if any(pkg in dep.lower() for pkg in database_packages)]

    # AI Provider dependencies (optional but commonly needed)
    ai_packages = ["anthropic", "openai"]
    ai = [dep for dep in all_deps if any(pkg in dep.lower() for pkg in ai_packages)]

    # Utilities (logging, file watching, etc.)
    utility_packages = ["loguru", "watchdog", "pandas"]
    utilities = [dep for dep in all_deps if any(pkg in dep.lower() for pkg in utility_packages)]

    return {
        "core": core,
        "api": api,
        "database": database,
        "ai": ai,
        "utilities": utilities,
    }


def get_python_version() -> str:
    """Extract Python version requirement from main pyproject.toml.

    Returns:
        Python version string (e.g., ">=3.11")

    Raises:
        FileNotFoundError: If pyproject.toml cannot be found
        KeyError: If requires-python field is missing
    """
    hive_root = Path(__file__).parent.parent.parent
    pyproject_path = hive_root / "pyproject.toml"

    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    requires_python: str = pyproject["project"]["requires-python"]
    return requires_python


def format_dependencies_for_toml(dependencies: list[str], indent: int = 4) -> str:
    """Format dependency list for TOML output.

    Args:
        dependencies: List of dependency strings (e.g., ["agno>=2.2.3"])
        indent: Number of spaces for indentation

    Returns:
        Formatted string suitable for TOML file
    """
    if not dependencies:
        return ""

    indent_str = " " * indent
    formatted_deps = [f'{indent_str}"{dep}",' for dep in dependencies]
    return "\n".join(formatted_deps)
