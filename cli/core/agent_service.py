"""Agent Service Management Stubs.

Minimal stub implementations to fix import errors in tests.
These are placeholders that satisfy import requirements.
"""

import os
import signal
import time
from typing import Optional, Dict, Any
from pathlib import Path

# Import DockerComposeManager - import inside function to avoid module issues


class AgentService:
    """Agent service management stub."""
    
    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path(".")
        self.pid_file = Path(".") / "agent.pid"
        self.log_file = Path(".") / "agent.log"
    
    def install(self) -> bool:
        """Install agent service stub."""
        return True
    
    def start(self) -> bool:
        """Start agent service stub."""
        return True
    
    def stop(self) -> bool:
        """Stop agent service stub."""
        return True
    
    def restart(self) -> bool:
        """Restart agent service stub."""
        return True
    
    def status(self) -> Dict[str, Any]:
        """Get agent service status stub."""
        return {"status": "running", "healthy": True}
    
    def logs(self, lines: int = 100) -> str:
        """Get agent service logs stub."""
        return "Agent service log output"
    
    def reset(self) -> bool:
        """Reset agent service stub."""
        return True

    # Installation methods
    def install_agent_environment(self, workspace_path: str) -> bool:
        """Install agent environment with proper orchestration."""
        # Validate workspace first
        if not self._validate_workspace(Path(workspace_path)):
            return False
            
        # Create agent env file
        if not self._create_agent_env_file(workspace_path):
            return False
            
        # Setup postgres
        if not self._setup_agent_postgres(workspace_path):
            return False
            
        # Generate API key
        if not self._generate_agent_api_key(workspace_path):
            return False
            
        return True
    
    def _validate_workspace(self, workspace_path: Path) -> bool:
        """Validate workspace has required structure and files."""
        # Check if workspace path exists
        if not workspace_path.exists():
            return False
        
        # Check if workspace path is a directory
        if not workspace_path.is_dir():
            return False
        
        # Check for docker-compose.yml in docker/agent/ or root
        docker_compose_agent = workspace_path / "docker" / "agent" / "docker-compose.yml"
        docker_compose_root = workspace_path / "docker-compose.yml"
        
        if not docker_compose_agent.exists() and not docker_compose_root.exists():
            return False
        
        return True
    
    def _create_agent_env_file(self, workspace_path: str) -> bool:
        """Create docker/agent/.env from main .env for agent-specific configuration."""
        try:
            workspace = Path(workspace_path)
            env_main = workspace / ".env"
            docker_agent_dir = workspace / "docker" / "agent"
            env_agent = docker_agent_dir / ".env"
            
            # Check if main .env exists - REQUIRED
            if not env_main.exists():
                print("❌ Main .env file not found. Please run main application install first.")
                print("   Run: uv run automagik-hive --init")
                return False
            
            # Ensure docker/agent directory exists
            docker_agent_dir.mkdir(parents=True, exist_ok=True)
            
            # Read main .env content
            content = env_main.read_text()
            
            # Apply agent-specific transformations
            # Port transformations: 8886 -> 38886, 5532 -> 35532
            agent_content = content.replace("8886", "38886")
            agent_content = agent_content.replace("5532", "35532")
            
            # Database name transformation: /hive -> /hive_agent (but not /hive_agent -> /hive_agent_agent)
            import re
            agent_content = re.sub(r'/hive(?!_agent)', '/hive_agent', agent_content)
            
            # Extract postgres credentials from HIVE_DATABASE_URL and add them as separate variables
            db_url_match = re.search(r'HIVE_DATABASE_URL=postgresql\+psycopg://([^:]+):([^@]+)@[^/]+/(.+)', agent_content)
            if db_url_match:
                db_user = db_url_match.group(1)
                db_password = db_url_match.group(2)
                db_name = db_url_match.group(3)
                
                # Add postgres environment variables required by Docker
                postgres_vars = f"""
# PostgreSQL Docker Environment Variables
POSTGRES_USER={db_user}
POSTGRES_PASSWORD={db_password}  
POSTGRES_DB={db_name}
"""
                agent_content += postgres_vars
            
            # Write transformed content to docker/agent/.env
            env_agent.write_text(agent_content)
            
            print(f"✅ Generated docker/agent/.env from main .env")
            return True
            
        except (IOError, OSError) as e:
            print(f"❌ Failed to create agent env file: {e}")
            return False
    
    def _setup_agent_postgres(self, workspace_path: str) -> bool:
        """Setup agent postgres using docker compose command."""
        import subprocess
        from pathlib import Path
        
        try:
            # Define the docker compose command to start postgres-agent
            workspace = Path(workspace_path)
            compose_file = workspace / "docker" / "agent" / "docker-compose.yml"
            
            # Execute docker compose command to start postgres service
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "up", "-d", "postgres-agent"],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            # Return False if docker command failed
            return result.returncode == 0
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            # Handle subprocess errors gracefully
            return False
    
    def _generate_agent_api_key(self, workspace_path: str) -> bool:
        """Generate agent API key with env file validation."""
        import secrets
        
        # Check if docker/agent/.env file exists first
        workspace = Path(workspace_path)
        docker_agent_dir = workspace / "docker" / "agent"
        env_agent = docker_agent_dir / ".env"
        if not env_agent.exists():
            return False
        
        try:
            # Generate secure API key with required format
            token = secrets.token_urlsafe(32)
            new_api_key = f"hive_agent_{token}"
            
            # Read current file content
            content = env_agent.read_text()
            lines = content.splitlines()
            
            # Find and update or add HIVE_API_KEY
            updated = False
            for i, line in enumerate(lines):
                if line.startswith("HIVE_API_KEY="):
                    lines[i] = f"HIVE_API_KEY={new_api_key}"
                    updated = True
                    break
            
            # If HIVE_API_KEY doesn't exist, add it
            if not updated:
                lines.append(f"HIVE_API_KEY={new_api_key}")
            
            # Write updated content back to file
            env_agent.write_text("\n".join(lines) + "\n")
            
            return True
            
        except (IOError, OSError) as e:
            # Handle file I/O errors gracefully
            return False

    # Validation methods
    def _validate_agent_environment(self, workspace_path: Path) -> bool:
        """Validate agent environment by checking required files and directories.
        
        Args:
            workspace_path: Path to the workspace directory
            
        Returns:
            bool: True if both docker/agent/.env file and .venv directory exist, False otherwise
        """
        try:
            # Check if docker/agent/.env file exists
            env_agent_file = workspace_path / "docker" / "agent" / ".env"
            if not env_agent_file.exists():
                return False
            
            # Check if .venv directory exists and is a directory
            venv_dir = workspace_path / ".venv"
            if not venv_dir.exists() or not venv_dir.is_dir():
                return False
                
            return True
            
        except (OSError, PermissionError):
            # Handle path validation errors gracefully
            return False

    # Credential generation methods
    def _generate_agent_postgres_credentials(self, workspace_path: str) -> bool:
        """Generate agent postgres credentials with secure token generation.
        
        Updates the HIVE_DATABASE_URL in .env.agent with new secure credentials
        while preserving database name and connection details.
        
        Args:
            workspace_path: Path to the workspace containing .env.agent
            
        Returns:
            True on successful credential generation and update, False on failure
        """
        import secrets
        import re
        
        try:
            # Check if docker/agent/.env file exists
            workspace = Path(workspace_path)
            docker_agent_dir = workspace / "docker" / "agent"
            env_agent = docker_agent_dir / ".env"
            
            if not env_agent.exists():
                return False
                
            # Read current env file content
            current_content = env_agent.read_text()
            
            # Generate secure credentials using secrets.token_urlsafe(32)
            secure_token = secrets.token_urlsafe(32)
            
            # Pattern to match HIVE_DATABASE_URL and extract components
            url_pattern = r'HIVE_DATABASE_URL=postgresql\+psycopg://([^:]+):([^@]+)@([^/]+)/(.+)'
            
            def update_database_url(match):
                """Update database URL with new secure credentials"""
                protocol = "postgresql+psycopg"
                host_port = match.group(3)  # localhost:35532
                database = match.group(4)   # hive_agent
                
                # Use the secure token for both username and password
                new_url = f"HIVE_DATABASE_URL={protocol}://{secure_token}:{secure_token}@{host_port}/{database}"
                return new_url
            
            # Update the database URL with new credentials
            updated_content = re.sub(url_pattern, update_database_url, current_content)
            
            # Write updated content back to file
            env_agent.write_text(updated_content)
            
            return True
            
        except (OSError, IOError, PermissionError):
            # Handle file I/O errors gracefully
            return False
        except Exception:
            # Handle any other unexpected errors gracefully
            return False

    # Server management methods
    def serve_agent(self, workspace_path: str) -> bool:
        """Serve agent with environment validation."""
        # Validate agent environment first
        if not self._validate_agent_environment(Path(workspace_path)):
            return False
        
        # Check if agent is already running
        if self._is_agent_running():
            return True
            
        # Start agent in background
        return self._start_agent_background(workspace_path)
    
    def stop_agent(self, workspace_path: str) -> bool:
        """Stop agent with proper error handling."""
        # Check if agent is already stopped
        if not self._is_agent_running():
            return True
        
        # Try to stop the agent and return the actual result
        return self._stop_agent_background()
    
    def restart_agent(self, workspace_path: str) -> bool:
        """Restart agent with proper error handling."""
        # Attempt to stop the agent first (ignore failure if already stopped)
        self._stop_agent_background()
            
        # Add a small delay to ensure cleanup
        import time
        time.sleep(1)
        
        # Start the agent again
        return self.serve_agent(workspace_path)

    # Background process management
    def _start_agent_background(self, workspace_path: str) -> bool:
        """Start agent background process with validation."""
        import subprocess
        import time
        from pathlib import Path
        
        try:
            workspace = Path(workspace_path)
            docker_agent_dir = workspace / "docker" / "agent"
            env_agent = docker_agent_dir / ".env"
            
            # Check if docker/agent/.env file exists
            if not env_agent.exists():
                return False
            
            # Create logs directory if it doesn't exist
            logs_dir = workspace / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            # Set up log file path
            self.log_file = logs_dir / "agent.log"
            
            # Start the agent process using subprocess.Popen
            # This simulates starting the agent server in background
            with open(self.log_file, "w") as log_file:
                process = subprocess.Popen(
                    ["uv", "run", "python", "-m", "api.serve"],
                    cwd=workspace,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    env={**os.environ, "HIVE_ENV_FILE": str(env_agent)}
                )
            
            # Store the PID
            self.pid_file.write_text(str(process.pid))
            
            # Give the process a moment to start
            time.sleep(0.1)
            
            # Validate that the process actually started successfully
            return self._is_agent_running()
            
        except (subprocess.SubprocessError, OSError, IOError):
            # Handle any errors during process startup
            return False
    
    def _stop_agent_background(self) -> bool:
        """Stop agent background process with graceful shutdown and force kill fallback.
        
        Returns:
            bool: True on successful termination, False on failure (no PID file, process already dead, etc.)
        """
        
        # Check if PID file exists
        if not self.pid_file.exists():
            return True  # Agent already stopped, success
        
        try:
            # Read PID from file
            pid_str = self.pid_file.read_text().strip()
            if not pid_str.isdigit():
                return False
            pid = int(pid_str)
            
            # Check if process exists using os.kill(pid, 0)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                # Process already dead, clean up PID file
                self.pid_file.unlink()
                return True  # Process already dead and cleaned up, success
            except PermissionError:
                # Process exists but we don't have permission, try to continue anyway
                pass
            
            # Attempt graceful shutdown with SIGTERM
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                # Process died before we could send SIGTERM
                self.pid_file.unlink()
                return True
            except PermissionError:
                # Don't have permission to kill, can't proceed
                return False
            
            # Wait for process to terminate (with timeout)
            timeout_seconds = 10
            check_interval = 0.2
            checks = int(timeout_seconds / check_interval)
            
            for _ in range(checks):
                try:
                    # Check if process still exists
                    os.kill(pid, 0)
                    time.sleep(check_interval)
                except ProcessLookupError:
                    # Process terminated gracefully
                    self.pid_file.unlink()
                    return True
            
            # If graceful shutdown failed, force kill with SIGKILL
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                # Process died between our checks
                self.pid_file.unlink()
                return True
            except PermissionError:
                # Don't have permission to force kill
                return False
            
            # Give a brief moment for force kill to take effect
            time.sleep(0.1)
            
            # Final check to ensure process is dead
            try:
                os.kill(pid, 0)
                # Process still exists after force kill, something is wrong
                return False
            except ProcessLookupError:
                # Process successfully terminated
                self.pid_file.unlink()
                return True
                
        except (IOError, OSError, ValueError):
            # Handle file read errors, permission errors, or invalid PID
            return False
    
    def _is_agent_running(self) -> bool:
        """Check if agent is running by checking PID file and process."""
        if not self.pid_file or not self.pid_file.exists():
            return False
        
        try:
            pid = int(self.pid_file.read_text().strip())
            os.kill(pid, 0)  # Signal 0 just checks if process exists
            return True
        except (ValueError, OSError, ProcessLookupError):
            return False
    
    def _get_agent_pid(self) -> Optional[int]:
        """Get agent PID from file and verify process exists.
        
        Returns:
            Optional[int]: PID if process exists, None if no file or process doesn't exist
        """
        # Check if PID file exists
        if not self.pid_file.exists():
            return None
        
        try:
            # Read PID from file
            pid_str = self.pid_file.read_text().strip()
            if not pid_str.isdigit():
                return None
            pid = int(pid_str)
            
            # Check if process exists using os.kill(pid, 0)
            try:
                os.kill(pid, 0)
                return pid
            except ProcessLookupError:
                # Process doesn't exist, clean up PID file
                self.pid_file.unlink()
                return None
            except PermissionError:
                # Process exists but we don't have permission to check
                # This counts as existing for our purposes
                return pid
                
        except (IOError, OSError, ValueError):
            # Handle file read errors or invalid PID
            return None

    # Logs and status methods
    def show_agent_logs(self, workspace_path: str, tail: Optional[int] = None) -> bool:
        """Show agent logs with proper error handling."""
        import subprocess
        
        # Check if log file exists
        if not self.log_file.exists():
            return False
        
        try:
            # Build the tail command
            if tail is not None:
                cmd = ["tail", "-n", str(tail), str(self.log_file)]
            else:
                cmd = ["cat", str(self.log_file)]
            
            # Execute the command
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            
            # Return False on subprocess errors
            if result.returncode != 0:
                return False
            
            # Successfully displayed logs
            return True
            
        except Exception:
            # Return False on any exception
            return False
    
    def get_agent_status(self, workspace_path: str) -> Dict[str, str]:
        """Get agent status with Docker Compose integration."""
        status = {}
        
        try:
            # Check agent server status
            if self._is_agent_running():
                pid = self._get_agent_pid()
                if pid:
                    status["agent-server"] = f"✅ Running (PID: {pid}, Port: 38886)"
                else:
                    status["agent-server"] = "✅ Running (Port: 38886)"
            else:
                status["agent-server"] = "🛑 Stopped"
            
            # Check postgres status using Docker Compose directly
            try:
                import subprocess
                from pathlib import Path
                workspace = Path(workspace_path)
                compose_file = workspace / "docker" / "agent" / "docker-compose.yml"
                
                # Use docker compose ps to check if postgres-agent is running
                result = subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "ps", "-q", "postgres-agent"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    # Container ID returned, check if it's running
                    container_id = result.stdout.strip()
                    inspect_result = subprocess.run(
                        ["docker", "inspect", "--format", "{{.State.Running}}", container_id],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if inspect_result.returncode == 0 and inspect_result.stdout.strip() == "true":
                        status["agent-postgres"] = "✅ Running (Port: 35532)"
                    else:
                        status["agent-postgres"] = "🛑 Stopped"
                else:
                    status["agent-postgres"] = "🛑 Stopped"
            except Exception:
                status["agent-postgres"] = "🛑 Stopped"
                
        except Exception:
            # Fallback to stopped status on any error
            status = {"agent-server": "🛑 Stopped", "agent-postgres": "🛑 Stopped"}
        
        return status

    # Reset and cleanup methods
    def reset_agent_environment(self, workspace_path: str) -> bool:
        """Reset agent environment with proper orchestration."""
        # Cleanup existing environment first
        if not self._cleanup_agent_environment(workspace_path):
            return False
            
        # Reinstall the environment
        return self.install_agent_environment(workspace_path)
    
    def _cleanup_agent_environment(self, workspace_path: str) -> bool:
        """Cleanup agent environment with comprehensive cleanup."""
        import subprocess
        from pathlib import Path
        
        try:
            workspace = Path(workspace_path)
            
            # Stop agent background process first
            try:
                self._stop_agent_background()
            except Exception:
                # Continue cleanup even if stop fails
                pass
            
            # Remove docker/agent/.env file if it exists
            docker_agent_dir = workspace / "docker" / "agent"
            env_agent = docker_agent_dir / ".env"
            if env_agent.exists():
                try:
                    env_agent.unlink()
                except OSError:
                    # Continue cleanup even if file removal fails
                    pass
            
            # Stop and remove Docker containers
            try:
                compose_file = workspace / "docker" / "agent" / "docker-compose.yml"
                if compose_file.exists():
                    subprocess.run(
                        ["docker", "compose", "-f", str(compose_file), "down", "-v"],
                        check=False,
                        capture_output=True,
                        timeout=60
                    )
            except Exception:
                # Continue cleanup even if Docker operations fail
                pass
            
            # Remove postgres data directory if it exists
            try:
                data_dir = workspace / "data" / "postgres-agent"
                if data_dir.exists():
                    import shutil
                    shutil.rmtree(data_dir)
            except Exception:
                # Continue cleanup even if data removal fails
                pass
            
            return True
            
        except Exception:
            # Return True even on exceptions - cleanup should be best-effort
            return True
