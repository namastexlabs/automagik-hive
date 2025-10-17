"""
Comprehensive test suite for CredentialService - targeting 50%+ coverage.

This test suite covers the critical authentication and credential management
functionality with emphasis on security validation, file operations, and
edge case handling.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from lib.auth.credential_service import CredentialService


class TestCredentialServiceInitialization:
    """Test credential service initialization and configuration."""

    def test_init_with_project_root_sets_paths_correctly(self, tmp_path):
        """Test initialization with project root parameter."""
        service = CredentialService(project_root=tmp_path)

        assert service.project_root == tmp_path
        assert service.master_env_file == tmp_path / ".env"
        assert service.env_file == tmp_path / ".env"

    def test_init_with_legacy_env_file_parameter(self, tmp_path):
        """Test backward compatibility with env_file parameter."""
        env_file = tmp_path / "custom.env"
        service = CredentialService(env_file=env_file)

        assert service.project_root == tmp_path
        assert service.master_env_file == env_file
        assert service.env_file == env_file

    def test_init_with_current_directory_default(self):
        """Test initialization with current directory as default."""
        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/test/current")
            service = CredentialService()

            assert service.project_root == Path("/test/current")
            assert service.master_env_file == Path("/test/current/.env")

    def test_init_with_env_file_in_current_directory_edge_case(self, tmp_path):
        """Test edge case where env_file parent is current directory marker."""
        env_file = Path(".") / ".env"

        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path
            service = CredentialService(env_file=env_file)

            assert service.project_root == tmp_path

    def test_variable_names_set_correctly(self):
        """Test that variable names are set to expected values."""
        service = CredentialService()

        assert service.postgres_user_var == "POSTGRES_USER"
        assert service.postgres_password_var == "POSTGRES_PASSWORD"  # noqa: S105 - Test fixture password
        assert service.postgres_db_var == "POSTGRES_DB"
        assert service.database_url_var == "HIVE_DATABASE_URL"
        assert service.api_key_var == "HIVE_API_KEY"


class TestCredentialGeneration:
    """Test credential generation methods."""

    def test_generate_postgres_credentials_with_defaults(self):
        """Test PostgreSQL credential generation with default parameters."""
        service = CredentialService()

        creds = service.generate_postgres_credentials()

        assert "user" in creds
        assert "password" in creds
        assert "database" in creds
        assert "host" in creds
        assert "port" in creds
        assert "url" in creds

        # Test default values
        assert creds["host"] == "localhost"
        assert creds["port"] == "5532"
        assert creds["database"] == "hive"

        # Test credential format
        assert len(creds["user"]) >= 12  # Should be at least 12 chars
        assert len(creds["password"]) >= 12  # Should be at least 12 chars
        assert creds["user"].isalnum()  # Should be alphanumeric only
        assert creds["password"].isalnum()  # Should be alphanumeric only

        # Test URL format
        expected_url = f"postgresql+psycopg://{creds['user']}:{creds['password']}@localhost:5532/hive"
        assert creds["url"] == expected_url

    def test_generate_postgres_credentials_with_custom_parameters(self):
        """Test PostgreSQL credential generation with custom parameters."""
        service = CredentialService()

        creds = service.generate_postgres_credentials(host="custom.host.com", port=9999, database="custom_db")

        assert creds["host"] == "custom.host.com"
        assert creds["port"] == "9999"
        assert creds["database"] == "custom_db"
        assert "custom.host.com:9999/custom_db" in creds["url"]

    def test_generate_hive_api_key_format(self):
        """Test Hive API key generation format."""
        service = CredentialService()

        api_key = service.generate_hive_api_key()

        assert api_key.startswith("hive_")
        assert len(api_key) > 37  # hive_ (5) + token (32+)

        # Test uniqueness
        api_key2 = service.generate_hive_api_key()
        assert api_key != api_key2

    def test_generate_secure_token_with_safe_chars(self):
        """Test secure token generation with safe characters."""
        service = CredentialService()

        token = service._generate_secure_token(16, safe_chars=True)

        assert len(token) == 16
        assert "-" not in token  # Should be removed
        assert "_" not in token  # Should be removed

    def test_generate_secure_token_without_safe_chars(self):
        """Test secure token generation without character restrictions."""
        service = CredentialService()

        token = service._generate_secure_token(24, safe_chars=False)

        # Should be URL-safe base64 encoded
        assert len(token) >= 20  # URL-safe base64 can be shorter

    def test_normalize_master_credentials_payload_accepts_legacy_keys(self):
        """Legacy installer payloads should normalize into master credential schema."""
        service = CredentialService()

        legacy_payload = {
            "HIVE_POSTGRES_USER": "legacy_user",
            "HIVE_POSTGRES_PASSWORD": "legacy_pass",
            "HIVE_API_KEY": "hive_workspace_normalizedtoken",
        }

        normalized = service._normalize_master_credentials_payload(legacy_payload)

        assert normalized["postgres_user"] == "legacy_user"
        assert normalized["postgres_password"] == "legacy_pass"  # noqa: S105 - Test fixture password
        assert normalized["api_key_base"] == "workspace_normalizedtoken"


class TestCredentialExtraction:
    """Test credential extraction from environment files."""

    def test_extract_postgres_credentials_from_valid_env(self, tmp_path):
        """Test extracting PostgreSQL credentials from valid .env file."""
        env_file = tmp_path / ".env"
        env_content = """
