#!/usr/bin/env python3
"""
Credential Management Service for Automagik Hive.

SINGLE SOURCE OF TRUTH for all credential generation across the entire system.
Generates credentials ONCE during install and populates ALL 3 modes consistently.

DESIGN PRINCIPLES:
1. Generate credentials ONCE during installation
2. Share same DB user/password across all modes (security best practice)  
3. SHARED DATABASE: All modes use postgres port 5532, different API ports
4. Schema separation: workspace(public), agent(agent schema), genie(genie schema)
5. Consistent API keys but with mode-specific prefixes for identification
6. Template-based environment file generation
7. Backward compatibility with existing Makefile and CLI installers
8. Container sharing: Single postgres container for all modes
"""

import secrets
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

from lib.logging import logger


class CredentialService:
    """SINGLE SOURCE OF TRUTH for all Automagik Hive credential management."""
    
    # Default base ports (can be overridden by .env)
    DEFAULT_BASE_PORTS = {"db": 5532, "api": 8886}
    
    # Port prefixes for each mode
    PORT_PREFIXES = {
        "workspace": "",      # No prefix - use base ports
        "agent": "3",         # 3 prefix: shared postgres 5532, API 38886  
        "genie": "4"          # 4 prefix: shared postgres 5532, API 45886
    }
    
    # Database names per mode - ALL USE SHARED DATABASE WITH SCHEMA SEPARATION
    DATABASES = {
        "workspace": "hive",    # All modes use same database  
        "agent": "hive",        # Same database, different schema
        "genie": "hive"         # Same database, different schema
    }
    
    # Container names for shared approach
    CONTAINERS = {
        "agent": {
            "postgres": "hive-postgres-shared",  # Shared container
            "api": "hive-agent-dev-server"
        },
        "workspace": {
            "postgres": "hive-postgres-shared"   # Same shared container
        }
    }

    def __init__(self, project_root: Path = None, env_file: Path = None) -> None:
        """
        Initialize credential service.

        Args:
            project_root: Project root directory (defaults to current working directory)
            env_file: Path to environment file (defaults to .env) - for backward compatibility
        """
        # Handle backward compatibility
        if env_file is not None and project_root is None:
            # Legacy usage: CredentialService(env_file=Path(".env"))
            self.project_root = env_file.parent if env_file.parent != Path(".") else Path.cwd()
            self.master_env_file = env_file
        else:
            # New usage: CredentialService(project_root=Path("/path"))
            self.project_root = project_root or Path.cwd()
            self.master_env_file = self.project_root / ".env"
        
        # Legacy support for existing API
        self.env_file = self.master_env_file
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
        self, port: int = 5532, database: str = "hive"
    ) -> dict[str, str]:
        """
        Generate agent-specific credentials with unified user/pass from main.
        
        SHARED DATABASE APPROACH: Uses same postgres port and database as main
        Only schema separation differentiates agent from workspace mode

        Replicates Makefile use_unified_credentials_for_agent function:
        - Reuses main PostgreSQL user/password
        - Uses shared database and port with schema separation

        Args:
            port: Shared database port (default: 5532)
            database: Shared database name (default: hive)

        Returns:
            Dict containing agent credentials with schema separation
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
        postgres_found = False
        api_key_found = False

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
                    postgres_found = True
                    break

            if not postgres_found:
                env_content.append(f"{self.database_url_var}={postgres_creds['url']}")

        # Update API key
        if api_key:
            for i, line in enumerate(env_content):
                if line.startswith(f"{self.api_key_var}="):
                    env_content[i] = f"{self.api_key_var}={api_key}"
                    api_key_found = True
                    break

            if not api_key_found:
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

    def extract_base_ports_from_env(self) -> Dict[str, int]:
        """
        Extract base ports from .env file or return defaults.
        
        Returns:
            Dict containing base ports for db and api
        """
        base_ports = self.DEFAULT_BASE_PORTS.copy()
        
        if not self.master_env_file.exists():
            logger.debug("No .env file found, using default base ports", defaults=base_ports)
            return base_ports
        
        try:
            env_content = self.master_env_file.read_text()
            
            for line in env_content.splitlines():
                line = line.strip()
                if line.startswith("HIVE_DATABASE_URL="):
                    url = line.split("=", 1)[1].strip()
                    if "postgresql+psycopg://" in url:
                        parsed = urlparse(url)
                        if parsed.port:
                            base_ports["db"] = parsed.port
                            logger.debug("Found custom database port in .env", port=parsed.port)
                            
                elif line.startswith("HIVE_API_PORT="):
                    port = line.split("=", 1)[1].strip()
                    try:
                        base_ports["api"] = int(port)
                        logger.debug("Found custom API port in .env", port=port)
                    except ValueError:
                        logger.warning("Invalid API port in .env, using default", invalid_port=port)
                        
        except Exception as e:
            logger.error("Failed to extract base ports from .env", error=str(e))
            
        logger.info("Base ports extracted", ports=base_ports)
        return base_ports
    
    def calculate_ports(self, mode: str, base_ports: Dict[str, int]) -> Dict[str, int]:
        """
        Calculate ports by adding prefix to base ports.
        
        PREFIXED DATABASE APPROACH: Each mode uses prefixed database and API ports
        Agent uses 35532, Genie uses 45532, Workspace uses base 5532
        
        Args:
            mode: Mode name (workspace, agent, genie)
            base_ports: Base ports dict with 'db' and 'api' keys
            
        Returns:
            Dict containing calculated ports for the mode
        """
        if mode not in self.PORT_PREFIXES:
            raise ValueError(f"Unknown mode: {mode}. Valid modes: {list(self.PORT_PREFIXES.keys())}")
            
        prefix = self.PORT_PREFIXES[mode]
        
        if not prefix:
            # No prefix for workspace mode
            return base_ports.copy()
        
        # Prefixed database ports for mode separation
        calculated_ports = {
            "db": int(f"{prefix}{base_ports['db']}"),  # Prefixed postgres port
            "api": int(f"{prefix}{base_ports['api']}")  # Prefixed API port
        }
        
        logger.debug(
            "Calculated ports for prefixed database approach", 
            mode=mode, prefix=prefix, ports=calculated_ports, 
            base_postgres_port=base_ports["db"]
        )
        return calculated_ports
    
    def get_deployment_ports(self) -> Dict[str, Dict[str, int]]:
        """
        Get deployment ports for all modes using dynamic base ports.
        
        Returns:
            Dict mapping mode names to their port configurations
        """
        base_ports = self.extract_base_ports_from_env()
        
        deployment_ports = {}
        for mode in self.PORT_PREFIXES:
            deployment_ports[mode] = self.calculate_ports(mode, base_ports)
            
        logger.info("Deployment ports calculated", ports=deployment_ports)
        return deployment_ports
    
    def derive_mode_credentials(
        self, 
        master_credentials: Dict[str, str], 
        mode: str
    ) -> Dict[str, str]:
        """
        Derive mode-specific credentials from master credentials.
        
        SHARED DATABASE APPROACH:
        - SHARED: user, password, database name (hive), postgres port (5532)
        - DIFFERENT: API ports, API key prefixes, schema namespaces
        
        Args:
            master_credentials: Master credentials from generate_master_credentials()
            mode: Mode name (workspace, agent, genie)
            
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
            # Agent/genie modes use schema-specific connection
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
            "schema": "public" if mode == "workspace" else mode  # Schema separation
        }
        
        logger.info(
            f"Derived {mode} credentials for shared database approach",
            database=database_name,
            shared_db_port=mode_ports["db"],
            api_port=mode_ports["api"],
            schema=mode_credentials["schema"]
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
        if mode in ["agent", "genie"]:
            # Schema creation should integrate with Agno framework
            # This is a placeholder for now - actual implementation should
            # integrate with the database initialization system
            logger.info(f"Schema creation for {mode} mode - integrate with Agno framework")
    
    def detect_existing_containers(self) -> Dict[str, bool]:
        """Detect existing Docker containers for shared approach."""
        import subprocess
        
        containers_status = {}
        
        for mode, container_info in self.CONTAINERS.items():
            for service, container_name in container_info.items():
                try:
                    # Check if container exists and is running
                    result = subprocess.run(
                        ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
                        capture_output=True, text=True, check=False
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
        old_containers = ["hive-postgres-agent", "hive-postgres-genie"]
        needs_migration = any(
            container for container in old_containers 
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

    def generate_master_credentials(self) -> Dict[str, str]:
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
            api_key_base_length=len(master_api_key_base)
        )
        
        return master_credentials
    
    def install_all_modes(
        self, 
        modes: List[str] = None,
        force_regenerate: bool = False,
        sync_mcp: bool = False
    ) -> Dict[str, Dict[str, str]]:
        """
        MAIN INSTALLATION FUNCTION: Install credentials for all specified modes.
        
        This is the primary entry point called by both Makefile and CLI installers.
        Generates master credentials ONCE and derives mode-specific configs.
        
        Args:
            modes: List of modes to install (defaults to all: workspace, agent, genie)
            force_regenerate: Force regeneration even if credentials exist
            sync_mcp: Whether to sync credentials to MCP config (default: False)
            
        Returns:
            Dict mapping mode names to their credential sets
        """
        modes = modes or list(self.PORT_PREFIXES.keys())
        logger.info(f"Installing credentials for modes: {modes}")
        
        # Check if master credentials exist and should be reused
        existing_master = self._extract_existing_master_credentials()
        
        if existing_master and not force_regenerate:
            logger.info("Reusing existing master credentials")
            master_credentials = existing_master
        else:
            logger.info("Generating new master credentials")
            master_credentials = self.generate_master_credentials()
            
            # Save master credentials to main .env file
            self._save_master_credentials(master_credentials)
        
        # Generate credentials for each requested mode
        all_mode_credentials = {}
        
        for mode in modes:
            logger.info(f"Setting up {mode} mode...")
            
            # Derive mode-specific credentials
            mode_creds = self.derive_mode_credentials(master_credentials, mode)
            all_mode_credentials[mode] = mode_creds
            
            # Create environment file for this mode
            self._create_mode_env_file(mode, mode_creds)
        
        # Update MCP config if requested (once after all modes are set up)
        if sync_mcp:
            try:
                self.sync_mcp_config_with_credentials()
            except Exception as e:
                logger.warning("MCP sync failed but continuing with credential installation", error=str(e))
        
        logger.info(f"Credential installation complete for modes: {modes}")
        return all_mode_credentials
        
    def _extract_existing_master_credentials(self) -> Optional[Dict[str, str]]:
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
                    'your-secure-password-here',
                    'your-hive-api-key-here',
                    'your-password',
                    'change-me',
                    'placeholder',
                    'example',
                    'template',
                    'replace-this'
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
                    "api_key_base": api_key_base
                }
                
        except Exception as e:
            logger.error("Failed to extract existing master credentials", error=str(e))
            
        return None
        
    def _save_master_credentials(self, master_credentials: Dict[str, str]) -> None:
        """Save master credentials to main .env file."""
        logger.info("Saving master credentials to main .env file")
        
        # Create main .env from .env.example if it doesn't exist
        if not self.master_env_file.exists():
            env_example = self.project_root / ".env.example"
            if env_example.exists():
                logger.info("Creating .env from .env.example template with comprehensive configuration")
                self.master_env_file.write_text(env_example.read_text())
            else:
                logger.warning(".env.example not found, creating minimal .env file")
                self.master_env_file.write_text(self._get_base_env_template())
        
        # Update credentials in .env file
        env_content = self.master_env_file.read_text()
        lines = env_content.splitlines()
        
        # Generate main workspace credentials for main .env
        main_db_url = (
            f"postgresql+psycopg://{master_credentials['postgres_user']}:"
            f"{master_credentials['postgres_password']}@localhost:5532/hive"
        )
        main_api_key = f"hive_{master_credentials['api_key_base']}"
        
        # Update lines
        modified_lines = []
        db_url_found = False
        api_key_found = False
        
        for line in lines:
            if line.startswith("HIVE_DATABASE_URL="):
                modified_lines.append(f"HIVE_DATABASE_URL={main_db_url}")
                db_url_found = True
            elif line.startswith("HIVE_API_KEY="):
                modified_lines.append(f"HIVE_API_KEY={main_api_key}")
                api_key_found = True
            else:
                modified_lines.append(line)
        
        # Add missing entries
        if not db_url_found:
            modified_lines.append(f"HIVE_DATABASE_URL={main_db_url}")
        if not api_key_found:
            modified_lines.append(f"HIVE_API_KEY={main_api_key}")
            
        self.master_env_file.write_text("\n".join(modified_lines) + "\n")
        logger.info("Master credentials saved to .env with all comprehensive configurations from template")
        
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
        
    def _create_mode_env_file(self, mode: str, credentials: Dict[str, str]) -> None:
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
HIVE_API_PORT={credentials['api_port']}
HIVE_API_WORKERS=1

# Database Configuration (Shared Credentials)
HIVE_DATABASE_URL={credentials['database_url']}
POSTGRES_HOST={credentials['postgres_host']}
POSTGRES_PORT=5532
POSTGRES_USER={credentials['postgres_user']}
POSTGRES_PASSWORD={credentials['postgres_password']}
POSTGRES_DB={credentials['postgres_database']}

# Security & Authentication
HIVE_API_KEY={credentials['api_key']}
HIVE_CORS_ORIGINS=http://localhost:3000,http://localhost:{credentials['api_port']}
HIVE_AUTH_DISABLED=true

# Development Mode Settings
HIVE_DEV_MODE=true
HIVE_ENABLE_METRICS=true
HIVE_AGNO_MONITOR=false
HIVE_DEFAULT_MODEL=gpt-4.1-mini
"""
        
        env_file.write_text(env_content)
        logger.info(f"Created {mode} environment file", file=str(env_file))
