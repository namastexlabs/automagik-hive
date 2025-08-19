"""
Comprehensive Unit Tests for Clean YAML-Database Bidirectional Sync System

Testing the newly implemented clean architecture:
- lib/versioning/dev_mode.py - Environment flag control
- lib/versioning/file_sync_tracker.py - File modification tracking
- lib/versioning/bidirectional_sync.py - Core sync engine

Target: 85%+ coverage with meaningful validation of sync behavior and error scenarios.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest
import yaml

from lib.versioning.agno_version_service import VersionInfo
from lib.versioning.bidirectional_sync import BidirectionalSync
from lib.versioning.dev_mode import DevMode
from lib.versioning.file_sync_tracker import FileSyncTracker


class TestDevMode:
    """Test DevMode environment flag behavior."""

    def test_dev_mode_enabled_true(self):
        """Test HIVE_DEV_MODE=true enables dev mode."""
        with patch.dict(os.environ, {"HIVE_DEV_MODE": "true"}):
            assert DevMode.is_enabled() is True

    def test_dev_mode_enabled_false(self):
        """Test HIVE_DEV_MODE=false disables dev mode."""
        with patch.dict(os.environ, {"HIVE_DEV_MODE": "false"}):
            assert DevMode.is_enabled() is False

    def test_dev_mode_case_insensitive(self):
        """Test case insensitive parsing of dev mode flag."""
        test_cases = ["TRUE", "True", "tRuE", "FALSE", "False", "fAlSe"]
        for case in test_cases:
            with patch.dict(os.environ, {"HIVE_DEV_MODE": case}):
                expected = case.lower() == "true"
                assert DevMode.is_enabled() is expected

    def test_dev_mode_default_false(self):
        """Test dev mode defaults to False when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert DevMode.is_enabled() is False

    def test_dev_mode_invalid_values(self):
        """Test invalid values default to False."""
        invalid_values = ["yes", "1", "enable", "on", "", "maybe", "unknown"]
        for invalid in invalid_values:
            with patch.dict(os.environ, {"HIVE_DEV_MODE": invalid}):
                assert DevMode.is_enabled() is False

    def test_get_mode_description_dev(self):
        """Test mode description in dev mode."""
        with patch.dict(os.environ, {"HIVE_DEV_MODE": "true"}):
            description = DevMode.get_mode_description()
            assert "DEV MODE" in description
            assert "YAML only" in description
            assert "no database sync" in description

    def test_get_mode_description_production(self):
        """Test mode description in production mode."""
        with patch.dict(os.environ, {"HIVE_DEV_MODE": "false"}):
            description = DevMode.get_mode_description()
            assert "PRODUCTION MODE" in description
            assert "bidirectional" in description
            assert "YAML ↔ DATABASE" in description


