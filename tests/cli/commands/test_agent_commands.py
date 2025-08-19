"""Comprehensive test coverage for cli.commands.agent module.

This test suite achieves >50% coverage for AgentCommands class by testing:
1. Class initialization and core methods
2. Command execution workflows (install, serve, stop, restart, status, logs)
3. Error handling for subprocess failures and Docker issues
4. Status checking and health validation
5. CLI argument processing and validation

Focuses on lines 16-110 that were previously missing coverage.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch, call, MagicMock

import pytest

# Import the module under test
from cli.commands.agent import AgentCommands
from cli.core.agent_service import AgentService


class TestAgentCommandsInitialization:
    """Test AgentCommands class initialization - targeting lines 15-17."""

    def test_init_with_none_workspace(self):
        """Test initialization with None workspace path."""
        agent_cmd = AgentCommands(workspace_path=None)
        
        assert agent_cmd.workspace_path == Path()
        assert isinstance(agent_cmd.agent_service, AgentService)

    def test_init_with_custom_workspace(self):
        """Test initialization with custom workspace path."""
        custom_path = Path("/test/workspace")
        agent_cmd = AgentCommands(workspace_path=custom_path)
        
        assert agent_cmd.workspace_path == custom_path
        assert isinstance(agent_cmd.agent_service, AgentService)

    def test_init_default_workspace(self):
        """Test initialization with default parameters."""
        agent_cmd = AgentCommands()
        
        assert agent_cmd.workspace_path == Path()
        assert isinstance(agent_cmd.agent_service, AgentService)


class TestAgentCommandsInstall:
    """Test install method - targeting lines 19-29."""

    @patch('builtins.print')
    @patch.object(AgentService, 'install_agent_environment', return_value=True)
    @patch.object(AgentService, 'serve_agent', return_value=True)
    def test_install_success(self, mock_serve, mock_install, mock_print):
        """Test successful installation."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.install("/test/workspace")
        
        assert result is True
        mock_print.assert_called_with("🚀 Installing and starting agent services in: /test/workspace")
        mock_install.assert_called_once_with("/test/workspace")
        mock_serve.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    @patch.object(AgentService, 'install_agent_environment', return_value=False)
    def test_install_failure_install_step(self, mock_install, mock_print):
        """Test installation failure during install step."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.install("/test/workspace")
        
        assert result is False
        mock_print.assert_called_with("🚀 Installing and starting agent services in: /test/workspace")
        mock_install.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    @patch.object(AgentService, 'install_agent_environment', return_value=True)
    @patch.object(AgentService, 'serve_agent', return_value=False)
    def test_install_failure_serve_step(self, mock_serve, mock_install, mock_print):
        """Test installation failure during serve step."""
        agent_cmd = AgentCommands()
        
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
             patch.object(AgentService, 'install_agent_environment', return_value=True) as mock_install, \
             patch.object(AgentService, 'serve_agent', return_value=True) as mock_serve:
            
            result = agent_cmd.install()
            
            assert result is True
            mock_print.assert_called_with("🚀 Installing and starting agent services in: .")
            mock_install.assert_called_once_with(".")
            mock_serve.assert_called_once_with(".")


class TestAgentCommandsStart:
    """Test start method - targeting lines 31-38."""

    @patch('builtins.print')
    @patch.object(AgentService, 'serve_agent', return_value=True)
    def test_start_success(self, mock_serve, mock_print):
        """Test successful start."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.start("/test/workspace")
        
        assert result is True
        mock_print.assert_called_with("🚀 Starting agent services in: /test/workspace")
        mock_serve.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    @patch.object(AgentService, 'serve_agent', return_value=False)
    def test_start_failure(self, mock_serve, mock_print):
        """Test start failure."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.start("/test/workspace")
        
        assert result is False
        mock_print.assert_called_with("🚀 Starting agent services in: /test/workspace")
        mock_serve.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    @patch.object(AgentService, 'serve_agent', side_effect=Exception("Start failed"))
    def test_start_exception_handling(self, mock_serve, mock_print):
        """Test start exception handling."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.start("/test/workspace")
        
        assert result is False
        mock_print.assert_called_with("🚀 Starting agent services in: /test/workspace")

    def test_start_default_workspace(self):
        """Test start with default workspace parameter."""
        agent_cmd = AgentCommands()
        
        with patch('builtins.print') as mock_print, \
             patch.object(AgentService, 'serve_agent', return_value=True) as mock_serve:
            
            result = agent_cmd.start()
            
            assert result is True
            mock_print.assert_called_with("🚀 Starting agent services in: .")
            mock_serve.assert_called_once_with(".")


