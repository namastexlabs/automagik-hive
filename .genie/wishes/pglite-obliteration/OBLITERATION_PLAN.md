# PGLite Obliteration Plan

**Date:** 2025-10-29
**Context:** PGLite backend will not be used; complete removal required
**Branch:** Feature branch from `dev`

---

## Executive Summary

PGLite was implemented as a WebAssembly-based PostgreSQL alternative for development environments. After evaluation, the decision has been made to not use PGLite and remove all related code, tests, documentation, and tooling.

## Scope Analysis

### 🎯 Core Implementation (PRIORITY 1 - Foundation)

**Provider Layer:**
- `lib/database/providers/pglite.py` (354 lines) - HTTP-based backend with subprocess management
- `lib/database/providers/__init__.py` - Export registry
- `lib/database/backend_factory.py` - Factory with PGLite creation logic
- `lib/database/__init__.py` - DatabaseBackendType.PGLITE enum

**Bridge Infrastructure:**
- `tools/pglite-bridge/server.js` - Node.js HTTP bridge
- `tools/pglite-bridge/package.json` - npm dependencies
- `tools/pglite-bridge/start.sh` - Start script
- `tools/pglite-bridge/stop.sh` - Stop script
- `tools/pglite-bridge/health.sh` - Health check
- `tools/pglite-bridge/.gitignore` - Bridge artifacts
- `tools/pglite-bridge/README.md` - Bridge documentation

### 🧪 Test Infrastructure (PRIORITY 2 - Validation)

**Unit Tests:**
- `tests/lib/database/test___init__.py` - Backend enum tests
- `tests/lib/database/test_backend_factory.py` - Factory tests with PGLite
- `tests/lib/database/providers/test___init__.py` - Provider exports
- `tests/lib/database/providers/test_pglite.py` - PGLite-specific tests

**Integration Tests:**
- `tests/integration/database/test_backend_integration.py` - Multi-backend integration
- `tests/integration/database/test_backend_migration.py` - Migration scenarios
- `tests/integration/database/test_backend_performance.py` - Performance benchmarks
- `tests/integration/database/test_backend_selection.py` - Backend selection logic

**CLI Tests:**
- `tests/cli/test_backend_detection.py` - Backend auto-detection
- `tests/cli/test_backend_flag.py` - CLI flag parsing
- `tests/cli/test_backend_prompt.py` - Interactive backend selection
- `tests/cli/test_docker_skip.py` - Docker skip logic
- `tests/cli/test_utils.py` - CLI utility functions

### 🛠️ CLI & Utilities (PRIORITY 3 - User Interface)

**CLI Commands:**
- `cli/commands/postgres.py` - PGLite startup logic
- `cli/commands/service.py` - Service management with PGLite
- `cli/docker_manager.py` - Docker/PGLite detection
- `cli/main.py` - Main CLI with backend selection
- `cli/utils.py` - Backend detection utilities

**Startup Integration:**
- `lib/utils/startup_orchestration.py` - Orchestrated startup with PGLite references
- `api/serve.py` - Production server with backend initialization

### 📚 Documentation (PRIORITY 4 - Knowledge)

**Migration & Setup:**
- `docs/MIGRATION_PGLITE.md` - PGLite migration guide
- `RELEASE_NOTES_v0.2.0.md` - Release notes mentioning PGLite
- `README.md` - Installation references

**Genie Artifacts:**
- `genie/wishes/pglite-migration/` - Complete wish directory
  - `DEATH_TESTAMENT.md` - Original migration death testament
  - `hive-coder-cli-backend-integration-202510212119.md`
  - `hive-coder-database-providers-202510212022.md`
  - `hive-coder-docker-removal-202510212152.md`
  - `hive-coder-pglite-docs-202510211936.md`
  - `hive-tests-backend-prompt-spam-fix-202510282314.md`
  - `hive-tests-backend-selection-202510281950.md`
  - `hive-tests-database-backend-202510211924.md`
  - `hive-tests-pglite-backend-abstraction-202510211702.md`

### ⚙️ Configuration (PRIORITY 5 - Settings)

**Environment & Config:**
- `lib/config/settings.py` - HIVE_DATABASE_BACKEND with PGLite option
- `.env.example` - PGLite environment variables
- `.gitignore` - pglite-data directory
- `Makefile` - PGLite-related targets

**Docker & Infrastructure:**
- `docker/lib/__init__.py` - Backend detection for containers
- `docker/README.md` - PGLite vs Docker documentation

