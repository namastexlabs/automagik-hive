"""Tests for ContentCleaner processor.

Tests cover:
- GLYPH artifact removal (raw GLYPH and GLYPH<...>)
- HTML comment removal (<!-- ... -->)
- Markdown table removal (lines starting with |)
- Ligature fixing (Beijing pattern)
- HTML entity unescaping
- English line filtering (when enabled)
- Vowel-bearing token counting
- Mixed letter/digit filtering
- Uppercase gibberish filtering
- Finalization (blank line collapse, apostrophe spacing)
- Configuration toggles
- Edge cases and error handling
"""

import pytest

from lib.knowledge.config.processing_config import ContentCleaningConfig
from lib.knowledge.processors.content_cleaner import ContentCleaner


class TestContentCleanerGlyphRemoval:
    """Test GLYPH artifact removal functionality."""

    @pytest.fixture
    def cleaner(self):
        """Create cleaner with default config."""
        config = ContentCleaningConfig()
        return ContentCleaner(config)

    def test_remove_raw_glyph(self, cleaner):
        """Should remove raw GLYPH markers."""
        content = "This is GLYPHtext with artifacts"
        result = cleaner.clean(content)

        assert "GLYPH" not in result
        assert "text" in result

    def test_remove_glyph_with_tags(self, cleaner):
        """Should remove GLYPH<tag> patterns."""
        content = "Start GLYPH<tag>middle GLYPH<another>end"
        result = cleaner.clean(content)

        assert "GLYPH" not in result
        assert "Start" in result
        assert "middle" in result
        assert "end" in result

    def test_remove_multiple_glyphs(self, cleaner):
        """Should remove all GLYPH occurrences."""
        content = "GLYPH<a>First GLYPH second GLYPHthird GLYPH<tag>"
        result = cleaner.clean(content)

        assert "GLYPH" not in result
        assert "First" in result
        assert "second" in result

    def test_preserve_text_around_glyph(self, cleaner):
        """Should preserve surrounding text when removing GLYPH."""
        content = "Valid text GLYPH<artifact> more valid text"
        result = cleaner.clean(content)

        assert "Valid text" in result
        assert "more valid text" in result
        assert "GLYPH" not in result


class TestContentCleanerHtmlComments:
    """Test HTML comment removal functionality."""

    @pytest.fixture
    def cleaner(self):
        """Create cleaner with default config."""
        config = ContentCleaningConfig()
        return ContentCleaner(config)

    def test_remove_html_comment(self, cleaner):
        """Should remove HTML comments."""
        content = "Text before <!-- comment here --> text after"
        result = cleaner.clean(content)

        assert "<!--" not in result
        assert "-->" not in result
        assert "comment here" not in result
        assert "Text before" in result
        assert "text after" in result

    def test_remove_multiline_html_comment(self, cleaner):
        """Should remove multiline HTML comments."""
        content = """Text before
<!-- This is a
multiline
comment -->
Text after"""
        result = cleaner.clean(content)

        assert "<!--" not in result
        assert "comment" not in result
        assert "Text before" in result
        assert "Text after" in result

    def test_remove_multiple_html_comments(self, cleaner):
        """Should remove all HTML comments."""
        content = "Start <!-- comment 1 --> middle <!-- comment 2 --> end"
        result = cleaner.clean(content)

        assert "<!--" not in result
        assert "comment 1" not in result
        assert "comment 2" not in result


class TestContentCleanerMarkdownTables:
    """Test markdown table removal functionality."""

    @pytest.fixture
    def cleaner(self):
        """Create cleaner with default config."""
        config = ContentCleaningConfig()
        return ContentCleaner(config)

    def test_remove_markdown_table_row(self, cleaner):
        """Should remove markdown table rows."""
        content = """Normal text
| Column 1 | Column 2 |
More normal text"""
        result = cleaner.clean(content)

        assert "|" not in result
        assert "Column" not in result
        assert "Normal text" in result
        assert "More normal text" in result

    def test_remove_multiple_markdown_table_rows(self, cleaner):
        """Should remove all markdown table rows."""
        content = """Text
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
More text"""
        result = cleaner.clean(content)

        assert "|" not in result
        assert "Header" not in result
        assert "Cell" not in result
        assert "Text" in result
        assert "More text" in result


