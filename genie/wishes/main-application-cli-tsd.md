# Technical Specification Document: Main Application CLI Pattern

## Executive Summary

This document specifies the implementation of main application CLI commands that mirror the successful agent CLI pattern, enabling consistent Docker Compose orchestration for the main Automagik Hive application with persistent data storage.

## Success Pattern Analysis

### Agent CLI Success Factors

The current agent CLI implementation demonstrates several proven patterns:

1. **Clean Command Interface**: Simple, intuitive commands (--agent-install, --agent-start, --agent-stop, etc.)
2. **Docker Compose Integration**: Seamless orchestration using docker-compose.yml files
3. **Environment Inheritance**: Proper .env file inheritance with selective overrides
4. **Cross-Platform Compatibility**: Robust path handling and error management
5. **Service Health Monitoring**: Status checks and log access
6. **Workspace Isolation**: Complete separation from main application

### Key Implementation Patterns

```python
# Command Structure Pattern
class MainCommands:
    def install(self, workspace: str = ".") -> bool:
        # Install and start main services
    def start(self, workspace: str = ".") -> bool:
        # Start main services
    def stop(self, workspace: str = ".") -> bool:
        # Stop main services
    def restart(self, workspace: str = ".") -> bool:
        # Restart main services (stop + start)
    def status(self, workspace: str = ".") -> bool:
        # Check main status
    def logs(self, workspace: str = ".", tail: int = 50) -> bool:
        # Show main logs
    def reset(self, workspace: str = ".") -> bool:
        # Reset main environment
```

## Key Differences for Main Application

### Critical Distinctions

| Aspect | Agent Pattern | Main Application Pattern |
|--------|---------------|--------------------------|
| **Credentials** | Hardcoded test credentials | Use existing .env credentials directly |
| **API Port** | Hardcoded 38886 | Dynamic from HIVE_API_PORT env var |
| **Database Port** | Hardcoded 35532 | Use HIVE_DATABASE_URL from .env |
| **Data Persistence** | Ephemeral (no volumes) | Persistent to data/ directory |
| **Environment** | Override with test values | Use .env values directly |
| **Service Names** | agent-postgres, agent-api | main-postgres, main-app |
| **Commands** | --agent-* | --main-* |

### Environment Configuration

```yaml
# Agent Pattern (Override)
environment:
  - HIVE_API_PORT=38886
  - HIVE_DATABASE_URL=postgresql+psycopg://test_user:test_pass@agent-postgres:5432/hive_agent
  - HIVE_API_KEY=agent-test-key-12345

# Main Pattern (Inherit from .env)
env_file:
  - ../../.env
environment:
  - RUNTIME_ENV=prd
  # No overrides - use .env values directly
```

## Technical Implementation

### 1. CLI Integration

#### Command Parser Updates (cli/main.py)

```python
# Add main application commands to argument parser
def create_parser() -> argparse.ArgumentParser:
    # ... existing code ...
    
    # Main application commands
    parser.add_argument("--main-install", nargs="?", const=".", metavar="WORKSPACE", 
                       help="Install and start main application services")
    parser.add_argument("--main-start", nargs="?", const=".", metavar="WORKSPACE", 
                       help="Start main application services")
    parser.add_argument("--main-stop", nargs="?", const=".", metavar="WORKSPACE", 
                       help="Stop main application services")
    parser.add_argument("--main-restart", nargs="?", const=".", metavar="WORKSPACE", 
                       help="Restart main application services")
    parser.add_argument("--main-status", nargs="?", const=".", metavar="WORKSPACE", 
                       help="Check main application status")
    parser.add_argument("--main-logs", nargs="?", const=".", metavar="WORKSPACE", 
                       help="Show main application logs")
    parser.add_argument("--main-reset", nargs="?", const=".", metavar="WORKSPACE", 
                       help="Reset main application environment")
```

#### Command Routing (cli/main.py)