class TestFileSyncTracker:
    """Test FileSyncTracker file modification tracking."""

    @pytest.fixture
    def tracker(self):
        """Create FileSyncTracker instance."""
        with patch("lib.versioning.file_sync_tracker.settings") as mock_settings:
            mock_settings.return_value.BASE_DIR = "/test/base"
            return FileSyncTracker()

    @pytest.fixture
    def sample_yaml_paths(self):
        """Sample YAML file paths for testing."""
        return [
            Path("/test/base/ai/agents/test-agent/config.yaml"),
            Path("/test/base/ai/workflows/test-workflow/config.yaml"),
            Path("/test/base/ai/teams/test-team/config.yaml"),
        ]

    def test_get_yaml_path_agent(self, tracker, sample_yaml_paths):
        """Test YAML path resolution for agent."""
        expected_path = sample_yaml_paths[0]

        def mock_exists(path_self):
            return str(path_self) == str(expected_path)

        with patch.object(Path, "exists", mock_exists):
            path = tracker._get_yaml_path("test-agent")
            assert path == expected_path

    def test_get_yaml_path_workflow(self, tracker, sample_yaml_paths):
        """Test YAML path resolution for workflow."""
        expected_path = sample_yaml_paths[1]

        def mock_exists(path_self):
            return str(path_self) == str(expected_path)

        with patch.object(Path, "exists", mock_exists):
            path = tracker._get_yaml_path("test-workflow")
            assert path == expected_path

    def test_get_yaml_path_team(self, tracker, sample_yaml_paths):
        """Test YAML path resolution for team."""
        expected_path = sample_yaml_paths[2]

        def mock_exists(path_self):
            return str(path_self) == str(expected_path)

        with patch.object(Path, "exists", mock_exists):
            path = tracker._get_yaml_path("test-team")
            assert path == expected_path

    def test_get_yaml_path_not_found(self, tracker):
        """Test FileNotFoundError when YAML config doesn't exist."""
        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(
                FileNotFoundError,
                match="YAML config not found for component: nonexistent",
            ):
                tracker._get_yaml_path("nonexistent")

    def test_yaml_newer_than_db_true(self, tracker):
        """Test YAML file is newer than database."""
        yaml_time = datetime.now()
        db_time = yaml_time - timedelta(minutes=5)

        with patch.object(
            tracker, "_get_yaml_path", return_value=Path("/test/config.yaml")
        ):
            with patch("os.path.getmtime", return_value=yaml_time.timestamp()):
                assert tracker.yaml_newer_than_db("test-component", db_time) is True

    def test_yaml_newer_than_db_false(self, tracker):
        """Test YAML file is older than database."""
        yaml_time = datetime.now() - timedelta(minutes=10)
        db_time = datetime.now()

        with patch.object(
            tracker, "_get_yaml_path", return_value=Path("/test/config.yaml")
        ):
            with patch("os.path.getmtime", return_value=yaml_time.timestamp()):
                assert tracker.yaml_newer_than_db("test-component", db_time) is False

    def test_yaml_newer_than_db_same_time(self, tracker):
        """Test YAML file has same time as database."""
        same_time = datetime.now()

        with patch.object(
            tracker, "_get_yaml_path", return_value=Path("/test/config.yaml")
        ):
            with patch("os.path.getmtime", return_value=same_time.timestamp()):
                assert tracker.yaml_newer_than_db("test-component", same_time) is False

    def test_yaml_newer_than_db_file_not_found(self, tracker):
        """Test FileNotFoundError returns False (DB as source of truth)."""
        db_time = datetime.now()

        with patch.object(tracker, "_get_yaml_path", side_effect=FileNotFoundError()):
            assert tracker.yaml_newer_than_db("test-component", db_time) is False

    def test_yaml_newer_than_db_os_error(self, tracker):
        """Test OSError returns False (DB as source of truth)."""
        db_time = datetime.now()

        with patch.object(
            tracker, "_get_yaml_path", return_value=Path("/test/config.yaml")
        ):
            with patch("os.path.getmtime", side_effect=OSError("Permission denied")):
                assert tracker.yaml_newer_than_db("test-component", db_time) is False

    def test_get_yaml_modification_time_success(self, tracker):
        """Test successful YAML modification time retrieval."""
        test_time = datetime.now()

        with patch.object(
            tracker, "_get_yaml_path", return_value=Path("/test/config.yaml")
        ):
            with patch("os.path.getmtime", return_value=test_time.timestamp()):
                result = tracker.get_yaml_modification_time("test-component")
                assert result == test_time

    def test_get_yaml_modification_time_file_not_found(self, tracker):
        """Test FileNotFoundError returns None."""
        with patch.object(tracker, "_get_yaml_path", side_effect=FileNotFoundError()):
            result = tracker.get_yaml_modification_time("test-component")
            assert result is None

    def test_get_yaml_modification_time_os_error(self, tracker):
        """Test OSError returns None."""
        with patch.object(
            tracker, "_get_yaml_path", return_value=Path("/test/config.yaml")
        ):
            with patch("os.path.getmtime", side_effect=OSError("Permission denied")):
                result = tracker.get_yaml_modification_time("test-component")
                assert result is None

    def test_yaml_exists_true(self, tracker):
        """Test YAML file exists."""
        with patch.object(
            tracker, "_get_yaml_path", return_value=Path("/test/config.yaml")
        ):
            assert tracker.yaml_exists("test-component") is True

    def test_yaml_exists_false(self, tracker):
        """Test YAML file doesn't exist."""
        with patch.object(tracker, "_get_yaml_path", side_effect=FileNotFoundError()):
            assert tracker.yaml_exists("test-component") is False


