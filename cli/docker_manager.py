"""Docker Manager - Simple container operations."""

import subprocess
import sys
import time
import yaml
from pathlib import Path
from typing import Dict, List, Optional


class DockerManager:
    """Simple Docker operations manager."""
    
    # Container definitions
    CONTAINERS = {
        "agent": {
            "postgres": "hive-agent-postgres",
            "api": "hive-agent-api"
        },
        "workspace": {
            "postgres": "hive-workspace-postgres", 
            "api": "hive-workspace-api"
        }
    }
    
    # Port mappings
    PORTS = {
        "agent": {"postgres": 35532, "api": 38886},
        "workspace": {"postgres": 35533, "api": 38887}
    }
    
    def __init__(self):
        self.project_root = Path.cwd()
        
        # Map component to docker template file
        self.template_files = {
            "workspace": self.project_root / "docker/templates/workspace.yml",
            "agent": self.project_root / "docker/templates/agent.yml"
        }
    
    def _run_command(self, cmd: List[str], capture_output: bool = False) -> Optional[str]:
        """Run shell command."""
        try:
            if capture_output:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return result.stdout.strip()
            else:
                subprocess.run(cmd, check=True)
                return None
        except subprocess.CalledProcessError as e:
            if capture_output:
                print(f"❌ Command failed: {' '.join(cmd)}")
                print(f"Error: {e.stderr}")
            return None
        except FileNotFoundError:
            print(f"❌ Command not found: {cmd[0]}")
            return None
    
    def _check_docker(self) -> bool:
        """Check if Docker is available."""
        if not self._run_command(["docker", "--version"], capture_output=True):
            print("❌ Docker not found. Please install Docker first.")
            return False
        
        # Check if Docker daemon is running
        if not self._run_command(["docker", "ps"], capture_output=True):
            print("❌ Docker daemon not running. Please start Docker.")
            return False
        
        return True
    
    def _get_containers(self, component: str) -> List[str]:
        """Get container names for component."""
        if component == "all":
            containers = []
            for comp in self.CONTAINERS:
                containers.extend(self.CONTAINERS[comp].values())
            return containers
        elif component in self.CONTAINERS:
            return list(self.CONTAINERS[component].values())
        else:
            print(f"❌ Unknown component: {component}")
            return []
    
    def _container_exists(self, container: str) -> bool:
        """Check if container exists."""
        return self._run_command(["docker", "ps", "-a", "--filter", f"name={container}", "--format", "{{.Names}}"], capture_output=True) == container
    
    def _container_running(self, container: str) -> bool:
        """Check if container is running."""
        return self._run_command(["docker", "ps", "--filter", f"name={container}", "--format", "{{.Names}}"], capture_output=True) == container
    
    def _create_network(self) -> None:
        """Create Docker network if it doesn't exist."""
        networks = self._run_command(["docker", "network", "ls", "--filter", "name=hive-network", "--format", "{{.Name}}"], capture_output=True)
        if "hive-network" not in (networks or ""):
            print("🔗 Creating Docker network...")
            self._run_command(["docker", "network", "create", "hive-network"])
    
    def _get_postgres_image(self, component: str) -> str:
        """Get PostgreSQL image from docker compose template."""
        template_file = self.template_files.get(component)
        if not template_file or not template_file.exists():
            # Fallback to defaults
            fallback_images = {
                "workspace": "agnohq/pgvector:16",
                "agent": "pgvector/pgvector:pg16"
            }
            return fallback_images.get(component, "agnohq/pgvector:16")
        
        try:
            with open(template_file, 'r') as f:
                compose_data = yaml.safe_load(f)
            
            # Look for postgres service image
            services = compose_data.get('services', {})
            for service_name, service_config in services.items():
                if 'postgres' in service_name.lower() or service_name == 'postgres':
                    return service_config.get('image', 'agnohq/pgvector:16')
            
            # Fallback if no postgres service found
            return "agnohq/pgvector:16"
            
        except Exception:
            # Fallback on any error
            return "agnohq/pgvector:16"
    
    def _create_postgres_container(self, component: str) -> bool:
        """Create PostgreSQL container."""
        container_name = self.CONTAINERS[component]["postgres"]
        port = self.PORTS[component]["postgres"]
        
        if self._container_exists(container_name):
            print(f"✅ PostgreSQL container {container_name} already exists")
            return True
        
        postgres_image = self._get_postgres_image(component)
        print(f"🐘 Creating PostgreSQL container {container_name} with {postgres_image}...")
        
        cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "--network", "hive-network",
            "-p", f"{port}:5432",
            "-e", f"POSTGRES_DB=hive_{component}",
            "-e", "POSTGRES_USER=hive_user",
            "-e", "POSTGRES_PASSWORD=hive_password",
            "-v", f"hive_{component}_data:/var/lib/postgresql/data",
            postgres_image
        ]
        
        return self._run_command(cmd) is None
    
    def _create_api_container(self, component: str) -> bool:
        """Create API container."""
        container_name = self.CONTAINERS[component]["api"]
        port = self.PORTS[component]["api"]
        
        if self._container_exists(container_name):
            print(f"✅ API container {container_name} already exists")
            return True
        
        print(f"🚀 Creating API container {container_name}...")
        
        # Create .env file for component
        env_file = self.project_root / f".env.{component}"
        if not env_file.exists():
            env_content = f"""# Automagik Hive {component.title()} Environment
DATABASE_URL=postgresql://hive_user:hive_password@hive-{component}-postgres:5432/hive_{component}
HIVE_API_KEY=hive_{component}_api_key_123
PORT={port}
ENVIRONMENT={component}
"""
            env_file.write_text(env_content)
            print(f"📝 Created {env_file}")
        
        # Build image if it doesn't exist
        images = self._run_command(["docker", "images", "--filter", f"reference=hive-{component}", "--format", "{{.Repository}}"], capture_output=True)
        if f"hive-{component}" not in (images or ""):
            print(f"🏗️ Building {component} image...")
            if not self._run_command(["docker", "build", "-t", f"hive-{component}", "."]):
                print(f"❌ Failed to build {component} image")
                return False
        
        cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "--network", "hive-network",
            "-p", f"{port}:8000",
            "--env-file", str(env_file),
            "-v", f"{self.project_root}:/app",
            "-w", "/app",
            f"hive-{component}",
            "python", "-m", "api.serve"
        ]
        
        return self._run_command(cmd) is None
    
    def install(self, component: str) -> bool:
        """Install component containers."""
        if not self._check_docker():
            return False
        
        # Interactive installation
        if component == "interactive":
            return self._interactive_install()
        
        print(f"🚀 Installing {component}...")
        
        self._create_network()
        
        components = ["agent", "workspace"] if component == "all" else [component]
        
        for comp in components:
            if comp not in self.CONTAINERS:
                print(f"❌ Unknown component: {comp}")
                return False
            
            print(f"\n📦 Setting up {comp} component...")
            
            # Create PostgreSQL container
            if not self._create_postgres_container(comp):
                print(f"❌ Failed to create PostgreSQL for {comp}")
                return False
            
            # Wait for PostgreSQL to start
            postgres_container = self.CONTAINERS[comp]["postgres"]
            if not self._container_running(postgres_container):
                print(f"🔄 Starting PostgreSQL...")
                self._run_command(["docker", "start", postgres_container])
            
            # Wait for PostgreSQL to be ready
            print("⏳ Waiting for PostgreSQL to be ready...")
            time.sleep(5)
            
            # Create API container
            if not self._create_api_container(comp):
                print(f"❌ Failed to create API for {comp}")
                return False
        
        print(f"\n✅ {component} installation complete!")
        return True
    
    def start(self, component: str) -> bool:
        """Start component containers."""
        containers = self._get_containers(component)
        if not containers:
            return False
        
        print(f"🚀 Starting {component} services...")
        
        success = True
        for container in containers:
            if self._container_exists(container):
                if not self._container_running(container):
                    print(f"▶️ Starting {container}...")
                    if not self._run_command(["docker", "start", container]):
                        success = False
                else:
                    print(f"✅ {container} already running")
            else:
                print(f"❌ Container {container} not found. Run --install first.")
                success = False
        
        return success
    
    def stop(self, component: str) -> bool:
        """Stop component containers."""
        containers = self._get_containers(component)
        if not containers:
            return False
        
        print(f"🛑 Stopping {component} services...")
        
        success = True
        for container in containers:
            if self._container_running(container):
                print(f"⏹️ Stopping {container}...")
                if not self._run_command(["docker", "stop", container]):
                    success = False
            else:
                print(f"✅ {container} already stopped")
        
        return success
    
    def restart(self, component: str) -> bool:
        """Restart component containers."""
        containers = self._get_containers(component)
        if not containers:
            return False
        
        print(f"🔄 Restarting {component} services...")
        
        success = True
        for container in containers:
            if self._container_exists(container):
                print(f"🔄 Restarting {container}...")
                if not self._run_command(["docker", "restart", container]):
                    success = False
            else:
                print(f"❌ Container {container} not found. Run --install first.")
                success = False
        
        return success
    
    def status(self, component: str) -> None:
        """Show component status."""
        containers = self._get_containers(component)
        if not containers:
            return
        
        print(f"\n📊 {component.title()} Status:")
        print("=" * 50)
        
        for container in containers:
            if self._container_exists(container):
                if self._container_running(container):
                    # Get port info
                    port_info = self._run_command(["docker", "port", container], capture_output=True)
                    status = f"🟢 Running"
                    if port_info:
                        status += f" - {port_info.split(' -> ')[0]}"
                else:
                    status = "🔴 Stopped"
            else:
                status = "❌ Not installed"
            
            print(f"{container:25} {status}")
    
    def health(self, component: str) -> None:
        """Check component health."""
        containers = self._get_containers(component)
        if not containers:
            return
        
        print(f"\n🏥 {component.title()} Health Check:")
        print("=" * 50)
        
        for container in containers:
            if self._container_running(container):
                # Basic health check - container running
                print(f"{container:25} 🟢 Healthy")
            elif self._container_exists(container):
                print(f"{container:25} 🟡 Stopped")
            else:
                print(f"{container:25} 🔴 Not installed")
    
    def logs(self, component: str, lines: int = 50) -> None:
        """Show component logs."""
        containers = self._get_containers(component)
        if not containers:
            return
        
        for container in containers:
            if self._container_exists(container):
                print(f"\n📋 Logs for {container} (last {lines} lines):")
                print("-" * 60)
                self._run_command(["docker", "logs", "--tail", str(lines), container])
            else:
                print(f"❌ Container {container} not found")
    
    def uninstall(self, component: str) -> bool:
        """Uninstall component containers."""
        containers = self._get_containers(component)
        if not containers:
            return False
        
        print(f"🗑️ Uninstalling {component}...")
        
        # Confirm with user
        response = input(f"⚠️ This will remove all {component} containers and data. Continue? (y/N): ")
        if response.lower() != 'y':
            print("❌ Uninstall cancelled")
            return False
        
        success = True
        for container in containers:
            if self._container_exists(container):
                # Stop if running
                if self._container_running(container):
                    print(f"⏹️ Stopping {container}...")
                    self._run_command(["docker", "stop", container])
                
                # Remove container
                print(f"🗑️ Removing {container}...")
                if not self._run_command(["docker", "rm", container]):
                    success = False
            
            # Remove volumes
            if component != "all":
                volume_name = f"hive_{component}_data"
                volumes = self._run_command(["docker", "volume", "ls", "--filter", f"name={volume_name}", "--format", "{{.Name}}"], capture_output=True)
                if volume_name in (volumes or ""):
                    print(f"🗑️ Removing volume {volume_name}...")
                    self._run_command(["docker", "volume", "rm", volume_name])
        
        if success:
            print(f"✅ {component} uninstalled successfully!")
        
        return success

    def _interactive_install(self) -> bool:
        """Interactive installation with user choices."""
        print("🚀 Automagik Hive Interactive Installation")
        print("=" * 50)
        
        # 1. Main Hive installation
        print("\n🏠 Automagik Hive Core (Main Application)")
        print("This includes the workspace server and web interface")
        while True:
            hive_choice = input("Would you like to install Hive Core? (Y/n): ").strip().lower()
            if hive_choice in ["y", "yes", "n", "no", ""]:
                break
            print("❌ Please enter y/yes or n/no.")
        
        install_hive = hive_choice not in ["n", "no"]
        
        if not install_hive:
            print("👋 Skipping Hive installation")
            return True
        
        # Database setup for Hive
        print("\n📦 Database Setup for Hive:")
        print("1. Use our PostgreSQL + pgvector container (recommended)")
        print("   → PostgreSQL 15 with pgvector extension for AI/RAG capabilities")
        print("2. Use existing PostgreSQL database")
        print("   → Connect to your own PostgreSQL instance")
        
        while True:
            db_choice = input("\nSelect database option (1-2): ").strip()
            if db_choice in ["1", "2"]:
                break
            print("❌ Invalid choice. Please enter 1 or 2.")
        
        if db_choice == "1":
            print("✅ Using PostgreSQL + pgvector container for Hive")
            use_container = True
        else:
            print("📝 Custom database setup for Hive")
            use_container = False
            
            # Ask for credentials
            print("\nEnter your PostgreSQL connection details:")
            host = input("Host (localhost): ").strip() or "localhost"
            port = input("Port (5432): ").strip() or "5432"
            database = input("Database name (automagik_hive): ").strip() or "automagik_hive"
            username = input("Username: ").strip()
            password = input("Password: ").strip()
            
            if not username or not password:
                print("❌ Username and password are required")
                return False
        
        # Get input for additional components only if Hive is being installed
        install_genie = False
        install_agent = False
        
        if install_hive:
            # 2. Genie installation
            print("\n🧞 Genie (AI Agent Assistant)")
            while True:
                genie_choice = input("Would you like to install Genie? (y/N): ").strip().lower()
                if genie_choice in ["y", "yes", "n", "no", ""]:
                    break
                print("❌ Please enter y/yes or n/no.")
            
            install_genie = genie_choice in ["y", "yes"]
            
            # 3. Agent Workspace installation
            print("\n🤖 Agent Workspace (Optional)")
            print("Separate isolated testing environment for agents (different from main Hive)")
            while True:
                agent_choice = input("Would you like to install Agent Workspace? (y/N): ").strip().lower()
                if agent_choice in ["y", "yes", "n", "no", ""]:
                    break
                print("❌ Please enter y/yes or n/no.")
            
            install_agent = agent_choice in ["y", "yes"]
        
        # Determine what to install
        components_to_install = []
        if install_hive:
            components_to_install.append("workspace")
        if install_agent:
            components_to_install.append("agent")
        
        if not components_to_install:
            print("👋 No components selected for installation")
            return True
        
        # Install selected components
        success = True
        for component in components_to_install:
            print(f"\n🚀 Installing {component}...")
            if use_container:
                if not self.install(component):
                    success = False
                    break
            else:
                # Custom database installation (simplified for now)
                print("🔧 Custom database installation not fully implemented yet")
                print(f"💡 For now, please use: uv run python -m cli.main --install {component}")
        
        if install_genie:
            print("\n🧞 Genie installation not yet implemented")
            print("💡 Coming soon in future updates!")
        
        return success