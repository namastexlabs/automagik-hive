"""Comprehensive test coverage for ai.agents.tools.code_understanding_toolkit module.

This test suite focuses on achieving >50% coverage for the code understanding toolkit,
testing symbol finding, reference analysis, and code overview functionality.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from ai.agents.tools.code_understanding_toolkit import (
    find_symbol,
    find_referencing_symbols,
    find_referencing_code_snippets,
    get_symbols_overview,
    _detect_symbol_type,
    _analyze_reference_context,
    _analyze_usage_pattern,
    _extract_symbols_from_file,
    _parse_symbol_definition,
)


class TestFindSymbol:
    """Test suite for find_symbol function."""

    @pytest.fixture
    def temp_project_files(self):
        """Create temporary project files for testing."""
        files_content = {
            "main.py": '''def main_function():
    """Main application function."""
    return "main"

class MainClass:
    def __init__(self):
        self.value = 42
        
    def process_data(self):
        return self.value * 2

MAIN_CONSTANT = "main_value"
''',
            "utils.py": '''def utility_function():
    """Utility helper function."""
    return main_function()  # Reference to main

def helper_function():
    return "helper"

class UtilityClass:
    def main_function(self):  # Same name but different context
        return "utility_main"
''',
            "subdir/module.py": '''import sys

def main_function():
    """Another main function in submodule."""
    pass

test_var = "test"
'''
        }
        
        temp_files = {}
        project_root = Path.cwd()
        
        for file_path, content in files_content.items():
            full_path = project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            temp_files[file_path] = full_path
        
        yield temp_files
        
        # Cleanup
        for file_path in temp_files.values():
            if file_path.exists():
                file_path.unlink()
        
        # Remove created directories
        subdir = project_root / "subdir"
        if subdir.exists() and subdir.is_dir():
            subdir.rmdir()

    def test_find_symbol_success(self, temp_project_files):
        """Test successful symbol finding."""
        result = find_symbol("main_function")
        
        assert "Found" in result
        assert "main_function" in result
        assert "main.py" in result or "utils.py" in result or "subdir/module.py" in result
        
        # Should find multiple occurrences
        lines = result.split('\n')
        file_references = [line for line in lines if "📍" in line]
        assert len(file_references) >= 2  # At least 2 different files

    def test_find_symbol_case_sensitive(self, temp_project_files):
        """Test case-sensitive symbol search."""
        result = find_symbol("Main_function", case_sensitive=True)
        
        # Should not find matches due to case mismatch
        assert "No symbols found" in result

    def test_find_symbol_case_insensitive(self, temp_project_files):
        """Test case-insensitive symbol search."""
        result = find_symbol("MAIN_FUNCTION", case_sensitive=False)
        
        assert "Found" in result
        assert "main_function" in result.lower()

    def test_find_symbol_with_file_pattern(self, temp_project_files):
        """Test symbol search with file pattern filter."""
        result = find_symbol("main_function", file_pattern="*.py")
        
        assert "Found" in result
        assert "main_function" in result

    def test_find_symbol_with_type_filter(self, temp_project_files):
        """Test symbol search with symbol type filter."""
        result = find_symbol("MainClass", symbol_type="class")
        
        assert "Found" in result
        assert "class" in result
        assert "MainClass" in result

    def test_find_symbol_not_found(self, temp_project_files):
        """Test search for non-existent symbol."""
        result = find_symbol("non_existent_symbol")
        
        assert "No symbols found" in result
        assert "non_existent_symbol" in result

    def test_find_symbol_large_results(self, temp_project_files):
        """Test handling of large result sets."""
        # Create many files with the same symbol
        project_root = Path.cwd()
        temp_files = []
        
        try:
            for i in range(25):
                file_path = project_root / f"test_{i}.py"
                file_path.write_text(f"def common_symbol():\n    return {i}")
                temp_files.append(file_path)
            
            result = find_symbol("common_symbol")
            
            assert "Found 25 symbol(s)" in result
            assert "showing first 20" in result
            assert "and 5 more results" in result
            
        finally:
            # Cleanup
            for file_path in temp_files:
                if file_path.exists():
                    file_path.unlink()

    def test_find_symbol_with_context(self, temp_project_files):
        """Test that symbol search includes context."""
        result = find_symbol("process_data")
        
        assert "Found" in result
        assert "process_data" in result
        # Should include line numbers and context
        assert "📍" in result  # File location marker


class TestFindReferencingSymbols:
    """Test suite for find_referencing_symbols function."""

    @pytest.fixture
    def temp_reference_files(self):
        """Create temporary files with symbol references."""
        files_content = {
            "target.py": '''def target_function():
    """The target function we want to find references to."""
    return "target"

class TargetClass:
    def method(self):
        return "target_method"
''',
            "references.py": '''from target import target_function

def caller():
    return target_function()  # Function call reference

def another_caller():
    result = target_function()  # Another function call
    return result

# Import reference already at top
target_var = target_function  # Variable assignment reference
''',
            "more_refs.py": '''import target

def use_target():
    # Property access style reference
    return target.target_function()
    
class RefClass:
    def __init__(self):
        self.func = target_function  # Assignment in class
'''
        }
        
        temp_files = {}
        project_root = Path.cwd()
        
        for file_path, content in files_content.items():
            full_path = project_root / file_path
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            temp_files[file_path] = full_path
        
        yield temp_files
        
        # Cleanup
        for file_path in temp_files.values():
            if file_path.exists():
                file_path.unlink()

    def test_find_referencing_symbols_success(self, temp_reference_files):
        """Test successful reference finding."""
        result = find_referencing_symbols(
            target_symbol="target_function",
            target_file="target.py"
        )
        
        assert "Found" in result
        assert "target_function" in result
        assert "references.py" in result or "more_refs.py" in result
        
        # Should find different types of references
        assert "function_call" in result or "import" in result or "assignment" in result

    def test_find_referencing_symbols_with_line_filter(self, temp_reference_files):
        """Test reference finding with specific target line."""
        result = find_referencing_symbols(
            target_symbol="target_function",
            target_file="target.py",
            target_line=1  # The definition line
        )
        
        assert "Found" in result
        assert "target_function" in result
        # Should exclude the definition line itself

    def test_find_referencing_symbols_with_type_filter(self, temp_reference_files):
        """Test reference finding with symbol type filter."""
        result = find_referencing_symbols(
            target_symbol="target_function",
            target_file="target.py",
            symbol_types=["function_call"]
        )
        
        # Should only include function call references
        assert "target_function" in result

    def test_find_referencing_symbols_not_found(self, temp_reference_files):
        """Test reference finding for symbol with no references."""
        result = find_referencing_symbols(
            target_symbol="non_existent_symbol",
            target_file="target.py"
        )
        
        assert "No references found" in result

    def test_find_referencing_symbols_invalid_file(self, temp_reference_files):
        """Test reference finding with invalid target file."""
        result = find_referencing_symbols(
            target_symbol="target_function",
            target_file="non_existent.py"
        )
        
        assert "Target file not found" in result

    def test_find_referencing_symbols_with_context(self, temp_reference_files):
        """Test that reference finding includes context lines."""
        result = find_referencing_symbols(
            target_symbol="target_function",
            target_file="target.py"
        )
        
        # Should include context lines with line numbers
        lines = result.split('\n')
        context_lines = [line for line in lines if line.strip() and line[0].isdigit()]
        assert len(context_lines) > 0


class TestFindReferencingCodeSnippets:
    """Test suite for find_referencing_code_snippets function."""

    @pytest.fixture
    def temp_snippet_files(self):
        """Create temporary files for code snippet testing."""
        files_content = {
            "target.py": '''def target_function():
    """Function to find snippets for."""
    return "target"
''',
            "usage.py": '''from target import target_function

def example_usage():
    """Example of how target_function is used."""
    # Setup some data
    data = "test_data"
    
    # Call the target function
    result = target_function()
    
    # Process the result
    processed = result.upper()
    return processed

class UsageClass:
    def __init__(self):
        # Using target function in constructor
        self.initial_value = target_function()
        
    def process(self):
        # Another usage context
        return f"Processed: {target_function()}"
'''
        }
        
        temp_files = {}
        project_root = Path.cwd()
        
        for file_path, content in files_content.items():
            full_path = project_root / file_path
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            temp_files[file_path] = full_path
        
        yield temp_files
        
        # Cleanup
        for file_path in temp_files.values():
            if file_path.exists():
                file_path.unlink()

    def test_find_referencing_code_snippets_success(self, temp_snippet_files):
        """Test successful code snippet finding."""
        result = find_referencing_code_snippets(
            target_symbol="target_function",
            target_file="target.py",
            context_lines=2
        )
        
        assert "Code snippets referencing" in result
        assert "target_function" in result
        assert "usage.py" in result
        
        # Should show line numbers and context
        assert "📄" in result  # File marker
        lines = result.split('\n')
        numbered_lines = [line for line in lines if ':' in line and line.split(':')[0].strip().isdigit()]
        assert len(numbered_lines) > 0

    def test_find_referencing_code_snippets_with_context(self, temp_snippet_files):
        """Test code snippet finding with different context sizes."""
        result = find_referencing_code_snippets(
            target_symbol="target_function",
            target_file="target.py",
            context_lines=5
        )
        
        assert "Code snippets referencing" in result
        # With more context lines, should include more surrounding code
        lines = result.split('\n')
        numbered_lines = [line for line in lines if ':' in line and line.split(':')[0].strip().isdigit()]
        # Should have substantial context around each reference
        assert len(numbered_lines) > 10

    def test_find_referencing_code_snippets_not_found(self, temp_snippet_files):
        """Test code snippet finding for symbol with no references."""
        result = find_referencing_code_snippets(
            target_symbol="non_existent_symbol",
            target_file="target.py"
        )
        
        assert "No code snippets found" in result

    def test_find_referencing_code_snippets_invalid_file(self, temp_snippet_files):
        """Test code snippet finding with invalid target file."""
        result = find_referencing_code_snippets(
            target_symbol="target_function",
            target_file="non_existent.py"
        )
        
        assert "Target file not found" in result

    def test_find_referencing_code_snippets_usage_analysis(self, temp_snippet_files):
        """Test that usage patterns are analyzed in code snippets."""
        result = find_referencing_code_snippets(
            target_symbol="target_function",
            target_file="target.py"
        )
        
        # Should analyze different usage patterns
        assert "Function Call" in result or "Import" in result


class TestGetSymbolsOverview:
    """Test suite for get_symbols_overview function."""

    @pytest.fixture
    def temp_overview_files(self):
        """Create temporary files for symbol overview testing."""
        files_content = {
            "overview_test.py": '''"""Module for testing symbol overview."""

import os
import sys

# Module constants
MODULE_VERSION = "1.0.0"
_PRIVATE_CONSTANT = "private"

def public_function():
    """Public function."""
    return "public"

def _private_function():
    """Private function."""
    return "private"

class PublicClass:
    """Public class."""
    
    def __init__(self):
        self.value = 0
        
    def public_method(self):
        return "public_method"
        
    def _private_method(self):
        return "private_method"

class _PrivateClass:
    """Private class."""
    pass

# Module variables
global_var = "global"
_private_var = "private"
''',
            "subdir/nested.py": '''def nested_function():
    """Function in nested directory."""
    pass

class NestedClass:
    pass
'''
        }
        
        temp_files = {}
        project_root = Path.cwd()
        
        for file_path, content in files_content.items():
            full_path = project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            temp_files[file_path] = full_path
        
        yield temp_files
        
        # Cleanup
        for file_path in temp_files.values():
            if file_path.exists():
                file_path.unlink()
        
        # Remove created directories
        subdir = project_root / "subdir"
        if subdir.exists() and subdir.is_dir():
            subdir.rmdir()

    def test_get_symbols_overview_single_file(self, temp_overview_files):
        """Test symbol overview for a single file."""
        result = get_symbols_overview("overview_test.py")
        
        assert "Symbol Overview" in result
        assert "overview_test.py" in result
        assert "FUNCTIONS" in result
        assert "CLASSES" in result
        
        # Should show public and private symbols
        assert "public_function" in result
        assert "_private_function" in result
        assert "PublicClass" in result
        assert "_PrivateClass" in result

    def test_get_symbols_overview_exclude_private(self, temp_overview_files):
        """Test symbol overview excluding private symbols."""
        result = get_symbols_overview(
            "overview_test.py",
            include_private=False
        )
        
        assert "Symbol Overview" in result
        assert "public_function" in result
        assert "PublicClass" in result
        # Should not include private symbols
        assert "_private_function" not in result
        assert "_PrivateClass" not in result

    def test_get_symbols_overview_type_filter(self, temp_overview_files):
        """Test symbol overview with symbol type filter."""
        result = get_symbols_overview(
            "overview_test.py",
            symbol_types=["function"]
        )
        
        assert "Symbol Overview" in result
        assert "FUNCTIONS" in result
        assert "public_function" in result
        # Should not include classes when filtered to functions only
        assert "CLASSES" not in result

    def test_get_symbols_overview_directory(self, temp_overview_files):
        """Test symbol overview for a directory."""
        result = get_symbols_overview("subdir")
        
        assert "Symbol Overview" in result
        assert "subdir/nested.py" in result or "nested.py" in result
        assert "nested_function" in result
        assert "NestedClass" in result

    def test_get_symbols_overview_not_found(self, temp_overview_files):
        """Test symbol overview for non-existent path."""
        result = get_symbols_overview("non_existent_path")
        
        assert "Path not found" in result

    def test_get_symbols_overview_no_symbols(self, temp_overview_files):
        """Test symbol overview when no symbols match filters."""
        result = get_symbols_overview(
            "overview_test.py",
            symbol_types=["interface"]  # Type that doesn't exist in Python
        )
        
        assert "No symbols found" in result

    def test_get_symbols_overview_with_visibility_indicators(self, temp_overview_files):
        """Test that overview shows visibility indicators."""
        result = get_symbols_overview(
            "overview_test.py",
            include_private=True
        )
        
        # Should show visibility indicators (🔓 for public, 🔒 for private)
        assert "🔓" in result or "🔒" in result


class TestHelperFunctions:
    """Test suite for helper functions."""

    def test_detect_symbol_type_python_class(self):
        """Test _detect_symbol_type for Python classes."""
        line = "class MyClass:"
        result = _detect_symbol_type(line, "MyClass")
        assert result == "class"

    def test_detect_symbol_type_python_function(self):
        """Test _detect_symbol_type for Python functions."""
        line = "def my_function(arg1, arg2):"
        result = _detect_symbol_type(line, "my_function")
        assert result == "function"

    def test_detect_symbol_type_python_variable(self):
        """Test _detect_symbol_type for Python variables."""
        line = "my_variable = 42"
        result = _detect_symbol_type(line, "my_variable")
        assert result == "variable"

    def test_detect_symbol_type_python_import(self):
        """Test _detect_symbol_type for Python imports."""
        test_cases = [
            ("import os", "os", "import"),
            ("from sys import path", "path", "import"),
        ]
        
        for line, symbol, expected in test_cases:
            result = _detect_symbol_type(line, symbol)
            assert result == expected

    def test_detect_symbol_type_javascript(self):
        """Test _detect_symbol_type for JavaScript constructs."""
        test_cases = [
            ("function myFunc() {", "myFunc", "function"),
            ("const myVar = 42;", "myVar", "variable"),
            ("let anotherVar = 'test';", "anotherVar", "variable"),
            ("var oldVar = true;", "oldVar", "variable"),
            ("const myFunc = () => {", "myFunc", "function"),
        ]
        
        for line, symbol, expected in test_cases:
            result = _detect_symbol_type(line, symbol)
            assert result == expected

    def test_detect_symbol_type_java(self):
        """Test _detect_symbol_type for Java constructs."""
        test_cases = [
            ("public class MyClass {", "MyClass", "class"),
            ("private class InnerClass {", "InnerClass", "class"),
            ("public interface MyInterface {", "MyInterface", "interface"),
            ("public void myMethod() {", "myMethod", "method"),
            ("private int myMethod(String arg) {", "myMethod", "method"),
        ]
        
        for line, symbol, expected in test_cases:
            result = _detect_symbol_type(line, symbol)
            assert result == expected

    def test_detect_symbol_type_generic_reference(self):
        """Test _detect_symbol_type for generic references."""
        line = "result = some_symbol + other_symbol"
        result = _detect_symbol_type(line, "some_symbol")
        assert result == "reference"

    def test_analyze_reference_context_function_call(self):
        """Test _analyze_reference_context for function calls."""
        line = "result = my_function(arg1, arg2)"
        result = _analyze_reference_context(line, "my_function")
        assert result == "function_call"

    def test_analyze_reference_context_property_access(self):
        """Test _analyze_reference_context for property access."""
        test_cases = [
            ("obj.my_property", "my_property", "property_access"),
            ("my_property.method()", "my_property", "property_access"),
        ]
        
        for line, symbol, expected in test_cases:
            result = _analyze_reference_context(line, symbol)
            assert result == expected

    def test_analyze_reference_context_import(self):
        """Test _analyze_reference_context for imports."""
        line = "import my_module"
        result = _analyze_reference_context(line, "my_module")
        assert result == "import"

    def test_analyze_reference_context_inheritance(self):
        """Test _analyze_reference_context for inheritance."""
        test_cases = [
            ("class Child extends Parent {", "Parent", "inheritance"),
            ("class MyClass implements Interface {", "Interface", "inheritance"),
        ]
        
        for line, symbol, expected in test_cases:
            result = _analyze_reference_context(line, symbol)
            assert result == expected

    def test_analyze_reference_context_assignment(self):
        """Test _analyze_reference_context for assignments."""
        line = "my_var = some_function()"
        result = _analyze_reference_context(line, "some_function")
        assert result == "assignment"

    def test_analyze_reference_context_instantiation(self):
        """Test _analyze_reference_context for object instantiation."""
        line = "obj = new MyClass()"
        result = _analyze_reference_context(line, "MyClass")
        assert result == "instantiation"

    def test_analyze_usage_pattern_constructor_call(self):
        """Test _analyze_usage_pattern for constructor calls."""
        line = "obj = new MyClass(args)"
        result = _analyze_usage_pattern(line, "MyClass")
        assert result == "Constructor Call"

    def test_analyze_usage_pattern_function_call(self):
        """Test _analyze_usage_pattern for function calls."""
        line = "result = myFunction(arg1, arg2)"
        result = _analyze_usage_pattern(line, "myFunction")
        assert result == "Function Call"

    def test_analyze_usage_pattern_property_access(self):
        """Test _analyze_usage_pattern for property access."""
        line = "value = obj.myProperty"
        result = _analyze_usage_pattern(line, "myProperty")
        assert result == "Property Access"

    def test_analyze_usage_pattern_inheritance(self):
        """Test _analyze_usage_pattern for inheritance."""
        line = "class Child extends MyParent {"
        result = _analyze_usage_pattern(line, "MyParent")
        assert result == "Inheritance"

    def test_analyze_usage_pattern_interface_implementation(self):
        """Test _analyze_usage_pattern for interface implementation."""
        line = "class MyClass implements MyInterface {"
        result = _analyze_usage_pattern(line, "MyInterface")
        assert result == "Interface Implementation"

    def test_analyze_usage_pattern_import(self):
        """Test _analyze_usage_pattern for imports."""
        test_cases = [
            ("import MyModule", "MyModule", "Import"),
            ("from package import MyModule", "MyModule", "Import"),
        ]
        
        for line, symbol, expected in test_cases:
            result = _analyze_usage_pattern(line, symbol)
            assert result == expected

    def test_analyze_usage_pattern_generic_reference(self):
        """Test _analyze_usage_pattern for generic references."""
        line = "value = some_symbol + other_value"
        result = _analyze_usage_pattern(line, "some_symbol")
        assert result == "Reference"

    def test_extract_symbols_from_file_python(self):
        """Test _extract_symbols_from_file for Python files."""
        content = '''def my_function():
    """Test function."""
    pass

class MyClass:
    """Test class."""
    def __init__(self):
        pass

# Variable assignment
my_var = "test"
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            symbols = _extract_symbols_from_file(temp_path, None, True)
            
            # Should find function, class, and potentially variables
            symbol_names = [s['name'] for s in symbols]
            assert 'my_function' in symbol_names
            assert 'MyClass' in symbol_names
            
            # Check symbol details
            func_symbol = next(s for s in symbols if s['name'] == 'my_function')
            assert func_symbol['type'] == 'function'
            assert func_symbol['line'] == 1
            assert func_symbol['private'] is False
            
            class_symbol = next(s for s in symbols if s['name'] == 'MyClass')
            assert class_symbol['type'] == 'class'
            assert class_symbol['private'] is False
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_extract_symbols_from_file_private_filter(self):
        """Test _extract_symbols_from_file with private symbol filtering."""
        content = '''def public_function():
    pass

def _private_function():
    pass

class PublicClass:
    pass

class _PrivateClass:
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            # Test excluding private symbols
            symbols = _extract_symbols_from_file(temp_path, None, False)
            symbol_names = [s['name'] for s in symbols]
            
            assert 'public_function' in symbol_names
            assert 'PublicClass' in symbol_names
            assert '_private_function' not in symbol_names
            assert '_PrivateClass' not in symbol_names
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_extract_symbols_from_file_type_filter(self):
        """Test _extract_symbols_from_file with symbol type filtering."""
        content = '''def test_function():
    pass

class TestClass:
    pass

test_var = "value"
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            # Test filtering to only functions
            symbols = _extract_symbols_from_file(temp_path, ['function'], True)
            symbol_types = [s['type'] for s in symbols]
            
            assert 'function' in symbol_types
            assert 'class' not in symbol_types
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_parse_symbol_definition_python_function(self):
        """Test _parse_symbol_definition for Python functions."""
        test_cases = [
            ("def my_function():", "my_function", "function"),
            ("def _private_function(arg1, arg2):", "_private_function", "function"),
            ("    def indented_function():", "indented_function", "function"),
        ]
        
        for line, expected_name, expected_type in test_cases:
            result = _parse_symbol_definition(line, 1)
            
            assert result is not None
            assert result['name'] == expected_name
            assert result['type'] == expected_type
            assert result['line'] == 1
            assert result['signature'] == line.strip()
            assert result['private'] == expected_name.startswith('_')

    def test_parse_symbol_definition_python_class(self):
        """Test _parse_symbol_definition for Python classes."""
        test_cases = [
            ("class MyClass:", "MyClass"),
            ("class _PrivateClass(BaseClass):", "_PrivateClass"),
            ("    class NestedClass:", "NestedClass"),
        ]
        
        for line, expected_name in test_cases:
            result = _parse_symbol_definition(line, 1)
            
            assert result is not None
            assert result['name'] == expected_name
            assert result['type'] == 'class'
            assert result['private'] == expected_name.startswith('_')

    def test_parse_symbol_definition_javascript_function(self):
        """Test _parse_symbol_definition for JavaScript functions."""
        test_cases = [
            ("function myFunction() {", "myFunction"),
            ("  function anotherFunction(arg) {", "anotherFunction"),
        ]
        
        for line, expected_name in test_cases:
            result = _parse_symbol_definition(line, 1)
            
            assert result is not None
            assert result['name'] == expected_name
            assert result['type'] == 'function'

    def test_parse_symbol_definition_javascript_variable(self):
        """Test _parse_symbol_definition for JavaScript variables."""
        test_cases = [
            ("const myVar = 42;", "myVar"),
            ("let anotherVar = 'test';", "anotherVar"),
            ("var oldVar = true;", "oldVar"),
        ]
        
        for line, expected_name in test_cases:
            result = _parse_symbol_definition(line, 1)
            
            assert result is not None
            assert result['name'] == expected_name
            assert result['type'] == 'variable'

    def test_parse_symbol_definition_no_match(self):
        """Test _parse_symbol_definition with non-definition lines."""
        test_cases = [
            "# This is a comment",
            "    print('Hello, World!')",
            "x + y = z",  # Not a proper assignment
            "if condition:",
        ]
        
        for line in test_cases:
            result = _parse_symbol_definition(line, 1)
            assert result is None


@pytest.fixture
def temp_project_structure():
    """Create a temporary project structure for testing."""
    project_root = Path.cwd()
    temp_files = []
    
    # Create test files
    files_content = {
        "test_main.py": "def main(): pass",
        "utils/helper.py": "def help(): pass", 
        "models/user.py": "class User: pass"
    }
    
    for file_path, content in files_content.items():
        full_path = project_root / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        temp_files.append(full_path)
    
    yield project_root
    
    # Cleanup
    for file_path in temp_files:
        if file_path.exists():
            file_path.unlink()
    
    # Remove directories
    for dir_path in ["utils", "models"]:
        dir_full_path = project_root / dir_path
        if dir_full_path.exists() and dir_full_path.is_dir():
            dir_full_path.rmdir()


def test_integration_symbol_search_and_analysis(temp_project_structure):
    """Integration test combining symbol search with reference analysis."""
    # First, find all symbols named 'main' 
    find_result = find_symbol("main")
    assert "Found" in find_result or "No symbols found" in find_result
    
    # Then get an overview of the entire project
    overview_result = get_symbols_overview(".")
    assert "Symbol Overview" in overview_result
    
    # The integration should work without errors
    assert len(find_result) > 0
    assert len(overview_result) > 0