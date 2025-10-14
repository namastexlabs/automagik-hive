# Forge Planning Report: Knowledge Enhancement System

**Wish**: Knowledge Enhancement System
**Status**: APPROVED
**Created**: 2025-10-14 12:40 UTC
**Approved By**: User
**Origin Branch**: wish/knowledge-enhancement

---

## Executive Summary

Transform ALL Knowledge API-inserted documents from raw text chunks into semantically structured, searchable knowledge with rich metadata matching CSV-loaded content quality. Implementation broken into 6 consolidated task groups for efficient parallel execution.

**Key Goals**:
- **PDF library A/B testing** to select optimal extraction tool (docling vs alternatives)
- User-configurable entity extraction via YAML
- Auto-detection of business_unit from content keywords
- Parallel processing pipeline for speed/accuracy balance
- LLM-optimized semantic chunking preserving document structure
- Forward-only processing (new API insertions only)

---

## Approved Task Groups

### Group A0: PDF Extraction Library A/B Testing
**Agent**: `hive-coder`
**Branch**: `wish/knowledge-enhancement`
**Dependencies**: None (parallel with Group A)

**Bundled Subtasks**:
- A0: PDF library comparative analysis (docling vs pypdf vs pdfplumber vs pymupdf)

**Scope**:
Conduct A/B testing of PDF extraction libraries to determine the best option for document processing. Evaluate accuracy, performance, structure detection, Unicode support, memory usage, and error handling using real-world sample documents (financial reports, invoices, manuals).

**Libraries to Test**:
1. **docling** - Primary candidate (IBM Research)
2. **pypdf** / **pypdf2** - Popular lightweight alternative
3. **pdfplumber** - Table extraction specialist
4. **pymupdf** (fitz) - Performance-focused option

**Test Criteria**:
- Text extraction quality and formatting retention
- Table preservation and structure detection
- Processing speed for 1-20 page documents
- Brazilian Portuguese character handling
- Peak memory consumption
- Robustness with malformed PDFs

**Success Criteria**:
✅ Comparison test suite with sample PDFs executed
✅ Performance benchmarks completed (speed, memory, accuracy)
✅ Recommendation report with pros/cons analysis
✅ Selected library documented and ready for B3 integration
✅ Test coverage for comparison framework

**Evidence Expected**:
- Death Testament from hive-coder
- Comparative analysis report with metrics
- Sample PDFs and test results
- Library recommendation with rationale

---

### Group A: Foundation & Configuration
**Agent**: `hive-coder`
**Branch**: `wish/knowledge-enhancement`
**Dependencies**: None (parallel with Group A0)

**Bundled Subtasks**:
- A1: Metadata models (Pydantic schemas for EnhancedMetadata, ExtractedEntities, DocumentType)
- A2: Processing config schema (ProcessingConfig Pydantic model)
- D1: Create `lib/knowledge/config/knowledge_processing.yaml`
- D2: Config loader utility (`load_knowledge_config()`)
- D3: Settings integration (global toggle + config path override)

**Scope**:
Create all foundational models and configuration infrastructure for knowledge processing. This includes Pydantic schemas for metadata validation, dedicated YAML configuration file separate from agent configs, and config loader utility with environment variable override support.

**Success Criteria**:
✅ Pydantic models validate sample data without errors
✅ `lib/knowledge/config/knowledge_processing.yaml` loads successfully
✅ Config loader searches correct paths (custom → default → built-in)
✅ Settings expose `hive_enable_enhanced_knowledge` and `hive_knowledge_config_path`
✅ Tests validate config loading and model validation

**Evidence Expected**:
- Death Testament from hive-coder
- Unit tests for Pydantic models
- Unit tests for config loader
- Settings integration tests

---

### Group B: Core Processors
**Agent**: `hive-coder`
**Branch**: `wish/knowledge-enhancement`
**Dependencies**: Group A (needs models and config), Group A0 (PDF library selection for B3)

**Bundled Subtasks**:
- B1: Type detector (filename + content patterns)
- B2: Entity extractor (dates, amounts, people, organizations + custom entities via YAML)
- B3: Semantic chunker (LLM-optimized, table-preserving, paragraph-aware) - **uses selected PDF library from A0**
- B4: Metadata enricher (auto-categorize, auto-tag, business_unit auto-detection)

