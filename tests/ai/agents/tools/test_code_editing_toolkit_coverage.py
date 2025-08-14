"""Comprehensive test coverage for ai.agents.tools.code_editing_toolkit module.

This test suite focuses on achieving >50% coverage for the code editing toolkit,
testing core functionality, error handling, and edge cases.
"""

import ast
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch
import pytest

from ai.agents.tools.code_editing_toolkit import (
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
    _validate_js_syntax,
    _detect_language,
    _is_valid_identifier,
    _get_project_files,
    _smart_rename_symbol,
)


class TestReplaceSymbolBody:
    """Test suite for replace_symbol_body function."""

    @pytest.fixture
    def temp_test_file(self):
        """Create a temporary Python file for testing."""
        content = '''def hello_world():
    """A simple greeting function."""
    print("Hello, World!")
    return "hello"

class TestClass:
    def method_one(self):
        return "method one"
        
    def method_two(self):
        return "method two"
'''
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.py', 
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(content)
            temp_path = f.name
        
        # Convert to relative path
        project_root = Path.cwd()
        relative_path = Path(temp_path).relative_to(project_root)
        
        yield str(relative_path)
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_replace_function_body_success(self, temp_test_file):
        """Test successful replacement of a function body."""
        new_body = '''"""Updated greeting function."""
    print("Hello, Updated World!")
    return "updated"'''
        
        result = replace_symbol_body(
            file_path=temp_test_file,
            symbol_name="hello_world",
            symbol_type="function",
            new_body=new_body,
            backup=False
        )
        
        assert "✅ Successfully replaced body" in result
        assert "hello_world" in result
        
        # Verify the file was actually modified
        project_root = Path.cwd()
        file_path = project_root / temp_test_file
        content = file_path.read_text()
        assert "Hello, Updated World!" in content
        assert "Updated greeting function" in content

    def test_replace_class_method_body(self, temp_test_file):
        """Test replacement of a class method body."""
        new_body = '''return "updated method one"'''
        
        result = replace_symbol_body(
            file_path=temp_test_file,
            symbol_name="method_one",
            symbol_type="function",
            new_body=new_body,
            backup=False
        )
        
        assert "✅ Successfully replaced body" in result
        
        # Verify the change
        project_root = Path.cwd()
        file_path = project_root / temp_test_file
        content = file_path.read_text()
        assert "updated method one" in content

    def test_replace_with_backup(self, temp_test_file):
        """Test replacement with backup creation."""
        new_body = '''print("With backup!")
    return "backup"'''
        
        result = replace_symbol_body(
            file_path=temp_test_file,
            symbol_name="hello_world",
            symbol_type="function",
            new_body=new_body,
            backup=True
        )
        
        assert "✅ Successfully replaced body" in result
        assert "💾 Backup created" in result
        
        # Check that backup was created
        project_root = Path.cwd()
        file_dir = (project_root / temp_test_file).parent
        backup_files = list(file_dir.glob("*.backup_*"))
        assert len(backup_files) > 0

    def test_replace_invalid_file(self):
        """Test replacement with non-existent file."""
        result = replace_symbol_body(
            file_path="non_existent_file.py",
            symbol_name="test_func",
            symbol_type="function",
            new_body="pass"
        )
        
        assert "Error: File 'non_existent_file.py' does not exist" in result

    def test_replace_symbol_not_found(self, temp_test_file):
        """Test replacement when symbol is not found."""
        result = replace_symbol_body(
            file_path=temp_test_file,
            symbol_name="non_existent_function",
            symbol_type="function",
            new_body="pass"
        )
        
        assert "Error: Symbol 'non_existent_function' of type 'function' not found" in result

    def test_replace_unsafe_path(self):
        """Test replacement with unsafe file path."""
        result = replace_symbol_body(
            file_path="../../../etc/passwd",
            symbol_name="test",
            symbol_type="function",
            new_body="malicious"
        )
        
        assert "Error: Invalid or unsafe path" in result

    def test_replace_with_syntax_error(self, temp_test_file):
        """Test replacement that would create syntax errors."""
        # Create invalid Python syntax
        new_body = '''print("Missing closing quote
    return "invalid"'''
        
        result = replace_symbol_body(
            file_path=temp_test_file,
            symbol_name="hello_world",
            symbol_type="function",
            new_body=new_body,
            validate_syntax=True
        )
        
        assert "Error: Syntax validation failed" in result


