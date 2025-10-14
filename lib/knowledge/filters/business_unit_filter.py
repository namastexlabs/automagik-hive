"""
Business Unit Knowledge Base Filter
Leverages the comprehensive business unit configuration for enhanced filtering
"""

from typing import Any, cast

from lib.knowledge import config_aware_filter
from lib.logging import logger


class BusinessUnitFilter:
    """
    Business unit filter that uses the comprehensive business unit configuration
    from config.yaml for intelligent keyword matching and content filtering.
    """

    def __init__(self) -> None:
        """Initialize with loaded configuration."""
        # IMPORTANT: use the module-local loader symbol so tests can patch
        # 'lib.knowledge.filters.business_unit_filter.load_global_knowledge_config'
        # directly, as expected by the test suite.
        self.config: dict[str, Any] = load_global_knowledge_config()

        # Defensive normalization in case the loaded config has unexpected shapes
        business_units_cfg = self.config.get("business_units", {}) if isinstance(self.config, dict) else {}
        self.business_units: dict[str, Any] = (
            business_units_cfg if isinstance(business_units_cfg, dict) else {}
        )

        search_cfg = self.config.get("search_config", {}) if isinstance(self.config, dict) else {}
        self.search_config: dict[str, Any] = (
            search_cfg if isinstance(search_cfg, dict) else {}
        )

        perf_cfg = self.config.get("performance", {}) if isinstance(self.config, dict) else {}
        self.performance: dict[str, Any] = (
            perf_cfg if isinstance(perf_cfg, dict) else {}
        )

        # Build keyword lookup maps for faster filtering
        self._build_keyword_maps()

        logger.info(
            "Business unit filter initialized",
            business_units=len(self.business_units),
            total_keywords=sum(
                len(bu.get("keywords", [])) for bu in self.business_units.values()
            ),
        )

    def _build_keyword_maps(self) -> None:
        """Build optimized keyword lookup maps for fast filtering."""
        self.keyword_to_business_unit: dict[str, list[str]] = {}
        self.business_unit_keywords: dict[str, dict[str, Any]] = {}

        # Guard against malformed business units configuration
        if not isinstance(self.business_units, dict):
            return

        for unit_id, unit_config in self.business_units.items():
            if not isinstance(unit_config, dict):
                # Skip malformed entries gracefully
                continue

            unit_name = unit_config.get("name", unit_id)
            keywords = unit_config.get("keywords", []) or []

            self.business_unit_keywords[unit_id] = {
                "name": unit_name,
                "keywords": keywords,
                "expertise": unit_config.get("expertise", []) or [],
                "common_issues": unit_config.get("common_issues", []) or [],
            }

            # Build reverse lookup
            for keyword in keywords:
                if keyword not in self.keyword_to_business_unit:
                    self.keyword_to_business_unit[keyword] = []
                self.keyword_to_business_unit[keyword].append(unit_id)

    def detect_business_unit_from_text(self, text: str) -> str | None:
        """
        Detect the most likely business unit based on keyword matching.

        Args:
            text: Text content to analyze

        Returns:
            Business unit ID with highest keyword match score, or None
        """
        if not text:
            return None

        text_lower = text.lower()
        unit_scores: dict[str, dict[str, Any]] = {}

        # Score each business unit based on keyword matches
        for unit_id, unit_data in self.business_unit_keywords.items():
            score = 0
            matched_keywords: list[str] = []

            for keyword in unit_data["keywords"]:
                if keyword.lower() in text_lower:
                    score += 1
                    matched_keywords.append(keyword)

            if score > 0:
                unit_scores[unit_id] = {
                    "score": score,
                    "matched_keywords": matched_keywords,
                    "name": unit_data["name"],
                }

        if not unit_scores:
            return None

        # Return the unit with highest score
        best_unit = max(unit_scores.items(), key=lambda x: x[1]["score"])
        best_unit_id, best_data = best_unit

        logger.debug(
            "Business unit detected",
            text_preview=text[:50] + "...",
            detected_unit=best_data["name"],
            score=best_data["score"],
            matched_keywords=best_data["matched_keywords"][:5],
        )  # Log first 5 matches

        return best_unit_id

    def get_search_params(self) -> dict[str, Any]:
        """Get search parameters from configuration."""
        return {
            "max_results": self.search_config.get("max_results", 3),
            "relevance_threshold": self.search_config.get("relevance_threshold", 0.7),
            "enable_hybrid_search": self.search_config.get(
                "enable_hybrid_search", True
            ),
            "use_semantic_search": self.search_config.get("use_semantic_search", True),
        }

    def get_performance_settings(self) -> dict[str, Any]:
        """Get performance settings from configuration."""
        return {
            "cache_ttl": self.performance.get("cache_ttl", 300),
            "enable_caching": self.performance.get("enable_caching", True),
            "cache_max_size": self.performance.get("cache_max_size", 1000),
        }

    def filter_documents_by_business_unit(
        self, documents: list[Any], target_unit: str
    ) -> list[Any]:
        """
        Filter documents to only include those matching the target business unit.

        Args:
            documents: List of document objects
            target_unit: Business unit ID to filter for

        Returns:
            Filtered list of documents
        """
        if target_unit not in self.business_unit_keywords:
            logger.warning("Unknown business unit for filtering", unit=target_unit)
            return documents

        filtered_docs: list[Any] = []

        for doc in documents:
            # Check existing metadata first
            if hasattr(doc, "meta_data") and doc.meta_data.get("business_unit"):
                doc_unit = doc.meta_data["business_unit"].lower()
                target_name = self.business_unit_keywords[target_unit]["name"].lower()

                if target_name in doc_unit or doc_unit in target_name.lower():
                    filtered_docs.append(doc)
                    continue

            # Fall back to keyword matching
            content = getattr(doc, "content", "") or ""
            detected_unit = self.detect_business_unit_from_text(content)

            if detected_unit == target_unit:
                filtered_docs.append(doc)

        logger.info(
            "Documents filtered by business unit",
            target_unit=self.business_unit_keywords[target_unit]["name"],
            original_count=len(documents),
            filtered_count=len(filtered_docs),
        )

        return filtered_docs

    def get_business_unit_info(self, unit_id: str) -> dict[str, Any] | None:
        """Get complete information about a business unit."""
        return self.business_unit_keywords.get(unit_id)

    def list_business_units(self) -> dict[str, str]:
        """List all available business units."""
        return {
            unit_id: unit_data["name"]
            for unit_id, unit_data in self.business_unit_keywords.items()
        }


