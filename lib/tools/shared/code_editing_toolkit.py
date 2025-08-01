"""
Code Editing Toolkit - Symbol-Aware Modifications and Code Transformations

Extracted from code-editing-agent for reuse across the agent ecosystem.
Focuses on safe code editing, refactoring operations, and automated transformations.
"""

import ast
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from agno.tools import tool


@tool
def replace_symbol_body(
    file_path: str,
    symbol_name: str,
    symbol_type: str,
    new_body: str,
    validate_syntax: bool = True,
    backup: bool = True,
) -> str:
    """
    Replace the body of a function, class, or method while preserving its signature.

    Args:
        file_path: Relative path to the file containing the symbol
        symbol_name: Name of the symbol to modify (function, class, or method)
        symbol_type: Type of symbol ('function', 'class', 'method')
        new_body: New body content for the symbol
        validate_syntax: Whether to validate syntax after modification
        backup: Whether to create backup before modification

    Returns:
        Success message with modification details or error information
    """
    try:
        # Validate path security
        if not _is_safe_path(file_path):
            return f"Error: Invalid or unsafe path '{file_path}'"

        project_root = Path(os.getcwd())
        target_file = project_root / file_path

        if not target_file.exists():
            return f"Error: File '{file_path}' does not exist"

        # Create backup if requested
        backup_path = None
        if backup:
            backup_path = _create_backup(target_file)

        # Read current content
        content = target_file.read_text(encoding="utf-8")
        original_lines = content.splitlines()

        # Find the symbol definition
        symbol_info = _find_symbol_definition(content, symbol_name, symbol_type)
        if not symbol_info:
            return f"Error: Symbol '{symbol_name}' of type '{symbol_type}' not found"

        # Extract symbol information
        start_line = symbol_info["start_line"]
        end_line = symbol_info["end_line"]
        signature_line = symbol_info["signature_line"]
        indentation = symbol_info["indentation"]

        # Prepare new body with proper indentation
        new_lines = _format_symbol_body(new_body, indentation, symbol_type)

        # Replace the symbol body
        modified_lines = (
            original_lines[:signature_line]
            + [original_lines[signature_line]]  # Keep signature
            + new_lines
            + original_lines[end_line + 1 :]
        )

        modified_content = "\n".join(modified_lines)

        # Validate syntax if requested
        if validate_syntax and target_file.suffix == ".py":
            validation_result = _validate_python_syntax(modified_content)
            if not validation_result["valid"]:
                return f"Error: Syntax validation failed: {validation_result['error']}"

        # Write modified content
        target_file.write_text(modified_content, encoding="utf-8")

        # Generate result message
        lines_modified = end_line - start_line
        result = f"✅ Successfully replaced body of {symbol_type} '{symbol_name}' in {file_path}"
        result += f"\n📊 Modified {lines_modified} lines (lines {start_line + 1}-{end_line + 1})"

        if backup_path:
            result += f"\n💾 Backup created: {backup_path.name}"

        if validate_syntax and target_file.suffix == ".py":
            result += "\n✅ Syntax validation passed"

        return result

    except Exception as e:
        return f"Error replacing symbol body: {e!s}"


