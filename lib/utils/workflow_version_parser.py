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
    init_file = workflow_dir / "__init__.py"
    
    if not init_file.exists():
        logger.debug(
            "No __init__.py found in workflow directory",
            workflow_dir=str(workflow_dir)
        )
        return "1"  # Default version
    
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content)
        
        # Add parent references for proper module-level detection
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                child.parent = parent
        
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign) and 
                len(node.targets) == 1 and
                isinstance(node.targets[0], ast.Name) and
                node.targets[0].id == '__version__'):
                
                # Only accept module-level assignments (not in functions/classes)
                if hasattr(node, 'parent') and isinstance(node.parent, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    continue
                
                try:
                    # Extract the version value
                    version = ast.literal_eval(node.value)
                    return str(version)  # Convert to string for consistency
                except (ValueError, TypeError):
                    # Skip non-literal expressions for security
                    continue
                
    except SyntaxError as e:
        logger.warning(
            "Syntax error in workflow __init__.py",
            workflow_dir=str(workflow_dir),
            error=str(e)
        )
        return "1"  # Fallback on syntax errors
    except (OSError, UnicodeDecodeError) as e:
        logger.error(
            "Failed to read workflow __init__.py",
            workflow_dir=str(workflow_dir),
            error=str(e)
        )
        raise WorkflowVersionError(f"Cannot read {init_file}: {e}")
    
    return "1"  # Fallback version if no __version__ found


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
    metadata = {
        'version': '1',
        'description': None,
        'author': None,
    }
    
    if not init_file.exists():
        return metadata
    
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content)
        
        # Add parent references for module-level detection
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                child.parent = parent
        
        # Extract docstring if present
        docstring = ast.get_docstring(tree)
        if docstring:
            metadata['description'] = docstring
        
        # Extract module-level assignments
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name):
                    # Only accept module-level assignments
                    if hasattr(node, 'parent') and isinstance(node.parent, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                        continue
                        
                    try:
                        value = ast.literal_eval(node.value)
                        # Handle special metadata fields
                        if target.id.startswith('__') and target.id.endswith('__'):
                            metadata[target.id[2:-2]] = value  # Remove __ prefix/suffix
                        else:
                            metadata[target.id] = value
                    except (ValueError, TypeError):
                        # Skip non-literal values for security
                        pass
                        
    except SyntaxError as e:
        logger.warning(
            "Syntax error in workflow __init__.py during metadata extraction",
            workflow_dir=str(workflow_dir),
            error=str(e)
        )
        # Return default metadata on syntax errors
        return metadata
    except (OSError, UnicodeDecodeError) as e:
        logger.error(
            "Failed to read workflow __init__.py for metadata",
            workflow_dir=str(workflow_dir),
            error=str(e)
        )
        raise WorkflowMetadataError(f"Cannot read {init_file}: {e}")
    
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
    validation = {
        'has_init': False,
        'has_workflow_py': False,
        'has_version': False,
        'valid_structure': False,
        'extra_files': [],
        'missing_files': [],
        'errors': []
    }
    
    if not workflow_dir.exists() or not workflow_dir.is_dir():
        raise WorkflowStructureError(f"Workflow directory does not exist or is not a directory: {workflow_dir}")
    
    try:
        # Check for __init__.py
        init_file = workflow_dir / "__init__.py"
        validation['has_init'] = init_file.exists()
        if not validation['has_init']:
            validation['missing_files'].append('__init__.py')
        
        # Check for workflow.py
        workflow_file = workflow_dir / "workflow.py"
        validation['has_workflow_py'] = workflow_file.exists()
        if not validation['has_workflow_py']:
            validation['missing_files'].append('workflow.py')
        
        # Check for version in __init__.py
        if validation['has_init']:
            try:
                version = get_workflow_version_from_init(workflow_dir)
                validation['has_version'] = version != "1" or _has_version_constant(init_file)
            except WorkflowVersionError:
                validation['has_version'] = False
                validation['errors'].append('Failed to extract version from __init__.py')
        else:
            validation['has_version'] = False
        
        # Find extra files (beyond required __init__.py, workflow.py, optional config.yaml)
        required_files = {'__init__.py', 'workflow.py'}
        optional_files = {'config.yaml'}
        
        for file_path in workflow_dir.iterdir():
            if file_path.is_file():
                filename = file_path.name
                if filename not in required_files and filename not in optional_files:
                    # Skip common development files
                    if not filename.startswith('.') and not filename.endswith('.pyc'):
                        validation['extra_files'].append(filename)
        
        # Overall structure validity
        validation['valid_structure'] = (
            validation['has_init'] and 
            validation['has_workflow_py'] and 
            validation['has_version'] and
            len(validation['errors']) == 0
        )
        
    except Exception as e:
        logger.error(
            "Unexpected error during workflow structure validation",
            workflow_dir=str(workflow_dir),
            error=str(e)
        )
        raise WorkflowStructureError(f"Validation failed for {workflow_dir}: {e}")
    
    return validation


def _has_version_constant(init_file: Path) -> bool:
    """Check if __init__.py contains a __version__ constant."""
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content)
        
        # Add parent references
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                child.parent = parent
        
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign) and 
                len(node.targets) == 1 and
                isinstance(node.targets[0], ast.Name) and
                node.targets[0].id == '__version__'):
                
                # Only accept module-level assignments
                if hasattr(node, 'parent') and isinstance(node.parent, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    continue
                    
                return True
                
    except Exception:
        pass
    
    return False


def discover_workflows_with_versions(workflows_dir: Path) -> dict[str, dict[str, Any]]:
    """
    Discover all workflows with their version information.
    
    Args:
        workflows_dir: Path to workflows directory (e.g., ai/workflows)
        
    Returns:
        Dictionary mapping workflow names to their metadata
    """
    workflows = {}
    
    if not workflows_dir.exists():
        logger.warning(f"Workflows directory does not exist: {workflows_dir}")
        return workflows
    
    for workflow_path in workflows_dir.iterdir():
        if not workflow_path.is_dir() or workflow_path.name.startswith("_"):
            continue
            
        workflow_name = workflow_path.name
        
        try:
            validation = validate_workflow_structure(workflow_path)
            
            if validation['has_workflow_py']:  # Minimum requirement
                metadata = get_workflow_metadata_from_init(workflow_path)
                metadata.update({
                    'workflow_name': workflow_name,
                    'workflow_path': str(workflow_path),
                    'structure_valid': validation['valid_structure'],
                    'validation_details': validation
                })
                workflows[workflow_name] = metadata
                
        except (WorkflowStructureError, WorkflowMetadataError) as e:
            logger.warning(
                "Failed to process workflow",
                workflow_name=workflow_name,
                error=str(e)
            )
            # Include failed workflow with error info
            workflows[workflow_name] = {
                'workflow_name': workflow_name,
                'workflow_path': str(workflow_path),
                'version': '1',
                'structure_valid': False,
                'error': str(e)
            }
            continue
            
    return dict(sorted(workflows.items()))  # Sort by workflow name