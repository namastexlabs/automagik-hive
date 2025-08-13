"""Test database configuration using existing .env credentials."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Use existing database URL from .env, but modify for test database
TEST_DATABASE_URL = os.getenv("HIVE_DATABASE_URL", "sqlite:///test_hive.db")

# For PostgreSQL, change database name to include _test suffix
if TEST_DATABASE_URL.startswith("postgresql"):
    # Extract base URL and modify database name
    base_url = TEST_DATABASE_URL.rsplit("/", 1)[0]
    db_name = TEST_DATABASE_URL.rsplit("/", 1)[1]
    TEST_DATABASE_URL = f"{base_url}/{db_name}_test"

# Test configuration
TEST_CONFIG = {
    "database_url": TEST_DATABASE_URL,
    "test_data_sets": ["minimal", "comprehensive", "stress"],
    "mock_services": ["auth", "anthropic", "openai", "database"],
    "coverage_threshold": 80.0,
    "tier_targets": {
        "tier_1": 95.0,  # Mission critical
        "tier_2": 85.0,  # High impact
        "tier_3": 75.0,  # Moderate impact
        "tier_4": 60.0,  # Supportive
    },
}
