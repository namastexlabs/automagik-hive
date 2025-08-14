# Test Suite Deprecation Warnings Analysis

## Overview
Systematic analysis of deprecation warnings in the test suite requiring fixes to maintain forward compatibility.

## Identified Issues

### 1. Pydantic Field Deprecation (PRIORITY: HIGH)
**Location**: lib/mcp/config.py (SOURCE CODE - REQUIRES FORGE TASK)
**Issue**: Using deprecated `env` parameter in Field()
**Current Code**:
```python
mcp_enabled: bool = Field(True, env="MCP_ENABLED")
mcp_connection_timeout: float = Field(30.0, env="MCP_CONNECTION_TIMEOUT")
```

**Required Fix**:
```python
mcp_enabled: bool = Field(default=True, json_schema_extra={"env": "MCP_ENABLED"})
mcp_connection_timeout: float = Field(default=30.0, json_schema_extra={"env": "MCP_CONNECTION_TIMEOUT"})
```

### 2. SQLAlchemy DeclarativeBase Deprecation (PRIORITY: HIGH)  
**Location**: lib/models/base.py (SOURCE CODE - REQUIRES FORGE TASK)
**Issue**: Using deprecated `declarative_base()` function
**Current Code**:
```python
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base(metadata=metadata)
```

**Required Fix**:
```python
from sqlalchemy.orm import declarative_base
Base = declarative_base(metadata=metadata)
```

### 3. HTTPX Content Parameter Deprecation (PRIORITY: MEDIUM)
**Locations**: Multiple test files (TEST CODE - CAN FIX DIRECTLY)
**Issue**: Using deprecated `content` parameter in HTTPX requests
**Files Affected**: Need to scan test files for httpx usage

### 4. Coroutine Warnings (PRIORITY: MEDIUM)
**Locations**: 
- api/routes/test_mcp_router.py (TEST CODE - CAN FIX DIRECTLY)
- api/test_serve.py (TEST CODE - CAN FIX DIRECTLY)
**Issue**: Unawaited coroutines causing RuntimeWarnings

### 5. Pytest Cache Permissions (PRIORITY: LOW)
**Location**: System-level configuration
**Issue**: Permission denied errors with pytest cache
**Current Workaround**: Cache disabled via `cachedir: /dev/null`

## Impact Assessment
- **Current Test Status**: 913 passing, 30 skipped, 0 failed
- **Warning Count**: 12+ deprecation warnings preventing clean test runs
- **Risk Level**: HIGH - Future library versions may break compatibility

## Action Plan
1. Create automagik-forge tasks for source code deprecations
2. Fix test-related deprecations directly in tests/ directory  
3. Validate all fixes with comprehensive test run
4. Ensure zero warnings and all tests still pass

## Testing Strategy
- Run pytest with deprecation warnings as errors to catch all issues
- Validate each fix individually to prevent regressions
- Maintain test isolation and mocking patterns