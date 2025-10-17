"""
Comprehensive test suite for AI root resolution functionality.

Tests AI directory resolution with multi-level precedence handling, directory
structure validation, helper functions, and exception handling for the TDD RED phase
implementation of lib/utils/ai_root.py.

This test suite drives the implementation of:
- resolve_ai_root() function with 4-level precedence logic
- validate_ai_structure() directory validation function
- get_ai_subdirectory() helper function
- AIRootError custom exception class

All tests are designed to FAIL initially to guide TDD implementation.
"""

import shutil
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from lib.utils.ai_root import (
    AIRootError,
    get_ai_subdirectory,
    resolve_ai_root,
    validate_ai_structure,
)


@pytest.fixture
def temp_ai_structure():
    """Create temporary AI directory structure with required subdirectories."""
    temp_dir = Path(tempfile.mkdtemp())
    (temp_dir / "agents").mkdir()
    (temp_dir / "teams").mkdir()
    (temp_dir / "workflows").mkdir()
    # Add optional directories that exist in real AI structure
    (temp_dir / "tools").mkdir()
    (temp_dir / "templates").mkdir()
    yield temp_dir
    shutil.rmtree(str(temp_dir))


@pytest.fixture
def incomplete_ai_structure():
    """Create temporary AI directory structure missing some required subdirectories."""
    temp_dir = Path(tempfile.mkdtemp())
    (temp_dir / "agents").mkdir()
    # Missing teams and workflows directories
    yield temp_dir
    shutil.rmtree(str(temp_dir))


@pytest.fixture
def mock_settings_with_ai_root():
    """Create mock settings object with hive_ai_root attribute."""
    settings = Mock()
    settings.hive_ai_root = "/mock/ai/root"
    return settings


@pytest.fixture
def mock_settings_without_ai_root():
    """Create mock settings object without hive_ai_root attribute."""
    settings = Mock()
    del settings.hive_ai_root  # Ensure attribute doesn't exist
    return settings


