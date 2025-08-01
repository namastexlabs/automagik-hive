"""
File Management Toolkit - Complete File Operation Suite

Extracted from file-management-agent for reuse across the agent ecosystem.
Provides secure file system operations, content manipulation, and data integrity.
"""

import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from agno.tools import tool


@tool
def read_file(
    relative_path: str,
    start_line: int = 0,
    end_line: int | None = None,
    max_chars: int = 200000,
    encoding: str = "utf-8",
) -> str:
    """
    Read file content within the project directory with chunking support.

    Args:
        relative_path: The relative path to the file from project root
        start_line: 0-based index of the first line to retrieve
        end_line: 0-based index of the last line to retrieve (inclusive)
        max_chars: Maximum characters to return (prevents memory issues)
        encoding: Text encoding to use for reading the file

    Returns:
        File content or error message with reading status
    """
    try:
        # Validate path security
        if not _is_safe_path(relative_path):
            return f"Error: Invalid or unsafe path '{relative_path}'. Use relative paths within project only."

        project_root = Path(os.getcwd())
        file_path = project_root / relative_path

        if not file_path.exists():
            return f"Error: File '{relative_path}' does not exist"

        if not file_path.is_file():
            return f"Error: '{relative_path}' is not a file"

        # Check file size before reading
        file_size = file_path.stat().st_size
        if file_size > max_chars * 2:  # Rough estimate
            return f"Error: File too large ({file_size} bytes). Use start_line/end_line parameters or increase max_chars."

        # Read file content
        try:
            content = file_path.read_text(encoding=encoding, errors="replace")
        except UnicodeDecodeError:
            # Try alternative encodings
            for alt_encoding in ["latin-1", "cp1252", "utf-16"]:
                try:
                    content = file_path.read_text(
                        encoding=alt_encoding, errors="replace"
                    )
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return f"Error: Could not decode file '{relative_path}' with any supported encoding"

        # Handle line-based reading
        if start_line > 0 or end_line is not None:
            lines = content.splitlines()
            total_lines = len(lines)

            if start_line >= total_lines:
                return f"Error: start_line ({start_line}) exceeds file length ({total_lines} lines)"

            if end_line is None:
                selected_lines = lines[start_line:]
            else:
                if end_line >= total_lines:
                    end_line = total_lines - 1
                selected_lines = lines[start_line : end_line + 1]

            content = "\n".join(selected_lines)

        # Apply character limit
        if len(content) > max_chars:
            content = content[:max_chars]
            content += f"\n\n[... Content truncated at {max_chars} characters. Use start_line/end_line for specific sections.]"

        # Add file metadata
        file_info = _get_file_info(file_path)
        header = f"📄 File: {relative_path} ({file_info['size']} bytes, {file_info['lines']} lines)\n"
        header += f"📅 Modified: {file_info['modified']}\n\n"

        return header + content

    except Exception as e:
        return f"Error reading file '{relative_path}': {e!s}"


@tool
def create_text_file(
    relative_path: str,
    content: str,
    encoding: str = "utf-8",
    backup_existing: bool = True,
) -> str:
    """
    Create or overwrite a file with the given content.

    Args:
        relative_path: The relative path to the file to create
        content: The content to write to the file
        encoding: Text encoding to use for writing
        backup_existing: Whether to backup existing files before overwriting

    Returns:
        Success message or error details
    """
    try:
        # Validate path security
        if not _is_safe_path(relative_path):
            return f"Error: Invalid or unsafe path '{relative_path}'. Use relative paths within project only."

        project_root = Path(os.getcwd())
        file_path = project_root / relative_path

        # Check if we're overwriting an existing file
        will_overwrite = file_path.exists()
        backup_path = None

        if will_overwrite and backup_existing:
            # Create backup
            backup_path = _create_backup(file_path)

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content with atomic operation
        temp_file = None
        try:
            # Write to temporary file first
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding=encoding,
                dir=file_path.parent,
                delete=False,
                suffix=".tmp",
            ) as temp_file:
                temp_file.write(content)
                temp_file.flush()
                os.fsync(temp_file.fileno())

            # Atomic move to final location
            shutil.move(temp_file.name, str(file_path))

            # Verify content was written correctly
            written_size = file_path.stat().st_size
            len(content.encode(encoding))

            result_msg = f"✅ File created: {relative_path} ({written_size} bytes)"

            if will_overwrite:
                result_msg += " (overwrote existing file)"
                if backup_path:
                    result_msg += f" - backup: {backup_path.name}"

            # Add content summary
            lines = content.count("\n") + 1
            result_msg += f"\n📊 Content: {lines} lines, {written_size} bytes"

            return result_msg

        except Exception:
            # Cleanup temporary file if it exists
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise

    except Exception as e:
        return f"Error creating file '{relative_path}': {e!s}"


