"""Tests for lib.utils.ai_root module.

Tests the AI root resolution functionality with TDD methodology.
"""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from lib.config.settings import HiveSettings


class TestResolveAiRoot:
    """Test resolve_ai_root function."""

    def test_resolve_ai_root_with_explicit_path(self, tmp_path):
        """Test resolve_ai_root with explicit path argument."""
        from lib.utils.ai_root import resolve_ai_root

        # Create a mock AI directory structure
        ai_dir = tmp_path / "custom-ai"
        ai_dir.mkdir()
        (ai_dir / "agents").mkdir()
        (ai_dir / "teams").mkdir()
        (ai_dir / "workflows").mkdir()

        # Mock settings
        mock_settings = Mock(spec=HiveSettings)
        mock_settings.hive_ai_root = "ai"

        result = resolve_ai_root(str(ai_dir), mock_settings)

        assert result == ai_dir
        assert result.exists()

    def test_resolve_ai_root_with_hive_ai_root_env_var(self, tmp_path):
        """Test resolve_ai_root with HIVE_AI_ROOT environment variable."""
        from lib.utils.ai_root import resolve_ai_root

        # Create a mock AI directory structure
        ai_dir = tmp_path / "env-ai"
        ai_dir.mkdir()
        (ai_dir / "agents").mkdir()
        (ai_dir / "teams").mkdir()
        (ai_dir / "workflows").mkdir()

        # Mock settings
        mock_settings = Mock(spec=HiveSettings)
        mock_settings.hive_ai_root = "ai"

        with patch.dict(os.environ, {"HIVE_AI_ROOT": str(ai_dir)}):
            result = resolve_ai_root(None, mock_settings)

        assert result == ai_dir
        assert result.exists()

    def test_resolve_ai_root_with_settings_default(self, tmp_path):
        """Test resolve_ai_root with settings default value."""
        from lib.utils.ai_root import resolve_ai_root

        # Create the default AI directory structure
        ai_dir = tmp_path / "ai"
        ai_dir.mkdir()
        (ai_dir / "agents").mkdir()
        (ai_dir / "teams").mkdir()
        (ai_dir / "workflows").mkdir()

        # Mock settings
        mock_settings = Mock(spec=HiveSettings)
        mock_settings.hive_ai_root = "ai"

        with patch("lib.utils.ai_root.Path.cwd", return_value=tmp_path):
            result = resolve_ai_root(None, mock_settings)

        assert result == ai_dir
        assert result.exists()

    def test_resolve_ai_root_precedence_explicit_over_env(self, tmp_path):
        """Test that explicit path takes precedence over environment variable."""
        from lib.utils.ai_root import resolve_ai_root

        # Create two different AI directory structures
        explicit_dir = tmp_path / "explicit-ai"
        explicit_dir.mkdir()
        (explicit_dir / "agents").mkdir()
        (explicit_dir / "teams").mkdir()
        (explicit_dir / "workflows").mkdir()

        env_dir = tmp_path / "env-ai"
        env_dir.mkdir()
        (env_dir / "agents").mkdir()
        (env_dir / "teams").mkdir()
        (env_dir / "workflows").mkdir()

        # Mock settings
        mock_settings = Mock(spec=HiveSettings)
        mock_settings.hive_ai_root = "ai"

        with patch.dict(os.environ, {"HIVE_AI_ROOT": str(env_dir)}):
            result = resolve_ai_root(str(explicit_dir), mock_settings)

        assert result == explicit_dir
        assert result != env_dir

    def test_resolve_ai_root_precedence_env_over_settings(self, tmp_path):
        """Test that environment variable takes precedence over settings default."""
        from lib.utils.ai_root import resolve_ai_root

        # Create AI directory structure
        env_dir = tmp_path / "env-ai"
        env_dir.mkdir()
        (env_dir / "agents").mkdir()
        (env_dir / "teams").mkdir()
        (env_dir / "workflows").mkdir()

        # Mock settings
        mock_settings = Mock(spec=HiveSettings)
        mock_settings.hive_ai_root = "ai"

        with patch.dict(os.environ, {"HIVE_AI_ROOT": str(env_dir)}):
            result = resolve_ai_root(None, mock_settings)

        assert result == env_dir

    def test_resolve_ai_root_missing_directory_structure(self, tmp_path):
        """Test resolve_ai_root raises error when directory structure is missing."""
        from lib.utils.ai_root import resolve_ai_root

        # Create directory without required subdirectories
        ai_dir = tmp_path / "incomplete-ai"
        ai_dir.mkdir()
        # Missing agents/, teams/, workflows/ directories

        # Mock settings
        mock_settings = Mock(spec=HiveSettings)
        mock_settings.hive_ai_root = "ai"

        with pytest.raises(ValueError, match="AI root directory must contain"):
            resolve_ai_root(str(ai_dir), mock_settings)

    def test_resolve_ai_root_nonexistent_directory(self, tmp_path):
        """Test resolve_ai_root raises error when directory doesn't exist."""
        from lib.utils.ai_root import resolve_ai_root

        # Non-existent directory
        nonexistent_dir = tmp_path / "nonexistent-ai"

        # Mock settings
        mock_settings = Mock(spec=HiveSettings)
        mock_settings.hive_ai_root = "ai"

        with pytest.raises(FileNotFoundError):
            resolve_ai_root(str(nonexistent_dir), mock_settings)

    def test_resolve_ai_root_with_path_object(self, tmp_path):
        """Test resolve_ai_root works with Path objects."""
        from lib.utils.ai_root import resolve_ai_root

        # Create a mock AI directory structure
        ai_dir = tmp_path / "path-ai"
        ai_dir.mkdir()
        (ai_dir / "agents").mkdir()
        (ai_dir / "teams").mkdir()
        (ai_dir / "workflows").mkdir()

        # Mock settings
        mock_settings = Mock(spec=HiveSettings)
        mock_settings.hive_ai_root = "ai"

        result = resolve_ai_root(ai_dir, mock_settings)

        assert result == ai_dir
        assert result.exists()

    def test_resolve_ai_root_with_relative_path(self, tmp_path):
        """Test resolve_ai_root with relative path."""
        from lib.utils.ai_root import resolve_ai_root

        # Create a mock AI directory structure
        ai_dir = tmp_path / "relative-ai"
        ai_dir.mkdir()
        (ai_dir / "agents").mkdir()
        (ai_dir / "teams").mkdir()
        (ai_dir / "workflows").mkdir()

        # Change to parent directory
        original_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))

            # Mock settings
            mock_settings = Mock(spec=HiveSettings)
            mock_settings.hive_ai_root = "ai"

            result = resolve_ai_root("relative-ai", mock_settings)

            assert result == ai_dir.resolve()
            assert result.exists()
        finally:
            os.chdir(original_cwd)


class TestAiRootIntegration:
    """Integration tests for AI root functionality."""

    def test_resolve_ai_root_with_real_settings(self, tmp_path):
        """Test resolve_ai_root with real HiveSettings instance."""
        from lib.utils.ai_root import resolve_ai_root

        # Create a mock AI directory structure
        ai_dir = tmp_path / "ai"
        ai_dir.mkdir()
        (ai_dir / "agents").mkdir()
        (ai_dir / "teams").mkdir()
        (ai_dir / "workflows").mkdir()

        # Create minimal settings for testing
        required_env_vars = {
            "HIVE_ENVIRONMENT": "development",
            "HIVE_API_PORT": "8886",
            "HIVE_DATABASE_URL": "postgresql://localhost:5432/test",
            "HIVE_API_KEY": "hive_test_key_that_is_long_enough_32chars",
            "HIVE_CORS_ORIGINS": "http://localhost:3000",
        }

        with patch.dict(os.environ, required_env_vars, clear=True):
            settings = HiveSettings()
            settings.hive_ai_root = "ai"

            with patch("lib.utils.ai_root.Path.cwd", return_value=tmp_path):
                result = resolve_ai_root(None, settings)

            assert result == ai_dir
            assert result.exists()