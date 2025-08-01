"""
Code Understanding Toolkit - Symbol Analysis and Language Server Integration

Extracted from code-understanding-agent for reuse across the agent ecosystem.
Focuses on deep code understanding, symbol relationships, and architectural analysis.
"""

import os
import re
from pathlib import Path
from typing import Any

from agno.tools import tool


@tool
def find_symbol(
    symbol_name: str,
    symbol_type: str | None = None,
    file_pattern: str | None = None,
    case_sensitive: bool = True,
) -> str:
    """
    Perform a global search for symbols with the given name or containing a substring.

    Args:
        symbol_name: The symbol name or substring to search for
        symbol_type: Optional filter by symbol type (class, function, variable, etc.)
        file_pattern: Optional file pattern to limit search scope (e.g., "*.py")
        case_sensitive: Whether to perform case-sensitive search

    Returns:
        Detailed information about found symbols including locations and context
    """
    try:
        project_root = Path(os.getcwd())
        results = []
        search_pattern = symbol_name if case_sensitive else symbol_name.lower()

        # Define file extensions based on file_pattern or use common ones
        if file_pattern:
            if file_pattern.startswith("*."):
                extensions = [file_pattern[1:]]  # Remove *
            else:
                extensions = [".py", ".js", ".ts", ".java", ".cpp", ".c", ".h"]
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
            ]

        def search_in_file(file_path: Path) -> list[dict[str, Any]]:
            """Search for symbols in a single file"""
            file_results = []
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()

                for line_num, line in enumerate(lines, 1):
                    search_line = line if case_sensitive else line.lower()
                    if search_pattern in search_line:
                        # Try to determine symbol type from context
                        detected_type = _detect_symbol_type(line, symbol_name)

                        if symbol_type and detected_type != symbol_type:
                            continue

                        # Get surrounding context
                        start_line = max(0, line_num - 3)
                        end_line = min(len(lines), line_num + 2)
                        context_lines = lines[start_line:end_line]

                        file_results.append(
                            {
                                "file": str(file_path.relative_to(project_root)),
                                "line": line_num,
                                "symbol_type": detected_type,
                                "content": line.strip(),
                                "context": "\n".join(
                                    f"{start_line + i + 1:4d}: {line}"
                                    for i, line in enumerate(context_lines)
                                ),
                            }
                        )
            except Exception:
                pass  # Skip files that can't be read

            return file_results

        # Search through project files
        for file_path in project_root.rglob("*"):
            if file_path.is_file() and file_path.suffix in extensions:
                # Skip common non-source directories
                if any(
                    part
                    in [".git", "node_modules", "__pycache__", ".venv", "build", "dist"]
                    for part in file_path.parts
                ):
                    continue

                results.extend(search_in_file(file_path))

        if not results:
            return f"No symbols found matching '{symbol_name}'" + (
                f" of type '{symbol_type}'" if symbol_type else ""
            )

        # Format results
        output = [f"Found {len(results)} symbol(s) matching '{symbol_name}':\n"]

        for result in sorted(results, key=lambda x: (x["file"], x["line"])):
            output.append(
                f"📍 {result['file']}:{result['line']} - {result['symbol_type']}"
            )
            output.append(f"   {result['content']}")
            output.append("")

        # If results are too many, show first 20 with summary
        if len(results) > 20:
            summary_results = results[:20]
            output = [
                f"Found {len(results)} symbol(s) matching '{symbol_name}' (showing first 20):\n"
            ]
            for result in summary_results:
                output.append(
                    f"📍 {result['file']}:{result['line']} - {result['symbol_type']}"
                )
                output.append(f"   {result['content']}")
            output.append(f"\n... and {len(results) - 20} more results")

        return "\n".join(output)

    except Exception as e:
        return f"Error searching for symbol '{symbol_name}': {e!s}"


