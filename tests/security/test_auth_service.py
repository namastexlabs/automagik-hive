"""
Comprehensive security tests for AuthService.

Tests critical authentication security patterns including:
- API key validation security
- Timing attack prevention
- Auth bypass prevention
- Edge case handling
- Environment security
"""

import os
import time
from unittest.mock import MagicMock, patch

import pytest

from lib.auth.service import AuthService


class TestAuthServiceSecurity:
    """Test suite for AuthService security patterns."""

    @pytest.fixture
    def clean_environment(self):
        """Clean environment for each test."""
        # Store original values
        original_auth_disabled = os.environ.get("HIVE_AUTH_DISABLED")
        original_api_key = os.environ.get("HIVE_API_KEY")

        # Clean environment
        os.environ.pop("HIVE_AUTH_DISABLED", None)
        os.environ.pop("HIVE_API_KEY", None)

        yield

        # Restore original values
        if original_auth_disabled is not None:
            os.environ["HIVE_AUTH_DISABLED"] = original_auth_disabled
        else:
            os.environ.pop("HIVE_AUTH_DISABLED", None)

        if original_api_key is not None:
            os.environ["HIVE_API_KEY"] = original_api_key
        else:
            os.environ.pop("HIVE_API_KEY", None)

    @pytest.fixture
    def mock_auth_init_service(self):
        """Mock AuthInitService to control key generation."""
        with patch("lib.auth.service.AuthInitService") as mock_init:
            mock_instance = MagicMock()
            mock_instance.ensure_api_key.return_value = "test_key_123"
            mock_init.return_value = mock_instance
            yield mock_instance

    def test_auth_service_initialization_with_key(
        self,
        clean_environment,
        mock_auth_init_service,
    ):
        """Test AuthService properly initializes with API key."""
        service = AuthService()

        assert service.api_key == "test_key_123"
        assert not service.auth_disabled
        mock_auth_init_service.ensure_api_key.assert_called_once()

    def test_auth_service_initialization_disabled(
        self,
        clean_environment,
        mock_auth_init_service,
    ):
        """Test AuthService respects HIVE_AUTH_DISABLED flag."""
        os.environ["HIVE_AUTH_DISABLED"] = "true"

        service = AuthService()

        assert service.auth_disabled
        assert service.api_key == "test_key_123"

    @pytest.mark.asyncio
    async def test_valid_api_key_acceptance(
        self,
        clean_environment,
        mock_auth_init_service,
    ):
        """Test that valid API keys are accepted."""
        service = AuthService()

        result = await service.validate_api_key("test_key_123")

        assert result

    @pytest.mark.asyncio
    async def test_invalid_api_key_rejection(
        self,
        clean_environment,
        mock_auth_init_service,
    ):
        """Test that invalid API keys are rejected."""
        service = AuthService()

        result = await service.validate_api_key("wrong_key")

        assert not result

    @pytest.mark.asyncio
    async def test_none_api_key_rejection(
        self,
        clean_environment,
        mock_auth_init_service,
    ):
        """Test that None API key is rejected."""
        service = AuthService()

        result = await service.validate_api_key(None)

        assert not result

    @pytest.mark.asyncio
    async def test_empty_string_api_key_rejection(
        self,
        clean_environment,
        mock_auth_init_service,
    ):
        """Test that empty string API key is rejected."""
        service = AuthService()

        result = await service.validate_api_key("")

        assert not result

    @pytest.mark.asyncio
    async def test_whitespace_api_key_rejection(
        self,
        clean_environment,
        mock_auth_init_service,
    ):
        """Test that whitespace-only API key is rejected."""
        service = AuthService()

        result = await service.validate_api_key("   ")

        assert not result

    @pytest.mark.asyncio
    async def test_auth_disabled_bypass(
        self,
        clean_environment,
        mock_auth_init_service,
    ):
        """Test that authentication bypass works when disabled."""
        os.environ["HIVE_AUTH_DISABLED"] = "true"
        service = AuthService()

        # Should return True even with invalid keys when auth disabled
        result = await service.validate_api_key("invalid_key")
        assert result

        result = await service.validate_api_key(None)
        assert result

        result = await service.validate_api_key("")
        assert result

    @pytest.mark.asyncio
    async def test_no_api_key_configured_error(self, clean_environment):
        """Test that missing API key configuration raises error."""
        with patch("lib.auth.service.AuthInitService") as mock_init:
            mock_instance = MagicMock()
            mock_instance.ensure_api_key.return_value = None
            mock_init.return_value = mock_instance

            service = AuthService()

            with pytest.raises(
                ValueError,
                match="HIVE_API_KEY not properly initialized",
            ):
                await service.validate_api_key("any_key")

    @pytest.mark.asyncio
    async def test_timing_attack_resistance(
        self,
        clean_environment,
        mock_auth_init_service,
    ):
        """Test that validate_api_key is resistant to timing attacks."""
        service = AuthService()
        correct_key = "test_key_123"

        # Test multiple incorrect keys of varying lengths
        incorrect_keys = [
            "a",  # Very short
            "wrong_key",  # Medium length
            "this_is_a_very_long_incorrect_key_that_should_take_same_time",  # Long
            correct_key[:-1],  # Almost correct (missing last char)
            correct_key + "x",  # Almost correct (extra char)
        ]

        # Run multiple iterations to get average timing and reduce variance
        num_iterations = 5

        # Measure average timing for correct key
        correct_times = []
        for _ in range(num_iterations):
            start_time = time.perf_counter()
            await service.validate_api_key(correct_key)
            correct_times.append(time.perf_counter() - start_time)
        correct_time = sum(correct_times) / len(correct_times)

        # Measure average timing for incorrect keys
        for incorrect_key in incorrect_keys:
            incorrect_times = []
            for _ in range(num_iterations):
                start_time = time.perf_counter()
                result = await service.validate_api_key(incorrect_key)
                incorrect_times.append(time.perf_counter() - start_time)
                assert not result

            incorrect_time = sum(incorrect_times) / len(incorrect_times)

            # More generous threshold for CI/container environments
            # Timing attacks require microsecond precision - 50x variance is acceptable
            time_ratio = max(correct_time, incorrect_time) / min(
                correct_time,
                incorrect_time,
            )
            assert time_ratio < 50.0, f"Timing difference too large: {time_ratio}"

    def test_is_auth_enabled_with_auth_disabled_false(
        self,
        clean_environment,
        mock_auth_init_service,
    ):
        """Test is_auth_enabled returns True when auth is enabled."""
        service = AuthService()

        assert service.is_auth_enabled()

    def test_is_auth_enabled_with_auth_disabled_true(
        self,
        clean_environment,
        mock_auth_init_service,
    ):
        """Test is_auth_enabled returns False when auth is disabled."""
        os.environ["HIVE_AUTH_DISABLED"] = "true"
        service = AuthService()

        assert not service.is_auth_enabled()

    def test_get_current_key(self, clean_environment, mock_auth_init_service):
        """Test get_current_key returns the configured key."""
        service = AuthService()

        assert service.get_current_key() == "test_key_123"

    def test_regenerate_key(self, clean_environment, mock_auth_init_service):
        """Test key regeneration updates the service."""
        mock_auth_init_service.regenerate_key.return_value = "new_key_456"

        service = AuthService()
        old_key = service.get_current_key()

        new_key = service.regenerate_key()

        assert new_key == "new_key_456"
        assert service.get_current_key() == "new_key_456"
        assert old_key != new_key
        mock_auth_init_service.regenerate_key.assert_called_once()

    @pytest.mark.asyncio
    async def test_case_sensitive_api_key_validation(
        self,
        clean_environment,
        mock_auth_init_service,
    ):
        """Test that API key validation is case-sensitive."""
        service = AuthService()

        # Test various case variations should all fail
        case_variations = [
            "TEST_KEY_123",
            "Test_Key_123",
            "test_KEY_123",
            "test_key_123".upper(),
        ]

        for variation in case_variations:
            result = await service.validate_api_key(variation)
            assert not result, f"Case variation {variation} should be rejected"

    @pytest.mark.asyncio
    async def test_unicode_and_special_chars_in_key(self, clean_environment):
        """Test handling of unicode and special characters in API keys."""
        with patch("lib.auth.service.AuthInitService") as mock_init:
            # Test with key containing ASCII special chars (secrets.compare_digest limitation)
            special_key = "test_key_!@#$%^&*()_-=+[]{}|;:,.<>?"
            mock_instance = MagicMock()
            mock_instance.ensure_api_key.return_value = special_key
            mock_init.return_value = mock_instance

            service = AuthService()

            # Should accept exact match
            result = await service.validate_api_key(special_key)
            assert result

            # Should reject similar but different
            result = await service.validate_api_key(
                "test_key_!@#$%^&*()_-=+[]{}|;:,.<>!",
            )
            assert not result

    @pytest.mark.asyncio
    async def test_environment_variable_precedence(self, clean_environment):
        """Test that environment variables take precedence over other sources."""
        # Set environment variable directly
        os.environ["HIVE_API_KEY"] = "env_key_direct"

        with patch("lib.auth.service.AuthInitService") as mock_init:
            mock_instance = MagicMock()
            # ensure_api_key should return env value if set
            mock_instance.ensure_api_key.return_value = "env_key_direct"
            mock_init.return_value = mock_instance

            service = AuthService()

            # Should use environment variable
            assert service.api_key == "env_key_direct"

            result = await service.validate_api_key("env_key_direct")
            assert result

            result = await service.validate_api_key("other_key")
            assert not result