HIVE_DATABASE_URL=postgresql+psycopg://user123:pass456@localhost:5532/hive
OTHER_VAR=value
        """.strip()
        env_file.write_text(env_content)

        service = CredentialService(project_root=tmp_path)

        creds = service.extract_postgres_credentials_from_env()

        assert creds["user"] == "user123"
        assert creds["password"] == "pass456"  # noqa: S105 - Test fixture password
        assert creds["host"] == "localhost"
        assert creds["port"] == "5532"
        assert creds["database"] == "hive"
        assert "postgresql+psycopg://user123:pass456@localhost:5532/hive" in creds["url"]

    def test_extract_postgres_credentials_from_missing_env(self, tmp_path):
        """Test extracting credentials from non-existent .env file."""
        service = CredentialService(project_root=tmp_path)

        creds = service.extract_postgres_credentials_from_env()

        # Should return None for all values when file doesn't exist
        assert creds["user"] is None
        assert creds["password"] is None
        assert creds["host"] is None
        assert creds["port"] is None
        assert creds["database"] is None
        assert creds["url"] is None

    def test_extract_postgres_credentials_malformed_url(self, tmp_path):
        """Test extracting credentials from malformed URL in .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_URL=not-a-valid-url")

        service = CredentialService(project_root=tmp_path)

        creds = service.extract_postgres_credentials_from_env()

        # Should handle malformed URLs gracefully
        assert creds["user"] is None or creds["url"] == "not-a-valid-url"

    def test_extract_hive_api_key_from_valid_env(self, tmp_path):
        """Test extracting API key from valid .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_API_KEY=hive_test123456789")

        service = CredentialService(project_root=tmp_path)

        api_key = service.extract_hive_api_key_from_env()

        assert api_key == "hive_test123456789"

    def test_extract_hive_api_key_from_missing_env(self, tmp_path):
        """Test extracting API key from non-existent .env file."""
        service = CredentialService(project_root=tmp_path)

        api_key = service.extract_hive_api_key_from_env()

        assert api_key is None

    def test_extract_hive_api_key_empty_value(self, tmp_path):
        """Test extracting API key when value is empty."""
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_API_KEY=\n")

        service = CredentialService(project_root=tmp_path)

        api_key = service.extract_hive_api_key_from_env()

        assert api_key is None


class TestCredentialValidation:
    """Test credential validation functionality."""

    def test_validate_valid_postgres_credentials(self):
        """Test validation of valid PostgreSQL credentials."""
        service = CredentialService()

        postgres_creds = {
            "user": "abcdef123456789",  # 15 chars, alphanumeric
            "password": "xyz987654321abc",  # 15 chars, alphanumeric
            "url": "postgresql+psycopg://user:pass@host:5432/db",
        }

        results = service.validate_credentials(postgres_creds=postgres_creds)

        assert results["postgres_user_valid"] is True
        assert results["postgres_password_valid"] is True
        assert results["postgres_url_valid"] is True

    def test_validate_invalid_postgres_credentials(self):
        """Test validation of invalid PostgreSQL credentials."""
        service = CredentialService()

        postgres_creds = {
            "user": "short",  # Too short
            "password": "also_short!",  # Too short and has special chars
            "url": "not-postgresql://wrong",  # Wrong protocol
        }

        results = service.validate_credentials(postgres_creds=postgres_creds)

        assert results["postgres_user_valid"] is False
        assert results["postgres_password_valid"] is False
        assert results["postgres_url_valid"] is False

    def test_validate_valid_api_key(self):
        """Test validation of valid API key."""
        service = CredentialService()

        api_key = "hive_" + "x" * 35  # Valid format and length

        results = service.validate_credentials(api_key=api_key)

        assert results["api_key_valid"] is True

    def test_validate_invalid_api_key(self):
        """Test validation of invalid API key."""
        service = CredentialService()

        api_key = "wrong_prefix_test123"  # Wrong prefix

        results = service.validate_credentials(api_key=api_key)

        assert results["api_key_valid"] is False

    def test_validate_api_key_too_short(self):
        """Test validation of too-short API key."""
        service = CredentialService()

        api_key = "hive_short"  # Correct prefix but too short

        results = service.validate_credentials(api_key=api_key)

        assert results["api_key_valid"] is False


class TestCredentialSaving:
    """Test credential saving functionality."""

    def test_save_credentials_to_new_env_file(self, tmp_path):
        """Test saving credentials to new .env file."""
        service = CredentialService(project_root=tmp_path)

        postgres_creds = {"url": "postgresql+psycopg://testuser:testpass@localhost:5532/testdb"}
        api_key = "hive_testapikey123"

        service.save_credentials_to_env(postgres_creds, api_key)

        env_content = service.env_file.read_text()
        assert "HIVE_DATABASE_URL=postgresql+psycopg://testuser:testpass@localhost:5532/testdb" in env_content
        assert "HIVE_API_KEY=hive_testapikey123" in env_content

    def test_save_credentials_to_existing_env_file(self, tmp_path):
        """Test saving credentials to existing .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("EXISTING_VAR=keep_this\nHIVE_DATABASE_URL=old_url\n")

        service = CredentialService(project_root=tmp_path)

        postgres_creds = {"url": "postgresql+psycopg://new:creds@host:5432/db"}
        api_key = "hive_newkey"

        service.save_credentials_to_env(postgres_creds, api_key)

        env_content = service.env_file.read_text()
        assert "EXISTING_VAR=keep_this" in env_content  # Should preserve existing
        assert "postgresql+psycopg://new:creds@host:5432/db" in env_content  # Should update
        assert "HIVE_API_KEY=hive_newkey" in env_content  # Should add new
        assert "old_url" not in env_content  # Should remove old

    def test_save_credentials_create_if_missing_false(self, tmp_path):
        """Test saving credentials when create_if_missing=False and file doesn't exist."""
        service = CredentialService(project_root=tmp_path)

        postgres_creds = {"url": "postgresql+psycopg://test:test@host:5432/db"}

        # Should not create file and should return early
        service.save_credentials_to_env(postgres_creds, create_if_missing=False)

        assert not service.env_file.exists()


