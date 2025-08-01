"""Agent Service for CLI Operations.

This module provides high-level Agent service operations
for CLI commands, wrapping Docker Compose and process management functionality.
"""

import os
import signal
import subprocess
import time
from pathlib import Path

from docker.lib.compose_manager import DockerComposeManager


class AgentService:
    """High-level Agent service operations for CLI.
    
    Provides user-friendly Agent container and process management
    with integrated workspace validation and service orchestration.
    """

    def __init__(self):
        self.compose_manager = DockerComposeManager()
        self.agent_compose_file = "docker/agent/docker-compose.yml"
        self.agent_port = 38886
        self.agent_postgres_port = 35532
        self.logs_dir = Path("logs")
        self.pid_file = self.logs_dir / "agent-server.pid"
        self.log_file = self.logs_dir / "agent-server.log"

    def install_agent_environment(self, workspace_path: str) -> bool:
        """Install complete agent environment with isolated ports and database.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            True if installation successful, False otherwise
        """
        workspace = Path(workspace_path).resolve()
        if not self._validate_workspace(workspace, check_env=False):
            return False

        print("🤖 Setting up agent environment...")
        
        # Create agent environment file
        if not self._create_agent_env_file(str(workspace)):
            return False
            
        # Setup agent PostgreSQL
        if not self._setup_agent_postgres(str(workspace)):
            return False
            
        # Generate agent API key
        if not self._generate_agent_api_key(str(workspace)):
            return False
            
        print("✅ Agent environment ready!")
        print(f"🌐 Agent API will be available at: http://localhost:{self.agent_port}")
        print("💡 Start with: uvx automagik-hive --agent-serve")
        
        return True

    def serve_agent(self, workspace_path: str) -> bool:
        """Start agent server in background (non-blocking).
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            True if started successfully, False otherwise
        """
        workspace = Path(workspace_path).resolve()
        if not self._validate_agent_environment(workspace):
            return False

        # Check if already running
        if self._is_agent_running():
            pid = self._get_agent_pid()
            print(f"⚠️ Agent server already running (PID: {pid})")
            print(f"🌐 Agent API: http://localhost:{self.agent_port}")
            return True

        return self._start_agent_background(str(workspace))

    def stop_agent(self, workspace_path: str | None = None) -> bool:
        """Stop agent server cleanly.
        
        Args:
            workspace_path: Path to workspace directory (optional)
            
        Returns:
            True if stopped successfully, False otherwise
        """
        return self._stop_agent_background()

    def restart_agent(self, workspace_path: str) -> bool:
        """Restart agent server.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            True if restarted successfully, False otherwise
        """
        self._stop_agent_background()
        time.sleep(2)
        return self.serve_agent(workspace_path)

    def show_agent_logs(self, workspace_path: str | None = None, tail: int = 50) -> bool:
        """Show agent logs (non-blocking).
        
        Args:
            workspace_path: Path to workspace directory (optional)
            tail: Number of lines to show
            
        Returns:
            True if logs displayed, False otherwise
        """
        print("🤖 Agent Server Logs")
        
        if self.log_file.exists():
            print(f"📋 Recent Agent Logs (last {tail} lines):")
            print("-" * 50)
            try:
                result = subprocess.run(
                    ["tail", f"-{tail}", str(self.log_file)],
                    capture_output=True, text=True, check=False
                )
                if result.returncode == 0:
                    print(result.stdout)
                    return True
                else:
                    print(f"❌ Could not read log file: {result.stderr}")
                    return False
            except Exception as e:
                print(f"❌ Error reading logs: {e}")
                return False
        else:
            print("⚠️ No agent log file found")
            print("💡 Start agent server with 'uvx automagik-hive --agent-serve'")
            return False

    def get_agent_status(self, workspace_path: str | None = None) -> dict[str, str]:
        """Get agent environment status.
        
        Args:
            workspace_path: Path to workspace directory (optional)
            
        Returns:
            Dict with service status information
        """
        status = {}
        
        # Check agent server status
        if self._is_agent_running():
            pid = self._get_agent_pid()
            status["agent-server"] = f"✅ Running (PID: {pid}, Port: {self.agent_port})"
        else:
            status["agent-server"] = "🛑 Stopped"
            
        # Check agent postgres status
        workspace = workspace_path or "."
        postgres_status = self.compose_manager.get_service_status(
            "postgres-agent", str(Path(workspace).resolve())
        )
        
        if postgres_status.name == "RUNNING":
            status["agent-postgres"] = f"✅ Running (Port: {self.agent_postgres_port})"
        else:
            status["agent-postgres"] = "🛑 Stopped"
            
        return status

    def reset_agent_environment(self, workspace_path: str) -> bool:
        """Reset agent environment (destructive reinstall).
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            True if reset successful, False otherwise
        """
        workspace = Path(workspace_path).resolve()
        
        print("🔄 Resetting agent environment...")
        
        # Stop everything first
        self._cleanup_agent_environment(str(workspace))
        
        # Reinstall
        return self.install_agent_environment(str(workspace))

    def _validate_workspace(self, workspace: Path, check_env: bool = True) -> bool:
        """Validate workspace directory and required files."""
        if not workspace.exists():
            print(f"❌ Workspace directory does not exist: {workspace}")
            return False

        if not workspace.is_dir():
            print(f"❌ Workspace path is not a directory: {workspace}")
            return False

        # Check for docker-compose.yml
        compose_file = workspace / "docker-compose.yml"
        if not compose_file.exists():
            print(f"❌ Missing docker-compose.yml in workspace: {workspace}")
            print("💡 Run 'uvx automagik-hive --init' to initialize workspace")
            return False

        return True

    def _validate_agent_environment(self, workspace: Path) -> bool:
        """Validate agent environment is properly set up."""
        agent_env = workspace / ".env.agent"
        if not agent_env.exists():
            print("❌ Agent environment not found")
            print("💡 Run 'uvx automagik-hive --agent-install' first")
            return False
            
        # Check if venv exists
        venv_path = workspace / ".venv"
        if not venv_path.exists():
            print("❌ Virtual environment not found")
            print("💡 Run 'uvx automagik-hive --agent-install' first")
            return False
            
        return True

    def _create_agent_env_file(self, workspace_path: str) -> bool:
        """Create .env.agent file with proper port configuration."""
        workspace = Path(workspace_path)
        env_example = workspace / ".env.example"
        env_agent = workspace / ".env.agent"
        
        if not env_example.exists():
            print("❌ .env.example not found")
            return False
            
        try:
            # Copy .env.example to .env.agent
            with open(env_example, 'r') as src, open(env_agent, 'w') as dst:
                content = src.read()
                # Update ports for agent environment
                content = content.replace('HIVE_API_PORT=8886', f'HIVE_API_PORT={self.agent_port}')
                content = content.replace('localhost:5532', f'localhost:{self.agent_postgres_port}')
                content = content.replace('/hive', '/hive_agent')
                content = content.replace('http://localhost:8886', f'http://localhost:{self.agent_port}')
                dst.write(content)
                
            print("✅ Agent environment file created")
            return True
        except Exception as e:
            print(f"❌ Failed to create agent environment file: {e}")
            return False

    def _setup_agent_postgres(self, workspace_path: str) -> bool:
        """Setup agent PostgreSQL container."""
        workspace = Path(workspace_path)
        
        # Generate credentials
        if not self._generate_agent_postgres_credentials(str(workspace)):
            return False
            
        print("🐳 Starting Agent PostgreSQL container...")
        
        # Extract database URL from .env.agent
        env_agent = workspace / ".env.agent"
        try:
            with open(env_agent, 'r') as f:
                content = f.read()
                
            # Find database URL
            for line in content.split('\n'):
                if line.startswith('HIVE_DATABASE_URL='):
                    db_url = line.split('=', 1)[1]
                    break
            else:
                print("❌ Could not find HIVE_DATABASE_URL in .env.agent")
                return False
                
            # Parse database URL
            # postgresql+psycopg://user:pass@localhost:35532/hive_agent
            url_part = db_url.split('://', 1)[1]  # user:pass@localhost:35532/hive_agent
            credentials_part = url_part.split('@', 1)[0]  # user:pass
            postgres_user = credentials_part.split(':', 1)[0]
            postgres_password = credentials_part.split(':', 1)[1]
            postgres_db = url_part.split('/')[-1]  # hive_agent
            
            # Set environment variables for docker-compose
            env = os.environ.copy()
            env.update({
                'POSTGRES_USER': postgres_user,
                'POSTGRES_PASSWORD': postgres_password,
                'POSTGRES_DB': postgres_db,
                'POSTGRES_UID': str(os.getuid() if hasattr(os, 'getuid') else 1000),
                'POSTGRES_GID': str(os.getgid() if hasattr(os, 'getgid') else 1000),
            })
            
            # Create data directory
            data_dir = workspace / "data" / "postgres-agent"
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Start container
            cmd = [
                "docker", "compose", "-f", self.agent_compose_file,
                "up", "-d", "postgres-agent"
            ]
            
            result = subprocess.run(
                cmd, cwd=workspace, env=env, 
                capture_output=True, text=True, check=False
            )
            
            if result.returncode == 0:
                print(f"✅ Agent PostgreSQL container started on port {self.agent_postgres_port}!")
                return True
            else:
                print(f"❌ Failed to start agent PostgreSQL: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error setting up agent PostgreSQL: {e}")
            return False

    def _generate_agent_postgres_credentials(self, workspace_path: str) -> bool:
        """Generate PostgreSQL credentials for agent environment."""
        workspace = Path(workspace_path)
        env_agent = workspace / ".env.agent"
        
        try:
            # Generate random credentials
            import secrets
            postgres_user = secrets.token_urlsafe(12)[:16]
            postgres_pass = secrets.token_urlsafe(12)[:16]
            postgres_db = "hive_agent"
            
            # Update .env.agent file
            with open(env_agent, 'r') as f:
                content = f.read()
                
            # Replace database URL
            new_url = f"postgresql+psycopg://{postgres_user}:{postgres_pass}@localhost:{self.agent_postgres_port}/{postgres_db}"
            
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('HIVE_DATABASE_URL='):
                    lines[i] = f"HIVE_DATABASE_URL={new_url}"
                    break
                    
            with open(env_agent, 'w') as f:
                f.write('\n'.join(lines))
                
            print("✅ Agent PostgreSQL credentials generated and saved to .env.agent")
            print("🔒 Generated agent credentials:")
            print(f"  User: {postgres_user}")
            print(f"  Password: {postgres_pass}")
            print(f"  Database: {postgres_db}")
            
            return True
        except Exception as e:
            print(f"❌ Failed to generate agent PostgreSQL credentials: {e}")
            return False

    def _generate_agent_api_key(self, workspace_path: str) -> bool:
        """Generate API key for agent environment."""
        workspace = Path(workspace_path)
        env_agent = workspace / ".env.agent"
        
        try:
            import secrets
            api_key = f"hive_agent_{secrets.token_urlsafe(32)}"
            
            # Update .env.agent file
            with open(env_agent, 'r') as f:
                content = f.read()
                
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('HIVE_API_KEY='):
                    lines[i] = f"HIVE_API_KEY={api_key}"
                    break
                    
            with open(env_agent, 'w') as f:
                f.write('\n'.join(lines))
                
            print(f"🔑 Agent API Key: {api_key}")
            return True
        except Exception as e:
            print(f"❌ Failed to generate agent API key: {e}")
            return False

    def _start_agent_background(self, workspace_path: str) -> bool:
        """Start agent server in background."""
        workspace = Path(workspace_path)
        self.logs_dir.mkdir(exist_ok=True)
        
        print("🚀 Starting agent server in background...")
        
        try:
            # Prepare environment
            env = os.environ.copy()
            
            # Load .env.agent variables
            env_agent = workspace / ".env.agent"
            with open(env_agent, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env[key] = value
            
            # Start server process
            with open(self.log_file, 'w') as log_f:
                process = subprocess.Popen(
                    ["uv", "run", "python", "api/serve.py"],
                    cwd=workspace,
                    env=env,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
                
            # Save PID
            with open(self.pid_file, 'w') as pid_f:
                pid_f.write(str(process.pid))
                
            # Wait a moment to check if it started successfully
            time.sleep(3)
            
            if self._is_agent_running():
                pid = self._get_agent_pid()
                print(f"✅ Agent server started in background (PID: {pid})")
                print(f"🌐 Agent API: http://localhost:{self.agent_port}")
                print("📋 Logs: uvx automagik-hive --agent-logs")
                
                # Show startup logs
                print("📋 --- Startup logs ---")
                try:
                    result = subprocess.run(
                        ["head", "-20", str(self.log_file)],
                        capture_output=True, text=True, check=False
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        print(result.stdout)
                    else:
                        print("No logs yet")
                except:
                    print("No logs yet")
                    
                return True
            else:
                print("❌ Failed to start agent server")
                print("📋 Check logs: uvx automagik-hive --agent-logs")
                return False
                
        except Exception as e:
            print(f"❌ Error starting agent server: {e}")
            return False

    def _stop_agent_background(self) -> bool:
        """Stop agent server running in background."""
        if not self.pid_file.exists():
            print("⚠️ No agent server PID file found")
            return False
            
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
                
            # Check if process is running
            try:
                os.kill(pid, 0)  # Signal 0 just checks if process exists
            except ProcessLookupError:
                print("⚠️ Agent server not running")
                self.pid_file.unlink(missing_ok=True)
                return False
                
            print(f"🛑 Stopping agent server (PID: {pid})...")
            
            # Try graceful shutdown first
            os.kill(pid, signal.SIGTERM)
            
            # Wait up to 5 seconds for graceful shutdown
            for _ in range(50):
                try:
                    os.kill(pid, 0)
                    time.sleep(0.1)
                except ProcessLookupError:
                    break
            else:
                # Force kill if still running
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                    
            print("✅ Agent server stopped")
            self.pid_file.unlink(missing_ok=True)
            return True
            
        except Exception as e:
            print(f"❌ Error stopping agent server: {e}")
            return False

    def _is_agent_running(self) -> bool:
        """Check if agent server is running."""
        if not self.pid_file.exists():
            return False
            
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # Signal 0 just checks if process exists
            return True
        except (ProcessLookupError, ValueError, OSError):
            self.pid_file.unlink(missing_ok=True)
            return False

    def _get_agent_pid(self) -> int | None:
        """Get agent server PID if running."""
        if not self.pid_file.exists():
            return None
            
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # Check if process exists
            return pid
        except (ProcessLookupError, ValueError, OSError):
            self.pid_file.unlink(missing_ok=True)
            return None

    def _cleanup_agent_environment(self, workspace_path: str) -> bool:
        """Clean up existing agent environment."""
        workspace = Path(workspace_path)
        
        print("🧹 Cleaning up existing agent environment...")
        
        # Stop agent server
        self._stop_agent_background()
        
        # Stop agent containers
        try:
            subprocess.run([
                "docker", "compose", "-f", self.agent_compose_file, "down"
            ], cwd=workspace, capture_output=True, check=False)
        except:
            pass
            
        # Remove containers
        try:
            subprocess.run([
                "docker", "container", "rm", "hive-agents-agent", "hive-postgres-agent"
            ], capture_output=True, check=False)
        except:
            pass
            
        # Clean up files
        try:
            (workspace / ".env.agent").unlink(missing_ok=True)
            (workspace / "data" / "postgres-agent").rmdir() if (workspace / "data" / "postgres-agent").exists() else None
        except:
            pass
            
        print("✅ Agent environment cleaned up")
        return True