# Testing Report: C2 Factory Integration (TDD RED Phase)

**Task:** C2-factory-integration - Knowledge Factory Processor Integration
**Date:** 2025-10-14 16:22 UTC
**Branch:** wish/knowledge-enhancement
**Phase:** TDD RED (Failing Tests Created)

## Executive Summary

Created 11 comprehensive failing tests for factory integration with DocumentProcessor (Task C2). All tests properly fail as expected because the implementation doesn't exist yet. Tests validate config loading, processor integration, enable/disable toggles, and singleton behavior.

## Test Suite Created

**Location:** `/Users/caiorod/Documents/Namastex/automagik-hive/tests/lib/knowledge/test_knowledge_factory.py`

**New Test Class:** `TestKnowledgeFactoryProcessorIntegration`

### Test Categories (11 tests total)

#### 1. Configuration Loading Tests (3 tests)
- `test_factory_loads_processing_config` - Validates factory calls `load_knowledge_processing_config()`
- `test_factory_uses_default_config_when_no_override` - Tests default config path usage
- `test_factory_respects_custom_config_path` - Tests `HIVE_KNOWLEDGE_CONFIG_PATH` env var override

#### 2. Processor Integration Tests (3 tests)
- `test_factory_passes_config_to_knowledge_base` - Validates `processing_config` parameter passed to RowBasedCSVKnowledgeBase
- `test_factory_creates_knowledge_base_with_processor` - Tests processor attribute exists when enabled
- `test_factory_processor_none_when_disabled` - Tests processor is None when disabled

#### 3. Enable/Disable Toggle Tests (3 tests)
- `test_factory_enables_processing_when_config_enabled` - Tests `config.processing.enabled=true` behavior
- `test_factory_disables_processing_when_config_disabled` - Tests `config.processing.enabled=false` behavior
- `test_factory_handles_missing_config_gracefully` - Tests fallback when config is missing

#### 4. Singleton Behavior Tests (2 tests)
- `test_factory_shared_instance_has_processor` - Validates shared instance preserves processor
- `test_factory_reuses_processor_across_calls` - Validates processor reuse across multiple calls

## Test Execution Results

### Command
```bash
uv run pytest tests/lib/knowledge/test_knowledge_factory.py::TestKnowledgeFactoryProcessorIntegration -v
```

### Results: 11/11 FAILED ✅ (Expected RED Phase)

**Primary Failure Reason:**
```
AttributeError: <module 'lib.knowledge.factories.knowledge_factory'> does not have the attribute 'load_knowledge_processing_config'
```

**This is correct behavior** - the factory doesn't import or call the config loader yet.

### Test Failure Breakdown

| Test | Expected Behavior | Current Failure Reason |
|------|------------------|----------------------|
| `test_factory_loads_processing_config` | Factory calls config loader | `load_knowledge_processing_config` not imported |
| `test_factory_uses_default_config_when_no_override` | Uses None as default path | Config loader not called |
| `test_factory_respects_custom_config_path` | Reads `HIVE_KNOWLEDGE_CONFIG_PATH` env var | Config loader not integrated |
| `test_factory_passes_config_to_knowledge_base` | Passes `processing_config` parameter | Parameter not added to factory |
| `test_factory_creates_knowledge_base_with_processor` | Knowledge base has processor | Processor not initialized |
| `test_factory_processor_none_when_disabled` | Processor is None when disabled | Enable/disable logic missing |
| `test_factory_enables_processing_when_config_enabled` | Config enabled creates processor | Config check not implemented |
| `test_factory_disables_processing_when_config_disabled` | Config disabled skips processor | Config check not implemented |
| `test_factory_handles_missing_config_gracefully` | Fallback to defaults | Error handling not added |
| `test_factory_shared_instance_has_processor` | Singleton preserves processor | Processor not in singleton |
| `test_factory_reuses_processor_across_calls` | Same processor across calls | Processor not cached |

## Test Quality Metrics

### Coverage Areas
✅ Config loading from multiple paths
✅ Custom config path via environment variable
✅ Passing config to knowledge base constructor
✅ Processor creation when enabled
✅ Processor omission when disabled
✅ Enable/disable toggle behavior
✅ Graceful handling of missing config
✅ Singleton pattern with processor
✅ Processor reuse across calls