### 🌿 Git Artifacts (PRIORITY 6 - Cleanup)

**Branches:**
- `feature/pglite-backend-abstraction` (local & remote)
- `wish/pglite-migration` (local & remote)

---

## Obliteration Strategy

### Phase 1: Foundation Removal (Core Implementation)
**Agent:** `hive-coder`
**Complexity:** 6/10 (Multi-file coordination, enum updates)

**Tasks:**
1. Remove `lib/database/providers/pglite.py`
2. Remove `DatabaseBackendType.PGLITE` from enum
3. Update `lib/database/backend_factory.py`:
   - Remove PGLite import
   - Remove PGLite case from `detect_backend_from_url()`
   - Remove PGLite case from `create_backend()`
   - Update docstrings
4. Update `lib/database/providers/__init__.py` exports
5. Remove entire `tools/pglite-bridge/` directory

**Success Criteria:**
- No import errors when importing `lib.database`
- Factory functions don't reference PGLite
- Bridge tooling completely removed

### Phase 2: Test Obliteration (Validation Layer)
**Agent:** `hive-tests`
**Complexity:** 5/10 (Many files, straightforward removal)

**Tasks:**
1. Delete PGLite-specific test files:
   - `tests/lib/database/providers/test_pglite.py`
   - Backend-related CLI tests (detection, flags, prompts)
2. Update remaining test files:
   - `tests/lib/database/test_backend_factory.py` - Remove PGLite parametrize cases
   - `tests/integration/database/test_backend_*.py` - Remove PGLite scenarios
3. Clean up test fixtures referencing PGLite

**Success Criteria:**
- `uv run pytest tests/lib/database/` passes
- `uv run pytest tests/integration/database/` passes
- `uv run pytest tests/cli/` passes (if CLI tests remain)
- No PGLite test markers or fixtures

### Phase 3: CLI & Utilities Cleanup (User Interface)
**Agent:** `hive-coder`
**Complexity:** 4/10 (Localized changes, clear boundaries)

**Tasks:**
1. Update `cli/commands/postgres.py`:
   - Remove PGLite startup logic
   - Simplify to PostgreSQL-only
2. Update `cli/docker_manager.py`:
   - Remove PGLite detection
3. Update `cli/main.py`:
   - Remove backend selection logic
   - Simplify initialization
4. Update `cli/utils.py`:
   - Remove backend detection utilities
5. Clean `lib/utils/startup_orchestration.py`:
   - Remove PGLite orchestration references
6. Update `api/serve.py`:
   - Remove PGLite initialization paths

**Success Criteria:**
- CLI starts without PGLite options
- No backend selection prompts
- Simplified initialization code

### Phase 4: Documentation Purge (Knowledge Cleanup)
**Agent:** `hive-coder`
**Complexity:** 3/10 (Straightforward file deletion)

**Tasks:**
1. Delete documentation:
   - `docs/MIGRATION_PGLITE.md`
2. Update `README.md`:
   - Remove PGLite installation instructions
   - Remove PGLite backend references
3. Update `RELEASE_NOTES_v0.2.0.md`:
   - Note PGLite removal
4. Delete `genie/wishes/pglite-migration/` directory completely

**Success Criteria:**
- No PGLite documentation exists
- README doesn't mention PGLite
- Genie artifacts cleaned

### Phase 5: Configuration Cleanup (Settings)
**Agent:** `hive-coder`
**Complexity:** 3/10 (Environment variable cleanup)

**Tasks:**
1. Update `lib/config/settings.py`:
   - Remove `HIVE_DATABASE_BACKEND` PGLite option
   - Update validation/defaults
2. Update `.env.example`:
   - Remove `PGLITE_PORT`
   - Remove `PGLITE_DATA_DIR`
   - Remove PGLite-related comments
3. Update `.gitignore`:
   - Remove `pglite-data/`
   - Remove `tools/pglite-bridge/node_modules/`
4. Update `Makefile`:
   - Remove PGLite targets
5. Update `docker/README.md`:
   - Remove PGLite comparisons

**Success Criteria:**
- No PGLite environment variables
- Configuration validates without PGLite
- Gitignore cleaned

### Phase 6: Git Cleanup (Branch Removal)
**Agent:** `Manual` (requires user confirmation)
**Complexity:** 2/10 (Git operations)

**Tasks:**
1. Delete local branches:
   ```bash
   git branch -D feature/pglite-backend-abstraction
   git branch -D wish/pglite-migration
   ```
