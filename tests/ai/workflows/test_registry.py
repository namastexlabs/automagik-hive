"""
Tests for ai/workflows/registry.py - Workflow Registry and factory functions
"""

from unittest.mock import MagicMock, Mock, patch

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

    @patch("ai.workflows.registry.Path")
    def test_discover_workflows_no_directory(self, mock_path) -> None:
        """Test discovery when workflows directory doesn't exist."""
        mock_workflows_dir = Mock()
        mock_workflows_dir.exists.return_value = False
        mock_path.return_value = mock_workflows_dir

        result = _discover_workflows()
        assert result == {}

    def test_discover_workflows_success_integration(self) -> None:
        """Test successful workflow discovery using integration approach."""
        # Test that the function can be called without error
        result = _discover_workflows()
        assert isinstance(result, dict)
        # The result could be empty or contain actual workflows

    @patch("ai.workflows.registry.Path")
    def test_discover_workflows_skips_files(self, mock_path) -> None:
        """Test that discovery skips files and only processes directories."""
        mock_workflows_dir = MagicMock()
        mock_workflows_dir.exists.return_value = True

        mock_file = MagicMock()
        mock_file.is_dir.return_value = False

        mock_workflows_dir.iterdir.return_value = [mock_file]
        mock_path.return_value = mock_workflows_dir

        result = _discover_workflows()
        assert result == {}

    @patch("ai.workflows.registry.Path")
    def test_discover_workflows_skips_underscore_dirs(self, mock_path) -> None:
        """Test that discovery skips directories starting with underscore."""
        mock_workflows_dir = MagicMock()
        mock_workflows_dir.exists.return_value = True

        mock_private_dir = MagicMock()
        mock_private_dir.is_dir.return_value = True
        mock_private_dir.name = "_private-workflow"

        mock_workflows_dir.iterdir.return_value = [mock_private_dir]
        mock_path.return_value = mock_workflows_dir

        result = _discover_workflows()
        assert result == {}

    @patch("ai.workflows.registry.Path")
    def test_discover_workflows_missing_config(self, mock_path) -> None:
        """Test workflow discovery when config.yaml is missing."""
        mock_workflows_dir = MagicMock()
        mock_workflows_dir.exists.return_value = True

        mock_workflow_dir = MagicMock()
        mock_workflow_dir.is_dir.return_value = True
        mock_workflow_dir.name = "incomplete-workflow"

        mock_config_file = MagicMock()
        mock_workflow_file = MagicMock()
        mock_config_file.exists.return_value = False  # Missing config
        mock_workflow_file.exists.return_value = True

        mock_workflow_dir.__truediv__.side_effect = (
            lambda x: mock_config_file if x == "config.yaml" else mock_workflow_file
        )

        mock_workflows_dir.iterdir.return_value = [mock_workflow_dir]
        mock_path.return_value = mock_workflows_dir

        result = _discover_workflows()
        assert result == {}

    @patch("ai.workflows.registry.Path")
    def test_discover_workflows_missing_workflow_file(self, mock_path) -> None:
        """Test workflow discovery when workflow.py is missing."""
        mock_workflows_dir = MagicMock()
        mock_workflows_dir.exists.return_value = True

        mock_workflow_dir = MagicMock()
        mock_workflow_dir.is_dir.return_value = True
        mock_workflow_dir.name = "incomplete-workflow"

        mock_config_file = MagicMock()
        mock_workflow_file = MagicMock()
        mock_config_file.exists.return_value = True
        mock_workflow_file.exists.return_value = False  # Missing workflow.py

        mock_workflow_dir.__truediv__.side_effect = (
            lambda x: mock_config_file if x == "config.yaml" else mock_workflow_file
        )

        mock_workflows_dir.iterdir.return_value = [mock_workflow_dir]
        mock_path.return_value = mock_workflows_dir

        result = _discover_workflows()
        assert result == {}

    @patch("ai.workflows.registry.importlib.util")
    @patch("ai.workflows.registry.Path")
    def test_discover_workflows_no_factory_function(
        self, mock_path, mock_importlib
    ) -> None:
        """Test discovery when workflow module has no factory function."""
        mock_workflows_dir = MagicMock()
        mock_workflows_dir.exists.return_value = True

        mock_workflow_dir = MagicMock()
        mock_workflow_dir.is_dir.return_value = True
        mock_workflow_dir.name = "no-factory-workflow"

        mock_config_file = MagicMock()
        mock_workflow_file = MagicMock()
        mock_config_file.exists.return_value = True
        mock_workflow_file.exists.return_value = True

        mock_workflow_dir.__truediv__.side_effect = (
            lambda x: mock_config_file if x == "config.yaml" else mock_workflow_file
        )

        mock_workflows_dir.iterdir.return_value = [mock_workflow_dir]
        mock_path.return_value = mock_workflows_dir

        # Mock module loading
        mock_spec = Mock()
        mock_module = Mock()

        # Mock that the factory function doesn't exist
        def mock_hasattr(obj, name):
            return False  # No factory function found

        with patch("builtins.hasattr", side_effect=mock_hasattr):
            mock_importlib.spec_from_file_location.return_value = mock_spec
            mock_importlib.module_from_spec.return_value = mock_module

            result = _discover_workflows()

        assert result == {}

    @patch("ai.workflows.registry.importlib.util")
    @patch("ai.workflows.registry.Path")
    def test_discover_workflows_import_exception(
        self, mock_path, mock_importlib
    ) -> None:
        """Test discovery handles import exceptions gracefully."""
        mock_workflows_dir = MagicMock()
        mock_workflows_dir.exists.return_value = True

        mock_workflow_dir = MagicMock()
        mock_workflow_dir.is_dir.return_value = True
        mock_workflow_dir.name = "broken-workflow"

        mock_config_file = MagicMock()
        mock_workflow_file = MagicMock()
        mock_config_file.exists.return_value = True
        mock_workflow_file.exists.return_value = True

        mock_workflow_dir.__truediv__.side_effect = (
            lambda x: mock_config_file if x == "config.yaml" else mock_workflow_file
        )

        mock_workflows_dir.iterdir.return_value = [mock_workflow_dir]
        mock_path.return_value = mock_workflows_dir

        # Mock import failure
        mock_importlib.spec_from_file_location.side_effect = ImportError(
            "Failed to import",
        )

        result = _discover_workflows()
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

            # Should log debug and info messages
            mock_logger.debug.assert_called_once()
            mock_logger.info.assert_called_once()

            # Check log content
            debug_call = mock_logger.debug.call_args[0][0]
            info_call = mock_logger.info.call_args[0][0]

            assert "Initializing workflow registry" in debug_call
            assert "Workflow registry initialized" in info_call


if __name__ == "__main__":
    pytest.main([__file__])
