# 🧞 Logging Level Consistency WISH

**Status:** READY_FOR_REVIEW

## Executive Summary
Align every Automagik Hive entry point so environment-driven log levels control all output, eliminating stray DEBUG chatter while preserving structured diagnostics.

## Current State Analysis
**What exists:** Central Loguru configuration in `lib/logging/config.py:67` maps `HIVE_LOG_LEVEL` / `AGNO_LOG_LEVEL` and syncs standard logging; `api/serve.py:39` calls `setup_logging()` on import and threads emoji-driven handlers across the API stack. Tests and CLI flows rely on `loguru.logger` defaults without invoking `ensure_logging_initialized()`, and inventories live in `lib/logging/CLAUDE.md`.
**Gap identified:** Most command surfaces (`cli/main.py`, `docker/lib/compose_service.py`, background scripts, pytest fixtures) emit logs before configuration, so Loguru’s DEBUG default leaks regardless of `.env`. `api/serve.py:304-348` also emits verbose diagnostics with `logger.info("DEBUG: …")`, bypassing level filters. Missing `common/logging.py` leaves doc references orphaned.
**Solution approach:** Document all logger bootstrap paths, refactor to a single initialization contract (`ensure_logging_initialized()`) invoked by every process (CLI, API factories, workers, tests), normalize diagnostic levels, and add regression tests/fixtures that assert INFO-level filtering under default envs.

## Change Isolation Strategy
- **Isolation principle:** Keep configuration inside `lib/logging/config.py`; higher layers only call `ensure_logging_initialized()` to avoid embedding logging rules elsewhere.
- **Extension pattern:** Provide lightweight helper wrappers (e.g. CLI bootstrap) that initialize logging before executing existing workloads, keeping imported modules untouched.
- **Stability assurance:** Maintain current emoji/batch behavior and root handlers; new guards must be feature-flagged or default-safe to avoid breaking production observability.

## Success Criteria
✅ Inventory enumerates every logger initializer, handler, and environment dependency with ownership notes.
✅ Single bootstrap helper configures both Loguru and stdlib logging; no module calls `setup_logging()` directly.
✅ DEBUG messages disappear when `.env` sets INFO, while DEBUG mode remains opt-in through `HIVE_LOG_LEVEL=DEBUG`.
✅ All logger usage (Loguru + stdlib) follows one standardized pattern or adapter, eliminating mixed APIs.
✅ Verification artifacts (commands + pytest suites) demonstrate INFO-only output by default.

## Never Do (Protection Boundaries)
❌ Remove emoji/batch logging features or silence error/warning logs.
❌ Introduce ad-hoc `print` statements or alternative logging stacks.
❌ Modify `pyproject.toml`, install packages outside `uv`, or bypass `ensure_logging_initialized()` contract.

## Technical Architecture

### Component Structure
Logging Core:
├── lib/logging/config.py        # Environment-aware Loguru + stdlib configuration
├── lib/logging/__init__.py      # Exports logger, setup helpers, batch utilities
├── lib/logging/batch_logger.py  # Startup batching honoring env-driven verbosity
└── lib/logging/session_logger.py # Structured session lifecycle logging

