"""
FINAL COVERAGE TEST SUITE for CredentialService

This test suite targets the remaining 9 uncovered lines to achieve maximum coverage.
Focus: Execute the last edge cases that weren't covered by previous test suites.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from lib.auth.credential_service import CredentialService


class TestFinalCoverageTargeting:
    """Target the last 9 uncovered lines for maximum coverage."""
    
    def test_save_credentials_api_key_update_execution(self, tmp_path):
        """EXECUTE API key update path in save_credentials_to_env - lines 332-334."""
        service = CredentialService(project_root=tmp_path)
        
        # Create .env file with existing API key
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_API_KEY=old_key\nOTHER_VAR=value\n")
        
        # EXECUTE save with new API key to trigger update path - lines 332-334
        service.save_credentials_to_env(api_key="new_api_key")
        
        # Verify API key was updated, not appended
        content = env_file.read_text()
        assert "HIVE_API_KEY=new_api_key" in content
        assert "old_key" not in content
        assert content.count("HIVE_API_KEY") == 1  # Should only have one instance
        
    def test_install_all_modes_reuse_existing_credentials_execution(self, tmp_path):
        """EXECUTE existing credential reuse path - lines 856-857."""
        # Create .env with valid existing credentials (not placeholders)
        env_file = tmp_path / ".env"
        env_file.write_text(
            "HIVE_DATABASE_URL=postgresql+psycopg://existinguser:validpass123@localhost:5532/hive\n"
            "HIVE_API_KEY=hive_existingvalidkey456789\n"
        )
        
        service = CredentialService(project_root=tmp_path)
        
        # EXECUTE install_all_modes without force_regenerate - lines 856-857
        result = service.install_all_modes(force_regenerate=False)
        
        # Should reuse existing credentials
        assert "workspace" in result
        
        # Verify the original credentials were reused
        updated_content = env_file.read_text()
        assert "existinguser" in updated_content
        assert "validpass123" in updated_content
        
    def test_extract_master_credentials_api_key_placeholder_detection_execution(self, tmp_path):
        """EXECUTE API key placeholder detection - lines 937-938."""
        # Create .env with postgres URL and placeholder API key
        env_file = tmp_path / ".env"
        env_file.write_text(
            "HIVE_DATABASE_URL=postgresql+psycopg://validuser:validpass@localhost:5532/hive\n"
            "HIVE_API_KEY=hive_your-hive-api-key-here\n"
        )
        
        service = CredentialService(project_root=tmp_path)
        
        # EXECUTE extraction - should detect API key placeholder and return None
        existing_creds = service._extract_existing_master_credentials()
        
        # Should return None due to placeholder API key detection - lines 937-938
        assert existing_creds is None
        
    def test_save_master_credentials_with_env_example_execution(self, tmp_path):
        """EXECUTE master credential saving with .env.example - lines 959-960."""
        service = CredentialService(project_root=tmp_path)
        
        # Create .env.example file
        env_example = tmp_path / ".env.example"
        env_example_content = """# Example configuration
