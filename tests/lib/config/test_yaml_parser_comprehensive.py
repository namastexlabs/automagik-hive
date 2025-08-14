"""
Comprehensive test suite for YAMLConfigParser - Critical Coverage Batch 3

Tests YAML parsing, MCP tool validation, error handling, file operations,
and configuration validation for the YAML configuration parser system.

Target: 50%+ coverage for lib/config/yaml_parser.py (92 lines, 18% current)
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml

from lib.config.schemas import AgentConfig, AgentConfigMCP, MCPToolConfig, TeamConfig
from lib.config.yaml_parser import YAMLConfigParser
from lib.mcp.catalog import MCPCatalog


class TestYAMLConfigParser:
    """Comprehensive test suite for YAMLConfigParser class."""

    @pytest.fixture
    def mock_mcp_catalog(self):
        """Provide a mock MCP catalog for testing."""
        catalog = Mock(spec=MCPCatalog)
        catalog.has_server.return_value = True
        return catalog

    @pytest.fixture
    def parser_with_mock_catalog(self, mock_mcp_catalog):
        """Provide parser instance with mock catalog."""
        return YAMLConfigParser(mcp_catalog=mock_mcp_catalog)

    @pytest.fixture
    def valid_agent_config(self):
        """Provide valid agent configuration dictionary."""
        return {
            "agent_id": "test-agent",
            "name": "Test Agent", 
            "version": "1.0.0",
            "description": "Test agent for validation",
            "instructions": "You are a test agent",
            "tools": ["tool1", "mcp.test-server", "tool2"],
            "model": {"name": "gpt-4"},
            "memory": {"enable_user_memories": True}
        }

    @pytest.fixture
    def valid_team_config(self):
        """Provide valid team configuration dictionary."""
        return {
            "team_id": "test-team",
            "name": "Test Team",
            "version": "1.0.0", 
            "description": "Test team for validation",
            "members": ["agent1", "agent2"],
            "mode": "sequential"
        }

    def test_init_with_default_catalog(self):
        """Test initialization with default MCP catalog."""
        parser = YAMLConfigParser()
        
        assert parser.mcp_catalog is not None
        assert isinstance(parser.mcp_catalog, MCPCatalog)

    def test_init_with_custom_catalog(self, mock_mcp_catalog):
        """Test initialization with custom MCP catalog."""
        parser = YAMLConfigParser(mcp_catalog=mock_mcp_catalog)
        
        assert parser.mcp_catalog is mock_mcp_catalog

    def test_parse_agent_config_success(self, parser_with_mock_catalog, valid_agent_config):
        """Test successful agent configuration parsing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_agent_config, f)
            config_path = f.name
        
        try:
            result = parser_with_mock_catalog.parse_agent_config(config_path)
            
            assert isinstance(result, AgentConfigMCP)
            assert result.config.agent_id == "test-agent"
            assert result.config.name == "Test Agent"
            assert "tool1" in result.regular_tools
            assert "tool2" in result.regular_tools
            assert len(result.mcp_tools) == 1
            assert result.mcp_tools[0].server_name == "test-server"
            assert result.mcp_tools[0].enabled is True
        finally:
            Path(config_path).unlink()

    def test_parse_agent_config_file_not_found(self, parser_with_mock_catalog):
        """Test FileNotFoundError for missing configuration file."""
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            parser_with_mock_catalog.parse_agent_config("/nonexistent/file.yaml")

    def test_parse_agent_config_invalid_yaml(self, parser_with_mock_catalog):
        """Test ValueError for malformed YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: {")  # Malformed YAML
            config_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                parser_with_mock_catalog.parse_agent_config(config_path)
        finally:
            Path(config_path).unlink()

    def test_parse_agent_config_non_dict_content(self, parser_with_mock_catalog):
        """Test ValueError for non-dictionary YAML content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(["list", "instead", "of", "dict"], f)
            config_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Configuration file must contain a YAML object"):
                parser_with_mock_catalog.parse_agent_config(config_path)
        finally:
            Path(config_path).unlink()

    def test_parse_agent_config_tools_not_list(self, parser_with_mock_catalog, valid_agent_config):
        """Test ValueError when tools is not a list."""
        valid_agent_config["tools"] = "not-a-list"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_agent_config, f)
            config_path = f.name
        
        try:
            with pytest.raises(ValueError, match="'tools' must be a list"):
                parser_with_mock_catalog.parse_agent_config(config_path)
        finally:
            Path(config_path).unlink()

    def test_parse_team_config_success(self, parser_with_mock_catalog, valid_team_config):
        """Test successful team configuration parsing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_team_config, f)
            config_path = f.name
        
        try:
            result = parser_with_mock_catalog.parse_team_config(config_path)
            
            assert isinstance(result, TeamConfig)
            assert result.team_id == "test-team"
            assert result.name == "Test Team"
            assert result.members == ["agent1", "agent2"]
        finally:
            Path(config_path).unlink()

    def test_parse_team_config_file_not_found(self, parser_with_mock_catalog):
        """Test FileNotFoundError for missing team configuration."""
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            parser_with_mock_catalog.parse_team_config("/nonexistent/team.yaml")

    def test_parse_team_config_invalid_yaml(self, parser_with_mock_catalog):
        """Test ValueError for malformed team YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("{ invalid yaml")
            config_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                parser_with_mock_catalog.parse_team_config(config_path)
        finally:
            Path(config_path).unlink()

    def test_parse_tools_regular_tools_only(self, parser_with_mock_catalog):
        """Test parsing tools list with only regular tools."""
        tools_list = ["tool1", "tool2", "tool3"]
        
        regular, mcp = parser_with_mock_catalog._parse_tools(tools_list)
        
        assert regular == ["tool1", "tool2", "tool3"]
        assert mcp == []

    def test_parse_tools_mcp_tools_only(self, parser_with_mock_catalog):
        """Test parsing tools list with only MCP tools."""
        tools_list = ["mcp.server1", "mcp.server2"]
        
        regular, mcp = parser_with_mock_catalog._parse_tools(tools_list)
        
        assert regular == []
        assert mcp == ["server1", "server2"]

    def test_parse_tools_mixed_tools(self, parser_with_mock_catalog):
        """Test parsing tools list with mixed regular and MCP tools."""
        tools_list = ["regular1", "mcp.mcp_server", "regular2", "mcp.another_server"]
        
        regular, mcp = parser_with_mock_catalog._parse_tools(tools_list)
        
        assert regular == ["regular1", "regular2"]
        assert mcp == ["mcp_server", "another_server"]

    def test_parse_tools_empty_mcp_name(self, parser_with_mock_catalog):
        """Test parsing tools with empty MCP server name."""
        tools_list = ["tool1", "mcp.", "tool2"]  # Empty server name
        
        regular, mcp = parser_with_mock_catalog._parse_tools(tools_list)
        
        assert regular == ["tool1", "tool2"]
        assert mcp == []  # Empty MCP name should be ignored

    def test_parse_tools_non_string_entries(self, parser_with_mock_catalog):
        """Test parsing tools with non-string entries (should be skipped)."""
        tools_list = ["valid_tool", 123, None, "mcp.valid"]
        
        regular, mcp = parser_with_mock_catalog._parse_tools(tools_list)
        
        assert regular == ["valid_tool"]
        assert mcp == ["valid"]

    def test_parse_tools_whitespace_handling(self, parser_with_mock_catalog):
        """Test parsing tools with whitespace in names."""
        tools_list = [" tool1 ", "mcp. server ", " regular2"]
        
        regular, mcp = parser_with_mock_catalog._parse_tools(tools_list)
        
        assert regular == ["tool1", "regular2"]
        assert mcp == ["server"]

    def test_validate_mcp_tools_all_found(self, parser_with_mock_catalog, mock_mcp_catalog):
        """Test MCP tool validation when all servers are found."""
        mock_mcp_catalog.has_server.return_value = True
        mcp_tool_names = ["server1", "server2"]
        
        result = parser_with_mock_catalog._validate_mcp_tools(mcp_tool_names)
        
        assert len(result) == 2
        assert all(tool.enabled for tool in result)
        assert result[0].server_name == "server1"
        assert result[1].server_name == "server2"

    def test_validate_mcp_tools_not_found(self, parser_with_mock_catalog, mock_mcp_catalog):
        """Test MCP tool validation when servers are not found."""
        mock_mcp_catalog.has_server.return_value = False
        mcp_tool_names = ["missing_server"]
        
        result = parser_with_mock_catalog._validate_mcp_tools(mcp_tool_names)
        
        assert len(result) == 1
        assert result[0].server_name == "missing_server"
        assert result[0].enabled is False

    def test_validate_mcp_tools_mixed_results(self, parser_with_mock_catalog, mock_mcp_catalog):
        """Test MCP tool validation with mixed found/not found servers."""
        def has_server_side_effect(server_name):
            return server_name == "found_server"
        
        mock_mcp_catalog.has_server.side_effect = has_server_side_effect
        mcp_tool_names = ["found_server", "missing_server"]
        
        result = parser_with_mock_catalog._validate_mcp_tools(mcp_tool_names)
        
        assert len(result) == 2
        found_tool = next(tool for tool in result if tool.server_name == "found_server")
        missing_tool = next(tool for tool in result if tool.server_name == "missing_server")
        
        assert found_tool.enabled is True
        assert missing_tool.enabled is False

    def test_validate_mcp_tools_exception_handling(self, parser_with_mock_catalog, mock_mcp_catalog):
        """Test MCP tool validation handles exceptions gracefully."""
        mock_mcp_catalog.has_server.side_effect = Exception("Catalog error")
        mcp_tool_names = ["server1"]
        
        result = parser_with_mock_catalog._validate_mcp_tools(mcp_tool_names)
        
        # Should handle exception and continue with empty result
        assert len(result) == 0

    def test_update_agent_config_success(self, parser_with_mock_catalog, valid_agent_config):
        """Test successful agent configuration update."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_agent_config, f)
            config_path = f.name
        
        try:
            updates = {"version": "2.0.0", "new_field": "new_value"}
            parser_with_mock_catalog.update_agent_config(config_path, updates)
            
            # Read back the updated config
            with open(config_path, 'r', encoding='utf-8') as f:
                updated_config = yaml.safe_load(f)
            
            assert updated_config["version"] == "2.0.0"
            assert updated_config["new_field"] == "new_value"
            assert updated_config["agent_id"] == "test-agent"  # Original field preserved
            
        finally:
            Path(config_path).unlink()

    def test_update_agent_config_file_not_found(self, parser_with_mock_catalog):
        """Test update fails with FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            parser_with_mock_catalog.update_agent_config("/nonexistent.yaml", {})

    def test_update_agent_config_read_error(self, parser_with_mock_catalog):
        """Test update fails gracefully with file read errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: {")
            config_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Error updating configuration file"):
                parser_with_mock_catalog.update_agent_config(config_path, {"test": "value"})
        finally:
            Path(config_path).unlink()

    def test_get_mcp_tools_summary(self, parser_with_mock_catalog):
        """Test MCP tools summary generation."""
        # Create mock AgentConfigMCP
        mock_config = Mock(spec=AgentConfigMCP)
        mock_config.all_tools = ["tool1", "mcp_server1", "tool2"]
        mock_config.regular_tools = ["tool1", "tool2"]
        
        enabled_tool = Mock(spec=MCPToolConfig)
        enabled_tool.server_name = "server1"
        enabled_tool.enabled = True
        
        disabled_tool = Mock(spec=MCPToolConfig)
        disabled_tool.server_name = "server2"  
        disabled_tool.enabled = False
        
        mock_config.mcp_tools = [enabled_tool, disabled_tool]
        mock_config.mcp_server_names = ["server1", "server2"]
        
        summary = parser_with_mock_catalog.get_mcp_tools_summary(mock_config)
        
        assert summary["total_tools"] == 3
        assert summary["regular_tools"] == 2
        assert summary["mcp_tools"] == 2
        assert summary["mcp_servers"] == ["server1", "server2"]
        assert summary["enabled_mcp_tools"] == ["server1"]
        assert summary["disabled_mcp_tools"] == ["server2"]

    def test_validate_config_file_valid(self, parser_with_mock_catalog, valid_agent_config):
        """Test configuration file validation for valid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_agent_config, f)
            config_path = f.name
        
        try:
            result = parser_with_mock_catalog.validate_config_file(config_path)
            
            assert result["valid"] is True
            assert result["config_path"] == config_path
            assert result["agent_id"] == "test-agent"
            assert result["version"] == "1.0.0"
            assert result["errors"] == []
            assert "tools_summary" in result
            
        finally:
            Path(config_path).unlink()

    def test_validate_config_file_invalid(self, parser_with_mock_catalog):
        """Test configuration file validation for invalid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid yaml {")
            config_path = f.name
        
        try:
            result = parser_with_mock_catalog.validate_config_file(config_path)
            
            assert result["valid"] is False
            assert result["config_path"] == config_path
            assert result["agent_id"] is None
            assert result["version"] is None
            assert result["tools_summary"] is None
            assert len(result["errors"]) > 0
            
        finally:
            Path(config_path).unlink()

    def test_reload_mcp_catalog(self, parser_with_mock_catalog, mock_mcp_catalog):
        """Test MCP catalog reload functionality."""
        parser_with_mock_catalog.reload_mcp_catalog()
        
        mock_mcp_catalog.reload_catalog.assert_called_once()

    def test_str_representation(self, parser_with_mock_catalog, mock_mcp_catalog):
        """Test string representation includes MCP server count."""
        mock_mcp_catalog.list_servers.return_value = ["server1", "server2", "server3"]
        
        str_repr = str(parser_with_mock_catalog)
        
        assert "YAMLConfigParser" in str_repr
        assert "mcp_servers=3" in str_repr


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""

    def test_empty_tools_list(self):
        """Test parsing empty tools list."""
        parser = YAMLConfigParser()
        
        regular, mcp = parser._parse_tools([])
        
        assert regular == []
        assert mcp == []

    def test_tools_list_with_none_values(self):
        """Test parsing tools list containing None values."""
        parser = YAMLConfigParser()
        
        regular, mcp = parser._parse_tools([None, "tool1", None, "mcp.server"])
        
        assert regular == ["tool1"]
        assert mcp == ["server"]

    def test_file_encoding_issues(self):
        """Test handling of file encoding issues."""
        parser = YAMLConfigParser()
        
        # Create file with non-UTF-8 content
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.yaml', delete=False) as f:
            # Write some bytes that aren't valid UTF-8
            f.write(b'agent_id: test\ndescription: \xff\xfe invalid')
            config_path = f.name
        
        try:
            # Should handle encoding error gracefully
            with pytest.raises((ValueError, UnicodeDecodeError)):
                parser.parse_agent_config(config_path)
        finally:
            Path(config_path).unlink()

    def test_very_large_config_file(self):
        """Test handling of very large configuration files."""
        parser = YAMLConfigParser()
        
        # Create a large config with many tools
        large_config = {
            "agent_id": "large-agent",
            "name": "Large Agent",
            "version": "1.0.0",
            "tools": [f"tool_{i}" for i in range(1000)],  # 1000 tools
            "description": "A" * 10000,  # Large description
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(large_config, f)
            config_path = f.name
        
        try:
            # Should handle large files without issues
            result = parser.parse_agent_config(config_path)
            assert result.config.agent_id == "large-agent"
            assert len(result.regular_tools) == 1000
        finally:
            Path(config_path).unlink()

    def test_concurrent_file_access(self):
        """Test concurrent access to configuration files."""
        import threading
        import time
        
        parser = YAMLConfigParser()
        config = {"agent_id": "concurrent-test", "name": "Test", "version": "1.0.0", "tools": []}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name
        
        results = []
        errors = []
        
        def read_config():
            try:
                result = parser.parse_agent_config(config_path)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        try:
            # Start multiple concurrent reads
            threads = [threading.Thread(target=read_config) for _ in range(5)]
            
            for thread in threads:
                thread.start()
            
            for thread in threads:
                thread.join()
            
            # All reads should succeed
            assert len(results) == 5
            assert len(errors) == 0
            assert all(r.config.agent_id == "concurrent-test" for r in results)
            
        finally:
            Path(config_path).unlink()

    def test_malformed_mcp_tool_names(self):
        """Test handling of malformed MCP tool names."""
        parser = YAMLConfigParser()
        
        # Various malformed MCP tool patterns
        malformed_tools = [
            "mcp.",           # Empty server name
            "mcp..",          # Double dots
            "mcp. server",    # Space in server name
            "mcp.",           # Just mcp.
            "mcp.server-name", # Valid one for comparison
        ]
        
        regular, mcp = parser._parse_tools(malformed_tools)
        
        # Should only extract valid server names
        assert regular == []
        assert mcp == ["server-name"]  # Only the valid one

    @patch('lib.config.yaml_parser.yaml.safe_load')
    def test_yaml_load_exception(self, mock_yaml_load):
        """Test handling of yaml.safe_load exceptions."""
        mock_yaml_load.side_effect = yaml.YAMLError("YAML parsing error")
        parser = YAMLConfigParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("some content")
            config_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                parser.parse_agent_config(config_path)
        finally:
            Path(config_path).unlink()

    def test_permission_denied_file_access(self):
        """Test handling of permission denied errors."""
        parser = YAMLConfigParser()
        
        # Create a file and make it unreadable (on Unix-like systems)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("agent_id: test")
            config_path = f.name
        
        try:
            # Make file unreadable
            import stat
            Path(config_path).chmod(stat.S_IWRITE)  # Write-only (no read permission)
            
            # Should raise appropriate exception
            with pytest.raises((PermissionError, OSError)):
                parser.parse_agent_config(config_path)
                
        except (OSError, NotImplementedError):
            # Permission modification might not work on all systems
            pytest.skip("Cannot modify file permissions on this system")
        finally:
            # Restore permissions and cleanup
            try:
                Path(config_path).chmod(stat.S_IREAD | stat.S_IWRITE)
                Path(config_path).unlink()
            except (OSError, FileNotFoundError):
                pass