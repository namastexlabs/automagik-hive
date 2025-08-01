"""Container template management for UVX Automagik Hive.

Provides Docker Compose template generation with:
- Secure credential injection
- Multi-service container orchestration
- Cross-platform compatibility
- Template customization based on workspace needs
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ContainerCredentials:
    """Container service credentials for template generation."""

    postgres_user: str
    postgres_password: str
    postgres_db: str
    hive_api_key: str
    postgres_uid: str = "1000"
    postgres_gid: str = "1000"


@dataclass
class ContainerTemplate:
    """Container template configuration."""

    name: str
    filename: str
    description: str
    ports: dict[str, int]
    required_volumes: list[str]


class ContainerTemplateManager:
    """Manages Docker Compose template generation and customization."""

    # Template registry
    TEMPLATES = {
        "workspace": ContainerTemplate(
            name="Main Workspace",
            filename="docker-compose-workspace.yml",
            description="PostgreSQL service for UVX CLI integration",
            ports={"postgres": 5532},
            required_volumes=["./data/postgres"],
        ),
        "genie": ContainerTemplate(
            name="Genie Consultation",
            filename="docker-compose-genie.yml",
            description="All-in-one Genie service with PostgreSQL",
            ports={"genie": 48886, "postgres": 5432},
            required_volumes=["./data/postgres-genie"],
        ),
        "agent": ContainerTemplate(
            name="Agent Development",
            filename="docker-compose-agent.yml",
            description="Agent development environment with PostgreSQL",
            ports={"agent": 35532, "postgres": 35532},
            required_volumes=["./data/postgres-agent"],
        ),
    }

    def __init__(self, package_templates_dir: Path | None = None):
        """Initialize template manager.

        Args:
            package_templates_dir: Path to package templates directory
        """
        if package_templates_dir is None:
            # Default to docker/templates/ directory in package root
            package_root = Path(__file__).parent.parent.parent
            package_templates_dir = package_root / "docker" / "templates"

        self.templates_dir = package_templates_dir

    def generate_workspace_compose(
        self,
        workspace_path: Path,
        credentials: ContainerCredentials,
        custom_config: dict[str, Any] | None = None,
    ) -> Path:
        """Generate main workspace Docker Compose file.

        Args:
            workspace_path: Target workspace directory
            credentials: Database and API credentials
            custom_config: Optional custom configuration overrides

        Returns:
            Path to generated docker-compose.yml file
        """
        template_path = self.templates_dir / "workspace.yml"
        output_path = workspace_path / "docker-compose.yml"

        # Load template
        compose_config = self._load_template(template_path)

        # Apply credentials
        self._apply_credentials(compose_config, credentials, "workspace")

        # Apply custom configuration
        if custom_config:
            self._merge_config(compose_config, custom_config)

        # Write generated file
        self._write_compose_file(output_path, compose_config)

        return output_path

    def generate_genie_compose(
        self,
        workspace_path: Path,
        credentials: ContainerCredentials,
        custom_config: dict[str, Any] | None = None,
    ) -> Path:
        """Generate Genie consultation Docker Compose file.

        Args:
            workspace_path: Target workspace directory
            credentials: Database and API credentials
            custom_config: Optional custom configuration overrides

        Returns:
            Path to generated docker-compose-genie.yml file
        """
        template_path = self.templates_dir / "genie.yml"
        output_path = workspace_path / "genie" / "docker-compose-genie.yml"

        # Ensure genie directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load template
        compose_config = self._load_template(template_path)

        # Apply credentials with genie-specific adjustments
        genie_credentials = ContainerCredentials(
            postgres_user=f"genie_{credentials.postgres_user}",
            postgres_password=credentials.postgres_password,
            postgres_db="hive_genie",
            hive_api_key=credentials.hive_api_key,
            postgres_uid=credentials.postgres_uid,
            postgres_gid=credentials.postgres_gid,
        )
        self._apply_credentials(compose_config, genie_credentials, "genie")

        # Apply custom configuration
        if custom_config:
            self._merge_config(compose_config, custom_config)

        # Write generated file
        self._write_compose_file(output_path, compose_config)

        return output_path

    def generate_agent_compose(
        self,
        workspace_path: Path,
        credentials: ContainerCredentials,
        custom_config: dict[str, Any] | None = None,
    ) -> Path:
        """Generate agent development Docker Compose file.

        Args:
            workspace_path: Target workspace directory
            credentials: Database and API credentials
            custom_config: Optional custom configuration overrides

        Returns:
            Path to generated docker-compose-agent.yml file
        """
        template_path = self.templates_dir / "agent.yml"
        output_path = workspace_path / "agent-dev" / "docker-compose-agent.yml"

        # Ensure agent-dev directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load template
        compose_config = self._load_template(template_path)

        # Apply credentials with agent-specific adjustments
        agent_credentials = ContainerCredentials(
            postgres_user=f"agent_{credentials.postgres_user}",
            postgres_password=credentials.postgres_password,
            postgres_db="hive_agent",
            hive_api_key=credentials.hive_api_key,
            postgres_uid=credentials.postgres_uid,
            postgres_gid=credentials.postgres_gid,
        )
        self._apply_credentials(compose_config, agent_credentials, "agent")

        # Apply custom configuration
        if custom_config:
            self._merge_config(compose_config, custom_config)

        # Write generated file
        self._write_compose_file(output_path, compose_config)

        return output_path

    def generate_all_templates(
        self, workspace_path: Path, credentials: ContainerCredentials
    ) -> dict[str, Path]:
        """Generate all container templates for a workspace.

        Args:
            workspace_path: Target workspace directory
            credentials: Database and API credentials

        Returns:
            Dictionary mapping template name to generated file path
        """
        generated_files = {}

        # Generate main workspace compose
        generated_files["workspace"] = self.generate_workspace_compose(
            workspace_path, credentials
        )

        # Generate Genie compose
        generated_files["genie"] = self.generate_genie_compose(
            workspace_path, credentials
        )

        # Generate agent compose
        generated_files["agent"] = self.generate_agent_compose(
            workspace_path, credentials
        )

        return generated_files

    def create_required_directories(self, workspace_path: Path) -> None:
        """Create all required directories for container data persistence."""
        required_dirs = [
            "data/postgres",
            "data/postgres-genie",
            "data/postgres-agent",
            "genie",
            "agent-dev",
        ]

        for dir_path in required_dirs:
            full_path = workspace_path / dir_path
            full_path.mkdir(parents=True, exist_ok=True)

    def _load_template(self, template_path: Path) -> dict[str, Any]:
        """Load Docker Compose template from YAML file."""
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path) as f:
            return yaml.safe_load(f)

    def _apply_credentials(
        self,
        compose_config: dict[str, Any],
        credentials: ContainerCredentials,
        service_type: str,
    ) -> None:
        """Apply credentials to Docker Compose configuration."""
        # Apply environment variables to all services
        if "services" in compose_config:
            for service_config in compose_config["services"].values():
                if "environment" in service_config:
                    env_vars = service_config["environment"]

                    # Apply credentials to environment variables
                    for i, env_var in enumerate(env_vars):
                        if isinstance(env_var, str):
                            # Replace placeholder variables
                            env_var = env_var.replace(
                                "${POSTGRES_USER:-workspace}", credentials.postgres_user
                            )
                            env_var = env_var.replace(
                                f"${{{f'POSTGRES_USER:-{service_type}'}}}",
                                credentials.postgres_user,
                            )
                            env_var = env_var.replace(
                                "${POSTGRES_PASSWORD:-workspace}",
                                credentials.postgres_password,
                            )
                            env_var = env_var.replace(
                                f"${{{f'POSTGRES_PASSWORD:-{service_type}'}}}",
                                credentials.postgres_password,
                            )
                            env_var = env_var.replace(
                                "${POSTGRES_UID:-1000}", credentials.postgres_uid
                            )
                            env_var = env_var.replace(
                                "${POSTGRES_GID:-1000}", credentials.postgres_gid
                            )

                            env_vars[i] = env_var

                # Apply user configuration
                if "user" in service_config:
                    user_config = service_config["user"]
                    user_config = user_config.replace(
                        "${POSTGRES_UID:-1000}", credentials.postgres_uid
                    )
                    user_config = user_config.replace(
                        "${POSTGRES_GID:-1000}", credentials.postgres_gid
                    )
                    service_config["user"] = user_config

    def _merge_config(
        self, base_config: dict[str, Any], custom_config: dict[str, Any]
    ) -> None:
        """Merge custom configuration into base configuration."""
        for key, value in custom_config.items():
            if (
                key in base_config
                and isinstance(base_config[key], dict)
                and isinstance(value, dict)
            ):
                self._merge_config(base_config[key], value)
            else:
                base_config[key] = value

    def _write_compose_file(
        self, output_path: Path, compose_config: dict[str, Any]
    ) -> None:
        """Write Docker Compose configuration to file."""
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write YAML file with proper formatting
        with open(output_path, "w") as f:
            yaml.dump(
                compose_config, f, default_flow_style=False, indent=2, sort_keys=False
            )

    def get_template_info(self, template_name: str) -> ContainerTemplate | None:
        """Get information about a specific template."""
        return self.TEMPLATES.get(template_name)

    def list_templates(self) -> dict[str, ContainerTemplate]:
        """List all available container templates."""
        return self.TEMPLATES.copy()


# Convenience functions for common operations
def generate_workspace_containers(
    workspace_path: Path, credentials: ContainerCredentials
) -> dict[str, Path]:
    """Generate all container templates for a new workspace."""
    manager = ContainerTemplateManager()
    manager.create_required_directories(workspace_path)
    return manager.generate_all_templates(workspace_path, credentials)