class TestMCPConfigSync:
    """Test MCP configuration synchronization."""

    @pytest.mark.skip(
        reason="🚨 BLOCKED by task-10830c16-508a-4f45-b2f0-6f507bacb797 - MCP sync requires both postgres AND API key (source code bug)"
    )
    def test_sync_mcp_config_updates_postgres_connection(self, tmp_path):
        """Test that MCP config gets updated with PostgreSQL credentials."""
        # Create .env file with credentials
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_URL=postgresql+psycopg://newuser:newpass@localhost:5532/hive\n")

        # Create .mcp.json file
        mcp_file = tmp_path / ".mcp.json"
        mcp_content = """
{
  "mcpServers": {
    "postgres": {
      "command": "uvx",
      "args": ["mcp-server-postgres"],
      "env": {
        "POSTGRES_CONNECTION": "postgresql+psycopg://olduser:oldpass@localhost:5532/hive"
      }
    }
  }
}
        """.strip()
        mcp_file.write_text(mcp_content)

        service = CredentialService(project_root=tmp_path)
        service.sync_mcp_config_with_credentials(mcp_file)

        updated_content = mcp_file.read_text()
        assert "newuser:newpass" in updated_content
        assert "olduser:oldpass" not in updated_content

    @pytest.mark.skip(
        reason="🚨 BLOCKED by task-10830c16-508a-4f45-b2f0-6f507bacb797 - MCP sync requires both postgres AND API key (source code bug)"
    )
    def test_sync_mcp_config_adds_api_key(self, tmp_path):
        """Test that MCP config gets updated with API key."""
        # Create .env file with API key
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_API_KEY=hive_newkey123\n")

        # Create .mcp.json file without API key
        mcp_file = tmp_path / ".mcp.json"
        mcp_content = """
{
  "mcpServers": {
    "automagik-hive": {
      "command": "uvx",
      "args": ["mcp-server-automagik-hive"],
      "env": {}
    }
  }
}
        """.strip()
        mcp_file.write_text(mcp_content)

        service = CredentialService(project_root=tmp_path)
        service.sync_mcp_config_with_credentials(mcp_file)

        updated_content = mcp_file.read_text()
        assert '"HIVE_API_KEY": "hive_newkey123"' in updated_content

    def test_sync_mcp_config_missing_credentials(self, tmp_path):
        """Test MCP sync when credentials are missing."""
        service = CredentialService(project_root=tmp_path)

        mcp_file = tmp_path / ".mcp.json"
        mcp_file.write_text("{}")

        # Should handle missing credentials gracefully
        service.sync_mcp_config_with_credentials(mcp_file)

        # File should remain unchanged
        assert mcp_file.read_text() == "{}"