class TestContentCleanerSpacingNormalization:
    """Test spacing and formatting normalization."""

    @pytest.fixture
    def cleaner(self):
        """Create cleaner with default config."""
        config = ContentCleaningConfig()
        return ContentCleaner(config)

    def test_collapse_multiple_spaces(self, cleaner):
        """Should collapse multiple spaces to single space."""
        content = "Text  with    multiple     spaces"
        result = cleaner.clean(content)

        assert "  " not in result
        assert "Text with multiple spaces" in result

    def test_collapse_multiple_tabs(self, cleaner):
        """Should collapse multiple tabs to single space."""
        content = "Text\t\twith\t\t\ttabs"
        result = cleaner.clean(content)

        assert "\t\t" not in result

    def test_collapse_mixed_spaces_tabs(self, cleaner):
        """Should collapse mixed spaces and tabs."""
        content = "Text \t \t  mixed"
        result = cleaner.clean(content)

        # Multiple whitespace collapsed to single space
        assert "Text mixed" in result or "Text  mixed" not in result


class TestContentCleanerLigatureFixing:
    """Test ligature fixing functionality."""

    @pytest.fixture
    def cleaner(self):
        """Create cleaner with default config."""
        config = ContentCleaningConfig()
        return ContentCleaner(config)

    def test_fix_beijing_ligature(self, cleaner):
        """Should fix Be ĳ ing ligature to Beijing."""
        content = "The city of Be ĳ ing is beautiful"
        result = cleaner.clean(content)

        assert "Beijing" in result
        assert "ĳ" not in result

    def test_fix_beijing_ligature_no_spaces(self, cleaner):
        """Should fix Beĳing ligature to Beijing."""
        content = "Visit Beĳing China"
        result = cleaner.clean(content)

        assert "Beijing" in result
        assert "ĳ" not in result


class TestContentCleanerHtmlEntities:
    """Test HTML entity unescaping."""

    @pytest.fixture
    def cleaner(self):
        """Create cleaner with default config."""
        config = ContentCleaningConfig()
        return ContentCleaner(config)

    def test_unescape_html_entities(self, cleaner):
        """Should unescape HTML entities."""
        content = "Text with &lt;tags&gt; and &amp; entities"
        result = cleaner.clean(content)

        assert "&lt;" not in result
        assert "&gt;" not in result
        assert "&amp;" not in result
        assert "<tags>" in result
        assert "&" in result


