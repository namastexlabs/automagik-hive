"""
Simple YAML-driven emoji loader for automatic logging enhancement.

No complex detection - just loads YAML once and provides simple lookups.
The logging system automatically gets emojis by checking file paths and keywords.
"""

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


class EmojiLoader:
    """Simple YAML emoji loader with automatic path/keyword matching."""

    def __init__(self, config_path: str | None = None) -> None:
        if config_path is None:
            current_dir = Path(__file__).parent
            config_path_resolved: Path = (
                current_dir.parent / "config" / "emoji_mappings.yaml"
            )
        else:
            config_path_resolved = Path(config_path)

        self.config_path = config_path_resolved
        self._config = self._load_yaml()
        self._emoji_regex = re.compile(
            r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000026FF\U00002700-\U000027BF]"
        )

    def _load_yaml(self) -> dict[str, Any]:
        """Load YAML config - fail fast if not available."""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def has_emoji(self, text: str) -> bool:
        """Check if text already has emoji."""
        return bool(self._emoji_regex.search(text))

    @lru_cache(maxsize=500)
    def get_emoji(self, file_path: str = "", message: str = "") -> str:
        """
        Get emoji for file path or message content.

        Simple priority:
        1. Directory match in file_path
        2. Keyword match in message
        3. Extension match in file_path
        4. Return empty string (no fallback)
        """
        if not self._config or not self._config.get("resource_types"):
            return ""

        resource_types: dict[str, Any] = self._config["resource_types"]

        # Skip if message already has emoji
        if message and self.has_emoji(message):
            return ""

        # 1. Directory matching - longest first
        if file_path:
            directories: dict[str, str] = resource_types.get("directories", {})
            normalized_path = file_path.replace("\\", "/")

            for directory in sorted(directories.keys(), key=len, reverse=True):
                if normalized_path.startswith(directory):
                    return directories[directory]

        # 2. Smart keyword matching (prioritize longer phrases first)
        if message:
            message_lower = message.lower()

            # Collect all keywords from activities and services
            all_keywords: dict[str, str] = {}
            all_keywords.update(resource_types.get("activities", {}))
            all_keywords.update(resource_types.get("services", {}))

            # Sort by keyword length (longest first) to prioritize specific phrases
            sorted_keywords = sorted(
                all_keywords.items(), key=lambda x: len(x[0]), reverse=True
            )

            for keyword, emoji in sorted_keywords:
                if keyword in message_lower:
                    return emoji

        # 3. File extension
        if file_path:
            extension = Path(file_path).suffix.lower()
            file_types: dict[str, str] = resource_types.get("file_types", {})
            if extension in file_types:
                return file_types[extension]

        # Return empty - no fallback
        return ""


# Global instance
_loader: EmojiLoader | None = None


def get_emoji_loader() -> EmojiLoader:
    """Get singleton emoji loader."""
    global _loader
    if _loader is None:
        _loader = EmojiLoader()
    return _loader


def auto_emoji(message: str, file_path: str = "") -> str:
    """
    Automatically add emoji to message if appropriate.

    Usage:
    logger.info(auto_emoji("Starting system", __file__))
    """
    loader = get_emoji_loader()
    emoji = loader.get_emoji(file_path, message)

    if emoji:
        return f"{emoji} {message}"
    return message


def get_path_emoji(file_path: str) -> str:
    """Get emoji for a file path."""
    loader = get_emoji_loader()
    return loader.get_emoji(file_path)


def get_keyword_emoji(text: str) -> str:
    """Get emoji for text content."""
    loader = get_emoji_loader()
    return loader.get_emoji("", text)
