"""
Comprehensive test suite for lib/tools/shared/shell_toolkit.py
Testing shell toolkit wrapper functionality and integration with Agno ShellTools.
Target: 50%+ coverage with failing tests that guide TDD implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from lib.tools.shared.shell_toolkit import ShellToolkit


class TestShellToolkitInit:
    """Test ShellToolkit initialization."""
    
    def test_shell_toolkit_initialization(self):
        """Test ShellToolkit initializes with Agno ShellTools."""
        with patch('lib.tools.shared.shell_toolkit.ShellTools') as mock_shell_tools:
            mock_instance = Mock()
            mock_shell_tools.return_value = mock_instance
            
            toolkit = ShellToolkit()
            
            # Should create ShellTools instance
            mock_shell_tools.assert_called_once()
            assert hasattr(toolkit, '_shell_tools')
            assert toolkit._shell_tools is mock_instance

    def test_shell_toolkit_has_required_attributes(self):
        """Test ShellToolkit has all required attributes after init."""
        with patch('lib.tools.shared.shell_toolkit.ShellTools') as mock_shell_tools:
            mock_instance = Mock()
            mock_shell_tools.return_value = mock_instance
            
            toolkit = ShellToolkit()
            
            assert hasattr(toolkit, '_shell_tools')
            assert toolkit._shell_tools is not None

    def test_shell_toolkit_init_calls_shell_tools_constructor(self):
        """Test ShellToolkit initialization calls ShellTools constructor properly."""
        with patch('lib.tools.shared.shell_toolkit.ShellTools') as mock_shell_tools:
            mock_instance = Mock()
            mock_shell_tools.return_value = mock_instance
            
            toolkit = ShellToolkit()
            
            # Should call ShellTools constructor with no arguments
            mock_shell_tools.assert_called_once_with()
            assert toolkit._shell_tools is mock_instance


class TestGetTools:
    """Test get_tools method functionality."""
    
    def test_get_tools_returns_shell_tools_instance(self):
        """Test get_tools returns the underlying ShellTools instance."""
        with patch('lib.tools.shared.shell_toolkit.ShellTools') as mock_shell_tools:
            mock_instance = Mock()
            mock_shell_tools.return_value = mock_instance
            
            toolkit = ShellToolkit()
            tools = toolkit.get_tools()
            
            assert tools is mock_instance
            assert tools is toolkit._shell_tools

    def test_get_tools_returns_same_instance_multiple_calls(self):
        """Test get_tools returns the same instance on multiple calls."""
        with patch('lib.tools.shared.shell_toolkit.ShellTools') as mock_shell_tools:
            mock_instance = Mock()
            mock_shell_tools.return_value = mock_instance
            
            toolkit = ShellToolkit()
            
            tools1 = toolkit.get_tools()
            tools2 = toolkit.get_tools()
            
            assert tools1 is tools2
            assert tools1 is mock_instance

    def test_get_tools_preserves_shell_tools_interface(self):
        """Test get_tools preserves the ShellTools interface."""
        with patch('lib.tools.shared.shell_toolkit.ShellTools') as mock_shell_tools:
            mock_instance = Mock()
            mock_instance.execute.return_value = "command_result"
            mock_instance.run.return_value = {"status": "success"}
            mock_shell_tools.return_value = mock_instance
            
            toolkit = ShellToolkit()
            tools = toolkit.get_tools()
            
            # Should preserve ShellTools methods
            assert hasattr(tools, 'execute')
            assert hasattr(tools, 'run')
            
            # Should be able to call methods
            result = tools.execute("test command")
            assert result == "command_result"
            
            run_result = tools.run("test")
            assert run_result == {"status": "success"}

    def test_get_tools_with_mocked_shell_tools_methods(self):
        """Test get_tools with various mocked ShellTools methods."""
        with patch('lib.tools.shared.shell_toolkit.ShellTools') as mock_shell_tools:
            mock_instance = Mock()
            
            # Mock typical ShellTools methods
            mock_instance.run_command.return_value = "output"
            mock_instance.execute_script.return_value = {"code": 0}
            mock_instance.get_environment.return_value = {"PATH": "/usr/bin"}
            
            mock_shell_tools.return_value = mock_instance
            
            toolkit = ShellToolkit()
            tools = toolkit.get_tools()
            
            # Test that all mocked methods are accessible
            assert tools.run_command("ls") == "output"
            assert tools.execute_script("script.sh") == {"code": 0}
            assert tools.get_environment() == {"PATH": "/usr/bin"}


class TestShellToolkitWrapperBehavior:
    """Test ShellToolkit wrapper behavior and integration."""
    
    def test_toolkit_is_wrapper_not_inheritance(self):
        """Test ShellToolkit is a wrapper, not inheriting from ShellTools."""
        with patch('lib.tools.shared.shell_toolkit.ShellTools') as mock_shell_tools:
            mock_instance = Mock()
            mock_shell_tools.return_value = mock_instance
            
            toolkit = ShellToolkit()
            
            # Should not inherit from ShellTools
            assert not hasattr(toolkit, 'execute')
            assert not hasattr(toolkit, 'run')
            
            # But should provide access via get_tools()
            tools = toolkit.get_tools()
            assert tools is mock_instance

    def test_toolkit_delegates_to_shell_tools(self):
        """Test that ShellToolkit properly delegates to underlying ShellTools."""
        with patch('lib.tools.shared.shell_toolkit.ShellTools') as mock_shell_tools:
            mock_instance = Mock()
            mock_instance.some_method.return_value = "delegated_result"
            mock_shell_tools.return_value = mock_instance
            
            toolkit = ShellToolkit()
            tools = toolkit.get_tools()
            
            result = tools.some_method("arg1", key="value")
            
            # Should delegate to underlying instance
            mock_instance.some_method.assert_called_once_with("arg1", key="value")
            assert result == "delegated_result"

    def test_multiple_toolkit_instances_independent(self):
        """Test multiple ShellToolkit instances are independent."""
        with patch('lib.tools.shared.shell_toolkit.ShellTools') as mock_shell_tools:
            mock_instance1 = Mock()
            mock_instance2 = Mock()
            
            # Return different instances for each call
            mock_shell_tools.side_effect = [mock_instance1, mock_instance2]
            
            toolkit1 = ShellToolkit()
            toolkit2 = ShellToolkit()
            
            tools1 = toolkit1.get_tools()
            tools2 = toolkit2.get_tools()
            
            # Should be different instances
            assert tools1 is not tools2
            assert tools1 is mock_instance1
            assert tools2 is mock_instance2
            
            # Should have been called twice
            assert mock_shell_tools.call_count == 2

    def test_toolkit_preserves_shell_tools_state(self):
        """Test toolkit preserves ShellTools instance state."""
        with patch('lib.tools.shared.shell_toolkit.ShellTools') as mock_shell_tools:
            mock_instance = Mock()
            mock_instance.state = "initial"
            mock_shell_tools.return_value = mock_instance
            
            toolkit = ShellToolkit()
            tools = toolkit.get_tools()
            
            # Modify state
            tools.state = "modified"
            
            # Should preserve state on subsequent calls
            tools_again = toolkit.get_tools()
            assert tools_again.state == "modified"
            assert tools_again is tools


class TestShellToolkitImportPatterns:
    """Test import patterns and module dependencies."""
    
    def test_shell_tools_import_location(self):
        """Test that ShellTools is imported from correct location."""
        # This test verifies the import statement
        from agno.tools.shell import ShellTools
        
        # Should be able to import from expected location
        assert ShellTools is not None
        
        # Test that our toolkit uses the same import
        with patch('lib.tools.shared.shell_toolkit.ShellTools', ShellTools):
            toolkit = ShellToolkit()
            assert toolkit._shell_tools is not None

    def test_toolkit_import_independence(self):
        """Test toolkit can be imported independently."""
        # Should be able to import ShellToolkit without errors
        from lib.tools.shared.shell_toolkit import ShellToolkit as ImportedToolkit
        
        assert ImportedToolkit is ShellToolkit
        
        # Should be able to instantiate
        with patch('lib.tools.shared.shell_toolkit.ShellTools'):
            toolkit = ImportedToolkit()
            assert isinstance(toolkit, ImportedToolkit)

    def test_agno_dependency_handling(self):
        """Test handling of Agno dependency issues."""
        # Test behavior when ShellTools import fails
        with patch('lib.tools.shared.shell_toolkit.ShellTools', side_effect=ImportError("Agno not available")):
            with pytest.raises(ImportError, match="Agno not available"):
                ShellToolkit()

    def test_shell_tools_instantiation_failure(self):
        """Test handling when ShellTools instantiation fails."""
        with patch('lib.tools.shared.shell_toolkit.ShellTools', side_effect=RuntimeError("ShellTools init failed")):
            with pytest.raises(RuntimeError, match="ShellTools init failed"):
                ShellToolkit()


class TestModuleExports:
    """Test module exports and __all__ declaration."""
    
    def test_module_exports_shell_toolkit(self):
        """Test that module exports ShellToolkit in __all__."""
        import lib.tools.shared.shell_toolkit as shell_module
        
        assert hasattr(shell_module, '__all__')
        assert "ShellToolkit" in shell_module.__all__
        assert len(shell_module.__all__) == 1

    def test_shell_toolkit_available_in_module(self):
        """Test ShellToolkit is available as module attribute."""
        import lib.tools.shared.shell_toolkit as shell_module
        
        assert hasattr(shell_module, 'ShellToolkit')
        assert shell_module.ShellToolkit is ShellToolkit

    def test_module_auto_discovery_compatibility(self):
        """Test module is compatible with auto-discovery systems."""
        # Auto-discovery systems typically look for __all__ and class exports
        import lib.tools.shared.shell_toolkit as shell_module
        
        # Should have __all__ for explicit exports
        assert hasattr(shell_module, '__all__')
        
        # Should have the class available
        toolkit_class = getattr(shell_module, 'ShellToolkit', None)
        assert toolkit_class is not None
        assert callable(toolkit_class)

    def test_no_unintended_exports(self):
        """Test module doesn't export unintended symbols."""
        import lib.tools.shared.shell_toolkit as shell_module
        
        exported_symbols = shell_module.__all__
        
        # Should only export ShellToolkit
        assert len(exported_symbols) == 1
        assert exported_symbols == ["ShellToolkit"]
        
        # Should not export internal dependencies
        assert "ShellTools" not in exported_symbols