class TestAIRootResolution:
    """Test resolve_ai_root() function with precedence handling."""

    def test_resolve_with_explicit_path_takes_highest_precedence(self, temp_ai_structure, monkeypatch):
        """Test that explicit path argument takes highest precedence."""
        # Set environment variable and settings that should be ignored
        monkeypatch.setenv("HIVE_AI_ROOT", "/env/should/be/ignored")
        settings = Mock()
        settings.hive_ai_root = "/settings/should/be/ignored"

        result = resolve_ai_root(explicit_path=temp_ai_structure, settings=settings)
        # Both sides need to be resolved for comparison (handles macOS symlinks /var -> /private/var)
        assert result.resolve() == temp_ai_structure.resolve()

    def test_resolve_with_hive_ai_root_env_var_when_no_explicit_path(self, temp_ai_structure, monkeypatch):
        """Test that HIVE_AI_ROOT environment variable is used when no explicit path."""
        monkeypatch.setenv("HIVE_AI_ROOT", str(temp_ai_structure))
        settings = Mock()
        settings.hive_ai_root = "/settings/should/be/ignored"

        result = resolve_ai_root(explicit_path=None, settings=settings)
        assert result.resolve() == temp_ai_structure.resolve()

    def test_resolve_with_settings_object_when_no_env_var(self, temp_ai_structure, monkeypatch):
        """Test that settings object hive_ai_root is used when no env var."""
        monkeypatch.delenv("HIVE_AI_ROOT", raising=False)
        settings = Mock()
        settings.hive_ai_root = str(temp_ai_structure)

        result = resolve_ai_root(explicit_path=None, settings=settings)
        assert result.resolve() == temp_ai_structure.resolve()

    def test_resolve_with_default_ai_when_no_other_sources(self, monkeypatch):
        """Test that default 'ai' directory is used when no other sources available."""
        monkeypatch.delenv("HIVE_AI_ROOT", raising=False)

        result = resolve_ai_root(explicit_path=None, settings=None)
        assert result == Path("ai")

    def test_resolve_precedence_order_explicit_over_env_var(self, temp_ai_structure, monkeypatch):
        """Test explicit path takes precedence over environment variable."""
        env_dir = temp_ai_structure / "env_ai"
        env_dir.mkdir()
        explicit_dir = temp_ai_structure / "explicit_ai"
        explicit_dir.mkdir()

        monkeypatch.setenv("HIVE_AI_ROOT", str(env_dir))

        result = resolve_ai_root(explicit_path=explicit_dir, settings=None)
        assert result.resolve() == explicit_dir.resolve()

    def test_resolve_precedence_order_env_var_over_settings(self, temp_ai_structure, monkeypatch):
        """Test environment variable takes precedence over settings."""
        env_dir = temp_ai_structure / "env_ai"
        env_dir.mkdir()
        settings_dir = temp_ai_structure / "settings_ai"
        settings_dir.mkdir()

        monkeypatch.setenv("HIVE_AI_ROOT", str(env_dir))
        settings = Mock()
        settings.hive_ai_root = str(settings_dir)

        result = resolve_ai_root(explicit_path=None, settings=settings)
        assert result.resolve() == env_dir.resolve()

    def test_resolve_precedence_order_settings_over_default(self, temp_ai_structure, monkeypatch):
        """Test settings takes precedence over default."""
        monkeypatch.delenv("HIVE_AI_ROOT", raising=False)
        settings = Mock()
        settings.hive_ai_root = str(temp_ai_structure)

        result = resolve_ai_root(explicit_path=None, settings=settings)
        assert result.resolve() == temp_ai_structure.resolve()

    def test_resolve_with_relative_path_converts_to_absolute(self, temp_ai_structure):
        """Test that relative paths are converted to absolute paths."""
        # Create relative path by getting just the last part
        relative_path = Path(temp_ai_structure.name)

        with patch("pathlib.Path.resolve", return_value=temp_ai_structure):
            result = resolve_ai_root(explicit_path=relative_path, settings=None)
            assert result.is_absolute()

    def test_resolve_with_nonexistent_explicit_path_raises_error(self):
        """Test that non-existent explicit path raises AIRootError."""
        nonexistent_path = Path("/nonexistent/ai/directory")

        with pytest.raises(AIRootError, match="does not exist"):
            resolve_ai_root(explicit_path=nonexistent_path, settings=None)

    def test_resolve_with_invalid_env_var_path_raises_error(self, monkeypatch):
        """Test that invalid environment variable path raises AIRootError."""
        monkeypatch.setenv("HIVE_AI_ROOT", "/nonexistent/env/ai")

        with pytest.raises(AIRootError, match="does not exist"):
            resolve_ai_root(explicit_path=None, settings=None)

    def test_resolve_with_file_instead_of_directory_raises_error(self, temp_ai_structure):
        """Test that pointing to a file instead of directory raises AIRootError."""
        file_path = temp_ai_structure / "not_a_directory.txt"
        file_path.write_text("content")

        with pytest.raises(AIRootError, match="not a directory"):
            resolve_ai_root(explicit_path=file_path, settings=None)

    def test_resolve_with_none_settings_attribute(self, monkeypatch):
        """Test that settings object without hive_ai_root attribute falls back to default."""
        monkeypatch.delenv("HIVE_AI_ROOT", raising=False)
        settings = Mock()
        del settings.hive_ai_root  # Remove the attribute

        result = resolve_ai_root(explicit_path=None, settings=settings)
        assert result == Path("ai")

    def test_resolve_with_empty_env_var_falls_back_to_settings(self, temp_ai_structure, monkeypatch):
        """Test that empty environment variable falls back to settings."""
        monkeypatch.setenv("HIVE_AI_ROOT", "")
        settings = Mock()
        settings.hive_ai_root = str(temp_ai_structure)

        result = resolve_ai_root(explicit_path=None, settings=settings)
        assert result.resolve() == temp_ai_structure.resolve()

    def test_resolve_with_whitespace_only_env_var(self, temp_ai_structure, monkeypatch):
        """Test that whitespace-only environment variable is handled properly."""
        monkeypatch.setenv("HIVE_AI_ROOT", "   \t\n  ")
        settings = Mock()
        settings.hive_ai_root = str(temp_ai_structure)

        result = resolve_ai_root(explicit_path=None, settings=settings)
        assert result.resolve() == temp_ai_structure.resolve()