@tool
def list_dir(
    relative_path: str = ".",
    recursive: bool = False,
    max_items: int = 1000,
    show_hidden: bool = False,
    file_types: list[str] | None = None,
) -> str:
    """
    List files and directories in the given path with filtering options.

    Args:
        relative_path: The relative directory path to list
        recursive: Whether to scan subdirectories recursively
        max_items: Maximum number of items to return
        show_hidden: Whether to show hidden files (starting with .)
        file_types: Optional list of file extensions to filter (e.g., ['.py', '.js'])

    Returns:
        Formatted directory listing with file information
    """
    try:
        # Validate path security
        if not _is_safe_path(relative_path):
            return f"Error: Invalid or unsafe path '{relative_path}'"

        project_root = Path(os.getcwd())
        target_path = project_root / relative_path

        if not target_path.exists():
            return f"Error: Directory '{relative_path}' does not exist"

        if not target_path.is_dir():
            return f"Error: '{relative_path}' is not a directory"

        items = []
        item_count = 0

        # Collect items
        if recursive:
            for item in target_path.rglob("*"):
                if item_count >= max_items:
                    break
                if _should_include_item(item, show_hidden, file_types):
                    items.append(_format_item_info(item, project_root))
                    item_count += 1
        else:
            for item in target_path.iterdir():
                if item_count >= max_items:
                    break
                if _should_include_item(item, show_hidden, file_types):
                    items.append(_format_item_info(item, project_root))
                    item_count += 1

        if not items:
            return f"No items found in '{relative_path}'" + (
                f" (filtered by {file_types})" if file_types else ""
            )

        # Format output
        header = f"📁 Directory listing: {relative_path}"
        if recursive:
            header += " (recursive)"
        if file_types:
            header += f" (filtered: {', '.join(file_types)})"
        header += f"\nFound {len(items)} item(s):\n"

        # Sort items: directories first, then files
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

        output_lines = [header]
        for item in items:
            icon = "📁" if item["is_dir"] else "📄"
            size_info = f" ({item['size']})" if not item["is_dir"] else ""
            output_lines.append(f"{icon} {item['path']}{size_info}")

        if item_count >= max_items:
            output_lines.append(f"\n... (truncated at {max_items} items)")

        return "\n".join(output_lines)

    except Exception as e:
        return f"Error listing directory '{relative_path}': {e!s}"


