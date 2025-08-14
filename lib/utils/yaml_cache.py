"""
YAML Cache Manager - Centralized YAML Loading with Performance Optimization

This module provides a centralized caching system for YAML file loading to eliminate
redundant file reads and parsing operations across the Automagik Hive system.

Key Features:
- File modification time tracking for cache invalidation
- Glob pattern result caching for component discovery
- Thread-safe operations for concurrent access
- Memory management with configurable cache limits
- Hot reload support for development mode
"""

import glob
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from lib.logging import logger


@dataclass
class CachedYAML:
    """Container for cached YAML content with metadata."""

    content: dict[str, Any]
    mtime: float
    file_path: str
    size_bytes: int


@dataclass
class CachedGlob:
    """Container for cached glob results with metadata."""

    file_paths: list[str]
    dir_mtime: float
    pattern: str


class YAMLCacheManager:
    """
    Centralized YAML cache manager for high-performance component loading.

    This class eliminates redundant YAML file loading by caching parsed content
    and glob discovery results with automatic cache invalidation based on file
    modification times.
    """

    def __init__(
        self, max_cache_size: int = 1000, enable_hot_reload: bool | None = None
    ):
        """
        Initialize the YAML cache manager.

        Args:
            max_cache_size: Maximum number of cached YAML files (default: 1000)
            enable_hot_reload: Enable hot reload (auto-detect from HIVE_ENVIRONMENT)
        """
        self._yaml_cache: dict[str, CachedYAML] = {}
        self._glob_cache: dict[str, CachedGlob] = {}
        self._inheritance_cache: dict[str, str] = {}  # agent_id -> team_id
        self._lock = threading.RLock()
        self._max_cache_size = max_cache_size

        # Auto-detect hot reload mode from environment
        if enable_hot_reload is None:
            env = os.getenv("HIVE_ENVIRONMENT", "development").lower()
            self._enable_hot_reload = env == "development"
        else:
            self._enable_hot_reload = enable_hot_reload

        logger.debug(
            f"🐛 🚀 YAML Cache Manager initialized (max_size={max_cache_size}, hot_reload={self._enable_hot_reload})"
        )

    def get_yaml(
        self, file_path: str, force_reload: bool = False
    ) -> dict[str, Any] | None:
        """
        Get YAML content with intelligent caching.

        Args:
            file_path: Path to YAML file (relative or absolute)
            force_reload: Force reload ignoring cache

        Returns:
            Parsed YAML content or None if file doesn't exist
        """
        # Normalize path for consistent caching
        normalized_path = os.path.abspath(file_path)

        with self._lock:
            # Check if file exists
            if not os.path.exists(normalized_path):
                logger.debug(f"🐛 📄 YAML file not found: {file_path}")
                return None

            current_mtime = os.path.getmtime(normalized_path)

            # Check cache hit and validity
            if not force_reload and normalized_path in self._yaml_cache:
                cached = self._yaml_cache[normalized_path]

                # Cache hit - check if still valid
                if cached.mtime >= current_mtime:
                    logger.debug(f"🐛 📄 YAML cache hit: {file_path}")
                    return cached.content
                logger.debug(
                    f"🐛 📄 YAML cache invalidated (file modified): {file_path}"
                )

            # Cache miss or invalidated - load from file
            try:
                logger.debug(f"🐛 📄 Loading YAML from disk: {file_path}")
                with open(normalized_path, encoding="utf-8") as f:
                    file_content = f.read()
                    content = yaml.safe_load(file_content)

                # Cache the result
                file_size = os.path.getsize(normalized_path)
                self._yaml_cache[normalized_path] = CachedYAML(
                    content=content,
                    mtime=current_mtime,
                    file_path=normalized_path,
                    size_bytes=file_size,
                )

                # Manage cache size
                self._manage_cache_size()

                logger.debug(
                    f"🐛 📄 YAML cached successfully: {file_path} ({file_size} bytes)"
                )
                return content

            except Exception as e:
                logger.error(f"🚨 📄 Failed to load YAML file {file_path}: {e}")
                return None

    def discover_components(
        self, pattern: str, force_reload: bool = False
    ) -> list[str]:
        """
        Discover component files using cached glob patterns.

        Args:
            pattern: Glob pattern (e.g., "ai/agents/*/config.yaml")
            force_reload: Force reload ignoring cache

        Returns:
            List of matching file paths
        """
        with self._lock:
            # Determine directory to watch for changes
            pattern_dir = os.path.dirname(pattern.replace("*", "dummy"))
            if os.path.exists(pattern_dir):
                current_dir_mtime = max(
                    os.path.getmtime(pattern_dir),
                    max(
                        (
                            os.path.getmtime(os.path.join(pattern_dir, item))
                            for item in os.listdir(pattern_dir)
                            if os.path.isdir(os.path.join(pattern_dir, item))
                        ),
                        default=0,
                    ),
                )
            else:
                current_dir_mtime = 0

            # Check cache hit and validity
            if not force_reload and pattern in self._glob_cache:
                cached = self._glob_cache[pattern]

                # Cache hit - check if directory structure changed
                if cached.dir_mtime >= current_dir_mtime:
                    logger.debug(
                        f"🔍 Glob cache hit: {pattern} ({len(cached.file_paths)} files)"
                    )
                    return cached.file_paths.copy()
                logger.debug(
                    f"🔍 Glob cache invalidated (directory modified): {pattern}"
                )

            # Cache miss or invalidated - scan filesystem
            try:
                logger.debug(f"🔍 Scanning filesystem: {pattern}")
                file_paths = sorted(glob.glob(pattern))

                # Cache the result
                self._glob_cache[pattern] = CachedGlob(
                    file_paths=file_paths, dir_mtime=current_dir_mtime, pattern=pattern
                )

                logger.debug(
                    f"🔍 Glob cached successfully: {pattern} ({len(file_paths)} files)"
                )
                return file_paths.copy()

            except Exception as e:
                logger.error(f"🔍 Failed to scan pattern {pattern}: {e}")
                return []

    def get_agent_team_mapping(
        self, agent_id: str, force_reload: bool = False
    ) -> str | None:
        """
        Get the team ID for an agent using cached inheritance mapping.

        Args:
            agent_id: Agent identifier
            force_reload: Force reload of inheritance cache

        Returns:
            Team ID or None if not found
        """
        with self._lock:
            if force_reload or not self._inheritance_cache:
                self._rebuild_inheritance_cache()

            return self._inheritance_cache.get(agent_id)

    def _rebuild_inheritance_cache(self):
        """Rebuild the agent -> team inheritance mapping cache."""
        logger.debug("🔗 Rebuilding inheritance cache...")
        self._inheritance_cache.clear()

        # Discover all team configs
        team_configs = self.discover_components("ai/teams/*/config.yaml")

        for team_config_path in team_configs:
            team_config = self.get_yaml(team_config_path)
            if not team_config:
                continue

            team_id = Path(team_config_path).parent.name
            members = team_config.get("members", [])

            # Map each member to this team
            for member_id in members:
                self._inheritance_cache[member_id] = team_id

        logger.debug(
            f"🐛 🔗 Inheritance cache built: {len(self._inheritance_cache)} agent mappings"
        )

    def _manage_cache_size(self):
        """Manage cache size by removing least recently used entries."""
        if len(self._yaml_cache) > self._max_cache_size:
            # Simple LRU: remove 10% of oldest entries by mtime
            entries_to_remove = int(self._max_cache_size * 0.1)
            sorted_entries = sorted(self._yaml_cache.items(), key=lambda x: x[1].mtime)

            for path, _ in sorted_entries[:entries_to_remove]:
                del self._yaml_cache[path]

            logger.debug(f"🐛 📄 Cache cleanup: removed {entries_to_remove} entries")

    def invalidate_file(self, file_path: str):
        """
        Manually invalidate a specific file in the cache.

        Args:
            file_path: Path to file to invalidate
        """
        normalized_path = os.path.abspath(file_path)
        with self._lock:
            if normalized_path in self._yaml_cache:
                del self._yaml_cache[normalized_path]
                logger.debug(f"🐛 📄 Cache invalidated: {file_path}")

    def invalidate_pattern(self, pattern: str):
        """
        Manually invalidate a glob pattern in the cache.

        Args:
            pattern: Glob pattern to invalidate
        """
        with self._lock:
            if pattern in self._glob_cache:
                del self._glob_cache[pattern]
                logger.debug(f"🔍 Glob cache invalidated: {pattern}")

    def clear_cache(self):
        """Clear all caches."""
        with self._lock:
            self._yaml_cache.clear()
            self._glob_cache.clear()
            self._inheritance_cache.clear()
            logger.debug("🗑️ All caches cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache statistics for monitoring.

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_yaml_size = sum(
                cached.size_bytes for cached in self._yaml_cache.values()
            )
            total_glob_files = sum(
                len(cached.file_paths) for cached in self._glob_cache.values()
            )

            return {
                "yaml_cache_entries": len(self._yaml_cache),
                "yaml_cache_size_bytes": total_yaml_size,
                "glob_cache_entries": len(self._glob_cache),
                "glob_total_files": total_glob_files,
                "inheritance_mappings": len(self._inheritance_cache),
                "max_cache_size": self._max_cache_size,
                "hot_reload_enabled": self._enable_hot_reload,
            }


# Global singleton instance
_yaml_cache_manager: YAMLCacheManager | None = None
_cache_lock = threading.Lock()


def get_yaml_cache_manager() -> YAMLCacheManager:
    """
    Get the global YAML cache manager singleton.

    Returns:
        Global YAMLCacheManager instance
    """
    global _yaml_cache_manager
    if _yaml_cache_manager is None:
        with _cache_lock:
            if _yaml_cache_manager is None:
                _yaml_cache_manager = YAMLCacheManager()
    return _yaml_cache_manager


def reset_yaml_cache_manager():
    """Reset the global cache manager (useful for testing)."""
    global _yaml_cache_manager
    with _cache_lock:
        _yaml_cache_manager = None


# Convenience functions for easy integration
def load_yaml_cached(
    file_path: str, force_reload: bool = False
) -> dict[str, Any] | None:
    """
    Load YAML file using the global cache manager.

    Args:
        file_path: Path to YAML file
        force_reload: Force reload ignoring cache

    Returns:
        Parsed YAML content or None if file doesn't exist
    """
    return get_yaml_cache_manager().get_yaml(file_path, force_reload)


def discover_components_cached(pattern: str, force_reload: bool = False) -> list[str]:
    """
    Discover components using the global cache manager.

    Args:
        pattern: Glob pattern
        force_reload: Force reload ignoring cache

    Returns:
        List of matching file paths
    """
    return get_yaml_cache_manager().discover_components(pattern, force_reload)


def get_agent_team_cached(agent_id: str, force_reload: bool = False) -> str | None:
    """
    Get agent team mapping using the global cache manager.

    Args:
        agent_id: Agent identifier
        force_reload: Force reload of inheritance cache

    Returns:
        Team ID or None if not found
    """
    return get_yaml_cache_manager().get_agent_team_mapping(agent_id, force_reload)
