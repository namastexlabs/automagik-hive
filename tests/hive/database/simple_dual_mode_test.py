"""
Simple Dual Mode Testing Script.

This script tests the dual mode functionality using fresh imports.

Run with:
    uv run python tests/hive/database/simple_dual_mode_test.py
"""

import os
import sys


def test_external_mode():
    """Test external PostgreSQL mode."""
    print("\n" + "=" * 60)
    print("TEST 1: External PostgreSQL Mode")
    print("=" * 60)

    # Set HIVE_DATABASE_URL
    test_url = "postgresql+psycopg://user:pass@localhost:5432/testdb"
    os.environ["HIVE_DATABASE_URL"] = test_url

    # Get fresh settings (Pydantic reads from env)
    from hive.config.settings import HiveSettings

    config = HiveSettings(_env_file=None)

    print(f"  HIVE_DATABASE_URL set to: {test_url}")
    print(f"  config.hive_database_url: {config.hive_database_url}")
    print(f"  config.use_embedded_postgres: {config.use_embedded_postgres}")
    print(f"  config.database_mode: {config.database_mode}")

    # Assertions
    assert config.hive_database_url == test_url, "Database URL mismatch"
    assert config.use_embedded_postgres is False, "Should NOT use embedded postgres"
    assert config.database_mode == "external", "Mode should be 'external'"

    print("\n  ALL ASSERTIONS PASSED")

    # Cleanup
    del os.environ["HIVE_DATABASE_URL"]


def test_embedded_mode():
    """Test embedded PostgreSQL mode."""
    print("\n" + "=" * 60)
    print("TEST 2: Embedded PostgreSQL Mode (Serverless)")
    print("=" * 60)

    # Ensure HIVE_DATABASE_URL is not set
    if "HIVE_DATABASE_URL" in os.environ:
        del os.environ["HIVE_DATABASE_URL"]

    # Get fresh settings
    from hive.config.settings import HiveSettings

    config = HiveSettings(_env_file=None)

    print(f"  HIVE_DATABASE_URL: {os.environ.get('HIVE_DATABASE_URL', 'NOT SET')}")
    print(f"  config.hive_database_url: {config.hive_database_url}")
    print(f"  config.use_embedded_postgres: {config.use_embedded_postgres}")
    print(f"  config.database_mode: {config.database_mode}")
    print(f"  config.hive_embedded_postgres_port: {config.hive_embedded_postgres_port}")
    print(f"  config.hive_embedded_postgres_data_dir: {config.hive_embedded_postgres_data_dir}")

    # Assertions
    assert config.hive_database_url is None, "Database URL should be None"
    assert config.use_embedded_postgres is True, "Should use embedded postgres"
    assert config.database_mode == "embedded", "Mode should be 'embedded'"
    assert config.hive_embedded_postgres_port == 5432, "Default port should be 5432"
    assert config.hive_embedded_postgres_data_dir is None, "Default data dir should be None"

    print("\n  ALL ASSERTIONS PASSED")


def test_custom_config():
    """Test embedded mode with custom configuration."""
    print("\n" + "=" * 60)
    print("TEST 3: Embedded Mode with Custom Config")
    print("=" * 60)

    # Set custom embedded postgres config
    os.environ["HIVE_EMBEDDED_POSTGRES_PORT"] = "15432"
    os.environ["HIVE_EMBEDDED_POSTGRES_DATA_DIR"] = "/tmp/custom-pgdata"  # noqa: S108

    # Ensure HIVE_DATABASE_URL is not set
    if "HIVE_DATABASE_URL" in os.environ:
        del os.environ["HIVE_DATABASE_URL"]

    # Get fresh settings
    from hive.config.settings import HiveSettings

    config = HiveSettings(_env_file=None)

    print(f"  HIVE_EMBEDDED_POSTGRES_PORT: {os.environ['HIVE_EMBEDDED_POSTGRES_PORT']}")
    print(f"  HIVE_EMBEDDED_POSTGRES_DATA_DIR: {os.environ['HIVE_EMBEDDED_POSTGRES_DATA_DIR']}")
    print(f"  config.hive_embedded_postgres_port: {config.hive_embedded_postgres_port}")
    print(f"  config.hive_embedded_postgres_data_dir: {config.hive_embedded_postgres_data_dir}")
    print(f"  config.use_embedded_postgres: {config.use_embedded_postgres}")
    print(f"  config.database_mode: {config.database_mode}")

    # Assertions
    assert config.hive_embedded_postgres_port == 15432, "Custom port not applied"
    assert str(config.hive_embedded_postgres_data_dir) == "/tmp/custom-pgdata", "Custom data dir not applied"  # noqa: S108
    assert config.use_embedded_postgres is True, "Should use embedded postgres"
    assert config.database_mode == "embedded", "Mode should be 'embedded'"

    print("\n  ALL ASSERTIONS PASSED")

    # Cleanup
    del os.environ["HIVE_EMBEDDED_POSTGRES_PORT"]
    del os.environ["HIVE_EMBEDDED_POSTGRES_DATA_DIR"]


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SERVERLESS MODE - DUAL MODE VALIDATION")
    print("=" * 60)

    try:
        test_external_mode()
        test_embedded_mode()
        test_custom_config()

        print("\n" + "=" * 60)
        print("SUCCESS - ALL TESTS PASSED")
        print("=" * 60)
        print("\nSummary:")
        print("  - External mode detection: WORKING")
        print("  - Embedded mode detection: WORKING")
        print("  - Custom configuration: WORKING")
        print("\nThe dual mode system is functioning correctly!")

        return 0

    except AssertionError as e:
        print(f"\nFAILURE: {e}")
        return 1
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
