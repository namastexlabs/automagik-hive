"""Content cleaning processor for knowledge documents.

Removes encoding artifacts, GLYPH patterns, HTML comments, markdown tables,
and non-English content from document pages before processing. Configurable
via YAML settings.

Based on clean_english.py patterns adapted for document processing pipeline.
"""

from __future__ import annotations

import html
import re
from typing import List

from lib.knowledge.config.processing_config import ContentCleaningConfig
from lib.logging import logger


class ContentCleaner:
    """Clean document content by removing artifacts and encoding issues.

    Processes uploaded documents to remove GLYPH artifacts, HTML comments,
    markdown tables, fix ligatures, and optionally filter non-English content.
    All features are configurable via ContentCleaningConfig.
    """

    def __init__(self, config: ContentCleaningConfig) -> None:
        """Initialize content cleaner with configuration.

        Args:
            config: ContentCleaningConfig instance with feature toggles
        """
        self.config = config
        self.enabled = config.enabled
        self.remove_glyph = config.remove_glyph
        self.remove_html_comments = config.remove_html_comments
        self.remove_markdown_tables = config.remove_markdown_tables
        self.fix_ligatures = config.fix_ligatures
        self.filter_english_only = config.filter_english_only
        self.min_vowel_tokens = config.min_vowel_tokens

    def clean(self, content: str | None) -> str:
        """Clean document content and return cleaned string.

        Args:
            content: Raw document content to clean

        Returns:
            Cleaned content string (empty string if content is None/empty)
        """
        # Handle None and empty content
        if not content:
            return ""

        if not self.enabled:
            return content

        logger.debug(
            "Cleaning document content",
            content_length=len(content),
            enabled=self.enabled,
            filter_english=self.filter_english_only
        )

        # Apply cleaning pipeline
        cleaned = self._base_cleanup(content)

        if self.filter_english_only:
            cleaned = self._filter_english_lines(cleaned)

        cleaned = self._finalize_text(cleaned)

        logger.debug(
            "Content cleaning completed",
            original_length=len(content),
            cleaned_length=len(cleaned),
            reduction_pct=round((1 - len(cleaned) / len(content)) * 100, 2) if content else 0
        )

        return cleaned

    def _base_cleanup(self, text: str) -> str:
        """First pass: strip GLYPH, HTML comments, tables, normalize spacing.

        Args:
            text: Input text to clean

        Returns:
            Cleaned text after base cleanup
        """
        # Unescape HTML entities
        t = html.unescape(text)

        # Remove GLYPH artifacts (raw GLYPH and GLYPH<...>)
        if self.remove_glyph:
            t = re.sub(r'GLYPH(?:<[^>]*>)?', '', t)

        # Remove HTML comments
        if self.remove_html_comments:
            t = re.sub(r'<!--.*?-->', '', t, flags=re.S)

        # Remove markdown table rows entirely
        if self.remove_markdown_tables:
            t = re.sub(r'(?m)^\|.*$', '', t)

        # Collapse runs of spaces/tabs to single space
        t = re.sub(r'[ \t]{2,}', ' ', t)

        # Fix odd spacing/ligatures (e.g., "Be ĳ ing" → "Beijing")
        if self.fix_ligatures:
            t = re.sub(r'\bBe\s*ĳ\s*ing\b', 'Beijing', t)

        return t

    def _is_english_line(self, s: str) -> bool:
        """Heuristic filter: keep readable English, drop encoding junk.

        Uses vowel-bearing token counting and pattern detection to identify
        valid English content vs. encoding artifacts.

        Args:
            s: Line to check

        Returns:
            True if line appears to be valid English content
        """
        s = s.strip()
        if not s:
            return False

        # Drop lines beginning with asterisks + likely junk
        if re.match(r'^\*["A-Z]', s):
            return False

        # Drop lines that mix letters and digits (catches 8IBU noise)
        if re.search(r'[A-Za-z]\d|\d[A-Za-z]', s):
            return False

        # Drop lines containing a parenthesis followed by a long uppercase token
        # e.g., "(JWFIJN IFSUIFCPPLQFBTF"
        if re.search(r'\([A-Z]{3,}', s):
            return False

        # Tokenize words and compute vowel-bearing tokens
        words = re.findall(r"[A-Za-z]+'?[A-Za-z]*", s)
        vowel_tokens = [w for w in words if re.search(r'[aeiouAEIOU]', w)]

        # Compute uppercase no-vowel tokens (likely gibberish) of length >= 4
        up_no_vowel = [
            w for w in words
            if w.isupper() and len(w) >= 4 and not re.search(r'[AEIOU]', w)
        ]

        # If the line is dominated by uppercase no-vowel tokens, drop it
        if words and (len(up_no_vowel) / max(1, len(words)) > 0.5 or len(up_no_vowel) >= 2):
            return False

        # Keep markdown headers with vowels
        if s.startswith('#') and vowel_tokens:
            return True

        # Keep lines with at least min_vowel_tokens vowel-bearing tokens
        if len(vowel_tokens) >= self.min_vowel_tokens:
            return True

        # Keep short statements/questions with at least one vowel-bearing token
        if (s.endswith('?') or s.endswith('.')) and len(vowel_tokens) >= 1:
            return True

        return False

    def _filter_english_lines(self, text: str) -> str:
        """Filter text to keep only English-looking lines.

        Args:
            text: Input text

        Returns:
            Filtered text with only valid English lines
        """
        kept_lines: List[str] = []
        for line in text.splitlines():
            if self._is_english_line(line):
                kept_lines.append(line.rstrip())
        return "\n".join(kept_lines)

    def _finalize_text(self, text: str) -> str:
        """Normalize blank lines and common apostrophe spacing.

        Args:
            text: Input text

        Returns:
            Finalized text with normalized formatting
        """
        # Collapse 3+ blank lines to just two
        text = re.sub(r'\n{3,}', '\n\n', text).strip()
        # Fix spacing before possessive 's
        text = re.sub(r"\s+'s\b", "'s", text)
        return text


__all__ = ["ContentCleaner"]
