# Forge Plan – Logging Level Consistency Wish

- **Timestamp (UTC):** 2025-09-25 01:19
- **Wish Doc:** genie/wishes/logging-level-consistency-wish.md
- **Human Approval:** Granted by user via chat on 2025-09-25 (`start forging into VIBE KANBAN`).
- **Coordinator:** GENIE (orchestrator)

## Wish Recap
Align every Automagik Hive entry point so environment-driven log levels govern all output, eliminating stray DEBUG chatter while preserving structured diagnostics. Success demands an audited inventory, a single bootstrap contract, doc governance, and regression evidence.

## Approved Grouping

### Group 1 – logging-entrypoint-audit (agent: hive-coder)
- **Scope:** Execute Group A duties from the wish: catalog every bootstrap surface (API factories, CLI flows, scripts, tests), map environment variables and their precedence, and capture ownership notes. Deliver inventory tables and environment matrix appended to the wish evidence.
- **Evidence:** Inventory artifact stored under the wish, annotated code references, Death Testament with grep transcripts.
- **Dependencies:** None (kick-off phase).

### Group 2 – logging-bootstrap-unification (agent: hive-coder)
- **Scope:** Implement Group B outcomes: craft the single initialization helper, purge direct `setup_logging()` usage, align entry points (API, CLI, scripts) to the helper, introduce stdlib interception, tidy faux-DEBUG emitters, and refresh logging governance docs/validators.
- **Evidence:** Code diffs, validator coverage, doc edits in `lib/logging/CLAUDE.md`, Death Testament citing verification commands. Coordinate with Group 1 inventory for straggler checks.
- **Dependencies:** Group 1 inventory ready for reference.

### Group 3 – logging-validation-suite (agent: hive-tests)
- **Scope:** Fulfil Group C verification: add pytest coverage for INFO default + DEBUG opt-in, extend CLI smoke assertions, automate log sampling, and assemble the deliverables kit including future-wish recommendations.
- **Evidence:** Passing `uv run pytest …` outputs, log sampler transcript, appended wish evidence, Death Testament summarizing verification artifacts.
- **Dependencies:** Group 2 merged in the worktree.

## Evidence & Reporting Expectations
- Every agent must create a Death Testament under `genie/reports/` with timestamped name.
- Tests executed via `uv run pytest …`; manual commands logged in the Death Testament.
- Any follow-up risks or deferred surfaces documented for orchestration review.

## Next Steps
1. Record this plan in chat for human awareness (done).
2. Create Vibe Kanban tasks for each group under project `Automagik Hive` using this plan as reference.
3. Share task IDs, branch guidance, and this plan path with the human alongside numbered response options.