@tool
def find_referencing_symbols(
    target_symbol: str,
    target_file: str,
    target_line: int | None = None,
    symbol_types: list[str] | None = None,
) -> str:
    """
    Find symbols that reference the symbol at the given location.

    Args:
        target_symbol: The symbol name to find references for
        target_file: The file containing the target symbol
        target_line: Optional line number for more precise targeting
        symbol_types: Optional list of symbol types to include (class, function, etc.)

    Returns:
        List of symbols that reference the target symbol
    """
    try:
        project_root = Path(os.getcwd())
        target_path = project_root / target_file

        if not target_path.exists():
            return f"Target file not found: {target_file}"

        references = []
        search_extensions = [
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
        ]

        # Search for references across the project
        for file_path in project_root.rglob("*"):
            if file_path.is_file() and file_path.suffix in search_extensions:
                # Skip common non-source directories
                if any(
                    part
                    in [".git", "node_modules", "__pycache__", ".venv", "build", "dist"]
                    for part in file_path.parts
                ):
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    lines = content.splitlines()

                    for line_num, line in enumerate(lines, 1):
                        if target_symbol in line:
                            # Skip the definition itself
                            if (
                                file_path == target_path
                                and target_line
                                and line_num == target_line
                            ):
                                continue

                            # Try to understand the reference context
                            ref_type = _analyze_reference_context(line, target_symbol)

                            if symbol_types and ref_type not in symbol_types:
                                continue

                            # Get context around the reference
                            start_line = max(0, line_num - 2)
                            end_line = min(len(lines), line_num + 1)
                            context_lines = lines[start_line:end_line]

                            references.append(
                                {
                                    "file": str(file_path.relative_to(project_root)),
                                    "line": line_num,
                                    "reference_type": ref_type,
                                    "content": line.strip(),
                                    "context": "\n".join(
                                        f"{start_line + i + 1:4d}: {line}"
                                        for i, line in enumerate(context_lines)
                                    ),
                                }
                            )

                except Exception:
                    continue  # Skip files that can't be read

        if not references:
            return f"No references found for symbol '{target_symbol}' in {target_file}"

        # Format results
        output = [f"Found {len(references)} reference(s) to '{target_symbol}':\n"]

        for ref in sorted(references, key=lambda x: (x["file"], x["line"])):
            output.append(f"📍 {ref['file']}:{ref['line']} - {ref['reference_type']}")
            output.append(f"   {ref['content']}")
            output.append("")

        return "\n".join(output)

    except Exception as e:
        return f"Error finding references for '{target_symbol}': {e!s}"


@tool
def find_referencing_code_snippets(
    target_symbol: str, target_file: str, context_lines: int = 3
) -> str:
    """
    Find code snippets that reference the specified symbol with extended context.

    Args:
        target_symbol: The symbol name to find references for
        target_file: The file containing the target symbol
        context_lines: Number of context lines to show around each reference

    Returns:
        Code snippets showing how the symbol is used with context
    """
    try:
        project_root = Path(os.getcwd())
        target_path = project_root / target_file

        if not target_path.exists():
            return f"Target file not found: {target_file}"

        snippets = []
        search_extensions = [
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
        ]

        for file_path in project_root.rglob("*"):
            if file_path.is_file() and file_path.suffix in search_extensions:
                # Skip common non-source directories
                if any(
                    part
                    in [".git", "node_modules", "__pycache__", ".venv", "build", "dist"]
                    for part in file_path.parts
                ):
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    lines = content.splitlines()

                    for line_num, line in enumerate(lines, 1):
                        if target_symbol in line:
                            # Skip if this is the definition file and seems to be the definition
                            if file_path == target_path and any(
                                keyword in line
                                for keyword in [
                                    "def ",
                                    "class ",
                                    "function ",
                                    "var ",
                                    "let ",
                                    "const ",
                                ]
                            ):
                                continue

                            # Extract extended context
                            start_line = max(0, line_num - context_lines - 1)
                            end_line = min(len(lines), line_num + context_lines)
                            snippet_lines = lines[start_line:end_line]

                            # Analyze the usage pattern
                            usage_type = _analyze_usage_pattern(line, target_symbol)

                            snippet = {
                                "file": str(file_path.relative_to(project_root)),
                                "line_range": f"{start_line + 1}-{end_line}",
                                "target_line": line_num,
                                "usage_type": usage_type,
                                "snippet": "\n".join(
                                    f"{start_line + i + 1:4d}: {line}"
                                    for i, line in enumerate(snippet_lines)
                                ),
                                "highlighted_line": line_num,
                            }
                            snippets.append(snippet)

                except Exception:
                    continue

        if not snippets:
            return f"No code snippets found referencing '{target_symbol}'"

        # Format output
        output = [
            f"Code snippets referencing '{target_symbol}' ({len(snippets)} found):\n"
        ]

        for snippet in sorted(
            snippets, key=lambda x: (x["file"], int(x["target_line"]))
        ):
            output.append(
                f"📄 {snippet['file']} (lines {snippet['line_range']}) - {snippet['usage_type']}"
            )
            output.append(f"{snippet['snippet']}")
            output.append("")

        return "\n".join(output)

    except Exception as e:
        return f"Error finding code snippets for '{target_symbol}': {e!s}"


