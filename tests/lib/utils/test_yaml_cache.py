"""
Comprehensive tests for YAML Cache Manager.

Tests the centralized YAML loading and caching system to ensure proper
cache invalidation, thread safety, and performance optimization.
"""

import os
import threading
import time
from unittest.mock import MagicMock, patch

import pytest
import yaml

from lib.utils.yaml_cache import (
    CachedGlob,
    CachedYAML,
    YAMLCacheManager,
    get_yaml_cache_manager,
    reset_yaml_cache_manager,
)


class TestCachedYAML:
    """Test CachedYAML dataclass."""

    def test_cached_yaml_creation(self):
        """Test CachedYAML can be created with all required fields."""
        content = {"test": "data"}
        mtime = 1234567890.0
        file_path = "/test/path.yaml"
        size_bytes = 100

        cached = CachedYAML(content, mtime, file_path, size_bytes)

        assert cached.content == content
        assert cached.mtime == mtime
        assert cached.file_path == file_path
        assert cached.size_bytes == size_bytes


class TestCachedGlob:
    """Test CachedGlob dataclass."""

    def test_cached_glob_creation(self):
        """Test CachedGlob can be created with all required fields."""
        file_paths = ["/test/file1.yaml", "/test/file2.yaml"]
        dir_mtime = 1234567890.0
        pattern = "*.yaml"

        cached = CachedGlob(file_paths, dir_mtime, pattern)

        assert cached.file_paths == file_paths
        assert cached.dir_mtime == dir_mtime
        assert cached.pattern == pattern


