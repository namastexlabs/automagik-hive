#!/usr/bin/env python3
"""Remove hardcoded emojis from logger statements to let automatic emoji system work.

This script removes emoji prefixes from logger statements since the logging system
now automatically injects emojis based on YAML configuration and file context.
"""

import re
from pathlib import Path

from lib.logging import logger


def get_emoji_pattern():
    """Get regex pattern to match emoji characters."""
    return re.compile(
        r"^([🔧📊🤖📱🔐🌐⚡🐛✅❌⚠️🚨🔍💾📄📋🚀🎯💡🔄🗄️📖📜🧪📚⚙️🎨🔑👥💗📢]+\s*)",
    )


def remove_emojis_from_logger_calls(file_path: Path) -> bool:
    """Remove hardcoded emojis from logger calls in a Python file.

    Args:
        file_path: Path to Python file

    Returns:
        True if file was modified, False otherwise
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        original_content = content
        get_emoji_pattern()

        # Pattern to match logger calls with hardcoded emojis
        logger_pattern = re.compile(
            r'(logger\.(debug|info|warning|error)\s*\(\s*["\'])(([🔧📊🤖📱🔐🌐⚡🐛✅❌⚠️🚨🔍💾📄📋🚀🎯💡🔄🗄️📖📜🧪📚⚙️🎨🔑👥💗📢]+)\s*)([^"\']*["\'])',
            re.MULTILINE,
        )

        def replace_logger_emoji(match):
            prefix = match.group(1)  # logger.info("
            match.group(3)  # emoji characters + space
            message_part = match.group(5)  # rest of message + closing quote

            # Remove the emoji part, keeping the rest
            return f"{prefix}{message_part}"

        # Remove emojis from logger calls
        content = logger_pattern.sub(replace_logger_emoji, content)

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False

    except Exception:
        return False


def find_python_files_with_emojis(root_dir: Path) -> list[Path]:
    """Find Python files that contain hardcoded emojis in logger calls."""
    emoji_files = []
    get_emoji_pattern()

    for py_file in root_dir.rglob("*.py"):
        # Skip certain directories
        if any(
            skip in str(py_file)
            for skip in [".git", "__pycache__", "venv", ".venv", "node_modules"]
        ):
            continue

        try:
            with open(py_file, encoding="utf-8") as f:
                content = f.read()

            # Look for logger calls with emojis
            logger_with_emoji = re.search(
                r'logger\.(debug|info|warning|error)\s*\(\s*["\'][🔧📊🤖📱🔐🌐⚡🐛✅❌⚠️🚨🔍💾📄📋🚀🎯💡🔄🗄️📖📜🧪📚⚙️🎨🔑👥💗📢]',
                content,
            )

            if logger_with_emoji:
                emoji_files.append(py_file)

        except Exception:
            continue

    return emoji_files


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent

    logger.info("Removing hardcoded emojis from logger statements...")
    logger.info("This allows the automatic YAML-driven emoji system to work properly.")

    # Find files with hardcoded emojis
    emoji_files = find_python_files_with_emojis(project_root)

    if not emoji_files:
        logger.info("No hardcoded emojis found in logger statements!")
        return

    logger.info(f"Found {len(emoji_files)} files with hardcoded emojis:")
    for file_path in emoji_files:
        rel_path = file_path.relative_to(project_root)
        logger.info(f"  {rel_path}")

    logger.info(f"Processing {len(emoji_files)} files...")

    modified_count = 0
    for file_path in emoji_files:
        rel_path = file_path.relative_to(project_root)
        if remove_emojis_from_logger_calls(file_path):
            logger.info(f"  Modified {rel_path}")
            modified_count += 1
        else:
            logger.info(f"  Skipped {rel_path} (no changes needed)")

    logger.info(f"Completed! Modified {modified_count} files.")
    logger.info("The automatic emoji system will now inject emojis based on:")
    logger.info("  File path context (lib/ = lib, api/ = api, etc.)")
    logger.info("  Message keywords (database = database, auth = auth, etc.)")
    logger.info("  YAML configuration at lib/config/emoji_mappings.yaml")


if __name__ == "__main__":
    main()
