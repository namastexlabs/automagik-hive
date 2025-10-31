"""Tests for pyproject.toml generation in init command."""

import sys
import tomllib
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestPyprojectTomlGeneration:
    """Test pyproject.toml file generation."""

    @pytest.fixture
    def temp_project_dir(self, tmp_path):
        """Create a temporary project directory."""
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        return project_dir

    def test_pyproject_toml_is_created(self, temp_project_dir):
        """Should create pyproject.toml file in project directory."""
        from hive.cli.init import _generate_pyproject_toml

        _generate_pyproject_toml(temp_project_dir, "test-project")

        pyproject_file = temp_project_dir / "pyproject.toml"
        assert pyproject_file.exists(), "pyproject.toml should be created"

    def test_pyproject_toml_is_valid_toml(self, temp_project_dir):
        """Generated pyproject.toml should be valid TOML."""
        from hive.cli.init import _generate_pyproject_toml

        _generate_pyproject_toml(temp_project_dir, "test-project")

        pyproject_file = temp_project_dir / "pyproject.toml"
        with open(pyproject_file, "rb") as f:
            pyproject = tomllib.load(f)  # Should not raise

        assert isinstance(pyproject, dict)

    def test_pyproject_has_required_sections(self, temp_project_dir):
        """Should have [project], [build-system], [tool.uv] sections."""
        from hive.cli.init import _generate_pyproject_toml

        _generate_pyproject_toml(temp_project_dir, "test-project")

        pyproject_file = temp_project_dir / "pyproject.toml"
        with open(pyproject_file, "rb") as f:
            pyproject = tomllib.load(f)

        assert "project" in pyproject
        assert "build-system" in pyproject
        assert "tool" in pyproject
        assert "uv" in pyproject["tool"]

    def test_pyproject_name_matches_parameter(self, temp_project_dir):
        """Project name in pyproject.toml should match provided name."""
        from hive.cli.init import _generate_pyproject_toml

        project_name = "my-awesome-project"
        _generate_pyproject_toml(temp_project_dir, project_name)

        pyproject_file = temp_project_dir / "pyproject.toml"
        with open(pyproject_file, "rb") as f:
            pyproject = tomllib.load(f)

        assert pyproject["project"]["name"] == project_name

    def test_pyproject_has_python_version_requirement(self, temp_project_dir):
        """Should have requires-python field with version."""
        from hive.cli.init import _generate_pyproject_toml

        _generate_pyproject_toml(temp_project_dir, "test-project")

        pyproject_file = temp_project_dir / "pyproject.toml"
        with open(pyproject_file, "rb") as f:
            pyproject = tomllib.load(f)

        assert "requires-python" in pyproject["project"]
        assert "3.11" in pyproject["project"]["requires-python"]

    def test_pyproject_has_core_dependencies(self, temp_project_dir):
        """Should include core dependencies from main project."""
        from hive.cli.init import _generate_pyproject_toml

        _generate_pyproject_toml(temp_project_dir, "test-project")

        pyproject_file = temp_project_dir / "pyproject.toml"
        with open(pyproject_file, "rb") as f:
            pyproject = tomllib.load(f)

        deps = pyproject["project"]["dependencies"]
        deps_str = " ".join(deps).lower()

        # Check for essential packages
        assert "agno" in deps_str
        assert "pydantic" in deps_str
        assert "yaml" in deps_str

    def test_pyproject_dependencies_have_versions(self, temp_project_dir):
        """Dependencies should include version specifiers."""
        from hive.cli.init import _generate_pyproject_toml

        _generate_pyproject_toml(temp_project_dir, "test-project")

        pyproject_file = temp_project_dir / "pyproject.toml"
        with open(pyproject_file, "rb") as f:
            pyproject = tomllib.load(f)

        deps = pyproject["project"]["dependencies"]

        # At least some dependencies should have version specifiers
        versioned_deps = [d for d in deps if ">=" in d or "==" in d]
        assert len(versioned_deps) > 0, "Dependencies should have version specifiers"

    def test_pyproject_has_optional_dependency_groups(self, temp_project_dir):
        """Should include [dependency-groups] with optional groups."""
        from hive.cli.init import _generate_pyproject_toml

        _generate_pyproject_toml(temp_project_dir, "test-project")

        pyproject_file = temp_project_dir / "pyproject.toml"
        with open(pyproject_file, "rb") as f:
            pyproject = tomllib.load(f)

        assert "dependency-groups" in pyproject

    def test_pyproject_has_build_backend(self, temp_project_dir):
        """Should specify hatchling as build backend."""
        from hive.cli.init import _generate_pyproject_toml

        _generate_pyproject_toml(temp_project_dir, "test-project")

        pyproject_file = temp_project_dir / "pyproject.toml"
        with open(pyproject_file, "rb") as f:
            pyproject = tomllib.load(f)

        assert pyproject["build-system"]["requires"] == ["hatchling"]
        assert pyproject["build-system"]["build-backend"] == "hatchling.build"

    def test_pyproject_has_uv_package_flag(self, temp_project_dir):
        """Should enable uv package mode."""
        from hive.cli.init import _generate_pyproject_toml

        _generate_pyproject_toml(temp_project_dir, "test-project")

        pyproject_file = temp_project_dir / "pyproject.toml"
        with open(pyproject_file, "rb") as f:
            pyproject = tomllib.load(f)

        assert pyproject["tool"]["uv"]["package"] is True

    def test_no_hardcoded_versions_in_comments(self, temp_project_dir):
        """Generated file should not have hardcoded versions in comments."""
        from hive.cli.init import _generate_pyproject_toml

        _generate_pyproject_toml(temp_project_dir, "test-project")

        pyproject_file = temp_project_dir / "pyproject.toml"
        content = pyproject_file.read_text()

        # Check that comments don't contain specific version numbers
        # (versions should only appear in actual dependency specs)
        lines = content.split("\n")
        comment_lines = [line for line in lines if line.strip().startswith("#")]

        for line in comment_lines:
            # Comments shouldn't have version patterns like ">=2.2.3"
            assert not any(pattern in line for pattern in [">=" + str(i) for i in range(10)]), (
                f"Comment should not have hardcoded version: {line}"
            )