def test_config_filter() -> None:
    """Test function to demonstrate BusinessUnitFilter functionality."""
    # Create filter instance
    filter_instance = BusinessUnitFilter()
    
    logger.info("Testing BusinessUnitFilter functionality")
    
    # Test business unit detection
    test_texts = [
        "I need help with payment processing issues",
        "My account has problems and I need support",
        "Terminal configuration for merchant services"
    ]
    
    for text in test_texts:
        detected = filter_instance.detect_business_unit_from_text(text)
        if detected:
            unit_info = filter_instance.get_business_unit_info(detected)
            logger.info(f"Detected '{detected}' for text: '{text}'", unit_info=unit_info)
    
    # Test configuration access
    search_params = filter_instance.get_search_params()
    performance_settings = filter_instance.get_performance_settings()
    business_units = filter_instance.list_business_units()
    
    logger.info("Configuration retrieved", 
               search_params=search_params,
               performance_settings=performance_settings,
               business_units=business_units)


# --- Test patchability helper -------------------------------------------------
def load_global_knowledge_config() -> dict[str, Any]:
    """Expose config loader for unit-test patching.

    Tests expect to patch `lib.knowledge.filters.business_unit_filter.load_global_knowledge_config`.
    Delegate to the canonical loader while keeping a module-local symbol.
    """
    config = config_aware_filter.load_global_knowledge_config()
    return cast(dict[str, Any], config if isinstance(config, dict) else {})


def filter_by_document_type(
    documents: list[Any],
    document_type: str | list[str]
) -> list[Any]:
    """
    Filter documents by document type.

    Args:
        documents: List of documents to filter
        document_type: Single type or list of types to match
            Valid types: financial, report, invoice, contract, manual

    Returns:
        Filtered list of documents matching specified type(s)
    """
    if not documents:
        return []

    # Normalize to list
    target_types = [document_type] if isinstance(document_type, str) else document_type
    target_types = [t.lower() for t in target_types]

    filtered = []
    for doc in documents:
        meta = doc.meta_data or {}
        doc_type = meta.get("document_type", "").lower()

        if doc_type in target_types:
            filtered.append(doc)

    return filtered


def filter_by_document_types(
    documents: list[Any],
    document_types: list[str]
) -> list[Any]:
    """
    Filter documents by multiple document types.

    Args:
        documents: List of documents to filter
        document_types: List of types to match

    Returns:
        Filtered list of documents matching any of the specified types
    """
    return filter_by_document_type(documents, document_types)


