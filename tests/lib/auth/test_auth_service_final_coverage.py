"""
Final coverage tests for lib/auth/service.py - targeting 100% coverage.

These tests specifically target the remaining missing lines:
- Line 44: Development bypass scenario (auth_disabled = True)
- Line 50: API key not properly initialized error

Test Categories:
- Development bypass: Auth disabled scenarios returning True immediately
- Initialization errors: Missing API key error conditions
"""

import os
import pytest
from unittest.mock import Mock, patch

from lib.auth.service import AuthService


class TestDevelopmentBypass:
    """Test development auth bypass scenarios (line 44)."""

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
    @pytest.mark.asyncio
    async def test_auth_disabled_returns_true_immediately(self, mock_auth_init, clean_environment):
        """Test that auth disabled bypasses all validation and returns True (line 44)."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = "any_key"
        mock_auth_init.return_value = mock_service
        
        # Set auth disabled in development
        os.environ["HIVE_ENVIRONMENT"] = "development"
        os.environ["HIVE_AUTH_DISABLED"] = "true"
        
        service = AuthService()
        
        # All these should return True immediately due to bypass (line 44)
        assert await service.validate_api_key("any_key") is True
        assert await service.validate_api_key("wrong_key") is True
        assert await service.validate_api_key(None) is True
        assert await service.validate_api_key("") is True
        assert await service.validate_api_key("   ") is True
        assert await service.validate_api_key("totally_invalid") is True
        
        # Verify auth is actually disabled
        assert service.auth_disabled

    @patch('lib.auth.service.AuthInitService')
    @pytest.mark.asyncio
    async def test_auth_disabled_various_environments(self, mock_auth_init, clean_environment):
        """Test auth disabled bypass in various non-production environments."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = "test_key"
        mock_auth_init.return_value = mock_service
        
        # Test non-production environments with auth disabled
        environments = ["development", "staging", "test", "local", "custom"]
        
        for env in environments:
            os.environ["HIVE_ENVIRONMENT"] = env
            os.environ["HIVE_AUTH_DISABLED"] = "true"
            
            service = AuthService()
            
            # Should bypass validation and return True (line 44)
            result = await service.validate_api_key("anything")
            assert result is True
            
            # Clean up
            os.environ.pop("HIVE_ENVIRONMENT", None)
            os.environ.pop("HIVE_AUTH_DISABLED", None)


class TestApiKeyInitializationError:
    """Test API key initialization error scenarios (line 50)."""

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
    @pytest.mark.asyncio
    async def test_api_key_none_raises_error(self, mock_auth_init, clean_environment):
        """Test that None API key raises ValueError (line 50)."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = None  # API key not initialized
        mock_auth_init.return_value = mock_service
        
        # Auth enabled (default)
        service = AuthService()
        
        # Should raise ValueError when trying to validate with None api_key (line 50)
        with pytest.raises(ValueError, match="HIVE_API_KEY not properly initialized"):
            await service.validate_api_key("any_provided_key")

    @patch('lib.auth.service.AuthInitService')
    @pytest.mark.asyncio
    async def test_api_key_empty_string_raises_error(self, mock_auth_init, clean_environment):
        """Test that empty string API key raises ValueError (line 50)."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = ""  # Empty API key
        mock_auth_init.return_value = mock_service
        
        service = AuthService()
        
        # Should raise ValueError when trying to validate with empty api_key (line 50)
        with pytest.raises(ValueError, match="HIVE_API_KEY not properly initialized"):
            await service.validate_api_key("some_provided_key")

    @patch('lib.auth.service.AuthInitService')
    @pytest.mark.asyncio
    async def test_api_key_whitespace_raises_error(self, mock_auth_init, clean_environment):
        """Test that whitespace-only API key raises ValueError (line 50)."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = "   "  # Whitespace API key
        mock_auth_init.return_value = mock_service
        
        service = AuthService()
        
        # Should not raise error - whitespace is considered a valid (but poor) key
        # This tests the boundary condition
        result = await service.validate_api_key("   ")
        assert result  # Should match the whitespace key

        # Different key should fail
        result = await service.validate_api_key("real_key")
        assert not result

    @patch('lib.auth.service.AuthInitService')
    @pytest.mark.asyncio
    async def test_error_only_when_auth_enabled(self, mock_auth_init, clean_environment):
        """Test that API key error only occurs when auth is enabled."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = None
        mock_auth_init.return_value = mock_service
        
        # Test with auth disabled - should bypass error check
        os.environ["HIVE_AUTH_DISABLED"] = "true"
        service = AuthService()
        
        # Should return True due to bypass (line 44), not reach error check (line 50)
        result = await service.validate_api_key("any_key")
        assert result is True

    @patch('lib.auth.service.AuthInitService')
    @pytest.mark.asyncio
    async def test_production_environment_api_key_error(self, mock_auth_init, clean_environment):
        """Test API key initialization error in production environment."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = None
        mock_auth_init.return_value = mock_service
        
        # Production environment with auth forced enabled
        os.environ["HIVE_ENVIRONMENT"] = "production"
        os.environ["HIVE_AUTH_DISABLED"] = "true"  # Should be ignored
        
        service = AuthService()
        
        # Should raise error because production forces auth enabled (line 50)
        with pytest.raises(ValueError, match="HIVE_API_KEY not properly initialized"):
            await service.validate_api_key("production_key")


class TestEdgeCaseCombinations:
    """Test edge case combinations to ensure complete coverage."""

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
    @pytest.mark.asyncio
    async def test_validate_api_key_flow_coverage(self, mock_auth_init, clean_environment):
        """Test complete validate_api_key method flow for coverage."""
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = "valid_test_key"
        mock_auth_init.return_value = mock_service
        
        # Standard auth enabled case
        service = AuthService()
        
        # Test the complete flow:
        # 1. Auth not disabled (line 43 check fails)
        # 2. Provided key exists (line 46 check fails)  
        # 3. API key exists (line 49 check fails)
        # 4. Perform comparison (line 53)
        
        result = await service.validate_api_key("valid_test_key")
        assert result is True
        
        result = await service.validate_api_key("invalid_key")
        assert result is False

    @patch('lib.auth.service.AuthInitService')
    @pytest.mark.asyncio
    async def test_all_code_paths_combined(self, mock_auth_init, clean_environment):
        """Test all code paths to ensure 100% coverage."""
        # Test scenario 1: Auth disabled (line 44)
        mock_service = Mock()
        mock_service.ensure_api_key.return_value = "key1"
        mock_auth_init.return_value = mock_service
        
        os.environ["HIVE_AUTH_DISABLED"] = "true"
        service1 = AuthService()
        
        result = await service1.validate_api_key("anything")
        assert result is True  # Line 44 covered
        
        # Test scenario 2: API key None error (line 50)
        os.environ.pop("HIVE_AUTH_DISABLED", None)
        mock_service.ensure_api_key.return_value = None
        service2 = AuthService()
        
        with pytest.raises(ValueError):  # Line 50 covered
            await service2.validate_api_key("test")
            
        # Test scenario 3: Normal flow (all other lines)
        mock_service.ensure_api_key.return_value = "normal_key"
        service3 = AuthService()
        
        result = await service3.validate_api_key("normal_key")
        assert result is True  # Line 53 covered
        
        result = await service3.validate_api_key(None)
        assert result is False  # Line 47 covered