class TestAIStructureValidation:
    """Test validate_ai_structure() function."""

    def test_validate_complete_ai_structure_with_all_subdirs(self, temp_ai_structure):
        """Test validation of complete AI structure with all required subdirectories."""
        result = validate_ai_structure(temp_ai_structure)

        expected_result = {
            "valid": True,
            "ai_root": str(temp_ai_structure),
            "required_subdirs": {"agents": True, "teams": True, "workflows": True},
            "optional_subdirs": {"tools": True, "templates": True},
            "missing_subdirs": [],
            "errors": [],
        }

        assert result == expected_result

    def test_validate_ai_structure_missing_agents_directory(self, incomplete_ai_structure):
        """Test validation when agents directory is missing."""
        # Remove agents directory
        shutil.rmtree(str(incomplete_ai_structure / "agents"))

        result = validate_ai_structure(incomplete_ai_structure)

        assert result["valid"] is False
        assert "agents" in result["missing_subdirs"]
        assert any("agents" in error for error in result["errors"])

    def test_validate_ai_structure_missing_teams_directory(self, temp_ai_structure):
        """Test validation when teams directory is missing."""
        shutil.rmtree(str(temp_ai_structure / "teams"))

        result = validate_ai_structure(temp_ai_structure)

        assert result["valid"] is False
        assert "teams" in result["missing_subdirs"]
        assert result["required_subdirs"]["teams"] is False

    def test_validate_ai_structure_missing_workflows_directory(self, temp_ai_structure):
        """Test validation when workflows directory is missing."""
        shutil.rmtree(str(temp_ai_structure / "workflows"))

        result = validate_ai_structure(temp_ai_structure)

        assert result["valid"] is False
        assert "workflows" in result["missing_subdirs"]
        assert result["required_subdirs"]["workflows"] is False

    def test_validate_ai_structure_missing_multiple_subdirs(self, temp_ai_structure):
        """Test validation when multiple required subdirectories are missing."""
        shutil.rmtree(str(temp_ai_structure / "teams"))
        shutil.rmtree(str(temp_ai_structure / "workflows"))

        result = validate_ai_structure(temp_ai_structure)

        assert result["valid"] is False
        assert "teams" in result["missing_subdirs"]
        assert "workflows" in result["missing_subdirs"]
        assert len(result["missing_subdirs"]) == 2

    def test_validate_nonexistent_ai_directory_raises_error(self):
        """Test that validating non-existent directory raises AIRootError."""
        nonexistent_path = Path("/nonexistent/ai/directory")

        with pytest.raises(AIRootError, match="does not exist"):
            validate_ai_structure(nonexistent_path)

    def test_validate_file_instead_of_ai_directory_raises_error(self, temp_ai_structure):
        """Test that validating a file instead of directory raises AIRootError."""
        file_path = temp_ai_structure / "not_a_directory.txt"
        file_path.write_text("content")

        with pytest.raises(AIRootError, match="not a directory"):
            validate_ai_structure(file_path)

    def test_validate_ai_structure_with_extra_subdirectories(self, temp_ai_structure):
        """Test validation with extra subdirectories beyond required ones."""
        # Add extra directories
        (temp_ai_structure / "custom").mkdir()
        (temp_ai_structure / "experimental").mkdir()

        result = validate_ai_structure(temp_ai_structure)

        assert result["valid"] is True
        assert "custom" in str(result)  # Should be noted in some way
        assert "experimental" in str(result)

    def test_validate_ai_structure_with_permission_errors(self, temp_ai_structure):
        """Test validation handles permission errors gracefully."""
        agents_dir = temp_ai_structure / "agents"

        # Make directory unreadable
        try:
            agents_dir.chmod(0o000)

            with pytest.raises(AIRootError, match="Permission denied"):
                validate_ai_structure(temp_ai_structure)
        finally:
            # Restore permissions for cleanup
            agents_dir.chmod(0o755)

    def test_validate_ai_structure_with_empty_directory(self):
        """Test validation of completely empty AI directory."""
        temp_dir = Path(tempfile.mkdtemp())

        try:
            result = validate_ai_structure(temp_dir)

            assert result["valid"] is False
            assert len(result["missing_subdirs"]) == 3
            assert "agents" in result["missing_subdirs"]
            assert "teams" in result["missing_subdirs"]
            assert "workflows" in result["missing_subdirs"]
        finally:
            shutil.rmtree(str(temp_dir))

    def test_validate_ai_structure_with_files_instead_of_subdirs(self, temp_ai_structure):
        """Test validation when required subdirs are files instead of directories."""
        # Remove agents dir and create a file with same name
        shutil.rmtree(str(temp_ai_structure / "agents"))
        (temp_ai_structure / "agents").write_text("not a directory")

        result = validate_ai_structure(temp_ai_structure)

        assert result["valid"] is False
        assert "agents" in result["missing_subdirs"]


