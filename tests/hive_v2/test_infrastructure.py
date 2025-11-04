"""Test Hive V2 infrastructure foundation."""

import sys
from importlib.metadata import version
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def test_hive_package_exists():
    """Test that hive package can be imported."""
    import hive

    # Version should match package metadata
    assert hive.__version__ is not None
    assert isinstance(hive.__version__, str)
    # In dev mode, version might be "dev" or actual version from pyproject.toml
    assert hive.__version__ in ("dev", version("automagik-hive"))


def test_config_settings_import():
    """Test that settings can be imported."""
    from hive.config import settings

    config = settings()
    assert config is not None
    assert hasattr(config, "hive_environment")


def test_cli_app_import():
    """Test that CLI app can be imported."""
    from hive.cli import app

    assert app is not None


def test_api_app_creation():
    """Test that API app can be created."""
    from hive.api import create_app

    app = create_app()
    assert app is not None
    assert app.title == "Hive V2 API"


def test_default_emojis_defined():
    """Test that CLI emojis are defined."""
    from hive.config.defaults import CLI_EMOJIS

    assert "success" in CLI_EMOJIS
    assert "error" in CLI_EMOJIS
    assert "rocket" in CLI_EMOJIS


def test_project_template_files_exist():
    """Test that project template files exist."""
    template_dir = project_root / "hive" / "scaffolder" / "templates" / "project"

    assert (template_dir / ".env.example").exists()
    assert (template_dir / "README.md").exists()
    assert (template_dir / "hive.yaml").exists()
    assert (template_dir / "ai" / "agents" / "examples" / "support-bot" / "config.yaml").exists()


def test_settings_validation():
    """Test settings validation."""
    from hive.config.settings import HiveSettings

    # Test default values
    settings = HiveSettings()
    assert settings.hive_environment == "development"
    assert settings.hive_api_port == 8886
    assert settings.is_development is True
    assert settings.is_production is False


def test_cors_origins_parsing():
    """Test CORS origins parsing."""
    from hive.config.settings import HiveSettings

    settings = HiveSettings(hive_cors_origins="http://localhost:3000,https://example.com")
    origins = settings.cors_origins_list
    assert len(origins) == 2
    assert "http://localhost:3000" in origins
    assert "https://example.com" in origins


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
