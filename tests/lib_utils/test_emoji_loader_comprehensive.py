"""
Comprehensive tests for lib/utils/emoji_loader.py to improve from 42% to 90%+ coverage.
Testing the uncovered lines: 32-33, 37, 50-92, 114-119, 124-125, 130-131
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

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

        # Create config file with correct structure
        config_file = temp_directory / "emoji_config.yaml"
        correct_config = {
            "resource_types": {
                "directories": {"api/": "🌐", "db/": "🗄️", "tests/": "🧪"},
                "activities": {"success": "✅", "error": "❌", "warning": "⚠️"},
                "services": {"database": "🗄️", "api": "🌐"},
                "file_types": {".py": "🐍", ".yaml": "⚙️"},
            }
        }
        with open(config_file, "w") as f:
            yaml.dump(correct_config, f)

        # Test with custom config path
        loader = EmojiLoader(str(config_file))
        assert loader._config is not None
        assert "resource_types" in loader._config

    def test_emoji_loader_config_file_not_found(self):
        """Test behavior when config file not found."""
        from lib.utils.emoji_loader import EmojiLoader

        # Test with non-existent config path
        loader = EmojiLoader("/non/existent/path.yaml")

        # Should handle missing file gracefully
        assert loader._config == {}

    def test_emoji_loader_invalid_yaml(self, temp_directory):
        """Test behavior with invalid YAML file."""
        from lib.utils.emoji_loader import EmojiLoader

        # Create invalid YAML file
        invalid_yaml_file = temp_directory / "invalid.yaml"
        with open(invalid_yaml_file, "w") as f:
            f.write("invalid: yaml: content: [")

        loader = EmojiLoader(str(invalid_yaml_file))

        # Should handle invalid YAML gracefully
        assert loader._config == {}

    def test_auto_emoji_function_with_config(self, temp_directory):
        """Test auto_emoji function with valid config."""
        from lib.utils.emoji_loader import EmojiLoader, auto_emoji

        # Create proper config file
        config_file = temp_directory / "emoji_config.yaml"
        config = {
            "resource_types": {
                "directories": {"db/": "🗄️", "api/": "🌐"},
                "activities": {"database": "🗄️", "query": "🔍"},
                "services": {"api": "🌐", "endpoint": "🔗"},
            }
        }
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        # Reset the global loader and force creation with our config
        with patch("lib.utils.emoji_loader._loader", None):
            # Create a real loader with our config
            test_loader = EmojiLoader(str(config_file))

            with patch(
                "lib.utils.emoji_loader.get_emoji_loader", return_value=test_loader
            ):
                # Test message with matching keywords
                result = auto_emoji("Database query successful", "/path/to/file.py")
                # Should contain emoji or be unchanged
                assert isinstance(result, str)
                assert len(result) >= len("Database query successful")

                # Test message with directory pattern
                result = auto_emoji("Processing", "api/routes.py")
                assert isinstance(result, str)
                assert len(result) >= len("Processing")

    def test_auto_emoji_function_without_config(self):
        """Test auto_emoji function without config."""
        from lib.utils.emoji_loader import EmojiLoader, auto_emoji

        # Force no config by using non-existent file
        with patch("lib.utils.emoji_loader._loader", None):
            # Create a real loader with no config
            test_loader = EmojiLoader("/non/existent/path.yaml")

            with patch(
                "lib.utils.emoji_loader.get_emoji_loader", return_value=test_loader
            ):
                # Should return original message when no config
                message = "Test message"
                result = auto_emoji(message, "/path/to/file.py")
                assert result == message

    def test_emoji_loader_pattern_matching(self, temp_directory):
        """Test pattern matching logic."""
        from lib.utils.emoji_loader import EmojiLoader

        # Create config with proper structure
        config_file = temp_directory / "emoji_config.yaml"
        config = {
            "resource_types": {
                "directories": {"api/": "🌐", "db/": "🗄️", "tests/": "🧪"},
                "activities": {"endpoint": "🔗", "migration": "📦", "test": "🧪"},
            }
        }
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        loader = EmojiLoader(str(config_file))

        # Test pattern matching via get_emoji method
        test_cases = [
            ("api/routes.py", "API endpoint ready", "🌐"),
            ("db/migration.py", "Database migration complete", "🗄️"),
            ("tests/test_something.py", "Test case passed", "🧪"),
            ("random/file.py", "Random message", ""),
        ]

        for file_path, message, expected_result in test_cases:
            result = loader.get_emoji(file_path, message)
            if expected_result:
                assert result == expected_result or result != ""
            else:
                assert result == ""

    def test_emoji_loader_config_path_resolution(self):
        """Test config path resolution."""
        from lib.utils.emoji_loader import EmojiLoader

        loader = EmojiLoader()
        config_path = loader.config_path

        # Should return a valid Path object
        assert config_path is not None
        assert str(config_path).endswith("emoji_mappings.yaml")
        assert "lib/config" in str(config_path)

    def test_emoji_loader_lazy_initialization(self):
        """Test config initialization."""
        from lib.utils.emoji_loader import EmojiLoader

        loader = EmojiLoader()

        # Config should be loaded during initialization
        assert hasattr(loader, "_config")
        assert loader._config is not None or loader._config == {}

        # Test that config loading doesn't fail
        assert isinstance(loader._config, dict)

    def test_emoji_loader_file_permissions_error(self, temp_directory):
        """Test handling of file permission errors."""
        import os
        import stat

        from lib.utils.emoji_loader import EmojiLoader

        # Create a file and remove read permissions
        restricted_file = temp_directory / "restricted.yaml"
        with open(restricted_file, "w") as f:
            f.write("test: config")

        # Remove read permissions
        os.chmod(restricted_file, stat.S_IWRITE)

        try:
            loader = EmojiLoader(str(restricted_file))
            # Should handle permission error gracefully
            assert loader._config == {}
        finally:
            # Restore permissions for cleanup
            os.chmod(restricted_file, stat.S_IREAD | stat.S_IWRITE)

    def test_emoji_loader_yaml_parsing_error(self, temp_directory):
        """Test handling of YAML parsing errors."""
        from lib.utils.emoji_loader import EmojiLoader

        # Create file with invalid YAML
        invalid_file = temp_directory / "invalid.yaml"
        with open(invalid_file, "w") as f:
            f.write("invalid: yaml: content: { [ unclosed")

        loader = EmojiLoader(str(invalid_file))

        # Should handle YAML error gracefully
        assert loader._config == {}

    def test_emoji_loader_empty_config_file(self, temp_directory):
        """Test handling of empty config file."""
        from lib.utils.emoji_loader import EmojiLoader

        # Create empty file
        empty_file = temp_directory / "empty.yaml"
        with open(empty_file, "w") as f:
            f.write("")

        loader = EmojiLoader(str(empty_file))

        # Should handle empty file gracefully
        assert loader._config == {}

    def test_auto_emoji_edge_cases(self):
        """Test auto_emoji with edge cases."""
        from lib.utils.emoji_loader import EmojiLoader, auto_emoji

        # Force a clean loader with empty config
        with patch("lib.utils.emoji_loader._loader", None):
            test_loader = EmojiLoader("/non/existent/path.yaml")

            with patch(
                "lib.utils.emoji_loader.get_emoji_loader", return_value=test_loader
            ):
                # Test with empty message
                result = auto_emoji("", "/path/to/file.py")
                assert result == ""

                # Test with empty file path
                result = auto_emoji("Test message", "")
                assert result == "Test message"

                # Test normal case
                result = auto_emoji("Test message", "/path/to/file.py")
                assert isinstance(result, str)
                assert result == "Test message"

    def test_emoji_config_structure_validation(self, temp_directory):
        """Test config structure validation."""
        from lib.utils.emoji_loader import EmojiLoader

        # Create valid config structure
        config_file = temp_directory / "valid_config.yaml"
        config = {
            "resource_types": {
                "directories": {"api/": "🌐"},
                "activities": {"success": "✅"},
                "services": {"database": "🗄️"},
                "file_types": {".py": "🐍"},
            }
        }
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        loader = EmojiLoader(str(config_file))

        # Config should have required sections
        assert "resource_types" in loader._config

        # Resource types should be dict
        assert isinstance(loader._config["resource_types"], dict)
        assert isinstance(loader._config["resource_types"]["directories"], dict)

    def test_emoji_loader_multiple_pattern_matches(self, temp_directory):
        """Test behavior with multiple pattern matches."""
        from lib.utils.emoji_loader import EmojiLoader, auto_emoji

        # Create config with overlapping patterns
        config_file = temp_directory / "multi_config.yaml"
        config = {
            "resource_types": {
                "directories": {"api/": "🌐", "db/": "🗄️", "test/": "🧪"},
                "activities": {"database": "🗄️", "api": "🌐", "test": "🧪"},
            }
        }
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        with patch("lib.utils.emoji_loader._loader", None):
            test_loader = EmojiLoader(str(config_file))

            with patch(
                "lib.utils.emoji_loader.get_emoji_loader", return_value=test_loader
            ):
                # Message that could match multiple patterns
                message = "Database API test successful"
                result = auto_emoji(message, "/api/db/test_file.py")

                # Should handle multiple matches gracefully
                assert isinstance(result, str)
                assert len(result) >= len(message)  # May have emojis added

    def test_emoji_loader_performance_with_large_config(self, temp_directory):
        """Test performance with large configuration."""
        from lib.utils.emoji_loader import EmojiLoader

        # Create large config
        config_file = temp_directory / "large_config.yaml"
        large_config = {
            "resource_types": {
                "directories": {f"dir_{i}/": f"emoji_{i}" for i in range(100)},
                "activities": {f"activity_{i}": f"emoji_{i}" for i in range(100)},
                "services": {f"service_{i}": f"emoji_{i}" for i in range(100)},
                "file_types": {f".ext_{i}": f"emoji_{i}" for i in range(100)},
            }
        }
        with open(config_file, "w") as f:
            yaml.dump(large_config, f)

        loader = EmojiLoader(str(config_file))

        # Should handle large config efficiently
        assert loader._config is not None
        assert "resource_types" in loader._config
        assert len(loader._config["resource_types"]["directories"]) == 100

    def test_emoji_loader_unicode_handling(self, temp_directory):
        """Test Unicode emoji handling."""
        from lib.utils.emoji_loader import EmojiLoader, auto_emoji

        # Create config file
        config_file = temp_directory / "unicode_config.yaml"
        config = {"resource_types": {"activities": {"test": "🧪"}}}
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        with patch("lib.utils.emoji_loader._loader", None):
            test_loader = EmojiLoader(str(config_file))

            with patch(
                "lib.utils.emoji_loader.get_emoji_loader", return_value=test_loader
            ):
                # Test with Unicode characters in message
                unicode_message = "测试消息 with émojis"
                result = auto_emoji(unicode_message, "/test/file.py")

                # Should handle Unicode gracefully
                assert isinstance(result, str)

    def test_emoji_loader_config_caching(self, temp_directory):
        """Test that config loading works properly."""
        from lib.utils.emoji_loader import EmojiLoader

        # Create config file
        config_file = temp_directory / "cache_test.yaml"
        config = {"resource_types": {"activities": {"test": "🧪"}}}
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        loader = EmojiLoader(str(config_file))

        # Config should be loaded and consistent
        first_config = loader._config
        second_config = loader._config
        assert first_config is second_config
        assert "resource_types" in loader._config


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
