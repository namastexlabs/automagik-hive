"""Comprehensive tests for cli.core.agent_environment module.

These tests provide extensive coverage for agent environment management including
environment file generation, validation, credential extraction, and error handling.
All tests are designed with RED phase compliance for TDD workflow.
"""

import pytest
import secrets
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, mock_open

from cli.core.agent_environment import (
    AgentEnvironment,
    AgentCredentials,
    EnvironmentConfig,
    create_agent_environment,
    validate_agent_environment,
    cleanup_agent_environment,
    get_agent_ports,
)


@pytest.fixture
def sample_env_example_content() -> str:
    """Sample .env.example content for testing environment generation."""
    return """# Main Environment Configuration
# =========================================================================
HIVE_API_PORT=8886
HIVE_DATABASE_URL=postgresql+psycopg://user:password@localhost:5532/hive
HIVE_CORS_ORIGINS=http://localhost:8886
HIVE_API_KEY=your-hive-api-key-here
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
HIVE_DEFAULT_MODEL=claude-3.5-sonnet
"""


@pytest.fixture
def sample_main_env_content() -> str:
    """Sample main .env content for credential copying tests."""
    return """HIVE_DATABASE_URL=postgresql+psycopg://main_user:main_pass@main_host:5432/hive
ANTHROPIC_API_KEY=sk-main-anthropic-key-12345
OPENAI_API_KEY=sk-main-openai-key-67890
HIVE_DEFAULT_MODEL=claude-3.5-sonnet
HIVE_API_KEY=main-api-key"""


@pytest.fixture
def sample_agent_env_content() -> str:
    """Sample .env.agent content for validation tests."""
    return """# AUTOMAGIK HIVE - AGENT ENVIRONMENT CONFIGURATION
HIVE_API_PORT=38886
HIVE_DATABASE_URL=postgresql+psycopg://agent_user:agent_pass@localhost:35532/hive_agent
HIVE_API_KEY=agent-test-key-12345
HIVE_CORS_ORIGINS=http://localhost:38886
ANTHROPIC_API_KEY=sk-ant-agent-key"""


class TestAgentEnvironmentInitialization:
    """Test AgentEnvironment class initialization and configuration."""

    def test_init_with_workspace_path(self, temp_workspace):
        """Test AgentEnvironment initializes correctly with provided workspace path."""
        env = AgentEnvironment(temp_workspace)
        
        assert env.workspace_path == temp_workspace
        assert env.env_example_path == temp_workspace / ".env.example"
        assert env.env_agent_path == temp_workspace / ".env.agent"
        assert env.main_env_path == temp_workspace / ".env"
        assert isinstance(env.config, EnvironmentConfig)

    def test_init_with_default_workspace(self):
        """Test AgentEnvironment initializes with current directory when no path provided."""
        with patch('pathlib.Path.cwd', return_value=Path('/test/workspace')):
            env = AgentEnvironment()
            assert env.workspace_path == Path('/test/workspace')

    def test_init_creates_proper_config(self, temp_workspace):
        """Test AgentEnvironment creates proper configuration structure."""
        env = AgentEnvironment(temp_workspace)
        config = env.config
        
        assert config.source_file == temp_workspace / ".env.example"
        assert config.target_file == temp_workspace / ".env.agent"
        assert config.port_mappings == {"HIVE_API_PORT": 38886, "POSTGRES_PORT": 35532}
        assert config.database_suffix == "_agent"
        assert config.cors_port_mapping == {8886: 38886, 5532: 35532}


