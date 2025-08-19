#!/usr/bin/env python3
"""
Tests for CleanCredentialService - Read-only credential validation service.

ARCHITECTURAL PRINCIPLE: Tests validate that the credential service NEVER writes
environment variables, only validates and reads them.

This replaces the massive credential_service.py that inappropriately generated
.env files with a clean service that respects the architecture rule:
".env > docker compose yaml specific overrides, and THATS IT"
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from lib.auth.credential_service_clean import CleanCredentialService
from lib.config.settings import HiveSettings


class TestCleanCredentialService:
    """Test the clean credential service that only validates, never writes."""
    
    def setup_method(self):
        """Setup test environment."""
        self.project_root = Path("/test/project")
        self.service = CleanCredentialService(project_root=self.project_root)
    
    def test_initialization(self):
        """Test service initializes with project root."""
        assert self.service.project_root == self.project_root
        assert self.service.env_file_path == self.project_root / ".env"
    
    def test_initialization_with_custom_env_path(self):
        """Test service initializes with custom env file path."""
        custom_env = Path("/test/custom/.env")
        service = CleanCredentialService(project_root=self.project_root, env_file=custom_env)
        assert service.env_file_path == custom_env
        assert service.project_root == self.project_root
    
    def test_validate_env_file_exists_success(self):
        """Test validation passes when .env file exists."""
        with patch('pathlib.Path.exists', return_value=True):
            result = self.service.validate_env_file_exists()
            assert result is True
    
    def test_validate_env_file_exists_failure(self):
        """Test validation fails when .env file missing."""
        with patch('pathlib.Path.exists', return_value=False):
            result = self.service.validate_env_file_exists()
            assert result is False
    
    def test_validate_database_credentials_with_valid_settings(self):
        """Test database credential validation with valid Pydantic settings."""
        mock_settings = Mock(spec=HiveSettings)
        mock_settings.hive_database_url = "postgresql+psycopg://user:pass@localhost:5532/hive"
        
        with patch('lib.auth.credential_service_clean.get_settings', return_value=mock_settings):
            result = self.service.validate_database_credentials()
            
        assert result['valid'] is True
        assert result['database_url'] == mock_settings.hive_database_url
        assert 'error' not in result
    
    def test_validate_database_credentials_with_invalid_url(self):
        """Test database credential validation with invalid URL format."""
        mock_settings = Mock(spec=HiveSettings)
        mock_settings.hive_database_url = "invalid://url"
        
        with patch('lib.auth.credential_service_clean.get_settings', return_value=mock_settings):
            result = self.service.validate_database_credentials()
            
        assert result['valid'] is False
        assert 'error' in result
        assert 'Invalid database URL format' in result['error']
    
    def test_validate_api_credentials_with_valid_settings(self):
        """Test API credential validation with valid Pydantic settings."""
        mock_settings = Mock(spec=HiveSettings)
        mock_settings.hive_api_key = "hive_test_key_12345678901234567890123456"
        mock_settings.hive_api_port = 8886
        mock_settings.hive_api_host = "0.0.0.0"  # Add missing attribute
        
        with patch('lib.auth.credential_service_clean.get_settings', return_value=mock_settings):
            result = self.service.validate_api_credentials()
            
        assert result['valid'] is True
        assert result['api_key'] == mock_settings.hive_api_key
        assert result['api_port'] == mock_settings.hive_api_port
        assert 'error' not in result
    
    def test_validate_api_credentials_with_invalid_key_format(self):
        """Test API credential validation with invalid key format."""
        mock_settings = Mock(spec=HiveSettings)
        mock_settings.hive_api_key = "invalid_key"  # Doesn't start with 'hive_'
        mock_settings.hive_api_port = 8886
        
        with patch('lib.auth.credential_service_clean.get_settings', return_value=mock_settings):
            result = self.service.validate_api_credentials()
            
        assert result['valid'] is False
        assert 'error' in result
        assert 'API key format invalid' in result['error']
    
    def test_validate_api_credentials_with_invalid_port(self):
        """Test API credential validation with invalid port."""
        mock_settings = Mock(spec=HiveSettings)
        mock_settings.hive_api_key = "hive_test_key_12345678901234567890123456"
        mock_settings.hive_api_port = 99999  # Out of valid range
        
        with patch('lib.auth.credential_service_clean.get_settings', return_value=mock_settings):
            result = self.service.validate_api_credentials()
            
        assert result['valid'] is False
        assert 'error' in result
        assert 'API port out of valid range' in result['error']
    
    def test_validate_all_credentials_success(self):
        """Test complete credential validation with all valid credentials."""
        mock_settings = Mock(spec=HiveSettings)
        mock_settings.hive_database_url = "postgresql+psycopg://user:pass@localhost:5532/hive"
        mock_settings.hive_api_key = "hive_test_key_12345678901234567890123456"
        mock_settings.hive_api_port = 8886
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('lib.config.settings.get_settings', return_value=mock_settings):
            
            result = self.service.validate_all_credentials()
            
        assert result['valid'] is True
        assert result['env_file_exists'] is True
        assert result['database']['valid'] is True
        assert result['api']['valid'] is True
        assert 'errors' not in result
    
    def test_validate_all_credentials_failure(self):
        """Test complete credential validation with missing env file."""
        with patch('pathlib.Path.exists', return_value=False):
            result = self.service.validate_all_credentials()
            
        assert result['valid'] is False
        assert result['env_file_exists'] is False
        assert 'errors' in result
        assert len(result['errors']) > 0
    
    def test_get_connection_info_success(self):
        """Test connection info extraction from valid settings."""
        mock_settings = Mock(spec=HiveSettings)
        mock_settings.hive_database_url = "postgresql+psycopg://testuser:testpass@localhost:5532/testdb"
        mock_settings.hive_api_port = 8886
        mock_settings.hive_api_host = "0.0.0.0"
        
        with patch('lib.auth.credential_service_clean.get_settings', return_value=mock_settings):
            result = self.service.get_connection_info()
            
        assert result['database']['host'] == 'localhost'
        assert result['database']['port'] == 5532
        assert result['database']['user'] == 'testuser'
        assert result['database']['database'] == 'testdb'
        # Password should not be exposed in connection info
        assert 'password' not in result['database']
        
        assert result['api']['host'] == "0.0.0.0"
        assert result['api']['port'] == 8886
    
    def test_get_connection_info_with_invalid_database_url(self):
        """Test connection info extraction with invalid database URL."""
        mock_settings = Mock(spec=HiveSettings)
        mock_settings.hive_database_url = "invalid://url"
        mock_settings.hive_api_port = 8886
        mock_settings.hive_api_host = "0.0.0.0"
        
        with patch('lib.auth.credential_service_clean.get_settings', return_value=mock_settings):
            result = self.service.get_connection_info()
            
        # Invalid URL should still parse, but may have None values
        assert 'database' in result
        assert result['database']['host'] == 'url'  # The netloc part
        assert result['database']['port'] is None   # No port in invalid URL
        assert result['api']['port'] == 8886  # API info should still be valid


class TestCleanCredentialServiceArchitecturalCompliance:
    """Tests specifically for architectural compliance - no environment variable generation."""
    
    def setup_method(self):
        """Setup test environment."""
        self.service = CleanCredentialService()
    
    def test_no_env_file_creation_methods(self):
        """Test that service has NO methods for creating .env files."""
        # Verify that forbidden methods do not exist
        forbidden_methods = [
            'generate_master_credentials', 
            'generate_mode_credentials',
            'save_environment_file',
            'create_env_file',
            'write_env_file',
            '_create_mode_env_file',
            '_save_master_credentials',
            'generate_all_mode_credentials',
            'save_master_env_file'
        ]
        
        for method_name in forbidden_methods:
            assert not hasattr(self.service, method_name), \
                f"ARCHITECTURAL VIOLATION: Service has forbidden method '{method_name}' that generates environment variables"
    
    def test_only_read_operations_allowed(self):
        """Test that service only has read/validate operations."""
        # Get all methods that don't start with underscore
        public_methods = [method for method in dir(self.service) 
                         if not method.startswith('_') and callable(getattr(self.service, method))]
        
        # All public methods should be read-only or validation operations
        allowed_method_prefixes = ['validate', 'get', 'check', 'read', 'load']
        
        for method_name in public_methods:
            # Skip special methods like __init__
            if method_name.startswith('__'):
                continue
                
            method_is_allowed = any(method_name.startswith(prefix) for prefix in allowed_method_prefixes)
            assert method_is_allowed, \
                f"ARCHITECTURAL VIOLATION: Method '{method_name}' is not a read-only/validation operation"
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.write_text')
    def test_no_file_writing_operations(self, mock_write_text, mock_file_open):
        """Test that service never attempts to write files during any operation."""
        mock_settings = Mock(spec=HiveSettings)
        mock_settings.hive_database_url = "postgresql+psycopg://user:pass@localhost:5532/hive"
        mock_settings.hive_api_key = "hive_test_key_12345678901234567890123456"
        mock_settings.hive_api_port = 8886
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('lib.config.settings.get_settings', return_value=mock_settings):
            
            # Call all validation methods
            self.service.validate_env_file_exists()
            self.service.validate_database_credentials()
            self.service.validate_api_credentials()
            self.service.validate_all_credentials()
            self.service.get_connection_info()
            
        # Verify NO file writing occurred
        mock_write_text.assert_not_called()
        mock_file_open.assert_not_called()
    
    def test_architectural_compliance_documentation(self):
        """Test that service has proper architectural compliance documentation."""
        # Check class docstring mentions architectural principle
        class_doc = CleanCredentialService.__doc__
        assert class_doc is not None
        assert 'read-only' in class_doc.lower() or 'validation' in class_doc.lower()
        assert 'never' in class_doc.lower() and ('write' in class_doc.lower() or 'generate' in class_doc.lower())


if __name__ == "__main__":
    pytest.main([__file__])