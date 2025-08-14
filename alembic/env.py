import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Load environment variables from .env file
# Use explicit file path to ensure consistent loading across all environments
try:
    import os
    from pathlib import Path

    from dotenv import load_dotenv

    # Find project root (alembic/ is in project root) and load environment files
    # This makes loading independent of current working directory (fixes UVX issues)
    project_dir = Path(__file__).parent.parent

    # Load .env file (unified configuration)
    dotenv_path = project_dir / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path)
    # If .env doesn't exist, rely on system environment variables

except ImportError:
    pass  # dotenv not available, use system env vars

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import hive models for autogenerate support
from lib.models import Base

target_metadata = Base.metadata


# Get database URL from environment with comprehensive error handling
def get_url():
    db_url = os.getenv("HIVE_DATABASE_URL")
    if not db_url:
        # Comprehensive error message for UVX debugging
        raise ValueError(
            "HIVE_DATABASE_URL environment variable must be set. "
            "This error often occurs in UVX environments when .env files cannot be found. "
            "Ensure your .env file is properly configured or set HIVE_DATABASE_URL as a system environment variable."
        )

    # Convert psycopg:// to postgresql+psycopg:// for SQLAlchemy async
    # FIXED: Remove redundant replacement for postgresql+psycopg://
    if db_url.startswith("postgresql://"):
        return db_url.replace("postgresql://", "postgresql+psycopg://")
    return db_url


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="hive",  # Store alembic version table in hive schema
        include_schemas=True,  # Include schema in generated SQL
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema="hive",  # Store alembic version table in hive schema
        include_schemas=True,  # Include schema in generated SQL
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Override config with environment URL
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Create hive schema if it doesn't exist
        await connection.execute(text("CREATE SCHEMA IF NOT EXISTS hive"))
        await connection.commit()

        # Run migrations
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