def _normalize_date(date_str: str) -> str | None:
    """Normalize date to YYYY-MM-DD format for comparison."""
    if not date_str:
        return None

    try:
        # Try MM/YYYY
        if len(date_str) == 7 and "/" in date_str:
            month, year = date_str.split("/")
            return f"{year}-{month.zfill(2)}-01"

        # Try DD/MM/YYYY
        if len(date_str) == 10 and date_str.count("/") == 2:
            day, month, year = date_str.split("/")
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        # Try YYYY-MM-DD (already normalized)
        if len(date_str) == 10 and "-" in date_str:
            return date_str

        # Try YYYY-MM (period format)
        if len(date_str) == 7 and "-" in date_str:
            return f"{date_str}-01"

    except Exception:
        return None

    return None


def _date_in_range(date_str: str, start: str | None, end: str | None, year: str | None) -> bool:
    """Check if date falls within range."""
    if not date_str:
        return False

    # Year filtering
    if year and year in date_str:
        return True

    # Normalize date for comparison
    normalized = _normalize_date(date_str)
    if not normalized:
        return False

    # Range filtering
    if start:
        start_norm = _normalize_date(start)
        if start_norm and normalized < start_norm:
            return False

    if end:
        end_norm = _normalize_date(end)
        if end_norm and normalized > end_norm:
            return False

    return True


def filter_by_date_range(
    documents: list[Any],
    start: str | None = None,
    end: str | None = None,
    year: str | None = None
) -> list[Any]:
    """
    Filter documents by date range.

    Supports multiple date formats:
    - MM/YYYY (e.g., "07/2025")
    - DD/MM/YYYY (e.g., "15/07/2025")
    - YYYY-MM-DD (e.g., "2025-07-15")
    - YYYY-MM (e.g., "2025-07") via period field

    Args:
        documents: List of documents to filter
        start: Start date (inclusive)
        end: End date (inclusive)
        year: Year to filter (e.g., "2025")

    Returns:
        Filtered list of documents within date range
    """
    if not documents:
        return []

    filtered = []
    for doc in documents:
        meta = doc.meta_data or {}

        # Get dates from extracted_entities or period field
        entities = meta.get("extracted_entities", {})
        dates = entities.get("dates", [])
        period = meta.get("period")

        # Check period field first (YYYY-MM format)
        if period and _date_in_range(period, start, end, year):
            filtered.append(doc)
            continue

        # Check extracted dates
        for date in dates:
            if _date_in_range(date, start, end, year):
                filtered.append(doc)
                break

    return filtered


def filter_by_year(documents: list[Any], year: str) -> list[Any]:
    """
    Filter documents by year.

    Args:
        documents: List of documents to filter
        year: Year to filter (e.g., "2025")

    Returns:
        Filtered list of documents from the specified year
    """
    return filter_by_date_range(documents, year=year)


def filter_by_period(documents: list[Any], period: str) -> list[Any]:
    """
    Filter documents by period field (YYYY-MM format).

    Args:
        documents: List of documents to filter
        period: Period to match (e.g., "2025-07")

    Returns:
        Filtered list of documents with matching period
    """
    if not documents:
        return []

    filtered = []
    for doc in documents:
        meta = doc.meta_data or {}
        doc_period = meta.get("period")

        if doc_period == period:
            filtered.append(doc)

    return filtered


def filter_by_amount_range(
    documents: list[Any],
    min_amount: float | None = None,
    max_amount: float | None = None
) -> list[Any]:
    """
    Filter documents by amount range.

    Includes documents that have at least one amount within the range
    AND whose maximum amount does not exceed max_amount.

    Args:
        documents: List of documents to filter
        min_amount: Minimum amount (inclusive)
        max_amount: Maximum amount (inclusive)

    Returns:
        Filtered list of documents with amounts in range
    """
    if not documents:
        return []

    filtered = []
    for doc in documents:
        meta = doc.meta_data or {}
        entities = meta.get("extracted_entities", {})
        amounts = entities.get("amounts", [])

        if not amounts:
            continue

        # Check if max amount exceeds the limit
        if max_amount is not None and max(amounts) > max_amount:
            continue

        # Check if any amount is in range
        has_amount_in_range = False
        for amount in amounts:
            in_range = True
            if min_amount is not None and amount < min_amount:
                in_range = False
            if max_amount is not None and amount > max_amount:
                in_range = False

            if in_range:
                has_amount_in_range = True
                break

        if has_amount_in_range:
            filtered.append(doc)

    return filtered