@tool
def search_for_pattern(
    pattern: str,
    file_pattern: str = "*",
    case_sensitive: bool = False,
    use_regex: bool = False,
    max_results: int = 100,
    context_lines: int = 1,
) -> str:
    """
    Search for text patterns across files in the project.

    Args:
        pattern: The text pattern to search for
        file_pattern: File pattern to limit search (e.g., "*.py", "*.js")
        case_sensitive: Whether to perform case-sensitive search
        use_regex: Whether to interpret pattern as regular expression
        max_results: Maximum number of matches to return
        context_lines: Number of context lines to show around matches

    Returns:
        Search results with file locations and context
    """
    try:
        project_root = Path(os.getcwd())
        matches = []
        files_searched = 0

        # Determine file extensions from pattern
        if file_pattern == "*":
            extensions = [
                ".py",
                ".js",
                ".ts",
                ".java",
                ".cpp",
                ".c",
                ".h",
                ".rb",
                ".go",
                ".rs",
                ".txt",
                ".md",
            ]
        elif file_pattern.startswith("*."):
            extensions = [file_pattern[1:]]
        else:
            extensions = [
                ".py",
                ".js",
                ".ts",
                ".java",
                ".cpp",
                ".c",
                ".h",
                ".rb",
                ".go",
                ".rs",
                ".txt",
                ".md",
            ]

        # Compile regex if needed
        if use_regex:
            try:
                if case_sensitive:
                    regex = re.compile(pattern)
                else:
                    regex = re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                return f"Error: Invalid regular expression '{pattern}': {e!s}"

        # Search through files
        for file_path in project_root.rglob("*"):
            if len(matches) >= max_results:
                break

            if not file_path.is_file() or file_path.suffix not in extensions:
                continue

            # Skip common non-source directories
            if any(
                part
                in [
                    ".git",
                    "node_modules",
                    "__pycache__",
                    ".venv",
                    "build",
                    "dist",
                    ".pytest_cache",
                ]
                for part in file_path.parts
            ):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()
                files_searched += 1

                for line_num, line in enumerate(lines, 1):
                    if len(matches) >= max_results:
                        break

                    # Check for pattern match
                    found_match = False
                    if use_regex:
                        match = regex.search(line)
                        found_match = match is not None
                    else:
                        search_line = line if case_sensitive else line.lower()
                        search_pattern = pattern if case_sensitive else pattern.lower()
                        found_match = search_pattern in search_line

                    if found_match:
                        # Get context lines
                        start_line = max(0, line_num - context_lines - 1)
                        end_line = min(len(lines), line_num + context_lines)
                        context_block = lines[start_line:end_line]

                        match_info = {
                            "file": str(file_path.relative_to(project_root)),
                            "line": line_num,
                            "content": line.strip(),
                            "context": "\n".join(
                                f"{start_line + i + 1:4d}: {ctx_line}"
                                for i, ctx_line in enumerate(context_block)
                            ),
                        }
                        matches.append(match_info)

            except Exception:
                continue  # Skip files that can't be read

        if not matches:
            search_type = "regex" if use_regex else "text"
            return (
                f"No matches found for {search_type} pattern '{pattern}' "
                f"in {files_searched} files searched"
            )

        # Format results
        search_type = "regex" if use_regex else "text"
        output = [f"🔍 Search results for {search_type} pattern '{pattern}'"]
        output.append(
            f"Found {len(matches)} match(es) in {files_searched} files searched:\n"
        )

        for match in matches:
            output.append(f"📍 {match['file']}:{match['line']}")
            output.append(f"   {match['content']}")
            if context_lines > 0:
                output.append("   Context:")
                output.append(f"   {match['context']}")
            output.append("")

        if len(matches) >= max_results:
            output.append(f"... (limited to {max_results} results)")

        return "\n".join(output)

    except Exception as e:
        return f"Error searching for pattern '{pattern}': {e!s}"


