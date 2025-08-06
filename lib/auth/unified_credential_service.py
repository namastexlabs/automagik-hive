#!/usr/bin/env python3
"""
Unified Credential Management Service for Automagik Hive.

This is the SINGLE SOURCE OF TRUTH for all credential generation across the entire system.
Generates credentials ONCE during install and populates ALL 3 modes consistently.

DESIGN PRINCIPLES:
1. Generate credentials ONCE during installation
2. Share same DB user/password across all modes (security best practice)
3. Different ports per mode: workspace(5532/8886), agent(35532/38886), genie(48532/48886)
4. Consistent API keys but with mode-specific prefixes for identification
5. Template-based environment file generation
6. Backward compatibility with existing Makefile and CLI installers
"""

import secrets
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from lib.logging import logger


class UnifiedCredentialService:
    """Single source of truth for all Automagik Hive credential management."""
    
    # Port configuration for each mode
    MODES = {
        "workspace": {"db_port": 5532, "api_port": 8886},
        "agent": {"db_port": 35532, "api_port": 38886}, 
        "genie": {"db_port": 48532, "api_port": 48886}
    }
    
    # Database names per mode
    DATABASES = {
        "workspace": "hive",
        "agent": "hive_agent",
        "genie": "hive_genie"
    }
    
    def __init__(self, project_root: Path = None):
        """
        Initialize unified credential service.
        
        Args:
            project_root: Project root directory (defaults to current working directory)
        """
        self.project_root = project_root or Path.cwd()
        self.master_env_file = self.project_root / ".env"
        
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
    
    def derive_mode_credentials(
        self, 
        master_credentials: Dict[str, str], 
        mode: str
    ) -> Dict[str, str]:
        """
        Derive mode-specific credentials from master credentials.
        
        SHARED: user, password (security best practice - same DB user across environments)
        DIFFERENT: ports, database names, API key prefixes
        
        Args:
            master_credentials: Master credentials from generate_master_credentials()
            mode: Mode name (workspace, agent, genie)
            
        Returns:
            Dict containing mode-specific credentials
        """
        if mode not in self.MODES:
            raise ValueError(f"Unknown mode: {mode}. Valid modes: {list(self.MODES.keys())}")
            
        mode_config = self.MODES[mode]
        database_name = self.DATABASES[mode]
        
        # Create mode-specific API key with identifier prefix
        api_key = f"hive_{mode}_{master_credentials['api_key_base']}"
        
        # Create database URL with mode-specific port and database
        database_url = (
            f"postgresql+psycopg://{master_credentials['postgres_user']}:"
            f"{master_credentials['postgres_password']}@localhost:"
            f"{mode_config['db_port']}/{database_name}"
        )
        
        mode_credentials = {
            "postgres_user": master_credentials["postgres_user"],
            "postgres_password": master_credentials["postgres_password"],
            "postgres_database": database_name,
            "postgres_host": "localhost",
            "postgres_port": str(mode_config["db_port"]),
            "api_port": str(mode_config["api_port"]),
            "api_key": api_key,
            "database_url": database_url,
            "mode": mode
        }
        
        logger.info(
            f"Derived {mode} credentials from master",
            database=database_name,
            db_port=mode_config["db_port"],
            api_port=mode_config["api_port"]
        )
        
        return mode_credentials
    
    def install_all_modes(
        self, 
        modes: List[str] = None,
        force_regenerate: bool = False
    ) -> Dict[str, Dict[str, str]]:
        """
        MAIN INSTALLATION FUNCTION: Install credentials for all specified modes.
        
        This is the primary entry point called by both Makefile and CLI installers.
        Generates master credentials ONCE and derives mode-specific configs.
        
        Args:
            modes: List of modes to install (defaults to all: workspace, agent, genie)
            force_regenerate: Force regeneration even if credentials exist
            
        Returns:
            Dict mapping mode names to their credential sets
        """
        modes = modes or list(self.MODES.keys())
        logger.info(f"Installing unified credentials for modes: {modes}")
        
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
            
            # Update/create docker template with credentials
            self._update_docker_template(mode, mode_creds)
        
        # Update MCP configuration with shared credentials
        self._update_mcp_config(master_credentials, all_mode_credentials)
        
        logger.info(f"Unified credential installation complete for modes: {modes}")
        return all_mode_credentials
    
    def get_mode_credentials(self, mode: str) -> Optional[Dict[str, str]]:
        """
        Get existing credentials for a specific mode.
        
        Args:
            mode: Mode name (workspace, agent, genie)
            
        Returns:
            Dict with mode credentials or None if not found
        """
        mode_env_file = self._get_mode_env_file(mode)
        
        if not mode_env_file.exists():
            logger.warning(f"Environment file not found for {mode}", file=str(mode_env_file))
            return None
            
        return self._extract_credentials_from_file(mode_env_file, mode)
    
    def validate_installation(self, modes: List[str] = None) -> Dict[str, bool]:
        """
        Validate that all mode credentials are properly installed and consistent.
        
        Args:
            modes: List of modes to validate (defaults to all)
            
        Returns:
            Dict mapping mode names to validation status
        """
        modes = modes or list(self.MODES.keys())
        validation_results = {}
        
        logger.info(f"Validating credential installation for modes: {modes}")
        
        # Extract master credentials
        master_credentials = self._extract_existing_master_credentials()
        
        if not master_credentials:
            logger.error("No master credentials found - installation incomplete")
            return {mode: False for mode in modes}
        
        for mode in modes:
            mode_creds = self.get_mode_credentials(mode)
            
            if not mode_creds:
                validation_results[mode] = False
                continue
                
            # Validate consistency with master credentials
            is_valid = (
                mode_creds["postgres_user"] == master_credentials["postgres_user"]
                and mode_creds["postgres_password"] == master_credentials["postgres_password"]
                and mode_creds["api_key"].startswith(f"hive_{mode}_")
                and str(self.MODES[mode]["db_port"]) in mode_creds["database_url"]
                and mode_creds["postgres_database"] == self.DATABASES[mode]
            )
            
            validation_results[mode] = is_valid
            
            if is_valid:
                logger.info(f"✅ {mode} credentials validation passed")
            else:
                logger.error(f"❌ {mode} credentials validation failed")
        
        return validation_results
    
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
            
            if postgres_user and postgres_password and api_key_base:
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
        
        # Create main .env from example if it doesn't exist
        if not self.master_env_file.exists():
            env_example = self.project_root / ".env.example"
            if env_example.exists():
                logger.info("Creating .env from .env.example")
                self.master_env_file.write_text(env_example.read_text())
            else:
                logger.info("Creating new .env file")
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
        updated_lines = []
        db_url_updated = False
        api_key_updated = False
        
        for line in lines:
            if line.startswith("HIVE_DATABASE_URL="):
                updated_lines.append(f"HIVE_DATABASE_URL={main_db_url}")
                db_url_updated = True
            elif line.startswith("HIVE_API_KEY="):
                updated_lines.append(f"HIVE_API_KEY={main_api_key}")
                api_key_updated = True
            else:
                updated_lines.append(line)
        
        # Add missing entries
        if not db_url_updated:
            updated_lines.append(f"HIVE_DATABASE_URL={main_db_url}")
        if not api_key_updated:
            updated_lines.append(f"HIVE_API_KEY={main_api_key}")
            
        self.master_env_file.write_text("\n".join(updated_lines) + "\n")
        logger.info("Master credentials saved to .env")
    
    def _get_mode_env_file(self, mode: str) -> Path:
        """Get the environment file path for a specific mode."""
        if mode == "workspace":
            return self.master_env_file
        else:
            return self.project_root / f".env.{mode}"
    
    def _create_mode_env_file(self, mode: str, credentials: Dict[str, str]) -> None:
        """Create environment file for a specific mode."""
        env_file = self._get_mode_env_file(mode)
        
        logger.info(f"Creating {mode} environment file", file=str(env_file))
        
        if mode == "workspace":
            # Workspace uses main .env file (already created by _save_master_credentials)
            logger.info("Workspace uses main .env file (already created)")
            return
        
        # Create mode-specific .env file
        env_content = self._generate_mode_env_content(mode, credentials)
        env_file.write_text(env_content)
        
        logger.info(f"Created {mode} environment file", file=str(env_file))
    
    def _generate_mode_env_content(self, mode: str, credentials: Dict[str, str]) -> str:
        """Generate environment file content for a specific mode."""
        return f"""# =========================================================================
# ⚡ AUTOMAGIK HIVE - {mode.upper()} MODE CONFIGURATION
# =========================================================================
# 
# Generated by Unified Credential Service
# SINGLE SOURCE OF TRUTH: Shared DB credentials, mode-specific ports
#
# Mode: {mode}
# Database Port: {credentials['postgres_port']}
# API Port: {credentials['api_port']}
#
# =========================================================================

# -------------------------------------------------------------------------
# CORE APPLICATION SETTINGS
# -------------------------------------------------------------------------
HIVE_ENVIRONMENT=development
HIVE_LOG_LEVEL=INFO
AGNO_LOG_LEVEL=INFO

# -------------------------------------------------------------------------
# SERVER & API CONFIGURATION
# -------------------------------------------------------------------------
HIVE_API_HOST=0.0.0.0
HIVE_API_PORT={credentials['api_port']}
HIVE_API_WORKERS=1

# -------------------------------------------------------------------------
# DATABASE CONFIGURATION (UNIFIED CREDENTIALS)
# -------------------------------------------------------------------------
HIVE_DATABASE_URL={credentials['database_url']}

# Database connection components (for Docker containers)
POSTGRES_HOST={credentials['postgres_host']}
POSTGRES_PORT=5432
POSTGRES_USER={credentials['postgres_user']}
POSTGRES_PASSWORD={credentials['postgres_password']}
POSTGRES_DB={credentials['postgres_database']}

# -------------------------------------------------------------------------
# SECURITY & AUTHENTICATION
# -------------------------------------------------------------------------
HIVE_API_KEY={credentials['api_key']}
HIVE_CORS_ORIGINS=http://localhost:3000,http://localhost:{credentials['api_port']}
HIVE_AUTH_DISABLED=true

# -------------------------------------------------------------------------
# DEVELOPMENT MODE SETTINGS
# -------------------------------------------------------------------------
HIVE_DEV_MODE=true
HIVE_ENABLE_METRICS=true
HIVE_AGNO_MONITOR=false

# -------------------------------------------------------------------------
# AI PROVIDER KEYS (ADD YOUR ACTUAL KEYS)
# -------------------------------------------------------------------------
HIVE_DEFAULT_MODEL=gpt-4.1-mini

# Set these with your actual API keys:
# ANTHROPIC_API_KEY=your-anthropic-api-key-here
# GEMINI_API_KEY=your-gemini-api-key-here
# OPENAI_API_KEY=your-openai-api-key-here
# GROK_API_KEY=your-grok-api-key-here
# GROQ_API_KEY=your-groq-api-key-here

# -------------------------------------------------------------------------
# NOTIFICATIONS & TELEMETRY
# -------------------------------------------------------------------------
# LANGWATCH_API_KEY=your-langwatch-api-key-here
HIVE_ENABLE_LANGWATCH=true
"""
    
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

