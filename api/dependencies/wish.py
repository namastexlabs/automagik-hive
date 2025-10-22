"""Dependencies for accessing Genie wish metadata."""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel

from lib.config.settings import settings

TITLE_PATTERN = re.compile(r"^#+\s*(?P<title>.+?)\s*$")
STATUS_PATTERN = re.compile(r"^\*\*Status:\*\*\s*(?P<status>.+?)\s*$", re.IGNORECASE)


class WishMetadata(BaseModel):
    """Structured representation of a wish document."""

    id: str
    title: str
    status: str
    path: str


def _discover_wish_files(base_path: Path) -> Iterable[Path]:
    """Yield wish markdown files from the Genie workspace."""

    if not base_path.exists():
        return []

    return sorted(base_path.glob("*-wish.md"))


def _extract_title(lines: list[str], default: str) -> str:
    for line in lines:
        match = TITLE_PATTERN.match(line.strip())
        if match:
            return match.group("title").strip()
    return default


def _extract_status(lines: list[str]) -> str:
    for line in lines:
        match = STATUS_PATTERN.match(line.strip())
        if match:
            return match.group("status").strip()
    return "UNKNOWN"


def _parse_wish_file(path: Path, project_root: Path) -> WishMetadata:
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    default_title = path.stem.replace("-", " ").title()

    title = _extract_title(raw_lines, default=default_title)
    status = _extract_status(raw_lines)

    relative_path = str(path.relative_to(project_root))

    return WishMetadata(
        id=path.stem,
        title=title,
        status=status,
        path=relative_path,
    )


def get_wish_catalog() -> list[WishMetadata]:
    """Load wish metadata for FastAPI dependencies."""

    project_root = settings().project_root
    wishes_dir = project_root / "genie" / "wishes"

    wish_files = _discover_wish_files(wishes_dir)
    if not wish_files:
        return []

    return [_parse_wish_file(path, project_root) for path in wish_files]