class TestEnvironmentFileGeneration:
    """Test environment file generation functionality."""

    def test_generate_env_agent_success(self, temp_workspace, sample_env_example_content):
        """Test successful generation of .env.agent from .env.example."""
        # Setup
        env_example_file = temp_workspace / ".env.example"
        env_example_file.write_text(sample_env_example_content)
        env = AgentEnvironment(temp_workspace)

        # Execute
        result_path = env.generate_env_agent()

        # Verify
        assert result_path == env.env_agent_path
        assert result_path.exists()
        content = result_path.read_text()
        
        # Check port mappings
        assert "HIVE_API_PORT=38886" in content
        assert "HIVE_API_PORT=8886" not in content
        
        # Check database transformations
        assert "postgresql+psycopg://user:password@localhost:35532/hive_agent" in content
        assert "/hive" not in content or "/hive_agent" in content
        
        # Check CORS transformations
        assert "http://localhost:38886" in content
        assert "http://localhost:8886" not in content
        
        # Check agent-specific header
        assert "AUTOMAGIK HIVE - AGENT ENVIRONMENT CONFIGURATION" in content
        assert "Main Environment Configuration" not in content

    def test_generate_env_agent_file_exists_error(self, temp_workspace):
        """Test generation fails when .env.agent exists and force=False."""
        env = AgentEnvironment(temp_workspace)
        env.env_agent_path.touch()  # Create existing file

        with pytest.raises(FileExistsError, match=f"File {env.env_agent_path} already exists"):
            env.generate_env_agent(force=False)

    def test_generate_env_agent_force_overwrite(self, temp_workspace, sample_env_example_content):
        """Test generation succeeds with force=True when file exists."""
        # Setup
        env_example_file = temp_workspace / ".env.example"
        env_example_file.write_text(sample_env_example_content)
        env = AgentEnvironment(temp_workspace)
        env.env_agent_path.write_text("old_content_should_be_replaced")

        # Execute
        result_path = env.generate_env_agent(force=True)

        # Verify
        assert result_path.exists()
        content = result_path.read_text()
        assert "old_content_should_be_replaced" not in content
        assert "HIVE_API_PORT=38886" in content

    def test_generate_env_agent_template_missing_error(self, temp_workspace):
        """Test generation fails when .env.example template is missing."""
        env = AgentEnvironment(temp_workspace)
        
        with pytest.raises(FileNotFoundError, match=f"Template file {env.env_example_path} not found"):
            env.generate_env_agent()

    def test_port_mappings_transformation(self, temp_workspace):
        """Test port mappings are correctly applied during generation."""
        template_content = "HIVE_API_PORT=8886\nPOSTGRES_PORT=5532\nOTHER_PORT=9999"
        env_example_file = temp_workspace / ".env.example"
        env_example_file.write_text(template_content)
        env = AgentEnvironment(temp_workspace)

        env.generate_env_agent()
        content = env.env_agent_path.read_text()
        
        assert "HIVE_API_PORT=38886" in content
        assert "POSTGRES_PORT=35532" in content
        assert "OTHER_PORT=9999" in content  # Unchanged

    def test_database_mappings_transformation(self, temp_workspace):
        """Test database name transformations during generation."""
        template_content = "DATABASE_URL=postgresql://user:pass@host:5432/hive\nOTHER_DB=/other_hive"
        env_example_file = temp_workspace / ".env.example"
        env_example_file.write_text(template_content)
        env = AgentEnvironment(temp_workspace)

        env.generate_env_agent()
        content = env.env_agent_path.read_text()
        
        assert "/hive_agent" in content
        assert "/other_hive" in content  # Unchanged - not exact match

    def test_cors_mappings_transformation(self, temp_workspace):
        """Test CORS origin transformations during generation."""
        template_content = "CORS_ORIGINS=http://localhost:8886,https://localhost:8886"
        env_example_file = temp_workspace / ".env.example"
        env_example_file.write_text(template_content)
        env = AgentEnvironment(temp_workspace)

        env.generate_env_agent()
        content = env.env_agent_path.read_text()
        
        assert "http://localhost:38886" in content
        assert "https://localhost:38886" in content
        assert "http://localhost:8886" not in content


