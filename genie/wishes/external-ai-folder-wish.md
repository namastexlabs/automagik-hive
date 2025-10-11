# 🧞 External AI Folder Wish - Clean Reimplementation

**Status:** READY_FOR_EXECUTION  
**Type:** Runtime Architecture Upgrade (Remove Workspace Scaffolding → Support External AI Folders)  
**Complexity:** Medium (cross-cutting but conceptually simple)  
**Risk:** Registry path drift, CLI regressions, stale documentation

## Core Problem Statement
Automagik Hive still behaves like a workspace scaffolding tool. The current CLI expects users to clone the repo and operate inside our bundled `ai/` tree, while the `cli/workspace.py` implementation (see `cli/workspace.py:1`) continues to generate entire project templates and even shells out to `python -m api.main`. This brittle workflow blocks the real goal: **run Hive against any external AI definition folder with a single command like `uvx automagik-hive /path/to/custom-ai`**.

The previous attempt to retrofit external support stalled. We need a clean slate and a tighter design that treats the CLI as a runtime orchestrator, not a project generator.

## Desired Outcome
- User can point Hive at any AI folder (agents/teams/workflows) without cloning this repo.  
- Existing repo defaults still work when no external folder is provided.  
- All runtime services boot through `ServiceManager.serve_local(...)`, never via raw `python -m`.  
- No workspace scaffolding code, flags, or docs remain.

## Scope & Constraints
- **In scope:** CLI runtime flow, path resolution, registries, service bootstrap, docs, Makefile targets, automated tests.  
- **Out of scope:** Changes to agent schema, API behavior, or deployment packaging.

## Solution Architecture (Clean Rebuild)
### Phase 0 – Strip the Legacy Workflow **(MANDATORY GATE)**
**Goal:** Completely eradicate every workspace-scaffolding artifact **before** any new resolver or runtime code is added.

1. Delete `WorkspaceManager` scaffolding (`cli/workspace.py`) **and** all CLI init helpers (`cli/commands/init.py`, `InteractiveInitializer`, etc.).
2. Remove the `--init` flag and workspace positional handling from `cli/main.py` plus any related help text.
3. Purge Makefile/Makefile.temp, README, CLI testing reports, and other docs that mention workspace creation (`init`, `scaffold`, “workspace server”).
4. Delete or rewrite the workspace-specific test suites (`tests/cli/commands/test_init.py`, `tests/cli/test_workspace.py`, `tests/integration/cli/test_workspace_commands.py`, related fixtures) so the suite reflects the new runtime behavior.
5. Remove obsolete wish documents or clearly mark them superseded (e.g., `genie/wishes/workspace-surgical-refactor-wish.md`).
6. Confirm no residual imports reference removed modules (grep for `WorkspaceManager`, `workspace.`).
7. Run the full test suite to ensure the repo compiles/executes with **zero** new functionality added yet, capturing existing unrelated failures for the death testament.

🚫 **Do not proceed to Phase 1 until the cleanup diff is merged-ready and validated.**

### Phase 1 – Centralize AI Root Resolution (hive-coder)
1. Create `lib/utils/ai_root.py` with a single `resolve_ai_root(explicit_path: str | Path | None, settings: Settings) -> Path` helper.
   - Precedence: explicit CLI argument → `HIVE_AI_ROOT` env → `settings.hive_ai_root` (defaulting to `ai`).
   - Validate that the resolved path exists and contains `agents/`, `teams/`, and `workflows/` directories; raise a descriptive error otherwise.
2. Extend `lib/config/settings.py` with `hive_ai_root: str = Field(default="ai", ...)` and an `ai_root_path` property using the helper.

### Phase 2 – Refresh CLI Entry Point (hive-coder)
1. Update `cli/main.py` to accept an optional positional `ai_root` argument (`uvx automagik-hive /path/to/ai`).
2. When provided, set/override `HIVE_AI_ROOT` for the current invocation and pass the resolved path into downstream services (propagate via `Settings` or explicit parameter when instantiating `ServiceManager`).
3. Replace the ad-hoc server start logic with `ServiceManager.serve_local(...)`, ensuring it receives the resolved AI root (environment injection or constructor argument).
4. Ensure `dev` subcommand and other existing flags still work; document how they interact with external paths.

