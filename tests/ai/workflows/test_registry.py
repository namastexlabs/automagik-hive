"""
Tests for ai/workflows/registry.py - Workflow Registry and factory functions
"""

from unittest.mock import Mock, patch

import pytest

from ai.workflows.registry import (
    _discover_workflows,
    get_workflow,
    get_workflow_registry,
    is_workflow_registered,
    list_available_workflows,
)


class TestWorkflowDiscovery:
    """Test workflow discovery functionality."""

    def test_discover_workflows_no_directory(self, tmp_path) -> None:
        """Test discovery when workflows directory doesn't exist."""
        # Create AI root without workflows directory
        ai_root = tmp_path / "ai"
        ai_root.mkdir(parents=True)

        with patch("ai.workflows.registry.resolve_ai_root", return_value=ai_root):
            result = _discover_workflows()
            assert result == {}

    def test_discover_workflows_success_integration(self) -> None:
        """Test successful workflow discovery using integration approach."""
        # Test that the function can be called without error
        result = _discover_workflows()
        assert isinstance(result, dict)
        # The result could be empty or contain actual workflows

    def test_discover_workflows_skips_files(self, tmp_path) -> None:
        """Test that discovery skips files and only processes directories."""
        # Create AI root with workflows directory containing a file
        ai_root = tmp_path / "ai"
        workflows_dir = ai_root / "workflows"
        workflows_dir.mkdir(parents=True)

        # Create a file (not a directory)
        (workflows_dir / "file.py").write_text("# Not a workflow directory")

        with patch("ai.workflows.registry.resolve_ai_root", return_value=ai_root):
            result = _discover_workflows()
            assert result == {}

    def test_discover_workflows_skips_underscore_dirs(self, tmp_path) -> None:
        """Test that discovery skips directories starting with underscore."""
        # Create AI root with workflows directory containing a private directory
        ai_root = tmp_path / "ai"
        workflows_dir = ai_root / "workflows"
        workflows_dir.mkdir(parents=True)

        # Create a directory starting with underscore
        private_dir = workflows_dir / "_private-workflow"
        private_dir.mkdir()

        with patch("ai.workflows.registry.resolve_ai_root", return_value=ai_root):
            result = _discover_workflows()
            assert result == {}

    def test_discover_workflows_missing_config(self, tmp_path) -> None:
        """Test workflow discovery when config.yaml is missing."""
        # Create AI root with workflow directory but no config.yaml
        ai_root = tmp_path / "ai"
        workflows_dir = ai_root / "workflows"
        workflow_dir = workflows_dir / "incomplete-workflow"
        workflow_dir.mkdir(parents=True)

        # Create workflow.py but not config.yaml
        (workflow_dir / "workflow.py").write_text("# Workflow without config")

        with patch("ai.workflows.registry.resolve_ai_root", return_value=ai_root):
            result = _discover_workflows()
            assert result == {}

    def test_discover_workflows_missing_workflow_file(self, tmp_path) -> None:
        """Test workflow discovery when workflow.py is missing."""
        # Create AI root with workflow directory but no workflow.py
        ai_root = tmp_path / "ai"
        workflows_dir = ai_root / "workflows"
        workflow_dir = workflows_dir / "incomplete-workflow"
        workflow_dir.mkdir(parents=True)

        # Create config.yaml but not workflow.py
        (workflow_dir / "config.yaml").write_text("workflow:\n  workflow_id: incomplete-workflow\n")

        with patch("ai.workflows.registry.resolve_ai_root", return_value=ai_root):
            result = _discover_workflows()
            assert result == {}

    def test_discover_workflows_no_factory_function(self, tmp_path) -> None:
        """Test discovery when workflow module has no factory function."""
        # Create AI root with workflow directory
        ai_root = tmp_path / "ai"
        workflows_dir = ai_root / "workflows"
        workflow_dir = workflows_dir / "no-factory-workflow"
        workflow_dir.mkdir(parents=True)

        # Create config.yaml
        (workflow_dir / "config.yaml").write_text("workflow:\n  workflow_id: no-factory\n")

        # Create workflow.py without factory function
        workflow_code = """
# Workflow module without factory function
def some_other_function():
    pass
"""
        (workflow_dir / "workflow.py").write_text(workflow_code)

        with patch("ai.workflows.registry.resolve_ai_root", return_value=ai_root):
            result = _discover_workflows()

        # Should skip workflow without factory function
        assert result == {}

    def test_discover_workflows_import_exception(self, tmp_path) -> None:
        """Test discovery handles import exceptions gracefully."""
        # Create AI root with workflow directory
        ai_root = tmp_path / "ai"
        workflows_dir = ai_root / "workflows"
        workflow_dir = workflows_dir / "broken-workflow"
        workflow_dir.mkdir(parents=True)

        # Create config.yaml
        (workflow_dir / "config.yaml").write_text("workflow:\n  workflow_id: broken\n")

        # Create workflow.py with syntax error to cause import failure
        workflow_code = """
# This will cause an import error
def get_broken_workflow_workflow():
    # Invalid syntax - missing closing parenthesis
    return Workflow(
        name="Broken"
"""
        (workflow_dir / "workflow.py").write_text(workflow_code)

        with patch("ai.workflows.registry.resolve_ai_root", return_value=ai_root):
            result = _discover_workflows()

        # Should gracefully skip workflow that fails to import
        assert result == {}

    def test_hyphen_to_underscore_conversion_logic(self) -> None:
        """Test that hyphens in workflow names are properly converted to underscores."""
        # Test the logic directly
        workflow_name = "multi-word-workflow"
        expected_func_name = f"get_{workflow_name.replace('-', '_')}_workflow"
        assert expected_func_name == "get_multi_word_workflow_workflow"


