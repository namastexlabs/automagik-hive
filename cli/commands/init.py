"""Workspace Initialization CLI Commands for Automagik Hive.

This module provides the --init command implementation for interactive
workspace creation with API key collection and Docker Compose setup.
"""

import base64
import json
import os
import re
import secrets
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

from cli.core.docker_service import DockerService
from cli.core.postgres_service import PostgreSQLService
from cli.core.template_processor import TemplateProcessor, MCPConfigGenerator


class InitCommands:
    """Workspace initialization CLI command implementations.
    
    Provides interactive workspace creation with secure credential
    generation, API key collection, and Docker Compose setup.
    """

    def __init__(self):
        self.docker_service = DockerService()
        self.postgres_service = PostgreSQLService()
        self.template_processor = TemplateProcessor()
        self.mcp_generator = MCPConfigGenerator(self.template_processor)
        self.mcp_config_manager = MCPConfigManager()
        self.template_manager = ContainerTemplateManager()

    def init_workspace(self, workspace_name: str | None = None) -> bool:
        """Initialize a new workspace with interactive setup.
        
        Args:
            workspace_name: Optional workspace name/path
            
        Returns:
            True if initialization successful, False otherwise
        """
        print("🧞 Welcome to Automagik Hive Workspace Initialization!")
        print("✨ Let's create your magical development environment...\n")

        # Step 1: Determine workspace path
        workspace_path = self._get_workspace_path(workspace_name)
        if not workspace_path:
            return False

        print(f"📁 Creating workspace: {workspace_path}")

        # Step 2: Create workspace directory
        try:
            workspace_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"❌ Failed to create workspace directory: {e}")
            return False

        # Step 3: Interactive PostgreSQL setup choice
        postgres_config = self._setup_postgres_interactively()
        if not postgres_config:
            return False

        # Step 4: Container services selection
        container_services = self._select_container_services()
        print(f"📦 Selected container services: {', '.join(container_services)}")

        # Step 5: Generate secure credentials
        credentials = self._generate_credentials(postgres_config)
        print("🔐 Generated secure credentials")

        # Step 6: Collect API keys interactively
        api_keys = self._collect_api_keys()

        # Step 7: Create workspace files and containers
        if not self._create_workspace_files(workspace_path, credentials, api_keys, postgres_config, container_services):
            return False

        # Step 8: Create data directories
        self._create_data_directories(workspace_path, container_services)

        # Step 9: Success message
        self._show_success_message(workspace_path, container_services)

        return True

    def _get_workspace_path(self, workspace_name: str | None) -> Path | None:
        """Get and validate workspace path."""
        if workspace_name:
            workspace_path = Path(workspace_name).resolve()
        else:
            # Interactive workspace name input
            while True:
                name = input("📝 Enter workspace name/path (e.g., ./my-hive-workspace): ").strip()
                if not name:
                    print("❌ Workspace name cannot be empty")
                    continue
                workspace_path = Path(name).resolve()
                break

        # Check if workspace already exists
        if workspace_path.exists() and any(workspace_path.iterdir()):
            print(f"⚠️ Directory '{workspace_path}' already exists and is not empty")
            response = input("Continue anyway? (y/N): ").strip().lower()
            if response != "y":
                print("❌ Initialization cancelled")
                return None

            # Check for permission issues with existing files
            self._check_and_fix_permissions(workspace_path)

        return workspace_path

    def _select_container_services(self) -> list[str]:
        """Interactive container services selection."""
        print("\n📦 Container Services Selection")
        print("Choose your container services configuration:")
        print("1. 🗄️ PostgreSQL Only - Basic database service (Recommended)")
        print("2. 🚀 Full Stack - PostgreSQL + Agent Development + Genie Consultation")
        print("3. 🎯 Custom - Select specific services")

        while True:
            try:
                choice = input("\nEnter your choice (1-3): ").strip()

                if choice == "1":
                    print("✅ Selected: PostgreSQL database service")
                    return ["postgres"]
                if choice == "2":
                    print("✅ Selected: Full stack - PostgreSQL + Agent + Genie services")
                    return ["postgres", "agent", "genie"]
                if choice == "3":
                    return self._custom_service_selection()
                print("❌ Invalid choice. Please enter 1, 2, or 3.")

            except (EOFError, KeyboardInterrupt):
                print("\n❌ Service selection cancelled")
                return ["postgres"]  # Default to basic PostgreSQL

    def _custom_service_selection(self) -> list[str]:
        """Custom service selection with individual choices."""
        print("\n🎯 Custom Service Selection")
        print("Select which services to include (y/N):")
        
        services = []
        
        # PostgreSQL is always included
        services.append("postgres")
        print("✅ PostgreSQL Database - Always included")
        
        # Agent development environment
        try:
            agent_choice = input("🤖 Agent Development Environment? (y/N): ").strip().lower()
            if agent_choice == "y":
                services.append("agent")
                print("✅ Added Agent Development Environment")
        except (EOFError, KeyboardInterrupt):
            pass
        
        # Genie consultation service
        try:
            genie_choice = input("🧞 Genie Consultation Service? (y/N): ").strip().lower()
            if genie_choice == "y":
                services.append("genie")
                print("✅ Added Genie Consultation Service")
        except (EOFError, KeyboardInterrupt):
            pass
        
        print(f"\n📋 Selected services: {', '.join(services)}")
        return services

    def _check_and_fix_permissions(self, workspace_path: Path):
        """Check and fix permission issues with existing workspace files."""
        try:
            # Check if data directory exists and has permission issues
            data_path = workspace_path / "data"
            if data_path.exists():
                # Try to write a test file to check permissions
                test_file = data_path / ".permission_test"
                try:
                    test_file.touch()
                    test_file.unlink()  # Remove test file
                except PermissionError:
                    print("🔧 Detected permission issues with existing data/ directory")
                    print("💡 This is likely due to Docker containers creating files as root")
                    print("⚠️ You may need to run: sudo chown -R $USER:$USER data/")

                    # Ask user if they want to attempt fixing permissions
                    fix_response = input("Attempt to fix permissions automatically? (y/N): ").strip().lower()
                    if fix_response == "y":
                        try:
                            import os
                            import subprocess
                            subprocess.run(
                                ["sudo", "chown", "-R", f"{os.getuid()}:{os.getgid()}", str(data_path)],
                                check=True,
                                capture_output=True
                            )
                            print("✅ Permissions fixed successfully")
                        except subprocess.CalledProcessError:
                            print("❌ Failed to fix permissions automatically")
                            print("💡 Please run manually: sudo chown -R $USER:$USER data/")
                        except Exception as e:
                            print(f"❌ Error fixing permissions: {e}")

        except Exception as e:
            print(f"⚠️ Could not check permissions: {e}")

    def _setup_postgres_interactively(self) -> dict[str, str] | None:
        """Interactive PostgreSQL setup with user choice."""
        print("\n🗄️ PostgreSQL Database Setup")
        print("Choose your PostgreSQL setup option:")
        print("1. 🐳 Docker PostgreSQL (Recommended) - Automatic setup with pgvector")
        print("2. 🔌 External PostgreSQL - Use existing PostgreSQL server")
        print("3. ❌ Skip - Configure later manually")

        while True:
            try:
                choice = input("\nEnter your choice (1-3): ").strip()

                if choice == "1":
                    return self._setup_docker_postgres()
                if choice == "2":
                    return self._setup_external_postgres()
                if choice == "3":
                    print("⚠️ PostgreSQL configuration skipped")
                    print("💡 You'll need to configure HIVE_DATABASE_URL in .env manually")
                    return {"type": "manual", "database_url": "postgresql+psycopg://user:pass@localhost:5432/hive"}
                print("❌ Invalid choice. Please enter 1, 2, or 3.")

            except (EOFError, KeyboardInterrupt):
                print("\n❌ Setup cancelled")
                return None

    def _setup_docker_postgres(self) -> dict[str, str] | None:
        """Set up Docker PostgreSQL with automatic configuration."""
        print("\n🐳 Setting up Docker PostgreSQL...")

        # Check Docker availability
        if not self._check_docker_setup():
            print("❌ Docker setup failed. Please install Docker or choose external PostgreSQL.")
            return None

        print("✅ Docker PostgreSQL will be configured automatically")
        print("   • Image: agnohq/pgvector:16 (PostgreSQL with vector extensions)")
        print("   • Port: 5532 (external) → 5432 (container)")
        print("   • Database: hive")
        print("   • Extensions: pgvector for AI embeddings")

        return {
            "type": "docker",
            "image": "agnohq/pgvector:16",
            "port": "5532",
            "database": "hive"
        }

    def _setup_external_postgres(self) -> dict[str, str] | None:
        """Set up external PostgreSQL with user-provided connection details."""
        print("\n🔌 External PostgreSQL Setup")
        print("Please provide your PostgreSQL connection details:")

        try:
            # Collect connection details
            host = input("PostgreSQL Host (default: localhost): ").strip() or "localhost"
            port = input("PostgreSQL Port (default: 5432): ").strip() or "5432"

            # Validate port
            try:
                port_int = int(port)
                if not (1 <= port_int <= 65535):
                    raise ValueError("Port must be between 1-65535")
            except ValueError as e:
                print(f"❌ Invalid port: {e}")
                return None

            database = input("Database Name (default: hive): ").strip() or "hive"
            username = input("Username: ").strip()

            if not username:
                print("❌ Username is required")
                return None

            import getpass
            password = getpass.getpass("Password: ")

            # Build connection URL
            database_url = f"postgresql+psycopg://{username}:{password}@{host}:{port}/{database}"

            # Test connection
            print("🔍 Testing PostgreSQL connection...")
            if self._test_postgres_connection(database_url):
                print("✅ PostgreSQL connection successful!")
                return {
                    "type": "external",
                    "database_url": database_url,
                    "host": host,
                    "port": port,
                    "database": database,
                    "username": username
                }
            print("❌ PostgreSQL connection failed!")
            print("💡 Please check your connection details and try again")
            return None

        except (EOFError, KeyboardInterrupt):
            print("\n❌ Setup cancelled")
            return None

    def _test_postgres_connection(self, database_url: str) -> bool:
        """Test PostgreSQL connection."""
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(database_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def _check_docker_setup(self) -> bool:
        """Check Docker availability and setup."""
        print("🐳 Checking Docker setup...")

        if not self.docker_service.is_docker_available():
            print("❌ Docker is not available")
            print("📋 Please install Docker:")
            self._show_docker_install_instructions()
            return False

        if not self.docker_service.is_docker_running():
            print("❌ Docker daemon is not running")
            print("💡 Please start Docker and try again")
            return False

        print("✅ Docker is available and running")
        return True

    def _show_docker_install_instructions(self):
        """Show Docker installation instructions."""
        print("\n🔧 Docker Installation Instructions:")
        print("- macOS: Download Docker Desktop from https://docker.com")
        print("- Windows: Download Docker Desktop from https://docker.com")
        print("- Linux: Run: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh")
        print("- WSL2: Install Docker Desktop for Windows with WSL2 backend")

    def _generate_credentials(self, postgres_config: dict[str, str]) -> dict[str, str]:
        """Generate secure credentials for the workspace."""
        # Generate Hive API key (hive_ + 32 char secure token)
        api_key_token = self._generate_secure_string(32)
        hive_api_key = f"hive_{api_key_token}"

        if postgres_config["type"] == "docker":
            # Generate PostgreSQL credentials for Docker setup
            postgres_user = self._generate_secure_string(16)
            postgres_password = self._generate_secure_string(16)
            database_url = f"postgresql+psycopg://{postgres_user}:{postgres_password}@localhost:{postgres_config['port']}/{postgres_config['database']}"

            return {
                "postgres_user": postgres_user,
                "postgres_password": postgres_password,
                "database_url": database_url,
                "hive_api_key": hive_api_key
            }
        if postgres_config["type"] == "external":
            # Use provided external PostgreSQL connection
            return {
                "database_url": postgres_config["database_url"],
                "hive_api_key": hive_api_key
            }
        # manual setup
        # Placeholder credentials for manual configuration
        return {
            "database_url": postgres_config["database_url"],
            "hive_api_key": hive_api_key
        }

    def _convert_to_container_credentials(self, credentials: dict[str, str], postgres_config: dict[str, str]) -> ContainerCredentials:
        """Convert credentials dict to ContainerCredentials object."""
        return ContainerCredentials(
            postgres_user=credentials.get("postgres_user", "workspace"),
            postgres_password=credentials.get("postgres_password", "secure_password"),
            postgres_db=postgres_config.get("database", "hive"),
            hive_api_key=credentials["hive_api_key"],
            postgres_uid=str(os.getuid() if hasattr(os, 'getuid') else 1000),
            postgres_gid=str(os.getgid() if hasattr(os, 'getgid') else 1000)
        )

    def _generate_secure_string(self, length: int) -> str:
        """Generate cryptographically secure random string."""
        # Use URL-safe base64 encoding for secure random strings
        random_bytes = secrets.token_bytes(length * 3 // 4)  # Adjust for base64 encoding
        return base64.urlsafe_b64encode(random_bytes).decode("ascii")[:length]

    def _collect_api_keys(self) -> dict[str, str]:
        """Collect API keys from user interactively."""
        print("\n🔑 API Key Collection (Optional - press Enter to skip):")

        api_keys = {}

        try:
            # OpenAI API Key
            openai_key = input("OpenAI API Key (for GPT models): ").strip()
            if openai_key:
                api_keys["openai_api_key"] = openai_key

            # Anthropic API Key
            anthropic_key = input("Anthropic API Key (for Claude models): ").strip()
            if anthropic_key:
                api_keys["anthropic_api_key"] = anthropic_key

            # Google API Key
            google_key = input("Google API Key (for Gemini models): ").strip()
            if google_key:
                api_keys["google_api_key"] = google_key

            # XAI API Key
            xai_key = input("X.AI API Key (for Grok models): ").strip()
            if xai_key:
                api_keys["xai_api_key"] = xai_key

        except (EOFError, KeyboardInterrupt):
            print("\n⚠️ Non-interactive mode detected - skipping API key collection")
            print("💡 You can add API keys to .env file later")
            return {}

        if api_keys:
            print(f"✅ Collected {len(api_keys)} API key(s)")
        else:
            print("⚠️ No API keys provided - you can add them to .env later")

        return api_keys

    def _create_workspace_files(self, workspace_path: Path, credentials: dict[str, str], api_keys: dict[str, str], postgres_config: dict[str, str], container_services: list[str]) -> bool:
        """Create workspace configuration files."""
        try:
            # Create .env file
            self._create_env_file(workspace_path, credentials, api_keys)

            # Create container templates (for Docker PostgreSQL)
            if postgres_config["type"] == "docker":
                self._create_container_templates(workspace_path, credentials, postgres_config, container_services)

            # Copy .claude/ directory if available
            self._copy_claude_directory(workspace_path)

            # Create .mcp.json for Claude Code integration with multi-server support
            self._create_advanced_mcp_config(workspace_path, credentials, postgres_config)

            # Create ai/ directory structure
            self._create_ai_structure(workspace_path)

            # Create .gitignore
            self._create_gitignore(workspace_path)

            # Create startup script for convenience
            self._create_startup_script(workspace_path, postgres_config)

            return True

        except Exception as e:
            print(f"❌ Failed to create workspace files: {e}")
            return False

    def _create_env_file(self, workspace_path: Path, credentials: dict[str, str], api_keys: dict[str, str]):
        """Create .env file with credentials and API keys."""
        env_content = f"""# Automagik Hive Workspace Configuration
# Generated by uvx automagik-hive --init

# === Database Configuration ===
DATABASE_URL={credentials['database_url']}
HIVE_DATABASE_URL={credentials['database_url']}
"""

        # Add PostgreSQL-specific environment variables only for Docker setup
        if "postgres_user" in credentials:
            env_content += f"""POSTGRES_USER={credentials['postgres_user']}
POSTGRES_PASSWORD={credentials['postgres_password']}
POSTGRES_DB=hive
"""

        env_content += f"""
# === API Configuration ===
HIVE_API_KEY={credentials['hive_api_key']}
HIVE_HOST=0.0.0.0
HIVE_PORT=8886

# === AI Provider API Keys ===
"""

        # Add collected API keys
        for key, value in api_keys.items():
            env_content += f"{key.upper()}={value}\n"

        # Add placeholder for missing keys
        if "openai_api_key" not in api_keys:
            env_content += "# OPENAI_API_KEY=your-openai-key-here\n"
        if "anthropic_api_key" not in api_keys:
            env_content += "# ANTHROPIC_API_KEY=your-anthropic-key-here\n"
        if "google_api_key" not in api_keys:
            env_content += "# GOOGLE_API_KEY=your-google-key-here\n"
        if "xai_api_key" not in api_keys:
            env_content += "# XAI_API_KEY=your-xai-key-here\n"

        env_content += """
# === MCP Server Configuration ===
MCP_SERVER_PORT=8887

# === Development Settings ===
ENVIRONMENT=development
LOG_LEVEL=INFO
HIVE_DEV_MODE=true
"""

        env_file = workspace_path / ".env"
        env_file.write_text(env_content)

        # Set secure permissions
        env_file.chmod(0o600)

    def _create_container_templates(self, workspace_path: Path, credentials: dict[str, str], postgres_config: dict[str, str], container_services: list[str]):
        """Create container templates using the template system."""
        print("🏗️ Generating container templates...")
        
        # Convert to ContainerCredentials
        container_credentials = self._convert_to_container_credentials(credentials, postgres_config)
        
        # Create required directories first
        self.template_manager.create_required_directories(workspace_path)
        
        generated_files = {}
        
        # Generate templates based on selected services
        if "postgres" in container_services or len(container_services) == 1:
            # Main workspace compose file
            print("📦 Generating main workspace docker-compose.yml...")
            generated_files["workspace"] = self.template_manager.generate_workspace_compose(
                workspace_path, container_credentials
            )
        
        if "agent" in container_services:
            # Agent development environment
            print("🤖 Generating agent development environment...")
            generated_files["agent"] = self.template_manager.copy_agent_template(
                workspace_path, container_credentials
            )
        
        if "genie" in container_services:
            # Genie consultation service
            print("🧞 Generating genie consultation service...")
            generated_files["genie"] = self.template_manager.generate_genie_compose(
                workspace_path, container_credentials
            )
        
        print(f"✅ Generated {len(generated_files)} container template(s)")
        
        # Show generated files
        for service_type, file_path in generated_files.items():
            print(f"   • {service_type}: {file_path.name}")

    def _create_docker_compose_file(self, workspace_path: Path, credentials: dict[str, str]):
        """Create docker-compose.yml file with proper user/group settings."""
        import os

        # Get current user ID and group ID to avoid root ownership issues
        uid = os.getuid()
        gid = os.getgid()

        compose_content = f"""# Automagik Hive Docker Compose Configuration
# Generated by uvx automagik-hive --init

version: '3.8'

services:
  postgres:
    image: agnohq/pgvector:16
    container_name: hive-postgres
    user: "{uid}:{gid}"
    environment:
      POSTGRES_USER: {credentials['postgres_user']}
      POSTGRES_PASSWORD: {credentials['postgres_password']}
      POSTGRES_DB: hive
      PGUSER: {credentials['postgres_user']}
    ports:
      - "5532:5432"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U {credentials['postgres_user']} -d hive"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped
    networks:
      - hive-network

networks:
  hive-network:
    driver: bridge

volumes:
  postgres-data:
    driver: local
"""

        compose_file = workspace_path / "docker-compose.yml"
        compose_file.write_text(compose_content)

    def _copy_claude_directory(self, workspace_path: Path):
        """Copy .claude/ directory from package if available."""
        # Try to find .claude/ directory in the package
        possible_paths = [
            Path(__file__).parent.parent.parent / ".claude",  # From package
            Path.cwd() / ".claude"  # From current directory
        ]

        source_claude = None
        for path in possible_paths:
            if path.exists() and path.is_dir():
                source_claude = path
                break

        if source_claude:
            dest_claude = workspace_path / ".claude"
            try:
                shutil.copytree(source_claude, dest_claude, dirs_exist_ok=True)
                print("✅ Copied .claude/ directory for Claude Code integration")
            except Exception as e:
                print(f"⚠️ Could not copy .claude/ directory: {e}")
        else:
            print("⚠️ .claude/ directory not found - Claude Code integration not available")

    def _create_advanced_mcp_config(
        self, 
        workspace_path: Path, 
        credentials: Dict[str, str], 
        postgres_config: Optional[Dict[str, str]] = None
    ):
        """Create advanced multi-server MCP configuration with health checking."""
        print("\n🔧 Setting up advanced MCP integration...")
        
        try:
            # Generate comprehensive MCP configuration
            mcp_config = self.mcp_config_manager.generate_mcp_config(
                workspace_path=workspace_path,
                credentials=credentials,
                ide_type="claude-code",
                include_fallbacks=True,
                health_check=False  # Skip health checks during init for speed
            )
            
            # Write configuration
            success = self.mcp_config_manager.write_mcp_config(
                workspace_path=workspace_path,
                mcp_config=mcp_config
            )
            
            if success:
                print("✅ Advanced MCP configuration created successfully")
                print("   • Multi-server support enabled")
                print("   • Auto-detection configured")
                print("   • Fallback configurations included")
            else:
                raise Exception("Failed to write MCP configuration")
                
        except Exception as e:
            print(f"⚠️ Advanced MCP configuration failed: {e}")
            print("🔄 Falling back to basic configuration...")
            self._create_basic_mcp_fallback(workspace_path, credentials)

    def _create_basic_mcp_fallback(self, workspace_path: Path, credentials: Dict[str, str]):
        """Create basic MCP configuration as fallback."""
        basic_config = {
            "mcpServers": {
                "postgres": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-postgres"]
                },
                "automagik-hive": {
                    "command": "echo",
                    "args": ["Automagik Hive server not configured - set up manually"]
                }
            }
        }
        
        # Add database URL to postgres if available
        if "database_url" in credentials:
            basic_config["mcpServers"]["postgres"]["args"].append(credentials["database_url"])
        
        mcp_file = workspace_path / ".mcp.json"
        mcp_file.write_text(json.dumps(basic_config, indent=2))
        print("✅ Basic MCP fallback configuration created")

    def _create_ai_structure(self, workspace_path: Path):
        """Create ai/ directory structure with template components."""
        ai_path = workspace_path / "ai"
        ai_path.mkdir(parents=True, exist_ok=True)

        # Create README files
        (ai_path / "README.md").write_text("# AI Components\n\nCustom agents, teams, workflows, and tools for your workspace.\n")

        # Copy template components from package
        package_ai_path = Path(__file__).parent.parent.parent / "ai"
        if package_ai_path.exists():
            print("📋 Copying template AI components...")

            # Create subdirectories and copy templates
            for subdir in ["agents", "teams", "workflows", "tools"]:
                # Create the subdirectory
                (ai_path / subdir).mkdir(parents=True, exist_ok=True)

                # Copy template component if it exists
                template_name = f"template-{subdir[:-1]}"  # Remove 's' from plural
                source_template = package_ai_path / subdir / template_name

                if source_template.exists():
                    dest_template = ai_path / subdir / template_name
                    try:
                        shutil.copytree(source_template, dest_template, dirs_exist_ok=True)
                        print(f"✅ Copied {template_name}")
                    except Exception as e:
                        print(f"⚠️ Could not copy {template_name}: {e}")
                        # Create empty directory as fallback
                        dest_template.mkdir(parents=True, exist_ok=True)
        else:
            print("⚠️ Package AI templates not found - creating empty directories")
            # Fallback: create empty directories
            for subdir in ["agents", "teams", "workflows", "tools"]:
                (ai_path / subdir).mkdir(parents=True, exist_ok=True)

    def _create_gitignore(self, workspace_path: Path):
        """Create .gitignore file."""
        gitignore_content = """# Automagik Hive Workspace
.env
.env.local
data/
logs/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""

        gitignore_file = workspace_path / ".gitignore"
        gitignore_file.write_text(gitignore_content)

    def _create_data_directories(self, workspace_path: Path, container_services: list[str]):
        """Create data directories for persistence with proper permissions."""
        data_path = workspace_path / "data"

        try:
            # Base directories
            base_dirs = ["logs"]
            
            # Add service-specific directories
            if "postgres" in container_services or len(container_services) == 1:
                base_dirs.append("postgres")
            if "agent" in container_services:
                base_dirs.append("postgres-agent")
            if "genie" in container_services:
                base_dirs.append("postgres-genie")

            # Create directories with explicit permissions
            for subdir in base_dirs:
                dir_path = data_path / subdir
                dir_path.mkdir(parents=True, exist_ok=True)
                # Set permissions to allow current user read/write/execute
                dir_path.chmod(0o755)

            print(f"✅ Created data directories for {len(base_dirs)} service(s)")

        except PermissionError as e:
            print(f"❌ Permission error creating data directories: {e}")
            print("💡 This may be due to existing Docker-created files with root ownership")
            print("🔧 Fix: sudo chown -R $USER:$USER data/ (after workspace creation)")
            # Don't fail the entire initialization for this
            print("⚠️ Continuing without data directories - you may need to create them manually")

    def _create_startup_script(self, workspace_path: Path, postgres_config: dict[str, str], container_services: list[str] = None):
        """Create convenience startup script."""
        if postgres_config["type"] == "docker":
            startup_script = """#!/bin/bash
# Automagik Hive Workspace Startup Script
# Generated by uvx automagik-hive --init

set -e

echo "🧞 Starting Automagik Hive Workspace..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start PostgreSQL first
echo "🗄️ Starting PostgreSQL..."
docker compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker compose exec postgres pg_isready -U $(grep POSTGRES_USER .env | cut -d '=' -f2) >/dev/null 2>&1; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done

echo "✅ PostgreSQL is ready!"

# Start the workspace
echo "🚀 Starting workspace server..."
uvx automagik-hive ./

echo "🎉 Workspace started successfully!"
"""
        else:
            startup_script = """#!/bin/bash
# Automagik Hive Workspace Startup Script
# Generated by uvx automagik-hive --init

set -e

echo "🧞 Starting Automagik Hive Workspace..."

# Note: Using external PostgreSQL - ensure it's running and accessible
echo "🗄️ Using external PostgreSQL..."
echo "💡 Make sure your PostgreSQL server is running and accessible"

# Start the workspace
echo "🚀 Starting workspace server..."
uvx automagik-hive ./

echo "🎉 Workspace started successfully!"
"""

        script_file = workspace_path / "start.sh"
        script_file.write_text(startup_script)
        script_file.chmod(0o755)  # Make executable

        # Also create a Windows batch file
        if postgres_config["type"] == "docker":
            windows_script = """@echo off
REM Automagik Hive Workspace Startup Script
REM Generated by uvx automagik-hive --init

echo 🧞 Starting Automagik Hive Workspace...

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker and try again.
    exit /b 1
)

