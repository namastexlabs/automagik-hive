#!/usr/bin/env python3
"""
Credential Management Service for Automagik Hive.

SINGLE SOURCE OF TRUTH for all credential generation across the entire system.
Generates credentials ONCE during install and populates ALL 3 modes consistently.

DESIGN PRINCIPLES:
1. Generate credentials ONCE during installation
2. Share same DB user/password across all modes (security best practice)
3. SHARED DATABASE: All modes use postgres port 5532, different API ports
4. Schema separation: workspace(public)
5. Consistent API keys but with mode-specific prefixes for identification
6. Template-based environment file generation
7. Backward compatibility with existing Makefile and CLI installers
8. Container sharing: Single postgres container for all modes
"""

import secrets
from pathlib import Path
from urllib.parse import urlparse

from lib.auth.env_file_manager import EnvFileManager
from lib.logging import logger


class CredentialService:
    """SINGLE SOURCE OF TRUTH for all Automagik Hive credential management."""

    # Default ports (can be overridden by .env)
    DEFAULT_PORTS = {"postgres": 5532, "api": 8886}
    DEFAULT_BASE_PORTS = {
        "db": DEFAULT_PORTS["postgres"],
        "api": DEFAULT_PORTS["api"],
    }

    # Temporary compatibility - to be removed
    PORT_PREFIXES = {"workspace": ""}
    DATABASES = {"workspace": "hive"}
    CONTAINERS = {
        "workspace": {
            "postgres": "hive-postgres",
            "api": "hive-api",
        }
    }

    def __init__(
        self,
        project_root: Path | None = None,
        env_file: Path | None = None,
        env_manager: EnvFileManager | None = None,
    ) -> None:
        """
        Initialize credential service.

        Args:
            project_root: Project root directory (defaults to current working directory)
            env_file: Path to environment file (defaults to .env) - for backward compatibility
            env_manager: Optional env file manager instance for dependency injection
        """
        if env_manager is not None:
            self.env_manager = env_manager
        else:
            self.env_manager = EnvFileManager(
                project_root=project_root,
                env_file=env_file,
            )

        self.project_root = self.env_manager.project_root
        self.env_file = self.env_manager.primary_env_path
        self.master_env_file = self.env_manager.master_env_path
        self.postgres_user_var = "POSTGRES_USER"
        self.postgres_password_var = "POSTGRES_PASSWORD"  # noqa: S105
        self.postgres_db_var = "POSTGRES_DB"
        self.database_url_var = "HIVE_DATABASE_URL"
        self.api_key_var = "HIVE_API_KEY"

    def _refresh_env_paths(self) -> None:
        """Refresh cached env file paths from the manager."""
        self.env_file = self.env_manager.primary_env_path
        self.master_env_file = self.env_manager.master_env_path

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
        database_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"

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

    def generate_credentials(self) -> dict[str, str]:
        """
        Generate complete credential set for single-instance Automagik Hive.

        Returns:
            Dict containing all required credentials
        """
        logger.info("Generating credentials for Automagik Hive")

        # Generate secure PostgreSQL credentials
        user = self._generate_secure_token(16, safe_chars=True)
        password = self._generate_secure_token(16, safe_chars=True)

        # Use default ports
        postgres_port = self.DEFAULT_PORTS["postgres"]
        api_port = self.DEFAULT_PORTS["api"]

        # Create database URL
        database_url = f"postgresql+psycopg://{user}:{password}@localhost:{postgres_port}/hive"

        # Generate API key
        api_key = self.generate_hive_api_key()

        credentials = {
            "HIVE_POSTGRES_USER": user,
            "HIVE_POSTGRES_PASSWORD": password,
            "HIVE_POSTGRES_DB": "hive",
            "HIVE_POSTGRES_PORT": str(postgres_port),
            "HIVE_API_PORT": str(api_port),
            "HIVE_DATABASE_URL": database_url,
            "HIVE_API_KEY": api_key,
        }

        logger.info(
            "Credentials generated successfully", postgres_port=postgres_port, api_port=api_port, database="hive"
        )

        return credentials

    def extract_postgres_credentials_from_env(self) -> dict[str, str | None]:
        """
        Extract PostgreSQL credentials from .env file.

        Replicates Makefile extract_postgres_credentials_from_env function.

        Returns:
            Dict containing extracted credentials (may contain None values)
        """
        credentials = self.env_manager.extract_postgres_credentials(self.database_url_var)
        self._refresh_env_paths()
        return credentials

    def extract_hive_api_key_from_env(self) -> str | None:
        """
        Extract Hive API key from .env file.

        Replicates Makefile extract_hive_api_key_from_env function.

        Returns:
            API key if found, None otherwise
        """
        api_key = self.env_manager.extract_api_key(self.api_key_var)
        self._refresh_env_paths()
        return api_key

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
        updates: dict[str, str] = {}

        if postgres_creds and postgres_creds.get("url"):
            updates[self.database_url_var] = postgres_creds["url"]

        if api_key:
            updates[self.api_key_var] = api_key

        if not updates:
            logger.debug("No credential updates provided; skipping env write")
            return

        success = self.env_manager.update_values(
            updates,
            create_if_missing=create_if_missing,
        )

        if not success:
            logger.error(
                "Failed to persist credentials to env file",
                env_file=str(self.env_file),
            )
            return

        self._refresh_env_paths()
        logger.info("Credentials saved to .env file successfully")

    def sync_mcp_config_with_credentials(self, mcp_file: Path | None = None) -> None:
        """
        Update .mcp.json with current credentials.

        Replicates Makefile sync_mcp_config_with_credentials function.

        Args:
            mcp_file: Path to MCP config file (defaults to .mcp.json)
        """
        if mcp_file is None:
            import os

            mcp_config_path = os.getenv("HIVE_MCP_CONFIG_PATH", ".mcp.json")
            if os.path.isabs(mcp_config_path):
                mcp_file = Path(mcp_config_path)
            else:
                mcp_file = self.project_root / mcp_config_path

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

                # Check if HIVE_API_KEY exists
                if re.search(pattern, mcp_content):
                    # Update existing API key
                    mcp_content = re.sub(pattern, replacement, mcp_content)
                else:
                    # Add API key to the first server's env section if it exists
                    env_pattern = r'("env":\s*\{[^}]*)'
                    env_replacement = r'\1,\n        "HIVE_API_KEY": "' + api_key + '"'
                    if re.search(env_pattern, mcp_content):
                        mcp_content = re.sub(env_pattern, env_replacement, mcp_content)

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

            results["postgres_url_valid"] = postgres_creds.get("url") is not None and postgres_creds["url"].startswith(
                "postgresql+psycopg://"
            )

        if api_key:
            # Validate API key
            results["api_key_valid"] = (
                api_key is not None and api_key.startswith("hive_") and len(api_key) > 37  # hive_ (5) + token (32+)
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
            token = secrets.token_urlsafe(length + 8)  # Generate extra to account for trimming
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
            "postgres_configured": bool(postgres_creds["user"] and postgres_creds["password"]),
            "api_key_configured": bool(api_key),
            "postgres_credentials": {
                "has_user": bool(postgres_creds["user"]),
                "has_password": bool(postgres_creds["password"]),
                "has_database": bool(postgres_creds["database"]),
                "has_url": bool(postgres_creds["url"]),
            },
            "api_key_format_valid": bool(api_key and api_key.startswith("hive_")) if api_key else False,
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
        sync_mcp: bool = False,
    ) -> dict[str, str]:
        """
        Generate complete set of credentials for new workspace.

        Args:
            postgres_host: PostgreSQL host
            postgres_port: PostgreSQL port
            postgres_database: PostgreSQL database name
            sync_mcp: Whether to sync credentials to MCP config (default: False)

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

        # Update MCP config if requested
        if sync_mcp:
            try:
                self.sync_mcp_config_with_credentials()
            except Exception as e:
                logger.warning("MCP sync failed but continuing with credential generation", error=str(e))

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

    def extract_base_ports_from_env(self) -> dict[str, int]:
        """
        Extract base ports from .env file or return defaults.

        Returns:
            Dict containing base ports for db and api
        """
        ports = self.env_manager.extract_base_ports(
            self.DEFAULT_BASE_PORTS,
            self.database_url_var,
            "HIVE_API_PORT",
        )
        self._refresh_env_paths()
        logger.info("Base ports extracted", ports=ports)
        return ports

    def calculate_ports(self, mode: str, base_ports: dict[str, int]) -> dict[str, int]:
        """Compatibility method - returns base ports for workspace."""
        if mode != "workspace":
            raise ValueError(f"Only 'workspace' mode is supported, got: {mode}")
        return base_ports.copy()

    def derive_mode_credentials(self, master_credentials: dict[str, str], mode: str) -> dict[str, str]:
        """
        Derive mode-specific credentials from master credentials.

        SHARED DATABASE APPROACH:
        - SHARED: user, password, database name (hive), postgres port (5532)
        - DIFFERENT: API ports, API key prefixes, schema namespaces

        Args:
            master_credentials: Master credentials from generate_master_credentials()
            mode: Mode name (workspace)

        Returns:
            Dict containing mode-specific credentials with schema separation
        """
        if mode not in self.PORT_PREFIXES:
            raise ValueError(f"Unknown mode: {mode}. Valid modes: {list(self.PORT_PREFIXES.keys())}")

        # Calculate ports dynamically
        base_ports = self.extract_base_ports_from_env()
        mode_ports = self.calculate_ports(mode, base_ports)
        database_name = self.DATABASES[mode]  # All modes use 'hive' database

        # Create mode-specific API key with identifier prefix
        api_key = f"hive_{mode}_{master_credentials['api_key_base']}"

        # Create database URL with schema separation for non-workspace modes
        if mode == "workspace":
            # Workspace uses default public schema
            database_url = (
                f"postgresql+psycopg://{master_credentials['postgres_user']}:"
                f"{master_credentials['postgres_password']}@localhost:"
                f"{mode_ports['db']}/{database_name}"
            )
        else:
            # Non-workspace modes would use schema-specific connection
            database_url = (
                f"postgresql+psycopg://{master_credentials['postgres_user']}:"
                f"{master_credentials['postgres_password']}@localhost:"
                f"{mode_ports['db']}/{database_name}?options=-csearch_path={mode}"
            )

        mode_credentials = {
            "postgres_user": master_credentials["postgres_user"],
            "postgres_password": master_credentials["postgres_password"],
            "postgres_database": database_name,  # All modes use 'hive' database
            "postgres_host": "localhost",
            "postgres_port": str(mode_ports["db"]),  # Shared postgres port
            "api_port": str(mode_ports["api"]),
            "api_key": api_key,
            "database_url": database_url,
            "mode": mode,
            "schema": "public" if mode == "workspace" else mode,  # Schema separation
        }

        logger.info(
            f"Derived {mode} credentials for shared database approach",
            database=database_name,
            shared_db_port=mode_ports["db"],
            api_port=mode_ports["api"],
            schema=mode_credentials["schema"],
        )

        return mode_credentials

    def get_database_url_with_schema(self, mode: str) -> str:
        """Generate database URL with appropriate schema for mode."""
        base_url = self.extract_postgres_credentials_from_env()["url"]

        if not base_url:
            raise ValueError(f"No database URL found in .env file for mode {mode}")

        if mode == "workspace":
            return base_url  # Uses public schema (default)
        else:
            # Add schema search path for agent/genie modes
            separator = "&" if "?" in base_url else "?"
            return f"{base_url}{separator}options=-csearch_path={mode}"

    def ensure_schema_exists(self, mode: str):
        """Ensure the appropriate schema exists for the mode."""
        if mode != "workspace":
            # Schema creation should integrate with Agno framework
            # This is a placeholder for now - actual implementation should
            # integrate with the database initialization system
            logger.info(f"Schema creation for {mode} mode - integrate with Agno framework")

    def detect_existing_containers(self) -> dict[str, bool]:
        """Detect existing Docker containers for shared approach."""
        import subprocess

        containers_status = {}

        for _mode, container_info in self.CONTAINERS.items():
            for _service, container_name in container_info.items():
                try:
                    # Check if container exists and is running
                    result = subprocess.run(
                        ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    containers_status[container_name] = container_name in result.stdout
                except Exception as e:
                    logger.warning(f"Failed to check container {container_name}", error=str(e))
                    containers_status[container_name] = False

        logger.info("Container detection results", containers=containers_status)
        return containers_status

    def migrate_to_shared_database(self):
        """Migrate from separate database approach to shared database with schemas."""
        logger.info("Checking for migration to shared database approach")

        # Detect existing separate containers
        existing_containers = self.detect_existing_containers()

        # Check for old container names that need migration
        old_containers = []
        needs_migration = any(
            container
            for container in old_containers
            if container in existing_containers and existing_containers[container]
        )

        if needs_migration:
            logger.info("Migration needed from separate database containers to shared approach")
            # Offer migration to shared approach
            # Preserve existing data during migration
            # This should be implemented with proper data migration logic
            logger.warning("Migration logic not yet implemented - manual migration required")
        else:
            logger.info("No migration needed - using shared database approach")

    def generate_master_credentials(self) -> dict[str, str]:
        """
        Generate the SINGLE SET of master credentials used across all modes.

        This is the SINGLE SOURCE OF TRUTH - called ONCE during installation.

        Returns:
            Dict containing master credentials that will be shared across all modes
        """
        logger.info("Generating MASTER credentials (single source of truth)")

        # Generate secure master credentials
        master_user = self._generate_secure_token(16, safe_chars=True)
        master_password = self._generate_secure_token(16, safe_chars=True)
        master_api_key_base = secrets.token_urlsafe(32)

        master_credentials = {
            "postgres_user": master_user,
            "postgres_password": master_password,
            "api_key_base": master_api_key_base,
        }

        logger.info(
            "Master credentials generated",
            user_length=len(master_user),
            password_length=len(master_password),
            api_key_base_length=len(master_api_key_base),
        )

        return master_credentials

    def install_all_modes(
        self, modes: list[str] = None, force_regenerate: bool = False, sync_mcp: bool = False
    ) -> dict[str, dict[str, str]]:
        """
        SIMPLIFIED INSTALLATION FUNCTION: Install credentials for single instance.

        This is maintained for backward compatibility but now generates
        credentials for the single hive instance.

        Args:
            modes: Ignored - kept for backward compatibility
            force_regenerate: Force regeneration even if credentials exist
            sync_mcp: Whether to sync credentials to MCP config (default: False)

        Returns:
            Dict with single "workspace" entry for backward compatibility
        """
        logger.info("Installing credentials for Automagik Hive")

        # Check if credentials exist and should be reused
        existing_creds = self.extract_postgres_credentials_from_env()
        existing_api_key = self.extract_hive_api_key_from_env()

        if existing_creds.get("user") and existing_creds.get("password") and existing_api_key and not force_regenerate:
            logger.info("Reusing existing credentials")
            # Format existing credentials for backward compatibility
            credentials = {
                "postgres_user": existing_creds["user"],
                "postgres_password": existing_creds["password"],
                "postgres_database": existing_creds.get("database", "hive"),
                "postgres_host": existing_creds.get("host", "localhost"),
                "postgres_port": existing_creds.get("port", "5532"),
                "api_key": existing_api_key,
            }
        else:
            logger.info("Generating new credentials")
            # Generate new simplified credentials
            new_creds = self.generate_credentials()

            normalized_master_creds = self._normalize_master_credentials_payload(new_creds)

            # Save credentials to .env file
            self._save_master_credentials(normalized_master_creds)

            # Format for backward compatibility
            credentials = {
                "postgres_user": normalized_master_creds["postgres_user"],
                "postgres_password": normalized_master_creds["postgres_password"],
                "postgres_database": "hive",
                "postgres_host": "localhost",
                "postgres_port": new_creds["HIVE_POSTGRES_PORT"],
                "api_key": new_creds["HIVE_API_KEY"],
            }

        # Return in backward-compatible format with "workspace" key
        all_mode_credentials = {"workspace": credentials}

        # Update MCP config if requested (once after all modes are set up)
        if sync_mcp:
            try:
                self.sync_mcp_config_with_credentials()
            except Exception as e:
                logger.warning("MCP sync failed but continuing with credential installation", error=str(e))

        logger.info(f"Credential installation complete for modes: {modes}")
        return all_mode_credentials

    def _extract_existing_master_credentials(self) -> dict[str, str] | None:
        """Extract existing master credentials from main .env file."""
        if not self.master_env_file.exists():
            return None

        try:
            env_content = self.master_env_file.read_text()

            # Extract database URL
            postgres_user = None
            postgres_password = None
            api_key_base = None

            for line in env_content.splitlines():
                line = line.strip()
                if line.startswith("HIVE_DATABASE_URL="):
                    url = line.split("=", 1)[1].strip()
                    if "postgresql+psycopg://" in url:
                        parsed = urlparse(url)
                        if parsed.username and parsed.password:
                            postgres_user = parsed.username
                            postgres_password = parsed.password

                elif line.startswith("HIVE_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    if api_key.startswith("hive_"):
                        # Extract base from main API key (remove hive_ prefix)
                        api_key_base = api_key[5:]  # Remove "hive_" prefix

            # Validate credentials exist and are not placeholders
            if postgres_user and postgres_password and api_key_base:
                # Check for common placeholder patterns
                placeholder_patterns = [
                    "your-secure-password-here",
                    "your-hive-api-key-here",
                    "your-password",
                    "change-me",
                    "placeholder",
                    "example",
                    "template",
                    "replace-this",
                ]

                # Check if any credential contains placeholder patterns
                if any(pattern in postgres_password.lower() for pattern in placeholder_patterns):
                    logger.info("Detected placeholder password in main .env file - forcing credential regeneration")
                    return None

                if any(pattern in api_key_base.lower() for pattern in placeholder_patterns):
                    logger.info("Detected placeholder API key in main .env file - forcing credential regeneration")
                    return None

                return {
                    "postgres_user": postgres_user,
                    "postgres_password": postgres_password,
                    "api_key_base": api_key_base,
                }

        except Exception as e:
            logger.error("Failed to extract existing master credentials", error=str(e))

        return None

    def _normalize_master_credentials_payload(self, master_credentials: dict[str, str] | None) -> dict[str, str]:
        """Normalize incoming payloads to the master credential schema."""
        if not master_credentials:
            raise ValueError("Master credentials payload cannot be empty")

        postgres_user = master_credentials.get("postgres_user") or master_credentials.get("HIVE_POSTGRES_USER")
        postgres_password = master_credentials.get("postgres_password") or master_credentials.get(
            "HIVE_POSTGRES_PASSWORD"
        )

        api_key_base = master_credentials.get("api_key_base")
        if not api_key_base:
            raw_api_key = master_credentials.get("HIVE_API_KEY") or master_credentials.get("api_key")
            if raw_api_key and raw_api_key.startswith("hive_"):
                api_key_base = raw_api_key[len("hive_") :]
            else:
                api_key_base = raw_api_key

        normalized = {
            "postgres_user": postgres_user,
            "postgres_password": postgres_password,
            "api_key_base": api_key_base,
        }

        missing = [key for key, value in normalized.items() if not value]
        if missing:
            raise ValueError("Missing required master credential fields after normalization: " + ", ".join(missing))

        return normalized

    def _save_master_credentials(self, master_credentials: dict[str, str]) -> None:
        """Save master credentials to main .env file."""
        logger.info("Saving master credentials to main .env file")
        master_credentials = self._normalize_master_credentials_payload(master_credentials)

        primary_exists = self.env_manager.primary_env_path.exists()
        alias_exists = self.env_manager.alias_env_path.exists()

        if not primary_exists and alias_exists:
            self.env_manager.sync_alias()
        elif not primary_exists and not alias_exists:
            env_example = self.project_root / ".env.example"
            try:
                if env_example.exists():
                    logger.info("Creating .env from .env.example template with comprehensive configuration")
                    content = env_example.read_text()
                else:
                    logger.warning(".env.example not found, creating minimal .env file")
                    content = self._get_base_env_template()
                self.env_manager.primary_env_path.write_text(content)
                self.env_manager.sync_alias()
            except OSError as error:
                logger.error(
                    "Failed to hydrate master env file",
                    file=str(self.env_manager.primary_env_path),
                    error=str(error),
                )

        # Generate main workspace credentials for main .env
        main_db_url = (
            f"postgresql+psycopg://{master_credentials['postgres_user']}:"
            f"{master_credentials['postgres_password']}@localhost:5532/hive"
        )
        main_api_key = f"hive_{master_credentials['api_key_base']}"
        updates = {
            "HIVE_DATABASE_URL": main_db_url,
            "HIVE_API_KEY": main_api_key,
        }

        success = self.env_manager.update_values(updates, create_if_missing=True)
        if success:
            logger.info("Master credentials saved to .env with all comprehensive configurations from template")
        else:
            logger.error("Failed to persist master credentials to env file")

        self._refresh_env_paths()

    def _get_base_env_template(self) -> str:
        """Get base environment template for new installations."""
        return """# =========================================================================