@tool
def get_symbols_overview(
    file_or_directory: str,
    symbol_types: list[str] | None = None,
    include_private: bool = False,
) -> str:
    """
    Get an overview of top-level symbols defined in a file or directory.

    Args:
        file_or_directory: Path to file or directory to analyze
        symbol_types: Optional list of symbol types to include (class, function, variable)
        include_private: Whether to include private/internal symbols

    Returns:
        Structured overview of symbols with their types and locations
    """
    try:
        project_root = Path(os.getcwd())
        target_path = project_root / file_or_directory

        if not target_path.exists():
            return f"Path not found: {file_or_directory}"

        symbols = []

        if target_path.is_file():
            symbols.extend(
                _extract_symbols_from_file(target_path, symbol_types, include_private)
            )
        else:
            # Directory - analyze all relevant files
            for file_path in target_path.rglob("*"):
                if file_path.is_file() and file_path.suffix in [
                    ".py",
                    ".js",
                    ".ts",
                    ".java",
                    ".cpp",
                    ".c",
                    ".h",
                ]:
                    symbols.extend(
                        _extract_symbols_from_file(
                            file_path, symbol_types, include_private
                        )
                    )

        if not symbols:
            return f"No symbols found in {file_or_directory}"

        # Group symbols by file and type
        by_file = {}
        for symbol in symbols:
            file_key = symbol["file"]
            if file_key not in by_file:
                by_file[file_key] = {}

            symbol_type = symbol["type"]
            if symbol_type not in by_file[file_key]:
                by_file[file_key][symbol_type] = []

            by_file[file_key][symbol_type].append(symbol)

        # Format output
        output = [f"Symbol Overview for {file_or_directory}:\n"]

        for file_path in sorted(by_file.keys()):
            output.append(f"📄 {file_path}")

            for symbol_type in sorted(by_file[file_path].keys()):
                type_symbols = by_file[file_path][symbol_type]
                output.append(f"  {symbol_type.upper()}S ({len(type_symbols)}):")

                for symbol in sorted(type_symbols, key=lambda x: x["line"]):
                    visibility = "🔒" if symbol.get("private", False) else "🔓"
                    output.append(
                        f"    {visibility} {symbol['name']} (line {symbol['line']})"
                    )
                    if symbol.get("signature"):
                        output.append(f"        {symbol['signature']}")
            output.append("")

        return "\n".join(output)

    except Exception as e:
        return f"Error getting symbols overview for '{file_or_directory}': {e!s}"


# Helper functions


