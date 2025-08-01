"""Agent environment configuration management for UVX Automagik Hive.

Provides comprehensive management of .env.agent file generation and validation:
- Environment template processing from .env.example
- Port mapping for agent-specific services (8886→38886, 5532→35532)
- Database configuration with agent-specific naming
- Credential management with unified authentication
- Environment validation and cleanup
"""

import os
import re
import secrets
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, List


@dataclass
class AgentCredentials:
    """Agent-specific credentials extracted from environment."""
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_port: int
    hive_api_key: str
    hive_api_port: int
    cors_origins: str


@dataclass
class EnvironmentConfig:
    """Environment configuration with mappings and transformations."""
    source_file: Path
    target_file: Path
    port_mappings: Dict[str, int]
    database_suffix: str
    cors_port_mapping: Dict[int, int]


class AgentEnvironment:
    """Manages agent environment configuration generation and validation."""

    def __init__(self, workspace_path: Path = None):
        """Initialize agent environment manager.
        
        Args:
            workspace_path: Path to workspace directory (defaults to current directory)
        """
        self.workspace_path = workspace_path or Path.cwd()
        self.env_example_path = self.workspace_path / ".env.example"
        self.env_agent_path = self.workspace_path / ".env.agent"
        self.main_env_path = self.workspace_path / ".env"

        # Agent-specific configuration
        self.config = EnvironmentConfig(
            source_file=self.env_example_path,
            target_file=self.env_agent_path,
            port_mappings={
                "HIVE_API_PORT": 38886,      # 8886 → 38886
                "POSTGRES_PORT": 35532       # 5532 → 35532
            },
            database_suffix="_agent",        # hive → hive_agent
            cors_port_mapping={
                8886: 38886,                 # Update CORS origins
                5532: 35532
            }
        )

    def generate_env_agent(self, force: bool = False) -> Path:
        """Generate .env.agent from .env.example template with agent-specific modifications.
        
        Args:
            force: Overwrite existing .env.agent file if it exists
            
        Returns:
            Path to generated .env.agent file
            
        Raises:
            FileNotFoundError: If .env.example template doesn't exist
            FileExistsError: If .env.agent exists and force=False
        """
        if not self.env_example_path.exists():
            raise FileNotFoundError(f"Template file not found: {self.env_example_path}")

        if self.env_agent_path.exists() and not force:
            raise FileExistsError(f"Agent environment file already exists: {self.env_agent_path}")

        # Read template content
        with open(self.env_example_path, 'r') as f:
            content = f.read()

        # Apply agent-specific transformations
        content = self._apply_port_mappings(content)
        content = self._apply_database_mappings(content)
        content = self._apply_cors_mappings(content)
        content = self._apply_agent_specific_config(content)

        # Write agent environment file
        with open(self.env_agent_path, 'w') as f:
            f.write(content)

        return self.env_agent_path

    def validate_environment(self) -> Dict[str, Any]:
        """Validate agent environment configuration.
        
        Returns:
            Dictionary with validation results and status
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "config": None
        }

        # Check if .env.agent exists
        if not self.env_agent_path.exists():
            validation_results["valid"] = False
            validation_results["errors"].append(f"Agent environment file not found: {self.env_agent_path}")
            return validation_results

        try:
            # Load and validate configuration
            config = self._load_env_file(self.env_agent_path)
            validation_results["config"] = config

            # Validate required keys
            required_keys = [
                "HIVE_API_PORT",
                "HIVE_DATABASE_URL", 
                "HIVE_API_KEY"
            ]

            for key in required_keys:
                if key not in config:
                    validation_results["errors"].append(f"Missing required key: {key}")
                    validation_results["valid"] = False

            # Validate port values
            if "HIVE_API_PORT" in config:
                try:
                    port = int(config["HIVE_API_PORT"])
                    if port != 38886:
                        validation_results["warnings"].append(f"Expected HIVE_API_PORT=38886, got {port}")
                except ValueError:
                    validation_results["errors"].append("HIVE_API_PORT must be a valid integer")
                    validation_results["valid"] = False

            # Validate database URL
            if "HIVE_DATABASE_URL" in config:
                db_url = config["HIVE_DATABASE_URL"]
                if ":35532" not in db_url:
                    validation_results["warnings"].append("Expected database port 35532 in HIVE_DATABASE_URL")
                if "hive_agent" not in db_url:
                    validation_results["warnings"].append("Expected database name 'hive_agent' in HIVE_DATABASE_URL")

        except Exception as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Failed to validate environment: {e}")

        return validation_results

    def get_agent_credentials(self) -> Optional[AgentCredentials]:
        """Extract agent-specific credentials from .env.agent file.
        
        Returns:
            AgentCredentials object or None if file doesn't exist or is invalid
        """
        if not self.env_agent_path.exists():
            return None

        try:
            config = self._load_env_file(self.env_agent_path)
            
            # Parse database URL for credentials
            db_url = config.get("HIVE_DATABASE_URL", "")
            db_credentials = self._parse_database_url(db_url)
            
            return AgentCredentials(
                postgres_user=db_credentials.get("user", ""),
                postgres_password=db_credentials.get("password", ""),
                postgres_db=db_credentials.get("database", "hive_agent"),
                postgres_port=db_credentials.get("port", 35532),
                hive_api_key=config.get("HIVE_API_KEY", ""),
                hive_api_port=int(config.get("HIVE_API_PORT", 38886)),
                cors_origins=config.get("HIVE_CORS_ORIGINS", "http://localhost:38886")
            )
        except Exception:
            return None

    def update_environment(self, updates: Dict[str, str]) -> bool:
        """Update existing .env.agent with new values.
        
        Args:
            updates: Dictionary of key-value pairs to update
            
        Returns:
            True if successful, False otherwise
        """
        if not self.env_agent_path.exists():
            return False

        try:
            # Read current content
            with open(self.env_agent_path, 'r') as f:
                lines = f.readlines()

            # Update lines with new values
            updated_lines = []
            updated_keys = set()

            for line in lines:
                stripped = line.strip()
                if '=' in stripped and not stripped.startswith('#'):
                    key = stripped.split('=')[0]
                    if key in updates:
                        updated_lines.append(f"{key}={updates[key]}\n")
                        updated_keys.add(key)
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)

            # Add any new keys that weren't found
            for key, value in updates.items():
                if key not in updated_keys:
                    updated_lines.append(f"{key}={value}\n")

            # Write updated content
            with open(self.env_agent_path, 'w') as f:
                f.writelines(updated_lines)

            return True
        except Exception:
            return False

    def clean_environment(self) -> bool:
        """Remove agent environment files and cleanup.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.env_agent_path.exists():
                self.env_agent_path.unlink()
            return True
        except Exception:
            return False

    def copy_credentials_from_main_env(self) -> bool:
        """Copy compatible credentials from main .env to .env.agent.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.main_env_path.exists():
            return False

        try:
            main_config = self._load_env_file(self.main_env_path)
            
            # Keys to copy from main environment
            keys_to_copy = [
                "ANTHROPIC_API_KEY",
                "GEMINI_API_KEY", 
                "OPENAI_API_KEY",
                "GROK_API_KEY",
                "GROQ_API_KEY",
                "LANGWATCH_API_KEY",
                "HIVE_DEFAULT_MODEL",
                "HIVE_ENABLE_LANGWATCH",
                "HIVE_AGNO_MONITOR"
            ]

            updates = {}
            for key in keys_to_copy:
                if key in main_config:
                    updates[key] = main_config[key]

            # Also copy main database credentials for agent database
            if "HIVE_DATABASE_URL" in main_config:
                main_db_creds = self._parse_database_url(main_config["HIVE_DATABASE_URL"])
                if main_db_creds:
                    # Generate agent database URL with same credentials but different port/db
                    agent_db_url = self._build_agent_database_url(main_db_creds)
                    updates["HIVE_DATABASE_URL"] = agent_db_url

            return self.update_environment(updates)
        except Exception:
            return False

    def _apply_port_mappings(self, content: str) -> str:
        """Apply port mappings to environment content."""
        # Replace API port
        content = re.sub(
            r'HIVE_API_PORT=8886',
            f'HIVE_API_PORT={self.config.port_mappings["HIVE_API_PORT"]}',
            content
        )

        # Replace database port in URLs
        content = re.sub(
            r'localhost:5532',
            f'localhost:{self.config.port_mappings["POSTGRES_PORT"]}',
            content
        )

        return content

    def _apply_database_mappings(self, content: str) -> str:
        """Apply database name mappings to environment content."""
        # Replace database name in URL
        content = re.sub(
            r'/hive\b',
            f'/hive{self.config.database_suffix}',
            content
        )

        return content

    def _apply_cors_mappings(self, content: str) -> str:
        """Apply CORS origin port mappings to environment content."""
        # Update CORS origins
        for old_port, new_port in self.config.cors_port_mapping.items():
            content = re.sub(
                f'http://localhost:{old_port}',
                f'http://localhost:{new_port}',
                content
            )

        return content

    def _apply_agent_specific_config(self, content: str) -> str:
        """Apply agent-specific configuration changes."""
        # Add agent-specific comment header
        agent_header = (
            "# =========================================================================\n"
            "# ⚡ AUTOMAGIK HIVE - AGENT ENVIRONMENT CONFIGURATION\n"
            "# =========================================================================\n"
            "#\n"
            "# This is an auto-generated agent environment file.\n"
            "# Generated from .env.example with agent-specific port mappings:\n"
            "# - HIVE_API_PORT: 8886 → 38886\n"
            "# - POSTGRES_PORT: 5532 → 35532  \n"
            "# - DATABASE: hive → hive_agent\n"
            "#\n"
            "# DO NOT edit manually - regenerate with 'make install-agent'\n"
            "#\n"
        )

        # Replace original header with agent-specific header
        content = re.sub(
            r'# =========================================================================\n'
            r'# ⚡ AUTOMAGIK HIVE - ENVIRONMENT CONFIGURATION\n'
            r'# =========================================================================\n'
            r'#\n'
            r'# NOTES:\n'
            r'# - This is a template file\. Copy to \.env and fill in your values\.\n'
            r'# - For development, `make install` generates a pre-configured \.env file\.\n'
            r'# - DO NOT commit the \.env file to version control\.\n'
            r'#\n',
            agent_header,
            content
        )

        return content

    def _load_env_file(self, file_path: Path) -> Dict[str, str]:
        """Load environment file and return key-value pairs."""
        config = {}
        
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value

        return config

    def _parse_database_url(self, db_url: str) -> Optional[Dict[str, Any]]:
        """Parse PostgreSQL database URL into components."""
        # postgresql+psycopg://user:password@host:port/database
        pattern = r'postgresql\+psycopg://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
        match = re.match(pattern, db_url)
        
        if match:
            return {
                "user": match.group(1),
                "password": match.group(2),
                "host": match.group(3),
                "port": int(match.group(4)),
                "database": match.group(5)
            }
        return None

    def _build_agent_database_url(self, db_credentials: Dict[str, Any]) -> str:
        """Build agent database URL from main database credentials."""
        return (
            f"postgresql+psycopg://{db_credentials['user']}:{db_credentials['password']}"
            f"@{db_credentials['host']}:35532/hive_agent"
        )

    def generate_agent_api_key(self) -> str:
        """Generate a secure API key for agent environment."""
        return secrets.token_urlsafe(32)

    def ensure_agent_api_key(self) -> bool:
        """Ensure .env.agent has a valid API key, generate if missing."""
        if not self.env_agent_path.exists():
            return False

        config = self._load_env_file(self.env_agent_path)
        
        # Check if API key exists and is not placeholder
        api_key = config.get("HIVE_API_KEY", "")
        if not api_key or api_key == "your-hive-api-key-here":
            # Generate new API key
            new_api_key = self.generate_agent_api_key()
            return self.update_environment({"HIVE_API_KEY": new_api_key})

        return True


# Convenience functions for common operations
def create_agent_environment(workspace_path: Path = None, force: bool = False) -> Path:
    """Create agent environment with default configuration.
    
    Args:
        workspace_path: Path to workspace directory
        force: Overwrite existing files
        
    Returns:
        Path to generated .env.agent file
    """
    agent_env = AgentEnvironment(workspace_path)
    env_path = agent_env.generate_env_agent(force=force)
    
    # Copy credentials from main environment if available
    agent_env.copy_credentials_from_main_env()
    
    # Ensure API key is generated
    agent_env.ensure_agent_api_key()
    
    return env_path


def validate_agent_environment(workspace_path: Path = None) -> Dict[str, Any]:
    """Validate agent environment configuration.
    
    Args:
        workspace_path: Path to workspace directory
        
    Returns:
        Validation results dictionary
    """
    agent_env = AgentEnvironment(workspace_path)
    return agent_env.validate_environment()


def get_agent_ports(workspace_path: Path = None) -> Dict[str, int]:
    """Get agent-specific port mappings.
    
    Args:
        workspace_path: Path to workspace directory
        
    Returns:
        Dictionary with port mappings
    """
    agent_env = AgentEnvironment(workspace_path)
    credentials = agent_env.get_agent_credentials()
    
    if credentials:
        return {
            "api_port": credentials.hive_api_port,
            "postgres_port": credentials.postgres_port
        }
    
    # Return defaults if no environment found
    return {
        "api_port": 38886,
        "postgres_port": 35532
    }


def cleanup_agent_environment(workspace_path: Path = None) -> bool:
    """Clean up agent environment files.
    
    Args:
        workspace_path: Path to workspace directory
        
    Returns:
        True if successful
    """
    agent_env = AgentEnvironment(workspace_path)
    return agent_env.clean_environment()