HIVE_ENVIRONMENT=development
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive
HIVE_API_KEY=hive_example_key
# Other example variables
EXAMPLE_VAR=example_value"""
        env_example.write_text(env_example_content)
        
        master_credentials = {
            "postgres_user": "newuser123",
            "postgres_password": "newpass456", 
            "api_key_base": "newkey789"
        }
        
        # EXECUTE _save_master_credentials with .env.example present - lines 959-960
        service._save_master_credentials(master_credentials)
        
        # Verify .env was created from .env.example template
        env_content = service.master_env_file.read_text()
        assert "HIVE_ENVIRONMENT=development" in env_content  # From template
        assert "EXAMPLE_VAR=example_value" in env_content  # From template
        assert "newuser123" in env_content  # Updated with actual credentials
        assert "newpass456" in env_content


class TestEdgeCaseCredentialHandling:
    """Test additional edge cases for comprehensive coverage."""
    
    def test_postgres_credential_update_with_existing_entry(self, tmp_path):
        """Test postgres credential update when entry already exists."""
        service = CredentialService(project_root=tmp_path)
        
        # Create .env file with existing postgres URL
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_URL=old_postgres_url\nOTHER_VAR=value\n")
        
        postgres_creds = {
            "url": "postgresql+psycopg://newuser:newpass@localhost:5532/newdb"
        }
        
        # EXECUTE save to trigger postgres update path
        service.save_credentials_to_env(postgres_creds)
        
        # Verify postgres URL was updated, not appended
        content = env_file.read_text()
        assert "postgresql+psycopg://newuser:newpass@localhost:5532/newdb" in content
        assert "old_postgres_url" not in content
        assert content.count("HIVE_DATABASE_URL") == 1  # Should only have one instance
        
    def test_complex_installation_workflow_execution(self, tmp_path):
        """Test complete installation workflow with various edge cases."""
        service = CredentialService(project_root=tmp_path)
        
        # Test install all modes with custom modes list
        result = service.install_all_modes(modes=["workspace", "agent"])
        
        # Verify only requested modes were processed
        assert "workspace" in result
        assert "agent" in result
        assert "genie" not in result
        
        # Verify environment files were created appropriately
        main_env = tmp_path / ".env"
        agent_env = tmp_path / ".env.agent"
        genie_env = tmp_path / ".env.genie"
        
        assert main_env.exists()  # Workspace uses main .env
        assert agent_env.exists()  # Agent gets its own .env file
        assert not genie_env.exists()  # Genie wasn't requested
        
    def test_mcp_sync_with_complex_json_structure(self, tmp_path):
        """Test MCP sync with complex JSON structure and edge cases."""
        # Create .env with credentials
        env_file = tmp_path / ".env"
        env_file.write_text(
            "HIVE_DATABASE_URL=postgresql+psycopg://complexuser:complexpass@localhost:5532/hive\n"
            "HIVE_API_KEY=hive_complexkey123456\n"
        )
        
        # Create complex .mcp.json structure
        mcp_file = tmp_path / ".mcp.json"
        complex_mcp_content = {
            "mcpServers": {
                "postgres": {
                    "command": "uvx",
                    "args": ["mcp-server-postgres"],
                    "env": {
                        "POSTGRES_CONNECTION": "postgresql+psycopg://olduser:oldpass@localhost:5532/hive",
                        "OTHER_ENV": "other_value"
                    }
                },
                "automagik-hive": {
                    "command": "uvx", 
                    "args": ["mcp-server-automagik-hive"],
                    "env": {
                        "EXISTING_VAR": "existing_value"
                    }
                }
            }
        }
        mcp_file.write_text(json.dumps(complex_mcp_content, indent=2))
        
        service = CredentialService(project_root=tmp_path)
        
        # EXECUTE complex MCP sync
        service.sync_mcp_config_with_credentials(mcp_file)
        
        # Verify both postgres and API key were updated
        updated_content = mcp_file.read_text()
        assert "complexuser:complexpass" in updated_content
        assert "hive_complexkey123456" in updated_content
        assert "olduser:oldpass" not in updated_content
        assert "OTHER_ENV" in updated_content  # Should preserve other env vars
        
    def test_port_calculation_with_extreme_values(self):
        """Test port calculation with extreme base port values."""
        service = CredentialService()
        
        # Test with very high base ports
        extreme_base_ports = {"db": 65000, "api": 64000}
        
        # Test agent mode with extreme values
        agent_ports = service.calculate_ports("agent", extreme_base_ports)
        assert agent_ports["db"] == 365000  # 3 + 65000
        assert agent_ports["api"] == 364000  # 3 + 64000
        
        # Test genie mode with extreme values
        genie_ports = service.calculate_ports("genie", extreme_base_ports)
        assert genie_ports["db"] == 465000  # 4 + 65000 
        assert genie_ports["api"] == 464000  # 4 + 64000
        
    def test_credential_validation_comprehensive_edge_cases(self):
        """Test comprehensive credential validation edge cases."""
        service = CredentialService()
        
        # Test validation with mixed valid/invalid credentials
        mixed_postgres_creds = {
            "user": "validuser123456",  # Valid: long enough and alphanumeric
            "password": "short",  # Invalid: too short
            "url": "postgresql+psycopg://valid:url@host:5432/db"  # Valid
        }
        
        results = service.validate_credentials(postgres_creds=mixed_postgres_creds)
        
        assert results["postgres_user_valid"] is True
        assert results["postgres_password_valid"] is False
        assert results["postgres_url_valid"] is True
        
        # Test validation with edge case API key length
        edge_api_key = "hive_" + "x" * 37  # Exactly at minimum length
        results_api = service.validate_credentials(api_key=edge_api_key)
        assert results_api["api_key_valid"] is True
        
    def test_schema_handling_comprehensive_scenarios(self, tmp_path):
        """Test comprehensive schema handling scenarios."""
        # Create .env with complex database URL
        env_file = tmp_path / ".env"
        complex_db_url = "postgresql+psycopg://user:pass@host:5432/db?sslmode=require&connect_timeout=10"
        env_file.write_text(f"HIVE_DATABASE_URL={complex_db_url}\n")
        
        service = CredentialService(project_root=tmp_path)
        
        # Test URL generation for different modes with existing parameters
        workspace_url = service.get_database_url_with_schema("workspace")
        assert workspace_url == complex_db_url  # No schema modification
        
        agent_url = service.get_database_url_with_schema("agent") 
        assert "options=-csearch_path=agent" in agent_url
        assert "sslmode=require" in agent_url  # Original params preserved
        assert "&" in agent_url  # Proper parameter separator
        
        genie_url = service.get_database_url_with_schema("genie")
        assert "options=-csearch_path=genie" in genie_url
        assert "connect_timeout=10" in genie_url  # All original params preserved