**Scope**:
Implement all four core document processing modules with TDD approach. Each processor must support YAML configuration, handle Brazilian Portuguese content, and provide extensibility for custom entity types (patterns + regex).

**Key Features**:
- Type detector: >70% accuracy on filename + content analysis
- Entity extractor: Support custom entities via `custom_entities` YAML config
- Semantic chunker: Analyze entire document structure for LLM-friendly chunks (500-1500 chars)
- Metadata enricher: Auto-detect business_unit from keyword matching

**Success Criteria**:
✅ All processors follow TDD (tests written first)
✅ Type detector handles Brazilian document patterns
✅ Entity extractor supports patterns + regex for custom types
✅ Semantic chunker preserves tables and paragraph boundaries
✅ Metadata enricher auto-detects business_unit from keywords
✅ >85% test coverage for all processor modules

**Evidence Expected**:
- Death Testament from hive-coder
- Unit tests for each processor (test_type_detector.py, test_entity_extractor.py, test_semantic_chunker.py, test_metadata_enricher.py)
- Test coverage reports showing >85%

---

### Group C: Orchestrator & Integration
**Agent**: `hive-coder`
**Branch**: `wish/knowledge-enhancement`
**Dependencies**: Groups A + B (needs processors and config)

**Bundled Subtasks**:
- B5: Document processor orchestrator (parallel pipeline execution)
- C1: Override `_load_content` in RowBasedCSVKnowledgeBase
- C2: Factory integration (wire config into knowledge factory)
- C3: Filter extensions (support document_type, date ranges, custom entities)

**Scope**:
Build the orchestrator that coordinates all processors with parallel execution, integrate into existing knowledge base via `_load_content` override, update factory to load processing config, and extend filters for new metadata fields.

**Key Features**:
- Parallel processing: Type detection + entity extraction run concurrently
- Forward-only: Process only API-inserted documents (detect via metadata markers)
- CSV preservation: CSV-loaded knowledge completely unchanged
- Filter enhancements: Support filtering by document_type, business_unit, date ranges, custom entities

**Success Criteria**:
✅ Document processor orchestrates all 4 processors with parallel execution
✅ `_load_content` override processes API-inserted docs only
✅ CSV-loaded documents pass through unchanged
✅ Factory integration loads config from dedicated YAML file
✅ Filters support new metadata fields
✅ Integration tests show end-to-end flow working

**Evidence Expected**:
- Death Testament from hive-coder
- Integration tests (test_document_processor.py, test_enhanced_loading.py)
- Factory tests showing processor activation
- Filter tests covering new metadata fields

---

### Group D: Test Suite & Quality Assurance
**Agent**: `hive-tests`
**Branch**: `wish/knowledge-enhancement`
**Dependencies**: Groups A + B + C (needs complete implementation)

**Bundled Subtasks**:
- E1: Comprehensive unit tests for all processors
- E2: Integration tests (E2E upload → retrieve → verify)
- E3: Performance tests (100 docs <10s, <500MB memory)

**Scope**:
Create comprehensive test coverage across all layers: unit tests for individual processors, integration tests for end-to-end knowledge enhancement flow, and performance tests validating speed/memory targets.

**Test Coverage Requirements**:
- Unit tests: >85% coverage for `lib/knowledge/processors/`
- Integration tests: Full upload → process → retrieve → filter cycle
- Performance tests: 100 documents processed in <10s with <500MB memory
- Edge cases: Large messages, Unicode, special characters, concurrent requests

**Success Criteria**:
✅ `uv run pytest tests/lib/knowledge/processors/ --cov=lib/knowledge/processors` shows >85% coverage
✅ Integration test uploads document via API, retrieves with filters, verifies rich metadata
✅ Performance test processes 100 docs in <10s
✅ Memory usage stays under 500MB during batch processing
✅ All tests pass with green status

**Evidence Expected**:
- Death Testament from hive-tests
- Coverage reports (term + HTML)
- Performance benchmark results
- Test execution logs

---

