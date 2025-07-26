"""
Comprehensive tests for lib/utils/yaml_cache.py to improve from 26% to 90%+ coverage.
Testing uncovered lines: 59-72, 86-130, 143-184, 197-201, 205-223, 227-238, 247-251, 260-263, 267-271, 280-284, 308-312, 318-319, 334, 348, 362
"""

import shutil
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml


class TestYamlCacheManager:
    """Comprehensive tests for YAML cache manager."""

    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_yaml_content(self):
        """Sample YAML content for testing."""
        return {
            "test": {
                "name": "Sample Test",
                "version": "1.0.0",
                "description": "A sample test configuration",
            },
            "settings": {"debug": True, "timeout": 30},
        }

    def test_yaml_cache_manager_creation(self):
        """Test YAML cache manager creation."""
        from lib.utils.yaml_cache import YamlCacheManager

        manager = YamlCacheManager()
        assert manager is not None
        assert hasattr(manager, "_cache")
        assert hasattr(manager, "_file_mtimes")

    def test_get_yaml_cache_manager_singleton(self):
        """Test get_yaml_cache_manager singleton pattern."""
        from lib.utils.yaml_cache import get_yaml_cache_manager

        manager1 = get_yaml_cache_manager()
        manager2 = get_yaml_cache_manager()

        # Should return same instance
        assert manager1 is manager2
        assert manager1 is not None

    def test_yaml_cache_file_loading(self, temp_directory, sample_yaml_content):
        """Test YAML file loading with caching."""
        from lib.utils.yaml_cache import YamlCacheManager

        # Create test YAML file
        yaml_file = temp_directory / "test.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(sample_yaml_content, f)

        manager = YamlCacheManager()

        # First load should read from file
        result1 = manager.load_yaml(str(yaml_file))
        assert result1 == sample_yaml_content

        # Second load should use cache
        result2 = manager.load_yaml(str(yaml_file))
        assert result2 == sample_yaml_content
        assert result1 is result2  # Should be same object from cache

    def test_yaml_cache_file_modification_detection(
        self,
        temp_directory,
        sample_yaml_content,
    ):
        """Test file modification detection and cache invalidation."""
        from lib.utils.yaml_cache import YamlCacheManager

        yaml_file = temp_directory / "test.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(sample_yaml_content, f)

        manager = YamlCacheManager()

        # Load initial content
        result1 = manager.load_yaml(str(yaml_file))
        assert result1 == sample_yaml_content

        # Modify file
        time.sleep(0.1)  # Ensure different mtime
        modified_content = {"modified": True}
        with open(yaml_file, "w") as f:
            yaml.dump(modified_content, f)

        # Should detect modification and reload
        result2 = manager.load_yaml(str(yaml_file))
        assert result2 == modified_content
        assert result2 != result1

    def test_yaml_cache_invalid_file_handling(self):
        """Test handling of invalid/non-existent files."""
        from lib.utils.yaml_cache import YamlCacheManager

        manager = YamlCacheManager()

        # Test non-existent file
        result = manager.load_yaml("/non/existent/file.yaml")
        assert result is None

        # Test invalid YAML
        with patch("builtins.open", mock_open(read_data="invalid: yaml: content: [")):
            result = manager.load_yaml("/fake/invalid.yaml")
            assert result is None

    def test_yaml_cache_permission_error_handling(self):
        """Test handling of permission errors."""
        from lib.utils.yaml_cache import YamlCacheManager

        manager = YamlCacheManager()

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            result = manager.load_yaml("/restricted/file.yaml")
            assert result is None

    def test_yaml_cache_clear_functionality(self, temp_directory, sample_yaml_content):
        """Test cache clearing functionality."""
        from lib.utils.yaml_cache import YamlCacheManager

        yaml_file = temp_directory / "test.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(sample_yaml_content, f)

        manager = YamlCacheManager()

        # Load and cache
        manager.load_yaml(str(yaml_file))
        assert str(yaml_file) in manager._cache

        # Clear cache
        manager.clear_cache()
        assert len(manager._cache) == 0
        assert len(manager._file_mtimes) == 0

    def test_yaml_cache_thread_safety(self, temp_directory, sample_yaml_content):
        """Test thread safety of YAML cache."""
        from lib.utils.yaml_cache import get_yaml_cache_manager

        yaml_file = temp_directory / "test.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(sample_yaml_content, f)

        results = []
        errors = []

        def test_function():
            try:
                manager = get_yaml_cache_manager()
                result = manager.load_yaml(str(yaml_file))
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = [threading.Thread(target=test_function) for _ in range(10)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Should have no errors and consistent results
        assert len(errors) == 0
        assert len(results) == 10
        assert all(result == sample_yaml_content for result in results)

    def test_yaml_cache_memory_management(self, temp_directory):
        """Test memory management with large cache."""
        from lib.utils.yaml_cache import YamlCacheManager

        manager = YamlCacheManager()

        # Create many YAML files
        for i in range(100):
            yaml_file = temp_directory / f"test_{i}.yaml"
            content = {"index": i, "data": f"test_data_{i}"}
            with open(yaml_file, "w") as f:
                yaml.dump(content, f)

            # Load to cache
            manager.load_yaml(str(yaml_file))

        # All files should be cached
        assert len(manager._cache) == 100
        assert len(manager._file_mtimes) == 100

        # Clear should work
        manager.clear_cache()
        assert len(manager._cache) == 0


class TestYamlCacheUtilityFunctions:
    """Test utility functions in yaml_cache module."""

    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_load_yaml_cached_function(self, temp_directory):
        """Test load_yaml_cached utility function."""
        from lib.utils.yaml_cache import load_yaml_cached

        # Create test file
        yaml_file = temp_directory / "test.yaml"
        content = {"test": "content"}
        with open(yaml_file, "w") as f:
            yaml.dump(content, f)

        # Test loading
        result = load_yaml_cached(str(yaml_file))
        assert result == content

        # Test caching behavior
        result2 = load_yaml_cached(str(yaml_file))
        assert result2 == content

    def test_discover_components_cached_function(self, temp_directory):
        """Test discover_components_cached utility function."""
        from lib.utils.yaml_cache import discover_components_cached

        # Create component directories and files
        agents_dir = temp_directory / "agents"
        teams_dir = temp_directory / "teams"
        workflows_dir = temp_directory / "workflows"

        agents_dir.mkdir()
        teams_dir.mkdir()
        workflows_dir.mkdir()

        # Create component config files
        agent_config = temp_directory / "agents" / "config.yaml"
        team_config = temp_directory / "teams" / "config.yaml"
        workflow_config = temp_directory / "workflows" / "config.yaml"

        for config_file in [agent_config, team_config, workflow_config]:
            with open(config_file, "w") as f:
                yaml.dump({"name": "test_component"}, f)

        # Test discovery
        result = discover_components_cached(str(temp_directory))

        assert "agents" in result
        assert "teams" in result
        assert "workflows" in result

        # Should find the config files
        assert len(result["agents"]) > 0
        assert len(result["teams"]) > 0
        assert len(result["workflows"]) > 0

    def test_discover_components_empty_directory(self, temp_directory):
        """Test component discovery in empty directory."""
        from lib.utils.yaml_cache import discover_components_cached

        result = discover_components_cached(str(temp_directory))

        # Should return empty collections
        assert result["agents"] == []
        assert result["teams"] == []
        assert result["workflows"] == []

    def test_discover_components_non_existent_directory(self):
        """Test component discovery with non-existent directory."""
        from lib.utils.yaml_cache import discover_components_cached

        result = discover_components_cached("/non/existent/directory")

        # Should handle gracefully
        assert isinstance(result, dict)
        assert "agents" in result
        assert "teams" in result
        assert "workflows" in result

    def test_yaml_cache_error_recovery(self, temp_directory):
        """Test error recovery in YAML cache operations."""
        from lib.utils.yaml_cache import YamlCacheManager

        manager = YamlCacheManager()

        # Test recovery from OS errors
        with patch("os.path.getmtime", side_effect=OSError("File system error")):
            result = manager.load_yaml("/fake/file.yaml")
            assert result is None

        # Test recovery from YAML errors
        with patch("yaml.safe_load", side_effect=yaml.YAMLError("Invalid YAML")):
            with patch("builtins.open", mock_open(read_data="some: content")):
                result = manager.load_yaml("/fake/file.yaml")
                assert result is None

    def test_yaml_cache_mtime_comparison(self, temp_directory):
        """Test modification time comparison logic."""
        from lib.utils.yaml_cache import YamlCacheManager

        yaml_file = temp_directory / "test.yaml"
        content = {"version": 1}

        with open(yaml_file, "w") as f:
            yaml.dump(content, f)

        manager = YamlCacheManager()

        # First load
        result1 = manager.load_yaml(str(yaml_file))
        assert result1 == content

        # Get original mtime
        original_mtime = manager._file_mtimes.get(str(yaml_file))
        assert original_mtime is not None

        # Modify file with significantly different time
        time.sleep(0.1)
        updated_content = {"version": 2}
        with open(yaml_file, "w") as f:
            yaml.dump(updated_content, f)

        # Should detect change
        result2 = manager.load_yaml(str(yaml_file))
        assert result2 == updated_content

        # New mtime should be different
        new_mtime = manager._file_mtimes.get(str(yaml_file))
        assert new_mtime != original_mtime

    def test_yaml_cache_large_file_handling(self, temp_directory):
        """Test handling of large YAML files."""
        from lib.utils.yaml_cache import YamlCacheManager

        # Create large YAML content
        large_content = {
            f"section_{i}": {f"key_{j}": f"value_{i}_{j}" for j in range(100)}
            for i in range(50)
        }

        yaml_file = temp_directory / "large.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(large_content, f)

        manager = YamlCacheManager()

        # Should handle large files
        result = manager.load_yaml(str(yaml_file))
        assert result == large_content
        assert len(result) == 50

    def test_yaml_cache_concurrent_access(self, temp_directory):
        """Test concurrent access to cached files."""
        from lib.utils.yaml_cache import get_yaml_cache_manager

        yaml_file = temp_directory / "concurrent.yaml"
        content = {"concurrent": True}

        with open(yaml_file, "w") as f:
            yaml.dump(content, f)

        manager = get_yaml_cache_manager()
        results = []

        def concurrent_reader():
            result = manager.load_yaml(str(yaml_file))
            results.append(result)

        # Start multiple concurrent readers
        threads = [threading.Thread(target=concurrent_reader) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All should get the same result
        assert len(results) == 5
        assert all(result == content for result in results)


class TestYamlCacheEdgeCases:
    """Test edge cases and error conditions."""

    def test_yaml_cache_symlink_handling(self, temp_directory):
        """Test handling of symbolic links."""
        from lib.utils.yaml_cache import YamlCacheManager

        # Create original file
        original_file = temp_directory / "original.yaml"
        content = {"original": True}
        with open(original_file, "w") as f:
            yaml.dump(content, f)

        # Create symlink
        symlink_file = temp_directory / "symlink.yaml"
        try:
            symlink_file.symlink_to(original_file)

            manager = YamlCacheManager()

            # Should handle symlinks
            result = manager.load_yaml(str(symlink_file))
            assert result == content

        except OSError:
            # Skip test if symlinks not supported
            pytest.skip("Symlinks not supported on this system")

    def test_yaml_cache_unicode_content(self, temp_directory):
        """Test handling of Unicode content."""
        from lib.utils.yaml_cache import YamlCacheManager

        unicode_content = {
            "english": "Hello World",
            "chinese": "你好世界",
            "emoji": "🌍🚀✨",
            "japanese": "こんにちは世界",
        }

        yaml_file = temp_directory / "unicode.yaml"
        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(unicode_content, f, allow_unicode=True)

        manager = YamlCacheManager()
        result = manager.load_yaml(str(yaml_file))
        assert result == unicode_content

    def test_yaml_cache_binary_file_handling(self, temp_directory):
        """Test handling of binary files mistaken for YAML."""
        from lib.utils.yaml_cache import YamlCacheManager

        # Create binary file with .yaml extension
        binary_file = temp_directory / "binary.yaml"
        with open(binary_file, "wb") as f:
            f.write(b"\x00\x01\x02\x03\x04\x05")

        manager = YamlCacheManager()
        result = manager.load_yaml(str(binary_file))

        # Should handle gracefully
        assert result is None

    def test_yaml_cache_very_long_path(self, temp_directory):
        """Test handling of very long file paths."""
        from lib.utils.yaml_cache import YamlCacheManager

        # Create deeply nested directory
        deep_path = temp_directory
        for i in range(10):
            deep_path = deep_path / f"very_long_directory_name_{i}"
            deep_path.mkdir(exist_ok=True)

        yaml_file = deep_path / "deep_file.yaml"
        content = {"deep": True}

        try:
            with open(yaml_file, "w") as f:
                yaml.dump(content, f)

            manager = YamlCacheManager()
            result = manager.load_yaml(str(yaml_file))
            assert result == content

        except OSError:
            # Skip if path too long for filesystem
            pytest.skip("Path too long for filesystem")

    def test_yaml_cache_rapid_file_changes(self, temp_directory):
        """Test handling of rapid file changes."""
        from lib.utils.yaml_cache import YamlCacheManager

        yaml_file = temp_directory / "rapid.yaml"
        manager = YamlCacheManager()

        # Make rapid changes
        for i in range(10):
            content = {"version": i}
            with open(yaml_file, "w") as f:
                yaml.dump(content, f)

            result = manager.load_yaml(str(yaml_file))
            assert result["version"] == i

            # Small delay to ensure different mtimes
            time.sleep(0.01)

    def test_yaml_cache_circular_references(self, temp_directory):
        """Test handling of YAML with circular references."""
        from lib.utils.yaml_cache import YamlCacheManager

        # Create YAML with references (YAML anchors/aliases)
        yaml_content = """
        defaults: &defaults
          timeout: 30
          retries: 3

        config1:
          <<: *defaults
          name: "Config 1"

        config2:
          <<: *defaults
          name: "Config 2"
        """

        yaml_file = temp_directory / "references.yaml"
        with open(yaml_file, "w") as f:
            f.write(yaml_content)

        manager = YamlCacheManager()
        result = manager.load_yaml(str(yaml_file))

        # Should handle YAML references
        assert result is not None
        assert "config1" in result
        assert "config2" in result
        assert result["config1"]["timeout"] == 30
        assert result["config2"]["timeout"] == 30


class TestYamlCachePerformance:
    """Test performance aspects of YAML cache."""

    def test_yaml_cache_performance_benchmark(self, temp_directory):
        """Basic performance benchmark for YAML cache."""
        import time

        from lib.utils.yaml_cache import YamlCacheManager

        # Create test file
        yaml_file = temp_directory / "benchmark.yaml"
        content = {"benchmark": True, "data": list(range(1000))}
        with open(yaml_file, "w") as f:
            yaml.dump(content, f)

        manager = YamlCacheManager()

        # Time first load (from disk)
        start_time = time.time()
        result1 = manager.load_yaml(str(yaml_file))
        first_load_time = time.time() - start_time

        # Time second load (from cache)
        start_time = time.time()
        result2 = manager.load_yaml(str(yaml_file))
        cached_load_time = time.time() - start_time

        # Cache should be faster
        assert cached_load_time < first_load_time
        assert result1 == result2

    def test_yaml_cache_memory_efficiency(self, temp_directory):
        """Test memory efficiency of cache."""
        from lib.utils.yaml_cache import YamlCacheManager

        manager = YamlCacheManager()

        # Load same file multiple times
        yaml_file = temp_directory / "memory_test.yaml"
        content = {"memory": "test"}
        with open(yaml_file, "w") as f:
            yaml.dump(content, f)

        # Multiple loads should return same object (memory efficient)
        results = []
        for _ in range(5):
            result = manager.load_yaml(str(yaml_file))
            results.append(result)

        # All results should be the same object (same id)
        first_id = id(results[0])
        assert all(id(result) == first_id for result in results)