def _detect_symbol_type(line: str, symbol_name: str) -> str:
    """Detect the type of symbol from its context in the line"""
    line_lower = line.strip().lower()

    # Python patterns
    if line_lower.startswith("class "):
        return "class"
    if line_lower.startswith("def "):
        return "function"
    if " = " in line and not line_lower.startswith(("if ", "for ", "while ")):
        return "variable"
    if line_lower.startswith(("import ", "from ")):
        return "import"

    # JavaScript/TypeScript patterns
    if "function" in line_lower or "=>" in line:
        return "function"
    if line_lower.startswith(("const ", "let ", "var ")):
        return "variable"
    if "interface" in line_lower:
        return "interface"
    if "type " in line_lower and "=" in line:
        return "type"

    # Java patterns
    if "public class" in line_lower or "private class" in line_lower:
        return "class"
    if "public interface" in line_lower:
        return "interface"
    if (
        ("public " in line_lower or "private " in line_lower)
        and "(" in line
        and ")" in line
    ):
        return "method"

    # Generic patterns
    if "(" in line and ")" in line and symbol_name in line:
        return "function"
    if symbol_name in line and "=" in line:
        return "variable"

    return "reference"


def _analyze_reference_context(line: str, symbol: str) -> str:
    """Analyze how a symbol is being referenced in a line"""
    line_stripped = line.strip()

    if f"{symbol}(" in line:
        return "function_call"
    if f".{symbol}" in line or f"{symbol}." in line:
        return "property_access"
    if "import" in line_stripped and symbol in line:
        return "import"
    if "extends" in line or "implements" in line:
        return "inheritance"
    if "=" in line and symbol in line.split("=")[1]:
        return "assignment"
    if "new " in line and symbol in line:
        return "instantiation"
    return "reference"


def _analyze_usage_pattern(line: str, symbol: str) -> str:
    """Analyze the usage pattern of a symbol in context"""
    patterns = [
        (r"new\s+" + re.escape(symbol), "Constructor Call"),
        (r"" + re.escape(symbol) + r"\s*\(", "Function Call"),
        (r"\." + re.escape(symbol), "Property Access"),
        (r"extends\s+" + re.escape(symbol), "Inheritance"),
        (r"implements\s+" + re.escape(symbol), "Interface Implementation"),
        (r"import.*" + re.escape(symbol), "Import"),
        (r"from.*" + re.escape(symbol), "Import"),
    ]

    for pattern, usage_type in patterns:
        if re.search(pattern, line, re.IGNORECASE):
            return usage_type

    return "Reference"


def _extract_symbols_from_file(
    file_path: Path, symbol_types: list[str] | None, include_private: bool
) -> list[dict[str, Any]]:
    """Extract symbol definitions from a single file"""
    symbols = []

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        project_root = Path(os.getcwd())
        relative_path = str(file_path.relative_to(project_root))

        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith(("#", "//")):
                continue

            symbol = _parse_symbol_definition(line_stripped, line_num)
            if symbol:
                symbol["file"] = relative_path

                # Check if private and whether to include
                if not include_private and symbol.get("private", False):
                    continue

                # Check symbol type filter
                if symbol_types and symbol["type"] not in symbol_types:
                    continue

                symbols.append(symbol)

    except Exception:
        pass  # Skip files that can't be processed

    return symbols


def _parse_symbol_definition(line: str, line_num: int) -> dict[str, Any] | None:
    """Parse a line to extract symbol definition information"""
    line = line.strip()

    # Python patterns
    if line.startswith("class "):
        match = re.match(r"class\s+(\w+)", line)
        if match:
            return {
                "name": match.group(1),
                "type": "class",
                "line": line_num,
                "signature": line,
                "private": match.group(1).startswith("_"),
            }

    elif line.startswith("def "):
        match = re.match(r"def\s+(\w+)\s*\([^)]*\)", line)
        if match:
            return {
                "name": match.group(1),
                "type": "function",
                "line": line_num,
                "signature": line,
                "private": match.group(1).startswith("_"),
            }

    # JavaScript/TypeScript patterns
    elif "function" in line:
        match = re.search(r"function\s+(\w+)", line)
        if match:
            return {
                "name": match.group(1),
                "type": "function",
                "line": line_num,
                "signature": line,
                "private": match.group(1).startswith("_"),
            }

    elif re.match(r"(const|let|var)\s+\w+\s*=", line):
        match = re.match(r"(const|let|var)\s+(\w+)", line)
        if match:
            return {
                "name": match.group(2),
                "type": "variable",
                "line": line_num,
                "signature": line,
                "private": match.group(2).startswith("_"),
            }

    return None
