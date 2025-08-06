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
        
        # Agent has prefix "3"
        assert calculated == {"db": 35532, "api": 38886}

    def test_calculate_ports_genie(self):
        """Test port calculation for genie mode."""
        service = CredentialService()
        base_ports = {"db": 5532, "api": 8886}
        
        calculated = service.calculate_ports("genie", base_ports)
        
        # Genie has prefix "4"  
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