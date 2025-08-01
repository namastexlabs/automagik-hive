"""Container strategy implementation for UVX Automagik Hive.

Implements the expert-recommended Docker Compose multi-container architecture:
- Main Workspace: UVX CLI + Docker PostgreSQL (port 8886 + 5532)
- Genie Container: All-in-one PostgreSQL + FastAPI (port 48886)
- Agent Container: All-in-one PostgreSQL + FastAPI (port 35532)

Provides high-level orchestration of environment validation and container deployment.
"""

from dataclasses import dataclass
from pathlib import Path

from .environment import (
    EnvironmentValidation,
    EnvironmentValidator,
    print_validation_results,
)
from .templates import ContainerCredentials, ContainerTemplateManager


@dataclass
class ContainerStrategy:
    """Container orchestration strategy configuration."""

    name: str
    description: str
    services: list[str]
    ports: dict[str, int]
    validation_ports: list[int]


class ContainerOrchestrator:
    """High-level container orchestration for UVX Automagik Hive."""

    # Supported container strategies
    STRATEGIES = {
        "workspace": ContainerStrategy(
            name="Main Workspace",
            description="UVX CLI with Docker PostgreSQL",
            services=["postgres"],
            ports={"workspace": 8886, "postgres": 5532},
            validation_ports=[8886, 5532],
        ),
        "genie": ContainerStrategy(
            name="Genie Consultation",
            description="All-in-one Genie service container",
            services=["genie-server", "genie-postgres"],
            ports={"genie": 48886},
            validation_ports=[48886],
        ),
        "agent": ContainerStrategy(
            name="Agent Development",
            description="Agent development environment container",
            services=["app-agent", "postgres-agent"],
            ports={"agent": 35532},
            validation_ports=[35532],
        ),
        "full": ContainerStrategy(
            name="Full System",
            description="Complete multi-container system",
            services=[
                "postgres",
                "genie-server",
                "genie-postgres",
                "app-agent",
                "postgres-agent",
            ],
            ports={"workspace": 8886, "postgres": 5532, "genie": 48886, "agent": 35532},
            validation_ports=[8886, 5532, 48886, 35532],
        ),
    }

    def __init__(self):
        self.env_validator = EnvironmentValidator()
        self.template_manager = ContainerTemplateManager()

    def validate_and_prepare_workspace(
        self,
        workspace_path: Path,
        strategy: str = "workspace",
        credentials: ContainerCredentials | None = None,
        interactive: bool = True,
    ) -> tuple[bool, EnvironmentValidation, dict[str, Path] | None]:
        """Validate environment and prepare workspace with containers.

        Args:
            workspace_path: Target workspace directory
            strategy: Container strategy ("workspace", "genie", "agent", "full")
            credentials: Container credentials (generated if not provided)
            interactive: Whether to print results and prompt user

        Returns:
            Tuple of (success, validation_results, generated_files)
        """
        # Get strategy configuration
        if strategy not in self.STRATEGIES:
            raise ValueError(
                f"Unknown strategy: {strategy}. Available: {list(self.STRATEGIES.keys())}"
            )

        strategy_config = self.STRATEGIES[strategy]

        # Validate environment
        validation = self.env_validator.validate_all(strategy_config.validation_ports)

        if interactive:
            print_validation_results(validation)

        # If validation failed, return early
        if not validation.overall_passed:
            if interactive:
                pass
            return False, validation, None

        # Generate credentials if not provided
        if credentials is None:
            credentials = self._generate_default_credentials()

        # Prepare workspace and generate container templates
        try:
            generated_files = self._prepare_workspace_containers(
                workspace_path, strategy, credentials
            )

            if interactive:
                for _template_type, _file_path in generated_files.items():
                    pass

            return True, validation, generated_files

        except Exception:
            if interactive:
                pass
            return False, validation, None

    def validate_container_environment(
        self, strategy: str = "workspace", interactive: bool = True
    ) -> EnvironmentValidation:
        """Validate environment for specific container strategy.

        Args:
            strategy: Container strategy to validate for
            interactive: Whether to print results

        Returns:
            Environment validation results
        """
        if strategy not in self.STRATEGIES:
            raise ValueError(f"Unknown strategy: {strategy}")

        strategy_config = self.STRATEGIES[strategy]
        validation = self.env_validator.validate_all(strategy_config.validation_ports)

        if interactive:
            print_validation_results(validation)

        return validation

    def get_strategy_info(self, strategy: str) -> ContainerStrategy | None:
        """Get information about a container strategy."""
        return self.STRATEGIES.get(strategy)

    def list_strategies(self) -> dict[str, ContainerStrategy]:
        """List all available container strategies."""
        return self.STRATEGIES.copy()

    def _prepare_workspace_containers(
        self, workspace_path: Path, strategy: str, credentials: ContainerCredentials
    ) -> dict[str, Path]:
        """Prepare workspace with appropriate container templates."""
        # Create workspace directory
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Create required directories
        self.template_manager.create_required_directories(workspace_path)

        # Generate templates based on strategy
        generated_files = {}

        if strategy in ["workspace", "full"]:
            generated_files["workspace"] = (
                self.template_manager.generate_workspace_compose(
                    workspace_path, credentials
                )
            )

        if strategy in ["genie", "full"]:
            generated_files["genie"] = self.template_manager.generate_genie_compose(
                workspace_path, credentials
            )

        if strategy in ["agent", "full"]:
            generated_files["agent"] = self.template_manager.copy_agent_template(
                workspace_path, credentials
            )

        return generated_files

    def _generate_default_credentials(self) -> ContainerCredentials:
        """Generate default secure credentials for containers."""
        import base64
        import secrets

        # Generate secure random credentials
        postgres_user = base64.b64encode(secrets.token_bytes(12)).decode()[:16]
        postgres_password = base64.b64encode(secrets.token_bytes(12)).decode()[:16]
        hive_api_key = f"hive_{secrets.token_hex(16)}"

        return ContainerCredentials(
            postgres_user=postgres_user,
            postgres_password=postgres_password,
            postgres_db="hive",
            hive_api_key=hive_api_key,
        )


# Convenience functions for common operations
def validate_workspace_environment(interactive: bool = True) -> EnvironmentValidation:
    """Validate environment for main workspace operations."""
    orchestrator = ContainerOrchestrator()
    return orchestrator.validate_container_environment("workspace", interactive)


def validate_full_system_environment(interactive: bool = True) -> EnvironmentValidation:
    """Validate environment for full multi-container system."""
    orchestrator = ContainerOrchestrator()
    return orchestrator.validate_container_environment("full", interactive)


def prepare_workspace_with_strategy(
    workspace_path: Path, strategy: str = "workspace", interactive: bool = True
) -> tuple[bool, dict[str, Path]]:
    """Prepare workspace with specific container strategy.

    Returns:
        Tuple of (success, generated_files)
    """
    orchestrator = ContainerOrchestrator()
    success, validation, files = orchestrator.validate_and_prepare_workspace(
        workspace_path, strategy, interactive=interactive
    )
    return success, files or {}
