"""Tests for lib.memory module initialization."""

import pytest


class TestMemoryModuleInit:
    """Test memory module initialization."""

    def test_memory_module_can_be_imported(self):
        """Test that the memory module can be imported."""
        import lib.memory
        assert lib.memory is not None

    def test_memory_module_has_create_memory_instance(self):
        """Test that create_memory_instance is available from the module."""
        from lib.memory import create_memory_instance
        assert create_memory_instance is not None
        assert callable(create_memory_instance)

    def test_memory_module_has_create_agent_memory(self):
        """Test that create_agent_memory is available from the module."""
        from lib.memory import create_agent_memory
        assert create_agent_memory is not None
        assert callable(create_agent_memory)

    def test_memory_module_has_create_team_memory(self):
        """Test that create_team_memory is available from the module."""
        from lib.memory import create_team_memory
        assert create_team_memory is not None
        assert callable(create_team_memory)

    def test_memory_module_all_exports(self):
        """Test that __all__ contains expected exports."""
        import lib.memory
        assert hasattr(lib.memory, "__all__")
        expected_exports = ["create_memory_instance", "create_agent_memory", "create_team_memory"]
        for export in expected_exports:
            assert export in lib.memory.__all__