class TestInsertBeforeSymbol:
    """Test suite for insert_before_symbol function."""

    @pytest.fixture
    def temp_python_file(self):
        """Create a temporary Python file for testing."""
        content = '''import os

def first_function():
    return "first"

def second_function():
    return "second"

class MyClass:
    def __init__(self):
        self.value = 0
'''
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.py', 
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(content)
            temp_path = f.name
        
        project_root = Path.cwd()
        relative_path = Path(temp_path).relative_to(project_root)
        
        yield str(relative_path)
        
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_insert_before_function_success(self, temp_python_file):
        """Test successful insertion before a function."""
        new_code = '''def inserted_function():
    """This function was inserted."""
    return "inserted"
'''
        
        result = insert_before_symbol(
            file_path=temp_python_file,
            target_symbol="second_function",
            symbol_type="function",
            new_code=new_code,
            backup=False
        )
        
        assert "✅ Inserted" in result
        assert "before function 'second_function'" in result
        
        # Verify insertion
        project_root = Path.cwd()
        file_path = project_root / temp_python_file
        content = file_path.read_text()
        assert "inserted_function" in content
        assert content.find("inserted_function") < content.find("second_function")

    def test_insert_before_class(self, temp_python_file):
        """Test insertion before a class definition."""
        new_code = '''# Comment before class
CONSTANT = "before_class"
'''
        
        result = insert_before_symbol(
            file_path=temp_python_file,
            target_symbol="MyClass",
            symbol_type="class",
            new_code=new_code,
            backup=False
        )
        
        assert "✅ Inserted" in result
        
        # Verify insertion
        project_root = Path.cwd()
        file_path = project_root / temp_python_file
        content = file_path.read_text()
        assert "CONSTANT = \"before_class\"" in content
        assert content.find("before_class") < content.find("class MyClass")

    def test_insert_before_with_backup(self, temp_python_file):
        """Test insertion with backup creation."""
        new_code = 'print("Before function")\n'
        
        result = insert_before_symbol(
            file_path=temp_python_file,
            target_symbol="first_function",
            symbol_type="function",
            new_code=new_code,
            backup=True
        )
        
        assert "✅ Inserted" in result
        assert "💾 Backup created" in result

    def test_insert_before_symbol_not_found(self, temp_python_file):
        """Test insertion when target symbol is not found."""
        result = insert_before_symbol(
            file_path=temp_python_file,
            target_symbol="non_existent_function",
            symbol_type="function",
            new_code="pass",
            backup=False
        )
        
        assert "Error: Symbol 'non_existent_function' of type 'function' not found" in result

    def test_insert_before_invalid_file(self):
        """Test insertion with non-existent file."""
        result = insert_before_symbol(
            file_path="non_existent.py",
            target_symbol="test",
            symbol_type="function",
            new_code="pass"
        )
        
        assert "Error: File 'non_existent.py' does not exist" in result


class TestInsertAfterSymbol:
    """Test suite for insert_after_symbol function."""

    @pytest.fixture
    def temp_python_file(self):
        """Create a temporary Python file for testing."""
        content = '''def function_one():
    return 1

def function_two():
    return 2
    
class TestClass:
    pass
'''
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.py', 
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(content)
            temp_path = f.name
        
        project_root = Path.cwd()
        relative_path = Path(temp_path).relative_to(project_root)
        
        yield str(relative_path)
        
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_insert_after_function_success(self, temp_python_file):
        """Test successful insertion after a function."""
        new_code = '''def inserted_after():
    """Inserted after function_one."""
    return "after"
'''
        
        result = insert_after_symbol(
            file_path=temp_python_file,
            target_symbol="function_one",
            symbol_type="function",
            new_code=new_code,
            backup=False
        )
        
        assert "✅ Inserted" in result
        assert "after function 'function_one'" in result
        
        # Verify insertion order
        project_root = Path.cwd()
        file_path = project_root / temp_python_file
        content = file_path.read_text()
        assert "inserted_after" in content
        function_one_pos = content.find("def function_one")
        inserted_pos = content.find("def inserted_after")
        function_two_pos = content.find("def function_two")
        
        assert function_one_pos < inserted_pos < function_two_pos

    def test_insert_after_class(self, temp_python_file):
        """Test insertion after a class definition."""
        new_code = '''# Added after TestClass
GLOBAL_VAR = "after_class"
'''
        
        result = insert_after_symbol(
            file_path=temp_python_file,
            target_symbol="TestClass",
            symbol_type="class",
            new_code=new_code,
            backup=False
        )
        
        assert "✅ Inserted" in result
        
        # Verify insertion
        project_root = Path.cwd()
        file_path = project_root / temp_python_file
        content = file_path.read_text()
        assert "after_class" in content
        assert content.find("class TestClass") < content.find("after_class")