REM Start PostgreSQL first
echo 🗄️ Starting PostgreSQL...
docker compose up -d postgres

REM Wait for PostgreSQL to be ready
echo ⏳ Waiting for PostgreSQL to be ready...
:wait_postgres
timeout /t 2 /nobreak >nul
docker compose exec postgres pg_isready >nul 2>&1
if errorlevel 1 goto wait_postgres

echo ✅ PostgreSQL is ready!

REM Start the workspace
echo 🚀 Starting workspace server...
uvx automagik-hive ./

echo 🎉 Workspace started successfully!
"""
        else:
            windows_script = """@echo off
REM Automagik Hive Workspace Startup Script
REM Generated by uvx automagik-hive --init

echo 🧞 Starting Automagik Hive Workspace...

REM Note: Using external PostgreSQL - ensure it's running and accessible
echo 🗄️ Using external PostgreSQL...
echo 💡 Make sure your PostgreSQL server is running and accessible

REM Start the workspace
echo 🚀 Starting workspace server...
uvx automagik-hive ./

echo 🎉 Workspace started successfully!
"""

        batch_file = workspace_path / "start.bat"
        batch_file.write_text(windows_script)

    def _show_success_message(self, workspace_path: Path):
        """Show success message and next steps."""
        print(f"\n🎉 Workspace '{workspace_path.name}' created successfully!")
        print("\n📋 Quick Start Options:")
        print(f"1. cd {workspace_path}")
        print("2. Choose your preferred startup method:")
        print("   • ./start.sh              # Linux/macOS convenience script")
        print("   • start.bat               # Windows convenience script")
        print("   • uvx automagik-hive ./   # Direct CLI command")
        print("   • docker compose up      # Full Docker Compose")
        print("\n🔧 Configuration:")
        print("- Edit .env to add missing API keys")
        print("- Customize ai/ directory with your components")
        print("- Use .claude/ directory for Claude Code integration")
        print("\n📁 Workspace Structure:")
        print(f"   {workspace_path}/")
        print("   ├── .env                 # Environment configuration")
        print("   ├── docker-compose.yml   # Container orchestration")
        print("   ├── start.sh / start.bat # Convenience startup scripts")
        print("   ├── .claude/             # Claude Code integration")
        print("   ├── .mcp.json            # MCP server configuration")
        print("   ├── ai/                  # Your AI components")
        print("   └── data/                # Persistent data volumes")
        print("\n✨ Your magical development environment is ready!")

    # ========== ADVANCED TEMPLATE PROCESSING SYSTEM ==========
    
    def _load_workspace_config(self, workspace_path: Path) -> Dict[str, Any]:
        """Load workspace-specific configuration for template processing."""
        config = {
            "workspace_name": workspace_path.name,
            "workspace_path": str(workspace_path.absolute()),
            "default_host": "127.0.0.1",
            "default_port": 8886,
            "default_db_port": 5532,
            "database_name": "hive"
        }
        
        # Try to load existing .env for additional context
        env_file = workspace_path / ".env"
        if env_file.exists():
            config.update(self._parse_env_file(env_file))
        
        return config
    
    def _parse_env_file(self, env_file: Path) -> Dict[str, str]:
        """Parse .env file for template variables."""
        env_vars = {}
        try:
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        except Exception as e:
            print(f"⚠️ Warning: Could not parse .env file: {e}")
        
        return env_vars
    
    def _create_template_context(self, workspace_path: Path, postgres_config: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create comprehensive template context for dynamic configuration generation."""
        context = {
            # Workspace information
            "workspace_name": workspace_path.name,
            "workspace_path": str(workspace_path.absolute()),
            
            # Server configuration
            "host": "127.0.0.1",
            "api_port": 8886,
            "mcp_port": 8887,
            
            # Database configuration
            "db_host": "localhost",
            "db_port": 5532,
            "db_name": "hive",
            "db_user": "hive_user",
            
            # Service endpoints
            "api_base_url": "http://127.0.0.1:8886",
            "mcp_base_url": "http://127.0.0.1:8887",
        }
        
        # Override with postgres configuration if provided
        if postgres_config:
            if postgres_config.get("type") == "docker":
                context["db_port"] = postgres_config.get("port", 5532)
            elif postgres_config.get("type") == "external":
                # Parse external connection details
                host = postgres_config.get("host", "localhost")
                port = postgres_config.get("port", "5432") 
                context["db_host"] = host
                context["db_port"] = int(port)
        
        # Generate dynamic URLs
        context.update(self._generate_dynamic_urls(context))
        
        return context
    
    def _generate_dynamic_urls(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate dynamic URLs based on workspace configuration."""
        db_host = context["db_host"]
        db_port = context["db_port"]
        db_name = context["db_name"]
        
        return {
            "database_url": f"postgresql+psycopg://{db_host}:{db_port}/{db_name}",
            "postgres_connection_string": f"postgresql://{db_host}:{db_port}/{db_name}",
            "api_endpoint": f"http://{context['host']}:{context['api_port']}",
            "mcp_endpoint": f"http://{context['host']}:{context['mcp_port']}"
        }
    
    def _generate_dynamic_mcp_config(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dynamic MCP configuration using template context."""
        config = {
            "servers": {
                "automagik-hive": {
                    "command": "uv",
                    "args": [
                        "run", "uvicorn", "api.serve:app", 
                        "--host", context["host"], 
                        "--port", str(context["api_port"])
                    ],
                    "env": {
                        "DATABASE_URL": context["database_url"],
                        "HIVE_DATABASE_URL": context["database_url"]
                    }
                },
                "postgres": {
                    "command": "uv",
                    "args": [
                        "run", "mcp-server-postgres", 
                        "--connection-string", context["postgres_connection_string"]
                    ]
                }
            }
        }
        
        # Add optional servers based on workspace configuration
        if context.get("enable_additional_mcps", False):
            config["servers"].update(self._generate_additional_mcp_servers(context))
        
        return config
    
    def _generate_additional_mcp_servers(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate additional MCP servers based on workspace needs."""
        additional_servers = {}
        
        # Add filesystem MCP if needed
        if context.get("enable_filesystem_mcp", True):
            additional_servers["filesystem"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", context["workspace_path"]]
            }
        
        # Add git MCP if workspace is a git repository
        if (Path(context["workspace_path"]) / ".git").exists():
            additional_servers["git"] = {
                "command": "npx", 
                "args": ["-y", "@modelcontextprotocol/server-git", "--repository", context["workspace_path"]]
            }
        
        return additional_servers
    
    def _validate_mcp_config(self, config: Dict[str, Any]) -> bool:
        """Validate MCP configuration structure and required fields."""
        try:
            # Check top-level structure
            if "servers" not in config:
                print("❌ MCP config validation failed: missing 'servers' key")
                return False
            
            servers = config["servers"]
            if not isinstance(servers, dict):
                print("❌ MCP config validation failed: 'servers' must be a dictionary")
                return False
            
            # Validate each server configuration
            for server_name, server_config in servers.items():
                if not self._validate_server_config(server_name, server_config):
                    return False
            
            print("✅ MCP configuration validation passed")
            return True
            
        except Exception as e:
            print(f"❌ MCP config validation error: {e}")
            return False
    
    def _validate_server_config(self, server_name: str, config: Dict[str, Any]) -> bool:
        """Validate individual server configuration."""
        required_fields = ["command", "args"]
        
        for field in required_fields:
            if field not in config:
                print(f"❌ Server '{server_name}' missing required field: {field}")
                return False
        
        # Validate command exists (basic check)
        command = config["command"]
        if not isinstance(command, str) or not command.strip():
            print(f"❌ Server '{server_name}' has invalid command")
            return False
        
        # Validate args is a list
        args = config["args"]
        if not isinstance(args, list):
            print(f"❌ Server '{server_name}' args must be a list")
            return False
        
        return True
    
    def _create_fallback_mcp_config(self, workspace_path: Path):
        """Create fallback MCP configuration if dynamic generation fails."""
        print("🔄 Creating fallback MCP configuration...")
        
        fallback_config = {
            "servers": {
                "automagik-hive": {
                    "command": "uv",
                    "args": ["run", "uvicorn", "api.serve:app", "--host", "127.0.0.1", "--port", "8886"],
                    "env": {
                        "DATABASE_URL": "postgresql+psycopg://localhost:5532/hive",
                        "HIVE_DATABASE_URL": "postgresql+psycopg://localhost:5532/hive"
                    }
                },
                "postgres": {
                    "command": "uv",
                    "args": ["run", "mcp-server-postgres", "--connection-string", "postgresql://localhost:5532/hive"]
                }
            }
        }
        
        mcp_file = workspace_path / ".mcp.json"
        mcp_file.write_text(json.dumps(fallback_config, indent=2))
        print("✅ Created fallback .mcp.json configuration")
    
    def _process_template_placeholders(self, template_content: str, context: Dict[str, Any]) -> str:
        """Advanced placeholder replacement with validation."""
        try:
            # Define placeholder patterns
            patterns = {
                'simple': r'\{\{(\w+)\}\}',                    # {{variable}}
                'nested': r'\{\{(\w+)\.(\w+)\}\}',             # {{object.property}}
                'env': r'\$\{(\w+)\}',                         # ${ENV_VAR}
                'conditional': r'\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}',  # {{#if condition}}content{{/if}}
            }
            
            processed_content = template_content
            
            # Process simple placeholders
            def replace_simple(match):
                key = match.group(1)
                value = context.get(key, f"MISSING_{key}")
                if value == f"MISSING_{key}":
                    print(f"⚠️ Warning: Missing template variable: {key}")
                return str(value)
            
            processed_content = re.sub(patterns['simple'], replace_simple, processed_content)
            
            # Process nested placeholders
            def replace_nested(match):
                obj_key, prop_key = match.group(1), match.group(2)
                obj = context.get(obj_key, {})
                if isinstance(obj, dict):
                    value = obj.get(prop_key, f"MISSING_{obj_key}.{prop_key}")
                else:
                    value = f"MISSING_{obj_key}.{prop_key}"
                
                if str(value).startswith("MISSING_"):
                    print(f"⚠️ Warning: Missing nested template variable: {obj_key}.{prop_key}")
                return str(value)
            
            processed_content = re.sub(patterns['nested'], replace_nested, processed_content)
            
            # Process environment variables
            def replace_env(match):
                env_var = match.group(1)
                import os
                value = os.getenv(env_var, f"MISSING_ENV_{env_var}")
                if value == f"MISSING_ENV_{env_var}":
                    print(f"⚠️ Warning: Missing environment variable: {env_var}")
                return str(value)
            
            processed_content = re.sub(patterns['env'], replace_env, processed_content)
            
            # Process conditional blocks
            def replace_conditional(match):
                condition = match.group(1)
                content = match.group(2)
                if context.get(condition, False):
                    return content
                return ""
            
            processed_content = re.sub(patterns['conditional'], replace_conditional, processed_content, flags=re.DOTALL)
            
            return processed_content
            
        except Exception as e:
            print(f"❌ Template processing error: {e}")
            return template_content  # Return original on error
    
    def _validate_template_processing(self, processed_content: str) -> bool:
        """Validate that template processing completed successfully."""
        # Check for unprocessed placeholders
        unprocessed_patterns = [
            r'\{\{\w+\}\}',           # {{variable}}
            r'\{\{\w+\.\w+\}\}',      # {{object.property}}
            r'\$\{\w+\}',             # ${ENV_VAR}
            r'MISSING_\w+',           # Missing variables
        ]
        
        for pattern in unprocessed_patterns:
            matches = re.findall(pattern, processed_content)
            if matches:
                print(f"⚠️ Warning: Unprocessed template placeholders found: {matches}")
                return False
        
        return True