class TestYAMLCacheManager:
    """Comprehensive tests for YAMLCacheManager."""

    def setup_method(self):
        """Set up clean cache manager for each test."""
        reset_yaml_cache_manager()  # Reset singleton for clean tests
        self.cache = get_yaml_cache_manager()

    def test_singleton_pattern(self):
        """Test that YAMLCacheManager follows singleton pattern."""
        reset_yaml_cache_manager()  # Ensure clean state
        cache1 = get_yaml_cache_manager()
        cache2 = get_yaml_cache_manager()
        assert cache1 is cache2

    def test_cache_initialization(self):
        """Test cache manager initializes with empty caches."""
        cache = self.cache
        assert len(cache._yaml_cache) == 0
        assert len(cache._glob_cache) == 0
        assert isinstance(cache._lock, type(threading.RLock()))

    def test_load_yaml_file_not_exists(self):
        """Test loading non-existent YAML file returns None."""
        result = self.cache.get_yaml("/non/existent/file.yaml")
        assert result is None

    @patch("os.path.getmtime")
    @patch("os.path.getsize")
    @patch("os.path.exists")
    @patch("builtins.open")
    def test_load_yaml_success(
        self,
        mock_open,
        mock_exists,
        mock_getsize,
        mock_getmtime,
    ):
        """Test successful YAML file loading and caching."""
        # Setup mocks
        mock_exists.return_value = True
        mock_getmtime.return_value = 1234567890.0
        mock_getsize.return_value = 100

        yaml_content = {"test": "data", "nested": {"key": "value"}}
        mock_file = MagicMock()
        mock_file.read.return_value = yaml.dump(yaml_content)
        mock_open.return_value.__enter__.return_value = mock_file

        # Test loading
        result = self.cache.get_yaml("/test/file.yaml")

        assert result == yaml_content
        assert os.path.abspath("/test/file.yaml") in self.cache._yaml_cache

        cached_item = self.cache._yaml_cache[os.path.abspath("/test/file.yaml")]
        assert cached_item.content == yaml_content
        assert cached_item.mtime == 1234567890.0
        assert cached_item.file_path == os.path.abspath("/test/file.yaml")
        assert cached_item.size_bytes == 100

    @patch("os.path.getmtime")
    @patch("os.path.exists")
    def test_load_yaml_cache_hit(self, mock_exists, mock_getmtime):
        """Test YAML cache hit returns cached content without file access."""
        # Setup cache with existing item
        cached_content = {"cached": "data"}
        cached_item = CachedYAML(cached_content, 1234567890.0, "/test/file.yaml", 100)
        self.cache._yaml_cache["/test/file.yaml"] = cached_item

        # Mock file system
        mock_exists.return_value = True
        mock_getmtime.return_value = 1234567890.0  # Same mtime = cache hit

        result = self.cache.get_yaml("/test/file.yaml")

        assert result == cached_content
        # Verify no additional file operations occurred
        mock_getmtime.assert_called_once()

    @patch("os.path.getmtime")
    @patch("os.path.getsize")
    @patch("os.path.exists")
    @patch("builtins.open")
    def test_load_yaml_cache_invalidation(
        self,
        mock_open,
        mock_exists,
        mock_getsize,
        mock_getmtime,
    ):
        """Test cache invalidation when file is modified."""
        # Setup cache with existing item
        old_content = {"old": "data"}
        cached_item = CachedYAML(old_content, 1234567890.0, "/test/file.yaml", 100)
        self.cache._yaml_cache["/test/file.yaml"] = cached_item

        # Mock file system with newer modification time
        mock_exists.return_value = True
        mock_getmtime.return_value = 1234567900.0  # Newer mtime = cache miss
        mock_getsize.return_value = 150

        new_content = {"new": "data"}
        mock_file = MagicMock()
        mock_file.read.return_value = yaml.dump(new_content)
        mock_open.return_value.__enter__.return_value = mock_file

        result = self.cache.get_yaml("/test/file.yaml")

        assert result == new_content
        assert self.cache._yaml_cache["/test/file.yaml"].content == new_content
        assert self.cache._yaml_cache["/test/file.yaml"].mtime == 1234567900.0

    @patch("os.path.getmtime")
    @patch("os.path.getsize") 
    @patch("builtins.open")
    @patch("os.path.exists")
    def test_load_yaml_invalid_yaml(self, mock_exists, mock_open, mock_getsize, mock_getmtime):
        """Test handling of invalid YAML content."""
        mock_exists.return_value = True
        mock_getmtime.return_value = 1234567890.0
        mock_getsize.return_value = 100

        # Mock invalid YAML content
        mock_file = MagicMock()
        mock_file.read.return_value = "invalid: yaml: content: [unclosed"
        mock_open.return_value.__enter__.return_value = mock_file

        result = self.cache.get_yaml("/test/invalid.yaml")

        assert result is None
        # The error is logged but we can't easily mock loguru logger

    def test_load_yaml_file_permission_error(self):
        """Test handling of file permission errors."""
        with patch("os.path.exists", return_value=True):
            with patch("os.path.getmtime", return_value=1234567890.0):
                with patch("builtins.open", side_effect=PermissionError("Access denied")):
                    result = self.cache.get_yaml("/test/protected.yaml")

                    assert result is None
                    # The error is logged but we can't easily mock loguru logger

    @patch("glob.glob")
    @patch("os.path.getmtime")
    @patch("os.path.exists")
    @patch("os.listdir")
    def test_discover_yaml_files_success(
        self, mock_listdir, mock_exists, mock_getmtime, mock_glob
    ):
        """Test successful YAML file discovery with glob patterns."""
        file_paths = ["/test/file1.yaml", "/test/file2.yaml"]
        mock_glob.return_value = file_paths
        mock_getmtime.return_value = 1234567890.0
        mock_exists.return_value = True
        mock_listdir.return_value = []  # No subdirectories

        result = self.cache.discover_components("/test/*.yaml")

        assert result == file_paths
        assert "/test/*.yaml" in self.cache._glob_cache

        cached_item = self.cache._glob_cache["/test/*.yaml"]
        assert cached_item.file_paths == file_paths
        assert cached_item.dir_mtime == 1234567890.0
        assert cached_item.pattern == "/test/*.yaml"

    @patch("os.path.getmtime")
    @patch("os.path.exists")
    @patch("os.listdir")
    def test_discover_yaml_files_cache_hit(
        self, mock_listdir, mock_exists, mock_getmtime
    ):
        """Test glob cache hit returns cached results."""
        # Setup cache with existing glob results
        cached_paths = ["/test/cached1.yaml", "/test/cached2.yaml"]
        cached_item = CachedGlob(cached_paths, 1234567890.0, "*.yaml")
        self.cache._glob_cache["/test/*.yaml"] = cached_item

        mock_getmtime.return_value = 1234567890.0  # Same mtime = cache hit
        mock_exists.return_value = True
        mock_listdir.return_value = []  # No subdirectories

        result = self.cache.discover_components("/test/*.yaml")

        assert result == cached_paths
        mock_getmtime.assert_called_once()

    @patch("glob.glob")
    @patch("os.path.getmtime")
    @patch("os.path.exists")
    @patch("os.listdir")
    def test_discover_yaml_files_cache_invalidation(
        self, mock_listdir, mock_exists, mock_getmtime, mock_glob
    ):
        """Test glob cache invalidation when directory is modified."""
        # Setup cache with existing glob results
        old_paths = ["/test/old.yaml"]
        cached_item = CachedGlob(old_paths, 1234567890.0, "*.yaml")
        self.cache._glob_cache["/test/*.yaml"] = cached_item

        # Mock directory with newer modification time
        mock_getmtime.return_value = 1234567900.0  # Newer mtime = cache miss
        mock_exists.return_value = True
        mock_listdir.return_value = []  # No subdirectories
        new_paths = ["/test/new1.yaml", "/test/new2.yaml"]
        mock_glob.return_value = new_paths

        result = self.cache.discover_components("/test/*.yaml")

        assert result == new_paths
        assert self.cache._glob_cache["/test/*.yaml"].file_paths == new_paths
        assert self.cache._glob_cache["/test/*.yaml"].dir_mtime == 1234567900.0

    def test_discover_yaml_files_directory_not_exists(self):
        """Test discovery on non-existent directory returns empty list."""
        with patch("os.path.getmtime", side_effect=OSError("Directory not found")):
            result = self.cache.discover_components("/non/existent/*.yaml")
            assert result == []

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        # Populate caches
        self.cache._yaml_cache["/test/file.yaml"] = CachedYAML(
            {"test": "data"},
            123.0,
            "/test/file.yaml",
            100,
        )
        self.cache._glob_cache["/test/*.yaml"] = CachedGlob(
            ["/test/file.yaml"],
            123.0,
            "*.yaml",
        )

        assert len(self.cache._yaml_cache) == 1
        assert len(self.cache._glob_cache) == 1

        self.cache.clear_cache()

        assert len(self.cache._yaml_cache) == 0
        assert len(self.cache._glob_cache) == 0

    def test_get_cache_stats(self):
        """Test cache statistics reporting."""
        # Populate caches
        self.cache._yaml_cache["/test/file1.yaml"] = CachedYAML(
            {"test": "data1"},
            123.0,
            "/test/file1.yaml",
            100,
        )
        self.cache._yaml_cache["/test/file2.yaml"] = CachedYAML(
            {"test": "data2"},
            124.0,
            "/test/file2.yaml",
            200,
        )
        self.cache._glob_cache["/test/*.yaml"] = CachedGlob(
            ["/test/file1.yaml"],
            123.0,
            "*.yaml",
        )

        stats = self.cache.get_cache_stats()

        assert stats["yaml_cache_entries"] == 2
        assert stats["glob_cache_entries"] == 1
        assert stats["yaml_cache_size_bytes"] == 300

    def test_thread_safety(self):
        """Test thread safety of cache operations."""
        import concurrent.futures
        import tempfile
        import yaml
        
        # Create a real temporary file for thread safety testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
            test_data = {'thread_test': 'data', 'value': 42}
            yaml.dump(test_data, tmp)
            tmp_path = tmp.name
        
        try:
            def load_yaml_concurrently(thread_id):
                """Load YAML file in a separate thread."""
                result = self.cache.get_yaml(tmp_path)
                return thread_id, result
            
            # Test concurrent access with multiple threads
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(load_yaml_concurrently, i) for i in range(10)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Verify all threads got the same data
            assert len(results) == 10
            for thread_id, result in results:
                assert result == test_data
                
            # Verify cache has only one entry for the file
            assert len(self.cache._yaml_cache) == 1
            assert tmp_path in self.cache._yaml_cache
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_path)

    def test_memory_management_large_cache(self):
        """Test cache behavior with large numbers of entries."""
        # Add many cache entries
        for i in range(1000):
            key = f"/test/file_{i}.yaml"
            content = {"index": i, "data": "x" * 100}  # Some content size
            cached_item = CachedYAML(content, time.time(), key, len(str(content)))
            self.cache._yaml_cache[key] = cached_item

        # Verify cache can handle large numbers of entries
        stats = self.cache.get_cache_stats()
        assert stats["yaml_cache_entries"] == 1000
        assert stats["yaml_cache_size_bytes"] > 0

        # Test clearing large cache
        self.cache.clear_cache()
        stats_after_clear = self.cache.get_cache_stats()
        assert stats_after_clear["yaml_cache_entries"] == 0
        assert stats_after_clear["yaml_cache_size_bytes"] == 0