### Group E: Documentation & Knowledge Transfer
**Agent**: `hive-coder`
**Branch**: `wish/knowledge-enhancement`
**Dependencies**: Groups A + B + C + D (needs complete system)

**Bundled Subtasks**:
- E4: Update `lib/knowledge/CLAUDE.md` with enhanced processing documentation

**Scope**:
Update knowledge documentation to reflect new enhanced processing capabilities. Include configuration options, usage examples, before/after comparisons, migration guidance, and architecture diagrams.

**Documentation Requirements**:
- Configuration reference for `lib/knowledge/config/knowledge_processing.yaml`
- Custom entity examples (patterns + regex)
- Business unit auto-detection configuration
- Before/after examples showing improvement
- Usage guide for enabling/disabling feature
- Integration patterns for agents

**Success Criteria**:
✅ `lib/knowledge/CLAUDE.md` updated with comprehensive guide
✅ Configuration examples match actual YAML structure
✅ Before/after examples demonstrate quality improvement
✅ Usage patterns documented for common scenarios
✅ Migration guide for existing users

**Evidence Expected**:
- Death Testament from hive-coder
- Updated CLAUDE.md file
- Documentation review confirmation

---

## Execution Timeline

**Sequential Dependencies**:
```
A0 [PDF Testing] ──┐
                   ├──> B [Processors] → C [Integration] → D [Testing] + E [Docs]
A [Foundation] ────┘
```

**Parallel Opportunities**:
- Groups A0 + A run in parallel (no dependencies between them)
- Group B starts after both A0 + A complete (needs config + PDF library selection)
- Groups D + E can run in parallel after C completes
- Within groups, subtasks can be developed incrementally

**Estimated Execution**:
- Group A0: PDF library evaluation (2-3 agent cycles)
- Group A: Foundation layer (2-3 agent cycles, parallel with A0)
- Group B: Core processors (4-5 agent cycles, TDD approach)
- Group C: Integration (3-4 agent cycles)
- Group D: Testing (2-3 agent cycles)
- Group E: Documentation (1-2 agent cycles)

---

## Critical Success Factors

1. **PDF Library Selection**: Complete A/B testing before B3 implementation to ensure optimal extraction
2. **Configuration Separation**: Knowledge processing config in dedicated YAML file, NOT in agent configs
3. **TDD Discipline**: All processors developed with tests-first approach
4. **Forward-Only Processing**: Only enhance new API insertions, preserve existing data
5. **Custom Entity Extensibility**: Support user-defined entities via patterns + regex
6. **Performance Targets**: 100 docs <10s, <500MB memory
7. **Business Unit Auto-Detection**: Keyword-based classification from content

---

## Risk Mitigation

**Risk**: Config architecture confusion
- **Mitigation**: Dedicated `lib/knowledge/config/knowledge_processing.yaml` location, clear separation from agent configs

**Risk**: Breaking CSV-loaded knowledge
- **Mitigation**: Strict detection of API-inserted vs CSV-loaded documents, comprehensive integration tests

**Risk**: Performance degradation
- **Mitigation**: Parallel processing pipeline, performance tests in Group D

**Risk**: Poor entity extraction accuracy
- **Mitigation**: User-configurable patterns + regex, extensible custom entities

---

## Approval Record

**Approved By**: User
**Approval Time**: 2025-10-14 12:40 UTC
**Method**: Chat confirmation ("approve and create with forge master")

**Approved Groups**:
- ✅ Group A0: PDF Extraction Library A/B Testing
- ✅ Group A: Foundation & Configuration
- ✅ Group B: Core Processors
- ✅ Group C: Orchestrator & Integration
- ✅ Group D: Test Suite & Quality Assurance
- ✅ Group E: Documentation & Knowledge Transfer

---

## Forge Task Creation

Tasks created via `forge-master` with complete context loading and agent assignments. Each task references this planning report for coordination.

**Task Creation Status**: IN_PROGRESS

---

## Death Testament Requirements

Each agent must deliver a Death Testament documenting:
- What was implemented
- Tests written and results
- Configuration changes
- Integration points
- Known issues or limitations
- Next steps for dependent groups

**Report Location**: This file serves as the master plan. Individual agent Death Testaments should reference this report for context.

---

**END OF PLANNING REPORT**
