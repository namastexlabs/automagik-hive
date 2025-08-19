"""Comprehensive test coverage for cli.commands.agent module.

This test suite bypasses CLI package initialization issues and directly tests
the AgentCommands class to achieve >50% test coverage.

Focuses on testing lines 16-110 that were previously missing coverage:
- Class initialization and core methods
- Command execution workflows (install, serve, stop, restart, status, logs)
- Error handling for subprocess failures and Docker issues
- Status checking and health validation
- CLI argument processing and validation
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, call

import pytest

# Add project root to path for direct imports
# Current path: /tests/cli/commands/test_agent_direct.py
# Need to go up 4 levels to get to project root
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

print(f"Current file: {__file__}")
print(f"Project root: {project_root.absolute()}")
print(f"Working directory: {Path.cwd()}")

# Import modules directly to bypass CLI package initialization
import importlib.util

# Get the correct paths
agent_path = project_root / "cli" / "commands" / "agent.py"
service_path = project_root / "cli" / "core" / "agent_service.py"

print(f"Agent path: {agent_path}")
print(f"Service path: {service_path}")
print(f"Agent exists: {agent_path.exists()}")
print(f"Service exists: {service_path.exists()}")

# Import AgentCommands directly
agent_spec = importlib.util.spec_from_file_location(
    "agent_commands", 
    str(agent_path)
)
agent_module = importlib.util.module_from_spec(agent_spec)

# Import AgentService directly  
service_spec = importlib.util.spec_from_file_location(
    "agent_service",
    str(service_path)
)
service_module = importlib.util.module_from_spec(service_spec)

# Execute modules
agent_spec.loader.exec_module(agent_module)
service_spec.loader.exec_module(service_module)

# Get classes
AgentCommands = agent_module.AgentCommands
AgentService = service_module.AgentService


class TestAgentCommandsInitialization:
    """Test AgentCommands class initialization - targeting lines 15-17."""

    def test_init_with_none_workspace(self):
        """Test initialization with None workspace path."""
        agent_cmd = AgentCommands(workspace_path=None)
        
        assert agent_cmd.workspace_path == Path()
        assert hasattr(agent_cmd, 'agent_service')
        assert agent_cmd.agent_service.__class__.__name__ == 'AgentService'

    def test_init_with_custom_workspace(self):
        """Test initialization with custom workspace path."""
        custom_path = Path("/test/workspace")
        agent_cmd = AgentCommands(workspace_path=custom_path)
        
        assert agent_cmd.workspace_path == custom_path
        assert hasattr(agent_cmd, 'agent_service')
        assert agent_cmd.agent_service.__class__.__name__ == 'AgentService'

    def test_init_default_workspace(self):
        """Test initialization with default parameters."""
        agent_cmd = AgentCommands()
        
        assert agent_cmd.workspace_path == Path()
        # Check that agent_service is the correct type by checking its class name
        # rather than using isinstance with dynamically imported class
        assert agent_cmd.agent_service.__class__.__name__ == "AgentService"


class TestAgentCommandsInstall:
    """Test install method - targeting lines 19-29."""

    @patch('builtins.print')
    def test_install_success(self, mock_print):
        """Test successful installation."""
        agent_cmd = AgentCommands()
        
        # Patch the actual instance methods after creation
        with patch.object(agent_cmd.agent_service, 'install_agent_environment', return_value=True) as mock_install, \
             patch.object(agent_cmd.agent_service, 'serve_agent', return_value=True) as mock_serve:
            
            result = agent_cmd.install("/test/workspace")
            
            assert result is True
            mock_print.assert_called_with("🚀 Installing and starting agent services in: /test/workspace")
            mock_install.assert_called_once_with("/test/workspace")
            mock_serve.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    def test_install_failure_install_step(self, mock_print):
        """Test installation failure during install step."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation
        with patch.object(agent_cmd.agent_service, 'install_agent_environment', return_value=False) as mock_install:
            result = agent_cmd.install("/test/workspace")
            
            assert result is False
            mock_print.assert_called_with("🚀 Installing and starting agent services in: /test/workspace")
            mock_install.assert_called_once_with("/test/workspace")

    def test_install_failure_serve_step(self):
        """Test installation failure during serve step."""
        agent_cmd = AgentCommands()
        
        with patch('builtins.print') as mock_print, \
             patch.object(agent_cmd.agent_service, 'install_agent_environment', return_value=True) as mock_install, \
             patch.object(agent_cmd.agent_service, 'serve_agent', return_value=False) as mock_serve:
            
            result = agent_cmd.install("/test/workspace")
        
            assert result is False
            mock_print.assert_called_with("🚀 Installing and starting agent services in: /test/workspace")
            mock_install.assert_called_once_with("/test/workspace")
            mock_serve.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    @patch.object(AgentService, 'install_agent_environment', side_effect=Exception("Install failed"))
    def test_install_exception_handling(self, mock_install, mock_print):
        """Test installation exception handling."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.install("/test/workspace")
        
        assert result is False
        mock_print.assert_called_with("🚀 Installing and starting agent services in: /test/workspace")

    def test_install_default_workspace(self):
        """Test installation with default workspace parameter."""
        agent_cmd = AgentCommands()
        
        with patch('builtins.print') as mock_print, \
             patch.object(agent_cmd.agent_service, 'install_agent_environment', return_value=True) as mock_install, \
             patch.object(agent_cmd.agent_service, 'serve_agent', return_value=True) as mock_serve:
            
            result = agent_cmd.install()
            
            assert result is True
            mock_print.assert_called_with("🚀 Installing and starting agent services in: .")
            mock_install.assert_called_once_with(".")
            mock_serve.assert_called_once_with(".")


class TestAgentCommandsStart:
    """Test start method - targeting lines 31-38."""

    @patch('builtins.print')
    def test_start_success(self, mock_print):
        """Test successful start."""
        agent_cmd = AgentCommands()
        
        # Mock the agent_service.serve_agent method directly on the instance
        with patch.object(agent_cmd.agent_service, 'serve_agent', return_value=True) as mock_serve:
            result = agent_cmd.start("/test/workspace")
        
        assert result == True
        mock_print.assert_called_with("🚀 Starting agent services in: /test/workspace")
        mock_serve.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    def test_start_failure(self, mock_print):
        """Test start failure."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation
        with patch.object(agent_cmd.agent_service, 'serve_agent', return_value=False) as mock_serve:
            result = agent_cmd.start("/test/workspace")
            
            assert result is False
            mock_print.assert_called_with("🚀 Starting agent services in: /test/workspace")
            mock_serve.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    def test_start_exception_handling(self, mock_print):
        """Test start exception handling."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation to raise exception
        with patch.object(agent_cmd.agent_service, 'serve_agent', side_effect=Exception("Start failed")) as mock_serve:
            result = agent_cmd.start("/test/workspace")
            
            assert result is False
            mock_print.assert_called_with("🚀 Starting agent services in: /test/workspace")
            mock_serve.assert_called_once_with("/test/workspace")

    def test_start_default_workspace(self):
        """Test start with default workspace parameter."""
        agent_cmd = AgentCommands()
        
        with patch('builtins.print') as mock_print, \
             patch.object(agent_cmd.agent_service, 'serve_agent', return_value=True) as mock_serve:
            
            result = agent_cmd.start()
            
            assert result is True
            mock_print.assert_called_with("🚀 Starting agent services in: .")
            mock_serve.assert_called_once_with(".")


class TestAgentCommandsStop:
    """Test stop method - targeting lines 41-47."""

    @patch('builtins.print')
    def test_stop_success(self, mock_print):
        """Test successful stop."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation
        with patch.object(agent_cmd.agent_service, 'stop_agent', return_value=True) as mock_stop:
            result = agent_cmd.stop("/test/workspace")
            
            assert result is True
            mock_print.assert_called_with("🛑 Stopping agent services in: /test/workspace")
            mock_stop.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    def test_stop_failure(self, mock_print):
        """Test stop failure."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation
        with patch.object(agent_cmd.agent_service, 'stop_agent', return_value=False) as mock_stop:
            result = agent_cmd.stop("/test/workspace")
            
            assert result is False
            mock_print.assert_called_with("🛑 Stopping agent services in: /test/workspace")
            mock_stop.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    @patch.object(AgentService, 'stop_agent', side_effect=Exception("Stop failed"))
    def test_stop_exception_handling(self, mock_stop, mock_print):
        """Test stop exception handling."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.stop("/test/workspace")
        
        assert result is False
        mock_print.assert_any_call("🛑 Stopping agent services in: /test/workspace")