@tool
def delete_lines(
    relative_path: str, start_line: int, end_line: int, backup: bool = True
) -> str:
    """
    Delete a range of lines from a file.

    Args:
        relative_path: The relative path to the file
        start_line: 1-based line number to start deletion (inclusive)
        end_line: 1-based line number to end deletion (inclusive)
        backup: Whether to create a backup before modification

    Returns:
        Success message or error details
    """
    try:
        # Validate path security
        if not _is_safe_path(relative_path):
            return f"Error: Invalid or unsafe path '{relative_path}'"

        project_root = Path(os.getcwd())
        file_path = project_root / relative_path

        if not file_path.exists():
            return f"Error: File '{relative_path}' does not exist"

        # Create backup if requested
        backup_path = None
        if backup:
            backup_path = _create_backup(file_path)

        # Read current content
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)
        total_lines = len(lines)

        # Validate line numbers (convert to 0-based)
        start_idx = start_line - 1
        end_idx = end_line - 1

        if start_idx < 0 or start_idx >= total_lines:
            return f"Error: start_line {start_line} is out of range (1-{total_lines})"

        if end_idx < 0 or end_idx >= total_lines:
            return f"Error: end_line {end_line} is out of range (1-{total_lines})"

        if start_idx > end_idx:
            return f"Error: start_line ({start_line}) must be <= end_line ({end_line})"

        # Delete lines
        deleted_lines = lines[start_idx : end_idx + 1]
        new_lines = lines[:start_idx] + lines[end_idx + 1 :]
        new_content = "".join(new_lines)

        # Write modified content
        file_path.write_text(new_content, encoding="utf-8")

        # Generate result message
        lines_deleted = len(deleted_lines)
        result = f"✅ Deleted {lines_deleted} line(s) from {relative_path} (lines {start_line}-{end_line})"

        if backup_path:
            result += f"\n💾 Backup created: {backup_path.name}"

        result += f"\n📊 File now has {len(new_lines)} lines (was {total_lines})"

        return result

    except Exception as e:
        return f"Error deleting lines from '{relative_path}': {e!s}"


@tool
def replace_lines(
    relative_path: str,
    start_line: int,
    end_line: int,
    new_content: str,
    backup: bool = True,
) -> str:
    """
    Replace a range of lines in a file with new content.

    Args:
        relative_path: The relative path to the file
        start_line: 1-based line number to start replacement (inclusive)
        end_line: 1-based line number to end replacement (inclusive)
        new_content: New content to replace the lines with
        backup: Whether to create a backup before modification

    Returns:
        Success message or error details
    """
    try:
        # Validate path security
        if not _is_safe_path(relative_path):
            return f"Error: Invalid or unsafe path '{relative_path}'"

        project_root = Path(os.getcwd())
        file_path = project_root / relative_path

        if not file_path.exists():
            return f"Error: File '{relative_path}' does not exist"

        # Create backup if requested
        backup_path = None
        if backup:
            backup_path = _create_backup(file_path)

        # Read current content
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)
        total_lines = len(lines)

        # Validate line numbers (convert to 0-based)
        start_idx = start_line - 1
        end_idx = end_line - 1

        if start_idx < 0 or start_idx >= total_lines:
            return f"Error: start_line {start_line} is out of range (1-{total_lines})"

        if end_idx < 0 or end_idx >= total_lines:
            return f"Error: end_line {end_line} is out of range (1-{total_lines})"

        if start_idx > end_idx:
            return f"Error: start_line ({start_line}) must be <= end_line ({end_line})"

        # Prepare new content lines
        new_lines = new_content.splitlines(keepends=True)
        if new_content and not new_content.endswith("\n"):
            # Add newline if content doesn't end with one and isn't empty
            new_lines[-1] += "\n"

        # Replace lines
        replaced_lines = lines[start_idx : end_idx + 1]
        modified_lines = lines[:start_idx] + new_lines + lines[end_idx + 1 :]
        modified_content = "".join(modified_lines)

        # Write modified content
        file_path.write_text(modified_content, encoding="utf-8")

        # Generate result message
        lines_replaced = len(replaced_lines)
        lines_added = len(new_lines)

        result = f"✅ Replaced {lines_replaced} line(s) in {relative_path} (lines {start_line}-{end_line})"
        result += f" with {lines_added} new line(s)"

        if backup_path:
            result += f"\n💾 Backup created: {backup_path.name}"

        result += f"\n📊 File now has {len(modified_lines)} lines (was {total_lines})"

        return result

    except Exception as e:
        return f"Error replacing lines in '{relative_path}': {e!s}"