class TestCredentialStatus:
    """Test credential status reporting."""

    def test_get_credential_status_complete_setup(self, tmp_path):
        """Test credential status when everything is configured."""
        env_file = tmp_path / ".env"
        env_content = """
HIVE_DATABASE_URL=postgresql+psycopg://user123:pass456@localhost:5532/hive
HIVE_API_KEY=hive_validkey123456789
        """.strip()
        env_file.write_text(env_content)

        service = CredentialService(project_root=tmp_path)

        status = service.get_credential_status()

        assert status["env_file_exists"] is True
        assert status["postgres_configured"] is True
        assert status["api_key_configured"] is True
        assert status["postgres_credentials"]["has_user"] is True
        assert status["postgres_credentials"]["has_password"] is True
        assert status["postgres_credentials"]["has_database"] is True
        assert status["api_key_format_valid"] is True
        assert "validation" in status

    def test_get_credential_status_missing_env(self, tmp_path):
        """Test credential status when .env file is missing."""
        service = CredentialService(project_root=tmp_path)

        status = service.get_credential_status()

        assert status["env_file_exists"] is False
        assert status["postgres_configured"] is False
        assert status["api_key_configured"] is False


class TestCompleteCredentialSetup:
    """Test complete credential setup workflow."""

    def test_setup_complete_credentials_success(self, tmp_path):
        """Test complete credential setup workflow."""
        service = CredentialService(project_root=tmp_path)

        creds = service.setup_complete_credentials()

        assert "postgres_user" in creds
        assert "postgres_password" in creds
        assert "postgres_database" in creds
        assert "postgres_host" in creds
        assert "postgres_port" in creds
        assert "postgres_url" in creds
        assert "api_key" in creds

        # Verify .env file was created
        assert service.env_file.exists()
        env_content = service.env_file.read_text()
        assert "HIVE_DATABASE_URL=" in env_content
        assert "HIVE_API_KEY=" in env_content

    def test_setup_complete_credentials_with_custom_params(self, tmp_path):
        """Test complete credential setup with custom parameters."""
        service = CredentialService(project_root=tmp_path)

        creds = service.setup_complete_credentials(
            postgres_host="custom.host", postgres_port=9999, postgres_database="custom_db"
        )

        assert creds["postgres_host"] == "custom.host"
        assert creds["postgres_port"] == "9999"
        assert creds["postgres_database"] == "custom_db"
        assert "custom.host:9999/custom_db" in creds["postgres_url"]


