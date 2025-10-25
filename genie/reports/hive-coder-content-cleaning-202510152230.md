# Death Testament: Content Cleaning Implementation - Waiting for Tests

**Agent**: hive-coder
**Task**: Implement content cleaning functionality for knowledge processing pipeline
**Status**: BLOCKED - Waiting for hive-tests
**Date**: 2025-10-15 22:30 UTC
**Branch**: wish/knowledge-enhancement

## Executive Summary

Implementation task received for adding configurable content cleaning to the knowledge processing pipeline. Following TDD workflow and CLAUDE.md instructions, implementation is **blocked** pending test creation by hive-tests agent.

## Current State Analysis

### Files Reviewed

1. **/Users/caiorod/Documents/Namastex/automagik-hive/clean_english.py**
   - Reference implementation with base cleanup patterns
   - Functions: base_cleanup(), is_english_line(), finalize_text()
   - Handles GLYPH artifacts, HTML comments, tables, ligatures
   - English-only line filtering with vowel token heuristics

2. **/Users/caiorod/Documents/Namastex/automagik-hive/lib/knowledge/processors/document_processor.py**
   - Current orchestrator with 4-phase processing
   - Phase 1: Type detection + entity extraction (parallel)
   - Phase 2: Metadata enrichment
   - Phase 3: Semantic chunking
   - NEW Phase 0 needed: Content cleaning (before type detection)

3. **/Users/caiorod/Documents/Namastex/automagik-hive/lib/knowledge/config/processing_config.py**
   - Pydantic configuration models
   - Contains: TypeDetectionConfig, EntityExtractionConfig, ChunkingConfig, MetadataConfig
   - Needs: ContentCleaningConfig addition

4. **/Users/caiorod/Documents/Namastex/automagik-hive/lib/knowledge/config/knowledge_processing.yaml**
   - YAML configuration file
   - Current sections: enabled, type_detection, entity_extraction, chunking, metadata, document_splitting
   - Needs: content_cleaning section addition

### Test Status

Checked for existing tests:
```bash
find tests -name "*content_clean*" -o -name "*cleaner*"
# Result: No tests found

ls tests/lib/knowledge/processors/
# Existing tests:
# - test___init__.py
# - test_document_processor.py
# - test_entity_extractor.py
# - test_metadata_enricher.py
# - test_semantic_chunker.py
# - test_type_detector.py
# Missing: test_content_cleaner.py
```

**Conclusion**: No content cleaner tests exist. Implementation blocked per TDD workflow.

## Implementation Requirements (Ready to Execute)

### 1. New Module: lib/knowledge/processors/content_cleaner.py

**Based on clean_english.py patterns:**
- ContentCleaner class inheriting pattern from other processors
- Configuration via ContentCleaningConfig (Pydantic)
- Methods:
  - `__init__(self, config: ContentCleaningConfig)`
  - `clean(self, content: str) -> str` - Main entry point
  - `_base_cleanup(self, text: str) -> str` - GLYPH, HTML, tables
  - `_filter_english_lines(self, text: str) -> str` - Optional English-only
  - `_finalize_text(self, text: str) -> str` - Spacing, apostrophes
- Structured logging with performance metrics
- Handle empty/None content gracefully

### 2. Configuration Updates

**processing_config.py additions:**
```python
class ContentCleaningConfig(BaseModel):
    """Configuration for content cleaning."""

    enabled: bool = Field(default=True)
    remove_glyph: bool = Field(default=True)
    remove_html_comments: bool = Field(default=True)
    remove_markdown_tables: bool = Field(default=True)
    fix_ligatures: bool = Field(default=True)
    filter_english_only: bool = Field(default=False)
    min_vowel_tokens: int = Field(default=2, ge=1)

class ProcessingConfig(BaseModel):
    # Add to existing fields
    content_cleaning: ContentCleaningConfig = Field(
        default_factory=ContentCleaningConfig
    )
```

**knowledge_processing.yaml additions:**
```yaml
# Add new section
content_cleaning:
  enabled: true
  remove_glyph: true
  remove_html_comments: true
  remove_markdown_tables: true
  fix_ligatures: true
  filter_english_only: false
  min_vowel_tokens: 2
```

### 3. DocumentProcessor Integration

**Update document_processor.py process() method:**
```python
def process(self, document: dict[str, Any]) -> ProcessedDocument:
    # Add Phase 0 before existing phases

    # Phase 0: Content cleaning (NEW)
    if self.config.content_cleaning.enabled:
        cleaner = ContentCleaner(self.config.content_cleaning)
        content = cleaner.clean(document["content"])
        document["content"] = content  # Update for subsequent phases

    # Phase 1: Type detection + entity extraction (existing)
    doc_type, entities = self._parallel_analyze(filename, content)
    # ... rest of existing code
```

### 4. Export Updates

**processors/__init__.py:**
```python
from lib.knowledge.processors.content_cleaner import ContentCleaner

__all__ = [
    "DocumentProcessor",
    "TypeDetector",
    "EntityExtractor",
    "SemanticChunker",
    "MetadataEnricher",
    "ContentCleaner",  # NEW
]
```

