#!/usr/bin/env python3
"""
Credential Management Service for Automagik Hive.

Integrates existing Makefile credential generation patterns with CLI system.
Provides secure credential generation for PostgreSQL, API keys, and database URLs.
"""

import secrets
from pathlib import Path
from urllib.parse import urlparse

from lib.logging import logger


class CredentialService:
    """Service for generating and managing secure credentials."""

    def __init__(self, env_file: Path | None = None) -> None:
        """
        Initialize credential service.

        Args:
            env_file: Path to environment file (defaults to .env)
        """
        self.env_file = env_file or Path(".env")
        self.postgres_user_var = "POSTGRES_USER"
        self.postgres_password_var = "POSTGRES_PASSWORD"
        self.postgres_db_var = "POSTGRES_DB"
        self.database_url_var = "HIVE_DATABASE_URL"
        self.api_key_var = "HIVE_API_KEY"

    def generate_postgres_credentials(
        self, host: str = "localhost", port: int = 5532, database: str = "hive"
    ) -> dict[str, str]:
        """
        Generate secure PostgreSQL credentials.

        Replicates Makefile generate_postgres_credentials function:
        - PostgreSQL User: Random base64 string (16 chars)
        - PostgreSQL Password: Random base64 string (16 chars)
        - Database URL: postgresql+psycopg://user:pass@host:port/database

        Args:
            host: Database host (default: localhost)
            port: Database port (default: 5532)
            database: Database name (default: hive)

        Returns:
            Dict containing user, password, database, and full URL
        """
        logger.info("Generating secure PostgreSQL credentials")

        # Generate secure random credentials (16 chars base64, no special chars)
        user = self._generate_secure_token(16, safe_chars=True)
        password = self._generate_secure_token(16, safe_chars=True)

        # Construct database URL
        database_url = (
            f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"
        )

        credentials = {
            "user": user,
            "password": password,
            "database": database,
            "host": host,
            "port": str(port),
            "url": database_url,
        }

        logger.info(
            "PostgreSQL credentials generated",
            user_length=len(user),
            password_length=len(password),
            database=database,
            host=host,
            port=port,
        )

        return credentials

    def generate_hive_api_key(self) -> str:
        """
        Generate secure Hive API key.

        Replicates Makefile generate_hive_api_key function:
        - API Key: hive_[32-char secure token]

        Returns:
            Generated API key with hive_ prefix
        """
        logger.info("Generating secure Hive API key")

        # Generate 32-char secure token (URL-safe base64)
        token = secrets.token_urlsafe(32)
        api_key = f"hive_{token}"

        logger.info("Hive API key generated", key_length=len(api_key))

        return api_key

    def generate_agent_credentials(
        self, port: int = 35532, database: str = "hive_agent"
    ) -> dict[str, str]:
        """
        Generate agent-specific credentials with unified user/pass from main.

        Replicates Makefile use_unified_credentials_for_agent function:
        - Reuses main PostgreSQL user/password
        - Changes port and database name

        Args:
            port: Agent database port (default: 35532)
            database: Agent database name (default: hive_agent)

        Returns:
            Dict containing agent credentials
        """
        logger.info("Generating agent credentials with unified approach")

        # Get main credentials
        main_creds = self.extract_postgres_credentials_from_env()

        if main_creds["user"] and main_creds["password"]:
            # Reuse main credentials with different port/database
            agent_creds = {
                "user": main_creds["user"],
                "password": main_creds["password"],
                "database": database,
                "host": "localhost",
                "port": str(port),
                "url": f"postgresql+psycopg://{main_creds['user']}:{main_creds['password']}@localhost:{port}/{database}",
            }

            logger.info(
                "Agent credentials generated using unified approach",
                database=database,
                port=port,
            )
        else:
            # Generate new credentials if main not available
            agent_creds = self.generate_postgres_credentials(
                host="localhost", port=port, database=database
            )

            logger.info("Agent credentials generated (new credentials)")

        return agent_creds

    def extract_postgres_credentials_from_env(self) -> dict[str, str | None]:
        """
        Extract PostgreSQL credentials from .env file.

        Replicates Makefile extract_postgres_credentials_from_env function.

        Returns:
            Dict containing extracted credentials (may contain None values)
        """
        credentials = {
            "user": None,
            "password": None,
            "database": None,
            "host": None,
            "port": None,
            "url": None,
        }

        if not self.env_file.exists():
            logger.warning("Environment file not found", env_file=str(self.env_file))
            return credentials

        try:
            env_content = self.env_file.read_text()

            # Look for HIVE_DATABASE_URL
            for line in env_content.splitlines():
                line = line.strip()
                if line.startswith(f"{self.database_url_var}="):
                    url = line.split("=", 1)[1].strip()
                    if url and "postgresql+psycopg://" in url:
                        credentials["url"] = url

                        # Parse URL to extract components
                        parsed = urlparse(url)
                        if parsed.username:
                            credentials["user"] = parsed.username
                        if parsed.password:
                            credentials["password"] = parsed.password
                        if parsed.hostname:
                            credentials["host"] = parsed.hostname
                        if parsed.port:
                            credentials["port"] = str(parsed.port)
                        if parsed.path and len(parsed.path) > 1:
                            credentials["database"] = parsed.path[
                                1:
                            ]  # Remove leading /

                        logger.info("PostgreSQL credentials extracted from .env")
                        break

        except Exception as e:
            logger.error("Failed to extract PostgreSQL credentials", error=str(e))

        return credentials

    def extract_hive_api_key_from_env(self) -> str | None:
        """
        Extract Hive API key from .env file.

        Replicates Makefile extract_hive_api_key_from_env function.

        Returns:
            API key if found, None otherwise
        """
        if not self.env_file.exists():
            logger.warning("Environment file not found", env_file=str(self.env_file))
            return None

        try:
            env_content = self.env_file.read_text()

            for line in env_content.splitlines():
                line = line.strip()
                if line.startswith(f"{self.api_key_var}="):
                    api_key = line.split("=", 1)[1].strip()
                    if api_key:
                        logger.info("Hive API key extracted from .env")
                        return api_key

        except Exception as e:
            logger.error("Failed to extract Hive API key", error=str(e))

        return None

    def save_credentials_to_env(
        self,
        postgres_creds: dict[str, str] | None = None,
        api_key: str | None = None,
        create_if_missing: bool = True,
    ) -> None:
        """
        Save credentials to .env file.

        Args:
            postgres_creds: PostgreSQL credentials dict
            api_key: Hive API key
            create_if_missing: Create .env file if it doesn't exist
        """
        logger.info("Saving credentials to .env file")

        env_content = []
        postgres_updated = False
        api_key_updated = False

        # Read existing content if file exists
        if self.env_file.exists():
            env_content = self.env_file.read_text().splitlines()
        elif not create_if_missing:
            logger.error("Environment file does not exist and create_if_missing=False")
            return

        # Update PostgreSQL database URL
        if postgres_creds:
            for i, line in enumerate(env_content):
                if line.startswith(f"{self.database_url_var}="):
                    env_content[i] = f"{self.database_url_var}={postgres_creds['url']}"
                    postgres_updated = True
                    break

            if not postgres_updated:
                env_content.append(f"{self.database_url_var}={postgres_creds['url']}")

        # Update API key
        if api_key:
            for i, line in enumerate(env_content):
                if line.startswith(f"{self.api_key_var}="):
                    env_content[i] = f"{self.api_key_var}={api_key}"
                    api_key_updated = True
                    break

            if not api_key_updated:
                env_content.append(f"{self.api_key_var}={api_key}")

        # Write back to file
        try:
            self.env_file.write_text("\n".join(env_content) + "\n")
            logger.info("Credentials saved to .env file successfully")
        except Exception as e:
            logger.error("Failed to save credentials to .env file", error=str(e))
            raise

    def sync_mcp_config_with_credentials(self, mcp_file: Path | None = None) -> None:
        """
        Update .mcp.json with current credentials.

        Replicates Makefile sync_mcp_config_with_credentials function.

        Args:
            mcp_file: Path to MCP config file (defaults to .mcp.json)
        """
        mcp_file = mcp_file or Path(".mcp.json")

        if not mcp_file.exists():
            logger.warning("MCP config file not found", mcp_file=str(mcp_file))
            return

        # Extract current credentials
        postgres_creds = self.extract_postgres_credentials_from_env()
        api_key = self.extract_hive_api_key_from_env()

        if not (postgres_creds["user"] and postgres_creds["password"] and api_key):
            logger.warning("Cannot update MCP config - missing credentials")
            return

        try:
            mcp_content = mcp_file.read_text()

            # Update PostgreSQL connection string
            if postgres_creds["url"]:
                # Replace any existing PostgreSQL connection string
                import re

                pattern = r"postgresql\+psycopg://[^@]*@"
                replacement = f"postgresql+psycopg://{postgres_creds['user']}:{postgres_creds['password']}@"
                mcp_content = re.sub(pattern, replacement, mcp_content)

            # Update API key
            if api_key:
                import re

                pattern = r'"HIVE_API_KEY":\s*"[^"]*"'
                replacement = f'"HIVE_API_KEY": "{api_key}"'
                mcp_content = re.sub(pattern, replacement, mcp_content)

            mcp_file.write_text(mcp_content)
            logger.info("MCP config updated with current credentials")

        except Exception as e:
            logger.error("Failed to update MCP config", error=str(e))

    def validate_credentials(
        self, postgres_creds: dict[str, str] | None = None, api_key: str | None = None
    ) -> dict[str, bool]:
        """
        Validate credential format and security.

        Args:
            postgres_creds: PostgreSQL credentials to validate
            api_key: API key to validate

        Returns:
            Dict with validation results
        """
        results = {}

        if postgres_creds:
            # Validate PostgreSQL credentials
            results["postgres_user_valid"] = (
                postgres_creds.get("user") is not None
                and len(postgres_creds["user"]) >= 12
                and postgres_creds["user"].isalnum()
            )

            results["postgres_password_valid"] = (
                postgres_creds.get("password") is not None
                and len(postgres_creds["password"]) >= 12
                and postgres_creds["password"].isalnum()
            )

            results["postgres_url_valid"] = postgres_creds.get(
                "url"
            ) is not None and postgres_creds["url"].startswith("postgresql+psycopg://")

        if api_key:
            # Validate API key
            results["api_key_valid"] = (
                api_key is not None
                and api_key.startswith("hive_")
                and len(api_key) > 37  # hive_ (5) + token (32+)
            )

        logger.info("Credential validation completed", results=results)
        return results

    def _generate_secure_token(self, length: int = 16, safe_chars: bool = False) -> str:
        """
        Generate cryptographically secure random token.

        Args:
            length: Desired token length
            safe_chars: If True, generate base64 without special characters

        Returns:
            Secure random token
        """
        if safe_chars:
            # Use openssl-like approach from Makefile
            # Generate base64 and remove special characters, trim to length
            token = secrets.token_urlsafe(
                length + 8
            )  # Generate extra to account for trimming
            # Remove URL-safe characters that might cause issues
            token = token.replace("-", "").replace("_", "")
            return token[:length]
        return secrets.token_urlsafe(length)

    def get_credential_status(self) -> dict[str, any]:
        """
        Get current status of all credentials.

        Returns:
            Dict with credential status information
        """
        postgres_creds = self.extract_postgres_credentials_from_env()
        api_key = self.extract_hive_api_key_from_env()

        status = {
            "env_file_exists": self.env_file.exists(),
            "postgres_configured": bool(
                postgres_creds["user"] and postgres_creds["password"]
            ),
            "api_key_configured": bool(api_key),
            "postgres_credentials": {
                "has_user": bool(postgres_creds["user"]),
                "has_password": bool(postgres_creds["password"]),
                "has_database": bool(postgres_creds["database"]),
                "has_url": bool(postgres_creds["url"]),
            },
            "api_key_format_valid": bool(api_key and api_key.startswith("hive_"))
            if api_key
            else False,
        }

        # Validate credentials if they exist
        if postgres_creds["user"] or api_key:
            validation = self.validate_credentials(postgres_creds, api_key)
            status["validation"] = validation

        return status

    def setup_complete_credentials(
        self,
        postgres_host: str = "localhost",
        postgres_port: int = 5532,
        postgres_database: str = "hive",
    ) -> dict[str, str]:
        """
        Generate complete set of credentials for new workspace.

        Args:
            postgres_host: PostgreSQL host
            postgres_port: PostgreSQL port
            postgres_database: PostgreSQL database name

        Returns:
            Dict with all generated credentials
        """
        logger.info("Setting up complete credentials for new workspace")

        # Generate PostgreSQL credentials
        postgres_creds = self.generate_postgres_credentials(
            host=postgres_host, port=postgres_port, database=postgres_database
        )

        # Generate API key
        api_key = self.generate_hive_api_key()

        # Save to .env file
        self.save_credentials_to_env(postgres_creds, api_key)

        # Update MCP config if available
        self.sync_mcp_config_with_credentials()

        complete_creds = {
            "postgres_user": postgres_creds["user"],
            "postgres_password": postgres_creds["password"],
            "postgres_database": postgres_creds["database"],
            "postgres_host": postgres_creds["host"],
            "postgres_port": postgres_creds["port"],
            "postgres_url": postgres_creds["url"],
            "api_key": api_key,
        }

        logger.info(
            "Complete credentials setup finished",
            postgres_database=postgres_database,
            postgres_port=postgres_port,
        )

        return complete_creds
