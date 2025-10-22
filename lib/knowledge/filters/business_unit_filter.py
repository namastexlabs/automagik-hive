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
        self.business_units: dict[str, Any] = business_units_cfg if isinstance(business_units_cfg, dict) else {}

        search_cfg = self.config.get("search_config", {}) if isinstance(self.config, dict) else {}
        self.search_config: dict[str, Any] = search_cfg if isinstance(search_cfg, dict) else {}

        perf_cfg = self.config.get("performance", {}) if isinstance(self.config, dict) else {}
        self.performance: dict[str, Any] = perf_cfg if isinstance(perf_cfg, dict) else {}

        # Build keyword lookup maps for faster filtering
        self._build_keyword_maps()

        logger.info(
            "Business unit filter initialized",
            business_units=len(self.business_units),
            total_keywords=sum(len(bu.get("keywords", [])) for bu in self.business_units.values()),
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
            "enable_hybrid_search": self.search_config.get("enable_hybrid_search", True),
            "use_semantic_search": self.search_config.get("use_semantic_search", True),
        }

    def get_performance_settings(self) -> dict[str, Any]:
        """Get performance settings from configuration."""
        return {
            "cache_ttl": self.performance.get("cache_ttl", 300),
            "enable_caching": self.performance.get("enable_caching", True),
            "cache_max_size": self.performance.get("cache_max_size", 1000),
        }

    def filter_documents_by_business_unit(self, documents: list[Any], target_unit: str) -> list[Any]:
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
        return {unit_id: unit_data["name"] for unit_id, unit_data in self.business_unit_keywords.items()}


def test_config_filter() -> None:
    """Test function to demonstrate BusinessUnitFilter functionality."""
    # Create filter instance
    filter_instance = BusinessUnitFilter()

    logger.info("Testing BusinessUnitFilter functionality")

    # Test business unit detection
    test_texts = [
        "I need help with payment processing issues",
        "My account has problems and I need support",
        "Terminal configuration for merchant services",
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

    logger.info(
        "Configuration retrieved",
        search_params=search_params,
        performance_settings=performance_settings,
        business_units=business_units,
    )


# --- Test patchability helper -------------------------------------------------
def load_global_knowledge_config() -> dict[str, Any]:
    """Expose config loader for unit-test patching.

    Tests expect to patch `lib.knowledge.filters.business_unit_filter.load_global_knowledge_config`.
    Delegate to the canonical loader while keeping a module-local symbol.
    """
    config = config_aware_filter.load_global_knowledge_config()
    return cast(dict[str, Any], config if isinstance(config, dict) else {})


__all__ = [
    "BusinessUnitFilter",
    "load_global_knowledge_config",
]
