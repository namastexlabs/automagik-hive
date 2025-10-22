"""
Comprehensive test suite for workflow version parser module.

Tests AST-based version extraction from workflow __init__.py files, handling
missing files gracefully, parsing module-level metadata, validating workflow
directory structure, and discovering all workflows with version information.

This test suite drives the TDD RED phase implementation of:
- get_workflow_version_from_init(workflow_dir: Path) -> str
- get_workflow_metadata_from_init(workflow_dir: Path) -> dict
- validate_workflow_structure(workflow_dir: Path) -> dict
- discover_workflows_with_versions(workflows_dir: Path) -> dict
"""

import tempfile
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from lib.utils.workflow_version_parser import (
    WorkflowMetadataError,
    WorkflowStructureError,
    WorkflowVersionError,
    discover_workflows_with_versions,
    get_workflow_metadata_from_init,
    get_workflow_version_from_init,
    validate_workflow_structure,
)


class TestWorkflowVersionFromInit:
    """Test AST-based version extraction from workflow __init__.py files."""

    def test_extract_version_from_simple_numeric_assignment(self):
        """Test extraction of simple numeric __version__ assignment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "test-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text("__version__ = 1")

            version = get_workflow_version_from_init(workflow_dir)
            assert version == "1"

    def test_extract_version_from_string_assignment(self):
        """Test extraction of string __version__ assignment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "test-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text('__version__ = "2.1.0"')

            version = get_workflow_version_from_init(workflow_dir)
            assert version == "2.1.0"

    def test_extract_version_from_complex_init_file(self):
        """Test version extraction from complex __init__.py with multiple statements."""
        complex_init_content = textwrap.dedent('''
            """Complex workflow module."""
            
            import os
            from typing import Dict, Any
            
            # Metadata
            __version__ = "3.2.1"
            __author__ = "AutomagikHive Team"
            __description__ = "Advanced workflow processor"
            
            # Constants
            DEFAULT_CONFIG = {
                "timeout": 30,
                "retry_count": 3
            }
            
            def helper_function():
                pass
            
            class WorkflowProcessor:
                pass
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "complex-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(complex_init_content)

            version = get_workflow_version_from_init(workflow_dir)
            assert version == "3.2.1"

    def test_extract_version_with_single_quotes(self):
        """Test version extraction with single quotes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "test-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text("__version__ = '4.0.0-beta'")

            version = get_workflow_version_from_init(workflow_dir)
            assert version == "4.0.0-beta"

    def test_extract_version_with_triple_quotes(self):
        """Test version extraction with triple quotes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "test-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text('__version__ = """5.0.0"""')

            version = get_workflow_version_from_init(workflow_dir)
            assert version == "5.0.0"

    def test_extract_version_from_float_assignment(self):
        """Test extraction of float __version__ assignment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "test-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text("__version__ = 2.5")

            version = get_workflow_version_from_init(workflow_dir)
            assert version == "2.5"

    def test_version_extraction_handles_comments(self):
        """Test version extraction ignores comments and whitespace."""
        init_content_with_comments = textwrap.dedent('''
            # This is a comment
            # __version__ = "fake"
            
            """Module docstring."""
            
            # Real version below
            __version__ = "1.2.3"  # Version comment
            
            # More comments
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "commented-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(init_content_with_comments)

            version = get_workflow_version_from_init(workflow_dir)
            assert version == "1.2.3"

    def test_version_extraction_handles_unicode(self):
        """Test version extraction with unicode characters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "unicode-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text('__version__ = "1.0.0-α"', encoding="utf-8")

            version = get_workflow_version_from_init(workflow_dir)
            assert version == "1.0.0-α"

    def test_version_extraction_with_variable_assignment_expression(self):
        """Test version extraction with variable assignment expressions."""
        init_content = textwrap.dedent("""
            MAJOR = 2
            MINOR = 1
            PATCH = 0
            __version__ = f"{MAJOR}.{MINOR}.{PATCH}"
        """)

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "dynamic-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(init_content)

            # This should fail because it's a complex expression, not a simple literal
            with pytest.raises(WorkflowVersionError, match="Complex version assignment"):
                get_workflow_version_from_init(workflow_dir)

    def test_missing_init_file_returns_default(self):
        """Test handling of missing __init__.py file with default version."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "no-init-workflow"
            workflow_dir.mkdir()

            version = get_workflow_version_from_init(workflow_dir)
            assert version == "1.0.0"

    def test_init_file_without_version_returns_default(self):
        """Test handling of __init__.py without __version__ variable."""
        init_content = textwrap.dedent('''
            """Workflow module without version."""
            
            import os
            
            def some_function():
                pass
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "no-version-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(init_content)

            version = get_workflow_version_from_init(workflow_dir)
            assert version == "1.0.0"

    def test_empty_init_file_returns_default(self):
        """Test handling of empty __init__.py file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "empty-init-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text("")

            version = get_workflow_version_from_init(workflow_dir)
            assert version == "1.0.0"

    def test_invalid_syntax_init_file_raises_error(self):
        """Test handling of __init__.py with invalid Python syntax."""
        invalid_init_content = textwrap.dedent('''
            """Module with syntax error."""
            
            __version__ = "1.0.0
            # Missing closing quote
            
            def broken_function(:
                pass
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "broken-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(invalid_init_content)

            with pytest.raises(WorkflowVersionError, match="Failed to parse"):
                get_workflow_version_from_init(workflow_dir)

    def test_non_directory_path_raises_error(self):
        """Test error when workflow_dir is not a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "not-a-directory.txt"
            file_path.write_text("content")

            with pytest.raises(WorkflowVersionError, match="not a directory"):
                get_workflow_version_from_init(file_path)

    def test_nonexistent_directory_raises_error(self):
        """Test error when workflow directory doesn't exist."""
        nonexistent_path = Path("/nonexistent/workflow/directory")

        with pytest.raises(WorkflowVersionError, match="does not exist"):
            get_workflow_version_from_init(nonexistent_path)

    def test_permission_error_handling(self):
        """Test handling of permission errors when reading __init__.py."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "permission-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text('__version__ = "1.0.0"')

            # Mock at the open level which is what the actual function uses
            with patch("builtins.open", side_effect=PermissionError("Permission denied")):
                with pytest.raises(WorkflowVersionError, match="Permission denied"):
                    get_workflow_version_from_init(workflow_dir)

    def test_version_assignment_in_function_ignored(self):
        """Test that __version__ assignment inside functions is ignored."""
        init_content = textwrap.dedent('''
            """Module with version in function."""
            
            def setup():
                __version__ = "2.0.0"  # This should be ignored
                return "setup complete"
            
            __version__ = "1.5.0"  # This is the real version
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "function-version-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(init_content)

            version = get_workflow_version_from_init(workflow_dir)
            assert version == "1.5.0"

    def test_version_assignment_in_class_ignored(self):
        """Test that __version__ assignment inside classes is ignored."""
        init_content = textwrap.dedent('''
            """Module with version in class."""
            
            __version__ = "3.1.0"
            
            class WorkflowConfig:
                __version__ = "2.0.0"  # This should be ignored
                
                def __init__(self):
                    self.__version__ = "1.0.0"  # This should also be ignored
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "class-version-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(init_content)

            version = get_workflow_version_from_init(workflow_dir)
            assert version == "3.1.0"

    def test_multiple_version_assignments_uses_first(self):
        """Test that when multiple __version__ assignments exist, first one is used."""
        init_content = textwrap.dedent('''
            """Module with multiple version assignments."""
            
            __version__ = "1.0.0"  # First assignment
            
            # Some code here
            import os
            
            __version__ = "2.0.0"  # Second assignment (should be ignored)
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "multi-version-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(init_content)

            version = get_workflow_version_from_init(workflow_dir)
            assert version == "1.0.0"

    def test_version_with_augmented_assignment_fails(self):
        """Test that augmented assignment for __version__ raises error."""
        init_content = textwrap.dedent('''
            """Module with augmented assignment."""
            
            __version__ = "1.0.0"
            __version__ += "-dev"  # Augmented assignment
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "augmented-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(init_content)

            # Should still return the first assignment
            version = get_workflow_version_from_init(workflow_dir)
            assert version == "1.0.0"

    def test_version_extraction_performance_large_file(self):
        """Test version extraction performance with large __init__.py file."""
        # Create a large file with version at the beginning
        large_init_content = '__version__ = "1.0.0"\n'
        large_init_content += "\n".join([f"# Comment line {i}" for i in range(10000)])

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "large-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(large_init_content)

            import time

            start_time = time.time()
            version = get_workflow_version_from_init(workflow_dir)
            end_time = time.time()

            assert version == "1.0.0"
            # Should complete in reasonable time (less than 1 second)
            assert end_time - start_time < 1.0


class TestWorkflowMetadataFromInit:
    """Test extraction of module-level metadata from workflow __init__.py files."""

    def test_extract_basic_metadata(self):
        """Test extraction of basic metadata fields."""
        init_content = textwrap.dedent('''
            """Sample workflow module."""
            
            __version__ = "1.0.0"
            __author__ = "AutomagikHive Team"
            __description__ = "Sample workflow processor"
            __license__ = "MIT"
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "basic-metadata-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(init_content)

            metadata = get_workflow_metadata_from_init(workflow_dir)

            expected_metadata = {
                "__version__": "1.0.0",
                "__author__": "AutomagikHive Team",
                "__description__": "Sample workflow processor",
                "__license__": "MIT",
            }

            assert metadata == expected_metadata

    def test_extract_extended_metadata(self):
        """Test extraction of extended metadata fields."""
        init_content = textwrap.dedent('''
            """Extended workflow module."""
            
            __version__ = "2.1.0"
            __author__ = "John Doe <john@example.com>"
            __description__ = "Advanced workflow with extended features"
            __license__ = "Apache-2.0"
            __maintainer__ = "Jane Smith"
            __email__ = "maintainer@example.com"
            __url__ = "https://github.com/example/workflow"
            __status__ = "Production"
            __copyright__ = "2024 AutomagikHive"
            __credits__ = ["John Doe", "Jane Smith", "Bob Wilson"]
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "extended-metadata-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(init_content)

            metadata = get_workflow_metadata_from_init(workflow_dir)

            expected_metadata = {
                "__version__": "2.1.0",
                "__author__": "John Doe <john@example.com>",
                "__description__": "Advanced workflow with extended features",
                "__license__": "Apache-2.0",
                "__maintainer__": "Jane Smith",
                "__email__": "maintainer@example.com",
                "__url__": "https://github.com/example/workflow",
                "__status__": "Production",
                "__copyright__": "2024 AutomagikHive",
                "__credits__": ["John Doe", "Jane Smith", "Bob Wilson"],
            }

            assert metadata == expected_metadata

    def test_extract_metadata_with_mixed_quotes(self):
        """Test metadata extraction with mixed quote styles."""
        # Don't use dedent to preserve exact indentation
        init_content = """'''Mixed quotes workflow.'''

__version__ = "1.0.0"
__author__ = 'Single Quote Author'
__description__ = '''Triple quote description
that spans multiple lines.'''
__license__ = "Triple quote license"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "mixed-quotes-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(init_content)

            metadata = get_workflow_metadata_from_init(workflow_dir)

            expected_metadata = {
                "__version__": "1.0.0",
                "__author__": "Single Quote Author",
                "__description__": "Triple quote description\nthat spans multiple lines.",
                "__license__": "Triple quote license",
            }

            assert metadata == expected_metadata

    def test_extract_metadata_ignores_non_metadata_variables(self):
        """Test that only metadata variables are extracted."""
        init_content = textwrap.dedent('''
            """Workflow with mixed variables."""
            
            __version__ = "1.0.0"
            __author__ = "Test Author"
            
            # Non-metadata variables (should be ignored)
            CONFIG_FILE = "config.yaml"
            DEFAULT_TIMEOUT = 30
            _private_var = "private"
            public_var = "public"
            
            def some_function():
                pass
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "mixed-variables-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(init_content)

            metadata = get_workflow_metadata_from_init(workflow_dir)

            expected_metadata = {"__version__": "1.0.0", "__author__": "Test Author"}

            assert metadata == expected_metadata

    def test_extract_metadata_from_missing_init_file(self):
        """Test metadata extraction when __init__.py is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "no-init-workflow"
            workflow_dir.mkdir()

            metadata = get_workflow_metadata_from_init(workflow_dir)
            assert metadata == {"__version__": "1.0.0"}

    def test_extract_metadata_from_empty_init_file(self):
        """Test metadata extraction from empty __init__.py file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "empty-init-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text("")

            metadata = get_workflow_metadata_from_init(workflow_dir)
            assert metadata == {"__version__": "1.0.0"}

    def test_extract_metadata_handles_complex_expressions(self):
        """Test that complex expressions in metadata assignments raise errors."""
        init_content = textwrap.dedent('''
            """Workflow with complex expressions."""
            
            __version__ = "1.0.0"
            __author__ = "Simple Author"
            __description__ = f"Dynamic description with {__version__}"  # Complex expression
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "complex-expr-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(init_content)

            with pytest.raises(WorkflowMetadataError, match="Complex assignment"):
                get_workflow_metadata_from_init(workflow_dir)

    def test_extract_metadata_ignores_functions_and_classes(self):
        """Test that metadata inside functions and classes is ignored."""
        init_content = textwrap.dedent('''
            """Workflow with nested metadata."""
            
            __version__ = "1.0.0"
            __author__ = "Module Author"
            
            def setup():
                __version__ = "2.0.0"  # Should be ignored
                __author__ = "Function Author"  # Should be ignored
                
            class WorkflowConfig:
                __version__ = "3.0.0"  # Should be ignored
                __license__ = "Class License"  # Should be ignored
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "nested-metadata-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(init_content)

            metadata = get_workflow_metadata_from_init(workflow_dir)

            expected_metadata = {"__version__": "1.0.0", "__author__": "Module Author"}

            assert metadata == expected_metadata

    def test_extract_metadata_with_numeric_values(self):
        """Test metadata extraction with numeric and boolean values."""
        init_content = textwrap.dedent('''
            """Workflow with numeric metadata."""
            
            __version__ = 2
            __revision__ = 42
            __build__ = 1234567890
            __debug__ = True
            __stable__ = False
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "numeric-metadata-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(init_content)

            metadata = get_workflow_metadata_from_init(workflow_dir)

            expected_metadata = {
                "__version__": "2",
                "__revision__": "42",
                "__build__": "1234567890",
                "__debug__": "True",
                "__stable__": "False",
            }

            assert metadata == expected_metadata

    def test_extract_metadata_invalid_syntax_raises_error(self):
        """Test that invalid Python syntax in __init__.py raises error."""
        invalid_init_content = textwrap.dedent('''
            """Module with syntax error."""
            
            __version__ = "1.0.0
            __author__ = "Broken Author
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "broken-syntax-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(invalid_init_content)

            with pytest.raises(WorkflowMetadataError, match="Failed to parse"):
                get_workflow_metadata_from_init(workflow_dir)

    def test_extract_metadata_handles_list_values(self):
        """Test metadata extraction with list values."""
        init_content = textwrap.dedent('''
            """Workflow with list metadata."""
            
            __version__ = "1.0.0"
            __credits__ = ["John Doe", "Jane Smith", "Bob Wilson"]
            __keywords__ = ["workflow", "automation", "processing"]
            __supported_formats__ = ["json", "yaml", "xml"]
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "list-metadata-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(init_content)

            metadata = get_workflow_metadata_from_init(workflow_dir)

            expected_metadata = {
                "__version__": "1.0.0",
                "__credits__": ["John Doe", "Jane Smith", "Bob Wilson"],
                "__keywords__": ["workflow", "automation", "processing"],
                "__supported_formats__": ["json", "yaml", "xml"],
            }

            assert metadata == expected_metadata

    def test_extract_metadata_handles_dict_values(self):
        """Test metadata extraction with dictionary values."""
        init_content = textwrap.dedent('''
            """Workflow with dict metadata."""
            
            __version__ = "1.0.0"
            __config__ = {"timeout": 30, "retry_count": 3}
            __dependencies__ = {"python": ">=3.8", "pydantic": ">=1.0"}
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "dict-metadata-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(init_content)

            metadata = get_workflow_metadata_from_init(workflow_dir)

            expected_metadata = {
                "__version__": "1.0.0",
                "__config__": {"timeout": 30, "retry_count": 3},
                "__dependencies__": {"python": ">=3.8", "pydantic": ">=1.0"},
            }

            assert metadata == expected_metadata


class TestValidateWorkflowStructure:
    """Test validation of workflow directory structure."""

    def test_validate_complete_workflow_structure(self):
        """Test validation of complete workflow with all required files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "complete-workflow"
            workflow_dir.mkdir()

            # Create all required files
            (workflow_dir / "__init__.py").write_text('__version__ = "1.0.0"')
            (workflow_dir / "workflow.py").write_text("# Workflow implementation")
            (workflow_dir / "config.yaml").write_text("# Workflow configuration")

            result = validate_workflow_structure(workflow_dir)

            expected_result = {
                "valid": True,
                "has_init": True,
                "has_workflow": True,
                "has_config": True,
                "init_version": "1.0.0",
                "missing_files": [],
                "extra_files": [],
                "errors": [],
            }

            assert result == expected_result

    def test_validate_minimal_workflow_structure(self):
        """Test validation of minimal workflow with only __init__.py."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "minimal-workflow"
            workflow_dir.mkdir()

            (workflow_dir / "__init__.py").write_text('__version__ = "1.0.0"')

            result = validate_workflow_structure(workflow_dir)

            expected_result = {
                "valid": False,
                "has_init": True,
                "has_workflow": False,
                "has_config": False,
                "init_version": "1.0.0",
                "missing_files": ["workflow.py", "config.yaml"],
                "extra_files": [],
                "errors": ["Missing required file: workflow.py", "Missing required file: config.yaml"],
            }

            assert result == expected_result

    def test_validate_workflow_with_missing_init(self):
        """Test validation of workflow missing __init__.py."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "no-init-workflow"
            workflow_dir.mkdir()

            (workflow_dir / "workflow.py").write_text("# Workflow implementation")
            (workflow_dir / "config.yaml").write_text("# Workflow configuration")

            result = validate_workflow_structure(workflow_dir)

            expected_result = {
                "valid": False,
                "has_init": False,
                "has_workflow": True,
                "has_config": True,
                "init_version": "1.0.0",  # Default version
                "missing_files": ["__init__.py"],
                "extra_files": [],
                "errors": ["Missing required file: __init__.py"],
            }

            assert result == expected_result

    def test_validate_workflow_with_extra_files(self):
        """Test validation of workflow with extra files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "extra-files-workflow"
            workflow_dir.mkdir()

            # Create required files
            (workflow_dir / "__init__.py").write_text('__version__ = "1.0.0"')
            (workflow_dir / "workflow.py").write_text("# Workflow implementation")
            (workflow_dir / "config.yaml").write_text("# Workflow configuration")

            # Create extra files
            (workflow_dir / "README.md").write_text("# Workflow README")
            (workflow_dir / "tests.py").write_text("# Test file")
            (workflow_dir / "utils.py").write_text("# Utility functions")

            result = validate_workflow_structure(workflow_dir)

            expected_result = {
                "valid": True,
                "has_init": True,
                "has_workflow": True,
                "has_config": True,
                "init_version": "1.0.0",
                "missing_files": [],
                "extra_files": ["README.md", "tests.py", "utils.py"],
                "errors": [],
            }

            assert result == expected_result

    def test_validate_empty_workflow_directory(self):
        """Test validation of completely empty workflow directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "empty-workflow"
            workflow_dir.mkdir()

            result = validate_workflow_structure(workflow_dir)

            expected_result = {
                "valid": False,
                "has_init": False,
                "has_workflow": False,
                "has_config": False,
                "init_version": "1.0.0",  # Default version
                "missing_files": ["__init__.py", "workflow.py", "config.yaml"],
                "extra_files": [],
                "errors": [
                    "Missing required file: __init__.py",
                    "Missing required file: workflow.py",
                    "Missing required file: config.yaml",
                ],
            }

            assert result == expected_result

    def test_validate_nonexistent_workflow_directory(self):
        """Test validation of non-existent workflow directory."""
        nonexistent_path = Path("/nonexistent/workflow/directory")

        with pytest.raises(WorkflowStructureError, match="does not exist"):
            validate_workflow_structure(nonexistent_path)

    def test_validate_file_instead_of_directory(self):
        """Test validation when path points to a file instead of directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "not-a-directory.txt"
            file_path.write_text("content")

            with pytest.raises(WorkflowStructureError, match="not a directory"):
                validate_workflow_structure(file_path)

    def test_validate_workflow_with_subdirectories(self):
        """Test validation of workflow with subdirectories (should be in extra_files)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "subdir-workflow"
            workflow_dir.mkdir()

            # Create required files
            (workflow_dir / "__init__.py").write_text('__version__ = "1.0.0"')
            (workflow_dir / "workflow.py").write_text("# Workflow implementation")
            (workflow_dir / "config.yaml").write_text("# Workflow configuration")

            # Create subdirectories
            (workflow_dir / "tests").mkdir()
            (workflow_dir / "docs").mkdir()
            (workflow_dir / "assets").mkdir()

            result = validate_workflow_structure(workflow_dir)

            expected_result = {
                "valid": True,
                "has_init": True,
                "has_workflow": True,
                "has_config": True,
                "init_version": "1.0.0",
                "missing_files": [],
                "extra_files": ["assets", "docs", "tests"],
                "errors": [],
            }

            assert result == expected_result

    def test_validate_workflow_handles_permission_errors(self):
        """Test validation handles permission errors gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "permission-workflow"
            workflow_dir.mkdir()

            with patch("pathlib.Path.iterdir", side_effect=PermissionError("Permission denied")):
                with pytest.raises(WorkflowStructureError, match="Permission denied"):
                    validate_workflow_structure(workflow_dir)

    def test_validate_workflow_with_broken_init_file(self):
        """Test validation with broken __init__.py file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "broken-init-workflow"
            workflow_dir.mkdir()

            # Create required files
            (workflow_dir / "__init__.py").write_text('__version__ = "1.0.0')  # Syntax error
            (workflow_dir / "workflow.py").write_text("# Workflow implementation")
            (workflow_dir / "config.yaml").write_text("# Workflow configuration")

            result = validate_workflow_structure(workflow_dir)

            # Should still validate structure but note version parsing error
            assert result["valid"] is True
            assert result["has_init"] is True
            assert result["has_workflow"] is True
            assert result["has_config"] is True
            assert result["init_version"] == "1.0.0"  # Should fallback to default
            assert "Failed to parse version" in str(result.get("errors", []))

    def test_validate_workflow_structure_case_sensitive_files(self):
        """Test validation is case-sensitive for required files."""
        import platform

        # Skip test on case-insensitive filesystems (default macOS HFS+/APFS)
        if platform.system() == "Darwin":
            pytest.skip("macOS filesystem is typically case-insensitive")

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "case-sensitive-workflow"
            workflow_dir.mkdir()

            # Create files with wrong case
            (workflow_dir / "__INIT__.py").write_text('__version__ = "1.0.0"')
            (workflow_dir / "WORKFLOW.py").write_text("# Workflow implementation")
            (workflow_dir / "CONFIG.yaml").write_text("# Workflow configuration")

            result = validate_workflow_structure(workflow_dir)

            expected_result = {
                "valid": False,
                "has_init": False,
                "has_workflow": False,
                "has_config": False,
                "init_version": "1.0.0",  # Default
                "missing_files": ["__init__.py", "workflow.py", "config.yaml"],
                "extra_files": ["CONFIG.yaml", "WORKFLOW.py", "__INIT__.py"],
                "errors": [
                    "Missing required file: __init__.py",
                    "Missing required file: workflow.py",
                    "Missing required file: config.yaml",
                ],
            }

            assert result == expected_result


class TestDiscoverWorkflowsWithVersions:
    """Test discovery of all workflows with version information."""

    def test_discover_single_workflow(self):
        """Test discovery of single workflow in directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflows_dir = Path(temp_dir)

            # Create single workflow
            workflow_dir = workflows_dir / "sample-workflow"
            workflow_dir.mkdir()
            (workflow_dir / "__init__.py").write_text('__version__ = "1.0.0"')
            (workflow_dir / "workflow.py").write_text("# Implementation")
            (workflow_dir / "config.yaml").write_text("# Configuration")

            result = discover_workflows_with_versions(workflows_dir)

            expected_result = {
                "sample-workflow": {
                    "path": str(workflow_dir),
                    "version": "1.0.0",
                    "valid": True,
                    "metadata": {"__version__": "1.0.0"},
                    "structure": {
                        "valid": True,
                        "has_init": True,
                        "has_workflow": True,
                        "has_config": True,
                        "init_version": "1.0.0",
                        "missing_files": [],
                        "extra_files": [],
                        "errors": [],
                    },
                }
            }

            assert result == expected_result

    def test_discover_multiple_workflows(self):
        """Test discovery of multiple workflows in directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflows_dir = Path(temp_dir)

            # Create multiple workflows
            for i, name in enumerate(["workflow-alpha", "workflow-beta", "workflow-gamma"]):
                workflow_dir = workflows_dir / name
                workflow_dir.mkdir()
                (workflow_dir / "__init__.py").write_text(f'__version__ = "{i + 1}.0.0"')
                (workflow_dir / "workflow.py").write_text(f"# {name} implementation")
                (workflow_dir / "config.yaml").write_text(f"# {name} configuration")

            result = discover_workflows_with_versions(workflows_dir)

            assert len(result) == 3
            assert "workflow-alpha" in result
            assert "workflow-beta" in result
            assert "workflow-gamma" in result

            assert result["workflow-alpha"]["version"] == "1.0.0"
            assert result["workflow-beta"]["version"] == "2.0.0"
            assert result["workflow-gamma"]["version"] == "3.0.0"

            for workflow_name in result:
                assert result[workflow_name]["valid"] is True
                assert result[workflow_name]["structure"]["valid"] is True

    def test_discover_workflows_with_mixed_validity(self):
        """Test discovery of workflows with mixed validity states."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflows_dir = Path(temp_dir)

            # Create valid workflow
            valid_workflow = workflows_dir / "valid-workflow"
            valid_workflow.mkdir()
            (valid_workflow / "__init__.py").write_text('__version__ = "1.0.0"')
            (valid_workflow / "workflow.py").write_text("# Implementation")
            (valid_workflow / "config.yaml").write_text("# Configuration")

            # Create incomplete workflow
            incomplete_workflow = workflows_dir / "incomplete-workflow"
            incomplete_workflow.mkdir()
            (incomplete_workflow / "__init__.py").write_text('__version__ = "2.0.0"')
            # Missing workflow.py and config.yaml

            # Create workflow with no init
            no_init_workflow = workflows_dir / "no-init-workflow"
            no_init_workflow.mkdir()
            (no_init_workflow / "workflow.py").write_text("# Implementation")
            (no_init_workflow / "config.yaml").write_text("# Configuration")

            result = discover_workflows_with_versions(workflows_dir)

            assert len(result) == 3

            # Valid workflow
            assert result["valid-workflow"]["valid"] is True
            assert result["valid-workflow"]["version"] == "1.0.0"
            assert result["valid-workflow"]["structure"]["valid"] is True

            # Incomplete workflow
            assert result["incomplete-workflow"]["valid"] is False
            assert result["incomplete-workflow"]["version"] == "2.0.0"
            assert result["incomplete-workflow"]["structure"]["valid"] is False
            assert "workflow.py" in result["incomplete-workflow"]["structure"]["missing_files"]
            assert "config.yaml" in result["incomplete-workflow"]["structure"]["missing_files"]

            # No init workflow
            assert result["no-init-workflow"]["valid"] is False
            assert result["no-init-workflow"]["version"] == "1.0.0"  # Default
            assert result["no-init-workflow"]["structure"]["valid"] is False
            assert "__init__.py" in result["no-init-workflow"]["structure"]["missing_files"]

    def test_discover_workflows_ignores_non_directories(self):
        """Test that discovery ignores files and only processes directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflows_dir = Path(temp_dir)

            # Create valid workflow directory
            workflow_dir = workflows_dir / "real-workflow"
            workflow_dir.mkdir()
            (workflow_dir / "__init__.py").write_text('__version__ = "1.0.0"')
            (workflow_dir / "workflow.py").write_text("# Implementation")
            (workflow_dir / "config.yaml").write_text("# Configuration")

            # Create files that should be ignored
            (workflows_dir / "README.md").write_text("# Not a workflow")
            (workflows_dir / "setup.py").write_text("# Setup script")
            (workflows_dir / "requirements.txt").write_text("# Dependencies")

            result = discover_workflows_with_versions(workflows_dir)

            assert len(result) == 1
            assert "real-workflow" in result
            assert result["real-workflow"]["valid"] is True

    def test_discover_workflows_handles_hidden_directories(self):
        """Test that discovery handles hidden directories appropriately."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflows_dir = Path(temp_dir)

            # Create regular workflow
            workflow_dir = workflows_dir / "regular-workflow"
            workflow_dir.mkdir()
            (workflow_dir / "__init__.py").write_text('__version__ = "1.0.0"')
            (workflow_dir / "workflow.py").write_text("# Implementation")
            (workflow_dir / "config.yaml").write_text("# Configuration")

            # Create hidden directory (should be ignored)
            hidden_dir = workflows_dir / ".hidden-workflow"
            hidden_dir.mkdir()
            (hidden_dir / "__init__.py").write_text('__version__ = "2.0.0"')

            result = discover_workflows_with_versions(workflows_dir)

            assert len(result) == 1
            assert "regular-workflow" in result
            assert ".hidden-workflow" not in result

    def test_discover_workflows_from_empty_directory(self):
        """Test discovery from empty workflows directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflows_dir = Path(temp_dir)

            result = discover_workflows_with_versions(workflows_dir)
            assert result == {}

    def test_discover_workflows_from_nonexistent_directory(self):
        """Test discovery from non-existent directory raises error."""
        nonexistent_path = Path("/nonexistent/workflows/directory")

        with pytest.raises(WorkflowStructureError, match="does not exist"):
            discover_workflows_with_versions(nonexistent_path)

    def test_discover_workflows_from_file_path(self):
        """Test that discovery from file path raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "not-a-directory.txt"
            file_path.write_text("content")

            with pytest.raises(WorkflowStructureError, match="not a directory"):
                discover_workflows_with_versions(file_path)

    def test_discover_workflows_handles_permission_errors(self):
        """Test discovery handles permission errors gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflows_dir = Path(temp_dir)

            with patch("pathlib.Path.iterdir", side_effect=PermissionError("Permission denied")):
                with pytest.raises(WorkflowStructureError, match="Permission denied"):
                    discover_workflows_with_versions(workflows_dir)

    def test_discover_workflows_with_complex_metadata(self):
        """Test discovery of workflows with complex metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflows_dir = Path(temp_dir)

            # Create workflow with rich metadata
            workflow_dir = workflows_dir / "complex-metadata-workflow"
            workflow_dir.mkdir()

            complex_init = textwrap.dedent('''
                """Complex workflow with rich metadata."""
                
                __version__ = "2.1.0"
                __author__ = "AutomagikHive Team"
                __description__ = "Advanced workflow processor with AI capabilities"
                __license__ = "MIT"
                __maintainer__ = "John Doe"
                __email__ = "john@automagikhive.com"
                __url__ = "https://github.com/automagikhive/workflow"
                __status__ = "Production"
                __credits__ = ["Alice", "Bob", "Charlie"]
                __keywords__ = ["workflow", "ai", "automation"]
            ''')

            (workflow_dir / "__init__.py").write_text(complex_init)
            (workflow_dir / "workflow.py").write_text("# Implementation")
            (workflow_dir / "config.yaml").write_text("# Configuration")

            result = discover_workflows_with_versions(workflows_dir)

            workflow_info = result["complex-metadata-workflow"]
            assert workflow_info["version"] == "2.1.0"
            assert workflow_info["valid"] is True

            metadata = workflow_info["metadata"]
            assert metadata["__author__"] == "AutomagikHive Team"
            assert metadata["__description__"] == "Advanced workflow processor with AI capabilities"
            assert metadata["__license__"] == "MIT"
            assert metadata["__credits__"] == ["Alice", "Bob", "Charlie"]
            assert metadata["__keywords__"] == ["workflow", "ai", "automation"]

    def test_discover_workflows_performance_with_many_workflows(self):
        """Test discovery performance with many workflow directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflows_dir = Path(temp_dir)

            # Create many workflows
            num_workflows = 100
            for i in range(num_workflows):
                workflow_dir = workflows_dir / f"workflow-{i:03d}"
                workflow_dir.mkdir()
                (workflow_dir / "__init__.py").write_text(f'__version__ = "1.{i}.0"')
                (workflow_dir / "workflow.py").write_text(f"# Workflow {i}")
                (workflow_dir / "config.yaml").write_text(f"# Config {i}")

            import time

            start_time = time.time()
            result = discover_workflows_with_versions(workflows_dir)
            end_time = time.time()

            assert len(result) == num_workflows

            # Should complete in reasonable time (less than 5 seconds)
            assert end_time - start_time < 5.0

            # Verify random sampling
            assert result["workflow-050"]["version"] == "1.50.0"
            assert result["workflow-099"]["version"] == "1.99.0"

    def test_discover_workflows_sorts_results_alphabetically(self):
        """Test that discovery results are sorted alphabetically by workflow name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflows_dir = Path(temp_dir)

            # Create workflows in random order
            workflow_names = ["zebra-workflow", "alpha-workflow", "beta-workflow", "charlie-workflow"]
            for name in workflow_names:
                workflow_dir = workflows_dir / name
                workflow_dir.mkdir()
                (workflow_dir / "__init__.py").write_text('__version__ = "1.0.0"')
                (workflow_dir / "workflow.py").write_text("# Implementation")
                (workflow_dir / "config.yaml").write_text("# Configuration")

            result = discover_workflows_with_versions(workflows_dir)

            # Dictionary should maintain order in Python 3.7+
            result_keys = list(result.keys())
            expected_order = ["alpha-workflow", "beta-workflow", "charlie-workflow", "zebra-workflow"]
            assert result_keys == expected_order


class TestWorkflowParserExceptions:
    """Test custom exceptions for workflow version parser."""

    def test_workflow_version_error_creation(self):
        """Test WorkflowVersionError exception creation."""
        error = WorkflowVersionError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_workflow_metadata_error_creation(self):
        """Test WorkflowMetadataError exception creation."""
        error = WorkflowMetadataError("Metadata error message")
        assert str(error) == "Metadata error message"
        assert isinstance(error, Exception)

    def test_workflow_structure_error_creation(self):
        """Test WorkflowStructureError exception creation."""
        error = WorkflowStructureError("Structure error message")
        assert str(error) == "Structure error message"
        assert isinstance(error, Exception)


class TestWorkflowParserEdgeCases:
    """Test edge cases and boundary conditions for workflow version parser."""

    def test_workflow_with_very_long_version_string(self):
        """Test handling of extremely long version strings."""
        long_version = "1.0.0-" + "a" * 1000  # Very long version string

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "long-version-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(f'__version__ = "{long_version}"')

            version = get_workflow_version_from_init(workflow_dir)
            assert version == long_version

    def test_workflow_with_unicode_in_path(self):
        """Test handling of Unicode characters in workflow directory path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "workflow-ñ-测试"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text('__version__ = "1.0.0-unicode"', encoding="utf-8")

            version = get_workflow_version_from_init(workflow_dir)
            assert version == "1.0.0-unicode"

    def test_workflow_with_special_characters_in_metadata(self):
        """Test handling of special characters in metadata values."""
        special_metadata = textwrap.dedent('''
            """Workflow with special characters."""
            
            __version__ = "1.0.0"
            __author__ = "John Doe <john@example.com> & Team"
            __description__ = "Workflow with special chars: !@#$%^&*()[]{}|;:,.<>?"
            __license__ = "MIT/Apache-2.0"
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "special-chars-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(special_metadata, encoding="utf-8")

            metadata = get_workflow_metadata_from_init(workflow_dir)

            assert metadata["__author__"] == "John Doe <john@example.com> & Team"
            assert metadata["__description__"] == "Workflow with special chars: !@#$%^&*()[]{}|;:,.<>?"
            assert metadata["__license__"] == "MIT/Apache-2.0"

    def test_workflow_with_nested_quotes_in_strings(self):
        """Test handling of nested quotes in string values."""
        nested_quotes_content = textwrap.dedent('''
            """Workflow with nested quotes."""
            
            __version__ = "1.0.0"
            __description__ = "This workflow has 'single quotes' inside"
            __license__ = 'This license has "double quotes" inside'
            __notes__ = """This note has both 'single' and "double" quotes"""
        ''')

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / "nested-quotes-workflow"
            workflow_dir.mkdir()

            init_file = workflow_dir / "__init__.py"
            init_file.write_text(nested_quotes_content)

            metadata = get_workflow_metadata_from_init(workflow_dir)

            assert metadata["__description__"] == "This workflow has 'single quotes' inside"
            assert metadata["__license__"] == 'This license has "double quotes" inside'
            assert metadata["__notes__"] == """This note has both 'single' and "double" quotes"""

    def test_workflow_directory_with_symlinks(self):
        """Test handling of symbolic links in workflow directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create actual workflow
            real_workflow = Path(temp_dir) / "real-workflow"
            real_workflow.mkdir()
            (real_workflow / "__init__.py").write_text('__version__ = "1.0.0"')
            (real_workflow / "workflow.py").write_text("# Implementation")
            (real_workflow / "config.yaml").write_text("# Configuration")

            # Create symlink to workflow (Unix-like systems only)
            try:
                symlink_workflow = Path(temp_dir) / "symlink-workflow"
                symlink_workflow.symlink_to(real_workflow)

                # Test that symlinked workflow is handled correctly
                result = validate_workflow_structure(symlink_workflow)
                assert result["valid"] is True
                assert result["init_version"] == "1.0.0"

            except (OSError, NotImplementedError):
                # Skip test on systems that don't support symlinks
                pytest.skip("Symbolic links not supported on this system")

    def test_concurrent_workflow_discovery(self):
        """Test concurrent access to workflow discovery functions."""
        import queue
        import threading

        with tempfile.TemporaryDirectory() as temp_dir:
            workflows_dir = Path(temp_dir)

            # Create test workflows
            for i in range(10):
                workflow_dir = workflows_dir / f"concurrent-workflow-{i}"
                workflow_dir.mkdir()
                (workflow_dir / "__init__.py").write_text(f'__version__ = "1.{i}.0"')
                (workflow_dir / "workflow.py").write_text("# Implementation")
                (workflow_dir / "config.yaml").write_text("# Configuration")

            # Test concurrent discovery
            results_queue = queue.Queue()

            def discover_worker():
                result = discover_workflows_with_versions(workflows_dir)
                results_queue.put(result)

            threads = []
            for _ in range(5):  # 5 concurrent threads
                thread = threading.Thread(target=discover_worker)
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            # Verify all results are consistent
            results = []
            while not results_queue.empty():
                results.append(results_queue.get())

            assert len(results) == 5

            # All results should be identical
            first_result = results[0]
            for result in results[1:]:
                assert result == first_result

            assert len(first_result) == 10

    def test_workflow_discovery_memory_usage_large_files(self):
        """Test memory usage with workflows containing large __init__.py files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflows_dir = Path(temp_dir)

            # Create workflow with large __init__.py
            workflow_dir = workflows_dir / "large-init-workflow"
            workflow_dir.mkdir()

            # Create large content (but version at the top for efficiency)
            large_content = '__version__ = "1.0.0"\n'
            large_content += "# " + "Large comment content. " * 10000

            (workflow_dir / "__init__.py").write_text(large_content)
            (workflow_dir / "workflow.py").write_text("# Implementation")
            (workflow_dir / "config.yaml").write_text("# Configuration")

            # This should still work efficiently
            result = discover_workflows_with_versions(workflows_dir)

            assert len(result) == 1
            assert result["large-init-workflow"]["version"] == "1.0.0"
            assert result["large-init-workflow"]["valid"] is True
