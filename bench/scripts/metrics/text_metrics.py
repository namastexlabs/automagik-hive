"""Text quality metrics for PDF extraction benchmarking."""

import re
from typing import Optional
from rapidfuzz import fuzz
import unicodedata


def calculate_text_quality(
    extracted: str,
    ground_truth: str
) -> dict[str, float]:
    """Calculate text quality metrics.

    Args:
        extracted: Extracted text from PDF
        ground_truth: Ground truth text

    Returns:
        Dictionary of quality metrics
    """
    # Character-level F1 using fuzzy matching
    char_similarity = fuzz.ratio(extracted, ground_truth) / 100.0

    # Paragraph break consistency
    para_consistency = calculate_paragraph_consistency(extracted, ground_truth)

    # Unicode preservation (Brazilian Portuguese focus)
    unicode_preservation = calculate_unicode_preservation(extracted, ground_truth)

    return {
        "character_similarity": char_similarity,
        "paragraph_consistency": para_consistency,
        "unicode_preservation": unicode_preservation,
        "composite_score": (
            char_similarity * 0.5 +
            para_consistency * 0.25 +
            unicode_preservation * 0.25
        )
    }


def calculate_paragraph_consistency(
    extracted: str,
    ground_truth: str
) -> float:
    """Calculate paragraph break consistency.

    Args:
        extracted: Extracted text
        ground_truth: Ground truth text

    Returns:
        Consistency score (0-1)
    """
    # Count paragraph breaks (double newlines)
    extracted_breaks = extracted.count("\n\n")
    ground_truth_breaks = ground_truth.count("\n\n")

    if ground_truth_breaks == 0:
        return 1.0 if extracted_breaks == 0 else 0.5

    # Calculate relative difference
    diff = abs(extracted_breaks - ground_truth_breaks)
    max_breaks = max(extracted_breaks, ground_truth_breaks)

    if max_breaks == 0:
        return 1.0

    consistency = 1.0 - (diff / max_breaks)
    return max(0.0, consistency)


def calculate_unicode_preservation(
    extracted: str,
    ground_truth: str
) -> float:
    """Calculate Unicode character preservation.

    Focuses on Brazilian Portuguese diacritics:
    á, é, í, ó, ú, ç, ã, õ, â, ê, ô

    Args:
        extracted: Extracted text
        ground_truth: Ground truth text

    Returns:
        Preservation score (0-1)
    """
    # Brazilian Portuguese special characters
    pt_br_chars = set("áéíóúçãõâêôÁÉÍÓÚÇÃÕÂÊÔàèìòùÀÈÌÒÙ")

    # Find all special characters in ground truth
    gt_special = [c for c in ground_truth if c in pt_br_chars]

    if not gt_special:
        return 1.0  # No special characters to preserve

    # Count preserved characters in extracted text
    preserved = 0
    extracted_special = set(extracted)

    for char in gt_special:
        if char in extracted_special:
            preserved += 1

    return preserved / len(gt_special)


def calculate_formatting_metrics(text: str) -> dict[str, int]:
    """Calculate formatting retention metrics.

    Args:
        text: Extracted text

    Returns:
        Dictionary of formatting metrics
    """
    # Count potential headings (short lines, uppercase, or trailing digits)
    heading_pattern = re.compile(r"^[A-Z0-9][^\n]{0,79}$", re.MULTILINE)
    headings = len(heading_pattern.findall(text))

    # Count list items (lines starting with bullets or numbers)
    list_pattern = re.compile(r"^[\s]*[•\-\*\d]+[\.\)]\s+", re.MULTILINE)
    lists = len(list_pattern.findall(text))

    return {
        "heading_markers": headings,
        "list_markers": lists
    }


def calculate_per_page_metrics(
    extracted_pages: list[str],
    ground_truth_pages: Optional[list[str]] = None
) -> dict[str, list[float]]:
    """Calculate per-page text quality metrics.

    Args:
        extracted_pages: List of extracted text per page
        ground_truth_pages: Optional list of ground truth text per page

    Returns:
        Dictionary of per-page metrics
    """
    if not ground_truth_pages:
        # No ground truth - return basic metrics
        return {
            "page_lengths": [len(page) for page in extracted_pages],
            "page_count": len(extracted_pages)
        }

    # Calculate quality per page
    similarities = []
    para_consistencies = []
    unicode_preservations = []

    min_pages = min(len(extracted_pages), len(ground_truth_pages))

    for i in range(min_pages):
        metrics = calculate_text_quality(
            extracted_pages[i],
            ground_truth_pages[i]
        )
        similarities.append(metrics["character_similarity"])
        para_consistencies.append(metrics["paragraph_consistency"])
        unicode_preservations.append(metrics["unicode_preservation"])

    return {
        "page_similarities": similarities,
        "page_para_consistency": para_consistencies,
        "page_unicode_preservation": unicode_preservations,
        "mean_similarity": sum(similarities) / len(similarities) if similarities else 0.0,
        "mean_para_consistency": sum(para_consistencies) / len(para_consistencies) if para_consistencies else 0.0,
        "mean_unicode_preservation": sum(unicode_preservations) / len(unicode_preservations) if unicode_preservations else 0.0,
    }
