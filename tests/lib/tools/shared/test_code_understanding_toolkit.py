"""
Comprehensive test suite for code_understanding_toolkit.py

Tests all public functions and helper functions for code analysis and symbol discovery.
Focuses on achieving 50%+ coverage with real-world scenarios.
"""

import os
import tempfile
from pathlib import Path

import pytest

from lib.tools.shared.code_understanding_toolkit import (
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


class TestSymbolTypeDetection:
    """Test symbol type detection from code context."""

    def test_detect_python_functions(self):
        """Test detecting Python function definitions."""
        assert _detect_symbol_type("def my_function(param):", "my_function") == "function"
        assert _detect_symbol_type("    def indented_function():", "indented_function") == "function"
        assert _detect_symbol_type("async def async_function():", "async_function") == "function"

    def test_detect_python_classes(self):
        """Test detecting Python class definitions."""
        assert _detect_symbol_type("class MyClass:", "MyClass") == "class"
        assert _detect_symbol_type("class MyClass(BaseClass):", "MyClass") == "class"
        assert _detect_symbol_type("    class NestedClass:", "NestedClass") == "class"

    def test_detect_python_variables(self):
        """Test detecting Python variable assignments."""
        assert _detect_symbol_type("my_var = 'value'", "my_var") == "variable"
        assert _detect_symbol_type("    indented_var = 123", "indented_var") == "variable"
        assert _detect_symbol_type("CONSTANT = 'constant'", "CONSTANT") == "variable"

    def test_detect_python_imports(self):
        """Test detecting Python import statements."""
        assert _detect_symbol_type("import os", "os") == "import"
        assert _detect_symbol_type("from pathlib import Path", "Path") == "import"
        assert _detect_symbol_type("    import nested_import", "nested_import") == "import"

    def test_detect_javascript_functions(self):
        """Test detecting JavaScript function patterns."""
        assert _detect_symbol_type("function myFunction() {", "myFunction") == "function"
        assert _detect_symbol_type("const myFunc = () => {", "myFunc") == "function"
        assert _detect_symbol_type("const func = function() {", "func") == "function"

    def test_detect_javascript_variables(self):
        """Test detecting JavaScript variable declarations."""
        assert _detect_symbol_type("const myConst = 'value'", "myConst") == "variable"
        assert _detect_symbol_type("let myLet = 123", "myLet") == "variable"
        assert _detect_symbol_type("var myVar = true", "myVar") == "variable"

    def test_detect_typescript_interfaces(self):
        """Test detecting TypeScript interface definitions."""
        assert _detect_symbol_type("interface MyInterface {", "MyInterface") == "interface"
        assert _detect_symbol_type("export interface ExportedInterface {", "ExportedInterface") == "interface"

    def test_detect_typescript_types(self):
        """Test detecting TypeScript type definitions."""
        assert _detect_symbol_type("type MyType = string", "MyType") == "type"
        assert _detect_symbol_type("type UnionType = string | number", "UnionType") == "type"

    def test_detect_java_classes_methods(self):
        """Test detecting Java class and method patterns."""
        assert _detect_symbol_type("public class MyClass {", "MyClass") == "class"
        assert _detect_symbol_type("private class InnerClass {", "InnerClass") == "class"
        assert _detect_symbol_type("public interface MyInterface {", "MyInterface") == "interface"
        assert _detect_symbol_type("public void myMethod() {", "myMethod") == "method"
        assert _detect_symbol_type("private int calculate(int x) {", "calculate") == "method"

    def test_detect_generic_references(self):
        """Test detecting generic symbol references."""
        assert _detect_symbol_type("result = someFunction(params)", "someFunction") == "function"
        assert _detect_symbol_type("value = myVariable", "myVariable") == "variable"
        assert _detect_symbol_type("// Comment mentioning symbol", "symbol") == "reference"


class TestReferenceContextAnalysis:
    """Test analysis of how symbols are referenced."""

    def test_analyze_function_calls(self):
        """Test detecting function call contexts."""
        assert _analyze_reference_context("result = myFunction(param)", "myFunction") == "function_call"
        assert _analyze_reference_context("    myFunction()", "myFunction") == "function_call"
        assert _analyze_reference_context("await asyncFunction(data)", "asyncFunction") == "function_call"

    def test_analyze_property_access(self):
        """Test detecting property access patterns."""
        assert _analyze_reference_context("obj.myProperty", "myProperty") == "property_access"
        assert _analyze_reference_context("myObject.method()", "myObject") == "property_access"
        assert _analyze_reference_context("this.attribute = value", "attribute") == "property_access"

    def test_analyze_import_statements(self):
        """Test detecting import contexts."""
        assert _analyze_reference_context("import myModule from 'path'", "myModule") == "import"
        assert _analyze_reference_context("from package import myFunction", "myFunction") == "import"
        assert _analyze_reference_context("const { myExport } = require('module')", "myExport") == "import"

    def test_analyze_inheritance_patterns(self):
        """Test detecting inheritance and implementation."""
        assert _analyze_reference_context("class Child extends Parent {", "Parent") == "inheritance"
        assert _analyze_reference_context("class Implementation implements Interface {", "Interface") == "inheritance"

    def test_analyze_assignments(self):
        """Test detecting assignment contexts."""
        assert _analyze_reference_context("result = myVariable", "myVariable") == "assignment"
        assert _analyze_reference_context("let newVar = oldVar", "oldVar") == "assignment"

    def test_analyze_instantiation(self):
        """Test detecting object instantiation."""
        assert _analyze_reference_context("obj = new MyClass()", "MyClass") == "instantiation"
        assert _analyze_reference_context("instance = new MyClass(params)", "MyClass") == "instantiation"

    def test_analyze_generic_references(self):
        """Test fallback to generic reference."""
        assert _analyze_reference_context("// Comment about mySymbol", "mySymbol") == "reference"
        assert _analyze_reference_context("print mySymbol", "mySymbol") == "reference"


class TestUsagePatternAnalysis:
    """Test advanced usage pattern analysis."""

    def test_analyze_constructor_calls(self):
        """Test detecting constructor call patterns."""
        assert _analyze_usage_pattern("obj = new MyClass()", "MyClass") == "Constructor Call"
        assert _analyze_usage_pattern("instance = new MyClass(param1, param2)", "MyClass") == "Constructor Call"

    def test_analyze_function_calls_with_regex(self):
        """Test function call detection using regex."""
        assert _analyze_usage_pattern("result = myFunction()", "myFunction") == "Function Call"
        assert _analyze_usage_pattern("await myFunction(params)", "myFunction") == "Function Call"

    def test_analyze_property_access_with_regex(self):
        """Test property access detection using regex."""
        assert _analyze_usage_pattern("obj.myProperty", "myProperty") == "Property Access"
        assert _analyze_usage_pattern("this.myMethod()", "myMethod") == "Property Access"

    def test_analyze_inheritance_patterns_with_regex(self):
        """Test inheritance detection using regex."""
        assert _analyze_usage_pattern("class Child extends Parent", "Parent") == "Inheritance"
        assert _analyze_usage_pattern("class Impl implements Interface", "Interface") == "Interface Implementation"

    def test_analyze_import_patterns_with_regex(self):
        """Test import detection using regex."""
        assert _analyze_usage_pattern("import { myFunction } from 'module'", "myFunction") == "Import"
        assert _analyze_usage_pattern("from package import myClass", "myClass") == "Import"

    def test_analyze_fallback_reference(self):
        """Test fallback to generic reference."""
        assert _analyze_usage_pattern("some random text with mySymbol", "mySymbol") == "Reference"


class TestSymbolDefinitionParsing:
    """Test parsing of symbol definitions from code lines."""

    def test_parse_python_function_definitions(self):
        """Test parsing Python function definitions."""
        symbol = _parse_symbol_definition("def my_function(param1, param2):", 10)
        assert symbol is not None
        assert symbol["name"] == "my_function"
        assert symbol["type"] == "function"
        assert symbol["line"] == 10
        assert not symbol["private"]

        # Private function
        private_symbol = _parse_symbol_definition("def _private_function():", 15)
        assert private_symbol is not None
        assert private_symbol["private"] is True

    def test_parse_python_class_definitions(self):
        """Test parsing Python class definitions."""
        symbol = _parse_symbol_definition("class MyClass(BaseClass):", 20)
        assert symbol is not None
        assert symbol["name"] == "MyClass"
        assert symbol["type"] == "class"
        assert symbol["line"] == 20
        assert not symbol["private"]

        # Private class
        private_symbol = _parse_symbol_definition("class _PrivateClass:", 25)
        assert private_symbol is not None
        assert private_symbol["private"] is True

    def test_parse_javascript_function_definitions(self):
        """Test parsing JavaScript function definitions."""
        symbol = _parse_symbol_definition("function myFunction() {", 30)
        assert symbol is not None
        assert symbol["name"] == "myFunction"
        assert symbol["type"] == "function"
        assert symbol["line"] == 30

        # Arrow function won't match this pattern
        arrow_symbol = _parse_symbol_definition("const myArrow = () => {", 35)
        assert arrow_symbol is None

    def test_parse_javascript_variable_definitions(self):
        """Test parsing JavaScript variable definitions."""
        const_symbol = _parse_symbol_definition("const myConst = 'value'", 40)
        assert const_symbol is not None
        assert const_symbol["name"] == "myConst"
        assert const_symbol["type"] == "variable"
        assert const_symbol["line"] == 40

        let_symbol = _parse_symbol_definition("let myLet = 123", 45)
        assert let_symbol is not None
        assert let_symbol["name"] == "myLet"

        var_symbol = _parse_symbol_definition("var myVar = true", 50)
        assert var_symbol is not None
        assert var_symbol["name"] == "myVar"

    def test_parse_invalid_definitions(self):
        """Test parsing invalid or non-matching lines."""
        assert _parse_symbol_definition("// This is a comment", 10) is None
        assert _parse_symbol_definition("import os", 15) is None
        assert _parse_symbol_definition("result = function_call()", 20) is None
        assert _parse_symbol_definition("", 25) is None


class TestSymbolExtraction:
    """Test extracting symbols from files."""

    def test_extract_symbols_from_python_file(self):
        """Test extracting symbols from Python source."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write("""
# Test Python file
import os
from pathlib import Path

DEBUG = True
_private_var = "secret"

class MyClass:
    def __init__(self):
        self.value = None
    
    def public_method(self):
        return self.value
    
    def _private_method(self):
        return "private"

def public_function():
    return "public"

def _private_function():
    return "private"
""")
            temp_file.flush()
            
            try:
                file_path = Path(temp_file.name)
                symbols = _extract_symbols_from_file(file_path, None, True)  # Include private
                
                symbol_names = [s["name"] for s in symbols]
                symbol_types = [s["type"] for s in symbols]
                
                # Check that we found expected symbols
                assert "MyClass" in symbol_names
                assert "public_function" in symbol_names
                assert "_private_function" in symbol_names
                assert "__init__" in symbol_names
                assert "public_method" in symbol_names
                assert "_private_method" in symbol_names
                
                # Check types
                assert "class" in symbol_types
                assert "function" in symbol_types
                
                # Check private detection
                class_symbol = next(s for s in symbols if s["name"] == "MyClass")
                assert not class_symbol["private"]
                
                private_func_symbol = next(s for s in symbols if s["name"] == "_private_function")
                assert private_func_symbol["private"]
                
            finally:
                os.unlink(temp_file.name)

    def test_extract_symbols_with_type_filter(self):
        """Test extracting symbols with type filtering."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write("""
class TestClass:
    pass

def test_function():
    pass

test_variable = "value"
""")
            temp_file.flush()
            
            try:
                file_path = Path(temp_file.name)
                
                # Filter for only classes
                class_symbols = _extract_symbols_from_file(file_path, ["class"], True)
                assert len(class_symbols) == 1
                assert class_symbols[0]["name"] == "TestClass"
                
                # Filter for only functions
                function_symbols = _extract_symbols_from_file(file_path, ["function"], True)
                assert len(function_symbols) == 1
                assert function_symbols[0]["name"] == "test_function"
                
            finally:
                os.unlink(temp_file.name)

    def test_extract_symbols_exclude_private(self):
        """Test extracting symbols excluding private ones."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write("""
class PublicClass:
    pass

class _PrivateClass:
    pass

def public_function():
    pass

def _private_function():
    pass
""")
            temp_file.flush()
            
            try:
                file_path = Path(temp_file.name)
                symbols = _extract_symbols_from_file(file_path, None, False)  # Exclude private
                
                symbol_names = [s["name"] for s in symbols]
                assert "PublicClass" in symbol_names
                assert "public_function" in symbol_names
                assert "_PrivateClass" not in symbol_names
                assert "_private_function" not in symbol_names
                
            finally:
                os.unlink(temp_file.name)


class TestFindSymbolFunction:
    """Test the main find_symbol function."""

    def test_find_symbol_in_project_structure(self):
        """Test finding symbols across a project structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                # Create project structure
                src_dir = project_root / "src"
                src_dir.mkdir()
                test_dir = project_root / "tests"
                test_dir.mkdir()
                
                # Create Python files
                (src_dir / "main.py").write_text("""
def target_function():
    return "main"

class TargetClass:
    pass
""")
                
                (src_dir / "utils.py").write_text("""
def target_function():
    return "utils"

helper_var = "target_function usage"
""")
                
                (test_dir / "test_main.py").write_text("""
def test_target_function():
    assert True
""")
                
                # Test finding function across files
                result = find_symbol("target_function")
                
                assert "Found" in result
                assert "src/main.py" in result
                assert "src/utils.py" in result
                assert "test_main.py" in result
                
            finally:
                os.chdir(original_cwd)

    def test_find_symbol_with_type_filter(self):
        """Test finding symbols with type filtering."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                test_file = project_root / "test.py"
                test_file.write_text("""
def my_target():  # function
    return "function"

my_target = "variable"  # variable

class MyTarget:  # class (different case)
    pass
""")
                
                # Find only functions
                result = find_symbol("my_target", symbol_type="function")
                assert "Found" in result
                assert "function" in result
                lines = result.split('\n')
                function_lines = [line for line in lines if "def my_target" in line]
                assert len(function_lines) >= 1
                
            finally:
                os.chdir(original_cwd)

    def test_find_symbol_case_sensitivity(self):
        """Test case sensitive vs insensitive search."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                test_file = project_root / "test.py"
                test_file.write_text("""
def MyFunction():
    pass

def myfunction():
    pass

def MYFUNCTION():
    pass
""")
                
                # Case sensitive search
                result_sensitive = find_symbol("MyFunction", case_sensitive=True)
                assert "Found 1 symbol" in result_sensitive
                
                # Case insensitive search
                result_insensitive = find_symbol("MyFunction", case_sensitive=False)
                assert "Found 3 symbol" in result_insensitive
                
            finally:
                os.chdir(original_cwd)

    def test_find_symbol_with_file_pattern(self):
        """Test finding symbols with file pattern filtering."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                # Create files with different extensions
                py_file = project_root / "test.py"
                py_file.write_text("def target(): pass")
                
                js_file = project_root / "test.js"
                js_file.write_text("function target() {}")
                
                txt_file = project_root / "test.txt"
                txt_file.write_text("target mentioned here")
                
                # Search only Python files
                result = find_symbol("target", file_pattern="*.py")
                assert "Found" in result
                assert "test.py" in result
                assert "test.js" not in result
                
            finally:
                os.chdir(original_cwd)

    def test_find_symbol_no_results(self):
        """Test behavior when no symbols are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                test_file = project_root / "test.py"
                test_file.write_text("def other_function(): pass")
                
                result = find_symbol("nonexistent_symbol")
                assert "No symbols found" in result
                assert "nonexistent_symbol" in result
                
            finally:
                os.chdir(original_cwd)

    def test_find_symbol_many_results(self):
        """Test handling of many search results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                # Create many files with the target symbol
                for i in range(25):
                    file_path = project_root / f"file_{i}.py"
                    file_path.write_text(f"def target_symbol_{i}(): pass\ntarget_symbol = {i}")
                
                result = find_symbol("target_symbol")
                assert "showing first 20" in result
                assert "and 30 more results" in result or "more results" in result
                
            finally:
                os.chdir(original_cwd)


class TestFindReferencingSymbols:
    """Test finding symbols that reference a target symbol."""

    def test_find_referencing_symbols_basic(self):
        """Test basic reference finding functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                # Create target file with symbol definition
                target_file = project_root / "target.py"
                target_file.write_text("""
def target_function():
    return "target"
""")
                
                # Create file with references
                ref_file = project_root / "references.py"
                ref_file.write_text("""
from target import target_function

def caller():
    result = target_function()
    return result

class Usage:
    def method(self):
        return target_function()
""")
                
                result = find_referencing_symbols("target_function", "target.py")
                
                assert "Found" in result
                assert "references.py" in result
                assert "target_function()" in result
                
            finally:
                os.chdir(original_cwd)

    def test_find_referencing_symbols_with_line_number(self):
        """Test reference finding with specific line number."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                target_file = project_root / "target.py"
                target_file.write_text("""
def target_function():  # Line 2 (1-indexed)
    return "target"
""")
                
                ref_file = project_root / "references.py"
                ref_file.write_text("""
result = target_function()  # Should find this
""")
                
                result = find_referencing_symbols("target_function", "target.py", target_line=2)
                
                assert "Found" in result
                assert "references.py" in result
                # Should exclude the definition itself
                assert "target.py:2" not in result
                
            finally:
                os.chdir(original_cwd)

    def test_find_referencing_symbols_type_filter(self):
        """Test reference finding with symbol type filtering."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                target_file = project_root / "target.py"
                target_file.write_text("def target(): pass")
                
                ref_file = project_root / "references.py"
                ref_file.write_text("""
result = target()  # function_call
import_target = target  # assignment
# Comment about target  # reference
""")
                
                # Filter for only function calls
                result = find_referencing_symbols(
                    "target", 
                    "target.py", 
                    symbol_types=["function_call"]
                )
                
                assert "Found" in result
                lines = result.split('\n')
                function_call_lines = [line for line in lines if "function_call" in line]
                assert len(function_call_lines) >= 1
                
            finally:
                os.chdir(original_cwd)

    def test_find_referencing_symbols_no_references(self):
        """Test behavior when no references are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                target_file = project_root / "target.py"
                target_file.write_text("def isolated_function(): pass")
                
                other_file = project_root / "other.py"
                other_file.write_text("def unrelated_function(): pass")
                
                result = find_referencing_symbols("isolated_function", "target.py")
                
                assert "No references found" in result
                assert "isolated_function" in result
                
            finally:
                os.chdir(original_cwd)

    def test_find_referencing_symbols_file_not_found(self):
        """Test error handling when target file doesn't exist."""
        result = find_referencing_symbols("any_symbol", "nonexistent.py")
        assert "Target file not found" in result
        assert "nonexistent.py" in result


class TestFindReferencingCodeSnippets:
    """Test finding code snippets that reference symbols."""

    def test_find_referencing_code_snippets_with_context(self):
        """Test finding code snippets with context lines."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                target_file = project_root / "target.py"
                target_file.write_text("def target_function(): pass")
                
                ref_file = project_root / "usage.py"
                ref_file.write_text("""
# Setup code
def caller():
    # Before target call
    result = target_function()
    # After target call
    return result
""")
                
                result = find_referencing_code_snippets("target_function", "target.py", context_lines=2)
                
                assert "Code snippets referencing" in result
                assert "usage.py" in result
                assert "Before target call" in result
                assert "After target call" in result
                assert "result = target_function()" in result
                
            finally:
                os.chdir(original_cwd)

    def test_find_referencing_code_snippets_usage_types(self):
        """Test detection of different usage types in snippets."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                target_file = project_root / "target.py"
                target_file.write_text("class TargetClass: pass")
                
                usage_file = project_root / "usage.py"
                usage_file.write_text("""
# Constructor usage
obj = new TargetClass()

# Inheritance usage  
class Child extends TargetClass:
    pass

# Import usage
from target import TargetClass

# Property access
result = TargetClass.static_method()
""")
                
                result = find_referencing_code_snippets("TargetClass", "target.py")
                
                assert "Constructor Call" in result
                assert "Inheritance" in result
                assert "Import" in result
                assert "Property Access" in result
                
            finally:
                os.chdir(original_cwd)

    def test_find_referencing_code_snippets_excludes_definitions(self):
        """Test that code snippets exclude definition files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                target_file = project_root / "target.py"
                target_file.write_text("""
def target_function():
    return "defined here"
    
# This should not appear in snippets
result = target_function()
""")
                
                usage_file = project_root / "usage.py"
                usage_file.write_text("""
# This should appear in snippets
result = target_function()
""")
                
                result = find_referencing_code_snippets("target_function", "target.py")
                
                # Should include usage from other files
                assert "usage.py" in result
                # Should not include the definition or same-file usage
                lines = result.split('\n')
                target_file_lines = [line for line in lines if "target.py" in line]
                assert len(target_file_lines) == 0 or all("def " not in line for line in target_file_lines)
                
            finally:
                os.chdir(original_cwd)

    def test_find_referencing_code_snippets_no_snippets(self):
        """Test behavior when no code snippets are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                target_file = project_root / "target.py"
                target_file.write_text("def unused_function(): pass")
                
                result = find_referencing_code_snippets("unused_function", "target.py")
                assert "No code snippets found" in result
                assert "unused_function" in result
                
            finally:
                os.chdir(original_cwd)


class TestGetSymbolsOverview:
    """Test getting overview of symbols in files and directories."""

    def test_get_symbols_overview_single_file(self):
        """Test getting symbol overview for a single file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                test_file = project_root / "test.py"
                test_file.write_text("""
class PublicClass:
    def __init__(self):
        pass
    
    def public_method(self):
        return "public"
    
    def _private_method(self):
        return "private"

def public_function():
    return "function"

def _private_function():
    return "private function"

PUBLIC_VAR = "public"
_private_var = "private"
""")
                
                result = get_symbols_overview("test.py")
                
                assert "Symbol Overview" in result
                assert "test.py" in result
                assert "FUNCTIONS" in result
                assert "CLASSES" in result
                assert "PublicClass" in result
                assert "public_function" in result
                assert "_private_function" in result
                assert "=" in result  # Public symbol icon
                assert "=" in result  # Private symbol icon
                
            finally:
                os.chdir(original_cwd)

    def test_get_symbols_overview_directory(self):
        """Test getting symbol overview for a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                src_dir = project_root / "src"
                src_dir.mkdir()
                
                (src_dir / "module1.py").write_text("""
class Module1Class:
    pass

def module1_function():
    pass
""")
                
                (src_dir / "module2.py").write_text("""
def module2_function():
    pass

MODULE2_CONST = "constant"
""")
                
                result = get_symbols_overview("src")
                
                assert "Symbol Overview" in result
                assert "src/module1.py" in result
                assert "src/module2.py" in result
                assert "Module1Class" in result
                assert "module1_function" in result
                assert "module2_function" in result
                
            finally:
                os.chdir(original_cwd)

    def test_get_symbols_overview_with_type_filter(self):
        """Test symbol overview with type filtering."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                test_file = project_root / "test.py"
                test_file.write_text("""
class TestClass:
    pass

def test_function():
    pass

test_variable = "value"
""")
                
                # Filter for only classes
                result = get_symbols_overview("test.py", symbol_types=["class"])
                
                assert "TestClass" in result
                assert "test_function" not in result
                assert "CLASSES" in result
                assert "FUNCTIONS" not in result
                
            finally:
                os.chdir(original_cwd)

    def test_get_symbols_overview_exclude_private(self):
        """Test symbol overview excluding private symbols."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                test_file = project_root / "test.py"
                test_file.write_text("""
class PublicClass:
    pass

class _PrivateClass:
    pass

def public_function():
    pass

def _private_function():
    pass
""")
                
                result = get_symbols_overview("test.py", include_private=False)
                
                assert "PublicClass" in result
                assert "_PrivateClass" not in result
                assert "public_function" in result
                assert "_private_function" not in result
                
            finally:
                os.chdir(original_cwd)

    def test_get_symbols_overview_no_symbols(self):
        """Test behavior when no symbols are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                test_file = project_root / "empty.py"
                test_file.write_text("# Just a comment\npass")
                
                result = get_symbols_overview("empty.py")
                
                assert "No symbols found" in result
                assert "empty.py" in result
                
            finally:
                os.chdir(original_cwd)

    def test_get_symbols_overview_path_not_found(self):
        """Test error handling when path doesn't exist."""
        result = get_symbols_overview("nonexistent_path")
        assert "Path not found" in result
        assert "nonexistent_path" in result


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_find_symbol_error_handling(self):
        """Test error handling in find_symbol function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Test with invalid file permissions or corrupted files
                # Since we can't easily create truly unreadable files in tests,
                # we test the error path by ensuring graceful handling
                result = find_symbol("test_symbol")
                
                # Should not crash, even with no files
                assert "No symbols found" in result or "Found" in result
                
            finally:
                os.chdir(original_cwd)

    def test_extract_symbols_handles_encoding_errors(self):
        """Test that symbol extraction handles encoding issues gracefully."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.py', delete=False) as temp_file:
            # Write some invalid UTF-8 bytes
            temp_file.write(b"def function(): pass\n\xff\xfe\nother content")
            temp_file.flush()
            
            try:
                file_path = Path(temp_file.name)
                # Should not crash on encoding errors
                symbols = _extract_symbols_from_file(file_path, None, True)
                # May or may not find symbols, but shouldn't crash
                assert isinstance(symbols, list)
                
            finally:
                os.unlink(temp_file.name)

    def test_functions_with_empty_search_terms(self):
        """Test behavior with empty or invalid search terms."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                test_file = Path(temp_dir) / "test.py"
                test_file.write_text("def test(): pass")
                
                # Empty search term
                result = find_symbol("")
                assert "No symbols found" in result or "Found" in result
                
                # Whitespace only
                result = find_symbol("   ")
                assert "No symbols found" in result or "Found" in result
                
            finally:
                os.chdir(original_cwd)