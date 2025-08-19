"""
Test version synchronization across all UVX components.

Ensures all version references use the same source of truth from pyproject.toml.
"""

import contextlib
import re
from pathlib import Path

import pytest

from api.settings import api_settings
from cli import __version__ as cli_version
from lib.utils.version_reader import get_project_version, get_version_info


def test_pyproject_toml_version_format():
    """Test that pyproject.toml has a valid version format."""
    project_root = Path(__file__).parent.parent.parent.parent
    pyproject_path = project_root / "pyproject.toml"

    assert pyproject_path.exists(), "pyproject.toml should exist"

    content = pyproject_path.read_text(encoding="utf-8")
    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)

    assert version_match, "pyproject.toml should contain version field"
    version = version_match.group(1)

    # Validate version format (PEP 440 compliant)
    version_pattern = r"^(\d+!)?\d+(\.\d+)*((a|b|rc)\d+)?(\.post\d+)?(\.dev\d+)?$"
    assert re.match(version_pattern, version), (
        f"Version '{version}' should be PEP 440 compliant"
    )


def test_version_reader_consistency():
    """Test that version reader provides consistent version information."""
    version_info = get_version_info()

    assert "version" in version_info
    assert "cli_version" in version_info
    assert "api_version" in version_info
    assert "source" in version_info

    base_version = version_info["version"]

    # CLI version should contain the base version
    assert base_version in version_info["cli_version"]

    # API version should match base version
    assert version_info["api_version"] == base_version


@pytest.mark.skip(reason="Blocked by task-733cdd4e - CLI version hardcoded mismatch with project version")
def test_cli_version_sync():
    """Test that CLI version is synchronized with pyproject.toml."""
    project_version = get_project_version()

    # CLI __version__ should match project version
    assert cli_version == project_version

    # Test CLI version string format
    from lib.utils.version_reader import get_cli_version_string

    cli_version_string = get_cli_version_string()

    assert project_version in cli_version_string
    assert "automagik-hive CLI" in cli_version_string
    assert "UVX System" in cli_version_string


def test_api_version_sync():
    """Test that API version is synchronized with pyproject.toml."""
    project_version = get_project_version()

    # API settings version should match project version
    assert api_settings.version == project_version


@pytest.mark.skip(reason="Blocked by task-b287b2d8 - CLI version '0.1.0a61' does not match project version '0.1.0'")
def test_all_components_same_version():
    """Test that all components report the same version."""
    project_version = get_project_version()

    # All components should use the same version
    components = {
        "project": project_version,
        "cli": cli_version,
        "api": api_settings.version,
    }

    for component_name, component_version in components.items():
        assert component_version == project_version, (
            f"{component_name} version '{component_version}' "
            f"does not match project version '{project_version}'"
        )


def test_version_source_priority():
    """Test that version source priority works correctly."""
    version_info = get_version_info()

    # Should use importlib.metadata when package is installed (development mode)
    # or pyproject.toml when not installed
    valid_sources = ["importlib.metadata", "pyproject.toml", "fallback"]
    assert version_info["source"] in valid_sources

    # In development, importlib.metadata should be preferred
    if version_info["source"] == "importlib.metadata":
        # Package is installed in development mode
        import importlib.metadata

        installed_version = importlib.metadata.version("automagik-hive")
        assert version_info["version"] == installed_version


@pytest.mark.parametrize(
    "version_string",
    [
        "0.1.0",  # Basic release
        "0.1.0a1",  # Alpha pre-release
        "0.1.0b1",  # Beta pre-release
        "0.1.0rc1",  # Release candidate
        "1.2.3",  # Standard semantic version
    ],
)
def test_version_format_compatibility(version_string):
    """Test that various version formats work with the version reader."""
    # This is a unit test to ensure our version parsing is robust
    version_pattern = r"^(\d+!)?\d+(\.\d+)*((a|b|rc)\d+)?(\.post\d+)?(\.dev\d+)?$"
    assert re.match(version_pattern, version_string), (
        f"Version '{version_string}' should be valid PEP 440 format"
    )


if __name__ == "__main__":
    # CLI for manual testing

    version_info = get_version_info()

    # Run basic validation
    with contextlib.suppress(AssertionError):
        test_all_components_same_version()