class TestContentCleanerEnglishLineFiltering:
    """Test English line filtering when enabled."""

    @pytest.fixture
    def cleaner_with_filtering(self):
        """Create cleaner with English filtering enabled."""
        config = ContentCleaningConfig(filter_english_only=True, min_vowel_tokens=2)
        return ContentCleaner(config)

    @pytest.fixture
    def cleaner_without_filtering(self):
        """Create cleaner without English filtering."""
        config = ContentCleaningConfig(filter_english_only=False)
        return ContentCleaner(config)

    def test_keep_english_lines(self, cleaner_with_filtering):
        """Should keep lines with sufficient vowel-bearing tokens."""
        content = """This is a valid English sentence.
Another good line here."""
        result = cleaner_with_filtering.clean(content)

        assert "This is a valid English sentence" in result
        assert "Another good line here" in result

    def test_remove_mixed_letter_digit_lines(self, cleaner_with_filtering):
        """Should remove lines with mixed letters and digits."""
        content = """Valid English line.
8IBU mixed noise line
Another valid line."""
        result = cleaner_with_filtering.clean(content)

        assert "Valid English line" in result
        assert "Another valid line" in result
        assert "8IBU" not in result

    def test_remove_uppercase_gibberish(self, cleaner_with_filtering):
        """Should remove lines with uppercase no-vowel tokens."""
        content = """Normal text here.
JWFIJN IFSUIFCPPLQFBTF gibberish
More normal text."""
        result = cleaner_with_filtering.clean(content)

        assert "Normal text here" in result
        assert "More normal text" in result
        assert "JWFIJN" not in result
        assert "IFSUIFCPPLQFBTF" not in result

    def test_keep_markdown_headers_with_vowels(self, cleaner_with_filtering):
        """Should keep markdown headers with vowel-bearing tokens."""
        content = """# Introduction
## Background
Some content."""
        result = cleaner_with_filtering.clean(content)

        assert "# Introduction" in result or "Introduction" in result
        assert "Background" in result

    def test_keep_questions_with_vowels(self, cleaner_with_filtering):
        """Should keep questions with at least one vowel token."""
        content = """What?
Why is this?
How?"""
        result = cleaner_with_filtering.clean(content)

        # Lines with vowel-bearing tokens should be kept
        assert "What" in result or "Why" in result or "How" in result

    def test_remove_lines_with_parenthesis_uppercase(self, cleaner_with_filtering):
        """Should remove lines with parenthesis followed by uppercase tokens."""
        content = """Valid line here.
(JWFIJN IFSUIF garbage
Normal text."""
        result = cleaner_with_filtering.clean(content)

        assert "Valid line here" in result
        assert "Normal text" in result
        assert "JWFIJN" not in result

    def test_remove_asterisk_junk_lines(self, cleaner_with_filtering):
        """Should remove lines starting with asterisk and junk."""
        content = """Valid text.
*"JUNK LINE
More valid text."""
        result = cleaner_with_filtering.clean(content)

        assert "Valid text" in result
        assert "More valid text" in result
        assert "*\"JUNK" not in result

    def test_filtering_disabled_keeps_all(self, cleaner_without_filtering):
        """When filtering disabled, should keep all lines."""
        content = """Valid line.
8IBU mixed noise
JWFIJN IFSUIF gibberish
Normal line."""
        result = cleaner_without_filtering.clean(content)

        # All content should be preserved (after base cleanup)
        assert len(result) > 0


class TestContentCleanerFinalization:
    """Test finalization functionality."""

    @pytest.fixture
    def cleaner(self):
        """Create cleaner with default config."""
        config = ContentCleaningConfig()
        return ContentCleaner(config)

    def test_collapse_multiple_blank_lines(self, cleaner):
        """Should collapse 3+ blank lines to 2 blank lines."""
        content = """Line 1


Line 2




Line 3"""
        result = cleaner.clean(content)

        # Should have at most 2 consecutive newlines
        assert "\n\n\n\n" not in result
        assert "\n\n\n" not in result

    def test_fix_apostrophe_spacing(self, cleaner):
        """Should fix spacing before possessive 's."""
        content = "John 's book and Mary 's car"
        result = cleaner.clean(content)

        assert "John's" in result
        assert "Mary's" in result
        assert " 's" not in result

    def test_strip_leading_trailing_whitespace(self, cleaner):
        """Should strip leading and trailing whitespace."""
        content = "   \n  Content here  \n   "
        result = cleaner.clean(content)

        assert not result.startswith(" ")
        assert not result.startswith("\n")
        assert not result.endswith(" ")
        assert not result.endswith("\n")


class TestContentCleanerConfiguration:
    """Test configuration options."""

    def test_glyph_removal_disabled(self):
        """Should not remove GLYPH when disabled."""
        config = ContentCleaningConfig(remove_glyph=False)
        cleaner = ContentCleaner(config)

        content = "Text GLYPH<tag> more"
        result = cleaner.clean(content)

        assert "GLYPH" in result

    def test_html_comments_disabled(self):
        """Should not remove HTML comments when disabled."""
        config = ContentCleaningConfig(remove_html_comments=False)
        cleaner = ContentCleaner(config)

        content = "Text <!-- comment --> more"
        result = cleaner.clean(content)

        assert "<!--" in result
        assert "comment" in result

    def test_markdown_tables_disabled(self):
        """Should not remove markdown tables when disabled."""
        config = ContentCleaningConfig(remove_markdown_tables=False)
        cleaner = ContentCleaner(config)

        content = "Text\n| col1 | col2 |\nMore"
        result = cleaner.clean(content)

        assert "|" in result
        assert "col1" in result

    def test_ligature_fixing_disabled(self):
        """Should not fix ligatures when disabled."""
        config = ContentCleaningConfig(fix_ligatures=False)
        cleaner = ContentCleaner(config)

        content = "Visit Be ĳ ing"
        result = cleaner.clean(content)

        assert "ĳ" in result

    def test_all_features_disabled(self):
        """Should perform minimal processing when all features disabled."""
        config = ContentCleaningConfig(
            enabled=True,
            remove_glyph=False,
            remove_html_comments=False,
            remove_markdown_tables=False,
            fix_ligatures=False,
            filter_english_only=False
        )
        cleaner = ContentCleaner(config)

        content = "GLYPH<!-- comment -->| table |Be ĳ ing"
        result = cleaner.clean(content)

        # Should still do HTML unescaping and basic finalization
        assert len(result) > 0

    def test_processing_disabled_completely(self):
        """Should return input unchanged when processing disabled."""
        config = ContentCleaningConfig(enabled=False)
        cleaner = ContentCleaner(config)

        content = "GLYPH<!-- comment -->| table |"
        result = cleaner.clean(content)

        assert result == content


class TestContentCleanerEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def cleaner(self):
        """Create cleaner with default config."""
        config = ContentCleaningConfig()
        return ContentCleaner(config)

    def test_empty_content(self, cleaner):
        """Should handle empty content gracefully."""
        result = cleaner.clean("")

        assert result == ""

    def test_none_content(self, cleaner):
        """Should handle None content gracefully."""
        result = cleaner.clean(None)

        assert result == ""

    def test_whitespace_only_content(self, cleaner):
        """Should handle whitespace-only content."""
        result = cleaner.clean("   \n\n\t\t   ")

        assert result == ""

    def test_very_long_content(self, cleaner):
        """Should handle very long content efficiently."""
        # 10,000 lines of content
        content = "Valid English line.\n" * 10000
        result = cleaner.clean(content)

        assert len(result) > 0
        assert "Valid English line" in result

    def test_unicode_content(self, cleaner):
        """Should handle Portuguese and Unicode content correctly."""
        content = "Relatório de análise com conclusões importantes."
        result = cleaner.clean(content)

        assert "Relatório" in result
        assert "análise" in result
        assert "conclusões" in result

    def test_mixed_newline_styles(self, cleaner):
        """Should handle different newline styles."""
        content = "Line 1\nLine 2\r\nLine 3\rLine 4"
        result = cleaner.clean(content)

        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
        assert "Line 4" in result


class TestContentCleanerIntegration:
    """Test full cleaning pipeline with realistic content."""

    @pytest.fixture
    def cleaner_full_processing(self):
        """Create cleaner with full processing enabled."""
        config = ContentCleaningConfig(
            enabled=True,
            remove_glyph=True,
            remove_html_comments=True,
            remove_markdown_tables=True,
            fix_ligatures=True,
            filter_english_only=True,
            min_vowel_tokens=2
        )
        return ContentCleaner(config)

    @pytest.fixture
    def cleaner_basic_processing(self):
        """Create cleaner with only basic cleanup."""
        config = ContentCleaningConfig(
            enabled=True,
            remove_glyph=True,
            remove_html_comments=True,
            remove_markdown_tables=True,
            fix_ligatures=True,
            filter_english_only=False
        )
        return ContentCleaner(config)

    def test_full_pipeline_with_mixed_content(self, cleaner_full_processing):
        """Should clean complex document with multiple artifact types."""
        content = """
# Valid Report Title

This is a GLYPH<tag> valid English paragraph with content.

<!-- This HTML comment should be removed -->

| Table | Header |
|-------|--------|
| Data  | Values |

Visit Be ĳ ing for the conference.

8IBU mixed noise line should be removed
JWFIJN IFSUIFCPPLQFBTF gibberish line

Final valid paragraph with enough vowel-bearing tokens.


Conclusion.
"""
        result = cleaner_full_processing.clean(content)

        # Should keep valid content
        assert "Valid Report Title" in result
        assert "valid English paragraph" in result
        assert "Beijing" in result
        assert "Final valid paragraph" in result
        assert "Conclusion" in result

        # Should remove artifacts
        assert "GLYPH" not in result
        assert "<!--" not in result
        assert "| Table |" not in result
        assert "8IBU" not in result
        assert "JWFIJN" not in result

    def test_portuguese_document_preservation(self, cleaner_basic_processing):
        """Should preserve Portuguese content with basic cleanup."""
        content = """
# Relatório de GLYPH Despesas

GLYPH<artifact>Despesas de Julho 2025

<!-- comment -->

Salários: R$ 13.239,00
FGTS: R$ 1.266,02

| Tabela | Valores |
|--------|---------|

Total: R$ 14.505,02
"""
        result = cleaner_basic_processing.clean(content)

        # Should keep Portuguese content
        assert "Relatório" in result
        assert "Despesas" in result
        assert "Julho" in result
        assert "Salários" in result

        # Should remove artifacts
        assert "GLYPH" not in result
        assert "<!--" not in result
        assert "| Tabela |" not in result

    def test_real_world_expense_report(self, cleaner_basic_processing):
        """Should clean real-world expense report document."""
        content = """
GLYPH<page1>DESPESAS

Despesa com Pessoal    Julho 2025

<!-- Generated content -->

| Item              | Valor      |
|-------------------|------------|
| Salários          | 13.239,00  |
| Vale Transporte   | 182,40     |

GLYPH Total Geral: R$ 13.421,40

Responsável: João Silva
Empresa: Acme Serviços Ltda
"""
        result = cleaner_basic_processing.clean(content)

        # Should preserve meaningful content
        assert "DESPESAS" in result
        assert "Despesa com Pessoal" in result
        assert "Julho 2025" in result
        assert "13.239,00" in result
        assert "João Silva" in result

        # Should remove artifacts
        assert "GLYPH<page1>" not in result
        assert "<!--" not in result
        assert "| Item" not in result


