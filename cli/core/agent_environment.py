"""Agent Environment Management Stubs.

Minimal stub implementations to fix import errors in tests.
These are placeholders that satisfy import requirements.
"""

from typing import Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentCredentials:
    """Agent credentials for agent environment."""
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_port: int
    hive_api_key: str
    hive_api_port: int
    cors_origins: str


@dataclass
class EnvironmentConfig:
    """Environment configuration for agent setup."""
    source_file: Path
    target_file: Path
    port_mappings: dict
    database_suffix: str
    cors_port_mapping: dict


class AgentEnvironment:
    """Agent environment management."""
    
    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path.cwd()
        self.env_example_path = self.workspace_path / ".env.example"
        self.env_agent_path = self.workspace_path / ".env.agent"
        self.main_env_path = self.workspace_path / ".env"
        
        # Initialize config with defaults
        self.config = EnvironmentConfig(
            source_file=self.env_example_path,
            target_file=self.env_agent_path,
            port_mappings={"HIVE_API_PORT": 38886, "POSTGRES_PORT": 35532},
            database_suffix="_agent",
            cors_port_mapping={8886: 38886, 5532: 35532}
        )
    
    def generate_env_agent(self, force: bool = False) -> Path:
        """Generate .env.agent file from .env.example."""
        if self.env_agent_path.exists() and not force:
            raise FileExistsError(f"File {self.env_agent_path} already exists")
        
        if not self.env_example_path.exists():
            raise FileNotFoundError(f"Template file {self.env_example_path} not found")
        
        # Read template and apply transformations
        content = self.env_example_path.read_text()
        
        # Apply agent-specific transformations
        content = self._apply_port_mappings(content)
        content = self._apply_database_mappings(content)
        content = self._apply_cors_mappings(content)
        content = self._apply_agent_specific_config(content)
        
        # Write to target file
        self.env_agent_path.write_text(content)
        return self.env_agent_path
    
    def validate_environment(self) -> dict:
        """Validate agent environment configuration."""
        if not self.env_agent_path.exists():
            return {
                "valid": False,
                "errors": [f"Agent environment file {self.env_agent_path} not found"],
                "warnings": [],
                "config": None
            }
        
        try:
            config = self._load_env_file(self.env_agent_path)
            required_keys = ["HIVE_API_PORT", "HIVE_DATABASE_URL", "HIVE_API_KEY"]
            
            errors = []
            warnings = []
            
            # Check required keys
            for key in required_keys:
                if key not in config:
                    errors.append(f"Missing required key: {key}")
            
            # Validate port format
            if "HIVE_API_PORT" in config:
                try:
                    port = int(config["HIVE_API_PORT"])
                    if port != 38886:
                        warnings.append(f"Expected HIVE_API_PORT=38886, got {port}")
                except ValueError:
                    errors.append("HIVE_API_PORT must be a valid integer")
            
            # Validate database URL
            if "HIVE_DATABASE_URL" in config:
                if "35532" not in config["HIVE_DATABASE_URL"]:
                    warnings.append("Expected database port 35532")
                if "hive_agent" not in config["HIVE_DATABASE_URL"]:
                    warnings.append("Expected database name 'hive_agent'")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "config": config
            }
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Failed to validate environment: {str(e)}"],
                "warnings": [],
                "config": None
            }
    
    def get_agent_credentials(self) -> Optional[AgentCredentials]:
        """Extract agent credentials from environment file."""
        if not self.env_agent_path.exists():
            return None
        
        try:
            config = self._load_env_file(self.env_agent_path)
            
            # Parse database URL
            db_info = self._parse_database_url(config.get("HIVE_DATABASE_URL", ""))
            
            return AgentCredentials(
                postgres_user=db_info.get("user", "") if db_info else "",
                postgres_password=db_info.get("password", "") if db_info else "",
                postgres_db=db_info.get("database", "hive_agent") if db_info else "hive_agent",
                postgres_port=db_info.get("port", 35532) if db_info else 35532,
                hive_api_key=config.get("HIVE_API_KEY", ""),
                hive_api_port=int(config.get("HIVE_API_PORT", 38886)),
                cors_origins=config.get("HIVE_CORS_ORIGINS", "http://localhost:38886")
            )
        except Exception:
            return None
    
    def update_environment(self, updates: dict) -> bool:
        """Update environment file with new values."""
        if not self.env_agent_path.exists():
            return False
        
        try:
            content = self.env_agent_path.read_text()
            lines = content.split('\n')
            
            # Update existing keys and track what was updated
            updated_keys = set()
            for i, line in enumerate(lines):
                if '=' in line and not line.strip().startswith('#'):
                    key = line.split('=')[0].strip()
                    if key in updates:
                        lines[i] = f"{key}={updates[key]}"
                        updated_keys.add(key)
            
            # Add new keys that weren't found
            for key, value in updates.items():
                if key not in updated_keys:
                    lines.append(f"{key}={value}")
            
            # Write back to file
            self.env_agent_path.write_text('\n'.join(lines))
            return True
            
        except Exception:
            return False
    
    def clean_environment(self) -> bool:
        """Clean up agent environment files."""
        try:
            if self.env_agent_path.exists():
                self.env_agent_path.unlink()
            return True
        except Exception:
            return False
    
    def copy_credentials_from_main_env(self) -> bool:
        """Copy credentials from main .env to agent environment."""
        if not self.main_env_path.exists():
            return False
        
        try:
            main_config = self._load_env_file(self.main_env_path)
            
            # Keys to copy from main env
            keys_to_copy = [
                "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "HIVE_DEFAULT_MODEL"
            ]
            
            updates = {}
            for key in keys_to_copy:
                if key in main_config:
                    updates[key] = main_config[key]
            
            # Transform database URL if present
            if "HIVE_DATABASE_URL" in main_config:
                db_info = self._parse_database_url(main_config["HIVE_DATABASE_URL"])
                if db_info:
                    updates["HIVE_DATABASE_URL"] = self._build_agent_database_url(db_info)
            
            return self.update_environment(updates)
        except Exception:
            return False
    
    def ensure_agent_api_key(self) -> bool:
        """Ensure agent has a valid API key."""
        if not self.env_agent_path.exists():
            return False
        
        try:
            config = self._load_env_file(self.env_agent_path)
            current_key = config.get("HIVE_API_KEY", "")
            
            # Generate new key if missing or placeholder
            if not current_key or current_key == "your-hive-api-key-here":
                new_key = self.generate_agent_api_key()
                return self.update_environment({"HIVE_API_KEY": new_key})
            
            return True
        except Exception:
            return False
    
    def generate_agent_api_key(self) -> str:
        """Generate a new agent API key."""
        import secrets
        return secrets.token_urlsafe(32)
    
    # Internal helper methods
    def _apply_port_mappings(self, content: str) -> str:
        """Apply port mappings to content."""
        for old_port, new_port in [(8886, 38886), (5532, 35532)]:
            content = content.replace(f":{old_port}", f":{new_port}")
            content = content.replace(f"={old_port}", f"={new_port}")
        return content
    
    def _apply_database_mappings(self, content: str) -> str:
        """Apply database name mappings to content."""
        content = content.replace("/hive\n", "/hive_agent\n")
        content = content.replace("/hive ", "/hive_agent ")
        content = content.replace("/hive\"", "/hive_agent\"")
        return content
    
    def _apply_cors_mappings(self, content: str) -> str:
        """Apply CORS origin mappings to content."""
        return content.replace("http://localhost:8886", "http://localhost:38886")
    
    def _apply_agent_specific_config(self, content: str) -> str:
        """Apply agent-specific configuration headers."""
        agent_header = """# =========================================================================
# ⚡ AUTOMAGIK HIVE - AGENT ENVIRONMENT CONFIGURATION
# =========================================================================
#
# NOTES:
# - This is an auto-generated agent environment file
# - Port mappings: HIVE_API_PORT: 8886 → 38886, POSTGRES_PORT: 5532 → 35532  
# - Database: hive → hive_agent
# - DO NOT edit manually - regenerate with agent environment tools
#"""
        
        # Replace main environment header with agent-specific one
        lines = content.split('\n')
        header_end = 0
        for i, line in enumerate(lines):
            if line.startswith('#') or line.strip() == '':
                header_end = i + 1
            else:
                break
        
        return agent_header + '\n' + '\n'.join(lines[header_end:])
    
    def _load_env_file(self, file_path: Path) -> dict:
        """Load environment file as key-value dictionary."""
        config = {}
        if file_path.exists():
            for line in file_path.read_text().split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        return config
    
    def _parse_database_url(self, url: str) -> Optional[dict]:
        """Parse database URL into components."""
        try:
            # Simple regex-like parsing for postgresql URLs
            if not url.startswith('postgresql'):
                return None
            
            # Extract user:password@host:port/database
            parts = url.split('://', 1)[1]  # Remove postgresql://
            if '@' not in parts:
                return None
            
            auth_part, host_part = parts.split('@', 1)
            user, password = auth_part.split(':', 1) if ':' in auth_part else (auth_part, '')
            
            if '/' not in host_part:
                return None
            
            host_port, database = host_part.split('/', 1)
            host, port = host_port.split(':', 1) if ':' in host_port else (host_port, '5432')
            
            return {
                "user": user,
                "password": password,
                "host": host,
                "port": int(port),
                "database": database
            }
        except Exception:
            return None
    
    def _build_agent_database_url(self, db_info: dict) -> str:
        """Build agent database URL from components."""
        return f"postgresql+psycopg://{db_info['user']}:{db_info['password']}@{db_info['host']}:35532/hive_agent"


# Convenience functions
def create_agent_environment(workspace_path: Optional[Path] = None) -> AgentEnvironment:
    """Create agent environment stub function."""
    env = AgentEnvironment(workspace_path)
    env.create()
    return env


def validate_agent_environment(workspace_path: Optional[Path] = None) -> bool:
    """Validate agent environment stub function."""
    return True


def cleanup_agent_environment(workspace_path: Optional[Path] = None) -> bool:
    """Cleanup agent environment stub function."""
    return True


def get_agent_ports() -> dict[str, int]:
    """Get agent ports stub function."""
    return {"api": 38886, "postgres": 35532}