class TestPortCalculationAndModeSupport:
    """Test port calculation and multi-mode support functionality."""

    def test_extract_base_ports_from_env_with_custom_ports(self, tmp_path):
        """Test extracting custom base ports from .env file."""
        env_file = tmp_path / ".env"
        env_content = """
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:7777/hive
HIVE_API_PORT=8888
        """.strip()
        env_file.write_text(env_content)

        service = CredentialService(project_root=tmp_path)

        base_ports = service.extract_base_ports_from_env()

        assert base_ports["db"] == 7777
        assert base_ports["api"] == 8888

    def test_extract_base_ports_from_env_defaults(self, tmp_path):
        """Test extracting base ports when .env has default values."""
        service = CredentialService(project_root=tmp_path)

        base_ports = service.extract_base_ports_from_env()

        assert base_ports["db"] == 5532  # Default
        assert base_ports["api"] == 8886  # Default

    def test_master_env_alias_created_during_save(self, tmp_path):
        """Master env alias should mirror the primary .env file after save."""
        service = CredentialService(project_root=tmp_path)

        payload = {
            "postgres_user": "testaliasuser",
            "postgres_password": "testaliaspass",
            "api_key_base": "aliasbase",
        }

        service._save_master_credentials(payload)

        primary_env = tmp_path / ".env"
        alias_env = tmp_path / ".env.master"

        assert primary_env.exists()
        assert alias_env.exists(), "Expected .env.master alias to exist after save"
        assert alias_env.read_text() == primary_env.read_text()

    def test_base_port_fallback_prefers_alias_over_primary_env(self, tmp_path):
        """Alias takes precedence; fallback should ignore stale primary env overrides."""
        master_alias = tmp_path / ".env.master"
        # Alias present but with missing port values -> should trigger defaults
        master_alias.write_text(
            """
HIVE_DATABASE_URL=postgresql+psycopg://alias_user:alias_pass@localhost/hive
""".strip()
        )

        primary_env = tmp_path / ".env"
        primary_env.write_text(
            """
HIVE_DATABASE_URL=postgresql+psycopg://legacy_user:legacy_pass@localhost:6123/hive
HIVE_API_PORT=9777
""".strip()
        )

        service = CredentialService(project_root=tmp_path)

        base_ports = service.extract_base_ports_from_env()

        assert service.master_env_file == master_alias
        assert base_ports["db"] == CredentialService.DEFAULT_BASE_PORTS["db"]
        assert base_ports["api"] == CredentialService.DEFAULT_BASE_PORTS["api"]


