"""
Core authentication service for Automagik Hive.

Provides x-api-key validation and authentication logic.
"""

import os
import secrets

from .init_service import AuthInitService


class AuthService:
    """Core authentication service."""

    def __init__(self) -> None:
        # Initialize API key on startup
        self.init_service = AuthInitService()
        self.api_key = self.init_service.ensure_api_key()

        # Production security override: ALWAYS enable auth in production
        self.environment = os.getenv("HIVE_ENVIRONMENT", "development").lower()

        if self.environment == "production":
            # Production override: ALWAYS enable authentication regardless of HIVE_AUTH_DISABLED
            self.auth_disabled = False
        else:
            # Development/staging: respect HIVE_AUTH_DISABLED setting (default: enabled for security)
            self.auth_disabled = (
                os.getenv("HIVE_AUTH_DISABLED", "false").lower() == "true"
            )

    async def validate_api_key(self, provided_key: str | None) -> bool:
        """
        Validate provided API key against configured key.

        Args:
            provided_key: The API key to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if self.auth_disabled:
            return True  # Development bypass

        if not provided_key:
            return False

        if not self.api_key:
            raise ValueError("HIVE_API_KEY not properly initialized")

        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(self.api_key, provided_key)

    def is_auth_enabled(self) -> bool:
        """Check if authentication is enabled."""
        return not self.auth_disabled

    def get_current_key(self) -> str | None:
        """Get current API key."""
        return self.api_key

    def regenerate_key(self) -> str:
        """Regenerate API key."""
        api_key = self.init_service.regenerate_key()
        self.api_key = api_key
        return api_key

    def get_auth_status(self) -> dict[str, str | bool]:
        """Get current authentication status and configuration."""
        raw_auth_disabled = os.getenv("HIVE_AUTH_DISABLED", "false").lower() == "true"

        return {
            "environment": self.environment,
            "auth_enabled": not self.auth_disabled,
            "production_override_active": self.environment == "production"
            and raw_auth_disabled,
            "raw_hive_auth_disabled_setting": raw_auth_disabled,
            "effective_auth_disabled": self.auth_disabled,
            "security_note": "Authentication is ALWAYS enabled in production regardless of HIVE_AUTH_DISABLED setting",
        }
