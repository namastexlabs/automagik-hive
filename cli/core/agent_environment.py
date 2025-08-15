"""Agent Environment Management.

Container-first environment management focused on Docker service health
and .env file validation without hardcoded port mappings.
"""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class ServiceHealth:
    """Container service health status."""
    name: str
    running: bool
    healthy: bool
    container_id: Optional[str] = None


class AgentEnvironment:
    """Container-first agent environment management."""
    
    def __init__(self, workspace_path: Path | None = None):
        self.workspace_path = workspace_path or Path.cwd()
        self.env_example_path = self.workspace_path / ".env.example"
        self.main_env_path = self.workspace_path / ".env"
        self.docker_compose_path = self.workspace_path / "docker" / "agent" / "docker-compose.yml"
    
    def _get_compose_file(self) -> Path | None:
        """Get the docker-compose file path."""
        if self.docker_compose_path.exists():
            return self.docker_compose_path
        
        root_compose = self.workspace_path / "docker-compose.yml"
        if root_compose.exists():
            return root_compose
        
        return None
    
    def validate_agent_setup(self, force: bool = False) -> bool:
        """Validate agent setup using container health checks."""
        # Check that main .env exists
        if not self.main_env_path.exists():
            return False
        
        # Check that docker-compose.yml exists
        compose_file = self._get_compose_file()
        if not compose_file:
            return False
        
        # Validate database URL format instead of credentials
        return self._validate_database_url()
    
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
        """Validate agent environment configuration using container health."""
        if not self.main_env_path.exists():
            return {
                "valid": False,
                "errors": [f"Main environment file {self.main_env_path} not found"],
                "warnings": [],
                "config": None
            }
        
        compose_file = self._get_compose_file()
        if not compose_file:
            return {
                "valid": False,
                "errors": ["Docker compose file not found"],
                "warnings": [],
                "config": None
            }
        
        try:
            # Load main .env file
            main_config = self._load_env_file(self.main_env_path)
            required_keys = ["HIVE_API_KEY"]
            
            errors = []
            warnings = []
            
            # Check required keys in main .env
            for key in required_keys:
                if key not in main_config:
                    errors.append(f"Missing required key in main .env: {key}")
            
            # Validate database URL instead of credentials
            db_url = main_config.get("HIVE_DATABASE_URL")
            if db_url and not self._validate_database_url_format(db_url):
                errors.append("Invalid HIVE_DATABASE_URL format")
            
            # Check container health
            service_health = self._check_container_health(compose_file)
            for service in ["agent-postgres", "agent-api"]:
                health = service_health.get(service)
                if health and not health.running:
                    warnings.append(f"Service {service} is not running")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "config": main_config
            }
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Failed to validate environment: {e!s}"],
                "warnings": [],
                "config": None
            }
    
    def get_service_health(self) -> dict[str, ServiceHealth]:
        """Get health status of agent containers."""
        compose_file = self._get_compose_file()
        if not compose_file:
            return {}
        
        return self._check_container_health(compose_file)
    
    def update_environment(self, updates: dict) -> bool:
        """Update main .env file with provided values (agent inherits via docker-compose)."""
        if not self.main_env_path.exists():
            return False
        
        try:
            content = self.main_env_path.read_text()
            lines = content.split("\n")
            
            # Update existing keys and track what was processed
            processed_keys = set()
            for i, line in enumerate(lines):
                if "=" in line and not line.strip().startswith("#"):
                    key = line.split("=")[0].strip()
                    if key in updates:
                        lines[i] = f"{key}={updates[key]}"
                        processed_keys.add(key)
            
            # Add remaining keys that weren't found
            for key, value in updates.items():
                if key not in processed_keys:
                    lines.append(f"{key}={value}")
            
            # Write back to main .env file
            self.main_env_path.write_text("\n".join(lines))
            return True
            
        except Exception:
            return False
    
    def clean_environment(self) -> bool:
        """Clean up agent containers and volumes."""
        compose_file = self._get_compose_file()
        if not compose_file:
            return True
        
        try:
            subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "down", "-v"],
                check=False, capture_output=True, timeout=60
            )
            return True
        except Exception:
            return False
    
    def start_containers(self) -> bool:
        """Start agent containers using docker-compose."""
        compose_file = self._get_compose_file()
        if not compose_file:
            return False
        
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "up", "-d"],
                check=False, capture_output=True, text=True, timeout=120
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def stop_containers(self) -> bool:
        """Stop agent containers using docker-compose."""
        compose_file = self._get_compose_file()
        if not compose_file:
            return True
        
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "stop"],
                check=False, capture_output=True, timeout=60
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def restart_containers(self) -> bool:
        """Restart agent containers using docker-compose."""
        compose_file = self._get_compose_file()
        if not compose_file:
            return False
        
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "restart"],
                check=False, capture_output=True, timeout=120
            )
            return result.returncode == 0
        except Exception:
            return False
    
    # Internal helper methods
    def _validate_database_url(self) -> bool:
        """Validate database URL exists and has correct format."""
        if not self.main_env_path.exists():
            return False
        
        config = self._load_env_file(self.main_env_path)
        db_url = config.get("HIVE_DATABASE_URL")
        
        if not db_url:
            return False
        
        return self._validate_database_url_format(db_url)
    
    def _validate_database_url_format(self, url: str) -> bool:
        """Validate database URL format."""
        return url.startswith("postgresql") and "@" in url and "/" in url
    
    def _check_container_health(self, compose_file: Path) -> dict[str, ServiceHealth]:
        """Check health of containers using docker-compose."""
        health = {}
        
        for service_name in ["agent-postgres", "agent-api"]:
            try:
                # Get container ID
                result = subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "ps", "-q", service_name],
                    check=False, capture_output=True, text=True, timeout=10
                )
                
                if result.returncode != 0 or not result.stdout.strip():
                    health[service_name] = ServiceHealth(service_name, False, False)
                    continue
                
                container_id = result.stdout.strip()
                
                # Check if running
                inspect_result = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Running}}", container_id],
                    check=False, capture_output=True, text=True, timeout=5
                )
                
                running = (
                    inspect_result.returncode == 0 and 
                    inspect_result.stdout.strip() == "true"
                )
                
                health[service_name] = ServiceHealth(
                    service_name, running, running, container_id
                )
                
            except Exception:
                health[service_name] = ServiceHealth(service_name, False, False)
        
        return health
    
    def _load_env_file(self, file_path: Path) -> dict:
        """Load environment file as key-value dictionary."""
        config = {}
        if file_path.exists():
            for line in file_path.read_text().split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
        return config
    
    def get_container_logs(self, service_name: str, tail: int | None = None) -> str:
        """Get logs from a specific container service."""
        compose_file = self._get_compose_file()
        if not compose_file:
            return "No compose file found"
        
        try:
            cmd = ["docker", "compose", "-f", str(compose_file), "logs"]
            if tail is not None:
                cmd.extend(["--tail", str(tail)])
            cmd.append(service_name)
            
            result = subprocess.run(
                cmd, check=False, capture_output=True, text=True, timeout=30
            )
            
            return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
        except Exception as e:
            return f"Error getting logs: {e}"
    
    def get_all_container_logs(self, tail: int | None = None) -> dict[str, str]:
        """Get logs from all agent containers."""
        logs = {}
        for service_name in ["agent-postgres", "agent-api"]:
            logs[service_name] = self.get_container_logs(service_name, tail)
        return logs
    
    def get_container_status_summary(self) -> dict[str, str]:
        """Get a summary of container status."""
        health = self.get_service_health()
        status = {}
        
        for service_name, service_health in health.items():
            if service_health.running:
                status[service_name] = "✅ Running"
            else:
                status[service_name] = "🛑 Stopped"
        
        return status


# Convenience functions
def create_agent_environment(workspace_path: Path | None = None) -> AgentEnvironment:
    """Create agent environment with container management."""
    env = AgentEnvironment(workspace_path)
    env.ensure_main_env()  # Ensure main .env exists
    return env


def validate_agent_environment(workspace_path: Path | None = None) -> bool:
    """Validate agent environment using container health checks."""
    env = AgentEnvironment(workspace_path)
    return env.validate_agent_setup()


def cleanup_agent_environment(workspace_path: Path | None = None) -> bool:
    """Cleanup agent environment containers."""
    env = AgentEnvironment(workspace_path)
    return env.clean_environment()


def get_agent_status() -> dict[str, str]:
    """Get agent container status."""
    env = AgentEnvironment()
    return env.get_container_status_summary()
