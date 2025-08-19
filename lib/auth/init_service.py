"""
Authentication initialization service.

Handles auto-generation and management of API keys.
"""

import os
import secrets
from pathlib import Path

from lib.logging import logger


class AuthInitService:
    """Service for initializing and managing API keys."""

    def __init__(self) -> None:
        self.env_file = Path(".env")
        self.api_key_var = "HIVE_API_KEY"
        self.auth_disabled_var = "HIVE_AUTH_DISABLED"

    def ensure_api_key(self) -> str:
        """Ensure API key exists, generate if needed."""
        # Check environment first
        existing_key = os.getenv(self.api_key_var)
        if existing_key:
            return existing_key

        # Check .env file
        if self.env_file.exists():
            existing_key = self._read_key_from_env()
            if existing_key:
                # Return .env value without overriding shell environment
                return existing_key

        # For CLI operations, don't auto-generate keys that interfere with workspace creation
        # Only generate if we're in a proper workspace context
        if not self.env_file.exists() or not self.env_file.is_file():
            # Return a temporary key for CLI operations
            temp_key = self._generate_secure_key()
            logger.info(f"🔐 Using temporary API key for CLI operation: {temp_key}")
            os.environ[self.api_key_var] = temp_key
            return temp_key

        # Generate new key and save
        api_key = self._generate_secure_key()
        self._save_key_to_env(api_key)
        self._display_key_to_user(api_key)

        # Set in environment for current session
        os.environ[self.api_key_var] = api_key
        return api_key

    def _generate_secure_key(self) -> str:
        """Generate a cryptographically secure API key."""
        return f"hive_{secrets.token_urlsafe(32)}"

    def _save_key_to_env(self, api_key: str) -> None:
        """Add or replace API key in .env file."""
        env_content = []
        api_key_found = False

        # Read existing .env content
        if self.env_file.exists():
            env_content = self.env_file.read_text().splitlines()

        # Replace existing HIVE_API_KEY line or track if we need to add it
        for i, line in enumerate(env_content):
            if line.startswith(f"{self.api_key_var}="):
                env_content[i] = f"{self.api_key_var}={api_key}"
                api_key_found = True
                break

        # Add API key if it wasn't found
        if not api_key_found:
            env_content.append(f"{self.api_key_var}={api_key}")

        # Ensure AUTH_DISABLED is set to false if not present
        has_auth_disabled = any(
            line.startswith(f"{self.auth_disabled_var}=") for line in env_content
        )
        if not has_auth_disabled:
            env_content.append(f"{self.auth_disabled_var}=false")

        # Write back to file
        self.env_file.write_text("\n".join(env_content) + "\n")

    def _read_key_from_env(self) -> str | None:
        """Read API key from .env file."""
        if not self.env_file.exists():
            return None

        for line in self.env_file.read_text().splitlines():
            if line.startswith(f"{self.api_key_var}="):
                return line.split("=", 1)[1].strip()
        return None

    def _display_key_to_user(self, api_key: str) -> None:
        """Display generated API key to user."""
        logger.info("🔐 \n" + "=" * 60)
        logger.info("🔐 🔑 AUTOMAGIK HIVE - API KEY GENERATED")
        logger.info("🔐 " + "=" * 60)
        logger.info("🔐 A new API key has been generated and saved to .env:")
        logger.info(f"🔐 \nAPI Key: {api_key}")
        logger.info("🔐 \nUse this key in your API requests:")
        logger.info(f'🔐 curl -H "x-api-key: {api_key}" \\\\')
        from lib.config.settings import settings
        logger.info(f"🔐      http://localhost:{settings().hive_api_port}/api/v1/health")
        logger.info("🔐 \n" + "=" * 60 + "\n")

    def regenerate_key(self) -> str:
        """Generate and save a new API key."""
        api_key = self._generate_secure_key()
        self._save_key_to_env(api_key)
        self._display_key_to_user(api_key)

        # Update environment for current session
        os.environ[self.api_key_var] = api_key
        return api_key

    def get_current_key(self) -> str | None:
        """Get the current API key without generating a new one."""
        return os.getenv(self.api_key_var) or self._read_key_from_env()
