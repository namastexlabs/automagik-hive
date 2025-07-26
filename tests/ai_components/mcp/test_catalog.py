"""
Tests for lib/mcp/catalog.py - MCP Catalog system for managing server configurations
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from lib.mcp.catalog import MCPCatalog, MCPServerConfig
from lib.mcp.exceptions import MCPException


class TestMCPServerConfig:
    """Test MCP server configuration data class."""

    def test_basic_server_config_creation(self) -> None:
        """Test creating a basic server configuration."""
        config = MCPServerConfig(
            name="test-server",
            type="command",
            command="python",
            args=["--version"],
            env={"PATH": "/usr/bin"},
        )

        assert config.name == "test-server"
        assert config.type == "command"
        assert config.command == "python"
        assert config.args == ["--version"]
        assert config.env == {"PATH": "/usr/bin"}

    def test_minimal_server_config(self) -> None:
        """Test creating server config with minimal parameters."""
        config = MCPServerConfig(name="minimal-server", type="sse")

        assert config.name == "minimal-server"
        assert config.type == "sse"
        assert config.command is None
        assert config.args == []  # Should be initialized to empty list
        assert config.env == {}  # Should be initialized to empty dict
        assert config.url is None

    def test_post_init_args_initialization(self) -> None:
        """Test that __post_init__ initializes args when None."""
        config = MCPServerConfig(name="test", type="command", args=None)
        assert config.args == []

    def test_post_init_env_initialization(self) -> None:
        """Test that __post_init__ initializes env when None."""
        config = MCPServerConfig(name="test", type="command", env=None)
        assert config.env == {}

    def test_is_sse_server_property(self) -> None:
        """Test is_sse_server property."""
        sse_config = MCPServerConfig(name="sse-server", type="sse")
        command_config = MCPServerConfig(name="cmd-server", type="command")

        assert sse_config.is_sse_server is True
        assert command_config.is_sse_server is False

    def test_is_command_server_property(self) -> None:
        """Test is_command_server property."""
        # Type is command
        command_config = MCPServerConfig(name="cmd-server", type="command")
        assert command_config.is_command_server is True

        # Has command attribute
        command_with_attr = MCPServerConfig(
            name="cmd-server",
            type="other",
            command="python",
        )
        assert command_with_attr.is_command_server is True

        # Neither type nor command
        sse_config = MCPServerConfig(name="sse-server", type="sse")
        assert sse_config.is_command_server is False

    def test_sse_server_with_url(self) -> None:
        """Test SSE server configuration with URL."""
        config = MCPServerConfig(
            name="sse-server",
            type="sse",
            url="http://localhost:8080/sse",
        )

        assert config.is_sse_server is True
        assert config.url == "http://localhost:8080/sse"
        assert config.command is None


class TestMCPCatalog:
    """Test MCP catalog functionality."""

    def test_catalog_with_valid_config_file(self) -> None:
        """Test catalog initialization with valid configuration file."""
        # Create a temporary config file
        config_data = {
            "mcpServers": {
                "test-server": {
                    "type": "command",
                    "command": "python",
                    "args": ["test.py"],
                    "env": {"DEBUG": "1"},
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            catalog = MCPCatalog(temp_path)

            assert len(catalog.available_servers) == 1
            assert "test-server" in catalog.available_servers

            server_config = catalog.available_servers["test-server"]
            assert server_config.name == "test-server"
            assert server_config.type == "command"
            assert server_config.command == "python"
            assert server_config.args == ["test.py"]
            assert server_config.env == {"DEBUG": "1"}
        finally:
            Path(temp_path).unlink()

    def test_catalog_with_missing_config_file(self) -> None:
        """Test catalog initialization with missing configuration file."""
        with pytest.raises(MCPException, match="MCP configuration file not found"):
            MCPCatalog("nonexistent.json")

    def test_catalog_with_invalid_json(self) -> None:
        """Test catalog initialization with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name

        try:
            with pytest.raises(MCPException, match="Invalid JSON in MCP configuration"):
                MCPCatalog(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_catalog_with_non_dict_root(self) -> None:
        """Test catalog initialization with non-dictionary root."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(["not", "a", "dict"], f)
            temp_path = f.name

        try:
            with pytest.raises(MCPException, match="root must be a JSON object"):
                MCPCatalog(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_catalog_with_invalid_mcpservers(self) -> None:
        """Test catalog with invalid mcpServers structure."""
        config_data = {
            "mcpServers": "not a dict",  # Should be a dictionary
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(MCPException, match="'mcpServers' must be an object"):
                MCPCatalog(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_catalog_with_mixed_server_types(self) -> None:
        """Test catalog with both command and SSE servers."""
        config_data = {
            "mcpServers": {
                "command-server": {
                    "type": "command",
                    "command": "node",
                    "args": ["server.js"],
                },
                "sse-server": {"type": "sse", "url": "http://localhost:8080/sse"},
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            catalog = MCPCatalog(temp_path)

            assert len(catalog.available_servers) == 2

            # Check command server
            cmd_server = catalog.available_servers["command-server"]
            assert cmd_server.is_command_server is True
            assert cmd_server.command == "node"

            # Check SSE server
            sse_server = catalog.available_servers["sse-server"]
            assert sse_server.is_sse_server is True
            assert sse_server.url == "http://localhost:8080/sse"
        finally:
            Path(temp_path).unlink()

    def test_catalog_with_default_command_type(self) -> None:
        """Test that servers default to command type."""
        config_data = {
            "mcpServers": {
                "default-server": {
                    "command": "python",
                    "args": ["script.py"],
                    # No explicit type - should default to command
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            catalog = MCPCatalog(temp_path)

            server = catalog.available_servers["default-server"]
            assert server.type == "command"
            assert server.is_command_server is True
        finally:
            Path(temp_path).unlink()

    @patch("lib.mcp.catalog.logger")
    def test_catalog_skips_invalid_server_configs(self, mock_logger) -> None:
        """Test that catalog skips invalid server configurations."""
        config_data = {
            "mcpServers": {
                "valid-server": {"type": "command", "command": "python"},
                "invalid-server": "not a dict",  # Invalid config
                "unknown-type-server": {
                    "type": "unknown",  # Unknown type
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            catalog = MCPCatalog(temp_path)

            # Should only have the valid server
            assert len(catalog.available_servers) == 1
            assert "valid-server" in catalog.available_servers
            assert "invalid-server" not in catalog.available_servers
            assert "unknown-type-server" not in catalog.available_servers

            # Should have logged warnings
            assert mock_logger.warning.call_count >= 2
        finally:
            Path(temp_path).unlink()

    def test_get_server_config_success(self) -> None:
        """Test getting server configuration successfully."""
        config_data = {
            "mcpServers": {"test-server": {"type": "command", "command": "python"}},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            catalog = MCPCatalog(temp_path)
            config = catalog.get_server_config("test-server")

            assert isinstance(config, MCPServerConfig)
            assert config.name == "test-server"
            assert config.command == "python"
        finally:
            Path(temp_path).unlink()

    def test_get_server_config_not_found(self) -> None:
        """Test getting configuration for non-existent server."""
        config_data = {"mcpServers": {}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            catalog = MCPCatalog(temp_path)

            with pytest.raises(MCPException):
                catalog.get_server_config("nonexistent-server")
        finally:
            Path(temp_path).unlink()

    def test_list_servers(self) -> None:
        """Test listing all available servers."""
        config_data = {
            "mcpServers": {
                "server-a": {"type": "command", "command": "a"},
                "server-b": {"type": "command", "command": "b"},
                "server-c": {"type": "sse", "url": "http://c"},
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            catalog = MCPCatalog(temp_path)
            servers = catalog.list_servers()

            assert len(servers) == 3
            assert "server-a" in servers
            assert "server-b" in servers
            assert "server-c" in servers
        finally:
            Path(temp_path).unlink()

    def test_has_server(self) -> None:
        """Test checking if server exists."""
        config_data = {
            "mcpServers": {"existing-server": {"type": "command", "command": "test"}},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            catalog = MCPCatalog(temp_path)

            assert catalog.has_server("existing-server") is True
            assert catalog.has_server("nonexistent-server") is False
        finally:
            Path(temp_path).unlink()

    def test_get_server_info(self) -> None:
        """Test getting detailed server information."""
        config_data = {
            "mcpServers": {
                "info-server": {
                    "type": "command",
                    "command": "python",
                    "args": ["--version"],
                    "env": {"DEBUG": "1"},
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            catalog = MCPCatalog(temp_path)
            info = catalog.get_server_info("info-server")

            assert info["name"] == "info-server"
            assert info["type"] == "command"
            assert info["command"] == "python"
            assert info["args"] == ["--version"]
            assert info["env"] == {"DEBUG": "1"}
            assert info["url"] is None
            assert info["is_sse_server"] is False
            assert info["is_command_server"] is True
        finally:
            Path(temp_path).unlink()

    def test_reload_catalog(self) -> None:
        """Test reloading catalog from configuration file."""
        # Create initial config
        initial_config = {
            "mcpServers": {"initial-server": {"type": "command", "command": "initial"}},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(initial_config, f)
            temp_path = f.name

        try:
            catalog = MCPCatalog(temp_path)
            assert len(catalog.available_servers) == 1
            assert "initial-server" in catalog.available_servers

            # Update config file
            updated_config = {
                "mcpServers": {
                    "updated-server": {"type": "command", "command": "updated"},
                    "new-server": {"type": "sse", "url": "http://new"},
                },
            }

            with open(temp_path, "w") as f:
                json.dump(updated_config, f)

            # Reload catalog
            catalog.reload_catalog()

            assert len(catalog.available_servers) == 2
            assert "initial-server" not in catalog.available_servers
            assert "updated-server" in catalog.available_servers
            assert "new-server" in catalog.available_servers
        finally:
            Path(temp_path).unlink()

    def test_catalog_str_representation(self) -> None:
        """Test string representation of catalog."""
        config_data = {
            "mcpServers": {
                "server-1": {"type": "command", "command": "test1"},
                "server-2": {"type": "command", "command": "test2"},
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            catalog = MCPCatalog(temp_path)
            str_repr = str(catalog)

            assert "MCPCatalog(2 servers:" in str_repr
            assert "server-1" in str_repr
            assert "server-2" in str_repr
        finally:
            Path(temp_path).unlink()

    def test_catalog_repr_representation(self) -> None:
        """Test debug representation of catalog."""
        config_data = {
            "mcpServers": {"test-server": {"type": "command", "command": "test"}},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            catalog = MCPCatalog(temp_path)
            repr_str = repr(catalog)

            assert "MCPCatalog(config_path=" in repr_str
            assert temp_path in repr_str
            assert "test-server" in repr_str
        finally:
            Path(temp_path).unlink()

    def test_empty_mcpservers_section(self) -> None:
        """Test catalog with empty mcpServers section."""
        config_data = {"mcpServers": {}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            catalog = MCPCatalog(temp_path)

            assert len(catalog.available_servers) == 0
            assert catalog.list_servers() == []
        finally:
            Path(temp_path).unlink()

    def test_missing_mcpservers_section(self) -> None:
        """Test catalog with missing mcpServers section."""
        config_data = {"otherConfig": "value"}  # No mcpServers

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            catalog = MCPCatalog(temp_path)

            # Should create empty catalog when mcpServers is missing
            assert len(catalog.available_servers) == 0
            assert catalog.list_servers() == []
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__])
