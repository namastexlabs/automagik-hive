# Test Cleanup Checklist

## Empty Test Files (Delete - 8 total)

- [ ] /home/cezar/automagik/automagik-hive/tests/ai/tools/template-tool/test_tool.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/tools/shared/test_shell_toolkit.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/utils/test_message_validation.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/utils/test_startup_display.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/utils/test_proxy_workflows.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/utils/test_team_utils.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/utils/test_version_reader.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/versioning/test_agno_version_service.py

## Boilerplate Placeholder Tests (Delete or Rewrite - 15 total)

All files have identical structure with @pytest.mark.skip on placeholder tests.

- [ ] /home/cezar/automagik/automagik-hive/tests/lib/logging/test_config.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/logging/test_progress.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/logging/test_session_logger.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/metrics/test_config.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/middleware/test_error_handler.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/models/test_base.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/models/test_agent_metrics.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/models/test_component_versions.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/models/test_version_history.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/auth/test_dependencies.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/auth/test_init_service.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/auth/test_cli.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/config/test_schemas.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/config/test_server_config.py
- [ ] /home/cezar/automagik/automagik-hive/tests/integration/e2e/test_langwatch_integration.py

## Files with Excessive Bare Except Clauses and Weak Assertions (Rewrite)

These need refactoring to remove bare excepts and add real behavioral assertions:

- [ ] /home/cezar/automagik/automagik-hive/tests/lib/metrics/test_langwatch_integration.py (262 lines with 60+ bare excepts)
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/logging/test_batch_logger.py (209 lines, mostly trivial)
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/knowledge/test_metadata_csv_reader.py (245 lines with weak assertions)

## Files with Only test_module_imports Pattern (Remove these methods - 19 files)

Remove the trivial `test_module_imports()` method from:

1. test_version_history.py
2. test_base.py
3. test_agent_metrics.py
4. test_component_versions.py
5. test_metadata_csv_reader.py
6. test_server_config.py
7. test_session_logger.py
8. test_batch_logger.py
9. test_progress.py
10. test_config.py (metrics)
11. test_config.py (logging)
12. test_error_handler.py
13. test_langwatch_integration.py
14. test_dependencies.py
15. test_init_service.py
16. test_cli.py
17. test_schemas.py
18. test_progress.py
19. test_metrics_service.py

## Files with Weak hasattr(__doc__) Tests (Remove - 5 files)

These test Python semantics, not module behavior:

- [ ] /home/cezar/automagik/automagik-hive/tests/lib/config/test_schemas.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/config/test_server_config.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/auth/test_dependencies.py
- [ ] /home/cezar/automagik/automagik-hive/tests/lib/auth/test_init_service.py

---

## Priority Order

### PHASE 1: Delete Empty Files (5 minutes)
Delete all 8 empty test files - they provide no value and confuse test counts.

### PHASE 2: Delete Placeholder Boilerplate (5 minutes)
Delete all 15 boilerplate placeholder test files - they actively harm test suite quality with skipped TODOs.

### PHASE 3: Clean Up Trivial Tests (30 minutes)
Remove test_module_imports() methods from 19 files.
Remove test_module_attributes() hasattr(__doc__) tests from 5 files.

### PHASE 4: Refactor Weak Tests (2-4 hours)
Rewrite remaining files with bare except clauses:
- Replace bare `except` with specific exception types
- Add real behavioral assertions
- Remove tests that only test mocks
- Remove tests that only test existence

### PHASE 5: Add PR Review Standards (Ongoing)
- Require meaningful assertions (not just `is not None`)
- Ban bare except clauses in tests
- Require tests to verify behavior, not just object creation
- Consider pytest-cov coverage gates

---

## Quality Standards to Enforce

### Before Any Test Merge:
- [ ] Has at least 2-3 meaningful assertions
- [ ] Tests behavior, not just existence
- [ ] Uses specific exception handling, never bare `except`
- [ ] Does not test Python language semantics
- [ ] Is not testing only mocks without real behavior
- [ ] Has clear, accurate name matching implementation
- [ ] Uses proper setup/teardown, not bare excepts

### Code Review Checklist:
```
- [ ] Is this test testing actual behavior or just object creation?
- [ ] Would this test catch a real bug?
- [ ] Does this test use bare except clauses?
- [ ] Are all assertions meaningful and specific?
- [ ] Does this test verify mocks or real behavior?
```