# Generated by Unified Credential Service
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive
HIVE_API_KEY=hive_generated_key

HIVE_CORS_ORIGINS=http://localhost:3000,http://localhost:8886
HIVE_AUTH_DISABLED=true
HIVE_DEV_MODE=true
HIVE_DEFAULT_MODEL=gpt-4.1-mini
"""
    
    def _update_docker_template(self, mode: str, credentials: Dict[str, str]) -> None:
        """Update Docker template with generated credentials."""
        template_file = self.project_root / "docker" / "templates" / f"{mode}.yml"
        
        if not template_file.exists():
            logger.warning(f"Docker template not found for {mode}", file=str(template_file))
            return
        
        try:
            template_content = template_file.read_text()
            
            # Replace placeholder credentials with generated ones
            updated_content = template_content.replace(
                "POSTGRES_USER=workspace", f"POSTGRES_USER={credentials['postgres_user']}"
            ).replace(
                "POSTGRES_PASSWORD=workspace", f"POSTGRES_PASSWORD={credentials['postgres_password']}"
            ).replace(
                "POSTGRES_USER=agent", f"POSTGRES_USER={credentials['postgres_user']}"
            ).replace(
                "POSTGRES_PASSWORD=agent_secure_password", f"POSTGRES_PASSWORD={credentials['postgres_password']}"
            ).replace(
                "POSTGRES_USER=genie", f"POSTGRES_USER={credentials['postgres_user']}"
            ).replace(
                "POSTGRES_PASSWORD=genie_secure_password", f"POSTGRES_PASSWORD={credentials['postgres_password']}"
            )
            
            template_file.write_text(updated_content)
            logger.info(f"Updated Docker template for {mode}", file=str(template_file))
            
        except Exception as e:
            logger.error(f"Failed to update Docker template for {mode}", error=str(e))
    
    def _update_mcp_config(
        self, 
        master_credentials: Dict[str, str], 
        all_mode_credentials: Dict[str, Dict[str, str]]
    ) -> None:
        """Update MCP configuration with unified credentials."""
        mcp_file = self.project_root / ".mcp.json"
        
        if not mcp_file.exists():
            logger.warning("MCP config file not found", file=str(mcp_file))
            return
        
        try:
            import json
            import re
            
            mcp_content = mcp_file.read_text()
            
            # Update PostgreSQL connection strings for all modes
            for mode, creds in all_mode_credentials.items():
                # Replace any existing PostgreSQL connection string with new credentials
                pattern = r"postgresql\+psycopg://[^@]*@localhost:" + str(self.MODES[mode]["db_port"])
                replacement = f"postgresql+psycopg://{creds['postgres_user']}:{creds['postgres_password']}@localhost:{self.MODES[mode]['db_port']}"
                mcp_content = re.sub(pattern, replacement, mcp_content)
            
            # Update API keys
            for mode, creds in all_mode_credentials.items():
                pattern = f'"HIVE_API_KEY":\\s*"[^"]*"'
                replacement = f'"HIVE_API_KEY": "{creds["api_key"]}"'
                mcp_content = re.sub(pattern, replacement, mcp_content)
            
            mcp_file.write_text(mcp_content)
            logger.info("MCP configuration updated with unified credentials")
            
        except Exception as e:
            logger.error("Failed to update MCP configuration", error=str(e))
    
    def _extract_credentials_from_file(self, env_file: Path, mode: str) -> Optional[Dict[str, str]]:
        """Extract credentials from a specific environment file."""
        try:
            env_content = env_file.read_text()
            credentials = {}
            
            for line in env_content.splitlines():
                line = line.strip()
                if line.startswith("HIVE_DATABASE_URL="):
                    url = line.split("=", 1)[1].strip()
                    credentials["database_url"] = url
                    
                    if "postgresql+psycopg://" in url:
                        parsed = urlparse(url)
                        credentials["postgres_user"] = parsed.username
                        credentials["postgres_password"] = parsed.password
                        credentials["postgres_host"] = parsed.hostname or "localhost"
                        credentials["postgres_port"] = str(parsed.port or self.MODES[mode]["db_port"])
                        credentials["postgres_database"] = parsed.path[1:] if parsed.path else self.DATABASES[mode]
                        
                elif line.startswith("HIVE_API_KEY="):
                    credentials["api_key"] = line.split("=", 1)[1].strip()
                    
                elif line.startswith("HIVE_API_PORT="):
                    credentials["api_port"] = line.split("=", 1)[1].strip()
            
            credentials["mode"] = mode
            return credentials if credentials else None
            
        except Exception as e:
            logger.error(f"Failed to extract credentials from {env_file}", error=str(e))
            return None
    
    def _generate_secure_token(self, length: int = 16, safe_chars: bool = False) -> str:
        """Generate cryptographically secure random token."""
        if safe_chars:
            # Use openssl-like approach - generate base64 and remove special characters
            token = secrets.token_urlsafe(length + 8)  # Generate extra for trimming
            token = token.replace("-", "").replace("_", "")
            return token[:length]
        return secrets.token_urlsafe(length)
    
    def get_installation_summary(self, modes: List[str] = None) -> Dict[str, any]:
        """Get summary of current installation status."""
        modes = modes or list(self.MODES.keys())
        
        master_creds = self._extract_existing_master_credentials()
        validation_results = self.validate_installation(modes)
        
        summary = {
            "master_credentials_exist": bool(master_creds),
            "modes_validated": validation_results,
            "total_modes": len(modes),
            "successful_modes": sum(1 for result in validation_results.values() if result),
            "failed_modes": [mode for mode, result in validation_results.items() if not result],
            "port_assignments": {
                mode: {
                    "database_port": self.MODES[mode]["db_port"],
                    "api_port": self.MODES[mode]["api_port"],
                    "database_name": self.DATABASES[mode]
                }
                for mode in modes
            }
        }
        
        if master_creds:
            summary["shared_credentials"] = {
                "postgres_user": master_creds["postgres_user"],
                "postgres_user_length": len(master_creds["postgres_user"]),
                "postgres_password_length": len(master_creds["postgres_password"]),
                "api_key_base_length": len(master_creds["api_key_base"])
            }
        
        return summary