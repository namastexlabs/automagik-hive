# Hive Coder Death Testament – logging-entrypoint-audit (2025-09-25T01:31Z)

## Scope & Outcomes
- Mapped logging initialization across API, CLI, Docker helper, ops scripts, and pytest harness.
- Built environment precedence matrix for `HIVE_LOG_LEVEL`, `AGNO_LOG_LEVEL`, and `HIVE_VERBOSE_LOGS` with pytest override analysis.
- Appended inventory, matrix, and command transcripts to `genie/wishes/logging-level-consistency-wish.md` under the Evidence section.

## Files Touched
- genie/wishes/logging-level-consistency-wish.md (evidence section appended)

## Commands Executed
```bash
rg "setup_logging\(\)" -n
rg "from lib.logging import logger" -n scripts
rg "lib.logging.setup_logging" -n tests
rg -n "automagik-hive" pyproject.toml
rg "HIVE_LOG_LEVEL" -n tests/conftest.py
rg "AGNO_LOG_LEVEL" -n lib/logging/config.py
rg "HIVE_VERBOSE_LOGS" -n lib/logging/batch_logger.py
sed -n '1,200p' api/serve.py
sed -n '1,200p' cli/main.py
sed -n '1,200p' docker/lib/cli.py
sed -n '700,820p' tests/conftest.py
sed -n '60,110p' tests/api/test_serve.py
date -u +%Y%m%d%H%M
```

## Evidence & Observations
- Only `api/serve.py:47` directly invokes `setup_logging()`, confirming the single entry surface currently configuring Loguru.
- CLI, Docker helper, and ops scripts import `logger` without initialization, leaving log level at Loguru's default DEBUG when run standalone.
- Pytest autouse fixture simultaneously forces `HIVE_LOG_LEVEL=ERROR` and patches `lib.logging.setup_logging` to `None`, so the env override is inert and would break once Group 2 replaces the direct call.
- `.env` generation templates in `lib/auth/credential_service.py` set both `HIVE_LOG_LEVEL` and `AGNO_LOG_LEVEL` to `INFO`, while Docker Compose scaffolding lowercases the level (`info`).

## Risks & Follow-ups
- Group 2 must coordinate with QA before removing the `setup_logging` patch; otherwise importing `api.serve` under pytest will call `None`.
- Docker template should normalize env casing when the shared bootstrap lands to avoid inconsistent comparisons.
- Consider adding a dedicated pytest fixture that asserts `ensure_logging_initialized()` ran once to prevent regressions.

## Validation
- No automated tests executed in this phase; discovery-only deliverable validated via grep transcripts embedded in the wish evidence.