class TestShellToolkitIntegration:
    """Test ShellToolkit integration scenarios."""
    
    def test_toolkit_with_real_shell_tools_interface(self):
        """Test toolkit works with realistic ShellTools interface."""
        # Mock a realistic ShellTools interface
        mock_shell_tools_class = Mock()
        mock_instance = Mock()
        
        # Add typical shell tool methods
        mock_instance.run_command = Mock(return_value={"stdout": "output", "stderr": "", "code": 0})
        mock_instance.execute = Mock(return_value="command executed")
        mock_instance.run_script = Mock(return_value={"success": True})
        mock_instance.get_working_directory = Mock(return_value="/current/dir")
        mock_instance.change_directory = Mock(return_value=True)
        
        mock_shell_tools_class.return_value = mock_instance
        
        with patch('lib.tools.shared.shell_toolkit.ShellTools', mock_shell_tools_class):
            toolkit = ShellToolkit()
            tools = toolkit.get_tools()
            
            # Test various shell operations
            result1 = tools.run_command("ls -la")
            assert result1 == {"stdout": "output", "stderr": "", "code": 0}
            
            result2 = tools.execute("pwd")
            assert result2 == "command executed"
            
            result3 = tools.run_script("test.sh")
            assert result3 == {"success": True}
            
            current_dir = tools.get_working_directory()
            assert current_dir == "/current/dir"
            
            change_result = tools.change_directory("/new/dir")
            assert change_result is True

    def test_toolkit_error_propagation(self):
        """Test that errors from ShellTools are properly propagated."""
        mock_shell_tools_class = Mock()
        mock_instance = Mock()
        
        # Mock method that raises an exception
        mock_instance.run_command.side_effect = RuntimeError("Command execution failed")
        mock_shell_tools_class.return_value = mock_instance
        
        with patch('lib.tools.shared.shell_toolkit.ShellTools', mock_shell_tools_class):
            toolkit = ShellToolkit()
            tools = toolkit.get_tools()
            
            # Error should propagate through the wrapper
            with pytest.raises(RuntimeError, match="Command execution failed"):
                tools.run_command("failing_command")

    def test_toolkit_method_signature_preservation(self):
        """Test that method signatures are preserved through the wrapper."""
        mock_shell_tools_class = Mock()
        mock_instance = Mock()
        
        # Create a method with specific signature
        def mock_execute(command, timeout=30, cwd=None, env=None):
            return f"Executed: {command} (timeout={timeout}, cwd={cwd})"
        
        mock_instance.execute = mock_execute
        mock_shell_tools_class.return_value = mock_instance
        
        with patch('lib.tools.shared.shell_toolkit.ShellTools', mock_shell_tools_class):
            toolkit = ShellToolkit()
            tools = toolkit.get_tools()
            
            # Should be able to call with various argument patterns
            result1 = tools.execute("test")
            assert "Executed: test" in result1
            
            result2 = tools.execute("test", timeout=60)
            assert "timeout=60" in result2
            
            result3 = tools.execute("test", cwd="/tmp")
            assert "cwd=/tmp" in result3
            
            result4 = tools.execute("test", timeout=45, cwd="/home", env={"VAR": "value"})
            assert all(s in result4 for s in ["timeout=45", "cwd=/home"])

    def test_toolkit_with_async_shell_tools(self):
        """Test toolkit behavior with async ShellTools methods."""
        mock_shell_tools_class = Mock()
        mock_instance = Mock()
        
        # Mock async method
        async_mock = AsyncMock(return_value="async result")
        mock_instance.async_execute = async_mock
        mock_shell_tools_class.return_value = mock_instance
        
        with patch('lib.tools.shared.shell_toolkit.ShellTools', mock_shell_tools_class):
            toolkit = ShellToolkit()
            tools = toolkit.get_tools()
            
            # Should preserve async methods
            assert hasattr(tools, 'async_execute')
            assert tools.async_execute is async_mock