class TestEnvironmentValidation:
    """Test environment validation functionality."""

    def test_validate_environment_success(self, temp_workspace):
        """Test validation succeeds for properly configured environment."""
        env = AgentEnvironment(temp_workspace)
        env.env_agent_path.write_text(
            "HIVE_API_PORT=38886\n"
            "HIVE_DATABASE_URL=postgresql+psycopg://user:pass@host:35532/hive_agent\n"
            "HIVE_API_KEY=valid-api-key-12345\n"
        )

        result = env.validate_environment()
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0
        assert result["config"]["HIVE_API_KEY"] == "valid-api-key-12345"
        assert result["config"]["HIVE_API_PORT"] == "38886"

    def test_validate_environment_missing_file(self, temp_workspace):
        """Test validation fails when .env.agent file is missing."""
        env = AgentEnvironment(temp_workspace)
        
        result = env.validate_environment()
        
        assert result["valid"] is False
        assert f"Agent environment file {env.env_agent_path} not found" in result["errors"]
        assert result["config"] is None

    def test_validate_environment_missing_required_keys(self, temp_workspace):
        """Test validation identifies missing required configuration keys."""
        env = AgentEnvironment(temp_workspace)
        env.env_agent_path.write_text("SOME_OTHER_KEY=value\n")

        result = env.validate_environment()
        
        assert result["valid"] is False
        assert any("Missing required key: HIVE_API_PORT" in error for error in result["errors"])
        assert any("Missing required key: HIVE_DATABASE_URL" in error for error in result["errors"])
        assert any("Missing required key: HIVE_API_KEY" in error for error in result["errors"])

    def test_validate_environment_invalid_port_format(self, temp_workspace):
        """Test validation catches invalid port format."""
        env = AgentEnvironment(temp_workspace)
        env.env_agent_path.write_text(
            "HIVE_API_PORT=not-a-port\n"
            "HIVE_DATABASE_URL=postgresql+psycopg://user:pass@host:35532/hive_agent\n"
            "HIVE_API_KEY=valid-key\n"
        )

        result = env.validate_environment()
        
        assert result["valid"] is False
        assert any("HIVE_API_PORT must be a valid integer" in error for error in result["errors"])

    def test_validate_environment_wrong_port_warning(self, temp_workspace):
        """Test validation generates warnings for unexpected port values."""
        env = AgentEnvironment(temp_workspace)
        env.env_agent_path.write_text(
            "HIVE_API_PORT=8886\n"  # Wrong port, should be 38886
            "HIVE_DATABASE_URL=postgresql+psycopg://user:pass@host:5432/hive\n"  # Wrong port and db
            "HIVE_API_KEY=valid-key\n"
        )

        result = env.validate_environment()
        
        assert result["valid"] is True  # No errors, just warnings
        assert any("Expected HIVE_API_PORT=38886, got 8886" in warning for warning in result["warnings"])
        assert any("Expected database port 35532" in warning for warning in result["warnings"])
        assert any("Expected database name 'hive_agent'" in warning for warning in result["warnings"])

    def test_validate_environment_exception_handling(self, temp_workspace):
        """Test validation handles file reading exceptions gracefully."""
        env = AgentEnvironment(temp_workspace)
        
        # Create the .env.agent file so the file existence check passes
        env.env_agent_path.write_text("dummy content")
        
        # Mock the _load_env_file method to raise an exception
        with patch.object(env, '_load_env_file', side_effect=Exception("File read error")):
            result = env.validate_environment()
            
            assert result["valid"] is False
            assert any("Failed to validate environment: File read error" in error for error in result["errors"])
            assert result["config"] is None


class TestCredentialExtraction:
    """Test credential extraction and management functionality."""

    def test_get_agent_credentials_success(self, temp_workspace):
        """Test successful extraction of agent credentials from environment file."""
        env = AgentEnvironment(temp_workspace)
        env.env_agent_path.write_text(
            "HIVE_API_PORT=38886\n"
            "HIVE_DATABASE_URL=postgresql+psycopg://test_user:test_pass@db_host:35532/hive_agent\n"
            "HIVE_API_KEY=test-api-key-12345\n"
            "HIVE_CORS_ORIGINS=http://localhost:3000,https://app.example.com\n"
        )

        creds = env.get_agent_credentials()
        
        assert isinstance(creds, AgentCredentials)
        assert creds.postgres_user == "test_user"
        assert creds.postgres_password == "test_pass"
        assert creds.postgres_db == "hive_agent"
        assert creds.postgres_port == 35532
        assert creds.hive_api_key == "test-api-key-12345"
        assert creds.hive_api_port == 38886
        assert creds.cors_origins == "http://localhost:3000,https://app.example.com"

    def test_get_agent_credentials_missing_file(self, temp_workspace):
        """Test credential extraction returns None when file is missing."""
        env = AgentEnvironment(temp_workspace)
        
        creds = env.get_agent_credentials()
        
        assert creds is None

    def test_get_agent_credentials_malformed_database_url(self, temp_workspace):
        """Test credential extraction handles malformed database URLs gracefully."""
        env = AgentEnvironment(temp_workspace)
        env.env_agent_path.write_text(
            "HIVE_API_PORT=38886\n"
            "HIVE_DATABASE_URL=invalid-database-url\n"
            "HIVE_API_KEY=test-key\n"
        )

        creds = env.get_agent_credentials()
        
        assert creds is None

    def test_get_agent_credentials_partial_database_info(self, temp_workspace):
        """Test credential extraction with missing database URL components."""
        env = AgentEnvironment(temp_workspace)
        env.env_agent_path.write_text(
            "HIVE_API_PORT=38886\n"
            "HIVE_API_KEY=test-key\n"
            # Missing HIVE_DATABASE_URL
        )

        creds = env.get_agent_credentials()
        
        assert isinstance(creds, AgentCredentials)
        assert creds.postgres_user == ""
        assert creds.postgres_password == ""
        assert creds.postgres_db == "hive_agent"  # Default value
        assert creds.postgres_port == 35532  # Default value
        assert creds.hive_api_key == "test-key"
        assert creds.hive_api_port == 38886

    def test_get_agent_credentials_exception_handling(self, temp_workspace):
        """Test credential extraction handles file reading exceptions."""
        env = AgentEnvironment(temp_workspace)
        env.env_agent_path.write_text("VALID_CONTENT=value")
        
        with patch.object(env, '_load_env_file', side_effect=Exception("Read error")):
            creds = env.get_agent_credentials()
            assert creds is None


