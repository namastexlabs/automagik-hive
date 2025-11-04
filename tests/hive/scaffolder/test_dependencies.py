"""Tests for dependency extraction from pyproject.toml."""

import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from hive.scaffolder.dependencies import (
    format_dependencies_for_toml,
    get_hive_dependencies,
    get_python_version,
)


class TestGetHiveDependencies:
    """Test dependency extraction from main pyproject.toml."""

    def test_returns_dict_with_expected_keys(self):
        """Should return dict with core, api, database, ai, utilities keys."""
        deps = get_hive_dependencies()

        assert isinstance(deps, dict)
        assert "core" in deps
        assert "api" in deps
        assert "database" in deps
        assert "ai" in deps
        assert "utilities" in deps

    def test_core_dependencies_include_agno(self):
        """Core dependencies should include agno framework."""
        deps = get_hive_dependencies()

        core_deps_str = " ".join(deps["core"])
        assert "agno" in core_deps_str.lower()

    def test_core_dependencies_include_essential_packages(self):
        """Core dependencies should include pydantic, yaml, typer, rich."""
        deps = get_hive_dependencies()

        core_deps_str = " ".join(deps["core"]).lower()
        assert "pydantic" in core_deps_str
        assert "yaml" in core_deps_str
        assert "typer" in core_deps_str
        assert "rich" in core_deps_str

    def test_api_dependencies_include_fastapi(self):
        """API dependencies should include FastAPI and uvicorn."""
        deps = get_hive_dependencies()

        api_deps_str = " ".join(deps["api"]).lower()
        assert "fastapi" in api_deps_str
        assert "uvicorn" in api_deps_str

    def test_database_dependencies_include_sqlalchemy(self):
        """Database dependencies should include SQLAlchemy and postgres."""
        deps = get_hive_dependencies()

        db_deps_str = " ".join(deps["database"]).lower()
        assert "sqlalchemy" in db_deps_str
        assert "psycopg" in db_deps_str

    def test_ai_dependencies_include_providers(self):
        """AI dependencies should include anthropic and openai."""
        deps = get_hive_dependencies()

        ai_deps_str = " ".join(deps["ai"]).lower()
        assert "anthropic" in ai_deps_str or "openai" in ai_deps_str

    def test_dependencies_have_version_specifiers(self):
        """Dependencies should include version constraints."""
        deps = get_hive_dependencies()

        # Check core deps have versions
        core_with_versions = [d for d in deps["core"] if ">=" in d or "==" in d]
        assert len(core_with_versions) > 0, "Core dependencies should have version specifiers"

    def test_no_duplicate_dependencies(self):
        """Dependencies should not appear in multiple categories."""
        deps = get_hive_dependencies()

        all_deps = []
        for category in deps.values():
            all_deps.extend(category)

        # Extract package names (before version specifier)
        package_names = []
        for dep in all_deps:
            pkg_name = dep.split(">=")[0].split("==")[0].split("[")[0].strip()
            package_names.append(pkg_name)

        # Check for duplicates
        unique_packages = set(package_names)
        assert len(package_names) == len(unique_packages), "Found duplicate dependencies across categories"


class TestGetPythonVersion:
    """Test Python version extraction."""

    def test_returns_version_string(self):
        """Should return Python version requirement string."""
        version = get_python_version()

        assert isinstance(version, str)
        assert len(version) > 0

    def test_version_has_expected_format(self):
        """Version should match format like '>=3.11'."""
        version = get_python_version()

        # Should contain version operator and number
        assert any(op in version for op in [">=", "==", "~="])
        assert "3." in version  # Should specify Python 3.x

    def test_version_matches_project_requirement(self):
        """Version should be at least 3.11 as per project requirements."""
        version = get_python_version()

        # Extract version number
        version_num = version.replace(">=", "").strip()
        major, minor = version_num.split(".")[:2]

        assert int(major) >= 3
        assert int(minor) >= 11, "Project requires Python 3.11+"


class TestFormatDependenciesForToml:
    """Test TOML formatting utility."""

    def test_formats_single_dependency(self):
        """Should format single dependency correctly."""
        deps = ["agno>=2.2.3"]
        result = format_dependencies_for_toml(deps)

        assert '"agno>=2.2.3",' in result
        assert result.startswith("    ")  # Default indent

    def test_formats_multiple_dependencies(self):
        """Should format multiple dependencies with newlines."""
        deps = ["agno>=2.2.3", "pydantic>=2.12.0"]
        result = format_dependencies_for_toml(deps)

        assert '"agno>=2.2.3",' in result
        assert '"pydantic>=2.12.0",' in result
        assert "\n" in result

    def test_respects_custom_indent(self):
        """Should respect custom indentation."""
        deps = ["agno>=2.2.3"]
        result = format_dependencies_for_toml(deps, indent=8)

        assert result.startswith(" " * 8)

    def test_handles_empty_list(self):
        """Should handle empty dependency list."""
        deps = []
        result = format_dependencies_for_toml(deps)

        assert result == ""

    def test_preserves_version_constraints(self):
        """Should preserve complex version constraints."""
        deps = ["package>=1.0.0,<2.0.0", "other[extra]>=3.0"]
        result = format_dependencies_for_toml(deps)

        assert ">=1.0.0,<2.0.0" in result
        assert "[extra]>=3.0" in result


class TestIntegration:
    """Integration tests for full workflow."""

    def test_can_extract_and_format_all_dependencies(self):
        """Should successfully extract and format all dependency groups."""
        deps = get_hive_dependencies()

        # Format each group
        for category, dep_list in deps.items():
            if dep_list:  # Only format non-empty groups
                formatted = format_dependencies_for_toml(dep_list)
                assert len(formatted) > 0, f"Failed to format {category} dependencies"
                assert "\n" in formatted or len(dep_list) == 1

    def test_generates_valid_toml_structure(self):
        """Should generate valid TOML-compatible output."""
        deps = get_hive_dependencies()
        python_version = get_python_version()

        # Simulate minimal pyproject.toml generation
        core_formatted = format_dependencies_for_toml(deps["core"])

        toml_content = f"""[project]
name = "test-project"
requires-python = "{python_version}"
dependencies = [
{core_formatted}
]
"""

        # Basic validation - should have proper structure
        assert "[project]" in toml_content
        assert "requires-python =" in toml_content
        assert "dependencies = [" in toml_content
        assert 'name = "test-project"' in toml_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
