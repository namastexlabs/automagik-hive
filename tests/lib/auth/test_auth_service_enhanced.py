"""
Enhanced tests for lib/auth/service.py - targeting 100% coverage.

These tests complement existing integration tests by focusing on missing coverage areas:
- Production environment override scenarios  
- Complete get_auth_status method coverage
- Additional edge cases and error conditions

Test Categories:
- Production security: Environment-based security overrides
- Status reporting: Complete auth status method coverage
- Edge cases: Additional boundary conditions not covered elsewhere
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock

from lib.auth.service import AuthService


class TestProductionSecurityOverride:
    """Test production environment security override scenarios."""

    @pytest.fixture
    def clean_environment(self):
        """Clean environment for each test."""
        original_values = {}
        env_vars = ["HIVE_ENVIRONMENT", "HIVE_AUTH_DISABLED", "HIVE_API_KEY"]
        
        for var in env_vars:
            original_values[var] = os.environ.get(var)
            os.environ.pop(var, None)
        
        yield
        
        for var, value in original_values.items():
            if value is not None:
                os.environ[var] = value
            else:
                os.environ.pop(var, None)

    @patch('lib.auth.service.AuthInitService')
    def test_production_override_forces_auth_enabled(self, mock_auth_init, clean_environment):
        """Test that production environment forces auth enabled even with HIVE_AUTH_DISABLED=true."""
        # Setup mocks
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = "prod_key_123"
        mock_auth_init.return_value = mock_service
        
        # Set production environment with auth disabled flag
        os.environ["HIVE_ENVIRONMENT"] = "production"
        os.environ["HIVE_AUTH_DISABLED"] = "true"
        
        service = AuthService()
        
        # Production should override the disabled flag (line 26)
        assert not service.auth_disabled  # Auth should be forced enabled
        assert service.environment == "production"
        assert service.is_auth_enabled()

    @patch('lib.auth.service.AuthInitService')
    def test_production_case_insensitive(self, mock_auth_init, clean_environment):
        """Test production environment is case insensitive."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = "prod_key_123"
        mock_auth_init.return_value = mock_service
        
        # Test various case combinations
        production_values = ["PRODUCTION", "Production", "pRODUCTION"]
        
        for prod_value in production_values:
            os.environ["HIVE_ENVIRONMENT"] = prod_value
            os.environ["HIVE_AUTH_DISABLED"] = "true"
            
            service = AuthService()
            
            assert not service.auth_disabled
            assert service.environment == prod_value.lower()
            
            # Clean up for next iteration
            os.environ.pop("HIVE_ENVIRONMENT", None)

    @patch('lib.auth.service.AuthInitService')
    def test_non_production_respects_auth_disabled(self, mock_auth_init, clean_environment):
        """Test non-production environments respect HIVE_AUTH_DISABLED."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = "dev_key_123"
        mock_auth_init.return_value = mock_service
        
        # Test various non-production environments
        environments = ["development", "staging", "test", "local"]
        
        for env in environments:
            os.environ["HIVE_ENVIRONMENT"] = env
            os.environ["HIVE_AUTH_DISABLED"] = "true"
            
            service = AuthService()
            
            assert service.auth_disabled  # Non-production should respect the flag
            assert service.environment == env
            assert not service.is_auth_enabled()
            
            # Clean up for next iteration
            os.environ.pop("HIVE_ENVIRONMENT", None)
            os.environ.pop("HIVE_AUTH_DISABLED", None)


class TestGetAuthStatusMethod:
    """Test get_auth_status method for complete coverage."""

    @pytest.fixture
    def clean_environment(self):
        """Clean environment for each test."""
        original_values = {}
        env_vars = ["HIVE_ENVIRONMENT", "HIVE_AUTH_DISABLED", "HIVE_API_KEY"]
        
        for var in env_vars:
            original_values[var] = os.environ.get(var)
            os.environ.pop(var, None)
        
        yield
        
        for var, value in original_values.items():
            if value is not None:
                os.environ[var] = value
            else:
                os.environ.pop(var, None)

    @patch('lib.auth.service.AuthInitService')
    def test_get_auth_status_production_override_active(self, mock_auth_init, clean_environment):
        """Test get_auth_status when production override is active (lines 71-73)."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = "prod_key_123"
        mock_auth_init.return_value = mock_service
        
        # Set production environment with auth disabled in raw setting
        os.environ["HIVE_ENVIRONMENT"] = "production"
        os.environ["HIVE_AUTH_DISABLED"] = "true"
        
        service = AuthService()
        status = service.get_auth_status()
        
        # Verify status includes all required fields (lines 71-73)
        expected_status = {
            "environment": "production",
            "auth_enabled": True,  # Forced by production override
            "production_override_active": True,  # This should be True
            "raw_hive_auth_disabled_setting": True,
            "effective_auth_disabled": False,  # Overridden by production
            "security_note": "Authentication is ALWAYS enabled in production regardless of HIVE_AUTH_DISABLED setting"
        }
        
        assert status == expected_status
        assert status["production_override_active"]  # Covers the override logic

    @patch('lib.auth.service.AuthInitService')  
    def test_get_auth_status_no_production_override(self, mock_auth_init, clean_environment):
        """Test get_auth_status when production override is not active."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = "dev_key_123"
        mock_auth_init.return_value = mock_service
        
        # Set development environment with auth disabled
        os.environ["HIVE_ENVIRONMENT"] = "development"
        os.environ["HIVE_AUTH_DISABLED"] = "true"
        
        service = AuthService()
        status = service.get_auth_status()
        
        expected_status = {
            "environment": "development",
            "auth_enabled": False,
            "production_override_active": False,  # No override in development
            "raw_hive_auth_disabled_setting": True,
            "effective_auth_disabled": True,  # Not overridden
            "security_note": "Authentication is ALWAYS enabled in production regardless of HIVE_AUTH_DISABLED setting"
        }
        
        assert status == expected_status
        assert not status["production_override_active"]

    @patch('lib.auth.service.AuthInitService')
    def test_get_auth_status_production_with_auth_enabled(self, mock_auth_init, clean_environment):
        """Test get_auth_status in production with auth naturally enabled."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = "prod_key_123"
        mock_auth_init.return_value = mock_service
        
        # Set production environment with auth enabled (not disabled)
        os.environ["HIVE_ENVIRONMENT"] = "production"
        os.environ["HIVE_AUTH_DISABLED"] = "false"
        
        service = AuthService()
        status = service.get_auth_status()
        
        expected_status = {
            "environment": "production",
            "auth_enabled": True,
            "production_override_active": False,  # No override needed
            "raw_hive_auth_disabled_setting": False,
            "effective_auth_disabled": False,
            "security_note": "Authentication is ALWAYS enabled in production regardless of HIVE_AUTH_DISABLED setting"
        }
        
        assert status == expected_status
        assert not status["production_override_active"]  # No override needed

    @patch('lib.auth.service.AuthInitService')
    def test_get_auth_status_missing_env_vars(self, mock_auth_init, clean_environment):
        """Test get_auth_status with missing environment variables."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = "default_key_123"
        mock_auth_init.return_value = mock_service
        
        # No environment variables set - should use defaults
        service = AuthService()
        status = service.get_auth_status()
        
        expected_status = {
            "environment": "development",  # Default
            "auth_enabled": True,  # Default (auth_disabled = False)
            "production_override_active": False,
            "raw_hive_auth_disabled_setting": False,  # Default
            "effective_auth_disabled": False,  # Default
            "security_note": "Authentication is ALWAYS enabled in production regardless of HIVE_AUTH_DISABLED setting"
        }
        
        assert status == expected_status

    @patch('lib.auth.service.AuthInitService')
    def test_get_auth_status_various_env_values(self, mock_auth_init, clean_environment):
        """Test get_auth_status with various environment values."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = "test_key_123"
        mock_auth_init.return_value = mock_service
        
        # Test various environment combinations
        test_cases = [
            ("staging", "false", False, False),
            ("test", "true", True, False),
            ("local", "TRUE", True, False),
            ("production", "false", False, False),
            ("production", "true", True, True),  # Override active
        ]
        
        for env, auth_disabled, raw_disabled, override_active in test_cases:
            os.environ["HIVE_ENVIRONMENT"] = env
            os.environ["HIVE_AUTH_DISABLED"] = auth_disabled
            
            service = AuthService()
            status = service.get_auth_status()
            
            assert status["environment"] == env
            assert status["raw_hive_auth_disabled_setting"] == raw_disabled
            assert status["production_override_active"] == override_active
            
            # Clean up
            os.environ.pop("HIVE_ENVIRONMENT", None)
            os.environ.pop("HIVE_AUTH_DISABLED", None)