class TestDatabaseUrlParsing:
    """Test database URL parsing functionality."""

    @pytest.mark.parametrize("url,expected", [
        (
            "postgresql+psycopg://user:password@host:5432/database",
            {"user": "user", "password": "password", "host": "host", "port": 5432, "database": "database"}
        ),
        (
            "postgresql+psycopg://user@host:5432/database",
            {"user": "user", "password": "", "host": "host", "port": 5432, "database": "database"}
        ),
        (
            "postgresql+psycopg://user:password@host/database",
            {"user": "user", "password": "password", "host": "host", "port": 5432, "database": "database"}
        ),
        (
            "postgresql://simple_user:simple_pass@simple_host:1234/simple_db",
            {"user": "simple_user", "password": "simple_pass", "host": "simple_host", "port": 1234, "database": "simple_db"}
        ),
    ])
    def test_parse_database_url_valid_formats(self, temp_workspace, url, expected):
        """Test parsing of valid database URL formats."""
        env = AgentEnvironment(temp_workspace)
        result = env._parse_database_url(url)
        assert result == expected

    @pytest.mark.parametrize("invalid_url", [
        "invalid-protocol://user:pass@host:port/db",
        "postgresql+psycopg://user_pass@host:port/db",  # Missing password separator
        "postgresql+psycopg://user:pass@host_port/db",  # Missing port separator
        "postgresql+psycopg://user:pass@host:port",     # Missing database
        "postgresql+psycopg://host:port/db",            # Missing user
        "not-a-url-at-all",
        "",
        "postgresql+psycopg://",
    ])
    def test_parse_database_url_invalid_formats(self, temp_workspace, invalid_url):
        """Test parsing handles invalid database URL formats."""
        env = AgentEnvironment(temp_workspace)
        result = env._parse_database_url(invalid_url)
        assert result is None

    def test_parse_database_url_exception_handling(self, temp_workspace):
        """Test database URL parsing handles unexpected exceptions."""
        env = AgentEnvironment(temp_workspace)
        
        # Test with URL that might cause unexpected parsing issues
        result = env._parse_database_url("postgresql+psycopg://user:pass@[::1]:5432/db")
        # Should handle IPv6 addresses gracefully (return None for now)
        assert result is None


class TestEnvironmentUpdates:
    """Test environment file update functionality."""

    def test_update_environment_success(self, temp_workspace):
        """Test successful environment variable updates."""
        env = AgentEnvironment(temp_workspace)
        env.env_agent_path.write_text(
            "EXISTING_KEY=old_value\n"
            "# Comment line\n"
            "ANOTHER_KEY=another_value\n"
        )
        
        updates = {
            "EXISTING_KEY": "new_value",
            "NEW_KEY": "added_value",
            "ANOTHER_KEY": "updated_another_value"
        }

        success = env.update_environment(updates)
        
        assert success is True
        content = env.env_agent_path.read_text()
        assert "EXISTING_KEY=new_value" in content
        assert "NEW_KEY=added_value" in content
        assert "ANOTHER_KEY=updated_another_value" in content
        assert "# Comment line" in content  # Comments preserved

    def test_update_environment_missing_file(self, temp_workspace):
        """Test update fails when environment file doesn't exist."""
        env = AgentEnvironment(temp_workspace)
        
        success = env.update_environment({"KEY": "value"})
        
        assert success is False

    def test_update_environment_file_permission_error(self, temp_workspace):
        """Test update handles file permission errors gracefully."""
        env = AgentEnvironment(temp_workspace)
        env.env_agent_path.write_text("EXISTING_KEY=value")
        
        with patch('pathlib.Path.read_text', side_effect=PermissionError("Access denied")):
            success = env.update_environment({"KEY": "value"})
            assert success is False

    def test_update_environment_write_error(self, temp_workspace):
        """Test update handles file write errors gracefully."""
        env = AgentEnvironment(temp_workspace)
        env.env_agent_path.write_text("EXISTING_KEY=value")
        
        with patch('pathlib.Path.write_text', side_effect=OSError("Disk full")):
            success = env.update_environment({"KEY": "new_value"})
            assert success is False


