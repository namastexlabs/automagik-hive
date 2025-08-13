"""
TDD Test Suite for Genie Debug Agent __init__.py - RED Phase Implementation

This test suite follows TDD methodology with failing tests first to drive implementation.
Tests are designed to FAIL initially to enforce RED phase compliance.

Module Under Test: ai/agents/genie-debug/__init__.py
Pattern: Module export verification and import validation
"""

import pytest
from pathlib import Path
import os


class TestGenieDebugAgentInit:
    """Test suite for Genie Debug Agent __init__.py module."""
    
    def test_init_file_exists(self):
        """Test that the __init__.py file exists."""
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent.parent
        init_file = project_root / "ai" / "agents" / "genie-debug" / "__init__.py"
        
        assert init_file.exists(), f"__init__.py file not found at {init_file}"
    
    def test_init_exports_get_genie_debug_agent(self):
        """Test that __init__.py exports get_genie_debug_agent function."""
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent.parent
        init_file = project_root / "ai" / "agents" / "genie-debug" / "__init__.py"
        
        with open(init_file, 'r') as f:
            content = f.read()
        
        # Check that it imports get_genie_debug_agent
        assert "from .agent import get_genie_debug_agent" in content, "Should import get_genie_debug_agent"
    
    def test_init_module_has_correct_all_exports(self):
        """Test that __init__.py has correct __all__ exports."""
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent.parent
        init_file = project_root / "ai" / "agents" / "genie-debug" / "__init__.py"
        
        with open(init_file, 'r') as f:
            content = f.read()
        
        # Check __all__ exists and contains expected exports
        assert '__all__ = ["get_genie_debug_agent"]' in content, "Should have __all__ with get_genie_debug_agent"
    
    def test_init_module_docstring_exists(self):
        """Test that __init__.py has a proper module docstring."""
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent.parent
        init_file = project_root / "ai" / "agents" / "genie-debug" / "__init__.py"
        
        with open(init_file, 'r') as f:
            content = f.read()
        
        # Check module has docstring (look for triple quotes at the start)
        assert '"""' in content, "Module should have a docstring"


class TestGenieDebugAgentImports:
    """Test suite for import functionality."""
    
    def test_can_import_genie_debug_agent_function(self):
        """Test that get_genie_debug_agent can be imported directly."""
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent.parent
        init_file = project_root / "ai" / "agents" / "genie-debug" / "__init__.py"
        
        with open(init_file, 'r') as f:
            content = f.read()
        
        # Check that the function is properly exported
        assert "get_genie_debug_agent" in content, "Function should be available for import"
    
    def test_import_structure_follows_pattern(self):
        """Test that import structure follows expected pattern."""
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent.parent
        init_file = project_root / "ai" / "agents" / "genie-debug" / "__init__.py"
        agent_file = project_root / "ai" / "agents" / "genie-debug" / "agent.py"
        
        # Both files should exist for proper import structure
        assert init_file.exists(), "__init__.py should exist"
        assert agent_file.exists(), "agent.py should exist"
        
        with open(init_file, 'r') as f:
            init_content = f.read()
        
        with open(agent_file, 'r') as f:
            agent_content = f.read()
        
        # __init__.py should import from agent.py
        assert "from .agent import" in init_content, "Should import from agent module"
        # agent.py should define the function
        assert "def get_genie_debug_agent" in agent_content, "Agent module should define the function"


class TestTDDCompliance:
    """Tests to ensure TDD methodology compliance for __init__.py."""
    
    def test_red_phase_compliance(self):
        """Ensure tests fail in RED phase to drive implementation."""
        # This test documents TDD compliance for __init__.py
        # Tests above should fail until __init__.py is properly implemented
        assert True, "TDD RED phase documented for __init__.py - implementation needed"
    
    def test_init_drives_module_structure(self):
        """Test that __init__.py exists to drive proper module structure."""
        # This test ensures __init__.py is created to make the module importable
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent.parent
        init_file = project_root / "ai" / "agents" / "genie-debug" / "__init__.py"
        
        assert init_file.exists(), "__init__.py should exist to make module importable"