@tool
def insert_before_symbol(
    file_path: str,
    target_symbol: str,
    symbol_type: str,
    new_code: str,
    backup: bool = True,
) -> str:
    """
    Insert new code before a specified symbol definition.

    Args:
        file_path: Relative path to the file
        target_symbol: Name of the symbol to insert before
        symbol_type: Type of symbol ('function', 'class', 'method', 'variable')
        new_code: Code to insert before the symbol
        backup: Whether to create backup before modification

    Returns:
        Success message or error details
    """
    try:
        # Validate path security
        if not _is_safe_path(file_path):
            return f"Error: Invalid or unsafe path '{file_path}'"

        project_root = Path(os.getcwd())
        target_file = project_root / file_path

        if not target_file.exists():
            return f"Error: File '{file_path}' does not exist"

        # Create backup if requested
        backup_path = None
        if backup:
            backup_path = _create_backup(target_file)

        # Read current content
        content = target_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Find the target symbol
        symbol_line = _find_symbol_line(content, target_symbol, symbol_type)
        if symbol_line is None:
            return f"Error: Symbol '{target_symbol}' of type '{symbol_type}' not found"

        # Determine insertion point and indentation
        insertion_line = symbol_line
        indentation = _get_line_indentation(lines[symbol_line])

        # Format new code with proper indentation
        new_lines = _format_code_block(new_code, indentation)

        # Insert the new code
        modified_lines = (
            lines[:insertion_line] + new_lines + [""] + lines[insertion_line:]
        )
        modified_content = "\n".join(modified_lines)

        # Validate syntax for Python files
        if target_file.suffix == ".py":
            validation_result = _validate_python_syntax(modified_content)
            if not validation_result["valid"]:
                return f"Error: Syntax validation failed: {validation_result['error']}"

        # Write modified content
        target_file.write_text(modified_content, encoding="utf-8")

        # Generate result message
        lines_added = len(new_lines)
        result = f"✅ Inserted {lines_added} lines before {symbol_type} '{target_symbol}' in {file_path}"
        result += f"\n📍 Insertion at line {insertion_line + 1}"

        if backup_path:
            result += f"\n💾 Backup created: {backup_path.name}"

        return result

    except Exception as e:
        return f"Error inserting code before symbol: {e!s}"


@tool
def insert_after_symbol(
    file_path: str,
    target_symbol: str,
    symbol_type: str,
    new_code: str,
    backup: bool = True,
) -> str:
    """
    Insert new code after a specified symbol definition.

    Args:
        file_path: Relative path to the file
        target_symbol: Name of the symbol to insert after
        symbol_type: Type of symbol ('function', 'class', 'method', 'variable')
        new_code: Code to insert after the symbol
        backup: Whether to create backup before modification

    Returns:
        Success message or error details
    """
    try:
        # Validate path security
        if not _is_safe_path(file_path):
            return f"Error: Invalid or unsafe path '{file_path}'"

        project_root = Path(os.getcwd())
        target_file = project_root / file_path

        if not target_file.exists():
            return f"Error: File '{file_path}' does not exist"

        # Create backup if requested
        backup_path = None
        if backup:
            backup_path = _create_backup(target_file)

        # Read current content
        content = target_file.read_text(encoding="utf-8")

        # Find the symbol definition
        symbol_info = _find_symbol_definition(content, target_symbol, symbol_type)
        if not symbol_info:
            return f"Error: Symbol '{target_symbol}' of type '{symbol_type}' not found"

        lines = content.splitlines()
        end_line = symbol_info["end_line"]
        indentation = symbol_info["indentation"]

        # Format new code with proper indentation
        new_lines = _format_code_block(new_code, indentation)

        # Insert after the symbol
        insertion_point = end_line + 1
        modified_lines = [
            *lines[:insertion_point],
            "",
            *new_lines,
            *lines[insertion_point:],
        ]
        modified_content = "\n".join(modified_lines)

        # Validate syntax for Python files
        if target_file.suffix == ".py":
            validation_result = _validate_python_syntax(modified_content)
            if not validation_result["valid"]:
                return f"Error: Syntax validation failed: {validation_result['error']}"

        # Write modified content
        target_file.write_text(modified_content, encoding="utf-8")

        # Generate result message
        lines_added = len(new_lines)
        result = f"✅ Inserted {lines_added} lines after {symbol_type} '{target_symbol}' in {file_path}"
        result += f"\n📍 Insertion after line {end_line + 1}"

        if backup_path:
            result += f"\n💾 Backup created: {backup_path.name}"

        return result

    except Exception as e:
        return f"Error inserting code after symbol: {e!s}"