class TestWorkflowRegistry:
    """Test workflow registry functionality."""

    @patch("ai.workflows.registry._discover_workflows")
    def test_get_workflow_registry_lazy_initialization(self, mock_discover) -> None:
        """Test that workflow registry is lazily initialized."""
        # Reset the global registry
        import ai.workflows.registry

        ai.workflows.registry._WORKFLOW_REGISTRY = None

        mock_discover.return_value = {"test-workflow": Mock()}

        # First call should initialize
        registry1 = get_workflow_registry()
        mock_discover.assert_called_once()

        # Second call should use cached version
        registry2 = get_workflow_registry()
        mock_discover.assert_called_once()  # Still only called once

        assert registry1 is registry2

    @patch("ai.workflows.registry._discover_workflows")
    def test_get_workflow_success(self, mock_discover) -> None:
        """Test successful workflow retrieval."""
        mock_factory = Mock()
        mock_workflow = Mock()
        mock_factory.return_value = mock_workflow

        mock_discover.return_value = {"test-workflow": mock_factory}

        # Reset registry to force re-initialization
        import ai.workflows.registry

        ai.workflows.registry._WORKFLOW_REGISTRY = None

        result = get_workflow("test-workflow", version=1, param1="value1")

        assert result == mock_workflow
        mock_factory.assert_called_once_with(version=1, param1="value1")

    @patch("ai.workflows.registry._discover_workflows")
    def test_get_workflow_not_found(self, mock_discover) -> None:
        """Test workflow not found error."""
        mock_discover.return_value = {"workflow-1": Mock(), "workflow-2": Mock()}

        # Reset registry to force re-initialization
        import ai.workflows.registry

        ai.workflows.registry._WORKFLOW_REGISTRY = None

        with pytest.raises(ValueError, match="Workflow 'missing-workflow' not found"):
            get_workflow("missing-workflow")

    @patch("ai.workflows.registry._discover_workflows")
    def test_get_workflow_without_version(self, mock_discover) -> None:
        """Test workflow retrieval without version parameter."""
        mock_factory = Mock()
        mock_workflow = Mock()
        mock_factory.return_value = mock_workflow

        mock_discover.return_value = {"test-workflow": mock_factory}

        # Reset registry to force re-initialization
        import ai.workflows.registry

        ai.workflows.registry._WORKFLOW_REGISTRY = None

        result = get_workflow("test-workflow", param1="value1")

        assert result == mock_workflow
        mock_factory.assert_called_once_with(param1="value1")

    @patch("ai.workflows.registry._discover_workflows")
    def test_list_available_workflows(self, mock_discover) -> None:
        """Test listing available workflows."""
        mock_discover.return_value = {
            "workflow-b": Mock(),
            "workflow-a": Mock(),
            "workflow-c": Mock(),
        }

        # Reset registry to force re-initialization
        import ai.workflows.registry

        ai.workflows.registry._WORKFLOW_REGISTRY = None

        result = list_available_workflows()

        # Should be sorted alphabetically
        assert result == ["workflow-a", "workflow-b", "workflow-c"]

    @patch("ai.workflows.registry._discover_workflows")
    def test_list_available_workflows_empty(self, mock_discover) -> None:
        """Test listing available workflows when none exist."""
        mock_discover.return_value = {}

        # Reset registry to force re-initialization
        import ai.workflows.registry

        ai.workflows.registry._WORKFLOW_REGISTRY = None

        result = list_available_workflows()
        assert result == []

    @patch("ai.workflows.registry._discover_workflows")
    def test_is_workflow_registered_true(self, mock_discover) -> None:
        """Test checking if workflow is registered (positive case)."""
        mock_discover.return_value = {"existing-workflow": Mock()}

        # Reset registry to force re-initialization
        import ai.workflows.registry

        ai.workflows.registry._WORKFLOW_REGISTRY = None

        result = is_workflow_registered("existing-workflow")
        assert result is True

    @patch("ai.workflows.registry._discover_workflows")
    def test_is_workflow_registered_false(self, mock_discover) -> None:
        """Test checking if workflow is registered (negative case)."""
        mock_discover.return_value = {"existing-workflow": Mock()}

        # Reset registry to force re-initialization
        import ai.workflows.registry

        ai.workflows.registry._WORKFLOW_REGISTRY = None

        result = is_workflow_registered("non-existing-workflow")
        assert result is False

    @patch("ai.workflows.registry._discover_workflows")
    def test_workflow_registry_logging(self, mock_discover) -> None:
        """Test that appropriate logging occurs during registry initialization."""
        mock_discover.return_value = {"workflow-1": Mock(), "workflow-2": Mock()}

        # Reset registry to force re-initialization
        import ai.workflows.registry

        ai.workflows.registry._WORKFLOW_REGISTRY = None

        with patch("ai.workflows.registry.logger") as mock_logger:
            get_workflow_registry()

            # Should log debug messages twice (not info)
            assert mock_logger.debug.call_count == 2

            # Check log content - first debug call
            first_debug_call = mock_logger.debug.call_args_list[0][0][0]
            # Second debug call with keyword arguments
            second_debug_args = mock_logger.debug.call_args_list[1]

            assert "Initializing workflow registry" in first_debug_call
            assert "Workflow registry initialized" in second_debug_args[0][0]
            # Verify the workflow count was logged
            assert second_debug_args[1]["workflow_count"] == 2


if __name__ == "__main__":
    pytest.main([__file__])