class TestAgentCommandsRestart:
    """Test restart method - targeting lines 49-59."""

    @patch('builtins.print')
    def test_restart_success(self, mock_print):
        """Test successful restart."""
        agent_cmd = AgentCommands()
        
        with patch.object(agent_cmd, 'stop', return_value=True) as mock_stop, \
             patch.object(agent_cmd, 'start', return_value=True) as mock_start:
            
            result = agent_cmd.restart("/test/workspace")
            
            assert result is True
            mock_print.assert_called_with("🔄 Restarting agent services in: /test/workspace")
            mock_stop.assert_called_once_with("/test/workspace")
            mock_start.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    def test_restart_stop_failure_continues(self, mock_print):
        """Test restart continues even if stop fails."""
        agent_cmd = AgentCommands()
        
        with patch.object(agent_cmd, 'stop', return_value=False) as mock_stop, \
             patch.object(agent_cmd, 'start', return_value=True) as mock_start:
            
            result = agent_cmd.restart("/test/workspace")
            
            assert result is True
            expected_calls = [
                call("🔄 Restarting agent services in: /test/workspace"),
                call("⚠️ Stop failed, attempting restart anyway...")
            ]
            mock_print.assert_has_calls(expected_calls)
            mock_stop.assert_called_once_with("/test/workspace")
            mock_start.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    def test_restart_start_failure(self, mock_print):
        """Test restart failure when start fails."""
        agent_cmd = AgentCommands()
        
        with patch.object(agent_cmd, 'stop', return_value=True) as mock_stop, \
             patch.object(agent_cmd, 'start', return_value=False) as mock_start:
            
            result = agent_cmd.restart("/test/workspace")
            
            assert result is False
            mock_print.assert_called_with("🔄 Restarting agent services in: /test/workspace")
            mock_stop.assert_called_once_with("/test/workspace")
            mock_start.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    @patch.object(AgentCommands, 'stop', side_effect=Exception("Stop failed"))
    def test_restart_exception_handling(self, mock_stop, mock_print):
        """Test restart exception handling."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.restart("/test/workspace")
        
        assert result is False
        mock_print.assert_called_with("🔄 Restarting agent services in: /test/workspace")


class TestAgentCommandsStatus:
    """Test status method - targeting lines 61-73."""

    @patch('builtins.print')
    def test_status_success(self, mock_print):
        """Test successful status check."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation
        with patch.object(agent_cmd.agent_service, 'get_agent_status', return_value={"postgres": "✅ Running", "server": "✅ Running"}) as mock_status:
            result = agent_cmd.status("/test/workspace")
            
            assert result is True
            expected_calls = [
                call("🔍 Checking agent status in: /test/workspace"),
                call("  postgres: ✅ Running"),
                call("  server: ✅ Running")
            ]
            mock_print.assert_has_calls(expected_calls)
            mock_status.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    def test_status_empty_status(self, mock_print):
        """Test status check with empty status."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation
        with patch.object(agent_cmd.agent_service, 'get_agent_status', return_value={}) as mock_status:
            result = agent_cmd.status("/test/workspace")
            
            assert result is True
            mock_print.assert_called_with("🔍 Checking agent status in: /test/workspace")
            mock_status.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    def test_status_exception_handling(self, mock_print):
        """Test status exception handling."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation
        with patch.object(agent_cmd.agent_service, 'get_agent_status', side_effect=Exception("Status check failed")) as mock_status:
            result = agent_cmd.status("/test/workspace")
            
            assert result is False
            mock_print.assert_called_with("🔍 Checking agent status in: /test/workspace")
            mock_status.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    def test_status_multiple_services(self, mock_print):
        """Test status check with multiple services."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation
        with patch.object(agent_cmd.agent_service, 'get_agent_status', return_value={"service1": "status1", "service2": "status2", "service3": "status3"}) as mock_status:
            result = agent_cmd.status("/test/workspace")
            
            assert result is True
            expected_calls = [
                call("🔍 Checking agent status in: /test/workspace"),
                call("  service1: status1"),
                call("  service2: status2"),
                call("  service3: status3")
            ]
            mock_print.assert_has_calls(expected_calls)
            mock_status.assert_called_once_with("/test/workspace")


class TestAgentCommandsLogs:
    """Test logs method - targeting lines 75-81."""

    @patch('builtins.print')
    def test_logs_success(self, mock_print):
        """Test successful logs display."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation
        with patch.object(agent_cmd.agent_service, 'show_agent_logs', return_value=True) as mock_logs:
            result = agent_cmd.logs("/test/workspace", tail=100)
        
        assert result is True
        mock_print.assert_called_with("📋 Showing agent logs from: /test/workspace (last 100 lines)")
        mock_logs.assert_called_once_with("/test/workspace", 100)

    @patch('builtins.print')
    def test_logs_failure(self, mock_print):
        """Test logs display failure."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation
        with patch.object(agent_cmd.agent_service, 'show_agent_logs', return_value=False) as mock_logs:
            result = agent_cmd.logs("/test/workspace", tail=50)
            
            assert result is False
            mock_print.assert_called_with("📋 Showing agent logs from: /test/workspace (last 50 lines)")
            mock_logs.assert_called_once_with("/test/workspace", 50)

    @patch('builtins.print')
    def test_logs_exception_handling(self, mock_print):
        """Test logs exception handling."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation to raise exception
        with patch.object(agent_cmd.agent_service, 'show_agent_logs', side_effect=Exception("Logs failed")) as mock_logs:
            result = agent_cmd.logs("/test/workspace")
            
            assert result is False
            mock_print.assert_called_with("📋 Showing agent logs from: /test/workspace (last 50 lines)")
            mock_logs.assert_called_once_with("/test/workspace", 50)

    def test_logs_default_tail(self):
        """Test logs with default tail parameter."""
        agent_cmd = AgentCommands()
        
        with patch('builtins.print') as mock_print, \
             patch.object(agent_cmd.agent_service, 'show_agent_logs', return_value=True) as mock_logs:
            
            result = agent_cmd.logs("/test/workspace")
            
            assert result is True
            mock_print.assert_called_with("📋 Showing agent logs from: /test/workspace (last 50 lines)")
            mock_logs.assert_called_once_with("/test/workspace", 50)