@tool
def rename_symbol(
    file_path: str,
    old_name: str,
    new_name: str,
    symbol_type: str,
    scope: str = "file",
    backup: bool = True,
) -> str:
    """
    Rename a symbol and update all its references.

    Args:
        file_path: Relative path to the file containing the symbol
        old_name: Current name of the symbol
        new_name: New name for the symbol
        symbol_type: Type of symbol ('function', 'class', 'method', 'variable')
        scope: Scope of renaming ('file' or 'project')
        backup: Whether to create backup before modification

    Returns:
        Success message with rename statistics
    """
    try:
        # Validate path security
        if not _is_safe_path(file_path):
            return f"Error: Invalid or unsafe path '{file_path}'"

        project_root = Path(os.getcwd())
        target_file = project_root / file_path

        if not target_file.exists():
            return f"Error: File '{file_path}' does not exist"

        # Validate new name
        if not _is_valid_identifier(new_name):
            return f"Error: '{new_name}' is not a valid identifier"

        files_to_process = []
        if scope == "file":
            files_to_process = [target_file]
        else:  # project scope
            files_to_process = _get_project_files(project_root)

        backup_paths = []
        total_replacements = 0
        files_modified = 0

        # Process each file
        for file_to_process in files_to_process:
            if backup:
                backup_path = _create_backup(file_to_process)
                backup_paths.append(backup_path)

            content = file_to_process.read_text(encoding="utf-8", errors="ignore")

            # Perform smart renaming based on symbol type
            modified_content, replacements = _smart_rename_symbol(
                content, old_name, new_name, symbol_type
            )

            if replacements > 0:
                # Validate syntax for Python files
                if file_to_process.suffix == ".py":
                    validation_result = _validate_python_syntax(modified_content)
                    if not validation_result["valid"]:
                        return f"Error: Syntax validation failed in {file_to_process}: {validation_result['error']}"

                file_to_process.write_text(modified_content, encoding="utf-8")
                total_replacements += replacements
                files_modified += 1

        # Generate result message
        result = f"✅ Renamed symbol '{old_name}' to '{new_name}' ({symbol_type})"
        result += f"\n📊 {total_replacements} replacements in {files_modified} files"
        result += f"\n🎯 Scope: {scope}"

        if backup_paths:
            result += f"\n💾 Created {len(backup_paths)} backup(s)"

        return result

    except Exception as e:
        return f"Error renaming symbol: {e!s}"


@tool
def execute_shell_command(
    command: str,
    working_directory: str | None = None,
    timeout: int = 30,
    capture_output: bool = True,
) -> str:
    """
    Execute a shell command safely within the project context.

    Args:
        command: Shell command to execute
        working_directory: Optional working directory (relative to project root)
        timeout: Command timeout in seconds
        capture_output: Whether to capture and return command output

    Returns:
        Command execution results or error message
    """
    try:
        # Validate command safety
        if not _is_safe_command(command):
            return f"Error: Potentially unsafe command blocked: {command}"

        project_root = Path(os.getcwd())

        # Set working directory
        if working_directory:
            if not _is_safe_path(working_directory):
                return f"Error: Invalid working directory: {working_directory}"
            work_dir = project_root / working_directory
            if not work_dir.exists():
                return f"Error: Working directory does not exist: {working_directory}"
        else:
            work_dir = project_root

        # Execute command
        result = subprocess.run(
            command,
            check=False,
            shell=True,
            cwd=str(work_dir),
            capture_output=capture_output,
            text=True,
            timeout=timeout,
        )

        # Format output
        output_msg = f"🔧 Command executed: {command}\n"
        output_msg += f"📁 Working directory: {work_dir.relative_to(project_root) if work_dir != project_root else '.'}\n"
        output_msg += f"📊 Exit code: {result.returncode}\n"

        if capture_output:
            if result.stdout:
                output_msg += f"📤 Output:\n{result.stdout}\n"
            if result.stderr:
                output_msg += f"❌ Errors:\n{result.stderr}\n"

        if result.returncode != 0:
            output_msg += f"⚠️  Command failed with exit code {result.returncode}"
        else:
            output_msg += "✅ Command completed successfully"

        return output_msg

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds: {command}"
    except Exception as e:
        return f"Error executing command: {e!s}"


