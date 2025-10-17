"""
Workflow Version Parser

Extracts version information from workflow __init__.py files using AST parsing
to avoid import side-effects. This replaces YAML-based version discovery for workflows.
"""

import ast
from pathlib import Path
from typing import Any

from lib.logging import logger


class WorkflowVersionError(Exception):
    """Exception raised when workflow version cannot be extracted."""

    pass


class WorkflowMetadataError(Exception):
    """Exception raised when workflow metadata cannot be parsed."""

    pass


class WorkflowStructureError(Exception):
    """Exception raised when workflow directory structure is invalid."""

    pass


def get_workflow_version_from_init(workflow_dir: Path) -> str:
    """
    Extract version from workflow __init__.py using AST parsing.

    Args:
        workflow_dir: Path to workflow directory (e.g., ai/workflows/template-workflow)

    Returns:
        Version string (defaults to "1.0.0" if not found)

    Raises:
        WorkflowVersionError: If critical error occurs during version extraction
    """
    # Validate workflow_dir
    if not workflow_dir.exists():
        raise WorkflowVersionError(f"Workflow directory does not exist: {workflow_dir}")

    if not workflow_dir.is_dir():
        raise WorkflowVersionError(f"Path is not a directory: {workflow_dir}")

    init_file = workflow_dir / "__init__.py"

    if not init_file.exists():
        logger.debug("No __init__.py found in workflow directory", workflow_dir=str(workflow_dir))
        return "1.0.0"  # Default version

    try:
        with open(init_file, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)

        # Add parent references for proper module-level detection
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                child.parent = parent

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "__version__"
            ):
                # Only accept module-level assignments (not in functions/classes)
                if hasattr(node, "parent") and isinstance(
                    node.parent, ast.FunctionDef | ast.ClassDef | ast.AsyncFunctionDef
                ):
                    continue

                # Check if it's a complex expression (f-string, function call, etc.)
                if isinstance(node.value, ast.JoinedStr | ast.Call | ast.BinOp):
                    raise WorkflowVersionError("Complex version assignment not supported - use simple literals only")

                try:
                    # Extract the version value
                    version = ast.literal_eval(node.value)
                    return str(version)  # Convert to string for consistency
                except (ValueError, TypeError):
                    # Non-literal expressions
                    raise WorkflowVersionError("Complex version assignment not supported - use simple literals only")

    except SyntaxError as e:
        logger.warning("Syntax error in workflow __init__.py", workflow_dir=str(workflow_dir), error=str(e))
        raise WorkflowVersionError(f"Failed to parse {init_file}: {e}")
    except (OSError, UnicodeDecodeError, PermissionError) as e:
        logger.error("Failed to read workflow __init__.py", workflow_dir=str(workflow_dir), error=str(e))
        raise WorkflowVersionError(f"Cannot read {init_file}: {e}")

    return "1.0.0"  # Fallback version if no __version__ found


def get_workflow_metadata_from_init(workflow_dir: Path) -> dict[str, Any]:
    """
    Extract all metadata from workflow __init__.py using AST parsing.

    Args:
        workflow_dir: Path to workflow directory

    Returns:
        Dictionary containing extracted metadata (version, description, etc.)

    Raises:
        WorkflowMetadataError: If critical error occurs during metadata extraction
    """
    init_file = workflow_dir / "__init__.py"
    metadata = {}

    if not init_file.exists():
        return {"__version__": "1.0.0"}

    try:
        with open(init_file, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)

        # Add parent references for module-level detection
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                child.parent = parent

        # Extract module-level assignments
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name):
                    # Only accept module-level assignments
                    if hasattr(node, "parent") and isinstance(
                        node.parent, ast.FunctionDef | ast.ClassDef | ast.AsyncFunctionDef
                    ):
                        continue

                    # Only extract metadata fields (those starting and ending with __)
                    if target.id.startswith("__") and target.id.endswith("__"):
                        # Check if it's a complex expression
                        if isinstance(node.value, ast.JoinedStr | ast.Call | ast.BinOp):
                            raise WorkflowMetadataError(
                                "Complex assignment not supported for metadata fields - use simple literals only"
                            )

                        try:
                            value = ast.literal_eval(node.value)
                            # Keep the full __key__ format
                            metadata[target.id] = str(value) if not isinstance(value, list | dict) else value
                        except (ValueError, TypeError):
                            # Non-literal expressions
                            raise WorkflowMetadataError(
                                "Complex assignment not supported for metadata fields - use simple literals only"
                            )

    except SyntaxError as e:
        logger.warning(
            "Syntax error in workflow __init__.py during metadata extraction",
            workflow_dir=str(workflow_dir),
            error=str(e),
        )
        raise WorkflowMetadataError(f"Failed to parse {init_file}: {e}")
    except (OSError, UnicodeDecodeError) as e:
        logger.error("Failed to read workflow __init__.py for metadata", workflow_dir=str(workflow_dir), error=str(e))
        raise WorkflowMetadataError(f"Cannot read {init_file}: {e}")

    # Return default if no metadata found
    if not metadata:
        return {"__version__": "1.0.0"}

    return metadata