class TestRenameSymbol:
    """Test suite for rename_symbol function."""

    @pytest.fixture
    def temp_python_file(self):
        """Create a temporary Python file for testing."""
        content = '''def old_function_name():
    """Function to be renamed."""
    return old_function_name()

class OldClassName:
    def method_using_old_function(self):
        return old_function_name()
        
old_var = old_function_name()
'''
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.py', 
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(content)
            temp_path = f.name
        
        project_root = Path.cwd()
        relative_path = Path(temp_path).relative_to(project_root)
        
        yield str(relative_path)
        
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_rename_function_success(self, temp_python_file):
        """Test successful function renaming."""
        result = rename_symbol(
            file_path=temp_python_file,
            old_name="old_function_name",
            new_name="new_function_name",
            symbol_type="function",
            scope="file",
            backup=False
        )
        
        assert "✅ Renamed symbol" in result
        assert "old_function_name" in result
        assert "new_function_name" in result
        
        # Verify all occurrences were renamed
        project_root = Path.cwd()
        file_path = project_root / temp_python_file
        content = file_path.read_text()
        
        # Check function definition was renamed
        assert "def new_function_name():" in content
        assert "def old_function_name():" not in content
        
        # Check function calls were renamed
        assert "new_function_name()" in content

    def test_rename_class_success(self, temp_python_file):
        """Test successful class renaming."""
        result = rename_symbol(
            file_path=temp_python_file,
            old_name="OldClassName",
            new_name="NewClassName",
            symbol_type="class",
            scope="file",
            backup=False
        )
        
        assert "✅ Renamed symbol" in result
        
        # Verify class was renamed
        project_root = Path.cwd()
        file_path = project_root / temp_python_file
        content = file_path.read_text()
        assert "class NewClassName:" in content
        assert "class OldClassName:" not in content

    def test_rename_with_backup(self, temp_python_file):
        """Test renaming with backup creation."""
        result = rename_symbol(
            file_path=temp_python_file,
            old_name="old_function_name",
            new_name="renamed_function",
            symbol_type="function",
            scope="file",
            backup=True
        )
        
        assert "✅ Renamed symbol" in result
        assert "backup" in result

    def test_rename_invalid_identifier(self, temp_python_file):
        """Test renaming with invalid new identifier."""
        result = rename_symbol(
            file_path=temp_python_file,
            old_name="old_function_name",
            new_name="123invalid",
            symbol_type="function",
            scope="file"
        )
        
        assert "Error: '123invalid' is not a valid identifier" in result

    def test_rename_invalid_file(self):
        """Test renaming with non-existent file."""
        result = rename_symbol(
            file_path="non_existent.py",
            old_name="test",
            new_name="new_test",
            symbol_type="function",
            scope="file"
        )
        
        assert "Error: File 'non_existent.py' does not exist" in result