class TestAgentCommandsHealth:
    """Test health method - targeting lines 83-90."""

    @patch('builtins.print')
    def test_health_success(self, mock_print):
        """Test successful health check."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation
        with patch.object(agent_cmd.agent_service, 'get_agent_status', return_value={"postgres": "✅ Running", "server": "✅ Running"}) as mock_status:
            result = agent_cmd.health("/test/workspace")
            
            expected_result = {
                "status": "healthy",
                "workspace": "/test/workspace",
                "services": {"postgres": "✅ Running", "server": "✅ Running"}
            }
            assert result == expected_result
            mock_print.assert_called_with("🔍 Checking agent health in: /test/workspace")
            mock_status.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    def test_health_empty_status(self, mock_print):
        """Test health check with empty status."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method instead of class method
        with patch.object(agent_cmd.agent_service, 'get_agent_status', return_value={}):
            result = agent_cmd.health("/test/workspace")
        
        expected_result = {
            "status": "healthy",
            "workspace": "/test/workspace",
            "services": {}
        }
        assert result == expected_result
        mock_print.assert_called_with("🔍 Checking agent health in: /test/workspace")

    @patch('builtins.print')
    def test_health_exception_handling(self, mock_print):
        """Test health exception handling."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation to raise exception
        with patch.object(agent_cmd.agent_service, 'get_agent_status', side_effect=Exception("Health check failed")) as mock_status:
            result = agent_cmd.health("/test/workspace")
            
            expected_result = {
                "status": "error",
                "workspace": "/test/workspace"
            }
            assert result == expected_result
            mock_print.assert_called_with("🔍 Checking agent health in: /test/workspace")
            mock_status.assert_called_once_with("/test/workspace")

    def test_health_default_workspace(self):
        """Test health with default workspace parameter."""
        agent_cmd = AgentCommands()
        
        with patch('builtins.print') as mock_print:
            # Mock the instance method after AgentCommands creation
            agent_cmd.agent_service.get_agent_status = Mock(return_value={"service": "status"})
            
            result = agent_cmd.health()
            
            expected_result = {
                "status": "healthy",
                "workspace": ".",
                "services": {"service": "status"}
            }
            assert result == expected_result
            mock_print.assert_called_with("🔍 Checking agent health in: .")


class TestAgentCommandsReset:
    """Test reset method - targeting lines 92-100."""

    @patch('builtins.print')
    def test_reset_success(self, mock_print):
        """Test successful reset."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation
        with patch.object(agent_cmd.agent_service, 'reset_agent_environment', return_value=True) as mock_reset:
            result = agent_cmd.reset("/test/workspace")
        
        assert result is True
        expected_calls = [
            call("🗑️ Resetting agent environment in: /test/workspace"),
            call("This will destroy all containers and data, then reinstall and start fresh...")
        ]
        mock_print.assert_has_calls(expected_calls)
        mock_reset.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    def test_reset_failure(self, mock_print):
        """Test reset failure."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation
        with patch.object(agent_cmd.agent_service, 'reset_agent_environment', return_value=False) as mock_reset:
            result = agent_cmd.reset("/test/workspace")
        
        assert result is False
        expected_calls = [
            call("🗑️ Resetting agent environment in: /test/workspace"),
            call("This will destroy all containers and data, then reinstall and start fresh...")
        ]
        mock_print.assert_has_calls(expected_calls)
        mock_reset.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    @patch.object(AgentService, 'reset_agent_environment', side_effect=Exception("Reset failed"))
    def test_reset_exception_handling(self, mock_reset, mock_print):
        """Test reset exception handling."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.reset("/test/workspace")
        
        assert result is False
        expected_calls = [
            call("🗑️ Resetting agent environment in: /test/workspace"),
            call("This will destroy all containers and data, then reinstall and start fresh...")
        ]
        mock_print.assert_has_calls(expected_calls)


