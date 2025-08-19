#!/usr/bin/env python3
"""
CLI utilities for Automagik Hive authentication management.
Enhanced with comprehensive credential management service integration.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.auth.credential_service import CredentialService
from lib.auth.init_service import AuthInitService
from lib.logging import logger


def show_current_key() -> None:
    """Display the current API key."""
    init_service = AuthInitService()
    key = init_service.get_current_key()

    if key:
        from lib.config.settings import settings
        logger.info("Current API key retrieved", key_length=len(key), port=settings().hive_api_port)
    else:
        logger.warning("No API key found")


def regenerate_key() -> None:
    """Generate a new API key."""
    init_service = AuthInitService()
    api_key = init_service.regenerate_key()
    logger.info("API key regenerated", key_length=len(api_key))


def show_auth_status() -> None:
    """Show authentication configuration status."""
    auth_disabled = os.getenv("HIVE_AUTH_DISABLED", "false").lower() == "true"

    logger.info("Auth status requested", auth_disabled=auth_disabled)

    if auth_disabled:
        logger.warning("Authentication disabled - development mode")
    else:
        show_current_key()


def generate_postgres_credentials(
    host: str = "localhost",
    port: int = 5532,
    database: str = "hive",
    env_file: Path | None = None,
) -> dict[str, str]:
    """
    Generate secure PostgreSQL credentials using CLI-compatible service.

    Args:
        host: Database host
        port: Database port
        database: Database name
        env_file: Path to environment file

    Returns:
        Generated credentials dictionary
    """
    credential_service = CredentialService(env_file)
    creds = credential_service.generate_postgres_credentials(host, port, database)

    logger.info(
        "PostgreSQL credentials generated via CLI", database=database, port=port
    )

    return creds


def generate_complete_workspace_credentials(
    workspace_path: Path | None = None,
    postgres_host: str = "localhost",
    postgres_port: int = 5532,
    postgres_database: str = "hive",
) -> dict[str, str]:
    """
    Generate complete set of credentials for workspace initialization.

    Args:
        workspace_path: Path to workspace directory
        postgres_host: PostgreSQL host
        postgres_port: PostgreSQL port
        postgres_database: PostgreSQL database name

    Returns:
        Complete credentials dictionary
    """
    credential_service = CredentialService(project_root=workspace_path)
    creds = credential_service.setup_complete_credentials(
        postgres_host, postgres_port, postgres_database
    )

    logger.info(
        "Complete workspace credentials generated", workspace_path=str(workspace_path)
    )

    return creds


def generate_agent_credentials(
    port: int = 35532, database: str = "hive_agent", env_file: Path | None = None
) -> dict[str, str]:
    """
    Generate agent-specific credentials with unified approach.

    Args:
        port: Agent database port
        database: Agent database name
        env_file: Path to environment file

    Returns:
        Agent credentials dictionary
    """
    credential_service = CredentialService(env_file)
    creds = credential_service.generate_agent_credentials(port, database)

    logger.info("Agent credentials generated via CLI", database=database, port=port)

    return creds


def show_credential_status(env_file: Path | None = None) -> None:
    """
    Show comprehensive credential status.

    Args:
        env_file: Path to environment file
    """
    credential_service = CredentialService(env_file)
    status = credential_service.get_credential_status()

    logger.info("Credential status requested")

    if status.get("validation"):
        validation = status["validation"]
        if "postgres_user_valid" in validation:
            pass
        if "postgres_password_valid" in validation:
            pass
        if "postgres_url_valid" in validation:
            pass
        if "api_key_valid" in validation:
            pass

    if status["postgres_configured"]:
        status["postgres_credentials"]


def sync_mcp_credentials(
    mcp_file: Path | None = None, env_file: Path | None = None
) -> None:
    """
    Synchronize MCP configuration with current credentials.

    Args:
        mcp_file: Path to MCP config file
        env_file: Path to environment file
    """
    credential_service = CredentialService(env_file)
    credential_service.sync_mcp_config_with_credentials(mcp_file)

    logger.info("MCP configuration synchronized with credentials")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Automagik Hive Authentication and Credential Management"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Original authentication commands
    auth_parser = subparsers.add_parser("auth", help="Authentication management")
    auth_parser.add_argument(
        "action",
        choices=["show", "regenerate", "status"],
        help="Authentication action to perform",
    )

    # Credential management commands
    cred_parser = subparsers.add_parser("credentials", help="Credential management")
    cred_subparsers = cred_parser.add_subparsers(
        dest="cred_action", help="Credential actions"
    )

    # PostgreSQL credentials
    postgres_parser = cred_subparsers.add_parser(
        "postgres", help="Generate PostgreSQL credentials"
    )
    postgres_parser.add_argument("--host", default="localhost", help="Database host")
    postgres_parser.add_argument("--port", type=int, default=5532, help="Database port")
    postgres_parser.add_argument("--database", default="hive", help="Database name")
    postgres_parser.add_argument("--env-file", type=Path, help="Environment file path")

    # Agent credentials
    agent_parser = cred_subparsers.add_parser(
        "agent", help="Generate agent credentials"
    )
    agent_parser.add_argument(
        "--port", type=int, default=35532, help="Agent database port"
    )
    agent_parser.add_argument(
        "--database", default="hive_agent", help="Agent database name"
    )
    agent_parser.add_argument("--env-file", type=Path, help="Environment file path")

    # Complete workspace credentials
    workspace_parser = cred_subparsers.add_parser(
        "workspace", help="Generate complete workspace credentials"
    )
    workspace_parser.add_argument(
        "workspace_path", type=Path, help="Workspace directory path"
    )
    workspace_parser.add_argument("--host", default="localhost", help="Database host")
    workspace_parser.add_argument(
        "--port", type=int, default=5532, help="Database port"
    )
    workspace_parser.add_argument("--database", default="hive", help="Database name")

    # Credential status
    status_parser = cred_subparsers.add_parser("status", help="Show credential status")
    status_parser.add_argument("--env-file", type=Path, help="Environment file path")

    # MCP sync
    mcp_parser = cred_subparsers.add_parser(
        "sync-mcp", help="Sync MCP configuration with credentials"
    )
    mcp_parser.add_argument("--mcp-file", type=Path, help="MCP config file path")
    mcp_parser.add_argument("--env-file", type=Path, help="Environment file path")

    args = parser.parse_args()

    # Handle authentication commands (backward compatibility)
    if args.command == "auth":
        if args.action == "show":
            show_current_key()
        elif args.action == "regenerate":
            regenerate_key()
        elif args.action == "status":
            show_auth_status()

    # Handle credential management commands
    elif args.command == "credentials":
        if args.cred_action == "postgres":
            generate_postgres_credentials(
                host=args.host,
                port=args.port,
                database=args.database,
                env_file=args.env_file,
            )
        elif args.cred_action == "agent":
            generate_agent_credentials(
                port=args.port, database=args.database, env_file=args.env_file
            )
        elif args.cred_action == "workspace":
            generate_complete_workspace_credentials(
                workspace_path=args.workspace_path,
                postgres_host=args.host,
                postgres_port=args.port,
                postgres_database=args.database,
            )
        elif args.cred_action == "status":
            show_credential_status(env_file=args.env_file)
        elif args.cred_action == "sync-mcp":
            sync_mcp_credentials(mcp_file=args.mcp_file, env_file=args.env_file)
        else:
            cred_parser.print_help()

    # Backward compatibility: if no command specified, default to old behavior
    elif hasattr(args, "action"):
        if args.action == "show":
            show_current_key()
        elif args.action == "regenerate":
            regenerate_key()
        elif args.action == "status":
            show_auth_status()
    else:
        parser.print_help()