Entry Points & Surfaces:
├── api/serve.py                 # Factory import path (calls setup_logging today)
├── api/main.py                  # Alternative FastAPI factory lacking init guard
├── cli/main.py                  # CLI parser -> ServiceManager
├── cli/commands/service.py      # Dev/serve orchestration invoking uvicorn/docker
├── docker/lib/compose_service.py# Compose template logs
├── scripts/*.py                 # Ops automation relying on global logger defaults
├── tests/conftest.py            # Sets env vars but no logging bootstrap
└── tests/integration/config/*   # ServerConfig fixtures controlling log level

Standard Logging Consumers:
├── lib/memory/*, lib/utils/*, ai/*   # Call `logger.debug/info` extensively
└── third-party integrations (Agno, watchdog, uvicorn) # Expect stdlib levels to propagate

### Naming Conventions
- Initialization helper stays `ensure_logging_initialized()` in `lib/logging/config.py`.
- New bootstrap modules adopt `{surface}_logging.py` naming only inside `cli/` or `scripts/` if needed.
- Environment variables remain uppercase (`HIVE_LOG_LEVEL`, `AGNO_LOG_LEVEL`, `HIVE_VERBOSE_LOGS`).

## Task Decomposition

### Dependency Graph
```
A[Discovery Audit] ---> B[Governance & Alignment] ---> C[Validation & Documentation]
```

### Group A: Discovery Audit (Parallel)
Dependencies: None | Execute simultaneously

**A1-entrypoint-inventory**: @api/serve.py, @api/main.py, @cli/main.py, @cli/commands/service.py, @docker/lib/compose_service.py  Document how each surface initializes (or skips) logging, including process for uvicorn reload workers. Success: Inventory table capturing initializer, trigger timing, and ownership.

**A2-environment-matrix**: @tests/conftest.py, @lib/config/server_config.py, @lib/logging/config.py  Map all env vars influencing log levels (`HIVE_LOG_LEVEL`, `AGNO_LOG_LEVEL`, `HIVE_VERBOSE_LOGS`, test overrides). Success: Matrix noting precedence, defaults, and conflicts.

**A3-handler-audit**: @lib/logging/config.py, @lib/logging/batch_logger.py, @lib/logging/session_logger.py  Trace handlers/propagation for Loguru + stdlib + Agno patching to identify gaps (e.g., propagate=False loggers). Success: Diagram noting sinks, filters, and modules needing adjustments.

**A4-logger-inventory**: rg `logging.getLogger` across lib/*, api/*, ai/* to catalogue stdlib logger usage and ownership. Success: Spreadsheet mapping modules to migration strategy (adapter vs. refactor to Loguru).

**A5-entrypoint-spotlight**: Document existing direct `setup_logging()` call in `api/serve.py:47` plus scripts (e.g., `scripts/remove_hardcoded_emojis.py`) that call `logger` without initialization. Success: Inventory highlights exact call sites slated for bootstrap replacement.

### Group B: Governance & Alignment (After Group A)
Dependencies: Complete Group A

**B1-single-bootstrap**: @lib/logging/config.py, @lib/logging/__init__.py, @api/serve.py  Formalize a single `initialize_logging(surface)` helper that wraps `ensure_logging_initialized()`, remove ad-hoc `setup_logging()` calls (e.g., `api/serve.py:47`), and reset root handlers before wiring sinks (`logging.root.handlers.clear()`). Success: Grep shows zero direct `setup_logging()` call sites outside the helper and root handlers are controlled solely by the helper.

**B3-logger-unification**: @lib/logging/config.py, @lib/logging/CLAUDE.md, stdlib logger call sites from A4  Build a Loguru intercept handler so stdlib loggers (e.g., `lib/versioning/bidirectional_sync.py`, `api/routes/version_router.py`) flow through the unified pipeline, replace module-level `logging.getLogger` usages, and update validators (`scripts/validate_logging.py`) to flag stragglers. Success: Inventory from A4 marked "migrated" with standardized usage for each module and validator enforces the new rule.

**B4-diagnostic-scrub**: @api/serve.py:304, @api/serve.py:340, @api/serve.py:412  Convert `logger.info("DEBUG: …")` sequences into true debug-level calls or gate them behind `if logger.level("DEBUG")` to respect configuration. Success: API startup no longer emits faux-debug logs under INFO.

**B5-entrypoint-bootstrap**: @cli/main.py, @cli/commands/service.py, @api/main.py  Invoke the shared helper before command execution (including subprocess invocation) and ensure alternative FastAPI factories call the same guard. Success: CLI + API imports respect `HIVE_LOG_LEVEL` by default.

**B6-scripts-alignment**: @docker/lib/compose_service.py, @scripts/validate_logging.py, @scripts/remove_hardcoded_emojis.py  Add lightweight helpers (or reuse CLI bootstrap) so automation scripts initialize logging via the shared helper and never bypass setup. Success: Scripts under `/docker` and `/scripts` emit INFO-only by default.

**B7-test-fixture-guards**: @tests/conftest.py, @tests/integration/config/conftest.py  Patch fixtures to call `ensure_logging_initialized()` and assert resulting logger levels when fixtures set `HIVE_LOG_LEVEL`. Success: Tests fail if bootstrap missing or levels misapplied.

**B8-doc-governance**: @lib/logging/CLAUDE.md, @scripts/validate_logging.py  Document the single bootstrap helper, Loguru intercept strategy, and prohibition on raw stdlib logger creation; align validator rules to enforce it. Success: Doc reflects unified contract with examples and tooling enforces compliance.

### Group C: Validation & Documentation (After Group B)
Dependencies: Complete Group B

**C1-regression-tests**: Create `tests/lib/logging/test_level_enforcement.py` (new) verifying INFO default, DEBUG opt-in, AGNO propagation, and CLI bootstrap behavior via subprocess harness. Success: `uv run pytest tests/lib/logging/test_level_enforcement.py -q` passes, failing if DEBUG leaks.

**C2-cli-smoke**: Extend `tests/cli/commands/test_service.py` to launch dev server in dry-run/watch mode capturing startup logs and asserting absence of DEBUG when INFO. Success: CLI test suite produces deterministic assertions.

**C3-log-sampler**: Provide script (e.g., `scripts/logging_sampler.py`) or extend existing validator to scan sample runs and report mismatched levels; ensures automation coverage. Success: Script outputs “No debug leaks detected” under INFO and instructions recorded in wish evidence.

**C4-deliverables-kit**: `@genie/reports/logging-level-consistency-*.md`  Compile inventory, change log, verification outputs, and follow-up tickets (e.g., deeper AGNO audit) for Death Testament + wish closure.

**C5-future-wish-scout**: Identify remaining risky surfaces (e.g., third-party plugins) and recommend follow-up wishes or Forge tasks if remediation exceeds scope. Success: Recommendations appended to wish doc.

## Deliverables
- Logging initializer inventory with owners and trigger timing (Group A).
- Environment precedence matrix summarizing `.env`, CLI flags, and defaults (Group A).
- Governance & alignment implementation plan covering config updates, entry point hooks, and doc refresh (Group B).
- Verification package: CLI/API command transcripts, pytest run outputs, and automation script results proving INFO-only default behavior (Group C).
- Follow-up wish/Forge recommendations for any deferred work (Group C).

## Implementation Examples

### Bootstrap Helper Injection
```python
# lib/logging/bootstrap.py (potential helper created in Group B1)
from lib.logging.config import ensure_logging_initialized, logger

def initialize_logging(surface: str) -> None:
    ensure_logging_initialized()
    logger.bind(surface=surface).debug("Logging initialized for surface")
```

### CLI Guard Pattern
```python
# cli/main.py
from lib.logging.config import ensure_logging_initialized

def main() -> int:
    ensure_logging_initialized()
    parser = create_parser()
    args = parser.parse_args()
    ...
```

### Pytest Fixture Enforcement
```python
# tests/conftest.py
from lib.logging.config import ensure_logging_initialized

@pytest.fixture(autouse=True)
def bootstrap_logging_env():
    ensure_logging_initialized()
    yield
```

## Testing Protocol
```bash
# Validate logging initialization respects INFO by default
uv run pytest tests/lib/logging/test_level_enforcement.py -q

# Smoke-test CLI dev server bootstrap (captures logs via pytest capsys)
uv run pytest tests/cli/commands/test_service.py -k "logging_level_guard"

# Manual verification: ensure dev server emits INFO only
HIVE_LOG_LEVEL=INFO uv run automagik-hive --dev --host 127.0.0.1 --port 9999 --check-config

# DEBUG opt-in confirmation
HIVE_LOG_LEVEL=DEBUG uv run automagik-hive --dev --host 127.0.0.1 --port 9999 --check-config
```

## Validation Checklist
- [ ] All entry points call `ensure_logging_initialized()` exactly once.
- [ ] DEBUG output absent when `HIVE_LOG_LEVEL=INFO` (captured logs attached).
- [ ] AGNO loggers obey `AGNO_LOG_LEVEL` and no longer override defaults.
- [ ] Tests cover bootstrap fixtures, CLI flows, and API factories.
- [ ] Documentation updated: logging CLAUDE, wish evidence, follow-up notes.
- [ ] Feature toggles/flags allow reverting to current behavior if emergent issue.

```