# ⚡ AUTOMAGIK HIVE - MAIN CONFIGURATION
# =========================================================================
HIVE_ENVIRONMENT=development
HIVE_LOG_LEVEL=INFO
AGNO_LOG_LEVEL=INFO

HIVE_API_HOST=0.0.0.0
HIVE_API_PORT=8886
HIVE_API_WORKERS=1

# Generated by Credential Service
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive
HIVE_API_KEY=hive_generated_key

HIVE_CORS_ORIGINS=http://localhost:3000,http://localhost:8886
HIVE_AUTH_DISABLED=true
HIVE_DEV_MODE=true
HIVE_DEFAULT_MODEL=gpt-4.1-mini
"""

    def _create_mode_env_file(self, mode: str, credentials: dict[str, str]) -> None:
        """Create environment file for a specific mode."""
        if mode == "workspace":
            # Workspace uses main .env file (already created by _save_master_credentials)
            logger.info("Workspace uses main .env file (already created)")
            return

        env_file = self.project_root / f".env.{mode}"
        logger.info(f"Creating {mode} environment file", file=str(env_file))

        # Create mode-specific .env file content
        env_content = f"""# =========================================================================
# ⚡ AUTOMAGIK HIVE - {mode.upper()} MODE CONFIGURATION
# =========================================================================
HIVE_ENVIRONMENT=development
HIVE_LOG_LEVEL=INFO
AGNO_LOG_LEVEL=INFO

# Server & API Configuration
HIVE_API_HOST=0.0.0.0
HIVE_API_PORT={credentials["api_port"]}
HIVE_API_WORKERS=1

# Database Configuration (Shared Credentials)
HIVE_DATABASE_URL={credentials["database_url"]}
POSTGRES_HOST={credentials["postgres_host"]}
POSTGRES_PORT=5532
POSTGRES_USER={credentials["postgres_user"]}
POSTGRES_PASSWORD={credentials["postgres_password"]}
POSTGRES_DB={credentials["postgres_database"]}

# Security & Authentication
HIVE_API_KEY={credentials["api_key"]}
HIVE_CORS_ORIGINS=http://localhost:3000,http://localhost:{credentials["api_port"]}
HIVE_AUTH_DISABLED=true

# Development Mode Settings
HIVE_DEV_MODE=true
HIVE_ENABLE_METRICS=true
HIVE_AGNO_MONITOR=false
HIVE_DEFAULT_MODEL=gpt-4.1-mini
"""

        env_file.write_text(env_content)
        logger.info(f"Created {mode} environment file", file=str(env_file))