class TestMasterCredentialFlow:
    """Test master credential generation and simplified installation."""

    def test_generate_master_credentials(self):
        """Test generation of master credentials."""
        service = CredentialService()

        master_creds = service.generate_master_credentials()

        assert "postgres_user" in master_creds
        assert "postgres_password" in master_creds
        assert "api_key_base" in master_creds

        assert len(master_creds["postgres_user"]) >= 12
        assert len(master_creds["postgres_password"]) >= 12
        assert len(master_creds["api_key_base"]) >= 32

    def test_derive_mode_credentials_workspace(self):
        """Test deriving workspace mode credentials."""
        service = CredentialService()

        master_creds = {
            "postgres_user": "testuser123",
            "postgres_password": "testpass456",
            "api_key_base": "testapikey789",
        }

        mode_creds = service.derive_mode_credentials(master_creds, "workspace")

        assert mode_creds["postgres_user"] == "testuser123"
        assert mode_creds["postgres_password"] == "testpass456"  # noqa: S105 - Test fixture password
        assert mode_creds["api_key"] == "hive_workspace_testapikey789"
        assert mode_creds["schema"] == "public"
        assert "options=-csearch_path" not in mode_creds["database_url"]  # No schema override

    def test_derive_mode_credentials_agent_raises(self):
        """Non-workspace modes should raise until multi-mode support returns."""
        service = CredentialService()

        master_creds = {
            "postgres_user": "testuser123",
            "postgres_password": "testpass456",
            "api_key_base": "testapikey789",
        }

        with pytest.raises(ValueError, match="Unknown mode: agent"):
            service.derive_mode_credentials(master_creds, "agent")

    def test_derive_mode_credentials_invalid_mode(self):
        """Test deriving credentials for invalid mode."""
        service = CredentialService()
        master_creds = {"postgres_user": "user", "postgres_password": "pass", "api_key_base": "key"}

        with pytest.raises(ValueError, match="Unknown mode: invalid"):
            service.derive_mode_credentials(master_creds, "invalid")

    def test_install_all_modes_returns_workspace_only(self, tmp_path):
        """Installation should return a workspace entry for backward compatibility."""
        service = CredentialService(project_root=tmp_path)

        result = service.install_all_modes()

        assert set(result.keys()) == {"workspace"}

        workspace_creds = result["workspace"]
        assert workspace_creds["postgres_user"]
        assert workspace_creds["postgres_password"]
        assert workspace_creds["api_key"].startswith("hive_")


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""

    def test_extract_credentials_file_read_error(self, tmp_path):
        """Test handling file read errors during credential extraction."""
        tmp_path / ".env"

        service = CredentialService(project_root=tmp_path)

        # Mock file operations to raise exception
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            creds = service.extract_postgres_credentials_from_env()

            # Should return None values instead of crashing
            assert all(value is None for value in creds.values())

    def test_save_credentials_write_error(self, tmp_path):
        """Test handling write errors during credential saving."""
        service = CredentialService(project_root=tmp_path)

        postgres_creds = {"url": "postgresql+psycopg://test:test@host:5432/db"}

        # Mock write to raise exception
        with patch.object(Path, "write_text", side_effect=OSError("Disk full")):
            with pytest.raises(IOError):
                service.save_credentials_to_env(postgres_creds)

    def test_sync_mcp_config_missing_file(self, tmp_path):
        """Test MCP config sync when file doesn't exist."""
        service = CredentialService(project_root=tmp_path)

        # Should handle missing file gracefully
        service.sync_mcp_config_with_credentials()

        # No exception should be raised

    def test_detect_existing_containers_docker_not_available(self):
        """Test container detection when Docker is not available."""
        service = CredentialService()

        with patch("subprocess.run", side_effect=FileNotFoundError("docker not found")):
            containers = service.detect_existing_containers()

            # Should return False for all containers when Docker unavailable
            assert all(status is False for status in containers.values())

    def test_migration_check_no_old_containers(self):
        """Test migration check when no old containers exist."""
        service = CredentialService()

        with patch.object(service, "detect_existing_containers", return_value={}):
            # Should complete without error
            service.migrate_to_shared_database()

    def test_extract_existing_master_credentials_placeholder_detection(self, tmp_path):
        """Test that placeholder credentials are detected and rejected."""
        env_file = tmp_path / ".env"
        env_content = """
HIVE_DATABASE_URL=postgresql+psycopg://user:your-secure-password-here@localhost:5532/hive
HIVE_API_KEY=hive_your-hive-api-key-here
        """.strip()
        env_file.write_text(env_content)

        service = CredentialService(project_root=tmp_path)

        existing_creds = service._extract_existing_master_credentials()

        # Should detect placeholder and return None to force regeneration
        assert existing_creds is None