class TestAISubdirectoryHelper:
    """Test get_ai_subdirectory() helper function."""

    def test_get_agents_subdirectory_with_valid_ai_root(self, temp_ai_structure):
        """Test getting agents subdirectory with valid AI root."""
        result = get_ai_subdirectory(temp_ai_structure, "agents")
        assert result.resolve() == (temp_ai_structure / "agents").resolve()

    def test_get_teams_subdirectory_with_valid_ai_root(self, temp_ai_structure):
        """Test getting teams subdirectory with valid AI root."""
        result = get_ai_subdirectory(temp_ai_structure, "teams")
        assert result.resolve() == (temp_ai_structure / "teams").resolve()

    def test_get_workflows_subdirectory_with_valid_ai_root(self, temp_ai_structure):
        """Test getting workflows subdirectory with valid AI root."""
        result = get_ai_subdirectory(temp_ai_structure, "workflows")
        assert result.resolve() == (temp_ai_structure / "workflows").resolve()

    def test_get_tools_subdirectory_with_valid_ai_root(self, temp_ai_structure):
        """Test getting tools subdirectory (optional) with valid AI root."""
        result = get_ai_subdirectory(temp_ai_structure, "tools")
        assert result.resolve() == (temp_ai_structure / "tools").resolve()

    def test_get_subdirectory_with_nonexistent_ai_root_raises_error(self):
        """Test that non-existent AI root raises AIRootError."""
        nonexistent_root = Path("/nonexistent/ai/root")

        with pytest.raises(AIRootError, match="does not exist"):
            get_ai_subdirectory(nonexistent_root, "agents")

    def test_get_subdirectory_with_invalid_subdir_name_raises_error(self, temp_ai_structure):
        """Test that invalid subdirectory name raises AIRootError."""
        with pytest.raises(AIRootError, match="Invalid subdirectory"):
            get_ai_subdirectory(temp_ai_structure, "invalid_subdir")

    def test_get_subdirectory_creates_absolute_paths(self, temp_ai_structure):
        """Test that returned paths are always absolute."""
        result = get_ai_subdirectory(temp_ai_structure, "agents")
        assert result.is_absolute()

    def test_get_subdirectory_with_relative_ai_root(self, temp_ai_structure):
        """Test getting subdirectory with relative AI root path."""
        # Create a relative path reference
        relative_root = Path(".")

        with patch("pathlib.Path.resolve", return_value=temp_ai_structure):
            result = get_ai_subdirectory(relative_root, "agents")
            assert result.is_absolute()

    def test_get_subdirectory_with_nonexistent_subdirectory(self, temp_ai_structure):
        """Test getting subdirectory that doesn't exist yet."""
        # Remove agents directory
        shutil.rmtree(str(temp_ai_structure / "agents"))

        with pytest.raises(AIRootError, match="Subdirectory .* does not exist"):
            get_ai_subdirectory(temp_ai_structure, "agents")

    def test_get_subdirectory_validates_input_types(self, temp_ai_structure):
        """Test that function validates input parameter types."""
        with pytest.raises(AIRootError, match="must be a string"):
            get_ai_subdirectory(temp_ai_structure, 123)

    def test_get_subdirectory_handles_case_sensitivity(self, temp_ai_structure):
        """Test that subdirectory names are case-sensitive."""
        with pytest.raises(AIRootError, match="Invalid subdirectory"):
            get_ai_subdirectory(temp_ai_structure, "AGENTS")