class TestExecuteShellCommand:
    """Test suite for execute_shell_command function."""

    def test_execute_simple_command_success(self):
        """Test execution of a simple, safe command."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Hello World\n"
            mock_run.return_value.stderr = ""
            
            result = execute_shell_command("echo 'Hello World'")
            
            assert "🔧 Command executed: echo 'Hello World'" in result
            assert "✅ Command completed successfully" in result
            assert "📤 Output:" in result
            assert "Hello World" in result

    def test_execute_command_failure(self):
        """Test execution of a command that fails."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = "Command not found\n"
            
            result = execute_shell_command("nonexistentcommand")
            
            assert "❌ Errors:" in result
            assert "Command not found" in result
            assert "⚠️  Command failed with exit code 1" in result

    def test_execute_unsafe_command(self):
        """Test execution of potentially dangerous commands."""
        dangerous_commands = [
            "rm -rf /",
            "del C:\\",
            "sudo rm file",
            "wget http://malicious.com",
            "echo 'test' > /etc/passwd"
        ]
        
        for cmd in dangerous_commands:
            result = execute_shell_command(cmd)
            assert "Error: Potentially unsafe command blocked" in result

    def test_execute_command_timeout(self):
        """Test command execution timeout."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("sleep", 1)
            
            result = execute_shell_command("sleep 10", timeout=1)
            
            assert "Error: Command timed out after 1 seconds" in result

    def test_execute_command_with_working_directory(self):
        """Test command execution with working directory."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "success\n"
            mock_run.return_value.stderr = ""
            
            # Create a temporary directory for testing
            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path.cwd()
                rel_temp_dir = Path(temp_dir).relative_to(project_root)
                
                result = execute_shell_command(
                    "echo 'test'", 
                    working_directory=str(rel_temp_dir)
                )
                
                assert "✅ Command completed successfully" in result
                assert str(rel_temp_dir) in result

    def test_execute_command_invalid_working_directory(self):
        """Test command execution with invalid working directory."""
        result = execute_shell_command(
            "echo 'test'", 
            working_directory="non_existent_dir"
        )
        
        assert "Error: Working directory does not exist" in result


class TestValidateCodeSyntax:
    """Test suite for validate_code_syntax function."""

    @pytest.fixture
    def temp_python_file(self):
        """Create a temporary Python file for testing."""
        content = '''def valid_function():
    """Valid Python function."""
    x = 1 + 2
    return x

class ValidClass:
    def __init__(self):
        self.value = 42
'''
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.py', 
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(content)
            temp_path = f.name
        
        project_root = Path.cwd()
        relative_path = Path(temp_path).relative_to(project_root)
        
        yield str(relative_path)
        
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def temp_invalid_python_file(self):
        """Create a temporary Python file with syntax errors."""
        content = '''def invalid_function(
    # Missing closing parenthesis
    print("This will fail"
    return "invalid"
'''
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.py', 
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(content)
            temp_path = f.name
        
        project_root = Path.cwd()
        relative_path = Path(temp_path).relative_to(project_root)
        
        yield str(relative_path)
        
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_validate_valid_python_syntax(self, temp_python_file):
        """Test validation of valid Python syntax."""
        result = validate_code_syntax(temp_python_file)
        
        assert "✅ Syntax validation passed" in result
        assert "Language: Python" in result
        assert "Statistics:" in result

    def test_validate_invalid_python_syntax(self, temp_invalid_python_file):
        """Test validation of invalid Python syntax."""
        result = validate_code_syntax(temp_invalid_python_file)
        
        assert "❌ Syntax validation failed" in result
        assert "Error:" in result
        assert "Line:" in result

    def test_validate_javascript_syntax(self):
        """Test validation of JavaScript syntax."""
        js_content = '''function testFunction() {
    const x = 1 + 2;
    return x;
}
'''
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.js', 
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(js_content)
            temp_path = f.name
        
        try:
            project_root = Path.cwd()
            relative_path = Path(temp_path).relative_to(project_root)
            
            result = validate_code_syntax(str(relative_path))
            
            assert "✅ Syntax validation passed" in result
            assert "Language: Javascript" in result
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_validate_invalid_javascript_syntax(self):
        """Test validation of invalid JavaScript syntax."""
        js_content = '''function invalidFunction() {
    const x = 1 + 2
    // Missing semicolon and mismatched braces
    return x;
'''
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.js', 
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(js_content)
            temp_path = f.name
        
        try:
            project_root = Path.cwd()
            relative_path = Path(temp_path).relative_to(project_root)
            
            result = validate_code_syntax(str(relative_path))
            
            assert "❌ Syntax validation failed" in result
            assert "Mismatched braces" in result
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_validate_unsupported_language(self):
        """Test validation of unsupported language."""
        content = '''some random content'''
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.xyz', 
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            project_root = Path.cwd()
            relative_path = Path(temp_path).relative_to(project_root)
            
            result = validate_code_syntax(str(relative_path))
            
            assert "Syntax validation not supported for language: unknown" in result
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_validate_non_existent_file(self):
        """Test validation of non-existent file."""
        result = validate_code_syntax("non_existent.py")
        
        assert "Error: File 'non_existent.py' does not exist" in result