@tool
def validate_code_syntax(file_path: str, language: str | None = None) -> str:
    """
    Validate syntax of a code file.

    Args:
        file_path: Relative path to the file to validate
        language: Optional language override (auto-detected if not provided)

    Returns:
        Syntax validation results with error details if any
    """
    try:
        # Validate path security
        if not _is_safe_path(file_path):
            return f"Error: Invalid or unsafe path '{file_path}'"

        project_root = Path(os.getcwd())
        target_file = project_root / file_path

        if not target_file.exists():
            return f"Error: File '{file_path}' does not exist"

        # Auto-detect language if not provided
        if not language:
            language = _detect_language(target_file)

        content = target_file.read_text(encoding="utf-8")

        # Validate based on language
        if language == "python":
            validation = _validate_python_syntax(content)
        elif language in ["javascript", "typescript"]:
            validation = _validate_js_syntax(content, language)
        else:
            return f"Syntax validation not supported for language: {language}"

        # Format results
        if validation["valid"]:
            result = f"✅ Syntax validation passed for {file_path}"
            result += f"\n📝 Language: {language.title()}"
            if "stats" in validation:
                stats = validation["stats"]
                result += f"\n📊 Statistics: {stats.get('lines', 0)} lines, {stats.get('functions', 0)} functions"
        else:
            result = f"❌ Syntax validation failed for {file_path}"
            result += f"\n📝 Language: {language.title()}"
            result += f"\n🚨 Error: {validation['error']}"
            if "line_number" in validation:
                result += f"\n📍 Line: {validation['line_number']}"

        return result

    except Exception as e:
        return f"Error validating syntax: {e!s}"


# Helper functions


def _is_safe_path(path: str) -> bool:
    """Check if the path is safe (relative, within project, no traversal)"""
    if os.path.isabs(path):
        return False

    normalized = os.path.normpath(path)
    return not (normalized.startswith("..") or "/.." in normalized)


def _is_safe_command(command: str) -> bool:
    """Check if command is safe to execute"""
    # Block potentially dangerous commands
    dangerous_patterns = [
        "rm ",
        "del ",
        "format",
        "fdisk",
        "dd ",
        "sudo",
        "su ",
        "chmod 777",
        "chown",
        "wget",
        "curl",
        "nc ",
        "netcat",
        ">",
        ">>",
        "|",
        "&",
        ";",
        "$(",
        "`",
    ]

    command_lower = command.lower()
    return all(pattern not in command_lower for pattern in dangerous_patterns)