def validate_workflow_structure(workflow_dir: Path) -> dict[str, Any]:
    """
    Validate that workflow directory has required structure for pure Python discovery.

    Args:
        workflow_dir: Path to workflow directory

    Returns:
        Dictionary with validation results and details

    Raises:
        WorkflowStructureError: If critical validation error occurs
    """
    if not workflow_dir.exists():
        raise WorkflowStructureError(f"Workflow directory does not exist: {workflow_dir}")

    if not workflow_dir.is_dir():
        raise WorkflowStructureError(f"Path is not a directory: {workflow_dir}")

    validation = {
        "valid": False,
        "has_init": False,
        "has_workflow": False,
        "has_config": False,
        "init_version": "1.0.0",
        "missing_files": [],
        "extra_files": [],
        "errors": [],
    }

    try:
        # Check for __init__.py
        init_file = workflow_dir / "__init__.py"
        validation["has_init"] = init_file.exists()
        if not validation["has_init"]:
            validation["missing_files"].append("__init__.py")
            validation["errors"].append("Missing required file: __init__.py")

        # Check for workflow.py
        workflow_file = workflow_dir / "workflow.py"
        validation["has_workflow"] = workflow_file.exists()
        if not validation["has_workflow"]:
            validation["missing_files"].append("workflow.py")
            validation["errors"].append("Missing required file: workflow.py")

        # Check for config.yaml
        config_file = workflow_dir / "config.yaml"
        validation["has_config"] = config_file.exists()
        if not validation["has_config"]:
            validation["missing_files"].append("config.yaml")
            validation["errors"].append("Missing required file: config.yaml")

        # Extract version from __init__.py
        if validation["has_init"]:
            try:
                version = get_workflow_version_from_init(workflow_dir)
                validation["init_version"] = version
            except WorkflowVersionError:
                # Keep default version but don't fail validation
                # Structure validation only checks file presence
                validation["errors"].append("Failed to parse version from __init__.py")

        # Find extra files (beyond required __init__.py, workflow.py, config.yaml)
        required_files = {"__init__.py", "workflow.py", "config.yaml"}

        for file_path in sorted(workflow_dir.iterdir()):
            filename = file_path.name
            # Skip hidden files and __pycache__
            if filename.startswith(".") or filename == "__pycache__":
                continue

            if filename not in required_files:
                validation["extra_files"].append(filename)

        # Overall structure validity - all required files must exist
        # Version parsing errors don't invalidate structure
        validation["valid"] = validation["has_init"] and validation["has_workflow"] and validation["has_config"]

    except PermissionError as e:
        logger.error(
            "Permission error during workflow structure validation", workflow_dir=str(workflow_dir), error=str(e)
        )
        raise WorkflowStructureError(f"Permission denied: {e}")
    except Exception as e:
        logger.error(
            "Unexpected error during workflow structure validation", workflow_dir=str(workflow_dir), error=str(e)
        )
        raise WorkflowStructureError(f"Validation failed for {workflow_dir}: {e}")

    return validation


def _has_version_constant(init_file: Path) -> bool:
    """Check if __init__.py contains a __version__ constant."""
    try:
        with open(init_file, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)

        # Add parent references
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                child.parent = parent

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "__version__"
            ):
                # Only accept module-level assignments
                if hasattr(node, "parent") and isinstance(
                    node.parent, ast.FunctionDef | ast.ClassDef | ast.AsyncFunctionDef
                ):
                    continue

                return True

    except Exception:  # noqa: S110 - Silent exception handling is intentional
        pass

    return False


def discover_workflows_with_versions(workflows_dir: Path) -> dict[str, dict[str, Any]]:
    """
    Discover all workflows with their version information.

    Args:
        workflows_dir: Path to workflows directory (e.g., ai/workflows)

    Returns:
        Dictionary mapping workflow names to their metadata

    Raises:
        WorkflowStructureError: If workflows directory doesn't exist or is not a directory
    """
    if not workflows_dir.exists():
        raise WorkflowStructureError(f"Workflows directory does not exist: {workflows_dir}")

    if not workflows_dir.is_dir():
        raise WorkflowStructureError(f"Path is not a directory: {workflows_dir}")

    workflows = {}

    try:
        for workflow_path in sorted(workflows_dir.iterdir()):
            # Skip non-directories and hidden directories
            if not workflow_path.is_dir() or workflow_path.name.startswith((".", "_")):
                continue

            workflow_name = workflow_path.name

            try:
                # Validate structure
                structure = validate_workflow_structure(workflow_path)

                # Extract metadata
                metadata = get_workflow_metadata_from_init(workflow_path)

                # Build workflow info
                workflow_info = {
                    "path": str(workflow_path),
                    "version": metadata.get("__version__", "1.0.0"),
                    "valid": structure["valid"],
                    "metadata": metadata,
                    "structure": structure,
                }

                workflows[workflow_name] = workflow_info

            except (WorkflowStructureError, WorkflowMetadataError) as e:
                logger.warning("Failed to process workflow", workflow_name=workflow_name, error=str(e))
                # Include failed workflow with error info
                workflows[workflow_name] = {
                    "path": str(workflow_path),
                    "version": "1.0.0",
                    "valid": False,
                    "error": str(e),
                }

    except PermissionError as e:
        logger.error("Permission error during workflow discovery", workflows_dir=str(workflows_dir), error=str(e))
        raise WorkflowStructureError(f"Permission denied: {e}")
    except Exception as e:
        logger.error("Unexpected error during workflow discovery", workflows_dir=str(workflows_dir), error=str(e))
        raise WorkflowStructureError(f"Discovery failed for {workflows_dir}: {e}")

    return workflows
