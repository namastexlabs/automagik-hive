"""Tests for the FileSystemAdapter infrastructure layer.

This module tests file system operations including bypass flag management
and metrics collection functionality.
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.hooks.infrastructure.filesystem_adapter import FileSystemAdapter


class TestFileSystemAdapter:
    """Test suite for the FileSystemAdapter class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.adapter = FileSystemAdapter(self.test_dir)

        # Ensure hooks directory exists
        self.hooks_dir = Path(self.test_dir) / ".git" / "hooks"
        self.hooks_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_check_bypass_flag_not_exists(self):
        """Test check_bypass_flag returns False when no bypass file exists."""
        result = self.adapter.check_bypass_flag()
        assert result is False

    def test_create_bypass_flag_success(self):
        """Test successful creation of bypass flag."""
        reason = "Emergency deployment fix"
        duration = 2

        result = self.adapter.create_bypass_flag(reason, duration, "test_user")

        assert result is True
        assert self.adapter.bypass_file.exists()

        # Check file content
        with open(self.adapter.bypass_file) as f:
            content = f.read()

        assert reason in content
        assert "test_user" in content
        assert "2 hours" in content

    def test_check_bypass_flag_exists_valid(self):
        """Test check_bypass_flag returns True for valid bypass."""
        # Create a valid bypass flag
        self.adapter.create_bypass_flag("Test reason", 1, "test_user")

        result = self.adapter.check_bypass_flag()
        assert result is True

    def test_check_bypass_flag_expired(self):
        """Test check_bypass_flag removes expired bypass and returns False."""
        # Create bypass info with past expiration
        past_time = datetime.now() - timedelta(hours=2)
        expired_info = {
            "reason": "Test reason",
            "duration_hours": 1,
            "created_by": "test_user",
            "created_at": past_time.isoformat(),
            "expires_at": (past_time + timedelta(hours=1)).isoformat(),
        }

        # Write expired bypass file
        with open(self.adapter.bypass_file, "w") as f:
            f.write("# Expired bypass\n")
            f.write(json.dumps(expired_info, indent=2))

        result = self.adapter.check_bypass_flag()

        assert result is False
        assert not self.adapter.bypass_file.exists()  # Should be removed

    def test_remove_bypass_flag_success(self):
        """Test successful removal of bypass flag."""
        # Create bypass flag first
        self.adapter.create_bypass_flag("Test reason", 1)
        assert self.adapter.bypass_file.exists()

        result = self.adapter.remove_bypass_flag()

        assert result is True
        assert not self.adapter.bypass_file.exists()

    def test_remove_bypass_flag_not_exists(self):
        """Test removing non-existent bypass flag returns True."""
        result = self.adapter.remove_bypass_flag()
        assert result is True

    def test_get_bypass_info_valid(self):
        """Test get_bypass_info returns correct information."""
        reason = "Emergency fix"
        duration = 3
        user = "test_user"

        self.adapter.create_bypass_flag(reason, duration, user)

        info = self.adapter.get_bypass_info()

        assert info is not None
        assert info["reason"] == reason
        assert info["duration_hours"] == duration
        assert info["created_by"] == user
        assert "created_at" in info
        assert "expires_at" in info

    def test_get_bypass_info_not_exists(self):
        """Test get_bypass_info returns None when no bypass exists."""
        info = self.adapter.get_bypass_info()
        assert info is None

    def test_get_bypass_info_malformed(self):
        """Test get_bypass_info handles malformed bypass file."""
        # Create malformed bypass file
        with open(self.adapter.bypass_file, "w") as f:
            f.write("# Malformed file\n")
            f.write("invalid json content")

        info = self.adapter.get_bypass_info()
        assert info is None

    def test_get_project_root(self):
        """Test get_project_root returns correct path."""
        root = self.adapter.get_project_root()
        assert root == str(Path(self.test_dir).absolute())

    def test_ensure_directories_exist(self):
        """Test ensure_directories_exist creates required directories."""
        self.adapter.ensure_directories_exist()

        # Check that required directories exist
        expected_dirs = [
            Path(self.test_dir) / ".git" / "hooks",
            Path(self.test_dir) / "src" / "hooks" / "domain",
            Path(self.test_dir) / "src" / "hooks" / "application",
            Path(self.test_dir) / "src" / "hooks" / "infrastructure",
            Path(self.test_dir) / "tests" / "hooks",
        ]

        for directory in expected_dirs:
            assert directory.exists(), f"Directory {directory} was not created"

    def test_record_validation_metrics_new_file(self):
        """Test recording metrics to new file."""
        metrics = {
            "files_checked": 5,
            "blocked_count": 1,
            "bypass_used": False,
            "validation_result": "blocked",
        }

        self.adapter.record_validation_metrics(metrics)

        assert self.adapter.metrics_file.exists()

        with open(self.adapter.metrics_file) as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["files_checked"] == 5
        assert data[0]["blocked_count"] == 1
        assert "timestamp" in data[0]

    def test_record_validation_metrics_append(self):
        """Test appending metrics to existing file."""
        # Create initial metrics
        initial_metrics = [{"test": "data", "timestamp": "2023-01-01T00:00:00"}]
        with open(self.adapter.metrics_file, "w") as f:
            json.dump(initial_metrics, f)

        # Add new metrics
        new_metrics = {"files_checked": 3, "blocked_count": 0, "bypass_used": True}

        self.adapter.record_validation_metrics(new_metrics)

        with open(self.adapter.metrics_file) as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[0]["test"] == "data"  # Original data preserved
        assert data[1]["files_checked"] == 3  # New data added

    def test_record_validation_metrics_limit(self):
        """Test metrics file size limit (keeps last 1000 entries)."""
        # Create a large number of metrics entries
        large_metrics = [
            {"entry": i, "timestamp": "2023-01-01T00:00:00"} for i in range(1005)
        ]
        with open(self.adapter.metrics_file, "w") as f:
            json.dump(large_metrics, f)

        # Add one more entry
        self.adapter.record_validation_metrics({"new": "entry"})

        with open(self.adapter.metrics_file) as f:
            data = json.load(f)

        # Should keep only last 1000 entries plus the new one
        assert len(data) == 1000
        assert data[-1]["new"] == "entry"  # New entry is last
        assert data[0]["entry"] == 6  # First entry is from position 6 of original data

    def test_get_validation_metrics_no_file(self):
        """Test get_validation_metrics when no metrics file exists."""
        metrics = self.adapter.get_validation_metrics()

        assert metrics["total_validations"] == 0

    def test_get_validation_metrics_with_data(self):
        """Test get_validation_metrics with valid data."""
        # Create test metrics data
        base_time = datetime.now() - timedelta(days=3)
        test_data = []

        # Add metrics from different time periods
        for i in range(10):
            entry_time = base_time + timedelta(hours=i)
            test_data.append(
                {
                    "timestamp": entry_time.isoformat(),
                    "files_checked": i + 1,
                    "blocked_count": 1 if i % 3 == 0 else 0,
                    "bypass_used": i % 5 == 0,
                }
            )

        with open(self.adapter.metrics_file, "w") as f:
            json.dump(test_data, f)

        metrics = self.adapter.get_validation_metrics()

        assert metrics["total_validations"] == 10
        assert metrics["blocked_validations"] == 4  # Every 3rd entry
        assert metrics["bypassed_validations"] == 2  # Every 5th entry
        assert 0 <= metrics["success_rate"] <= 1
        assert metrics["avg_files_per_validation"] > 0

    def test_get_validation_metrics_date_filter(self):
        """Test get_validation_metrics filters by date range."""
        # Create test data with different timestamps
        old_time = datetime.now() - timedelta(days=10)
        recent_time = datetime.now() - timedelta(days=2)

        test_data = [
            {
                "timestamp": old_time.isoformat(),
                "files_checked": 1,
                "blocked_count": 0,
                "bypass_used": False,
            },
            {
                "timestamp": recent_time.isoformat(),
                "files_checked": 2,
                "blocked_count": 1,
                "bypass_used": False,
            },
        ]

        with open(self.adapter.metrics_file, "w") as f:
            json.dump(test_data, f)

        # Get metrics for last 7 days (should exclude the 10-day-old entry)
        metrics = self.adapter.get_validation_metrics(days=7)

        assert metrics["total_validations"] == 1
        assert metrics["avg_files_per_validation"] == 2.0

    def test_get_validation_metrics_malformed_data(self):
        """Test get_validation_metrics handles malformed data gracefully."""
        # Create file with malformed JSON
        with open(self.adapter.metrics_file, "w") as f:
            f.write("invalid json")

        metrics = self.adapter.get_validation_metrics()

        assert "error" in metrics
        assert metrics["total_validations"] == 0

    @patch("subprocess.run")
    def test_get_git_user_success(self, mock_run):
        """Test _get_git_user returns correct username."""
        mock_run.return_value = MagicMock(stdout="John Doe\n", returncode=0)

        user = self.adapter._get_git_user()

        assert user == "John Doe"
        mock_run.assert_called_once_with(
            ["git", "config", "user.name"],
            cwd=self.adapter.project_root,
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("subprocess.run")
    def test_get_git_user_failure(self, mock_run):
        """Test _get_git_user handles Git command failure."""
        mock_run.side_effect = Exception("Git error")

        user = self.adapter._get_git_user()

        assert user is None

    def test_is_bypass_expired_true(self):
        """Test _is_bypass_expired correctly identifies expired bypass."""
        past_time = datetime.now() - timedelta(hours=1)
        bypass_info = {"expires_at": past_time.isoformat()}

        result = self.adapter._is_bypass_expired(bypass_info)
        assert result is True

    def test_is_bypass_expired_false(self):
        """Test _is_bypass_expired correctly identifies valid bypass."""
        future_time = datetime.now() + timedelta(hours=1)
        bypass_info = {"expires_at": future_time.isoformat()}

        result = self.adapter._is_bypass_expired(bypass_info)
        assert result is False

    def test_is_bypass_expired_malformed(self):
        """Test _is_bypass_expired handles malformed expiration data."""
        bypass_info = {"expires_at": "invalid-date-format"}

        result = self.adapter._is_bypass_expired(bypass_info)
        assert result is True  # Treat malformed as expired

    def test_is_bypass_expired_missing_key(self):
        """Test _is_bypass_expired handles missing expires_at key."""
        bypass_info = {"reason": "test"}

        result = self.adapter._is_bypass_expired(bypass_info)
        assert result is True  # Treat missing key as expired