```python
def main() -> int:
    # ... existing code ...
    
    # Main application commands
    main_cmd = MainCommands()
    if args.main_install:
        return 0 if main_cmd.install(args.main_install) else 1
    elif args.main_start:
        return 0 if main_cmd.start(args.main_start) else 1
    elif args.main_stop:
        return 0 if main_cmd.stop(args.main_stop) else 1
    elif args.main_restart:
        return 0 if main_cmd.restart(args.main_restart) else 1
    elif args.main_status:
        return 0 if main_cmd.status(args.main_status) else 1
    elif args.main_logs:
        return 0 if main_cmd.logs(args.main_logs, args.tail) else 1
    elif args.main_reset:
        return 0 if main_cmd.reset(args.main_reset) else 1
```

### 2. Main Commands Implementation

#### File: cli/commands/main.py

```python
"""Main Application Commands Implementation.

Real implementation connecting to MainService for actual functionality.
"""

from typing import Optional, Dict, Any
from pathlib import Path
from cli.core.main_service import MainService


class MainCommands:
    """Main application commands implementation."""
    
    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path(".")
        self.main_service = MainService(self.workspace_path)
    
    def install(self, workspace: str = ".") -> bool:
        """Install and start main application services."""
        try:
            print(f"🚀 Installing and starting main application services in: {workspace}")
            if not self.main_service.install_main_environment(workspace):
                return False
            return self.main_service.serve_main(workspace)
        except Exception:
            return False
    
    def start(self, workspace: str = ".") -> bool:
        """Start main application services."""
        try:
            print(f"🚀 Starting main application services in: {workspace}")
            return self.main_service.serve_main(workspace)
        except Exception:
            return False
    
    def stop(self, workspace: str = ".") -> bool:
        """Stop main application services."""
        try:
            print(f"🛑 Stopping main application services in: {workspace}")
            return self.main_service.stop_main(workspace)
        except Exception:
            return False
    
    def restart(self, workspace: str = ".") -> bool:
        """Restart main application services."""
        try:
            print(f"🔄 Restarting main application services in: {workspace}")
            if not self.stop(workspace):
                print("⚠️ Stop failed, attempting restart anyway...")
            return self.start(workspace)
        except Exception:
            return False
    
    def status(self, workspace: str = ".") -> bool:
        """Check main application status."""
        try:
            print(f"🔍 Checking main application status in: {workspace}")
            status = self.main_service.get_main_status(workspace)
            
            for service, service_status in status.items():
                print(f"  {service}: {service_status}")
            
            return True
        except Exception:
            return False
    
    def logs(self, workspace: str = ".", tail: int = 50) -> bool:
        """Show main application logs."""
        try:
            print(f"📋 Showing main application logs from: {workspace} (last {tail} lines)")
            return self.main_service.show_main_logs(workspace, tail)
        except Exception:
            return False
    
    def reset(self, workspace: str = ".") -> bool:
        """Reset main application environment."""
        try:
            print(f"🗑️ Resetting main application environment in: {workspace}")
            print("This will destroy all containers and data, then reinstall and start fresh...")
            return self.main_service.reset_main_environment(workspace)
        except Exception:
            return False
```

### 3. Main Service Implementation

#### File: cli/core/main_service.py