class TestAdditionalEdgeCases:
    """Test additional edge cases for comprehensive coverage."""

    @pytest.fixture
    def clean_environment(self):
        """Clean environment for each test."""
        original_values = {}
        env_vars = ["HIVE_ENVIRONMENT", "HIVE_AUTH_DISABLED", "HIVE_API_KEY"]
        
        for var in env_vars:
            original_values[var] = os.environ.get(var)
            os.environ.pop(var, None)
        
        yield
        
        for var, value in original_values.items():
            if value is not None:
                os.environ[var] = value
            else:
                os.environ.pop(var, None)

    @patch('lib.auth.service.AuthInitService')
    def test_service_initialization_with_different_environments(self, mock_auth_init, clean_environment):
        """Test service initialization across different environments."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = "env_test_key"
        mock_auth_init.return_value = mock_service
        
        # Test various environment settings
        environments = [
            "development",
            "staging", 
            "test",
            "production",
            "DEVELOPMENT",  # Case variations
            "Production",
            "",  # Empty string
            "custom_env"  # Custom environment
        ]
        
        for env in environments:
            os.environ["HIVE_ENVIRONMENT"] = env
            
            service = AuthService()
            
            expected_env = env.lower()
            assert service.environment == expected_env
            
            # Production should always force auth enabled
            if expected_env == "production":
                assert not service.auth_disabled
            else:
                # Other environments should use default (enabled)
                assert not service.auth_disabled
            
            # Clean up
            os.environ.pop("HIVE_ENVIRONMENT", None)

    @patch('lib.auth.service.AuthInitService')
    @pytest.mark.asyncio
    async def test_validate_api_key_with_production_environment(self, mock_auth_init, clean_environment):
        """Test API key validation in production environment."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = "prod_secure_key"
        mock_auth_init.return_value = mock_service
        
        os.environ["HIVE_ENVIRONMENT"] = "production"
        os.environ["HIVE_AUTH_DISABLED"] = "true"  # Should be ignored
        
        service = AuthService()
        
        # Even with auth_disabled=true, production should validate keys
        result = await service.validate_api_key("prod_secure_key")
        assert result
        
        result = await service.validate_api_key("wrong_key")
        assert not result
        
        result = await service.validate_api_key(None)
        assert not result

    @patch('lib.auth.service.AuthInitService')
    def test_key_regeneration_in_different_environments(self, mock_auth_init, clean_environment):
        """Test key regeneration across different environments."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = "original_key"
        mock_service.regenerate_key.return_value = "new_regenerated_key"
        mock_auth_init.return_value = mock_service
        
        environments = ["development", "staging", "production"]
        
        for env in environments:
            os.environ["HIVE_ENVIRONMENT"] = env
            
            service = AuthService()
            original_key = service.get_current_key()
            
            new_key = service.regenerate_key()
            
            assert original_key == "original_key"
            assert new_key == "new_regenerated_key"
            assert service.get_current_key() == "new_regenerated_key"
            
            # Clean up
            os.environ.pop("HIVE_ENVIRONMENT", None)

    @patch('lib.auth.service.AuthInitService')
    def test_auth_service_state_consistency(self, mock_auth_init, clean_environment):
        """Test that AuthService maintains consistent state."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = "consistent_key"
        mock_auth_init.return_value = mock_service
        
        os.environ["HIVE_ENVIRONMENT"] = "production"
        os.environ["HIVE_AUTH_DISABLED"] = "true"
        
        service = AuthService()
        
        # Test state consistency across multiple calls
        assert service.is_auth_enabled() == (not service.auth_disabled)
        assert service.get_current_key() == service.api_key
        
        # Status should be consistent with internal state
        status = service.get_auth_status()
        assert status["auth_enabled"] == service.is_auth_enabled()
        assert status["environment"] == service.environment
        assert status["effective_auth_disabled"] == service.auth_disabled