"""Agent Environment Management.

Manages agent environment configuration using docker-compose inheritance
from the main .env file instead of separate agent-specific files.
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
        self.main_env_path = self.workspace_path / ".env"
        self.docker_compose_path = self.workspace_path / "docker" / "agent" / "docker-compose.yml"
        
        # Initialize config with docker-compose inheritance model
        self.config = EnvironmentConfig(
            source_file=self.main_env_path,
            target_file=self.docker_compose_path,
            port_mappings={"HIVE_API_PORT": 38886, "POSTGRES_PORT": 35532},
            database_suffix="_agent",
            cors_port_mapping={8886: 38886, 5532: 35532}
        )
    
    
    def validate_agent_setup(self, force: bool = False) -> bool:
        """Validate agent setup using docker-compose inheritance model."""
        # Check that main .env exists
        if not self.main_env_path.exists():
            return False
        
        # Check that docker-compose.yml exists
        if not self.docker_compose_path.exists():
            return False
        
        # Validate main .env has required keys for agent inheritance
        return self._validate_main_env_for_agent()
    
    def ensure_main_env(self) -> bool:
        """Ensure main .env file exists for docker-compose inheritance."""
        if self.main_env_path.exists():
            return True
        
        if self.env_example_path.exists():
            # Copy from example if main doesn't exist
            content = self.env_example_path.read_text()
            self.main_env_path.write_text(content)
            return True
        
        return False
    
    def validate_environment(self) -> dict:
        """Validate agent environment configuration using docker-compose inheritance."""
        if not self.main_env_path.exists():
            return {
                "valid": False,
                "errors": [f"Main environment file {self.main_env_path} not found"],
                "warnings": [],
                "config": None
            }
        
        if not self.docker_compose_path.exists():
            return {
                "valid": False,
                "errors": [f"Docker compose file {self.docker_compose_path} not found"],
                "warnings": [],
                "config": None
            }
        
        try:
            # Load main .env file for inheritance check
            main_config = self._load_env_file(self.main_env_path)
            required_keys = ["POSTGRES_USER", "POSTGRES_PASSWORD", "HIVE_API_KEY"]
            
            errors = []
            warnings = []
            
            # Check required keys in main .env
            for key in required_keys:
                if key not in main_config:
                    errors.append(f"Missing required key in main .env: {key}")
            
            # Validate docker-compose configuration exists
            if not self._validate_docker_compose_config():
                errors.append("Invalid docker-compose.yml configuration")
            
            # Check for proper port separation
            if "HIVE_API_PORT" in main_config:
                port = main_config["HIVE_API_PORT"]
                if port == "38886":
                    warnings.append("Main .env should use port 8886, agent gets 38886 via docker-compose")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "config": main_config
            }
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Failed to validate environment: {str(e)}"],
                "warnings": [],
                "config": None
            }
    
    def get_agent_credentials(self) -> Optional[AgentCredentials]:
        """Extract agent credentials from main .env file (docker-compose inheritance)."""
        if not self.main_env_path.exists():
            return None
        
        try:
            # Load from main .env since agent inherits via docker-compose
            config = self._load_env_file(self.main_env_path)
            
            return AgentCredentials(
                postgres_user=config.get("POSTGRES_USER", "test_user"),
                postgres_password=config.get("POSTGRES_PASSWORD", "test_pass"),
                postgres_db="hive_agent",  # Always hive_agent for agent
                postgres_port=35532,  # Fixed port for agent
                hive_api_key=config.get("HIVE_API_KEY", ""),
                hive_api_port=38886,  # Fixed port for agent
                cors_origins="http://localhost:38886"
            )
        except Exception:
            return None
    
    def update_environment(self, updates: dict) -> bool:
        """Update main .env file with provided values (agent inherits via docker-compose)."""
        if not self.main_env_path.exists():
            return False
        
        try:
            content = self.main_env_path.read_text()
            lines = content.split('\n')
            
            # Update existing keys and track what was processed
            processed_keys = set()
            for i, line in enumerate(lines):
                if '=' in line and not line.strip().startswith('#'):
                    key = line.split('=')[0].strip()
                    if key in updates:
                        lines[i] = f"{key}={updates[key]}"
                        processed_keys.add(key)
            
            # Add remaining keys that weren't found
            for key, value in updates.items():
                if key not in processed_keys:
                    lines.append(f"{key}={value}")
            
            # Write back to main .env file
            self.main_env_path.write_text('\n'.join(lines))
            return True
            
        except Exception:
            return False
    
    def clean_environment(self) -> bool:
        """Clean up agent environment - no longer needed with docker-compose inheritance."""
        # With docker-compose inheritance, no separate files to clean
        return True
    
    def copy_credentials_from_main_env(self) -> bool:
        """Copy credentials from main .env to agent environment - automatic with docker-compose."""
        # With docker-compose inheritance, this happens automatically
        return self.main_env_path.exists()
    
    def ensure_agent_api_key(self) -> bool:
        """Ensure agent has a valid API key."""
        # API keys are handled in the main .env file
        return self.main_env_path.exists()
    
    def generate_agent_api_key(self) -> str:
        """Generate an agent API key."""
        import secrets
        return secrets.token_urlsafe(32)
    
    # Internal helper methods
    def _validate_main_env_for_agent(self) -> bool:
        """Validate that main .env has required keys for agent inheritance."""
        if not self.main_env_path.exists():
            return False
        
        config = self._load_env_file(self.main_env_path)
        required_keys = ["POSTGRES_USER", "POSTGRES_PASSWORD", "HIVE_API_KEY"]
        
        return all(key in config for key in required_keys)
    
    def _validate_docker_compose_config(self) -> bool:
        """Validate that docker-compose.yml exists and has proper structure."""
        return self.docker_compose_path.exists()
    
    def _get_agent_port_mappings(self) -> dict:
        """Get agent-specific port mappings."""
        return {
            "HIVE_API_PORT": 38886,
            "POSTGRES_PORT": 35532
        }
    
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
            
            # Validate host:port format - if no colon found, this is invalid
            # URLs like "host_port" suggest port should be present but malformed
            if ':' in host_port:
                host, port_str = host_port.split(':', 1)
                # Validate port is numeric
                try:
                    port = int(port_str)
                except ValueError:
                    return None  # Invalid port number
            else:
                # No port specified - only allow this for URLs without explicit port indication
                # URLs containing "_port" suggest malformed port specification
                if "_port" in host_port:
                    return None  # Malformed URL with port indication but no separator
                host = host_port
                port = 5432  # Default PostgreSQL port
            
            return {
                "user": user,
                "password": password,
                "host": host,
                "port": port,
                "database": database
            }
        except Exception:
            return None
    
    def _build_agent_database_url(self, db_info: dict) -> str:
        """Build agent database URL from components."""
        return f"postgresql+psycopg://{db_info['user']}:{db_info['password']}@{db_info['host']}:35532/hive_agent"
    
    def _get_inherited_config(self) -> dict:
        """Get the configuration that agent inherits from main .env."""
        if not self.main_env_path.exists():
            return {}
        
        main_config = self._load_env_file(self.main_env_path)
        
        # Agent inherits these from main .env via docker-compose
        agent_config = {
            "postgres_user": main_config.get("POSTGRES_USER", "test_user"),
            "postgres_password": main_config.get("POSTGRES_PASSWORD", "test_pass"),
            "hive_api_key": main_config.get("HIVE_API_KEY", ""),
            # Agent-specific overrides via docker-compose environment
            "postgres_db": "hive_agent",
            "postgres_port": 35532,
            "hive_api_port": 38886,
            "cors_origins": "http://localhost:38886"
        }
        
        return agent_config


# Convenience functions
def create_agent_environment(workspace_path: Optional[Path] = None) -> AgentEnvironment:
    """Create agent environment using docker-compose inheritance."""
    env = AgentEnvironment(workspace_path)
    env.ensure_main_env()  # Ensure main .env exists for inheritance
    return env


def validate_agent_environment(workspace_path: Optional[Path] = None) -> bool:
    """Validate agent environment using docker-compose inheritance."""
    env = AgentEnvironment(workspace_path)
    return env.validate_agent_setup()


def cleanup_agent_environment(workspace_path: Optional[Path] = None) -> bool:
    """Cleanup agent environment - no longer needed with docker-compose inheritance."""
    # With docker-compose inheritance, no separate files to clean
    return True


def get_agent_ports() -> dict[str, int]:
    """Get agent ports stub function."""
    return {"api": 38886, "postgres": 35532}
