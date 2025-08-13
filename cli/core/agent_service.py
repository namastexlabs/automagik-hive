"""Agent Service Management Stubs.

Minimal stub implementations to fix import errors in tests.
These are placeholders that satisfy import requirements.
"""

import os
import signal
import time
from typing import Optional, Dict, Any
from pathlib import Path


class DockerComposeManager:
    """Docker Compose management stub for testing compatibility."""
    
    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path(".")
    
    def get_service_status(self, service_name: str = "postgres-agent"):
        """Get service status stub."""
        class MockStatus:
            name = "RUNNING"
        return MockStatus()


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
            
        # Setup both postgres and dev server
        if not self._setup_agent_containers(workspace_path):
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
        """Create .env.agent with simple fixed test credentials."""
        try:
            workspace = Path(workspace_path)
            env_agent = workspace / ".env.agent"
            
            # Simple fixed configuration for agent testing
            agent_content = """# Agent Environment - Fixed Test Credentials
# Simple configuration for agent development and testing

# -------------------------------------------------------------------------
# CORE APPLICATION SETTINGS
# -------------------------------------------------------------------------
HIVE_ENVIRONMENT=development
HIVE_LOG_LEVEL=INFO
AGNO_LOG_LEVEL=INFO

# -------------------------------------------------------------------------
# SERVER & API (Agent-specific ports)
# -------------------------------------------------------------------------
HIVE_API_HOST=0.0.0.0
HIVE_API_PORT=38886
HIVE_API_WORKERS=1

# -------------------------------------------------------------------------
# DATABASE (Agent-specific with fixed test credentials)
# -------------------------------------------------------------------------
HIVE_DATABASE_URL=postgresql+psycopg://test_user:test_pass@localhost:35532/hive_agent

# Docker PostgreSQL user permissions
POSTGRES_UID=1000
POSTGRES_GID=1000

# -------------------------------------------------------------------------
# AI PROVIDER KEYS & DEFAULTS
# -------------------------------------------------------------------------
HIVE_DEFAULT_MODEL=gpt-5

# AI Provider API Keys (inherit from environment if needed)
# ANTHROPIC_API_KEY=
# GEMINI_API_KEY=
# OPENAI_API_KEY=
# GROK_API_KEY=
# GROQ_API_KEY=
# COHERE_API_KEY=

# -------------------------------------------------------------------------
# SECURITY & AUTHENTICATION
# -------------------------------------------------------------------------
HIVE_API_KEY=agent-test-key-12345
HIVE_CORS_ORIGINS=http://localhost:3000,http://localhost:38886
HIVE_AUTH_DISABLED=true

# -------------------------------------------------------------------------
# DEVELOPMENT MODE
# -------------------------------------------------------------------------
HIVE_DEV_MODE=true

# -------------------------------------------------------------------------
# METRICS & MONITORING
# -------------------------------------------------------------------------
HIVE_ENABLE_METRICS=true
HIVE_AGNO_MONITOR=false

# MCP Configuration path
HIVE_MCP_CONFIG_PATH=ai/.mcp.json
"""
            
            # Write simple fixed content to .env.agent
            env_agent.write_text(agent_content)
            
            return True
            
        except (IOError, OSError):
            return False
    
    def _setup_agent_containers(self, workspace_path: str) -> bool:
        """Setup agent postgres AND dev server using docker compose command."""
        import subprocess
        import os
        from pathlib import Path
        
        try:
            # Define the docker compose command to start BOTH services
            workspace = Path(workspace_path)
            compose_file = workspace / "docker" / "agent" / "docker-compose.yml"
            
            # PostgreSQL uses ephemeral storage - no external data directory needed
            print("✅ Using ephemeral PostgreSQL storage - fresh database on each restart")
            
            # Execute docker compose command to start ALL services (postgres-agent AND agent-dev-server)
            print("🚀 Starting both postgres-agent and agent-dev-server containers...")
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "up", "-d"],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            if result.returncode != 0:
                print(f"❌ Docker compose failed: {result.stderr}")
                return False
                
            print("✅ Both agent containers started successfully")
            return True
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"❌ Error starting agent containers: {e}")
            return False
    
    def _generate_agent_api_key(self, workspace_path: str) -> bool:
        """Generate dynamic API key and update both .env.agent files."""
        import secrets
        
        try:
            workspace = Path(workspace_path)
            
            # Check if .env.agent file exists at workspace root - required for update
            env_agent_root = workspace / ".env.agent"
            if not env_agent_root.exists():
                return False
            
            # Generate secure API key using secrets.token_urlsafe()
            api_key = f"hive_agent_{secrets.token_urlsafe(32)}"
            
            # Update workspace root .env.agent file
            # Read existing content
            content = env_agent_root.read_text()
            
            # Replace HIVE_API_KEY line with new dynamic key
            lines = content.split('\n')
            updated_lines = []
            key_updated = False
            
            for line in lines:
                if line.startswith('HIVE_API_KEY='):
                    updated_lines.append(f'HIVE_API_KEY={api_key}')
                    key_updated = True
                else:
                    updated_lines.append(line)
            
            # If key wasn't found, add it to security section
            if not key_updated:
                # Find security section and add key
                security_index = -1
                for i, line in enumerate(updated_lines):
                    if '# SECURITY & AUTHENTICATION' in line:
                        security_index = i
                        break
                
                if security_index >= 0:
                    # Insert after the security header
                    updated_lines.insert(security_index + 2, f'HIVE_API_KEY={api_key}')
                else:
                    # Append at the end
                    updated_lines.append(f'HIVE_API_KEY={api_key}')
            
            # Write back updated content
            env_agent_root.write_text('\n'.join(updated_lines))
            
            # Update docker/agent/.env file
            docker_agent_dir = workspace / "docker" / "agent"
            docker_agent_dir.mkdir(parents=True, exist_ok=True)
            env_agent_docker = docker_agent_dir / ".env"
            
            # Simple fixed Docker environment configuration with dynamic API key
            docker_env_content = f"""# Simple Docker Agent Environment - Dynamic API Key
POSTGRES_HOST=postgres-agent
POSTGRES_PORT=5432
POSTGRES_DB=hive_agent
POSTGRES_USER=test_user
POSTGRES_PASSWORD=test_pass

HIVE_API_HOST=0.0.0.0
HIVE_API_PORT=38886
HIVE_API_WORKERS=1
HIVE_ENVIRONMENT=development

HIVE_API_KEY={api_key}

HIVE_LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
"""
            
            # Write dynamic content to docker/agent/.env
            env_agent_docker.write_text(docker_env_content)
            
            return True
            
        except (IOError, OSError):
            return False

    # Validation methods
    def _validate_agent_environment(self, workspace_path: Path) -> bool:
        """Validate agent environment by checking required files and directories.
        
        Args:
            workspace_path: Path to the workspace directory
            
        Returns:
            bool: True if both .env.agent file and .venv directory exist, False otherwise
        """
        try:
            # Check if .env.agent file exists at workspace root
            env_agent_file = workspace_path / ".env.agent"
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

    # Simple credential setup - no complex generation needed

    # Server management methods
    def serve_agent(self, workspace_path: str) -> bool:
        """Serve agent containers with environment validation."""
        # Validate agent environment first
        if not self._validate_agent_environment(Path(workspace_path)):
            print("❌ Agent environment validation failed")
            return False
        
        # Check if containers are already running
        status = self.get_agent_status(workspace_path)
        postgres_running = "✅ Running" in status.get("agent-postgres", "")
        server_running = "✅ Running" in status.get("agent-server", "")
        
        if postgres_running and server_running:
            print("✅ Both agent containers are already running")
            return True
            
        # Start containers using Docker Compose
        return self._setup_agent_containers(workspace_path)
    
    def stop_agent(self, workspace_path: str) -> bool:
        """Stop agent containers with proper error handling."""
        import subprocess
        from pathlib import Path
        
        try:
            workspace = Path(workspace_path)
            compose_file = workspace / "docker" / "agent" / "docker-compose.yml"
            
            if not compose_file.exists():
                print("❌ Docker compose file not found")
                return False
            
            print("🛑 Stopping agent containers...")
            
            # Stop all containers using Docker Compose
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "stop"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("✅ Agent containers stopped successfully")
                return True
            else:
                print(f"❌ Failed to stop containers: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error stopping agent containers: {e}")
            return False
    
    def restart_agent(self, workspace_path: str) -> bool:
        """Restart agent containers with proper error handling."""
        import subprocess
        from pathlib import Path
        import time
        
        try:
            workspace = Path(workspace_path)
            compose_file = workspace / "docker" / "agent" / "docker-compose.yml"
            
            if not compose_file.exists():
                print("❌ Docker compose file not found")
                return False
            
            print("🔄 Restarting agent containers...")
            
            # Restart all containers using Docker Compose
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "restart"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print("✅ Agent containers restarted successfully")
                return True
            else:
                print(f"❌ Failed to restart containers: {result.stderr}")
                # Fallback: try stop and start
                print("🔄 Attempting fallback: stop and start...")
                self.stop_agent(workspace_path)
                time.sleep(2)
                return self.serve_agent(workspace_path)
                
        except Exception as e:
            print(f"❌ Error restarting agent containers: {e}")
            return False

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
        """Show agent logs from Docker containers with proper error handling."""
        import subprocess
        from pathlib import Path
        
        try:
            workspace = Path(workspace_path)
            compose_file = workspace / "docker" / "agent" / "docker-compose.yml"
            
            if not compose_file.exists():
                print("❌ Docker compose file not found")
                return False
            
            print("📋 Agent Container Logs:")
            print("=" * 80)
            
            # Show logs for both containers
            for service_name, display_name in [
                ("postgres-agent", "PostgreSQL Database"),
                ("agent-dev-server", "FastAPI Development Server")
            ]:
                print(f"\n🔍 {display_name} ({service_name}):")
                print("-" * 50)
                
                # Build Docker Compose logs command
                cmd = ["docker", "compose", "-f", str(compose_file), "logs"]
                if tail is not None:
                    cmd.extend(["--tail", str(tail)])
                cmd.append(service_name)
                
                # Execute logs command
                result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    if result.stdout.strip():
                        print(result.stdout)
                    else:
                        print("(No logs available)")
                else:
                    print(f"❌ Failed to get logs: {result.stderr}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error getting agent logs: {e}")
            return False
    
    def get_agent_status(self, workspace_path: str) -> Dict[str, str]:
        """Get agent status with Docker Compose integration."""
        status = {}
        
        try:
            import subprocess
            from pathlib import Path
            workspace = Path(workspace_path)
            compose_file = workspace / "docker" / "agent" / "docker-compose.yml"
            
            # Check both containers using Docker Compose
            for service_name, display_name, port in [
                ("postgres-agent", "agent-postgres", "35532"), 
                ("agent-dev-server", "agent-server", "38886")
            ]:
                try:
                    # Use docker compose ps to check if service is running
                    result = subprocess.run(
                        ["docker", "compose", "-f", str(compose_file), "ps", "-q", service_name],
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
                            status[display_name] = f"✅ Running (Port: {port})"
                        else:
                            status[display_name] = "🛑 Stopped"
                    else:
                        status[display_name] = "🛑 Stopped"
                except Exception:
                    status[display_name] = "🛑 Stopped"
                
        except Exception:
            # Fallback to stopped status on any error
            status = {"agent-postgres": "🛑 Stopped", "agent-server": "🛑 Stopped"}
        
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
            
            # Note: No external data directory to clean up - PostgreSQL uses ephemeral storage
            
            return True
            
        except Exception:
            # Return True even on exceptions - cleanup should be best-effort
            return True