### Phase 3 – Registry & Service Integration (hive-coder)
1. Update `ai/agents/registry.py`, `ai/teams/registry.py`, and `ai/workflows/registry.py` to derive their base directories from the new resolver instead of hardcoded `Path("ai/...")` constants.
2. Update **every** component that currently hardcodes `ai/...` paths, including but not limited to:
   - `ai/tools/registry.py`
   - `lib/utils/yaml_cache.py`
   - `lib/utils/version_factory.py`
   - `lib/utils/startup_display.py`
   - `lib/services/version_sync_service.py`
   - `lib/config/settings.py` (`hive_mcp_config_path`)
   - `lib/config/emoji_mappings.yaml`
   - Integration tests that reference repo-relative `ai/` fixtures
   - Hooks/scripts (e.g., `scripts/pre-commit-hook.sh`) that enforce the repo layout
3. Ensure `ServiceManager`/`MainService` consumes the resolved AI root (e.g., via dependency injection or environment) so downstream services run against the external folder.
4. Maintain backwards compatibility: when no external folder is provided, everything should behave exactly as today.

### Phase 4 – Testing & Documentation (TDD compliance)
1. **Red:** Use `hive-tests` to add regression tests covering:  
   - Default behavior (no argument, uses repo `ai/`).  
   - `uvx automagik-hive /tmp/custom-ai` path resolution.  
   - `HIVE_AI_ROOT` environment override.  
   - Error handling for missing directories/files.  
2. **Green:** Implement phases 0–3 iteratively, keeping tests green.
3. **Refactor:** Run targeted cleanup, confirm imports and type hints stay consistent.
4. Update `README.md` with new usage examples and remove workspace scaffolding references.
5. Trim `Makefile` targets tied to workspace generation.

### Orchestration & Agent Routing
- Development tasks stay with **hive-coder** (code implementation).  
- Test authoring relies on **hive-tests** (follows TDD).  
- Formatting or lint adjustments, if needed, go to **hive-quality-ruff/mypy**.  
- No other agents required unless debugging emerges.

## Acceptance Criteria
- `uvx automagik-hive /tmp/demo-ai` boots successfully, loading agents/teams/workflows from that directory.
- `HIVE_AI_ROOT=/tmp/demo-ai uvx automagik-hive dev` honors the env var without additional arguments.
- Default invocation (`uvx automagik-hive dev`) uses the repo’s bundled `ai/` directory.
- All registries and services source definitions via the centralized resolver.
- The codebase contains **zero** references to workspace scaffolding.
- README and Makefile reflect the new runtime workflow.

## Verification Protocol
1. **Unit Tests** (run via `uv run pytest tests/cli/test_ai_root_resolution.py -v` or equivalent new suites).  
2. **Integration Check:**  
   ```bash
   mkdir -p /tmp/hive-external/{agents,teams,workflows}
   echo "name: cli-smoke" > /tmp/hive-external/agents/cli-smoke.yaml
   HIVE_AI_ROOT=/tmp/hive-external uvx automagik-hive dev --check-config
   ```
3. **Default Regression:** `uvx automagik-hive dev --check-config` inside the repo should still succeed.
4. **Static Analysis:** `uv run ruff check` and `uv run mypy` if the repo requires them pre-commit.

## Rollback Plan
If anything breaks, re-introduce the previous CLI entry (`cli/workspace.py`, CLI flags) from git history and revert the resolver integration. Document any fallout in the wish death testament.

## Success Metrics
- ✅ External AI folder launches without repo checkout.  
- ✅ Default repo experience unchanged.  
- ✅ No workspace scaffolding code remains.  
- ✅ All automated checks pass.

Let’s spawn the right agents and make this runtime magic happen! 🧞✨
