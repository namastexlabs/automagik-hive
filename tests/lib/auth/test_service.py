#!/usr/bin/env python3
"""Tests for CredentialService enhancements."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from lib.auth.credential_service import CredentialService


class TestCredentialServiceEnhancements:
    """Test enhanced CredentialService with dynamic base ports."""

    def test_extract_base_ports_from_env_defaults(self, tmp_path):
        """Test extraction of base ports returns defaults when .env doesn't exist."""
        # Create service with non-existent env file
        service = CredentialService(project_root=tmp_path)
        
        base_ports = service.extract_base_ports_from_env()
        
        assert base_ports == {"db": 5532, "api": 8886}

    def test_extract_base_ports_from_env_custom(self, tmp_path):
        """Test extraction of base ports from existing .env file."""
        # Create .env with custom ports
        env_file = tmp_path / ".env"
        env_file.write_text("""
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5433/hive
HIVE_API_PORT=8887
""")
        
        service = CredentialService(project_root=tmp_path)
        
        base_ports = service.extract_base_ports_from_env()
        
        assert base_ports == {"db": 5433, "api": 8887}

    def test_extract_base_ports_from_env_partial(self, tmp_path):
        """Test extraction with only partial port configuration."""
        # Create .env with only database port
        env_file = tmp_path / ".env"
        env_file.write_text("""
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5433/hive
# No API port specified
""")
        
        service = CredentialService(project_root=tmp_path)
        
        base_ports = service.extract_base_ports_from_env()
        
        # Should return custom db port and default api port
        assert base_ports == {"db": 5433, "api": 8886}

    def test_calculate_ports_workspace(self):
        """Test port calculation for workspace mode."""
        service = CredentialService()
        base_ports = {"db": 5532, "api": 8886}
        
        calculated = service.calculate_ports("workspace", base_ports)
        
        # Workspace has no prefix
        assert calculated == {"db": 5532, "api": 8886}

    def test_calculate_ports_agent(self):
        """Test port calculation for agent mode."""
        service = CredentialService()
        base_ports = {"db": 5532, "api": 8886}
        
        calculated = service.calculate_ports("agent", base_ports)
        
        # Agent uses prefixed database port and prefixed API port
        assert calculated == {"db": 35532, "api": 38886}

    def test_calculate_ports_genie(self):
        """Test port calculation for genie mode."""
        service = CredentialService()
        base_ports = {"db": 5532, "api": 8886}
        
        calculated = service.calculate_ports("genie", base_ports)
        
        # Genie uses prefixed database port and prefixed API port
        assert calculated == {"db": 45532, "api": 48886}

    def test_get_deployment_ports_dynamic(self, tmp_path):
        """Test that deployment ports are calculated dynamically from .env."""
        # Create .env with custom base ports
        env_file = tmp_path / ".env"
        env_file.write_text("""
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:6000/hive
HIVE_API_PORT=9000
""")
        
        service = CredentialService(project_root=tmp_path)
        
        deployment_ports = service.get_deployment_ports()
        
        expected = {
            "workspace": {"db": 6000, "api": 9000},
            "agent": {"db": 36000, "api": 39000},
            "genie": {"db": 46000, "api": 49000}
        }
        
        assert deployment_ports == expected

    def test_invalid_mode_raises_error(self):
        """Test that invalid mode raises ValueError."""
        service = CredentialService()
        base_ports = {"db": 5532, "api": 8886}
        
        with pytest.raises(ValueError, match="Unknown mode: invalid"):
            service.calculate_ports("invalid", base_ports)

    def test_save_master_credentials_uses_env_example(self, tmp_path):
        """Test that _save_master_credentials copies from .env.example when available."""
        # Create .env.example with comprehensive config
        env_example = tmp_path / ".env.example"
        env_example.write_text("""# Comprehensive config template
HIVE_ENVIRONMENT=development
HIVE_LOG_LEVEL=INFO
HIVE_API_HOST=0.0.0.0
HIVE_API_PORT=8886
HIVE_DATABASE_URL=postgresql+psycopg://template-user:template-pass@localhost:5532/hive
HIVE_API_KEY=template-api-key
ANTHROPIC_API_KEY=your-anthropic-key-here
OPENAI_API_KEY=your-openai-key-here
HIVE_ENABLE_METRICS=true
""")
        
        service = CredentialService(project_root=tmp_path)
        
        # Mock master credentials
        master_creds = {
            "postgres_user": "test_user",
            "postgres_password": "test_pass", 
            "api_key_base": "test_base_key"
        }
        
        # Call the method
        service._save_master_credentials(master_creds)
        
        # Check that .env was created
        env_file = tmp_path / ".env"
        assert env_file.exists()
        
        env_content = env_file.read_text()
        
        # Should have copied comprehensive config from .env.example
        assert "HIVE_ENVIRONMENT=development" in env_content
        assert "HIVE_LOG_LEVEL=INFO" in env_content
        assert "ANTHROPIC_API_KEY=your-anthropic-key-here" in env_content
        assert "OPENAI_API_KEY=your-openai-key-here" in env_content
        assert "HIVE_ENABLE_METRICS=true" in env_content
        
        # Should have updated the credentials with real values
        assert "HIVE_DATABASE_URL=postgresql+psycopg://test_user:test_pass@localhost:5532/hive" in env_content
        assert "HIVE_API_KEY=hive_test_base_key" in env_content
        
        # Template values should be replaced
        assert "template-user" not in env_content
        assert "template-api-key" not in env_content

    def test_save_master_credentials_fallback_without_example(self, tmp_path):
        """Test that _save_master_credentials falls back to minimal template when .env.example doesn't exist."""
        # Don't create .env.example
        service = CredentialService(project_root=tmp_path)
        
        # Mock master credentials
        master_creds = {
            "postgres_user": "test_user",
            "postgres_password": "test_pass",
            "api_key_base": "test_base_key"
        }
        
        # Call the method
        service._save_master_credentials(master_creds)
        
        # Check that .env was created with minimal template
        env_file = tmp_path / ".env"
        assert env_file.exists()
        
        env_content = env_file.read_text()
        
        # Should have minimal configuration
        assert "HIVE_ENVIRONMENT=development" in env_content
        assert "HIVE_LOG_LEVEL=INFO" in env_content
        
        # Should have updated credentials
        assert "HIVE_DATABASE_URL=postgresql+psycopg://test_user:test_pass@localhost:5532/hive" in env_content
        assert "HIVE_API_KEY=hive_test_base_key" in env_content

    def test_extract_existing_master_credentials_rejects_placeholders(self, tmp_path):
        """Test that _extract_existing_master_credentials rejects placeholder passwords."""
        # Create .env with placeholder credentials
        env_file = tmp_path / ".env"
        env_file.write_text("""
HIVE_DATABASE_URL=postgresql+psycopg://hive_user:your-secure-password-here@localhost:5532/hive
HIVE_API_KEY=hive_real_api_key_base
""")
        
        service = CredentialService(project_root=tmp_path)
        
        # Should return None because password is a placeholder
        credentials = service._extract_existing_master_credentials()
        
        assert credentials is None

    def test_extract_existing_master_credentials_rejects_placeholder_api_key(self, tmp_path):
        """Test that _extract_existing_master_credentials rejects placeholder API keys."""
        # Create .env with placeholder API key
        env_file = tmp_path / ".env"
        env_file.write_text("""
HIVE_DATABASE_URL=postgresql+psycopg://hive_user:real_secure_password@localhost:5532/hive
HIVE_API_KEY=hive_your-hive-api-key-here
""")
        
        service = CredentialService(project_root=tmp_path)
        
        # Should return None because API key is a placeholder
        credentials = service._extract_existing_master_credentials()
        
        assert credentials is None

    def test_extract_existing_master_credentials_accepts_valid_credentials(self, tmp_path):
        """Test that _extract_existing_master_credentials accepts valid non-placeholder credentials."""
        # Create .env with valid credentials
        env_file = tmp_path / ".env"
        env_file.write_text("""
HIVE_DATABASE_URL=postgresql+psycopg://hive_user:real_secure_password123@localhost:5532/hive
HIVE_API_KEY=hive_AFtzRGH5r01t2l291d4sivlizsd6EgYcfpUAW57te-I
""")
        
        service = CredentialService(project_root=tmp_path)
        
        # Should return valid credentials
        credentials = service._extract_existing_master_credentials()
        
        assert credentials is not None
        assert credentials["postgres_user"] == "hive_user"
        assert credentials["postgres_password"] == "real_secure_password123"
        assert credentials["api_key_base"] == "AFtzRGH5r01t2l291d4sivlizsd6EgYcfpUAW57te-I"

    def test_extract_existing_master_credentials_detects_various_placeholders(self, tmp_path):
        """Test that _extract_existing_master_credentials detects various placeholder patterns."""
        placeholder_passwords = [
            "your-secure-password-here",
            "your-password", 
            "change-me",
            "placeholder",
            "example",
            "template",
            "replace-this"
        ]
        
        for placeholder in placeholder_passwords:
            env_file = tmp_path / ".env"
            env_file.write_text(f"""
HIVE_DATABASE_URL=postgresql+psycopg://hive_user:{placeholder}@localhost:5532/hive
HIVE_API_KEY=hive_real_api_key_base
""")
            
            service = CredentialService(project_root=tmp_path)
            
            # Should return None for each placeholder pattern
            credentials = service._extract_existing_master_credentials()
            
            assert credentials is None, f"Placeholder '{placeholder}' was not detected"