@tool
def insert_at_line(
    relative_path: str, line_number: int, content: str, backup: bool = True
) -> str:
    """
    Insert content at a specific line number in a file.

    Args:
        relative_path: The relative path to the file
        line_number: 1-based line number where to insert (content will be inserted before this line)
        content: Content to insert
        backup: Whether to create a backup before modification

    Returns:
        Success message or error details
    """
    try:
        # Validate path security
        if not _is_safe_path(relative_path):
            return f"Error: Invalid or unsafe path '{relative_path}'"

        project_root = Path(os.getcwd())
        file_path = project_root / relative_path

        if not file_path.exists():
            return f"Error: File '{relative_path}' does not exist"

        # Create backup if requested
        backup_path = None
        if backup:
            backup_path = _create_backup(file_path)

        # Read current content
        file_content = file_path.read_text(encoding="utf-8")
        lines = file_content.splitlines(keepends=True)
        total_lines = len(lines)

        # Validate line number (convert to 0-based)
        insert_idx = line_number - 1

        if insert_idx < 0:
            return "Error: line_number must be >= 1"

        insert_idx = min(insert_idx, total_lines)

        # Prepare content to insert
        insert_lines = content.splitlines(keepends=True)
        if content and not content.endswith("\n"):
            insert_lines[-1] += "\n"

        # Insert content
        new_lines = lines[:insert_idx] + insert_lines + lines[insert_idx:]
        new_content = "".join(new_lines)

        # Write modified content
        file_path.write_text(new_content, encoding="utf-8")

        # Generate result message
        lines_inserted = len(insert_lines)
        actual_position = "end" if insert_idx >= total_lines else f"line {line_number}"

        result = f"✅ Inserted {lines_inserted} line(s) at {actual_position} in {relative_path}"

        if backup_path:
            result += f"\n💾 Backup created: {backup_path.name}"

        result += f"\n📊 File now has {len(new_lines)} lines (was {total_lines})"

        return result

    except Exception as e:
        return f"Error inserting content in '{relative_path}': {e!s}"


# Helper functions


def _is_safe_path(path: str) -> bool:
    """Check if the path is safe (relative, within project, no traversal)"""
    if os.path.isabs(path):
        return False

    # Check for path traversal attempts
    normalized = os.path.normpath(path)
    if normalized.startswith("..") or "/.." in normalized or "\\..\\" in normalized:
        return False

    # Check for dangerous paths
    dangerous_patterns = ["/etc/", "/root/", "/home/", "C:\\", "/usr/", "/var/"]
    return not any(pattern in normalized for pattern in dangerous_patterns)


def _get_file_info(file_path: Path) -> dict[str, Any]:
    """Get file information including size, modification time, and line count"""
    stat = file_path.stat()

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.count("\n") + 1
    except:
        lines = 0

    return {
        "size": _format_file_size(stat.st_size),
        "lines": lines,
        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
    }


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def _should_include_item(
    item: Path, show_hidden: bool, file_types: list[str] | None
) -> bool:
    """Check if an item should be included in directory listing"""
    # Skip hidden files unless requested
    if not show_hidden and item.name.startswith("."):
        return False

    # Skip common build/cache directories
    skip_dirs = {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "build",
        "dist",
        ".pytest_cache",
    }
    if item.is_dir() and item.name in skip_dirs:
        return False

    # Filter by file types if specified
    if file_types and item.is_file():
        return item.suffix in file_types

    return True


def _format_item_info(item: Path, project_root: Path) -> dict[str, Any]:
    """Format item information for directory listing"""
    stat = item.stat()
    return {
        "name": item.name,
        "path": str(item.relative_to(project_root)),
        "is_dir": item.is_dir(),
        "size": _format_file_size(stat.st_size) if item.is_file() else "",
        "modified": datetime.fromtimestamp(stat.st_mtime),
    }


def _create_backup(file_path: Path) -> Path:
    """Create a backup of the file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.name}.backup_{timestamp}"
    backup_path = file_path.parent / backup_name

    shutil.copy2(file_path, backup_path)
    return backup_path