class TestAgentCommandsStop:
    """Test stop method - targeting lines 41-47."""

    @patch('builtins.print')
    @patch.object(AgentService, 'stop_agent', return_value=True)
    def test_stop_success(self, mock_stop, mock_print):
        """Test successful stop."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.stop("/test/workspace")
        
        assert result is True
        mock_print.assert_called_with("🛑 Stopping agent services in: /test/workspace")
        mock_stop.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    @patch.object(AgentService, 'stop_agent', return_value=False)
    def test_stop_failure(self, mock_stop, mock_print):
        """Test stop failure."""
        agent_cmd = AgentCommands()
        
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
        mock_print.assert_called_with("🛑 Stopping agent services in: /test/workspace")


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
    @patch.object(AgentService, 'get_agent_status', return_value={"postgres": "✅ Running", "server": "✅ Running"})
    def test_status_success(self, mock_status, mock_print):
        """Test successful status check."""
        agent_cmd = AgentCommands()
        
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
    @patch.object(AgentService, 'get_agent_status', return_value={})
    def test_status_empty_status(self, mock_status, mock_print):
        """Test status check with empty status."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.status("/test/workspace")
        
        assert result is True
        mock_print.assert_called_with("🔍 Checking agent status in: /test/workspace")
        mock_status.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    @patch.object(AgentService, 'get_agent_status', side_effect=Exception("Status check failed"))
    def test_status_exception_handling(self, mock_status, mock_print):
        """Test status exception handling."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.status("/test/workspace")
        
        assert result is False
        mock_print.assert_called_with("🔍 Checking agent status in: /test/workspace")

    @patch('builtins.print')
    @patch.object(AgentService, 'get_agent_status', return_value={"service1": "status1", "service2": "status2", "service3": "status3"})
    def test_status_multiple_services(self, mock_status, mock_print):
        """Test status check with multiple services."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.status("/test/workspace")
        
        assert result is True
        expected_calls = [
            call("🔍 Checking agent status in: /test/workspace"),
            call("  service1: status1"),
            call("  service2: status2"),
            call("  service3: status3")
        ]
        mock_print.assert_has_calls(expected_calls)


