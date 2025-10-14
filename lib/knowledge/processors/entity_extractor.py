"""Entity extraction from document content.

Extracts:
- Dates in multiple Brazilian formats (DD/MM/YYYY, MM/YYYY, YYYY-MM-DD)
- Monetary amounts (R$ and plain numbers with Brazilian format)
- Person names (Brazilian name patterns)
- Organization names (Ltda, S.A., EIRELI)
- Period detection from most common date
"""

from __future__ import annotations

import re

from lib.knowledge.config.processing_config import EntityExtractionConfig
from lib.models.knowledge_metadata import ExtractedEntities


class EntityExtractor:
    """Extracts entities from document content."""

    # Date patterns for Brazilian formats (order matters - match longest first)
    # Use negative lookahead/lookbehind to prevent partial matches
    DATE_PATTERNS = [
        r'(?<!\d)\d{2}/\d{2}/\d{4}(?!\d)',  # 13/10/2025 (must match first)
        r'(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)',  # 2025-10-13
        r'(?<!\d/)\d{2}/\d{4}(?!/\d)',      # 07/2025 (avoid matching from DD/MM/YYYY)
    ]

    # Monetary amount pattern (Brazilian format)
    # Matches: R$ 1.500,00 or 1.500,00 or R$1500,00
    AMOUNT_PATTERN = r'R?\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'

    # Brazilian name pattern
    # Matches capitalized words with optional "de", "da", "do", "dos"
    NAME_PATTERN = r'\b[A-ZÀ-Ú][a-zà-ú]+(?:\s+(?:de|da|do|dos|e)\s+|\s+)[A-ZÀÚ][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+)*\b'

    # Organization pattern (Brazilian companies)
    # Matches one or more capitalized words followed by Ltda, S.A., or EIRELI
    # Note: No trailing \b because S.A. ends with a period
    ORG_PATTERN = r'[A-ZÀ-Ú][a-zA-Zà-ú]+(?:\s+[A-ZÀ-Ú][a-zA-Zà-ú]+)*\s+(?:Ltda|S\.A\.|EIRELI)'

    def __init__(self, config: EntityExtractionConfig):
        """Initialize entity extractor with configuration.

        Args:
            config: Entity extraction configuration
        """
        self.extract_dates = config.extract_dates
        self.extract_amounts = config.extract_amounts
        self.extract_names = config.extract_names
        self.extract_organizations = config.extract_organizations

    def extract(self, content: str | None) -> ExtractedEntities:
        """Extract entities from content.

        Args:
            content: Document content text

        Returns:
            ExtractedEntities with all found entities
        """
        if not content:
            return ExtractedEntities()

        return ExtractedEntities(
            dates=self._extract_dates(content) if self.extract_dates else [],
            amounts=self._extract_amounts(content) if self.extract_amounts else [],
            people=self._extract_names(content) if self.extract_names else [],
            organizations=self._extract_orgs(content) if self.extract_organizations else [],
            period=self._extract_period(content) if self.extract_dates else None
        )

    def _extract_dates(self, content: str) -> list[str]:
        """Extract dates in various formats.

        Args:
            content: Document content

        Returns:
            Sorted unique list of date strings
        """
        dates = []
        for pattern in self.DATE_PATTERNS:
            dates.extend(re.findall(pattern, content))
        return sorted(set(dates))

    def _extract_amounts(self, content: str) -> list[float]:
        """Extract monetary amounts.

        Args:
            content: Document content

        Returns:
            Sorted unique list of amounts as floats
        """
        matches = re.findall(self.AMOUNT_PATTERN, content)
        amounts = []
        for match in matches:
            # Convert Brazilian format to float
            # Remove thousands separator (.) and replace decimal separator (,) with .
            cleaned = match.replace('.', '').replace(',', '.')
            try:
                amounts.append(float(cleaned))
            except ValueError:
                continue
        return sorted(set(amounts))

    def _extract_names(self, content: str) -> list[str]:
        """Extract person names.

        Args:
            content: Document content

        Returns:
            Sorted unique list of names
        """
        names = re.findall(self.NAME_PATTERN, content)
        return sorted(set(names))

    def _extract_orgs(self, content: str) -> list[str]:
        """Extract organization names.

        Args:
            content: Document content

        Returns:
            Sorted unique list of organization names
        """
        orgs = re.findall(self.ORG_PATTERN, content)
        return sorted(set(orgs))

    def _extract_period(self, content: str) -> str | None:
        """Extract most common period from dates.

        Args:
            content: Document content

        Returns:
            Most common period string or None
        """
        dates = self._extract_dates(content)
        if not dates:
            return None

        # Extract period prefixes (first 5-7 chars depending on format)
        periods = []
        for date_str in dates:
            if '/' in date_str:
                # For 07/2025 or 15/10/2025, take first 5 chars (07/20 or 15/10)
                periods.append(date_str[:5])
            elif '-' in date_str:
                # For 2025-10-13, take first 7 chars (2025-10)
                periods.append(date_str[:7])

        if periods:
            # Return most common period
            return max(set(periods), key=periods.count)

        return None


__all__ = ["EntityExtractor"]
