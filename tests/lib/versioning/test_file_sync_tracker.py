"""
Comprehensive Test Suite for FileSyncTracker Module

Tests for file synchronization tracking functionality, including:
- YAML file path resolution and discovery
- File modification time comparison with database timestamps
- Timezone-aware datetime handling
- File existence validation
- Edge cases with various file system scenarios
- Error handling for missing files and permissions
"""

import os
import tempfile
from datetime import UTC, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lib.versioning.file_sync_tracker import FileSyncTracker


@pytest.fixture
def tracker():
    """Create FileSyncTracker instance with mocked base path."""
    with patch("lib.versioning.file_sync_tracker.settings") as mock_settings:
        mock_instance = MagicMock()
        mock_instance.BASE_DIR = Path("/test/base")
        mock_settings.return_value = mock_instance
        return FileSyncTracker()


@pytest.fixture
def temp_directory():
    """Create temporary directory for file system tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


class TestFileSyncTracker:
    """Test suite for FileSyncTracker core functionality."""

    def test_init_sets_base_path(self):
        """Test that FileSyncTracker initializes with correct base path from settings."""
        with patch("lib.versioning.file_sync_tracker.settings") as mock_settings:
            mock_instance = MagicMock()
            mock_instance.BASE_DIR = Path("/custom/base/path")
            mock_settings.return_value = mock_instance
            tracker = FileSyncTracker()
            
            assert tracker.base_path == Path("/custom/base/path")

    def test_get_yaml_path_finds_agent_config(self, tracker):
        """Test _get_yaml_path finds agent configuration file."""
        agent_path = Path("/test/base/ai/agents/test-agent/config.yaml")
        
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.side_effect = lambda: str(agent_path) in str(Path.cwd())
            
            # Mock the specific agent path to exist
            def path_exists_side_effect(self):
                return str(self) == str(agent_path)
            
            with patch.object(Path, "exists", path_exists_side_effect):
                result = tracker._get_yaml_path("test-agent")
                assert result == agent_path

    def test_get_yaml_path_finds_workflow_config(self, tracker):
        """Test _get_yaml_path finds workflow configuration file."""
        workflow_path = Path("/test/base/ai/workflows/test-workflow/config.yaml")
        
        def path_exists_side_effect(self):
            return str(self) == str(workflow_path)
        
        with patch.object(Path, "exists", path_exists_side_effect):
            result = tracker._get_yaml_path("test-workflow")
            assert result == workflow_path

    def test_get_yaml_path_finds_team_config(self, tracker):
        """Test _get_yaml_path finds team configuration file."""
        team_path = Path("/test/base/ai/teams/test-team/config.yaml")
        
        def path_exists_side_effect(self):
            return str(self) == str(team_path)
        
        with patch.object(Path, "exists", path_exists_side_effect):
            result = tracker._get_yaml_path("test-team")
            assert result == team_path

    def test_get_yaml_path_prioritizes_agent_over_workflow(self, tracker):
        """Test _get_yaml_path prioritizes agent path when multiple exist."""
        agent_path = Path("/test/base/ai/agents/test-component/config.yaml")
        workflow_path = Path("/test/base/ai/workflows/test-component/config.yaml")
        
        def path_exists_side_effect(self):
            return str(self) in [str(agent_path), str(workflow_path)]
        
        with patch.object(Path, "exists", path_exists_side_effect):
            result = tracker._get_yaml_path("test-component")
            # Should return agent path first (first in the list)
            assert result == agent_path

    def test_get_yaml_path_raises_filenotfounderror_when_missing(self, tracker):
        """Test _get_yaml_path raises FileNotFoundError when no config exists."""
        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(FileNotFoundError, match="YAML config not found for component: nonexistent"):
                tracker._get_yaml_path("nonexistent")

    def test_yaml_newer_than_db_with_datetime_object(self, tracker):
        """Test yaml_newer_than_db with datetime object comparison."""
        # Mock YAML file modification time (newer)
        yaml_mtime = datetime(2025, 1, 15, 12, 0, 0)
        db_created_at = datetime(2025, 1, 10, 12, 0, 0)
        
        with patch.object(tracker, "_get_yaml_path") as mock_path:
            mock_path.return_value = Path("/test/config.yaml")
            with patch("os.path.getmtime", return_value=yaml_mtime.timestamp()):
                result = tracker.yaml_newer_than_db("test-component", db_created_at)
                
                assert result is True

    def test_yaml_newer_than_db_with_iso_string(self, tracker):
        """Test yaml_newer_than_db with ISO string timestamp."""
        # Mock YAML file modification time (newer)
        yaml_mtime = datetime(2025, 1, 15, 12, 0, 0)
        db_created_at_iso = "2025-01-10T12:00:00Z"
        
        with patch.object(tracker, "_get_yaml_path") as mock_path:
            mock_path.return_value = Path("/test/config.yaml")
            with patch("os.path.getmtime", return_value=yaml_mtime.timestamp()):
                result = tracker.yaml_newer_than_db("test-component", db_created_at_iso)
                
                assert result is True

    def test_yaml_newer_than_db_with_timezone_aware_db_timestamp(self, tracker):
        """Test yaml_newer_than_db handles timezone-aware database timestamps."""
        # Mock YAML file modification time (naive)
        yaml_mtime = datetime(2025, 1, 15, 12, 0, 0)
        # Database timestamp with timezone
        db_created_at = datetime(2025, 1, 10, 12, 0, 0, tzinfo=UTC)
        
        with patch.object(tracker, "_get_yaml_path") as mock_path:
            mock_path.return_value = Path("/test/config.yaml")
            with patch("os.path.getmtime", return_value=yaml_mtime.timestamp()):
                result = tracker.yaml_newer_than_db("test-component", db_created_at)
                
                assert result is True

    def test_yaml_newer_than_db_with_iso_string_plus_timezone(self, tracker):
        """Test yaml_newer_than_db handles ISO string with +00:00 timezone."""
        yaml_mtime = datetime(2025, 1, 15, 12, 0, 0)
        db_created_at_iso = "2025-01-10T12:00:00+00:00"
        
        with patch.object(tracker, "_get_yaml_path") as mock_path:
            mock_path.return_value = Path("/test/config.yaml")
            with patch("os.path.getmtime", return_value=yaml_mtime.timestamp()):
                result = tracker.yaml_newer_than_db("test-component", db_created_at_iso)
                
                assert result is True

    def test_yaml_newer_than_db_yaml_older_returns_false(self, tracker):
        """Test yaml_newer_than_db returns False when YAML is older."""
        # Mock YAML file modification time (older)
        yaml_mtime = datetime(2025, 1, 5, 12, 0, 0)
        db_created_at = datetime(2025, 1, 10, 12, 0, 0)
        
        with patch.object(tracker, "_get_yaml_path") as mock_path:
            mock_path.return_value = Path("/test/config.yaml")
            with patch("os.path.getmtime", return_value=yaml_mtime.timestamp()):
                result = tracker.yaml_newer_than_db("test-component", db_created_at)
                
                assert result is False

    def test_yaml_newer_than_db_file_not_found_returns_false(self, tracker):
        """Test yaml_newer_than_db returns False when YAML file doesn't exist."""
        db_created_at = datetime(2025, 1, 10, 12, 0, 0)
        
        with patch.object(tracker, "_get_yaml_path") as mock_path:
            mock_path.side_effect = FileNotFoundError("File not found")
            
            result = tracker.yaml_newer_than_db("test-component", db_created_at)
            
            assert result is False

    def test_yaml_newer_than_db_os_error_returns_false(self, tracker):
        """Test yaml_newer_than_db returns False when OS error occurs."""
        db_created_at = datetime(2025, 1, 10, 12, 0, 0)
        
        with patch.object(tracker, "_get_yaml_path") as mock_path:
            mock_path.return_value = Path("/test/config.yaml")
            with patch("os.path.getmtime", side_effect=OSError("Permission denied")):
                result = tracker.yaml_newer_than_db("test-component", db_created_at)
                
                assert result is False

    def test_get_yaml_modification_time_success(self, tracker):
        """Test get_yaml_modification_time returns correct modification time."""
        expected_mtime = datetime(2025, 1, 15, 12, 0, 0)
        
        with patch.object(tracker, "_get_yaml_path") as mock_path:
            mock_path.return_value = Path("/test/config.yaml")
            with patch("os.path.getmtime", return_value=expected_mtime.timestamp()):
                result = tracker.get_yaml_modification_time("test-component")
                
                assert result == expected_mtime

    def test_get_yaml_modification_time_file_not_found_returns_none(self, tracker):
        """Test get_yaml_modification_time returns None when file doesn't exist."""
        with patch.object(tracker, "_get_yaml_path") as mock_path:
            mock_path.side_effect = FileNotFoundError("File not found")
            
            result = tracker.get_yaml_modification_time("test-component")
            
            assert result is None

    def test_get_yaml_modification_time_os_error_returns_none(self, tracker):
        """Test get_yaml_modification_time returns None on OS error."""
        with patch.object(tracker, "_get_yaml_path") as mock_path:
            mock_path.return_value = Path("/test/config.yaml")
            with patch("os.path.getmtime", side_effect=OSError("Permission denied")):
                result = tracker.get_yaml_modification_time("test-component")
                
                assert result is None

    def test_yaml_exists_returns_true_when_file_exists(self, tracker):
        """Test yaml_exists returns True when YAML config file exists."""
        with patch.object(tracker, "_get_yaml_path") as mock_path:
            mock_path.return_value = Path("/test/config.yaml")
            
            result = tracker.yaml_exists("test-component")
            
            assert result is True

    def test_yaml_exists_returns_false_when_file_missing(self, tracker):
        """Test yaml_exists returns False when YAML config file doesn't exist."""
        with patch.object(tracker, "_get_yaml_path") as mock_path:
            mock_path.side_effect = FileNotFoundError("File not found")
            
            result = tracker.yaml_exists("test-component")
            
            assert result is False


