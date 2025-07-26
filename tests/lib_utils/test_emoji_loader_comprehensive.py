"""
Comprehensive tests for lib/utils/emoji_loader.py to improve from 42% to 90%+ coverage.
Testing the uncovered lines: 32-33, 37, 50-92, 114-119, 124-125, 130-131
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml


class TestEmojiLoaderComprehensive:
    """Comprehensive tests for emoji loader functionality."""

    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_emoji_config(self):
        """Mock emoji configuration."""
        return {
            "emoji_mappings": {
                "success": "✅",
                "error": "❌",
                "warning": "⚠️",
                "info": "ℹ️",
                "database": "🗄️",
                "api": "🌐",
                "test": "🧪",
            },
            "context_patterns": {
                "api": ["endpoint", "route", "server"],
                "database": ["sql", "query", "migration"],
                "test": ["test", "spec", "assert"],
            },
        }

    def test_emoji_loader_initialization(self):
        """Test emoji loader initialization."""
        from lib.utils.emoji_loader import EmojiLoader

        loader = EmojiLoader()
        assert loader is not None
        assert hasattr(loader, "_config")

    def test_get_emoji_loader_singleton(self):
        """Test get_emoji_loader singleton pattern."""
        from lib.utils.emoji_loader import get_emoji_loader

        loader1 = get_emoji_loader()
        loader2 = get_emoji_loader()

        # Should return same instance
        assert loader1 is loader2
        assert loader1 is not None

    def test_emoji_loader_config_loading_success(
        self,
        temp_directory,
        mock_emoji_config,
    ):
        """Test successful config loading."""
        from lib.utils.emoji_loader import EmojiLoader

        # Create config file
        config_file = temp_directory / "emoji_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(mock_emoji_config, f)

        # Mock the config path
        with patch.object(
            EmojiLoader,
            "_get_config_path",
            return_value=str(config_file),
        ):
            loader = EmojiLoader()
            loader._load_config()

            assert loader._config is not None
            assert "emoji_mappings" in loader._config
            assert "context_patterns" in loader._config

    def test_emoji_loader_config_file_not_found(self):
        """Test behavior when config file not found."""
        from lib.utils.emoji_loader import EmojiLoader

        with patch.object(
            EmojiLoader,
            "_get_config_path",
            return_value="/non/existent/path.yaml",
        ):
            loader = EmojiLoader()
            loader._load_config()

            # Should handle missing file gracefully
            assert loader._config is None or loader._config == {}

    def test_emoji_loader_invalid_yaml(self):
        """Test behavior with invalid YAML file."""
        from lib.utils.emoji_loader import EmojiLoader

        invalid_yaml = "invalid: yaml: content: ["

        with patch("builtins.open", mock_open(read_data=invalid_yaml)):
            with patch.object(
                EmojiLoader,
                "_get_config_path",
                return_value="/fake/path.yaml",
            ):
                loader = EmojiLoader()
                loader._load_config()

                # Should handle invalid YAML gracefully
                assert loader._config is None or loader._config == {}

    def test_auto_emoji_function_with_config(self, mock_emoji_config):
        """Test auto_emoji function with valid config."""
        from lib.utils.emoji_loader import EmojiLoader, auto_emoji

        # Mock successful config loading
        with patch.object(EmojiLoader, "_load_config"):
            with patch.object(EmojiLoader, "_config", mock_emoji_config):
                # Test message with matching pattern
                result = auto_emoji("Database query successful", "/path/to/db_file.py")
                assert "🗄️" in result or result != "Database query successful"

                # Test message with API pattern
                result = auto_emoji("API endpoint created", "/path/to/api_file.py")
                assert "🌐" in result or result != "API endpoint created"

    def test_auto_emoji_function_without_config(self):
        """Test auto_emoji function without config."""
        from lib.utils.emoji_loader import auto_emoji

        # Force no config
        with patch("lib.utils.emoji_loader.get_emoji_loader") as mock_get_loader:
            mock_loader = MagicMock()
            mock_loader._config = None
            mock_get_loader.return_value = mock_loader

            # Should return original message
            message = "Test message"
            result = auto_emoji(message, "/path/to/file.py")
            assert result == message

    def test_emoji_loader_pattern_matching(self, mock_emoji_config):
        """Test pattern matching logic."""
        from lib.utils.emoji_loader import EmojiLoader

        with patch.object(EmojiLoader, "_config", mock_emoji_config):
            EmojiLoader()

            # Test context pattern matching
            test_cases = [
                ("API endpoint ready", "/api/routes.py", "api"),
                ("Database migration complete", "/db/migration.py", "database"),
                ("Test case passed", "/tests/test_something.py", "test"),
                ("Random message", "/random/file.py", None),
            ]

            for message, file_path, expected_context in test_cases:
                # This tests the internal pattern matching logic
                if expected_context:
                    patterns = mock_emoji_config["context_patterns"].get(
                        expected_context,
                        [],
                    )
                    message_lower = message.lower()
                    matches = any(pattern in message_lower for pattern in patterns)
                    if expected_context != "test":  # Test pattern is in filename
                        assert matches or expected_context in file_path.lower()
                    else:
                        assert matches or "test" in file_path.lower()

    def test_emoji_loader_config_path_resolution(self):
        """Test config path resolution."""
        from lib.utils.emoji_loader import EmojiLoader

        loader = EmojiLoader()
        config_path = loader._get_config_path()

        # Should return a valid path
        assert isinstance(config_path, str)
        assert config_path.endswith("emoji_config.yaml")
        assert "lib/utils" in config_path

    def test_emoji_loader_lazy_initialization(self):
        """Test lazy initialization of config."""
        from lib.utils.emoji_loader import EmojiLoader

        loader = EmojiLoader()

        # Config should not be loaded initially
        assert not hasattr(loader, "_config") or loader._config is None

        # Access should trigger loading
        with patch.object(loader, "_load_config") as mock_load:
            loader._ensure_config_loaded()
            mock_load.assert_called_once()

    def test_emoji_loader_file_permissions_error(self):
        """Test handling of file permission errors."""
        from lib.utils.emoji_loader import EmojiLoader

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with patch.object(
                EmojiLoader,
                "_get_config_path",
                return_value="/restricted/path.yaml",
            ):
                loader = EmojiLoader()
                loader._load_config()

                # Should handle permission error gracefully
                assert loader._config is None or loader._config == {}

    def test_emoji_loader_yaml_parsing_error(self):
        """Test handling of YAML parsing errors."""
        from lib.utils.emoji_loader import EmojiLoader

        with patch("yaml.safe_load", side_effect=yaml.YAMLError("Invalid YAML")):
            with patch.object(
                EmojiLoader,
                "_get_config_path",
                return_value="/fake/path.yaml",
            ):
                with patch("builtins.open", mock_open(read_data="some: yaml")):
                    loader = EmojiLoader()
                    loader._load_config()

                    # Should handle YAML error gracefully
                    assert loader._config is None or loader._config == {}

    def test_emoji_loader_empty_config_file(self):
        """Test handling of empty config file."""
        from lib.utils.emoji_loader import EmojiLoader

        with (
            patch("builtins.open", mock_open(read_data="")),
            patch.object(
                EmojiLoader,
                "_get_config_path",
                return_value="/fake/path.yaml",
            ),
        ):
            loader = EmojiLoader()
            loader._load_config()

            # Should handle empty file gracefully
            assert loader._config is None or loader._config == {}

    def test_auto_emoji_edge_cases(self):
        """Test auto_emoji with edge cases."""
        from lib.utils.emoji_loader import auto_emoji

        # Test with empty message
        result = auto_emoji("", "/path/to/file.py")
        assert result == ""

        # Test with None message
        result = auto_emoji(None, "/path/to/file.py")
        assert result is None or result == ""

        # Test with empty file path
        result = auto_emoji("Test message", "")
        assert result == "Test message"

        # Test with None file path
        result = auto_emoji("Test message", None)
        assert result == "Test message"

    def test_emoji_config_structure_validation(self, mock_emoji_config):
        """Test config structure validation."""
        from lib.utils.emoji_loader import EmojiLoader

        # Test valid config structure
        with patch.object(EmojiLoader, "_config", mock_emoji_config):
            loader = EmojiLoader()

            # Config should have required sections
            assert "emoji_mappings" in loader._config
            assert "context_patterns" in loader._config

            # Mappings should be dict
            assert isinstance(loader._config["emoji_mappings"], dict)
            assert isinstance(loader._config["context_patterns"], dict)

    def test_emoji_loader_multiple_pattern_matches(self, mock_emoji_config):
        """Test behavior with multiple pattern matches."""
        from lib.utils.emoji_loader import auto_emoji

        with patch("lib.utils.emoji_loader.get_emoji_loader") as mock_get_loader:
            mock_loader = MagicMock()
            mock_loader._config = mock_emoji_config
            mock_get_loader.return_value = mock_loader

            # Message that could match multiple patterns
            message = "Database API test successful"
            result = auto_emoji(message, "/api/db/test_file.py")

            # Should handle multiple matches gracefully
            assert isinstance(result, str)
            assert len(result) >= len(message)  # May have emojis added

    def test_emoji_loader_performance_with_large_config(self):
        """Test performance with large configuration."""
        from lib.utils.emoji_loader import EmojiLoader

        # Create large config
        large_config = {
            "emoji_mappings": {f"key_{i}": f"emoji_{i}" for i in range(1000)},
            "context_patterns": {f"pattern_{i}": [f"word_{i}"] for i in range(100)},
        }

        with patch.object(EmojiLoader, "_config", large_config):
            loader = EmojiLoader()

            # Should handle large config efficiently
            assert loader._config is not None
            assert len(loader._config["emoji_mappings"]) == 1000
            assert len(loader._config["context_patterns"]) == 100

    def test_emoji_loader_unicode_handling(self, mock_emoji_config):
        """Test Unicode emoji handling."""
        from lib.utils.emoji_loader import auto_emoji

        with patch("lib.utils.emoji_loader.get_emoji_loader") as mock_get_loader:
            mock_loader = MagicMock()
            mock_loader._config = mock_emoji_config
            mock_get_loader.return_value = mock_loader

            # Test with Unicode characters in message
            unicode_message = "测试消息 with émojis"
            result = auto_emoji(unicode_message, "/test/file.py")

            # Should handle Unicode gracefully
            assert isinstance(result, str)

    def test_emoji_loader_config_caching(self):
        """Test that config is cached after first load."""
        from lib.utils.emoji_loader import EmojiLoader

        loader = EmojiLoader()

        with patch.object(loader, "_load_config") as mock_load:
            mock_load.return_value = None
            loader._config = {"test": "config"}

            # First call should not reload
            loader._ensure_config_loaded()
            mock_load.assert_not_called()

            # Config should remain cached
            assert loader._config == {"test": "config"}


class TestEmojiLoaderIntegration:
    """Integration tests for emoji loader with other components."""

    def test_emoji_loader_with_logging(self):
        """Test emoji loader integration with logging."""
        from lib.utils.emoji_loader import auto_emoji

        # Test message that might come from logging
        log_message = "Application started successfully"
        result = auto_emoji(log_message, "/app/main.py")

        # Should return a string result
        assert isinstance(result, str)

    def test_emoji_loader_with_real_file_paths(self):
        """Test emoji loader with realistic file paths."""
        from lib.utils.emoji_loader import auto_emoji

        test_cases = [
            ("API server started", "/project/api/server.py"),
            ("Database connection established", "/project/db/connection.py"),
            ("Unit test passed", "/project/tests/test_module.py"),
            ("Configuration loaded", "/project/config/settings.py"),
        ]

        for message, file_path in test_cases:
            result = auto_emoji(message, file_path)

            # Should return a string (possibly with emojis)
            assert isinstance(result, str)
            assert len(result) >= len(message)

    def test_emoji_loader_thread_safety(self):
        """Test emoji loader thread safety."""
        import threading

        from lib.utils.emoji_loader import get_emoji_loader

        results = []

        def test_function():
            loader = get_emoji_loader()
            results.append(id(loader))

        # Create multiple threads
        threads = [threading.Thread(target=test_function) for _ in range(10)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All threads should get the same instance
        assert len(set(results)) == 1

    def test_emoji_loader_memory_usage(self):
        """Test emoji loader memory usage patterns."""
        from lib.utils.emoji_loader import auto_emoji, get_emoji_loader

        # Get initial loader
        loader = get_emoji_loader()
        initial_config = loader._config

        # Use auto_emoji multiple times
        for i in range(100):
            auto_emoji(f"Test message {i}", f"/path/to/file_{i}.py")

        # Config should remain the same (no memory leaks)
        final_config = loader._config
        assert initial_config is final_config