class TestShellToolkitErrorHandling:
    """Test error handling scenarios."""
    
    def test_shell_tools_none_handling(self):
        """Test handling when ShellTools returns None."""
        with patch('lib.tools.shared.shell_toolkit.ShellTools', return_value=None):
            toolkit = ShellToolkit()
            
            assert toolkit._shell_tools is None
            
            tools = toolkit.get_tools()
            assert tools is None

    def test_shell_tools_initialization_exception(self):
        """Test handling of ShellTools initialization exceptions."""
        with patch('lib.tools.shared.shell_toolkit.ShellTools', side_effect=ValueError("Invalid configuration")):
            with pytest.raises(ValueError, match="Invalid configuration"):
                ShellToolkit()

    def test_get_tools_after_initialization_failure(self):
        """Test get_tools behavior after failed initialization."""
        # This is a complex scenario that depends on implementation details
        # In practice, if __init__ fails, the object won't be created
        # But we can test partial initialization scenarios
        
        toolkit = object.__new__(ShellToolkit)  # Create without calling __init__
        
        # Should handle missing _shell_tools attribute
        with pytest.raises(AttributeError):
            toolkit.get_tools()

    def test_concurrent_access_to_get_tools(self):
        """Test concurrent access to get_tools method."""
        with patch('lib.tools.shared.shell_toolkit.ShellTools') as mock_shell_tools:
            mock_instance = Mock()
            mock_shell_tools.return_value = mock_instance
            
            toolkit = ShellToolkit()
            
            # Simulate concurrent access
            tools_list = []
            for _ in range(10):
                tools = toolkit.get_tools()
                tools_list.append(tools)
            
            # All should be the same instance
            assert all(tools is mock_instance for tools in tools_list)
            assert len(set(id(tools) for tools in tools_list)) == 1