def filter_by_minimum_amount(documents: list[Any], min_amount: float) -> list[Any]:
    """
    Filter documents by minimum amount.

    Args:
        documents: List of documents to filter
        min_amount: Minimum amount (inclusive)

    Returns:
        Filtered list of documents with amounts >= min_amount
    """
    return filter_by_amount_range(documents, min_amount=min_amount)


def filter_by_maximum_amount(documents: list[Any], max_amount: float) -> list[Any]:
    """
    Filter documents by maximum amount.

    Returns documents where ALL amounts are <= max_amount.

    Args:
        documents: List of documents to filter
        max_amount: Maximum amount (inclusive)

    Returns:
        Filtered list of documents with ALL amounts <= max_amount
    """
    if not documents:
        return []

    filtered = []
    for doc in documents:
        meta = doc.meta_data or {}
        entities = meta.get("extracted_entities", {})
        amounts = entities.get("amounts", [])

        if not amounts:
            continue

        # Check if ALL amounts are <= max_amount
        if all(amount <= max_amount for amount in amounts):
            filtered.append(doc)

    return filtered


def filter_by_person(documents: list[Any], person_name: str) -> list[Any]:
    """Filter documents mentioning specific person (case-insensitive partial match)."""
    if not documents or not person_name:
        return []

    person_lower = person_name.lower()
    filtered = []

    for doc in documents:
        meta = doc.meta_data or {}
        entities = meta.get("extracted_entities", {})
        people = entities.get("people", [])

        for person in people:
            if person_lower in person.lower():
                filtered.append(doc)
                break

    return filtered


def filter_by_organization(documents: list[Any], org_name: str) -> list[Any]:
    """Filter documents mentioning specific organization (case-insensitive partial match)."""
    if not documents or not org_name:
        return []

    org_lower = org_name.lower()
    filtered = []

    for doc in documents:
        meta = doc.meta_data or {}
        entities = meta.get("extracted_entities", {})
        orgs = entities.get("organizations", [])

        for org in orgs:
            if org_lower in org.lower():
                filtered.append(doc)
                break

    return filtered


def filter_by_custom_entity(
    documents: list[Any],
    entity_type: str,
    entity_value: str
) -> list[Any]:
    """
    Filter documents by custom entity types.

    Args:
        documents: List of documents to filter
        entity_type: Type of entity (e.g., "products", "locations")
        entity_value: Value to match

    Returns:
        Filtered list of documents with matching custom entities
    """
    if not documents or not entity_type or not entity_value:
        return []

    entity_value_lower = entity_value.lower()
    filtered = []

    for doc in documents:
        meta = doc.meta_data or {}
        entities = meta.get("extracted_entities", {})
        entity_list = entities.get(entity_type, [])

        for entity in entity_list:
            if entity_value_lower in str(entity).lower():
                filtered.append(doc)
                break

    return filtered


def apply_filters(
    documents: list[Any],
    document_type: str | list[str] | None = None,
    date_range: tuple[str, str] | None = None,
    year: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    person: str | None = None,
    organization: str | None = None
) -> list[Any]:
    """
    Apply multiple filters to documents.

    Args:
        documents: List of documents to filter
        document_type: Filter by type(s)
        date_range: Tuple of (start, end) dates
        year: Filter by year
        min_amount: Minimum amount
        max_amount: Maximum amount
        person: Person name to match
        organization: Organization name to match

    Returns:
        Filtered list of documents matching ALL criteria
    """
    filtered = documents

    if document_type:
        filtered = filter_by_document_type(filtered, document_type)

    if date_range:
        start, end = date_range
        filtered = filter_by_date_range(filtered, start=start, end=end)
    elif year:
        filtered = filter_by_date_range(filtered, year=year)

    if min_amount is not None or max_amount is not None:
        filtered = filter_by_amount_range(filtered, min_amount, max_amount)

    if person:
        filtered = filter_by_person(filtered, person)

    if organization:
        filtered = filter_by_organization(filtered, organization)

    return filtered


__all__ = [
    "BusinessUnitFilter",
    "load_global_knowledge_config",
    "filter_by_document_type",
    "filter_by_document_types",
    "filter_by_date_range",
    "filter_by_year",
    "filter_by_period",
    "filter_by_amount_range",
    "filter_by_minimum_amount",
    "filter_by_maximum_amount",
    "filter_by_person",
    "filter_by_organization",
    "filter_by_custom_entity",
    "apply_filters",
]