class TestAIRootErrorHandling:
    """Test AIRootError exception class and error propagation."""

    def test_ai_root_error_creation_with_message(self):
        """Test AIRootError can be created with custom message."""
        error_message = "Custom AI root error message"
        error = AIRootError(error_message)
        assert str(error) == error_message

    def test_ai_root_error_inheritance_from_exception(self):
        """Test that AIRootError properly inherits from Exception."""
        error = AIRootError("test message")
        assert isinstance(error, Exception)
        assert isinstance(error, AIRootError)

    def test_ai_root_error_clear_error_messages(self):
        """Test that AIRootError provides clear, actionable error messages."""
        # Test various error scenarios that should provide clear messages
        error_scenarios = [
            "AI root directory '/path/to/ai' does not exist",
            "AI root '/path/to/ai' is not a directory",
            "Required subdirectory 'agents' missing from AI root",
            "Permission denied accessing AI root directory",
            "Invalid subdirectory 'invalid' - must be one of: agents, teams, workflows, tools, templates",
        ]

        for message in error_scenarios:
            error = AIRootError(message)
            assert len(str(error)) > 10  # Ensure non-trivial message
            assert any(keyword in str(error).lower() for keyword in ["ai", "directory", "path"])

    def test_ai_root_error_propagation_in_resolve_function(self):
        """Test that AIRootError is properly propagated from resolve function."""
        with pytest.raises(AIRootError):
            resolve_ai_root(explicit_path=Path("/nonexistent"), settings=None)

    def test_ai_root_error_propagation_in_validate_function(self):
        """Test that AIRootError is properly propagated from validate function."""
        with pytest.raises(AIRootError):
            validate_ai_structure(Path("/nonexistent"))

    def test_ai_root_error_propagation_in_subdirectory_function(self):
        """Test that AIRootError is properly propagated from subdirectory function."""
        with pytest.raises(AIRootError):
            get_ai_subdirectory(Path("/nonexistent"), "agents")

    def test_ai_root_error_with_nested_exceptions(self):
        """Test AIRootError can wrap other exceptions appropriately."""
        try:
            # Simulate a permission error being caught and re-raised as AIRootError
            raise PermissionError("Access denied")
        except PermissionError as e:
            ai_error = AIRootError(f"Permission denied accessing AI root: {e}")
            assert "Permission denied" in str(ai_error)
            assert "Access denied" in str(ai_error)