### Mock Strategy
- Mocked `load_knowledge_processing_config` (doesn't exist yet - correct RED behavior)
- Mocked `RowBasedCSVKnowledgeBase` to isolate factory logic
- Mocked `ProcessingConfig` with enable/disable variations
- Proper environment variable mocking for custom paths
- Singleton reset in `setup_method()` for test isolation

### Test Structure Quality
✅ Clear test names describing expected behavior
✅ RED phase comments explaining why tests should fail
✅ Proper mocking to isolate factory behavior
✅ Comprehensive coverage of happy and failure paths
✅ Singleton reset between tests for isolation
✅ Organized into logical test groups with section comments

## Implementation Requirements (From Tests)

Based on the failing tests, the factory implementation needs to:

1. **Import config loader:**
   ```python
   from lib.knowledge.config.config_loader import load_knowledge_processing_config
   ```

2. **Load processing config in `create_knowledge_base()`:**
   ```python
   # Check for custom config path
   config_path = os.getenv("HIVE_KNOWLEDGE_CONFIG_PATH")
   processing_config = load_knowledge_processing_config(config_path)
   ```

3. **Pass config to RowBasedCSVKnowledgeBase:**
   ```python
   _shared_kb = RowBasedCSVKnowledgeBase(
       csv_path=str(csv_path_value),
       vector_db=vector_db,
       contents_db=contents_db,
       processing_config=processing_config  # NEW
   )
   ```

4. **Handle enable/disable logic:**
   - When `processing_config.processing["enabled"] == True` → processor initialized
   - When `processing_config.processing["enabled"] == False` → processor is None
   - Graceful fallback when config loading fails

5. **Preserve processor in singleton:**
   - Shared instance (`_shared_kb`) maintains processor reference
   - Multiple calls reuse the same processor instance

## Dependencies

**Upstream (Must be complete):**
- ✅ A1-metadata-models (ProcessedDocument, ProcessingConfig models exist)
- ✅ A2-processing-config (ProcessingConfig with enabled flag exists)
- ✅ B5-document-processor (DocumentProcessor orchestrator complete)
- ⚠️  C1-load-content-override (27/29 tests passing - nearly complete)

**Blocked Until:**
- C1 complete with processor initialization in RowBasedCSVKnowledgeBase

## Next Steps for GREEN Phase

1. **Wait for C1 completion** - Knowledge base needs processor initialization
2. **Add config loader import** to factory
3. **Load processing config** with custom path support
4. **Pass config to knowledge base constructor**
5. **Update singleton logic** to preserve processor
6. **Run tests again** expecting GREEN phase

## Files Modified

### Tests Created
- `/Users/caiorod/Documents/Namastex/automagik-hive/tests/lib/knowledge/test_knowledge_factory.py`
  - Added `TestKnowledgeFactoryProcessorIntegration` class (11 tests)
  - Lines 222-613

### Files to Modify (GREEN Phase)
- `/Users/caiorod/Documents/Namastex/automagik-hive/lib/knowledge/factories/knowledge_factory.py`
  - Import `load_knowledge_processing_config`
  - Load config in `create_knowledge_base()`
  - Pass `processing_config` to RowBasedCSVKnowledgeBase
  - Handle enable/disable toggle
  - Preserve processor in singleton

## Test Validation Commands

```bash
# Run C2 tests (all should FAIL in RED phase)
uv run pytest tests/lib/knowledge/test_knowledge_factory.py::TestKnowledgeFactoryProcessorIntegration -v

# After GREEN implementation, verify:
uv run pytest tests/lib/knowledge/test_knowledge_factory.py::TestKnowledgeFactoryProcessorIntegration -v

# Run all factory tests
uv run pytest tests/lib/knowledge/test_knowledge_factory.py -v

# Coverage check
uv run pytest tests/lib/knowledge/test_knowledge_factory.py --cov=lib/knowledge/factories --cov-report=term-missing
```

## Conclusion

**RED Phase: COMPLETE ✅**

Created 11 comprehensive failing tests validating factory integration with DocumentProcessor. All tests properly fail because:
1. Config loader not imported in factory
2. Processing config not loaded
3. Config not passed to knowledge base constructor
4. Enable/disable logic not implemented
5. Processor not preserved in singleton

Tests are well-structured, properly mocked, and ready to guide GREEN phase implementation. C2 can proceed to implementation once C1 is complete.

---

**Death Testament:**
Report saved to: `genie/reports/hive-tests-c2-factory-integration-202510141622.md`

Task C2 RED phase complete. Tests comprehensively validate factory processor integration requirements. Ready for GREEN phase implementation after C1 completion.