```python
"""Main Application Service Management.

Full implementation for main application Docker Compose orchestration.
"""

import os
import subprocess
import time
from typing import Optional, Dict, Any
from pathlib import Path


class MainService:
    """Main application service management."""
    
    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path(".")
    
    def install_main_environment(self, workspace_path: str) -> bool:
        """Install main application environment."""
        if not self._validate_workspace(Path(workspace_path)):
            return False
            
        if not self._setup_main_containers(workspace_path):
            return False
            
        print("✅ Main application environment installed successfully")
        return True
    
    def _validate_workspace(self, workspace_path: Path) -> bool:
        """Validate workspace has required structure and files."""
        try:
            normalized_workspace = workspace_path.resolve()
            
            if not normalized_workspace.exists() or not normalized_workspace.is_dir():
                return False
            
            # Check for docker-compose.yml in docker/main/ or root
            docker_compose_main = normalized_workspace / "docker" / "main" / "docker-compose.yml"
            docker_compose_root = normalized_workspace / "docker-compose.yml"
            
            if not docker_compose_main.exists() and not docker_compose_root.exists():
                print("❌ No docker-compose.yml found in docker/main/ or workspace root")
                return False
            
            # Check for .env file
            env_file = normalized_workspace / ".env"
            if not env_file.exists():
                print("❌ .env file not found in workspace root")
                return False
            
            return True
        except Exception:
            return False
    
    def _setup_main_containers(self, workspace_path: str) -> bool:
        """Setup main application containers using docker compose."""
        try:
            workspace = Path(workspace_path).resolve()
            
            # Find docker-compose.yml file
            docker_compose_main = workspace / "docker" / "main" / "docker-compose.yml"
            docker_compose_root = workspace / "docker-compose.yml"
            
            if docker_compose_main.exists():
                compose_file = docker_compose_main
            elif docker_compose_root.exists():
                compose_file = docker_compose_root
            else:
                print("❌ No docker-compose.yml found")
                return False
            
            # Ensure data directory exists for persistent storage
            data_dir = workspace / "data"
            data_dir.mkdir(exist_ok=True)
            
            postgres_data_dir = data_dir / "postgres"
            postgres_data_dir.mkdir(exist_ok=True)
            
            print("💾 Using persistent PostgreSQL storage in data/postgres")
            
            # Execute docker compose command
            print("🚀 Starting main application containers...")
            result = subprocess.run(
                ["docker", "compose", "-f", os.fspath(compose_file), "up", "-d"],
                check=False,
                capture_output=True,
                text=True,
                timeout=180,  # Longer timeout for main app
            )
            
            if result.returncode != 0:
                print(f"❌ Docker compose failed: {result.stderr}")
                return False
                
            print("✅ Main application containers started successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error starting main application containers: {e}")
            return False
    
    def serve_main(self, workspace_path: str) -> bool:
        """Serve main application containers."""
        # Check if containers are already running
        status = self.get_main_status(workspace_path)
        postgres_running = "✅ Running" in status.get("main-postgres", "")
        app_running = "✅ Running" in status.get("main-app", "")
        
        if postgres_running and app_running:
            print("✅ Main application containers are already running")
            return True
            
        return self._setup_main_containers(workspace_path)
    
    def stop_main(self, workspace_path: str) -> bool:
        """Stop main application containers."""
        try:
            workspace = Path(workspace_path).resolve()
            
            docker_compose_main = workspace / "docker" / "main" / "docker-compose.yml"
            docker_compose_root = workspace / "docker-compose.yml"
            
            if docker_compose_main.exists():
                compose_file = docker_compose_main
            elif docker_compose_root.exists():
                compose_file = docker_compose_root
            else:
                print("❌ Docker compose file not found")
                return False
            
            print("🛑 Stopping main application containers...")
            
            result = subprocess.run(
                ["docker", "compose", "-f", os.fspath(compose_file), "stop"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("✅ Main application containers stopped successfully")
                return True
            else:
                print(f"❌ Failed to stop containers: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error stopping main application containers: {e}")
            return False
    
    def restart_main(self, workspace_path: str) -> bool:
        """Restart main application containers."""
        try:
            workspace = Path(workspace_path).resolve()
            
            docker_compose_main = workspace / "docker" / "main" / "docker-compose.yml"
            docker_compose_root = workspace / "docker-compose.yml"
            
            if docker_compose_main.exists():
                compose_file = docker_compose_main
            elif docker_compose_root.exists():
                compose_file = docker_compose_root
            else:
                print("❌ Docker compose file not found")
                return False
            
            print("🔄 Restarting main application containers...")
            
            result = subprocess.run(
                ["docker", "compose", "-f", os.fspath(compose_file), "restart"],
                capture_output=True,
                text=True,
                timeout=180
            )
            
            if result.returncode == 0:
                print("✅ Main application containers restarted successfully")
                return True
            else:
                print(f"❌ Failed to restart containers: {result.stderr}")
                # Fallback: stop and start
                print("🔄 Attempting fallback: stop and start...")
                self.stop_main(workspace_path)
                time.sleep(2)
                return self.serve_main(workspace_path)
                
        except Exception as e:
            print(f"❌ Error restarting main application containers: {e}")
            return False
    
    def show_main_logs(self, workspace_path: str, tail: Optional[int] = None) -> bool:
        """Show main application logs."""
        try:
            workspace = Path(workspace_path).resolve()
            
            docker_compose_main = workspace / "docker" / "main" / "docker-compose.yml"
            docker_compose_root = workspace / "docker-compose.yml"
            
            if docker_compose_main.exists():
                compose_file = docker_compose_main
            elif docker_compose_root.exists():
                compose_file = docker_compose_root
            else:
                print("❌ Docker compose file not found")
                return False
            
            print("📋 Main Application Container Logs:")
            print("=" * 80)
            
            # Show logs for both containers
            for service_name, display_name in [
                ("postgres", "PostgreSQL Database"),
                ("app", "FastAPI Application Server")
            ]:
                print(f"\n🔍 {display_name} ({service_name}):")
                print("-" * 50)
                
                cmd = ["docker", "compose", "-f", os.fspath(compose_file), "logs"]
                if tail is not None:
                    cmd.extend(["--tail", str(tail)])
                cmd.append(service_name)
                
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
            print(f"❌ Error getting main application logs: {e}")
            return False
    
    def get_main_status(self, workspace_path: str) -> Dict[str, str]:
        """Get main application status."""
        status = {}
        
        try:
            workspace = Path(workspace_path).resolve()
            
            docker_compose_main = workspace / "docker" / "main" / "docker-compose.yml"
            docker_compose_root = workspace / "docker-compose.yml"
            
            if docker_compose_main.exists():
                compose_file = docker_compose_main
            elif docker_compose_root.exists():
                compose_file = docker_compose_root
            else:
                return {"main-postgres": "🛑 Stopped", "main-app": "🛑 Stopped"}
            
            # Check both containers using Docker Compose
            for service_name, display_name, port in [
                ("postgres", "main-postgres", "5532"),
                ("app", "main-app", "8886")
            ]:
                try:
                    result = subprocess.run(
                        ["docker", "compose", "-f", os.fspath(compose_file), "ps", "-q", service_name],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
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
            status = {"main-postgres": "🛑 Stopped", "main-app": "🛑 Stopped"}
        
        return status
    
    def reset_main_environment(self, workspace_path: str) -> bool:
        """Reset main application environment."""
        print("🗑️ Destroying all main application containers and data...")
        
        if not self._cleanup_main_environment(workspace_path):
            print("⚠️ Cleanup had issues, continuing with reset...")
            
        print("🔄 Reinstalling main application environment...")
        if not self.install_main_environment(workspace_path):
            return False
            
        print("🚀 Starting main application services...")
        return self.serve_main(workspace_path)
    
    def _cleanup_main_environment(self, workspace_path: str) -> bool:
        """Cleanup main application environment."""
        try:
            workspace = Path(workspace_path).resolve()
            
            docker_compose_main = workspace / "docker" / "main" / "docker-compose.yml"
            docker_compose_root = workspace / "docker-compose.yml"
            
            compose_file = None
            if docker_compose_main.exists():
                compose_file = docker_compose_main
            elif docker_compose_root.exists():
                compose_file = docker_compose_root
            
            if compose_file:
                subprocess.run(
                    ["docker", "compose", "-f", os.fspath(compose_file), "down", "-v"],
                    check=False,
                    capture_output=True,
                    timeout=60
                )
            
            # Clean up persistent data
            data_dir = workspace / "data"
            if data_dir.exists():
                import shutil
                shutil.rmtree(data_dir)
                print("🗑️ Cleaned up persistent data directory")
            
            return True
            
        except Exception:
            return True  # Best-effort cleanup
```