2. Delete remote branches (if authorized):
   ```bash
   git push origin --delete feature/pglite-backend-abstraction
   git push origin --delete wish/pglite-migration
   ```

**Success Criteria:**
- No local PGLite branches
- Remote branches removed (if authorized)

---

## Agent Coordination

### Primary Agents
- **hive-coder**: Implementation removal (Phases 1, 3, 4, 5)
- **hive-tests**: Test obliteration (Phase 2)
- **hive-reviewer**: Validation after each phase

### Orchestration Flow

```
Phase 1 (hive-coder) → Phase 2 (hive-tests)
                     ↓
            Phase 3 (hive-coder)
                     ↓
            Phase 4 (hive-coder)
                     ↓
            Phase 5 (hive-coder)
                     ↓
       hive-reviewer (final validation)
                     ↓
         Phase 6 (manual git cleanup)
```

### Verification Gates

After each phase:
1. Run relevant test suites
2. Verify no import errors
3. Check for remaining references via grep
4. Document completion in todo list

Final validation:
```bash
# No PGLite references in code
rg -i "pglite" --type py

# All tests pass
uv run pytest tests/lib/database/
uv run pytest tests/integration/database/
uv run pytest tests/api/

# Server starts cleanly
make dev
```

---

## Risk Assessment

### Low Risk
- Documentation removal (no code impact)
- Test removal (validates other code works)
- Git branch cleanup (reversible)

### Medium Risk
- Factory updates (affects backend selection)
- CLI changes (user-facing changes)
- Configuration cleanup (environment variables)

### High Risk
- Provider removal (breaks imports if referenced elsewhere)
- Enum changes (type system impact)

### Mitigation
- TDD approach: Update tests first when possible
- Phase-by-phase validation
- Full test suite between phases
- Keep commit history granular for easy rollback

---

## Success Criteria

### Code Quality
- ✅ No PGLite references in `lib/`, `api/`, `cli/`
- ✅ No broken imports
- ✅ Type system validates (mypy passes)
- ✅ All existing tests pass

### Documentation
- ✅ No PGLite documentation
- ✅ README updated
- ✅ Release notes reflect removal

### Configuration
- ✅ No PGLite environment variables
- ✅ Simplified backend selection
- ✅ PostgreSQL-only recommendation

### Completeness
- ✅ No PGLite artifacts in `tools/`
- ✅ No PGLite test files
- ✅ No PGLite genie wishes
- ✅ Git branches cleaned

---

## Post-Obliteration

### Commit Strategy
```
feat: Obliterate PGLite backend (Phase 1 - Core removal)
feat: Obliterate PGLite backend (Phase 2 - Tests)
feat: Obliterate PGLite backend (Phase 3 - CLI)
feat: Obliterate PGLite backend (Phase 4 - Docs)
feat: Obliterate PGLite backend (Phase 5 - Config)
docs: PGLite obliteration DEATH_TESTAMENT
```

### PR Title
**🔥 Obliterate PGLite backend - PostgreSQL-only strategy**

### PR Description Template
```markdown
## Summary
Complete removal of PGLite backend implementation in favor of PostgreSQL-only strategy.

## Motivation
PGLite will not be used. Removing unnecessary abstraction reduces complexity and maintenance burden.

## Changes
- ✅ Removed PGLite provider implementation
- ✅ Removed PGLite bridge tooling
- ✅ Simplified database factory (PostgreSQL + SQLite fallback only)
- ✅ Removed PGLite tests and documentation
- ✅ Cleaned CLI backend selection logic
- ✅ Updated configuration and environment variables

## Impact
- **Breaking Change**: HIVE_DATABASE_BACKEND=pglite no longer supported
- **Simplified**: Backend selection now PostgreSQL (default) or SQLite (CI/testing)
- **Documentation**: Installation guide simplified to PostgreSQL setup

## Testing
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ Server starts successfully with PostgreSQL
- ✅ No PGLite references remain in codebase

## Migration
Users with `HIVE_DATABASE_BACKEND=pglite` in `.env` should:
1. Remove the `HIVE_DATABASE_BACKEND` variable (defaults to PostgreSQL)
2. Ensure PostgreSQL is running (Docker or native)
3. Update `HIVE_DATABASE_URL` to point to PostgreSQL instance
```

---

## Execution Readiness

This plan is ready for execution. Proceed with Phase 1 when authorized.

**Next Step:** Create feature branch and begin Phase 1 (Foundation Removal)