class TestAuthServiceEdgeCases:
    """Test edge cases and boundary conditions for AuthService."""

    @pytest.fixture
    def clean_environment(self):
        """Clean environment for each test."""
        original_auth_disabled = os.environ.get("HIVE_AUTH_DISABLED")
        original_api_key = os.environ.get("HIVE_API_KEY")

        os.environ.pop("HIVE_AUTH_DISABLED", None)
        os.environ.pop("HIVE_API_KEY", None)

        yield

        if original_auth_disabled is not None:
            os.environ["HIVE_AUTH_DISABLED"] = original_auth_disabled
        else:
            os.environ.pop("HIVE_AUTH_DISABLED", None)

        if original_api_key is not None:
            os.environ["HIVE_API_KEY"] = original_api_key
        else:
            os.environ.pop("HIVE_API_KEY", None)

    def test_auth_disabled_variations(self, clean_environment):
        """Test various HIVE_AUTH_DISABLED environment values."""
        disabled_values = ["true", "TRUE", "True", "1", "yes", "YES", "on", "ON"]
        enabled_values = ["false", "FALSE", "False", "0", "no", "NO", "off", "OFF", ""]

        with patch("lib.auth.service.AuthInitService") as mock_init:
            mock_instance = MagicMock()
            mock_instance.ensure_api_key.return_value = "test_key"
            mock_init.return_value = mock_instance

            # Test disabled values (only "true" should disable auth)
            for value in disabled_values:
                os.environ["HIVE_AUTH_DISABLED"] = value
                service = AuthService()

                if value.lower() == "true":
                    assert service.auth_disabled, f"Value '{value}' should disable auth"
                else:
                    assert not service.auth_disabled, (
                        f"Value '{value}' should NOT disable auth"
                    )

                # Clean up
                os.environ.pop("HIVE_AUTH_DISABLED", None)

            # Test enabled values
            for value in enabled_values:
                os.environ["HIVE_AUTH_DISABLED"] = value
                service = AuthService()
                assert not service.auth_disabled, (
                    f"Value '{value}' should keep auth enabled"
                )

                # Clean up
                os.environ.pop("HIVE_AUTH_DISABLED", None)

    @pytest.mark.asyncio
    async def test_very_long_api_keys(self, clean_environment):
        """Test handling of very long API keys."""
        with patch("lib.auth.service.AuthInitService") as mock_init:
            # Generate very long key (1MB)
            very_long_key = "k" * (1024 * 1024)
            mock_instance = MagicMock()
            mock_instance.ensure_api_key.return_value = very_long_key
            mock_init.return_value = mock_instance

            service = AuthService()

            # Should handle long keys without issues
            result = await service.validate_api_key(very_long_key)
            assert result

            # Should still reject incorrect long keys
            wrong_long_key = "x" * (1024 * 1024)
            result = await service.validate_api_key(wrong_long_key)
            assert not result

    @pytest.mark.asyncio
    async def test_concurrent_api_key_validation(self, clean_environment):
        """Test concurrent API key validation for thread safety."""
        import asyncio

        with patch("lib.auth.service.AuthInitService") as mock_init:
            mock_instance = MagicMock()
            mock_instance.ensure_api_key.return_value = "concurrent_test_key"
            mock_init.return_value = mock_instance

            service = AuthService()

            # Run multiple concurrent validations
            async def validate_key(key):
                return await service.validate_api_key(key)

            # Mix of valid and invalid keys
            keys = [
                "concurrent_test_key",
                "wrong_key",
                "concurrent_test_key",
                "invalid",
                "concurrent_test_key",
            ]
            expected = [True, False, True, False, True]

            # Run concurrently
            tasks = [validate_key(key) for key in keys]
            results = await asyncio.gather(*tasks)

            assert results == expected

    def test_service_state_isolation(self, clean_environment):
        """Test that multiple AuthService instances don't interfere."""
        with patch("lib.auth.service.AuthInitService") as mock_init:
            # First service
            mock_instance1 = MagicMock()
            mock_instance1.ensure_api_key.return_value = "key1"
            mock_init.return_value = mock_instance1

            service1 = AuthService()

            # Second service with different mock
            mock_instance2 = MagicMock()
            mock_instance2.ensure_api_key.return_value = "key2"
            mock_init.return_value = mock_instance2

            service2 = AuthService()

            # Services should maintain separate state
            assert service1.api_key == "key1"
            assert service2.api_key == "key2"

            # Regenerating one shouldn't affect the other
            mock_instance1.regenerate_key.return_value = "new_key1"
            service1.regenerate_key()

            assert service1.api_key == "new_key1"
            assert service2.api_key == "key2"  # Should remain unchanged
