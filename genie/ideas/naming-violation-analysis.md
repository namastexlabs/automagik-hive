# Naming Convention Violation Analysis

## Critical Findings Summary

**VIOLATION SCOPE:** 16+ files with function/method naming violations  
**SEVERITY:** HIGH - Direct violation of CLAUDE.md naming conventions  
**USER FEEDBACK:** "its completly forbidden, across all codebase, to write files and functionsm etc, with fixed, etc"

## Detailed Violation Categories

### 1. HIGH SEVERITY: Function/Method Name Violations

**Core Principle Violated:** "Call things what they actually ARE, no additionals"

**Specific Violations Found:**

1. **lib/middleware/error_handler.py**
   - `_get_new_conversation_endpoint()` → Should be `_get_conversation_endpoint()`
   - USAGE: Called in error recovery flow

2. **Test Function Violations (15+ files):**
   - `test_production_sync_workflow_create_new_component()` → `test_production_sync_workflow_create_component()`
   - `test_ensure_api_key_generation_new()` → `test_ensure_api_key_generation()`
   - `test_save_key_to_env_new_file()` → `test_save_key_to_env_file()`
   - `test_update_gitignore_for_security_new_file()` → `test_update_gitignore_for_security_file()`
   - `test_update_environment_add_new_keys()` → `test_update_environment_add_keys()`
   - `test_get_migration_service_creates_new_instance()` → `test_get_migration_service_creates_instance()`
   - `test_sync_component_to_db_new_component()` → `test_sync_component_to_db_component()`
   - `test_record_validation_metrics_new_file()` → `test_record_validation_metrics_file()`
   - `test_new_event_loop_creation_and_cleanup()` → `test_event_loop_creation_and_cleanup()`

### 2. MEDIUM SEVERITY: Documentation Language

**Files:** `/genie/wishes/` documentation files
- "zen-enhanced" → "zen-integrated" or "zen-powered"
- "improved" → "optimized" or specific functionality
- Multiple references in technical documentation

### 3. LEGITIMATE BUSINESS CONTEXT (NOT VIOLATIONS)

**Database/API Fields (Acceptable):**
- `config_updated` - Database action field
- `updated_version` - Variable holding retrieved data
- `"Configuration updated via API"` - User message

**Comparative Logic (Acceptable):**
- `yaml_newer_than_db` - Temporal comparison
- `test_special_characters_and_newlines` - Functionality description

## Remediation Strategy

### Phase 1: Function Renaming (HIGH PRIORITY)
1. Rename `_get_new_conversation_endpoint` → `_get_conversation_endpoint`
2. Systematic test function renaming (15+ functions)
3. Update all call sites and references

### Phase 2: Documentation Cleanup (MEDIUM PRIORITY)
1. Replace "enhanced/improved" language with purpose-specific terms
2. Update /genie/wishes/ files to use descriptive language

### Phase 3: Prevention (CRITICAL)
1. Add pre-commit validation for forbidden patterns
2. Update CLAUDE.md with specific examples
3. Agent behavioral learning integration

## Naming Convention Rules (From CLAUDE.md)

**FORBIDDEN PATTERNS:**
- fixed, improved, updated, enhanced, optimized, better, new, v2, _fix, _v

**PRINCIPLE:**
- "Call things what they actually ARE, not what they became"
- Clean, descriptive names reflecting PURPOSE
- No modification status indicators

## Implementation Priority

1. **IMMEDIATE:** Fix `_get_new_conversation_endpoint` (production code)
2. **HIGH:** Rename test functions (development stability)
3. **MEDIUM:** Documentation language cleanup
4. **ONGOING:** Prevention mechanisms and validation

## Impact Assessment

- **Files Affected:** 16+ Python files
- **Test Suite Impact:** Multiple test files need function renames
- **Documentation Impact:** Several /genie/wishes/ files
- **Breaking Changes:** None (internal refactoring only)