class TestHelperFunctions:
    """Test suite for helper functions."""

    def test_is_safe_path_valid(self):
        """Test _is_safe_path with valid paths."""
        valid_paths = [
            "file.txt",
            "folder/file.txt",
            "deep/nested/folder/file.py",
            "src/main.py"
        ]
        
        for path in valid_paths:
            assert _is_safe_path(path) is True

    def test_is_safe_path_invalid(self):
        """Test _is_safe_path with invalid paths."""
        invalid_paths = [
            "/absolute/path",
            "../parent_folder",
            "folder/../../../etc/passwd",
            "C:\\Windows\\System32",
            "/etc/passwd",
            "/root/secret"
        ]
        
        for path in invalid_paths:
            assert _is_safe_path(path) is False

    def test_is_safe_command_valid(self):
        """Test _is_safe_command with safe commands."""
        safe_commands = [
            "ls -la",
            "python script.py",
            "node app.js",
            "make build"
        ]
        
        for cmd in safe_commands:
            assert _is_safe_command(cmd) is True

    def test_is_safe_command_invalid(self):
        """Test _is_safe_command with dangerous commands."""
        dangerous_commands = [
            "rm -rf /",
            "sudo rm file",
            "wget malicious.com",
            "echo 'data' > file",
            "command && dangerous",
            "$(malicious)",
            "command | dangerous"
        ]
        
        for cmd in dangerous_commands:
            assert _is_safe_command(cmd) is False

    def test_find_symbol_definition_function(self):
        """Test _find_symbol_definition for functions."""
        content = '''def test_function():
    """Test function."""
    return True

def another_function():
    pass
'''
        result = _find_symbol_definition(content, "test_function", "function")
        
        assert result is not None
        assert result["start_line"] == 0
        assert result["signature_line"] == 0
        assert "test_function" in content.splitlines()[result["start_line"]]

    def test_find_symbol_definition_class(self):
        """Test _find_symbol_definition for classes."""
        content = '''class TestClass:
    def __init__(self):
        pass
        
    def method(self):
        return True

class AnotherClass:
    pass
'''
        result = _find_symbol_definition(content, "TestClass", "class")
        
        assert result is not None
        assert result["start_line"] == 0
        assert "TestClass" in content.splitlines()[result["start_line"]]

    def test_find_symbol_definition_not_found(self):
        """Test _find_symbol_definition when symbol doesn't exist."""
        content = '''def existing_function():
    pass
'''
        result = _find_symbol_definition(content, "non_existent", "function")
        
        assert result is None

    def test_get_line_indentation(self):
        """Test _get_line_indentation function."""
        test_cases = [
            ("no_indent", 0),
            ("    four_spaces", 4),
            ("        eight_spaces", 8),
            ("\t\tone_tab", 2),  # Tabs count as single characters
            ("    \tmixed", 5),
        ]
        
        for line, expected_indent in test_cases:
            assert _get_line_indentation(line) == expected_indent

    def test_format_symbol_body(self):
        """Test _format_symbol_body function."""
        body = '''print("Hello")
return "test"'''
        formatted = _format_symbol_body(body, 0, "function")
        
        assert len(formatted) == 2
        assert formatted[0].startswith("    ")  # Should have 4-space indent
        assert "print" in formatted[0]
        assert "return" in formatted[1]

    def test_format_code_block(self):
        """Test _format_code_block function."""
        code = '''line1
line2
'''
        formatted = _format_code_block(code, 4)
        
        assert len(formatted) >= 2
        for line in formatted:
            if line.strip():  # Non-empty lines
                assert line.startswith("    ")  # Should have base indentation

    def test_validate_python_syntax_valid(self):
        """Test _validate_python_syntax with valid Python code."""
        valid_code = '''def test():
    x = 1 + 2
    return x

class Test:
    pass
'''
        result = _validate_python_syntax(valid_code)
        
        assert result["valid"] is True
        assert "stats" in result
        assert result["stats"]["functions"] == 1
        assert result["stats"]["classes"] == 1

    def test_validate_python_syntax_invalid(self):
        """Test _validate_python_syntax with invalid Python code."""
        invalid_code = '''def invalid_function(
    # Missing closing parenthesis
    return "error"
'''
        result = _validate_python_syntax(invalid_code)
        
        assert result["valid"] is False
        assert "error" in result
        assert "line_number" in result

    def test_validate_js_syntax_valid(self):
        """Test _validate_js_syntax with valid JavaScript-like code."""
        valid_js = '''function test() {
    const x = 1 + 2;
    return x;
}'''
        result = _validate_js_syntax(valid_js, "javascript")
        
        assert result["valid"] is True

    def test_validate_js_syntax_invalid(self):
        """Test _validate_js_syntax with invalid JavaScript-like code."""
        invalid_js = '''function test() {
    const x = 1 + 2;
    return x;
    // Missing closing brace'''
        result = _validate_js_syntax(invalid_js, "javascript")
        
        assert result["valid"] is False
        assert "Mismatched braces" in result["error"]

    def test_detect_language(self):
        """Test _detect_language function."""
        test_cases = [
            (".py", "python"),
            (".js", "javascript"),
            (".ts", "typescript"),
            (".java", "java"),
            (".cpp", "cpp"),
            (".c", "c"),
            (".h", "c"),
            (".rb", "ruby"),
            (".go", "go"),
            (".rs", "rust"),
            (".xyz", "unknown"),
        ]
        
        for extension, expected_lang in test_cases:
            test_path = Path(f"test{extension}")
            result = _detect_language(test_path)
            assert result == expected_lang

    def test_is_valid_identifier(self):
        """Test _is_valid_identifier function."""
        valid_identifiers = [
            "valid_name",
            "ValidName",
            "name123",
            "_private",
            "camelCase",
        ]
        
        invalid_identifiers = [
            "123invalid",
            "invalid-name",
            "invalid name",
            "__dunder__",
            "",
            "class",  # Python keyword
        ]
        
        for identifier in valid_identifiers:
            assert _is_valid_identifier(identifier) is True
            
        for identifier in invalid_identifiers:
            assert _is_valid_identifier(identifier) is False

    def test_smart_rename_symbol_function(self):
        """Test _smart_rename_symbol for function renaming."""
        content = '''def old_func():
    return old_func()

result = old_func()
'''
        new_content, replacements = _smart_rename_symbol(
            content, "old_func", "new_func", "function"
        )
        
        assert replacements > 0
        assert "new_func()" in new_content
        assert "def old_func():" not in new_content

    def test_smart_rename_symbol_class(self):
        """Test _smart_rename_symbol for class renaming."""
        content = '''class OldClass:
    pass

obj = OldClass()
'''
        new_content, replacements = _smart_rename_symbol(
            content, "OldClass", "NewClass", "class"
        )
        
        assert replacements > 0
        assert "NewClass" in new_content
        assert "class OldClass:" not in new_content

    def test_create_backup(self):
        """Test _create_backup function."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_path = Path(temp_file.name)
        
        try:
            # Create backup
            backup_path = _create_backup(temp_path)
            
            # Verify backup exists and contains same content
            assert backup_path.exists()
            assert backup_path.read_text() == temp_path.read_text()
            assert "backup_" in backup_path.name
            
            # Cleanup backup
            backup_path.unlink()
        finally:
            # Cleanup original
            if temp_path.exists():
                temp_path.unlink()


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for shell command tests."""
    with patch('ai.agents.tools.code_editing_toolkit.subprocess.run') as mock_run:
        yield mock_run


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        
        # Create some Python files
        (project_path / "main.py").write_text("def main(): pass")
        (project_path / "utils.py").write_text("def utility(): pass")
        
        # Create subdirectory with more files
        sub_dir = project_path / "submodule"
        sub_dir.mkdir()
        (sub_dir / "helper.py").write_text("def helper(): pass")
        
        # Change to temp directory for testing
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        yield project_path
        
        # Restore original directory
        os.chdir(original_cwd)


import subprocess


def test_get_project_files(temp_project_dir):
    """Test _get_project_files function."""
    files = _get_project_files(temp_project_dir)
    
    # Should find Python files
    py_files = [f for f in files if f.suffix == '.py']
    assert len(py_files) >= 3  # main.py, utils.py, helper.py
    
    # Should not include common build directories
    file_parts = [part for f in files for part in f.parts]
    assert ".git" not in file_parts
    assert "__pycache__" not in file_parts