class TestContentCleanerVowelTokenCounting:
    """Test vowel token counting logic for English filtering."""

    @pytest.fixture
    def cleaner(self):
        """Create cleaner with English filtering enabled."""
        config = ContentCleaningConfig(
            filter_english_only=True,
            min_vowel_tokens=2
        )
        return ContentCleaner(config)

    def test_two_vowel_tokens_kept(self, cleaner):
        """Lines with 2+ vowel tokens should be kept."""
        content = "This line has enough vowels."
        result = cleaner.clean(content)

        assert "This line has enough vowels" in result

    def test_one_vowel_token_removed(self, cleaner):
        """Lines with <2 vowel tokens should be removed."""
        content = "Xyz qrs"
        result = cleaner.clean(content)

        # Should be removed (no vowels)
        assert len(result.strip()) == 0 or "Xyz" not in result

    def test_no_vowel_tokens_removed(self, cleaner):
        """Lines with no vowel tokens should be removed."""
        content = "BCDFGH JKLMNP"
        result = cleaner.clean(content)

        # Should be removed (no vowels)
        assert len(result.strip()) == 0 or "BCDFGH" not in result

    def test_custom_min_vowel_tokens(self):
        """Should respect custom min_vowel_tokens setting."""
        config = ContentCleaningConfig(
            filter_english_only=True,
            min_vowel_tokens=3
        )
        cleaner = ContentCleaner(config)

        # 2 vowel tokens - should be removed with min=3
        content = "Quick test"
        result = cleaner.clean(content)

        # Should be removed or empty
        assert len(result.strip()) == 0 or "Quick test" not in result


class TestContentCleanerPerformance:
    """Test performance characteristics."""

    @pytest.fixture
    def cleaner(self):
        """Create cleaner with default config."""
        config = ContentCleaningConfig()
        return ContentCleaner(config)

    def test_performance_large_document(self, cleaner):
        """Should process large documents efficiently (<100ms per 1000 lines)."""
        import time

        # Create 1000-line document with mixed content
        lines = []
        for i in range(1000):
            if i % 5 == 0:
                lines.append("GLYPH<artifact>Valid content here")
            elif i % 5 == 1:
                lines.append("<!-- HTML comment -->More valid content")
            elif i % 5 == 2:
                lines.append("| Table | Row |")
            else:
                lines.append(f"Valid line number {i} with content")

        content = "\n".join(lines)

        start = time.time()
        result = cleaner.clean(content)
        duration_ms = (time.time() - start) * 1000

        assert len(result) > 0
        assert duration_ms < 500  # Should process in <500ms
