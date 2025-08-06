# CredentialService MCP Sync Behavior Tests

## 🎯 RED PHASE COMPLETE: Comprehensive Test Suite Created

This directory contains **59 comprehensive failing tests** that drive the TDD implementation of MCP sync behavior changes for the CredentialService class.

### 📊 Test Coverage Summary

- **Total Test Cases**: 59 tests across 4 files
- **Failing Tests**: 50 (as expected in RED phase)
- **Passing Tests**: 9 (existing functionality that should remain unchanged)
- **Lines of Test Code**: 1,930 lines of comprehensive test coverage

### 📁 Test File Organization

#### `test_credential_service_mcp_sync.py` (19 tests)
**Core functionality and behavior validation**
- Basic sync_mcp parameter behavior (True/False/default)
- Method signature validation for new parameters
- Backward compatibility verification
- Edge case handling (missing MCP files, invalid credentials)
- Parameter type validation
- Living documentation of expected behavior

#### `test_credential_service_mcp_sync_edge_cases.py` (16 tests)
**Advanced scenarios and complex edge cases**
- Integration with different installation workflows
- Error handling and graceful failure scenarios
- Performance considerations and thread safety
- Complex parameter interactions (sync_mcp + force_regenerate)
- Documentation workflows and automation scenarios
- Regression prevention for existing functionality

#### `test_credential_service_mcp_sync_integration.py` (14 tests)
**Real-world integration scenarios**
- Makefile integration patterns
- CLI command integration
- Docker Compose workflow integration
- Production deployment automation
- Error recovery and resilience testing
- Performance optimization validation
- Configuration customization support

#### `test_credential_service_mcp_sync_specification.py` (10 tests)
**Definitive API and behavior specification**
- Complete API signature requirements
- Behavioral specification with precise expectations
- Comprehensive requirement validation
- Integration preservation verification
- Complete specification checklist for implementation completion

### 🔧 Key Test Scenarios Covered

#### 🚨 Critical Requirements (Must ALL Pass)
1. **API Changes**: Add `sync_mcp` parameter with default `False` to:
   - `setup_complete_credentials(sync_mcp=False)`
   - `install_all_modes(sync_mcp=False)`

2. **Behavioral Requirements**:
   - `sync_mcp=False` (default): NEVER call `sync_mcp_config_with_credentials()`
   - `sync_mcp=True`: ALWAYS call `sync_mcp_config_with_credentials()` exactly once
   - Workspace installations: No MCP sync by default
   - Agent installations: MCP sync when explicitly requested

3. **Backward Compatibility**: All existing code must work unchanged
   - `setup_complete_credentials()` without parameters must work identically
   - `install_all_modes()` without sync_mcp must work identically
   - No existing behavior should change without explicit opt-in

#### 🛡️ Error Handling & Resilience
- MCP sync failures must not prevent credential generation
- Missing .mcp.json files handled gracefully
- Invalid .mcp.json content handled gracefully
- Invalid credentials handled gracefully
- File permission errors handled appropriately

#### ⚡ Performance & Integration
- MCP sync called at most once per installation
- Thread safety for concurrent credential generation
- Idempotent sync operations
- Preserves existing MCP server configurations
- Custom MCP file path support via environment variables

### 🎯 Implementation Guidance

#### Phase 1: Method Signature Updates
```python
def setup_complete_credentials(
    self,
    postgres_host: str = "localhost",
    postgres_port: int = 5532,
    postgres_database: str = "hive",
    sync_mcp: bool = False  # NEW PARAMETER
) -> dict[str, str]:

def install_all_modes(
    self, 
    modes: List[str] = None,
    force_regenerate: bool = False,
    sync_mcp: bool = False  # NEW PARAMETER
) -> Dict[str, Dict[str, str]]:
```

#### Phase 2: Conditional MCP Sync Logic
```python
# In setup_complete_credentials()
if sync_mcp:
    try:
        self.sync_mcp_config_with_credentials()
    except Exception as e:
        logger.warning(f"MCP sync failed but continuing: {e}")
        # Don't let MCP sync failure prevent credential generation

# In install_all_modes()
if sync_mcp:
    try:
        self.sync_mcp_config_with_credentials()  # Call once per installation
    except Exception as e:
        logger.warning(f"MCP sync failed but continuing: {e}")
```

#### Phase 3: Error Handling & Validation
- Wrap MCP sync calls in try/catch blocks
- Log warnings for sync failures but continue operation
- Validate sync_mcp parameter is boolean (or convert appropriately)
- Handle missing .mcp.json files gracefully in sync_mcp_config_with_credentials()

### 🚀 Running the Tests

```bash
# Run all MCP sync tests
uv run pytest tests/auth/test_credential_service_mcp_sync*.py -v

# Run specific test categories
uv run pytest tests/auth/test_credential_service_mcp_sync.py -v              # Core functionality
uv run pytest tests/auth/test_credential_service_mcp_sync_edge_cases.py -v   # Edge cases
uv run pytest tests/auth/test_credential_service_mcp_sync_integration.py -v  # Integration
uv run pytest tests/auth/test_credential_service_mcp_sync_specification.py -v # Specification

# Quick validation (no verbose output)
uv run pytest tests/auth/test_credential_service_mcp_sync*.py -q
```

### 📈 Success Metrics

**TDD Implementation Complete When**:
- All 50 failing tests pass ✅
- 9 existing tests continue to pass ✅
- No regression in existing functionality ✅
- All method signatures accept new parameters ✅
- All behavioral requirements met ✅
- Error handling robust and graceful ✅

### 🎭 TDD Workflow Integration

**RED PHASE**: ✅ COMPLETE - All 59 tests created and failing appropriately
**GREEN PHASE**: Next - Implement minimal code to make tests pass
**REFACTOR PHASE**: After GREEN - Clean up and optimize implementation

This comprehensive test suite ensures that the MCP sync behavior implementation will be robust, reliable, and maintainable while preserving all existing functionality.