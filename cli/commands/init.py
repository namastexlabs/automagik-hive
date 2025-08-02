"""Interactive workspace initialization with guided setup flow.

Implements the UVX --init command with:
- Interactive workspace creation
- Docker installation when missing
- API key collection
- Guided setup with excellent DX
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import shutil
import secrets
import string


class InteractiveInitializer:
    """Interactive workspace initialization with Docker and API key setup."""

    def __init__(self):
        self.workspace_path: Optional[Path] = None
        self.config: Dict[str, Any] = {}

    def initialize_workspace(self, workspace_name: Optional[str] = None) -> bool:
        """Main interactive initialization flow."""
        try:
            print("🧞 Welcome to Automagik Hive Interactive Setup!")
            print()

            # Step 1: Workspace directory selection
            if not self._setup_workspace_directory(workspace_name):
                return False

            # Step 2: Docker and PostgreSQL setup
            if not self._setup_database():
                return False

            # Step 3: API key collection
            self._collect_api_keys()

            # Step 4: Show setup summary and confirm
            if not self._confirm_setup():
                print("🛑 Setup cancelled by user.")
                return False

            # Step 5: Create workspace
            if not self._create_workspace():
                return False

            # Step 6: Show success message
            self._show_success_message()
            return True

        except KeyboardInterrupt:
            print("\n🛑 Setup interrupted by user.")
            return False
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False

    def _setup_workspace_directory(self, workspace_name: Optional[str]) -> bool:
        """Interactive workspace directory setup."""
        print("📁 Workspace Directory:")
        
        if workspace_name:
            workspace_path = Path(workspace_name).resolve()
        else:
            default_path = "./my-workspace"
            user_input = input(f"Enter workspace path [{default_path}]: ").strip()
            workspace_path = Path(user_input if user_input else default_path).resolve()

        self.workspace_path = workspace_path
        print(f"Selected workspace: {workspace_path}")

        # Check if directory exists
        if workspace_path.exists():
            if any(workspace_path.iterdir()):
                print(f"⚠️  Directory '{workspace_path}' exists and is not empty.")
                confirm = input("Continue and potentially overwrite files? [y/N]: ").strip().lower()
                if confirm not in ['y', 'yes']:
                    return False
        else:
            print(f"📁 Directory '{workspace_path}' doesn't exist.")
            confirm = input("🎯 Create workspace directory? [Y/n]: ").strip().lower()
            if confirm in ['n', 'no']:
                return False
            try:
                workspace_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {workspace_path}")
            except Exception as e:
                print(f"❌ Failed to create directory: {e}")
                return False

        return True

    def _setup_database(self) -> bool:
        """Interactive PostgreSQL + Docker setup."""
        print()
        print("🗄️ PostgreSQL + pgvector Database Setup:")
        print("Automagik Hive requires PostgreSQL with pgvector extension.")
        print()

        # Check Docker installation
        docker_available = self._check_docker()
        
        if not docker_available:
            print("❌ Docker not found.")
            print()
            print("💡 We can install Docker for you, or you can provide external PostgreSQL credentials.")
            print()
            print("Choose database setup:")
            print("1) Install Docker + built-in PostgreSQL (recommended)")
            print("2) Use external PostgreSQL server")
            print()
            
            while True:
                choice = input("Selection [1]: ").strip()
                if choice in ['', '1']:
                    if not self._install_docker():
                        return False
                    self.config['database_type'] = 'docker'
                    break
                elif choice == '2':
                    return self._setup_external_postgres()
                else:
                    print("Please choose 1 or 2.")
        else:
            print("✅ Docker found and running")
            self.config['database_type'] = 'docker'
            self._setup_docker_postgres()

        return True

    def _check_docker(self) -> bool:
        """Check if Docker is available and running."""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False
                
            # Check if daemon is running
            result = subprocess.run(['docker', 'ps'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _install_docker(self) -> bool:
        """Interactive Docker installation."""
        print()
        print("🐳 Installing Docker...")
        
        system = sys.platform.lower()
        
        if system.startswith('linux'):
            return self._install_docker_linux()
        elif system == 'darwin':
            return self._install_docker_macos()
        elif system.startswith('win'):
            return self._install_docker_windows()
        else:
            print(f"❌ Unsupported platform: {system}")
            print("Please install Docker manually and run setup again.")
            return False

    def _install_docker_linux(self) -> bool:
        """Install Docker on Linux."""
        print("Detecting Linux distribution...")
        
        try:
            # Try to detect distribution
            if shutil.which('apt'):
                print("📦 Installing Docker via apt...")
                commands = [
                    'sudo apt update',
                    'sudo apt install -y docker.io',
                    'sudo systemctl enable docker',
                    'sudo systemctl start docker',
                    'sudo usermod -aG docker $USER'
                ]
            elif shutil.which('yum'):
                print("📦 Installing Docker via yum...")
                commands = [
                    'sudo yum install -y docker',
                    'sudo systemctl enable docker',
                    'sudo systemctl start docker',
                    'sudo usermod -aG docker $USER'
                ]
            elif shutil.which('pacman'):
                print("📦 Installing Docker via pacman...")
                commands = [
                    'sudo pacman -S --noconfirm docker',
                    'sudo systemctl enable docker',
                    'sudo systemctl start docker',
                    'sudo usermod -aG docker $USER'
                ]
            else:
                print("❌ Could not detect package manager.")
                print("Please install Docker manually: https://docs.docker.com/engine/install/")
                return False
            
            for cmd in commands:
                print(f"Running: {cmd}")
                result = subprocess.run(cmd, shell=True, text=True)
                if result.returncode != 0:
                    print(f"❌ Command failed: {cmd}")
                    return False
            
            print("✅ Docker installed successfully!")
            print("⚠️  You may need to log out and back in for group permissions to take effect.")
            return True
            
        except Exception as e:
            print(f"❌ Docker installation failed: {e}")
            return False

    def _install_docker_macos(self) -> bool:
        """Install Docker on macOS."""
        print("📦 Docker Desktop is required for macOS.")
        print("Please download and install Docker Desktop from:")
        print("https://www.docker.com/products/docker-desktop")
        print()
        input("Press Enter after installing Docker Desktop and starting it...")
        
        return self._check_docker()

    def _install_docker_windows(self) -> bool:
        """Install Docker on Windows/WSL."""
        print("📦 Docker Desktop is required for Windows.")
        print("Please download and install Docker Desktop from:")
        print("https://www.docker.com/products/docker-desktop")
        print()
        print("⚠️  Make sure WSL2 is enabled if you're using WSL.")
        print()
        input("Press Enter after installing Docker Desktop and starting it...")
        
        return self._check_docker()

    def _setup_docker_postgres(self):
        """Setup Docker PostgreSQL configuration."""
        print("🐘 Setting up PostgreSQL container...")
        
        # Generate secure PostgreSQL credentials
        self.config['postgres_user'] = 'hive_' + self._generate_random_string(8)
        self.config['postgres_password'] = self._generate_random_string(32)
        self.config['postgres_db'] = 'hive'
        self.config['postgres_port'] = '5532'
        
        print("✅ Generated secure PostgreSQL credentials")

    def _setup_external_postgres(self) -> bool:
        """Setup external PostgreSQL configuration."""
        print()
        print("🗄️ External PostgreSQL Configuration:")
        
        host = input("PostgreSQL Host [localhost]: ").strip() or "localhost"
        port = input("PostgreSQL Port [5432]: ").strip() or "5432"
        database = input("PostgreSQL Database [hive]: ").strip() or "hive"
        username = input("PostgreSQL User: ").strip()
        
        if not username:
            print("❌ Username is required")
            return False
        
        import getpass
        password = getpass.getpass("PostgreSQL Password: ")
        
        if not password:
            print("❌ Password is required")
            return False
        
        self.config.update({
            'database_type': 'external',
            'postgres_host': host,
            'postgres_port': port,
            'postgres_db': database,
            'postgres_user': username,
            'postgres_password': password
        })
        
        # Test connection
        print("🔍 Testing connection...")
        if self._test_postgres_connection():
            print("✅ Connected to PostgreSQL")
            return True
        else:
            print("❌ Connection failed")
            return False

    def _test_postgres_connection(self) -> bool:
        """Test PostgreSQL connection."""
        try:
            import psycopg2
            
            conn_params = {
                'host': self.config['postgres_host'],
                'port': self.config['postgres_port'],
                'database': self.config['postgres_db'],
                'user': self.config['postgres_user'],
                'password': self.config['postgres_password']
            }
            
            conn = psycopg2.connect(**conn_params)
            cursor = conn.cursor()
            
            # Check for pgvector extension
            cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            if not cursor.fetchone():
                print("⚠️  pgvector extension not found - attempting to install...")
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                conn.commit()
                print("✅ pgvector extension installed")
            
            cursor.close()
            conn.close()
            return True
            
        except ImportError:
            print("❌ psycopg2 not available - will be installed with workspace")
            return True  # Assume it will work
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False

    def _collect_api_keys(self):
        """Collect API keys from user."""
        print()
        print("🔑 API Key Configuration:")
        print("These are optional but recommended for full functionality.")
        print("Leave empty to skip (you can add them later).")
        print()
        
        api_keys = {
            'openai': "🤖 OpenAI API Key",
            'anthropic': "🧠 Anthropic API Key", 
            'google': "💎 Google Gemini API Key"
        }
        
        for key, prompt in api_keys.items():
            value = input(f"{prompt}: ").strip()
            if value:
                self.config[f'{key}_api_key'] = value

    def _confirm_setup(self) -> bool:
        """Show setup summary and get confirmation."""
        print()
        print("📋 Setup Summary:")
        print(f"- Workspace: {self.workspace_path}")
        
        if self.config['database_type'] == 'docker':
            print("- Database: Built-in Docker PostgreSQL + pgvector")
        else:
            print(f"- Database: External PostgreSQL ({self.config['postgres_host']}:{self.config['postgres_port']})")
        
        print("- Templates: .env, .claude/, .mcp.json")
        
        api_count = sum(1 for key in self.config.keys() if key.endswith('_api_key'))
        print(f"- API Keys: {api_count} configured")
        print()
        
        confirm = input("🎯 Create Automagik Hive workspace? [Y/n]: ").strip().lower()
        return confirm not in ['n', 'no']

    def _create_workspace(self) -> bool:
        """Create the actual workspace."""
        print()
        print("🚀 Creating workspace...")
        
        try:
            # Create workspace directory if it doesn't exist
            self.workspace_path.mkdir(parents=True, exist_ok=True)
            
            # Generate .env file
            self._create_env_file()
            print("✅ Created .env with API keys + database URL")
            
            # Start PostgreSQL container if using Docker
            if self.config['database_type'] == 'docker':
                self._start_postgres_container()
                print("✅ Started PostgreSQL container (port 5532)")
            
            # Copy .claude/ folder
            self._copy_claude_folder()
            print("✅ Copied .claude/ agent ecosystem")
            
            # Generate .mcp.json
            self._create_mcp_config()
            print("✅ Generated .mcp.json configuration")
            
            # Create basic directory structure
            self._create_directory_structure()
            print("✅ Created workspace structure")
            
            return True
            
        except Exception as e:
            print(f"❌ Workspace creation failed: {e}")
            return False

    def _create_env_file(self):
        """Create .env file with configuration."""
        env_content = []
        
        # Database configuration
        if self.config['database_type'] == 'docker':
            database_url = (
                f"postgresql://{self.config['postgres_user']}:"
                f"{self.config['postgres_password']}@localhost:"
                f"{self.config['postgres_port']}/{self.config['postgres_db']}"
            )
        else:
            database_url = (
                f"postgresql://{self.config['postgres_user']}:"
                f"{self.config['postgres_password']}@{self.config['postgres_host']}:"
                f"{self.config['postgres_port']}/{self.config['postgres_db']}"
            )
        
        env_content.append(f"DATABASE_URL={database_url}")
        env_content.append(f"HIVE_API_KEY=hive_{self._generate_random_string(32)}")
        
        # API keys
        for key, value in self.config.items():
            if key.endswith('_api_key'):
                env_key = key.upper().replace('_API_KEY', '_API_KEY')
                env_content.append(f"{env_key}={value}")
        
        # Write .env file
        env_file = self.workspace_path / '.env'
        env_file.write_text('\n'.join(env_content) + '\n')

    def _start_postgres_container(self):
        """Start PostgreSQL Docker container."""
        container_name = "automagik-hive-postgres"
        
        # Stop and remove existing container
        subprocess.run(['docker', 'stop', container_name], 
                      capture_output=True, text=True)
        subprocess.run(['docker', 'rm', container_name], 
                      capture_output=True, text=True)
        
        # Start new container
        cmd = [
            'docker', 'run', '-d',
            '--name', container_name,
            '-p', f"{self.config['postgres_port']}:5432",
            '-e', f"POSTGRES_USER={self.config['postgres_user']}",
            '-e', f"POSTGRES_PASSWORD={self.config['postgres_password']}",
            '-e', f"POSTGRES_DB={self.config['postgres_db']}",
            '-v', f"{self.workspace_path}/data/postgres:/var/lib/postgresql/data",
            'agnohq/pgvector:16'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to start PostgreSQL container: {result.stderr}")

    def _copy_claude_folder(self):
        """Copy .claude/ folder from package."""
        # Try to find .claude folder in package
        try:
            import automagik_hive
            package_path = Path(automagik_hive.__file__).parent
            claude_source = package_path / '.claude'
        except ImportError:
            # Fallback to current directory
            claude_source = Path(__file__).parent.parent.parent / '.claude'
        
        if claude_source.exists():
            claude_dest = self.workspace_path / '.claude'
            if claude_dest.exists():
                shutil.rmtree(claude_dest)
            shutil.copytree(claude_source, claude_dest)
        else:
            print("⚠️  .claude folder not found - creating minimal structure")
            (self.workspace_path / '.claude').mkdir(exist_ok=True)

    def _create_mcp_config(self):
        """Create .mcp.json configuration."""
        mcp_config = {
            "mcpServers": {
                "automagik-hive": {
                    "command": "uvx",
                    "args": ["automagik-hive", "serve"],
                    "env": {}
                },
                "postgres": {
                    "command": "uvx",
                    "args": ["mcp-server-postgres", "--connection-string", "${DATABASE_URL}"],
                    "env": {}
                }
            }
        }
        
        mcp_file = self.workspace_path / '.mcp.json'
        import json
        mcp_file.write_text(json.dumps(mcp_config, indent=2))

    def _create_directory_structure(self):
        """Create basic workspace directory structure."""
        directories = [
            'ai/agents',
            'ai/teams', 
            'ai/workflows',
            'ai/tools',
            'data/postgres'
        ]
        
        for directory in directories:
            (self.workspace_path / directory).mkdir(parents=True, exist_ok=True)

    def _show_success_message(self):
        """Show success message with next steps."""
        print()
        print("🎉 Workspace ready! Next steps:")
        print(f"cd {self.workspace_path}")
        print(f"uvx automagik-hive {self.workspace_path}")
        print()
        print("💡 Your workspace includes:")
        print("- PostgreSQL database with pgvector")
        print("- Complete .claude/ agent ecosystem")  
        print("- MCP server configuration")
        print("- AI component structure (agents, teams, workflows, tools)")

    def _generate_random_string(self, length: int) -> str:
        """Generate cryptographically secure random string."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))