class TestCredentialCopying:
    """Test credential copying from main environment."""

    def test_copy_credentials_from_main_env_success(self, temp_workspace, sample_main_env_content):
        """Test successful copying of credentials from main .env file."""
        env = AgentEnvironment(temp_workspace)
        env.main_env_path.write_text(sample_main_env_content)
        env.env_agent_path.write_text("HIVE_API_PORT=38886\n")  # Initial agent env

        success = env.copy_credentials_from_main_env()
        
        assert success is True
        content = env.env_agent_path.read_text()
        assert "ANTHROPIC_API_KEY=sk-main-anthropic-key-12345" in content
        assert "OPENAI_API_KEY=sk-main-openai-key-67890" in content
        assert "HIVE_DEFAULT_MODEL=claude-3.5-sonnet" in content
        # Database URL should be transformed for agent use
        assert "HIVE_DATABASE_URL=postgresql+psycopg://main_user:main_pass@main_host:35532/hive_agent" in content

    def test_copy_credentials_missing_main_env(self, temp_workspace):
        """Test copying fails when main .env file doesn't exist."""
        env = AgentEnvironment(temp_workspace)
        
        success = env.copy_credentials_from_main_env()
        
        assert success is False

    def test_copy_credentials_exception_handling(self, temp_workspace):
        """Test credential copying handles exceptions gracefully."""
        env = AgentEnvironment(temp_workspace)
        env.main_env_path.write_text("VALID_CONTENT=value")
        
        with patch.object(env, '_load_env_file', side_effect=Exception("Read error")):
            success = env.copy_credentials_from_main_env()
            assert success is False


class TestApiKeyManagement:
    """Test API key generation and management."""

    def test_ensure_agent_api_key_generates_for_placeholder(self, temp_workspace):
        """Test API key generation when current key is placeholder."""
        env = AgentEnvironment(temp_workspace)
        env.env_agent_path.write_text("HIVE_API_KEY=your-hive-api-key-here\n")
        
        success = env.ensure_agent_api_key()
        
        assert success is True
        content = env.env_agent_path.read_text()
        assert "your-hive-api-key-here" not in content
        assert "HIVE_API_KEY=" in content
        # Verify a real key was generated (should be longer than placeholder)
        new_key = content.split("HIVE_API_KEY=")[1].split("\n")[0]
        assert len(new_key) > 20  # Generated keys should be substantial

    def test_ensure_agent_api_key_generates_for_missing(self, temp_workspace):
        """Test API key generation when key is missing."""
        env = AgentEnvironment(temp_workspace)
        env.env_agent_path.write_text("OTHER_KEY=value\n")
        
        success = env.ensure_agent_api_key()
        
        assert success is True
        content = env.env_agent_path.read_text()
        assert "HIVE_API_KEY=" in content

    def test_ensure_agent_api_key_keeps_existing(self, temp_workspace):
        """Test existing valid API key is preserved."""
        existing_key = "my-existing-secret-key-12345"
        env = AgentEnvironment(temp_workspace)
        env.env_agent_path.write_text(f"HIVE_API_KEY={existing_key}\n")
        
        success = env.ensure_agent_api_key()
        
        assert success is True
        content = env.env_agent_path.read_text()
        assert f"HIVE_API_KEY={existing_key}" in content

    def test_ensure_agent_api_key_missing_file(self, temp_workspace):
        """Test API key management fails when agent environment file is missing."""
        env = AgentEnvironment(temp_workspace)
        
        success = env.ensure_agent_api_key()
        
        assert success is False

    def test_generate_agent_api_key_format(self, temp_workspace):
        """Test generated API keys have expected format and entropy."""
        env = AgentEnvironment(temp_workspace)
        
        key1 = env.generate_agent_api_key()
        key2 = env.generate_agent_api_key()
        
        # Keys should be different
        assert key1 != key2
        # Keys should be URL-safe base64 format
        assert all(c.isalnum() or c in '-_' for c in key1)
        assert all(c.isalnum() or c in '-_' for c in key2)
        # Keys should be substantial length (32 bytes = ~43 chars in base64)
        assert len(key1) >= 40
        assert len(key2) >= 40