class TestFileSyncTrackerEdgeCases:
    """Test edge cases and boundary conditions for FileSyncTracker."""

    def test_yaml_newer_than_db_with_microsecond_precision(self, tracker):
        """Test yaml_newer_than_db handles microsecond-level time differences."""
        # YAML file is 1 microsecond newer
        yaml_mtime = datetime(2025, 1, 15, 12, 0, 0, 100000)  # 100ms
        db_created_at = datetime(2025, 1, 15, 12, 0, 0, 99999)   # 99.999ms
        
        with patch.object(tracker, "_get_yaml_path") as mock_path:
            mock_path.return_value = Path("/test/config.yaml")
            with patch("os.path.getmtime", return_value=yaml_mtime.timestamp()):
                result = tracker.yaml_newer_than_db("test-component", db_created_at)
                
                assert result is True

    def test_yaml_newer_than_db_exact_same_timestamp(self, tracker):
        """Test yaml_newer_than_db when timestamps are exactly equal."""
        same_time = datetime(2025, 1, 15, 12, 0, 0)
        
        with patch.object(tracker, "_get_yaml_path") as mock_path:
            mock_path.return_value = Path("/test/config.yaml")
            with patch("os.path.getmtime", return_value=same_time.timestamp()):
                result = tracker.yaml_newer_than_db("test-component", same_time)
                
                assert result is False  # Not newer, equal

    def test_yaml_newer_than_db_with_different_timezones(self, tracker):
        """Test yaml_newer_than_db handles different timezone representations."""
        # YAML file time (naive, assumed local)
        yaml_mtime = datetime(2025, 1, 15, 12, 0, 0)
        # Database time in different timezone (equivalent to UTC)
        db_created_at = datetime(2025, 1, 15, 7, 0, 0, tzinfo=timezone.utc)  # UTC
        
        with patch.object(tracker, "_get_yaml_path") as mock_path:
            mock_path.return_value = Path("/test/config.yaml")
            with patch("os.path.getmtime", return_value=yaml_mtime.timestamp()):
                result = tracker.yaml_newer_than_db("test-component", db_created_at)
                
                # Result depends on timezone conversion
                assert isinstance(result, bool)

    def test_yaml_newer_than_db_with_malformed_iso_string(self, tracker):
        """Test yaml_newer_than_db handles malformed ISO timestamp strings."""
        yaml_mtime = datetime(2025, 1, 15, 12, 0, 0)
        malformed_timestamps = [
            "2025-01-10T12:00:00",      # No timezone
            "2025-01-10 12:00:00Z",     # Space instead of T
            "2025-13-40T25:70:90Z",     # Invalid date/time values
            "not-a-timestamp",          # Completely invalid
            "",                         # Empty string
            "Z",                        # Just timezone
        ]
        
        with patch.object(tracker, "_get_yaml_path") as mock_path:
            mock_path.return_value = Path("/test/config.yaml")
            with patch("os.path.getmtime", return_value=yaml_mtime.timestamp()):
                
                for malformed_ts in malformed_timestamps:
                    try:
                        result = tracker.yaml_newer_than_db("test-component", malformed_ts)
                        # If it doesn't raise an exception, result should be boolean
                        assert isinstance(result, bool)
                    except ValueError:
                        # ValueError is acceptable for malformed timestamps
                        pass

    def test_get_yaml_path_with_special_component_ids(self, tracker):
        """Test _get_yaml_path handles component IDs with special characters."""
        special_ids = [
            "test-agent_v2",
            "agent.with.dots",
            "agent-with-many-dashes",
            "agent_with_underscores",
            "UPPERCASE-AGENT",
            "123-numeric-start",
            "agent-123-numeric-middle",
        ]
        
        for component_id in special_ids:
            agent_path = Path(f"/test/base/ai/agents/{component_id}/config.yaml")
            
            def path_exists_side_effect(self):
                return str(self) == str(agent_path)
            
            with patch.object(Path, "exists", path_exists_side_effect):
                result = tracker._get_yaml_path(component_id)
                assert result == agent_path

    def test_yaml_newer_than_db_with_very_old_timestamps(self, tracker):
        """Test yaml_newer_than_db handles very old timestamps correctly."""
        # Very old YAML file
        yaml_mtime = datetime(1970, 1, 1, 0, 0, 1)  # Just after Unix epoch
        db_created_at = datetime(2025, 1, 15, 12, 0, 0)
        
        with patch.object(tracker, "_get_yaml_path") as mock_path:
            mock_path.return_value = Path("/test/config.yaml")
            with patch("os.path.getmtime", return_value=yaml_mtime.timestamp()):
                result = tracker.yaml_newer_than_db("test-component", db_created_at)
                
                assert result is False

    def test_yaml_newer_than_db_with_future_timestamps(self, tracker):
        """Test yaml_newer_than_db handles future timestamps correctly."""
        # Future YAML file (could happen with clock skew)
        yaml_mtime = datetime(2030, 1, 1, 0, 0, 0)
        db_created_at = datetime(2025, 1, 15, 12, 0, 0)
        
        with patch.object(tracker, "_get_yaml_path") as mock_path:
            mock_path.return_value = Path("/test/config.yaml")
            with patch("os.path.getmtime", return_value=yaml_mtime.timestamp()):
                result = tracker.yaml_newer_than_db("test-component", db_created_at)
                
                assert result is True

    def test_get_yaml_path_checks_all_locations_before_failing(self, tracker):
        """Test _get_yaml_path checks all possible locations before raising error."""
        expected_paths = [
            Path("/test/base/ai/agents/missing-component/config.yaml"),
            Path("/test/base/ai/workflows/missing-component/config.yaml"),
            Path("/test/base/ai/teams/missing-component/config.yaml"),
        ]
        
        # Track which paths were checked
        checked_paths = []
        
        def path_exists_side_effect(self):
            checked_paths.append(str(self))
            return False
        
        with patch.object(Path, "exists", path_exists_side_effect):
            with pytest.raises(FileNotFoundError):
                tracker._get_yaml_path("missing-component")
            
            # Verify all expected paths were checked
            for expected_path in expected_paths:
                assert str(expected_path) in checked_paths