### 4. Docker Compose Configuration

#### Updated docker/main/docker-compose.yml

```yaml
# =============================================================================
# Main Application Container - PostgreSQL + FastAPI with Persistent Storage
# =============================================================================

services:
  # Main PostgreSQL with persistent storage
  postgres:
    image: agnohq/pgvector:16
    container_name: hive-main-postgres
    restart: unless-stopped
    ports:
      - "${HIVE_DATABASE_PORT:-5532}:5432"
    env_file:
      - ../../.env
    environment:
      - PGDATA=/var/lib/postgresql/data/pgdata
    volumes:
      - ../../data/postgres:/var/lib/postgresql/data
    user: "${POSTGRES_UID:-1000}:${POSTGRES_GID:-1000}"
    command: >
      postgres
      -c max_connections=200
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
    networks:
      - main_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $POSTGRES_USER -d $POSTGRES_DB"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  # Main FastAPI Application
  app:
    build:
      context: ../../
      dockerfile: docker/main/Dockerfile
      target: production
    container_name: hive-main-app
    restart: unless-stopped
    ports:
      - "${HIVE_API_PORT:-8886}:${HIVE_API_PORT:-8886}"
    env_file:
      - ../../.env
    environment:
      - RUNTIME_ENV=prd
    volumes:
      - main_app_logs:/app/logs
      - main_app_data:/app/data
      - ../../data:/app/shared_data
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - main_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:${HIVE_API_PORT:-8886}/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

networks:
  main_network:
    driver: bridge
    name: hive_main_network

volumes:
  main_app_logs:
    driver: local
    name: hive_main_app_logs
  main_app_data:
    driver: local
    name: hive_main_app_data
```