class TestYAMLCacheIntegration:
    """Integration tests using real files."""

    def test_real_yaml_file_loading(self, tmp_path):
        """Test loading and caching of real YAML files."""
        cache = YAMLCacheManager()
        cache.clear_cache()  # Start with clean cache

        # Create real YAML file
        sample_yaml_config = {"name": "test", "version": "1.0", "settings": {"debug": True}}
        yaml_file = tmp_path / "test_config.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(sample_yaml_config, f)

        # First load - should read from file
        result1 = cache.get_yaml(str(yaml_file))
        assert result1 == sample_yaml_config

        # Second load - should hit cache
        result2 = cache.get_yaml(str(yaml_file))
        assert result2 == sample_yaml_config
        assert result1 is result2  # Same object reference from cache

    def test_real_glob_discovery(self, tmp_path):
        """Test discovery of real YAML files with glob patterns."""
        cache = YAMLCacheManager()
        cache.clear_cache()

        # Create multiple YAML files
        sample_yaml_config = {"name": "test", "version": "1.0"}
        for i in range(3):
            yaml_file = tmp_path / f"config_{i}.yaml"
            with open(yaml_file, "w") as f:
                yaml.dump({**sample_yaml_config, "index": i}, f)

        # Discover files
        discovered_files = cache.discover_components(str(tmp_path) + "/config_*.yaml")

        assert len(discovered_files) == 3
        assert all(str(tmp_path) in path for path in discovered_files)
        assert all(path.endswith(".yaml") for path in discovered_files)

    def test_file_modification_detection(self, tmp_path):
        """Test cache invalidation when files are modified."""
        cache = YAMLCacheManager()
        cache.clear_cache()

        yaml_file = tmp_path / "modifiable_config.yaml"
        sample_yaml_config = {"name": "test", "version": "1.0"}

        # Create initial file
        with open(yaml_file, "w") as f:
            yaml.dump(sample_yaml_config, f)

        # Load file and verify caching
        result1 = cache.get_yaml(str(yaml_file))
        assert result1 == sample_yaml_config

        # Modify file
        time.sleep(0.01)  # Ensure different mtime
        modified_config = {**sample_yaml_config, "modified": True}
        with open(yaml_file, "w") as f:
            yaml.dump(modified_config, f)

        # Load again - should detect modification and reload
        result2 = cache.get_yaml(str(yaml_file))
        assert result2 == modified_config
        assert result2 != result1

    def test_performance_characteristics(self, tmp_path):
        """Test performance characteristics of cache operations."""
        import time
        
        cache = YAMLCacheManager()
        cache.clear_cache()

        # Create test file
        sample_yaml_config = {"name": "performance_test", "data": list(range(100))}
        yaml_file = tmp_path / "performance_test.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(sample_yaml_config, f)

        # Measure first load (file read)
        start_time = time.time()
        result1 = cache.get_yaml(str(yaml_file))
        first_load_time = time.time() - start_time

        # Measure second load (cache hit)
        start_time = time.time()
        result2 = cache.get_yaml(str(yaml_file))
        second_load_time = time.time() - start_time

        # Cache hit should be significantly faster
        assert second_load_time < first_load_time
        assert second_load_time < 0.001  # < 1ms for cache hit
        assert result1 == result2
        assert result1 is result2  # Same object reference
