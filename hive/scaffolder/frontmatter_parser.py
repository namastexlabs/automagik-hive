"""Markdown frontmatter parser for YAML extraction."""

import re
from pathlib import Path
from typing import Any

import yaml

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)^---\s*\n(.*)$", re.DOTALL | re.MULTILINE)


def parse_markdown_frontmatter(file_path: str) -> dict[str, Any]:
    """
    Parse markdown file with YAML frontmatter.

    Args:
        file_path: Path to markdown file with frontmatter

    Returns:
        {
            "frontmatter": dict,  # Parsed YAML between --- delimiters
            "content": str        # Markdown content after frontmatter
        }

    Raises:
        ValueError: If file has no frontmatter or malformed YAML
        FileNotFoundError: If file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Markdown file not found: {file_path}")

    content = path.read_text(encoding="utf-8")
    match = FRONTMATTER_PATTERN.match(content)

    if not match:
        raise ValueError(f"No frontmatter found in {file_path}")

    yaml_content, markdown_content = match.groups()

    try:
        frontmatter = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in frontmatter: {e}")

    return {"frontmatter": frontmatter or {}, "content": markdown_content.strip()}