### 5. Usage Examples

#### Command Line Interface

```bash
# Main application lifecycle
uv run automagik-hive --main-install     # Install and start main services
uv run automagik-hive --main-start       # Start main services
uv run automagik-hive --main-stop        # Stop main services
uv run automagik-hive --main-restart     # Restart main services
uv run automagik-hive --main-status      # Check status
uv run automagik-hive --main-logs        # View logs (last 50 lines)
uv run automagik-hive --main-logs --tail 100  # View last 100 lines
uv run automagik-hive --main-reset       # Reset environment (destructive)
```

#### Environment Configuration

```bash
# .env file controls all main application settings
HIVE_API_HOST=0.0.0.0
HIVE_API_PORT=8886
HIVE_DATABASE_URL=postgresql+psycopg://hive_user:secure-password@localhost:5532/hive
POSTGRES_USER=hive_user
POSTGRES_PASSWORD=secure-password
POSTGRES_DB=hive
POSTGRES_UID=1000
POSTGRES_GID=1000
```

## Implementation Benefits

### 1. Consistency
- Identical command patterns between agent and main application
- Unified Docker Compose orchestration approach
- Consistent error handling and status reporting

### 2. Production Readiness
- Persistent data storage in data/ directory
- Environment-driven configuration
- Health checks and proper service dependencies

### 3. Developer Experience
- Simple, memorable commands
- Clear status and logging output
- Robust error handling and recovery

### 4. Operational Excellence
- Non-destructive operations (except reset)
- Graceful service management
- Cross-platform compatibility

## Quality Assurance

### 1. Test Coverage Requirements
- Unit tests for all command classes
- Integration tests for Docker Compose operations
- Cross-platform compatibility tests
- Error handling and recovery tests

### 2. Validation Criteria
- Commands succeed on clean environment
- Commands handle existing containers gracefully
- Persistent data survives container restarts
- Environment variables properly inherited
- Service health checks function correctly

### 3. Acceptance Criteria
- [ ] All --main-* commands implemented and functional
- [ ] Persistent PostgreSQL data storage working
- [ ] Environment inheritance from .env working
- [ ] Docker Compose orchestration working
- [ ] Status reporting accurate
- [ ] Log access functional
- [ ] Cross-platform compatibility verified
- [ ] Error handling robust
- [ ] Test coverage >90%

## Migration Strategy

### 1. Phase 1: Core Implementation
- Implement MainCommands class
- Implement MainService class
- Update CLI argument parser
- Create basic Docker Compose configuration

### 2. Phase 2: Integration
- Add command routing to main CLI
- Implement status and logging
- Add health checks
- Test basic functionality

### 3. Phase 3: Production Readiness
- Add comprehensive error handling
- Implement reset functionality
- Add cross-platform support
- Complete test coverage

### 4. Phase 4: Documentation and Validation
- Update README and documentation
- Perform end-to-end testing
- Validate against acceptance criteria
- Deploy and monitor

## Conclusion

This specification leverages the proven success of the agent CLI pattern while adapting it appropriately for main application requirements. The implementation maintains consistency, ensures production readiness, and provides an excellent developer experience through simple, intuitive commands and robust orchestration capabilities.