@pytest.mark.integration
class TestShellToolkitSystemIntegration:
    """Integration tests for ShellToolkit with system components."""
    
    def test_toolkit_registry_integration(self):
        """Test ShellToolkit integration with tool registry systems."""
        # Test that toolkit can be discovered and used by registry systems
        with patch('lib.tools.shared.shell_toolkit.ShellTools') as mock_shell_tools:
            mock_instance = Mock()
            mock_shell_tools.return_value = mock_instance
            
            # Simulate registry discovery
            toolkit_class = ShellToolkit
            
            # Should be instantiable
            toolkit = toolkit_class()
            assert isinstance(toolkit, ShellToolkit)
            
            # Should provide tools interface
            tools = toolkit.get_tools()
            assert tools is mock_instance

    def test_toolkit_with_agno_ecosystem(self):
        """Test toolkit integration with broader Agno ecosystem."""
        # This test simulates integration with Agno's tool ecosystem
        
        # Mock Agno ShellTools with realistic interface
        mock_shell_tools_class = Mock()
        mock_instance = Mock()
        
        # Simulate Agno ShellTools interface
        mock_instance.tools = ["ls", "cd", "pwd", "grep"]
        mock_instance.execute_command = Mock(return_value={"status": "success"})
        mock_instance.get_available_tools = Mock(return_value=["shell_command", "file_ops"])
        
        mock_shell_tools_class.return_value = mock_instance
        
        with patch('lib.tools.shared.shell_toolkit.ShellTools', mock_shell_tools_class):
            toolkit = ShellToolkit()
            tools = toolkit.get_tools()
            
            # Should integrate with Agno ecosystem
            assert tools.tools == ["ls", "cd", "pwd", "grep"]
            
            result = tools.execute_command("test")
            assert result == {"status": "success"}
            
            available = tools.get_available_tools()
            assert available == ["shell_command", "file_ops"]

    def test_toolkit_lifecycle_management(self):
        """Test toolkit lifecycle in application context."""
        with patch('lib.tools.shared.shell_toolkit.ShellTools') as mock_shell_tools:
            mock_instance = Mock()
            mock_instance.cleanup = Mock()
            mock_instance.close = Mock()
            mock_shell_tools.return_value = mock_instance
            
            # Creation phase
            toolkit = ShellToolkit()
            assert toolkit._shell_tools is mock_instance
            
            # Usage phase
            tools = toolkit.get_tools()
            tools.some_operation = Mock(return_value="done")
            result = tools.some_operation()
            assert result == "done"
            
            # Cleanup phase (if supported by underlying ShellTools)
            if hasattr(tools, 'cleanup'):
                tools.cleanup()
                mock_instance.cleanup.assert_called_once()
            
            if hasattr(tools, 'close'):
                tools.close()
                mock_instance.close.assert_called_once()

    def test_toolkit_memory_management(self):
        """Test toolkit memory management and resource cleanup."""
        import gc
        import weakref
        
        with patch('lib.tools.shared.shell_toolkit.ShellTools') as mock_shell_tools:
            mock_instance = Mock()
            mock_shell_tools.return_value = mock_instance
            
            # Create toolkit and get weak reference
            toolkit = ShellToolkit()
            toolkit_ref = weakref.ref(toolkit)
            tools_ref = weakref.ref(toolkit.get_tools())
            
            # Verify references exist
            assert toolkit_ref() is not None
            assert tools_ref() is not None
            
            # Clean up
            del toolkit
            gc.collect()
            
            # Toolkit should be garbage collected
            assert toolkit_ref() is None
            # Tools reference behavior depends on ShellTools implementation
            # but should not prevent cleanup