class TestAgentCommandsUninstall:
    """Test uninstall method - targeting lines 102-110."""

    @patch('builtins.print')
    def test_uninstall_success(self, mock_print):
        """Test successful uninstall."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation
        with patch.object(agent_cmd.agent_service, 'uninstall_agent_environment', return_value=True) as mock_uninstall:
            result = agent_cmd.uninstall("/test/workspace")
        
        assert result is True
        expected_calls = [
            call("🗑️ Uninstalling agent environment in: /test/workspace"),
            call("This will destroy all containers and data permanently...")
        ]
        mock_print.assert_has_calls(expected_calls)
        mock_uninstall.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    def test_uninstall_failure(self, mock_print):
        """Test uninstall failure."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation
        with patch.object(agent_cmd.agent_service, 'uninstall_agent_environment', return_value=False) as mock_uninstall:
            result = agent_cmd.uninstall("/test/workspace")
        
        assert result is False
        expected_calls = [
            call("🗑️ Uninstalling agent environment in: /test/workspace"),
            call("This will destroy all containers and data permanently...")
        ]
        mock_print.assert_has_calls(expected_calls)
        mock_uninstall.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    def test_uninstall_exception_handling(self, mock_print):
        """Test uninstall exception handling."""
        agent_cmd = AgentCommands()
        
        # Mock the instance method after creation to raise exception
        with patch.object(agent_cmd.agent_service, 'uninstall_agent_environment', side_effect=Exception("Uninstall failed")) as mock_uninstall:
            result = agent_cmd.uninstall("/test/workspace")
        
        assert result is False
        expected_calls = [
            call("🗑️ Uninstalling agent environment in: /test/workspace"),
            call("This will destroy all containers and data permanently...")
        ]
        mock_print.assert_has_calls(expected_calls)
        mock_uninstall.assert_called_once_with("/test/workspace")


class TestAgentCommandsEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_workspace_parameter_types(self):
        """Test various workspace parameter types."""
        agent_cmd = AgentCommands()
        
        with patch.object(AgentService, 'get_agent_status', return_value={}) as mock_status:
            # Test with empty string
            result = agent_cmd.status("")
            assert result is True
            
            # Test with Path object converted to string
            result = agent_cmd.status(str(Path("/test/path")))
            assert result is True
            
            # Test with special characters
            result = agent_cmd.status("/test/path with spaces")
            assert result is True

    def test_all_methods_return_boolean_except_health(self):
        """Test all methods return boolean except health."""
        agent_cmd = AgentCommands()
        
        with patch.object(AgentService, 'install_agent_environment', return_value=True), \
             patch.object(AgentService, 'serve_agent', return_value=True), \
             patch.object(AgentService, 'stop_agent', return_value=True), \
             patch.object(AgentService, 'get_agent_status', return_value={}), \
             patch.object(AgentService, 'show_agent_logs', return_value=True), \
             patch.object(AgentService, 'reset_agent_environment', return_value=True), \
             patch.object(AgentService, 'uninstall_agent_environment', return_value=True), \
             patch('builtins.print'):
            
            # Test boolean return methods
            assert isinstance(agent_cmd.install(), bool)
            assert isinstance(agent_cmd.start(), bool)
            assert isinstance(agent_cmd.stop(), bool)
            assert isinstance(agent_cmd.restart(), bool)
            assert isinstance(agent_cmd.status(), bool)
            assert isinstance(agent_cmd.logs(), bool)
            assert isinstance(agent_cmd.reset(), bool)
            assert isinstance(agent_cmd.uninstall(), bool)
            
            # Test dict return method
            assert isinstance(agent_cmd.health(), dict)

    def test_exception_handling_robustness(self):
        """Test that all methods handle exceptions gracefully."""
        agent_cmd = AgentCommands()
        
        # Test that all methods return False when exceptions occur
        # Need to patch the instance methods after AgentCommands is created
        with patch.object(agent_cmd.agent_service, 'install_agent_environment', side_effect=Exception("Test error")), \
             patch.object(agent_cmd.agent_service, 'serve_agent', side_effect=Exception("Test error")), \
             patch.object(agent_cmd.agent_service, 'stop_agent', side_effect=Exception("Test error")), \
             patch.object(agent_cmd.agent_service, 'get_agent_status', side_effect=Exception("Test error")), \
             patch.object(agent_cmd.agent_service, 'show_agent_logs', side_effect=Exception("Test error")), \
             patch.object(agent_cmd.agent_service, 'reset_agent_environment', side_effect=Exception("Test error")), \
             patch.object(agent_cmd.agent_service, 'uninstall_agent_environment', side_effect=Exception("Test error")), \
             patch('builtins.print'):
            
            assert agent_cmd.install() is False
            assert agent_cmd.start() is False
            assert agent_cmd.stop() is False
            assert agent_cmd.restart() is False
            assert agent_cmd.status() is False
            assert agent_cmd.logs() is False
            assert agent_cmd.reset() is False
            assert agent_cmd.uninstall() is False
            
            # Health should return error dict
            health_result = agent_cmd.health()
            assert health_result["status"] == "error"

    def test_parameter_validation_edge_cases(self):
        """Test parameter validation and edge cases."""
        agent_cmd = AgentCommands()
        
        with patch.object(agent_cmd.agent_service, 'show_agent_logs', return_value=True) as mock_logs, \
             patch('builtins.print'):
            
            # Test logs with various tail values
            agent_cmd.logs(".", tail=0)
            mock_logs.assert_called_with(".", 0)
            
            agent_cmd.logs(".", tail=1000)
            mock_logs.assert_called_with(".", 1000)
            
            # Test logs with negative tail (should still pass to service)
            agent_cmd.logs(".", tail=-1)
            mock_logs.assert_called_with(".", -1)

    def test_print_message_validation(self):
        """Test that all methods print expected messages."""
        agent_cmd = AgentCommands()
        
        with patch.object(AgentService, 'install_agent_environment', return_value=True), \
             patch.object(AgentService, 'serve_agent', return_value=True), \
             patch.object(AgentService, 'stop_agent', return_value=True), \
             patch.object(AgentService, 'get_agent_status', return_value={}), \
             patch.object(AgentService, 'show_agent_logs', return_value=True), \
             patch.object(AgentService, 'reset_agent_environment', return_value=True), \
             patch.object(AgentService, 'uninstall_agent_environment', return_value=True), \
             patch('builtins.print') as mock_print:
            
            agent_cmd.install("/test")
            assert "🚀 Installing and starting agent services in: /test" in str(mock_print.call_args_list)
            
            agent_cmd.start("/test")
            assert "🚀 Starting agent services in: /test" in str(mock_print.call_args_list)
            
            agent_cmd.stop("/test")
            assert "🛑 Stopping agent services in: /test" in str(mock_print.call_args_list)
            
            agent_cmd.restart("/test")
            assert "🔄 Restarting agent services in: /test" in str(mock_print.call_args_list)
            
            agent_cmd.status("/test")
            assert "🔍 Checking agent status in: /test" in str(mock_print.call_args_list)
            
            agent_cmd.logs("/test")
            assert "📋 Showing agent logs from: /test" in str(mock_print.call_args_list)
            
            agent_cmd.health("/test")
            assert "🔍 Checking agent health in: /test" in str(mock_print.call_args_list)
            
            agent_cmd.reset("/test")
            assert "🗑️ Resetting agent environment in: /test" in str(mock_print.call_args_list)
            
            agent_cmd.uninstall("/test")
            assert "🗑️ Uninstalling agent environment in: /test" in str(mock_print.call_args_list)