class TestEnvironmentCleanup:
    """Test environment cleanup functionality."""

    def test_clean_environment_success(self, temp_workspace):
        """Test successful cleanup of agent environment files."""
        env = AgentEnvironment(temp_workspace)
        env.env_agent_path.write_text("CONTENT_TO_DELETE=value")
        assert env.env_agent_path.exists()

        success = env.clean_environment()
        
        assert success is True
        assert not env.env_agent_path.exists()

    def test_clean_environment_missing_file(self, temp_workspace):
        """Test cleanup succeeds even when file doesn't exist."""
        env = AgentEnvironment(temp_workspace)
        assert not env.env_agent_path.exists()

        success = env.clean_environment()
        
        assert success is True

    def test_clean_environment_permission_error(self, temp_workspace):
        """Test cleanup handles permission errors gracefully."""
        env = AgentEnvironment(temp_workspace)
        env.env_agent_path.write_text("content")
        
        with patch('pathlib.Path.unlink', side_effect=PermissionError("Access denied")):
            success = env.clean_environment()
            assert success is False


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_create_agent_environment_function(self, temp_workspace):
        """Test create_agent_environment convenience function."""
        with patch('cli.core.agent_environment.AgentEnvironment') as mock_env_class:
            mock_env = Mock()
            mock_env_class.return_value = mock_env
            
            result = create_agent_environment(temp_workspace)
            
            mock_env_class.assert_called_once_with(temp_workspace)
            mock_env.create.assert_called_once()
            assert result == mock_env

    def test_validate_agent_environment_function(self, temp_workspace):
        """Test validate_agent_environment convenience function."""
        # This is a stub function that currently returns True
        result = validate_agent_environment(temp_workspace)
        assert result is True

    def test_cleanup_agent_environment_function(self, temp_workspace):
        """Test cleanup_agent_environment convenience function."""
        # This is a stub function that currently returns True
        result = cleanup_agent_environment(temp_workspace)
        assert result is True

    def test_get_agent_ports_function(self):
        """Test get_agent_ports convenience function."""
        result = get_agent_ports()
        
        assert isinstance(result, dict)
        assert "api" in result
        assert "postgres" in result
        assert result["api"] == 38886
        assert result["postgres"] == 35532


class TestInternalHelperMethods:
    """Test internal helper methods for comprehensive coverage."""

    def test_load_env_file_success(self, temp_workspace):
        """Test _load_env_file helper method."""
        env = AgentEnvironment(temp_workspace)
        test_file = temp_workspace / "test.env"
        test_file.write_text(
            "KEY1=value1\n"
            "KEY2=value2\n"
            "# Comment line\n"
            "KEY3=value with spaces\n"
            "\n"  # Empty line
            "KEY4=\n"  # Empty value
        )
        
        result = env._load_env_file(test_file)
        
        expected = {
            "KEY1": "value1",
            "KEY2": "value2",
            "KEY3": "value with spaces",
            "KEY4": ""
        }
        assert result == expected

    def test_load_env_file_missing(self, temp_workspace):
        """Test _load_env_file with missing file."""
        env = AgentEnvironment(temp_workspace)
        missing_file = temp_workspace / "missing.env"
        
        result = env._load_env_file(missing_file)
        
        assert result == {}

    def test_build_agent_database_url(self, temp_workspace):
        """Test _build_agent_database_url helper method."""
        env = AgentEnvironment(temp_workspace)
        db_info = {
            "user": "test_user",
            "password": "test_pass",
            "host": "test_host",
            "port": 5432,
            "database": "original_db"
        }
        
        result = env._build_agent_database_url(db_info)
        
        expected = "postgresql+psycopg://test_user:test_pass@test_host:35532/hive_agent"
        assert result == expected

    def test_apply_agent_specific_config_header_replacement(self, temp_workspace):
        """Test _apply_agent_specific_config replaces headers correctly."""
        env = AgentEnvironment(temp_workspace)
        content = """# Original Header
# Some comments
# End of header

KEY=value
ANOTHER_KEY=another_value"""
        
        result = env._apply_agent_specific_config(content)
        
        assert "AUTOMAGIK HIVE - AGENT ENVIRONMENT CONFIGURATION" in result
        assert "Original Header" not in result
        assert "KEY=value" in result
        assert "ANOTHER_KEY=another_value" in result
        assert "Port mappings: HIVE_API_PORT: 8886 → 38886" in result
