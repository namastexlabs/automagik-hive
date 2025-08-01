#!/usr/bin/env python3
"""Docker Compose CLI for UVX Automagik Hive.

Provides command-line interface for T1.7: Foundational Services Containerization.
Integrates with existing credential management and Docker Compose service.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.docker.compose_service import DockerComposeService
from lib.logging import logger


def setup_foundational_services(
    workspace_path: Path,
    postgres_port: int = 5532,
    postgres_database: str = "hive",
    api_port: int = 8886,
    include_app: bool = False,
    verbose: bool = False,
) -> bool:
    """CLI command for setting up foundational services containerization.

    Implements T1.7: Complete PostgreSQL container and credential management
    within Docker Compose strategy.

    Args:
        workspace_path: Path to workspace directory
        postgres_port: PostgreSQL external port
        postgres_database: PostgreSQL database name
        api_port: API server port
        include_app: Include application service in compose
        verbose: Enable verbose output

    Returns:
        True if setup successful, False otherwise
    """
    try:
        logger.info(
            "Starting foundational services setup", workspace=str(workspace_path)
        )

        if verbose:
            pass

        # Initialize Docker Compose service
        compose_service = DockerComposeService(workspace_path)

        # Setup foundational services
        compose_path, env_path, data_dir = compose_service.setup_foundational_services(
            postgres_port=postgres_port,
            postgres_database=postgres_database,
            api_port=api_port,
            include_app_service=include_app,
        )

        if verbose:
            pass

        logger.info("Foundational services setup completed successfully")
        return True

    except Exception as e:
        logger.error("Foundational services setup failed", error=str(e))
        if verbose:
            pass
        return False


def generate_postgres_container_template(
    output_path: Path | None = None,
    postgres_port: int = 5532,
    postgres_database: str = "hive",
    verbose: bool = False,
) -> bool:
    """CLI command for generating PostgreSQL container template only.

    Args:
        output_path: Output path for docker-compose.yml
        postgres_port: PostgreSQL external port
        postgres_database: PostgreSQL database name
        verbose: Enable verbose output

    Returns:
        True if generation successful, False otherwise
    """
    try:
        logger.info("Generating PostgreSQL container template", port=postgres_port)

        if verbose:
            pass

        # Initialize service
        workspace_path = output_path.parent if output_path else Path.cwd()
        compose_service = DockerComposeService(workspace_path)

        # Generate PostgreSQL-only template
        compose_config = compose_service.generate_complete_docker_compose_template(
            postgres_port=postgres_port,
            postgres_database=postgres_database,
            include_app_service=False,
        )

        # Save template
        compose_service.save_docker_compose_template(compose_config, output_path)

        if verbose:
            pass

        logger.info("PostgreSQL container template generated successfully")
        return True

    except Exception as e:
        logger.error("PostgreSQL template generation failed", error=str(e))
        if verbose:
            pass
        return False


def generate_workspace_credentials(
    workspace_path: Path,
    postgres_port: int = 5532,
    postgres_database: str = "hive",
    api_port: int = 8886,
    verbose: bool = False,
) -> bool:
    """CLI command for generating workspace credentials only.

    Args:
        workspace_path: Path to workspace directory
        postgres_port: PostgreSQL port
        postgres_database: PostgreSQL database name
        api_port: API server port
        verbose: Enable verbose output

    Returns:
        True if generation successful, False otherwise
    """
    try:
        logger.info("Generating workspace credentials", workspace=str(workspace_path))

        if verbose:
            pass

        # Initialize service
        compose_service = DockerComposeService(workspace_path)

        # Generate credentials and environment file
        env_content = compose_service.generate_workspace_environment_file(
            postgres_port=postgres_port,
            postgres_database=postgres_database,
            api_port=api_port,
        )

        # Save environment file
        compose_service.save_environment_file(env_content)

        if verbose:
            pass

        logger.info("Workspace credentials generated successfully")
        return True

    except Exception as e:
        logger.error("Workspace credentials generation failed", error=str(e))
        if verbose:
            pass
        return False


def setup_postgres_data_directories(
    workspace_path: Path,
    postgres_data_path: str = "./data/postgres",
    verbose: bool = False,
) -> bool:
    """CLI command for setting up PostgreSQL data directories.

    Args:
        workspace_path: Path to workspace directory
        postgres_data_path: Relative path for PostgreSQL data
        verbose: Enable verbose output

    Returns:
        True if setup successful, False otherwise
    """
    try:
        logger.info(
            "Setting up PostgreSQL data directories", workspace=str(workspace_path)
        )

        if verbose:
            pass

        # Initialize service
        compose_service = DockerComposeService(workspace_path)

        # Create data directories
        compose_service.create_data_directories(postgres_data_path)

        if verbose:
            pass

        logger.info("PostgreSQL data directories setup completed")
        return True

    except Exception as e:
        logger.error("PostgreSQL data directories setup failed", error=str(e))
        if verbose:
            pass
        return False


def validate_docker_compose_setup(workspace_path: Path, verbose: bool = False) -> bool:
    """CLI command for validating Docker Compose setup.

    Args:
        workspace_path: Path to workspace directory
        verbose: Enable verbose output

    Returns:
        True if validation successful, False otherwise
    """
    try:
        logger.info("Validating Docker Compose setup", workspace=str(workspace_path))

        if verbose:
            pass

        # Check required files
        compose_file = workspace_path / "docker-compose.yml"
        env_file = workspace_path / ".env"
        data_dir = workspace_path / "data" / "postgres"

        validation_results = {
            "docker-compose.yml": compose_file.exists(),
            ".env file": env_file.exists(),
            "PostgreSQL data directory": data_dir.exists(),
            ".env permissions": env_file.stat().st_mode & 0o777 == 0o600
            if env_file.exists()
            else False,
        }

        all_valid = all(validation_results.values())

        if verbose:
            for _item, _valid in validation_results.items():
                pass

        if all_valid:
            pass
        else:
            pass

        logger.info("Docker Compose setup validation completed", valid=all_valid)
        return all_valid

    except Exception as e:
        logger.error("Docker Compose setup validation failed", error=str(e))
        if verbose:
            pass
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Docker Compose CLI for UVX Automagik Hive Foundational Services"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Setup foundational services command
    setup_parser = subparsers.add_parser(
        "setup", help="Setup foundational services containerization"
    )
    setup_parser.add_argument(
        "workspace_path", type=Path, help="Workspace directory path"
    )
    setup_parser.add_argument(
        "--postgres-port", type=int, default=5532, help="PostgreSQL external port"
    )
    setup_parser.add_argument(
        "--postgres-db", default="hive", help="PostgreSQL database name"
    )
    setup_parser.add_argument(
        "--api-port", type=int, default=8886, help="API server port"
    )
    setup_parser.add_argument(
        "--include-app", action="store_true", help="Include application service"
    )
    setup_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    # Generate PostgreSQL template command
    postgres_parser = subparsers.add_parser(
        "postgres", help="Generate PostgreSQL container template"
    )
    postgres_parser.add_argument(
        "--output", type=Path, help="Output path for docker-compose.yml"
    )
    postgres_parser.add_argument(
        "--port", type=int, default=5532, help="PostgreSQL external port"
    )
    postgres_parser.add_argument(
        "--database", default="hive", help="PostgreSQL database name"
    )
    postgres_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    # Generate credentials command
    creds_parser = subparsers.add_parser(
        "credentials", help="Generate workspace credentials"
    )
    creds_parser.add_argument(
        "workspace_path", type=Path, help="Workspace directory path"
    )
    creds_parser.add_argument(
        "--postgres-port", type=int, default=5532, help="PostgreSQL port"
    )
    creds_parser.add_argument(
        "--postgres-db", default="hive", help="PostgreSQL database name"
    )
    creds_parser.add_argument(
        "--api-port", type=int, default=8886, help="API server port"
    )
    creds_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    # Setup data directories command
    data_parser = subparsers.add_parser(
        "data", help="Setup PostgreSQL data directories"
    )
    data_parser.add_argument(
        "workspace_path", type=Path, help="Workspace directory path"
    )
    data_parser.add_argument(
        "--data-path", default="./data/postgres", help="PostgreSQL data path"
    )
    data_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    # Validate setup command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate Docker Compose setup"
    )
    validate_parser.add_argument(
        "workspace_path", type=Path, help="Workspace directory path"
    )
    validate_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    args = parser.parse_args()

    if args.command == "setup":
        success = setup_foundational_services(
            workspace_path=args.workspace_path,
            postgres_port=args.postgres_port,
            postgres_database=args.postgres_db,
            api_port=args.api_port,
            include_app=args.include_app,
            verbose=args.verbose,
        )
        sys.exit(0 if success else 1)

    elif args.command == "postgres":
        success = generate_postgres_container_template(
            output_path=args.output,
            postgres_port=args.port,
            postgres_database=args.database,
            verbose=args.verbose,
        )
        sys.exit(0 if success else 1)

    elif args.command == "credentials":
        success = generate_workspace_credentials(
            workspace_path=args.workspace_path,
            postgres_port=args.postgres_port,
            postgres_database=args.postgres_db,
            api_port=args.api_port,
            verbose=args.verbose,
        )
        sys.exit(0 if success else 1)

    elif args.command == "data":
        success = setup_postgres_data_directories(
            workspace_path=args.workspace_path,
            postgres_data_path=args.data_path,
            verbose=args.verbose,
        )
        sys.exit(0 if success else 1)

    elif args.command == "validate":
        success = validate_docker_compose_setup(
            workspace_path=args.workspace_path, verbose=args.verbose
        )
        sys.exit(0 if success else 1)

    else:
        parser.print_help()
        sys.exit(1)