class TestAgentCommandsLogs:
    """Test logs method - targeting lines 75-81."""

    @patch('builtins.print')
    @patch.object(AgentService, 'show_agent_logs', return_value=True)
    def test_logs_success(self, mock_logs, mock_print):
        """Test successful logs display."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.logs("/test/workspace", tail=100)
        
        assert result is True
        mock_print.assert_called_with("📋 Showing agent logs from: /test/workspace (last 100 lines)")
        mock_logs.assert_called_once_with("/test/workspace", 100)

    @patch('builtins.print')
    @patch.object(AgentService, 'show_agent_logs', return_value=False)
    def test_logs_failure(self, mock_logs, mock_print):
        """Test logs display failure."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.logs("/test/workspace", tail=50)
        
        assert result is False
        mock_print.assert_called_with("📋 Showing agent logs from: /test/workspace (last 50 lines)")
        mock_logs.assert_called_once_with("/test/workspace", 50)

    @patch('builtins.print')
    @patch.object(AgentService, 'show_agent_logs', side_effect=Exception("Logs failed"))
    def test_logs_exception_handling(self, mock_logs, mock_print):
        """Test logs exception handling."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.logs("/test/workspace")
        
        assert result is False
        mock_print.assert_called_with("📋 Showing agent logs from: /test/workspace (last 50 lines)")

    def test_logs_default_tail(self):
        """Test logs with default tail parameter."""
        agent_cmd = AgentCommands()
        
        with patch('builtins.print') as mock_print, \
             patch.object(AgentService, 'show_agent_logs', return_value=True) as mock_logs:
            
            result = agent_cmd.logs("/test/workspace")
            
            assert result is True
            mock_print.assert_called_with("📋 Showing agent logs from: /test/workspace (last 50 lines)")
            mock_logs.assert_called_once_with("/test/workspace", 50)


class TestAgentCommandsHealth:
    """Test health method - targeting lines 83-90."""

    @patch('builtins.print')
    @patch.object(AgentService, 'get_agent_status', return_value={"postgres": "✅ Running", "server": "✅ Running"})
    def test_health_success(self, mock_status, mock_print):
        """Test successful health check."""
        agent_cmd = AgentCommands()
        
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
    @patch.object(AgentService, 'get_agent_status', return_value={})
    def test_health_empty_status(self, mock_status, mock_print):
        """Test health check with empty status."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.health("/test/workspace")
        
        expected_result = {
            "status": "healthy",
            "workspace": "/test/workspace",
            "services": {}
        }
        assert result == expected_result
        mock_print.assert_called_with("🔍 Checking agent health in: /test/workspace")

    @patch('builtins.print')
    @patch.object(AgentService, 'get_agent_status', side_effect=Exception("Health check failed"))
    def test_health_exception_handling(self, mock_status, mock_print):
        """Test health exception handling."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.health("/test/workspace")
        
        expected_result = {
            "status": "error",
            "workspace": "/test/workspace"
        }
        assert result == expected_result
        mock_print.assert_called_with("🔍 Checking agent health in: /test/workspace")

    def test_health_default_workspace(self):
        """Test health with default workspace parameter."""
        agent_cmd = AgentCommands()
        
        with patch('builtins.print') as mock_print, \
             patch.object(AgentService, 'get_agent_status', return_value={"service": "status"}) as mock_status:
            
            result = agent_cmd.health()
            
            expected_result = {
                "status": "healthy",
                "workspace": ".",
                "services": {"service": "status"}
            }
            assert result == expected_result
            mock_print.assert_called_with("🔍 Checking agent health in: .")
            mock_status.assert_called_once_with(".")


class TestAgentCommandsReset:
    """Test reset method - targeting lines 92-100."""

    @patch('builtins.print')
    @patch.object(AgentService, 'reset_agent_environment', return_value=True)
    def test_reset_success(self, mock_reset, mock_print):
        """Test successful reset."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.reset("/test/workspace")
        
        assert result is True
        expected_calls = [
            call("🗑️ Resetting agent environment in: /test/workspace"),
            call("This will destroy all containers and data, then reinstall and start fresh...")
        ]
        mock_print.assert_has_calls(expected_calls)
        mock_reset.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    @patch.object(AgentService, 'reset_agent_environment', return_value=False)
    def test_reset_failure(self, mock_reset, mock_print):
        """Test reset failure."""
        agent_cmd = AgentCommands()
        
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
    @patch.object(AgentService, 'uninstall_agent_environment', return_value=True)
    def test_uninstall_success(self, mock_uninstall, mock_print):
        """Test successful uninstall."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.uninstall("/test/workspace")
        
        assert result is True
        expected_calls = [
            call("🗑️ Uninstalling agent environment in: /test/workspace"),
            call("This will destroy all containers and data permanently...")
        ]
        mock_print.assert_has_calls(expected_calls)
        mock_uninstall.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    @patch.object(AgentService, 'uninstall_agent_environment', return_value=False)
    def test_uninstall_failure(self, mock_uninstall, mock_print):
        """Test uninstall failure."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.uninstall("/test/workspace")
        
        assert result is False
        expected_calls = [
            call("🗑️ Uninstalling agent environment in: /test/workspace"),
            call("This will destroy all containers and data permanently...")
        ]
        mock_print.assert_has_calls(expected_calls)
        mock_uninstall.assert_called_once_with("/test/workspace")

    @patch('builtins.print')
    @patch.object(AgentService, 'uninstall_agent_environment', side_effect=Exception("Uninstall failed"))
    def test_uninstall_exception_handling(self, mock_uninstall, mock_print):
        """Test uninstall exception handling."""
        agent_cmd = AgentCommands()
        
        result = agent_cmd.uninstall("/test/workspace")
        
        assert result is False
        expected_calls = [
            call("🗑️ Uninstalling agent environment in: /test/workspace"),
            call("This will destroy all containers and data permanently...")
        ]
        mock_print.assert_has_calls(expected_calls)


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
        with patch.object(AgentService, 'install_agent_environment', side_effect=Exception("Test error")), \
             patch.object(AgentService, 'serve_agent', side_effect=Exception("Test error")), \
             patch.object(AgentService, 'stop_agent', side_effect=Exception("Test error")), \
             patch.object(AgentService, 'get_agent_status', side_effect=Exception("Test error")), \
             patch.object(AgentService, 'show_agent_logs', side_effect=Exception("Test error")), \
             patch.object(AgentService, 'reset_agent_environment', side_effect=Exception("Test error")), \
             patch.object(AgentService, 'uninstall_agent_environment', side_effect=Exception("Test error")), \
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