class TestInitFileGeneration:
    """Test __init__.py file generation."""

    @pytest.fixture
    def temp_project_dir(self, tmp_path):
        """Create a temporary project directory."""
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        return project_dir

    def test_init_files_are_created(self, temp_project_dir):
        """Should create __init__.py files in ai directories."""
        from hive.cli.init import _create_init_files

        # Create directories first
        (temp_project_dir / "ai" / "agents").mkdir(parents=True)
        (temp_project_dir / "ai" / "teams").mkdir(parents=True)
        (temp_project_dir / "ai" / "workflows").mkdir(parents=True)
        (temp_project_dir / "ai" / "tools").mkdir(parents=True)

        _create_init_files(temp_project_dir)

        # Check init files exist
        assert (temp_project_dir / "ai" / "__init__.py").exists()
        assert (temp_project_dir / "ai" / "agents" / "__init__.py").exists()
        assert (temp_project_dir / "ai" / "teams" / "__init__.py").exists()
        assert (temp_project_dir / "ai" / "workflows" / "__init__.py").exists()
        assert (temp_project_dir / "ai" / "tools" / "__init__.py").exists()

    def test_init_files_have_docstrings(self, temp_project_dir):
        """__init__.py files should have module docstrings."""
        from hive.cli.init import _create_init_files

        (temp_project_dir / "ai" / "agents").mkdir(parents=True)
        _create_init_files(temp_project_dir)

        init_file = temp_project_dir / "ai" / "agents" / "__init__.py"
        content = init_file.read_text()

        # Should have a docstring
        assert '"""' in content or "'''" in content

    def test_init_files_mention_automagik_hive(self, temp_project_dir):
        """__init__.py files should mention Automagik Hive."""
        from hive.cli.init import _create_init_files

        (temp_project_dir / "ai" / "agents").mkdir(parents=True)
        _create_init_files(temp_project_dir)

        init_file = temp_project_dir / "ai" / "agents" / "__init__.py"
        content = init_file.read_text()

        assert "Automagik Hive" in content or "auto-generated" in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