class TestAIRootIntegration:
    """Test integration scenarios and end-to-end workflows."""

    def test_integration_with_settings_object_and_env_var(self, temp_ai_structure, monkeypatch):
        """Test integration with both settings object and environment variable."""
        # Set up environment variable
        env_ai_dir = temp_ai_structure / "env_ai"
        env_ai_dir.mkdir()
        (env_ai_dir / "agents").mkdir()
        (env_ai_dir / "teams").mkdir()
        (env_ai_dir / "workflows").mkdir()

        monkeypatch.setenv("HIVE_AI_ROOT", str(env_ai_dir))

        # Create settings with different path
        settings = Mock()
        settings.hive_ai_root = str(temp_ai_structure)

        # Environment variable should take precedence
        resolved_root = resolve_ai_root(explicit_path=None, settings=settings)
        assert resolved_root.resolve() == env_ai_dir.resolve()

        # Validate the resolved structure
        validation = validate_ai_structure(resolved_root)
        assert validation["valid"] is True

    def test_integration_end_to_end_resolution_and_validation(self, temp_ai_structure):
        """Test complete end-to-end workflow from resolution to validation."""
        # Resolve AI root
        ai_root = resolve_ai_root(explicit_path=temp_ai_structure, settings=None)

        # Validate the structure
        validation = validate_ai_structure(ai_root)
        assert validation["valid"] is True

        # Get subdirectories
        agents_dir = get_ai_subdirectory(ai_root, "agents")
        teams_dir = get_ai_subdirectory(ai_root, "teams")
        workflows_dir = get_ai_subdirectory(ai_root, "workflows")

        assert agents_dir.exists()
        assert teams_dir.exists()
        assert workflows_dir.exists()

    def test_integration_error_handling_across_functions(self):
        """Test error handling integration across all functions."""
        nonexistent_root = Path("/nonexistent/ai/root")

        # All functions should raise AIRootError for non-existent paths
        with pytest.raises(AIRootError):
            resolve_ai_root(explicit_path=nonexistent_root, settings=None)

        with pytest.raises(AIRootError):
            validate_ai_structure(nonexistent_root)

        with pytest.raises(AIRootError):
            get_ai_subdirectory(nonexistent_root, "agents")

    def test_integration_with_unicode_paths(self, temp_ai_structure):
        """Test integration with Unicode characters in paths."""
        unicode_ai_dir = temp_ai_structure / "ai_测试_ñ"
        unicode_ai_dir.mkdir()
        (unicode_ai_dir / "agents").mkdir()
        (unicode_ai_dir / "teams").mkdir()
        (unicode_ai_dir / "workflows").mkdir()

        # Should handle Unicode paths correctly
        resolved_root = resolve_ai_root(explicit_path=unicode_ai_dir, settings=None)
        assert resolved_root.resolve() == unicode_ai_dir.resolve()

        validation = validate_ai_structure(resolved_root)
        assert validation["valid"] is True

    def test_integration_with_symlinked_directories(self, temp_ai_structure):
        """Test integration with symbolic links (Unix-like systems only)."""
        try:
            # Create symlink to AI directory
            symlink_path = temp_ai_structure.parent / "ai_symlink"
            symlink_path.symlink_to(temp_ai_structure)

            # Should resolve symlinks correctly
            resolved_root = resolve_ai_root(explicit_path=symlink_path, settings=None)
            validation = validate_ai_structure(resolved_root)
            assert validation["valid"] is True

        except (OSError, NotImplementedError):
            # Skip test on systems that don't support symlinks
            pytest.skip("Symbolic links not supported on this system")

    def test_integration_concurrent_access_to_ai_root(self, temp_ai_structure):
        """Test concurrent access to AI root functions."""
        results = []
        errors = []

        def worker():
            try:
                ai_root = resolve_ai_root(explicit_path=temp_ai_structure, settings=None)
                validation = validate_ai_structure(ai_root)
                agents_dir = get_ai_subdirectory(ai_root, "agents")
                results.append((ai_root, validation["valid"], agents_dir))
            except Exception as e:
                errors.append(e)

        # Run multiple threads concurrently
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All threads should succeed
        assert len(errors) == 0
        assert len(results) == 5

        # All results should be consistent
        for ai_root, is_valid, agents_dir in results:
            assert ai_root.resolve() == temp_ai_structure.resolve()
            assert is_valid is True
            assert agents_dir.resolve() == (temp_ai_structure / "agents").resolve()

    def test_integration_with_real_project_structure(self):
        """Test integration with actual project AI directory structure."""
        # Test with the real AI directory if it exists
        real_ai_path = Path("ai")

        if real_ai_path.exists():
            resolved_root = resolve_ai_root(explicit_path=real_ai_path, settings=None)
            validation = validate_ai_structure(resolved_root)

            # Real AI structure should be valid
            assert validation["valid"] is True
            assert validation["required_subdirs"]["agents"] is True
            assert validation["required_subdirs"]["teams"] is True
            assert validation["required_subdirs"]["workflows"] is True
        else:
            pytest.skip("Real AI directory not found in project")

    def test_integration_performance_with_large_directory_structures(self, temp_ai_structure):
        """Test performance with large directory structures."""
        # Create many subdirectories in agents folder
        agents_dir = temp_ai_structure / "agents"
        for i in range(100):
            (agents_dir / f"agent_{i:03d}").mkdir()

        start_time = time.time()

        # Should still be fast
        ai_root = resolve_ai_root(explicit_path=temp_ai_structure, settings=None)
        validation = validate_ai_structure(ai_root)
        agents_subdir = get_ai_subdirectory(ai_root, "agents")

        end_time = time.time()

        assert validation["valid"] is True
        assert agents_subdir.resolve() == agents_dir.resolve()
        # Should complete in reasonable time (less than 1 second)
        assert end_time - start_time < 1.0


class TestAIRootEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_resolve_with_very_long_path(self, temp_ai_structure):
        """Test handling of extremely long file paths."""
        # Create deeply nested directory structure
        deep_path = temp_ai_structure
        for i in range(10):
            deep_path = deep_path / f"very_long_directory_name_{i}" / "nested"

        try:
            deep_path.mkdir(parents=True)
            (deep_path / "agents").mkdir()
            (deep_path / "teams").mkdir()
            (deep_path / "workflows").mkdir()

            result = resolve_ai_root(explicit_path=deep_path, settings=None)
            assert result.resolve() == deep_path.resolve()

        except OSError:
            # Skip if filesystem doesn't support such long paths
            pytest.skip("Filesystem doesn't support very long paths")

    def test_resolve_with_special_characters_in_path(self, temp_ai_structure):
        """Test handling of special characters in directory paths."""
        special_chars_dir = temp_ai_structure / "ai-with-special!@#$%^&*()_+chars"

        try:
            special_chars_dir.mkdir()
            (special_chars_dir / "agents").mkdir()
            (special_chars_dir / "teams").mkdir()
            (special_chars_dir / "workflows").mkdir()

            result = resolve_ai_root(explicit_path=special_chars_dir, settings=None)
            assert result.resolve() == special_chars_dir.resolve()

        except OSError:
            # Skip if filesystem doesn't support special characters
            pytest.skip("Filesystem doesn't support special characters in paths")

    def test_validate_structure_with_circular_symlinks(self, temp_ai_structure):
        """Test handling of circular symbolic links."""
        try:
            # Create circular symlink
            circular_link = temp_ai_structure / "circular"
            circular_link.symlink_to(temp_ai_structure)

            # Should handle circular links gracefully
            validation = validate_ai_structure(temp_ai_structure)
            assert validation["valid"] is True

        except (OSError, NotImplementedError):
            pytest.skip("Symbolic links not supported on this system")

    def test_concurrent_directory_modification_during_validation(self, temp_ai_structure):
        """Test validation behavior when directory is modified during validation."""

        def modify_directory():
            # Wait a bit then modify directory
            time.sleep(0.1)
            try:
                (temp_ai_structure / "new_dir").mkdir()
            except Exception:  # noqa: S110 - Silent exception handling is intentional
                pass  # Ignore errors during concurrent modification

        # Start modification in background
        modifier_thread = threading.Thread(target=modify_directory)
        modifier_thread.start()

        # Validate while modification is happening
        validation = validate_ai_structure(temp_ai_structure)

        modifier_thread.join()

        # Should still succeed even with concurrent modifications
        assert validation["valid"] is True

    def test_resolve_with_maximum_environment_variable_length(self, monkeypatch):
        """Test handling of very long environment variable values."""
        very_long_path = "/very/long/path/" + "a" * 1000
        monkeypatch.setenv("HIVE_AI_ROOT", very_long_path)

        # Should handle long environment variables gracefully
        with pytest.raises(AIRootError):  # Path won't exist, but should handle length
            resolve_ai_root(explicit_path=None, settings=None)