def _create_backup(file_path: Path) -> Path:
    """Create a backup of the file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.name}.backup_{timestamp}"
    backup_path = file_path.parent / backup_name

    shutil.copy2(file_path, backup_path)
    return backup_path


def _find_symbol_definition(
    content: str, symbol_name: str, symbol_type: str
) -> dict[str, Any] | None:
    """Find symbol definition and return its location info"""
    lines = content.splitlines()

    for i, line in enumerate(lines):
        line_stripped = line.strip()

        # Python patterns
        if (
            symbol_type == "function"
            and line_stripped.startswith(f"def {symbol_name}(")
        ) or (
            symbol_type == "class" and line_stripped.startswith(f"class {symbol_name}")
        ):
            end_line = _find_symbol_end(lines, i, _get_line_indentation(line))
            return {
                "start_line": i,
                "end_line": end_line,
                "signature_line": i,
                "indentation": _get_line_indentation(line),
            }

    return None


def _find_symbol_line(content: str, symbol_name: str, symbol_type: str) -> int | None:
    """Find the line number where a symbol is defined"""
    lines = content.splitlines()

    for i, line in enumerate(lines):
        if (symbol_type == "function" and f"def {symbol_name}(" in line) or (
            symbol_type == "class" and f"class {symbol_name}" in line
        ):
            return i
        if symbol_type == "variable" and f"{symbol_name} =" in line:
            return i

    return None


def _find_symbol_end(lines: list[str], start_line: int, base_indent: int) -> int:
    """Find the end line of a symbol block based on indentation"""
    for i in range(start_line + 1, len(lines)):
        line = lines[i]
        if line.strip() == "":
            continue

        current_indent = _get_line_indentation(line)
        if current_indent <= base_indent:
            return i - 1

    return len(lines) - 1


def _get_line_indentation(line: str) -> int:
    """Get the indentation level of a line"""
    return len(line) - len(line.lstrip())


def _format_symbol_body(body: str, indentation: int, symbol_type: str) -> list[str]:
    """Format symbol body with proper indentation"""
    lines = body.split("\n")
    formatted_lines = []

    base_indent = " " * (indentation + 4)  # Standard Python indentation

    for line in lines:
        if line.strip():  # Non-empty line
            formatted_lines.append(base_indent + line.lstrip())
        else:  # Empty line
            formatted_lines.append("")

    return formatted_lines


def _format_code_block(code: str, base_indentation: int) -> list[str]:
    """Format code block with proper indentation"""
    lines = code.split("\n")
    formatted_lines = []

    indent_str = " " * base_indentation

    for line in lines:
        if line.strip():  # Non-empty line
            formatted_lines.append(indent_str + line.lstrip())
        else:  # Empty line
            formatted_lines.append("")

    return formatted_lines


def _validate_python_syntax(content: str) -> dict[str, Any]:
    """Validate Python syntax and return detailed results"""
    try:
        tree = ast.parse(content)

        # Count various elements
        stats = {
            "lines": len(content.splitlines()),
            "functions": len(
                [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            ),
            "classes": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
        }

        return {"valid": True, "stats": stats}

    except SyntaxError as e:
        return {
            "valid": False,
            "error": str(e),
            "line_number": e.lineno,
            "offset": e.offset,
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


def _validate_js_syntax(content: str, language: str) -> dict[str, Any]:
    """Validate JavaScript/TypeScript syntax (basic check)"""
    # Basic syntax checks for JS/TS
    common_errors = []

    # Check for basic syntax issues
    if content.count("{") != content.count("}"):
        common_errors.append("Mismatched braces")

    if content.count("(") != content.count(")"):
        common_errors.append("Mismatched parentheses")

    if content.count("[") != content.count("]"):
        common_errors.append("Mismatched brackets")

    if common_errors:
        return {"valid": False, "error": ", ".join(common_errors)}

    return {"valid": True}


def _detect_language(file_path: Path) -> str:
    """Detect programming language from file extension"""
    extension = file_path.suffix.lower()

    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".rb": "ruby",
        ".go": "go",
        ".rs": "rust",
    }

    return language_map.get(extension, "unknown")


def _is_valid_identifier(name: str) -> bool:
    """Check if name is a valid identifier"""
    return name.isidentifier() and not name.startswith("__")


def _get_project_files(project_root: Path) -> list[Path]:
    """Get all relevant project files for renaming operations"""
    files = []
    extensions = [".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".rb", ".go", ".rs"]

    for file_path in project_root.rglob("*"):
        if (
            file_path.is_file()
            and file_path.suffix in extensions
            and not any(
                part
                in [".git", "node_modules", "__pycache__", ".venv", "build", "dist"]
                for part in file_path.parts
            )
        ):
            files.append(file_path)

    return files


def _smart_rename_symbol(
    content: str, old_name: str, new_name: str, symbol_type: str
) -> tuple[str, int]:
    """Perform intelligent symbol renaming with context awareness"""
    replacements = 0

    # Define word boundary patterns for different symbol types
    if symbol_type in ["function", "method"]:
        # Match function calls and definitions
        pattern = r"\b" + re.escape(old_name) + r"(?=\s*\()"
    elif symbol_type == "class":
        # Match class names in various contexts
        pattern = r"\b" + re.escape(old_name) + r"(?=\s*[\(:]|$)"
    else:
        # General symbol matching with word boundaries
        pattern = r"\b" + re.escape(old_name) + r"\b"

    # Perform replacement
    new_content = re.sub(pattern, new_name, content)
    replacements = len(re.findall(pattern, content))

    return new_content, replacements