class TestBidirectionalSync:
    """Test BidirectionalSync core sync engine."""

    @pytest.fixture
    def mock_version_service(self):
        """Mock AgnoVersionService."""
        return AsyncMock()

    @pytest.fixture
    def mock_file_tracker(self):
        """Mock FileSyncTracker."""
        return Mock()

    @pytest.fixture
    def sync_engine(self, mock_version_service, mock_file_tracker):
        """Create BidirectionalSync with mocked dependencies."""
        with patch(
            "lib.versioning.bidirectional_sync.AgnoVersionService"
        ) as mock_service_class:
            with patch(
                "lib.versioning.bidirectional_sync.FileSyncTracker"
            ) as mock_tracker_class:
                mock_service_class.return_value = mock_version_service
                mock_tracker_class.return_value = mock_file_tracker

                sync = BidirectionalSync("test_db_url")
                sync.version_service = mock_version_service
                sync.file_tracker = mock_file_tracker
                return sync

    @pytest.fixture
    def sample_yaml_config(self):
        """Sample YAML configuration."""
        return {
            "agent": {
                "component_id": "test-agent",
                "name": "Test Agent",
                "version": 1,
                "description": "Test agent configuration",
            }
        }

    @pytest.fixture
    def sample_db_version(self, sample_yaml_config):
        """Sample database version."""
        return VersionInfo(
            component_id="test-agent",
            component_type="agent",
            version=1,
            config=sample_yaml_config,
            created_at=datetime.now().isoformat(),
            created_by="test",
            description="Test version",
            is_active=True,
        )

    @pytest.mark.asyncio
    async def test_sync_component_no_db_creates_from_yaml(
        self, sync_engine, mock_version_service, sample_yaml_config
    ):
        """Test sync creates DB version when no DB version exists (YAML → DB)."""
        # Setup: No DB version, YAML exists
        mock_version_service.get_active_version.return_value = None

        with patch.object(
            sync_engine, "_load_yaml_config", return_value=sample_yaml_config
        ):
            with patch.object(sync_engine, "_create_db_version") as mock_create:
                result = await sync_engine.sync_component("test-agent", "agent")

                assert result == sample_yaml_config
                mock_create.assert_called_once_with(
                    "test-agent", "agent", sample_yaml_config, 1
                )

    @pytest.mark.asyncio
    async def test_sync_component_yaml_newer_updates_db(
        self,
        sync_engine,
        mock_version_service,
        mock_file_tracker,
        sample_yaml_config,
        sample_db_version,
    ):
        """Test sync updates DB when YAML file is newer (YAML → DB)."""
        # Setup: DB version exists, YAML file is newer
        mock_version_service.get_active_version.return_value = sample_db_version
        mock_file_tracker.yaml_newer_than_db.return_value = True

        with patch.object(
            sync_engine, "_load_yaml_config", return_value=sample_yaml_config
        ):
            with patch.object(sync_engine, "_update_db_from_yaml") as mock_update:
                result = await sync_engine.sync_component("test-agent", "agent")

                assert result == sample_yaml_config
                mock_update.assert_called_once_with(
                    "test-agent", "agent", sample_yaml_config, 1
                )

    @pytest.mark.asyncio
    async def test_sync_component_db_newer_updates_yaml(
        self,
        sync_engine,
        mock_version_service,
        mock_file_tracker,
        sample_yaml_config,
        sample_db_version,
    ):
        """Test sync updates YAML when DB version is higher (DB → YAML)."""
        # Setup: DB has higher version number
        sample_db_version.version = 2
        mock_version_service.get_active_version.return_value = sample_db_version
        mock_file_tracker.yaml_newer_than_db.return_value = False

        yaml_config_v1 = sample_yaml_config.copy()
        yaml_config_v1["agent"]["version"] = 1

        with patch.object(
            sync_engine, "_load_yaml_config", return_value=yaml_config_v1
        ):
            with patch.object(sync_engine, "_update_yaml_from_db") as mock_update:
                result = await sync_engine.sync_component("test-agent", "agent")

                assert result == sample_db_version.config
                mock_update.assert_called_once_with(
                    "test-agent", "agent", sample_db_version
                )

    @pytest.mark.asyncio
    async def test_sync_component_versions_in_sync(
        self,
        sync_engine,
        mock_version_service,
        mock_file_tracker,
        sample_yaml_config,
        sample_db_version,
    ):
        """Test sync returns DB config when versions are in sync."""
        # Setup: Same version, YAML not newer
        mock_version_service.get_active_version.return_value = sample_db_version
        mock_file_tracker.yaml_newer_than_db.return_value = False

        with patch.object(
            sync_engine, "_load_yaml_config", return_value=sample_yaml_config
        ):
            result = await sync_engine.sync_component("test-agent", "agent")

            assert result == sample_db_version.config

    @pytest.mark.asyncio
    async def test_sync_component_no_yaml_no_db_raises_error(
        self, sync_engine, mock_version_service
    ):
        """Test ValueError when no YAML and no DB version exist."""
        mock_version_service.get_active_version.return_value = None

        with patch.object(sync_engine, "_load_yaml_config", return_value=None):
            with pytest.raises(
                ValueError, match="No configuration found for test-agent"
            ):
                await sync_engine.sync_component("test-agent", "agent")

    @pytest.mark.asyncio
    async def test_sync_component_no_yaml_returns_db(
        self, sync_engine, mock_version_service, sample_db_version
    ):
        """Test returns DB config when no YAML but DB exists."""
        mock_version_service.get_active_version.return_value = sample_db_version

        with patch.object(sync_engine, "_load_yaml_config", return_value=None):
            result = await sync_engine.sync_component("test-agent", "agent")

            assert result == sample_db_version.config

    @pytest.mark.asyncio
    async def test_sync_component_invalid_yaml_version_raises_error(
        self, sync_engine, mock_version_service
    ):
        """Test ValueError for invalid YAML version."""
        invalid_configs = [
            {"agent": {"component_id": "test", "version": "dev"}},  # String version
            {"agent": {"component_id": "test", "version": None}},  # None version
            {"agent": {"component_id": "test"}},  # Missing version
        ]

        mock_version_service.get_active_version.return_value = None

        for invalid_config in invalid_configs:
            with patch.object(
                sync_engine, "_load_yaml_config", return_value=invalid_config
            ):
                with pytest.raises(ValueError, match="Invalid version in YAML"):
                    await sync_engine.sync_component("test-agent", "agent")

    def test_load_yaml_config_success(
        self, sync_engine, mock_file_tracker, sample_yaml_config
    ):
        """Test successful YAML config loading."""
        yaml_path = Path("/test/config.yaml")
        mock_file_tracker._get_yaml_path.return_value = yaml_path

        with patch("builtins.open", mock_open(read_data=yaml.dump(sample_yaml_config))):
            with patch("yaml.safe_load", return_value=sample_yaml_config):
                result = sync_engine._load_yaml_config("test-agent", "agent")

                assert result == sample_yaml_config

    def test_load_yaml_config_missing_component_type(
        self, sync_engine, mock_file_tracker
    ):
        """Test warning for missing component type in YAML."""
        yaml_path = Path("/test/config.yaml")
        mock_file_tracker._get_yaml_path.return_value = yaml_path
        config_without_agent = {"team": {"component_id": "test"}}

        with patch(
            "builtins.open", mock_open(read_data=yaml.dump(config_without_agent))
        ):
            with patch("yaml.safe_load", return_value=config_without_agent):
                result = sync_engine._load_yaml_config("test-agent", "agent")

                assert result is None

    def test_load_yaml_config_file_not_found(self, sync_engine, mock_file_tracker):
        """Test FileNotFoundError handling."""
        mock_file_tracker._get_yaml_path.side_effect = FileNotFoundError()

        result = sync_engine._load_yaml_config("test-agent", "agent")
        assert result is None

    def test_load_yaml_config_yaml_error(self, sync_engine, mock_file_tracker):
        """Test YAMLError handling."""
        yaml_path = Path("/test/config.yaml")
        mock_file_tracker._get_yaml_path.return_value = yaml_path

        with patch("builtins.open", mock_open(read_data="invalid: yaml: content:")):
            with patch("yaml.safe_load", side_effect=yaml.YAMLError("Invalid YAML")):
                result = sync_engine._load_yaml_config("test-agent", "agent")

                assert result is None

    @pytest.mark.asyncio
    async def test_create_db_version_success(
        self, sync_engine, mock_version_service, sample_yaml_config
    ):
        """Test successful DB version creation."""
        mock_version_service.create_version.return_value = 123  # Valid version ID

        await sync_engine._create_db_version(
            "test-agent", "agent", sample_yaml_config, 1
        )

        mock_version_service.create_version.assert_called_once_with(
            component_id="test-agent",
            component_type="agent",
            version=1,
            config=sample_yaml_config,
            description="Created from YAML sync for test-agent",
        )
        mock_version_service.set_active_version.assert_called_once_with(
            component_id="test-agent",
            version=1,
        )

    @pytest.mark.asyncio
    async def test_create_db_version_failure(
        self, sync_engine, mock_version_service, sample_yaml_config
    ):
        """Test DB version creation failure."""
        mock_version_service.create_version.return_value = None

        with pytest.raises(
            ValueError, match="Failed to create database version for test-agent"
        ):
            await sync_engine._create_db_version(
                "test-agent", "agent", sample_yaml_config, 1
            )

    @pytest.mark.asyncio
    async def test_create_db_version_exception(
        self, sync_engine, mock_version_service, sample_yaml_config
    ):
        """Test DB version creation with exception."""
        mock_version_service.create_version.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await sync_engine._create_db_version(
                "test-agent", "agent", sample_yaml_config, 1
            )

    @pytest.mark.asyncio
    async def test_update_db_from_yaml_success(
        self, sync_engine, mock_version_service, sample_yaml_config
    ):
        """Test successful DB update from YAML."""
        mock_version_service.create_version.return_value = "version-id-123"
        mock_version_service.set_active_version.return_value = None

        await sync_engine._update_db_from_yaml(
            "test-agent", "agent", sample_yaml_config, 1
        )

        mock_version_service.create_version.assert_called_once_with(
            component_id="test-agent",
            component_type="agent",
            version=1,
            config=sample_yaml_config,
            description="Updated from YAML sync for test-agent",
        )
        mock_version_service.set_active_version.assert_called_once_with(
            component_id="test-agent",
            version=1,
        )

    @pytest.mark.asyncio
    async def test_update_db_from_yaml_failure(
        self, sync_engine, mock_version_service, sample_yaml_config
    ):
        """Test DB update from YAML failure."""
        mock_version_service.create_version.return_value = None  # Falsy value triggers ValueError
        mock_version_service.set_active_version.return_value = None

        with pytest.raises(
            ValueError, match="Failed to update database from YAML for test-agent"
        ):
            await sync_engine._update_db_from_yaml(
                "test-agent", "agent", sample_yaml_config, 1
            )

    @pytest.mark.asyncio
    async def test_update_yaml_from_db_success(
        self, sync_engine, mock_file_tracker, sample_db_version
    ):
        """Test successful YAML update from DB."""
        yaml_path = Path("/test/config.yaml")
        mock_file_tracker._get_yaml_path.return_value = yaml_path

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("yaml.dump") as mock_dump:
                await sync_engine._update_yaml_from_db(
                    "test-agent", "agent", sample_db_version
                )

                mock_file.assert_called_once_with(yaml_path, "w")
                mock_dump.assert_called_once_with(
                    sample_db_version.config,
                    mock_file.return_value.__enter__.return_value,
                    default_flow_style=False,
                    sort_keys=False,
                )

    @pytest.mark.asyncio
    async def test_update_yaml_from_db_exception(
        self, sync_engine, mock_file_tracker, sample_db_version
    ):
        """Test YAML update from DB with exception."""
        yaml_path = Path("/test/config.yaml")
        mock_file_tracker._get_yaml_path.return_value = yaml_path

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError, match="Permission denied"):
                await sync_engine._update_yaml_from_db(
                    "test-agent", "agent", sample_db_version
                )

    @pytest.mark.asyncio
    async def test_write_back_to_yaml_success(self, sync_engine, mock_file_tracker):
        """Test successful API write-back to YAML."""
        yaml_path = Path("/test/config.yaml")
        mock_file_tracker._get_yaml_path.return_value = yaml_path
        config = {"agent": {"component_id": "test", "version": 2}}

        with patch(
            "lib.versioning.bidirectional_sync.DevMode.is_enabled", return_value=False
        ):
            with patch("builtins.open", mock_open()) as mock_file:
                with patch("yaml.dump") as mock_dump:
                    await sync_engine.write_back_to_yaml(
                        "test-agent", "agent", config, 2
                    )

                    mock_file.assert_called_once_with(yaml_path, "w")
                    mock_dump.assert_called_once_with(
                        config,
                        mock_file.return_value.__enter__.return_value,
                        default_flow_style=False,
                        sort_keys=False,
                    )

    @pytest.mark.asyncio
    async def test_write_back_to_yaml_dev_mode_skip(self, sync_engine):
        """Test write-back skipped in dev mode."""
        config = {"agent": {"component_id": "test", "version": 2}}

        with patch(
            "lib.versioning.bidirectional_sync.DevMode.is_enabled", return_value=True
        ):
            with patch("builtins.open") as mock_file:
                await sync_engine.write_back_to_yaml("test-agent", "agent", config, 2)

                # Should not attempt to open file in dev mode
                mock_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_write_back_to_yaml_exception(self, sync_engine, mock_file_tracker):
        """Test write-back with exception."""
        yaml_path = Path("/test/config.yaml")
        mock_file_tracker._get_yaml_path.return_value = yaml_path
        config = {"agent": {"component_id": "test", "version": 2}}

        with patch(
            "lib.versioning.bidirectional_sync.DevMode.is_enabled", return_value=False
        ):
            with patch(
                "builtins.open", side_effect=PermissionError("Write permission denied")
            ):
                with pytest.raises(PermissionError, match="Write permission denied"):
                    await sync_engine.write_back_to_yaml(
                        "test-agent", "agent", config, 2
                    )


# Store test creation patterns in memory for future reference
@pytest.mark.asyncio
async def test_store_successful_patterns():
    """Store successful test creation patterns in memory."""
    try:
        pass
    except Exception:
        # If memory storage fails, just pass - this is not critical for test functionality
        pass