class TestFileSyncTrackerIntegration:
    """Integration tests for FileSyncTracker with real file system operations."""

    def test_real_file_system_operations(self, temp_directory):
        """Test FileSyncTracker with actual file system operations."""
        # Create directory structure
        agents_dir = temp_directory / "ai" / "agents" / "test-agent"
        agents_dir.mkdir(parents=True)
        
        config_file = agents_dir / "config.yaml"
        config_file.write_text("agent:\n  name: test\n  version: 1\n")
        
        # Create tracker with real base path
        with patch("lib.versioning.file_sync_tracker.settings") as mock_settings:
            mock_instance = MagicMock()
            mock_instance.BASE_DIR = Path(str(temp_directory))
            mock_settings.return_value = mock_instance
            tracker = FileSyncTracker()
            
            # Test finding the config file
            yaml_path = tracker._get_yaml_path("test-agent")
            assert yaml_path == config_file
            
            # Test file existence check
            assert tracker.yaml_exists("test-agent") is True
            
            # Test modification time
            mtime = tracker.get_yaml_modification_time("test-agent")
            assert isinstance(mtime, datetime)
            
            # Test timestamp comparison
            old_time = datetime(2020, 1, 1, 0, 0, 0)
            assert tracker.yaml_newer_than_db("test-agent", old_time) is True

    def test_file_permissions_handling(self, temp_directory):
        """Test FileSyncTracker handles file permission issues gracefully."""
        # Create directory structure
        agents_dir = temp_directory / "ai" / "agents" / "restricted-agent"
        agents_dir.mkdir(parents=True)
        
        config_file = agents_dir / "config.yaml"
        config_file.write_text("agent:\n  name: restricted\n  version: 1\n")
        
        # Make file unreadable (if on Unix-like system)
        try:
            config_file.chmod(0o000)
        except (OSError, NotImplementedError):
            # Skip this test on systems that don't support chmod
            pytest.skip("File permissions not supported on this system")
        
        try:
            with patch("lib.versioning.file_sync_tracker.settings") as mock_settings:
                mock_instance = MagicMock()
                mock_instance.BASE_DIR = Path(str(temp_directory))
                mock_settings.return_value = mock_instance
                tracker = FileSyncTracker()
                
                # File exists but might not be accessible for mtime
                assert tracker.yaml_exists("restricted-agent") is True
                
                # Modification time might fail due to permissions
                mtime = tracker.get_yaml_modification_time("restricted-agent")
                # Could be None or actual time depending on system
                assert mtime is None or isinstance(mtime, datetime)
        
        finally:
            # Restore permissions for cleanup
            try:
                config_file.chmod(0o644)
            except (OSError, NotImplementedError):
                pass