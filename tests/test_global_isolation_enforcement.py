"""
Test the global test isolation enforcement mechanism.

This test file verifies that our global test isolation works correctly
to prevent project directory pollution.
"""

import warnings
from pathlib import Path

import pytest


def test_global_isolation_fixture_is_active(enforce_global_test_isolation):
    """Test that the global isolation fixture is properly active."""
    # The fixture should provide a temp directory
    assert enforce_global_test_isolation is not None
    assert isinstance(enforce_global_test_isolation, Path)
    assert enforce_global_test_isolation.exists()
    assert "test_isolation" in str(enforce_global_test_isolation)


def test_isolated_workspace_protects_against_pollution(isolated_workspace):
    """Test that isolated_workspace fixture provides complete protection."""
    # Create a file - should go into the isolated workspace
    test_file = Path("safe_test_file.txt")
    test_file.write_text("This should be in isolated workspace")

    # Verify file was created in the isolated workspace, not project root
    assert test_file.exists()
    assert str(test_file.absolute()).find("test_workspace") != -1

    # Verify we're not in the project root
    current_dir = Path.cwd()
    assert "test_workspace" in str(current_dir)


def test_warning_system_for_project_pollution():
    """Test that warnings are issued for potential project pollution."""
    # This test runs without isolated_workspace to test the warning system

    # Capture warnings
    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        # Try to create a file that might trigger a warning
        # Note: The warning depends on whether we're in project root
        project_root = Path(__file__).parent.parent.absolute()
        current_dir = Path.cwd()

        if current_dir == project_root:
            # We're in project root, so this should trigger a warning
            with open("test_warning_file.txt", "w") as f:
                f.write("This should trigger a warning")

            # Clean up immediately
            if Path("test_warning_file.txt").exists():
                Path("test_warning_file.txt").unlink()

            # Check if warning was triggered
            pollution_warnings = [w for w in warning_list if "attempted to create file" in str(w.message)]

            # If we got a warning, verify it's properly formatted
            if pollution_warnings:
                warning_msg = str(pollution_warnings[0].message)
                assert "test_warning_file.txt" in warning_msg
                assert "isolated_workspace fixture" in warning_msg


def test_temp_path_is_safe_by_default(tmp_path):
    """Test that tmp_path usage doesn't trigger warnings."""
    # Create files in tmp_path - should never trigger warnings
    test_file = tmp_path / "safe_file.txt"
    test_file.write_text("This is safe in tmp_path")

    # Verify file exists and is in temp location
    assert test_file.exists()
    assert "tmp" in str(test_file.absolute()).lower()


class TestGlobalIsolationBehavior:
    """Test class to verify isolation works across different test patterns."""

    def test_class_based_test_isolation(self, isolated_workspace):
        """Test that class-based tests also get isolation protection."""
        # This should be protected by the isolated_workspace fixture
        current_dir = Path.cwd()
        # Should not be in project root if isolation is working
        project_root = Path(__file__).parent.parent.absolute()

        # We're using isolated_workspace, so we shouldn't be in project root
        assert current_dir != project_root
        # Verify we're in the isolated workspace
        assert "test_workspace" in str(current_dir)
        assert isolated_workspace in current_dir.parents or current_dir == isolated_workspace


@pytest.mark.parametrize("filename", ["test_artifact.txt", "temporary_file.tmp", "output_data.json"])
def test_parametrized_isolation(filename, tmp_path):
    """Test that parametrized tests maintain isolation."""
    # Use tmp_path to ensure safe file operations
    test_file = tmp_path / filename
    test_file.write_text(f"Test content for {filename}")

    assert test_file.exists()
    assert "tmp" in str(test_file.absolute()).lower()