## TDD Workflow Compliance

### CRITICAL: Red-Green-Refactor

Following CLAUDE.md instructions:
1. **RED** - hive-tests creates failing tests (BLOCKED HERE)
2. **GREEN** - hive-coder implements to pass tests (NEXT STEP)
3. **REFACTOR** - Clean up with green tests

### Quote from /CLAUDE.md:
> "Strict Rule — never dispatch `hive-coder` without prior failing tests from `hive-tests`."

### Current Status
- Task received with complete requirements
- Codebase analyzed and implementation plan ready
- **Waiting for hive-tests to create test_content_cleaner.py**
- Cannot proceed to implementation without failing tests

## Required Tests (For hive-tests)

### Test Coverage Needed:

1. **Basic Functionality**
   - test_remove_glyph_artifacts
   - test_remove_html_comments
   - test_remove_markdown_tables
   - test_fix_ligatures

2. **English Filtering**
   - test_english_line_detection
   - test_filter_english_only_enabled
   - test_filter_english_only_disabled
   - test_min_vowel_tokens_threshold

3. **Configuration**
   - test_content_cleaning_enabled
   - test_content_cleaning_disabled
   - test_partial_cleanup_configuration

4. **Edge Cases**
   - test_empty_content
   - test_none_content
   - test_unicode_content
   - test_mixed_content

5. **Integration**
   - test_document_processor_with_content_cleaning
   - test_content_cleaning_before_type_detection
   - test_performance_overhead

6. **Performance**
   - test_cleaning_overhead_under_50ms

## Success Criteria Checklist

Once tests are created and implementation proceeds:

- [ ] All hive-tests created tests pass
- [ ] Content cleaned BEFORE type detection (Phase 0)
- [ ] YAML configuration controls behavior
- [ ] No breaking changes to existing documents
- [ ] Performance overhead < 50ms per document
- [ ] Structured logging shows cleaning metrics
- [ ] Pydantic configuration validation works
- [ ] Empty/None content handled gracefully
- [ ] Backward compatibility maintained (default: enabled)

## Integration Points Summary

- **Configuration System**: Uses @lib/knowledge/config/processing_config.py patterns
- **Document Processor**: Integrates into @lib/knowledge/processors/document_processor.py
- **Reference Implementation**: Based on @clean_english.py patterns
- **Processor Pattern**: Follows existing processor architecture

## Risks & Mitigation

### Identified Risks:
1. **Performance overhead** - Mitigated by performance tests (<50ms target)
2. **Breaking changes** - Mitigated by default enabled, backward compatibility
3. **Unicode handling** - Mitigated by explicit UTF-8 handling
4. **Test coverage gaps** - Mitigated by comprehensive test requirements

### Coordination:
- hive-tests: Create test_content_cleaner.py with full coverage
- hive-coder: Implement after tests created (this agent)
- hive-quality: Verify after implementation (ruff, mypy, format)

## Next Steps

1. **BLOCKED**: Wait for hive-tests to create test_content_cleaner.py
2. **READY**: Implementation code prepared and documented above
3. **PENDING**: Execute implementation once tests exist and fail
4. **PENDING**: Verify all tests pass
5. **PENDING**: Create Death Testament with validation evidence

## Commands to Execute (After Tests Created)

```bash
# Verify tests fail initially (RED phase)
uv run pytest tests/lib/knowledge/processors/test_content_cleaner.py -v

# Implement content_cleaner.py
# (Implementation ready per specifications above)

# Verify tests pass (GREEN phase)
uv run pytest tests/lib/knowledge/processors/test_content_cleaner.py -v

# Run full processor test suite
uv run pytest tests/lib/knowledge/processors/ -v

# Verify integration
uv run pytest tests/lib/knowledge/ -v --cov=lib/knowledge
```

## Files to Create (After Tests)

1. `/Users/caiorod/Documents/Namastex/automagik-hive/lib/knowledge/processors/content_cleaner.py`
2. Update `/Users/caiorod/Documents/Namastex/automagik-hive/lib/knowledge/config/processing_config.py`
3. Update `/Users/caiorod/Documents/Namastex/automagik-hive/lib/knowledge/config/knowledge_processing.yaml`
4. Update `/Users/caiorod/Documents/Namastex/automagik-hive/lib/knowledge/processors/document_processor.py`
5. Update `/Users/caiorod/Documents/Namastex/automagik-hive/lib/knowledge/processors/__init__.py`

## Conclusion

Implementation is **BLOCKED** per TDD workflow compliance. All preparation work completed:
- Requirements analyzed
- Codebase inspected
- Implementation plan documented
- Test requirements specified

**Waiting for hive-tests to create failing tests before proceeding.**

---

**Handoff**: This testament documents readiness for content cleaning implementation. Next agent (hive-tests) should create comprehensive test coverage for ContentCleaner class. After tests exist and fail, hive-coder can proceed with implementation per specifications above.

**Branch**: wish/knowledge-enhancement
**Status**: BLOCKED - Waiting for RED phase (hive-tests)
**Estimated Implementation Time**: <30 minutes after tests created