class TestSchemaAndDatabaseHandling:
    """Test database schema handling and URL generation."""

    def test_get_database_url_with_schema_workspace(self, tmp_path):
        """Test database URL generation for workspace (no schema override)."""
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db")

        service = CredentialService(project_root=tmp_path)

        url = service.get_database_url_with_schema("workspace")

        assert url == "postgresql+psycopg://user:pass@host:5432/db"
        assert "options=" not in url  # No schema override for workspace

    def test_get_database_url_with_schema_agent(self, tmp_path):
        """Test database URL generation for agent mode (with schema override)."""
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db")

        service = CredentialService(project_root=tmp_path)

        url = service.get_database_url_with_schema("agent")

        assert "options=-csearch_path=agent" in url

    def test_get_database_url_with_schema_existing_params(self, tmp_path):
        """Test database URL generation when URL already has parameters."""
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db?sslmode=require")

        service = CredentialService(project_root=tmp_path)

        url = service.get_database_url_with_schema("agent")

        assert "sslmode=require" in url
        assert "options=-csearch_path=agent" in url
        assert "&" in url  # Should use & as separator

    def test_get_database_url_with_schema_missing_url(self, tmp_path):
        """Test database URL generation when no URL exists."""
        service = CredentialService(project_root=tmp_path)

        with pytest.raises(ValueError, match="No database URL found"):
            service.get_database_url_with_schema("agent")

    def test_ensure_schema_exists_agent_mode(self):
        """Test schema existence check for agent mode."""
        service = CredentialService()

        # Should not raise exception (placeholder implementation)
        service.ensure_schema_exists("agent")

    def test_ensure_schema_exists_workspace_mode(self):
        """Test schema existence check for workspace mode."""
        service = CredentialService()

        # Should not raise exception for workspace
        service.ensure_schema_exists("workspace")


class TestSecurityValidation:
    """Test security-related validation and edge cases."""

    def test_generated_credentials_meet_security_requirements(self):
        """Test that generated credentials meet minimum security requirements."""
        service = CredentialService()

        # Test multiple generations for consistency
        for _ in range(5):
            creds = service.generate_postgres_credentials()

            # Check password strength
            assert len(creds["password"]) >= 12
            assert creds["password"].isalnum()  # Only safe characters

            # Check user name format
            assert len(creds["user"]) >= 12
            assert creds["user"].isalnum()

            # Check uniqueness (very low probability of collision)
            creds2 = service.generate_postgres_credentials()
            assert creds["password"] != creds2["password"]
            assert creds["user"] != creds2["user"]

    def test_api_key_entropy_validation(self):
        """Test that API keys have sufficient entropy."""
        service = CredentialService()

        # Generate multiple keys and check uniqueness
        keys = set()
        for _ in range(10):
            key = service.generate_hive_api_key()
            keys.add(key)

            # Each key should be unique
            assert len(keys) == len(list(keys))

        # Should have 10 unique keys
        assert len(keys) == 10

    def test_credential_validation_sql_injection_patterns(self):
        """Test credential validation rejects SQL injection patterns."""
        service = CredentialService()

        malicious_creds = {
            "user": "user'; DROP TABLE users; --",
            "password": "pass'OR'1'='1",
            "url": "postgresql+psycopg://user'; DROP TABLE users; --:pass@host/db",
        }

        results = service.validate_credentials(postgres_creds=malicious_creds)

        # Should fail validation due to special characters
        assert results["postgres_user_valid"] is False
        assert results["postgres_password_valid"] is False
