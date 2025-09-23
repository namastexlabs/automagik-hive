# 🧞 Forge Planning System Redesign

**Status:** READY_FOR_REVIEW  
**Type:** Meta-Workflow Upgrade (Wish ⇢ Forge orchestration)  
**Complexity:** High (multi-document coordination, agent pipeline changes)  
**Risk:** Process drift, conflicting command guidance, agent routing regressions

## Core Problem Statement
Our planning guidance still reflects the retired TSD/DDD pipeline and multi-document PRD flow. The legacy write-up in this file prescribes per-wish directories (`prd.md`, `context/`, etc.), CCMP command clones, and Bash-based orchestration that no longer exists. Meanwhile, `.claude/commands/wish.md` now defines a streamlined single-file wish template, and `forge.md` / `forge-master.md` encode the actual Forge handoff. Without reconciling these sources, `/wish` authors receive mixed instructions and Forge execution risks diverging from the approved context-engineering plan.

## Desired Outcomes
- One canonical planning blueprint that matches the updated `/wish` instructions and Forge workflow.
- Clear phase gates that lean on real files (`.claude/commands/wish.md`, `forge.md`, `forge-master.md`, `AGENTS.md`).
- Elimination of PRD/DDD terminology and duplicate command catalogs.
- Documented checkpoints for alignment, validation, and rollout so agents can implement confidently.

## Scope & Constraints
- **In scope:** This wish document, `.claude/commands/wish.md`, `forge.md`, `forge-master.md`, `AGENTS.md`, supporting documentation under `genie/`.  
- **Out of scope:** Changes to Forge MCP credentials, backend service behaviour, or creation of new CLI commands beyond what `/wish` and `/forge` already expose.

## Solution Architecture (Phase-Based)

### Phase 0 – Baseline Alignment **(Gate)**
- `@.claude/commands/wish.md`: Confirm the new single-file wish template is authoritative; flag any residual references to PRD/DDD for cleanup.
- `@forge.md`, `@forge-master.md`: Inventory current instructions and highlight mismatches with the updated wish template (branch naming, approval flow, validation evidence).
- `@AGENTS.md`: Note sections that still describe dev-planner/dev-designer or TSD/DDD language.
- **Exit criteria:** Shared understanding of current docs, checklist of stale concepts to remove.

### Phase 1 – Wish Instruction Consolidation (Genie + human doc review)
- Update `.claude/commands/wish.md` (already partially complete via External AI Folder wish) to reference this redesign as the canonical planning example and remove leftover legacy callouts.
- Add cross-links or pointers in `.claude/commands/wish.md` to `forge.md` so authors know how approval handoff works.
- Ensure `genie/wishes/*` guidance consistently references the single-document structure (no `/templates` directories or PRDs).

### Phase 2 – Forge Workflow Harmonization (`hive-coder` if CLI hooks required)
- Revise `forge.md` to reflect the approved wish phases (Phase 0 context gathering → Phase 1 skeleton → Phase 2 decomposition) and ensure approval gating mirrors the new template language.
- Refresh `forge-master.md` so task creation instructions pull context from the single wish file plus `forge.md` checkpoints instead of `prd.md` references.
- Document the alignment between the approved breakdown format and Forge task fields (titles, branches, context `@` markers).

### Phase 3 – Agent & Knowledge Base Updates (Genie-coordinated)
- `@AGENTS.md`: Replace dev-planner/dev-designer references with Wish Architect + Forge Master roles; clarify delegation order (wish → forge → forge-master).
- `@CLAUDE.md` (if necessary): Update high-level onboarding text to reflect the streamlined pipeline.
- Archive or rewrite any other docs referencing the retired workflow (e.g., `wish.md` in repo root, legacy reports).

### Phase 4 – Validation & Rollout (`hive-tests` for doc lint checks)
- Run `rg "PRD"` and `rg "TSD"` to confirm terminology removal.
- Execute documentation lint/format checks if available (e.g., `uv run python scripts/check_docs.py` when applicable).
- Dry-run `/wish` → `/forge` on a sample wish (no execution) to ensure instructions line up end-to-end.
- Capture findings and update this wish status to `READY_FOR_EXECUTION` once stakeholders approve.

## Orchestration & Agent Routing
- Documentation updates → capture in Death Testament for Genie/human follow-up.
- Any automation or CLI tweaks tied to Forge interaction → `hive-coder` (after docs stabilized).
- Test authoring or doc validation scripts → `hive-tests`.
- Formatting lint (ruff/mypy) → `hive-quality-ruff`, `hive-quality-mypy` if code changes surface.

## Acceptance Criteria
- ✅ `.claude/commands/wish.md`, `forge.md`, and `forge-master.md` reference the same phase names, approval gates, and evidence expectations.
- ✅ No repository documentation instructs users to create PRDs, DDDs, or per-wish subdirectories.
- ✅ `AGENTS.md` reflects the Wish Architect ⇢ Forge Master orchestration without legacy roles.
- ✅ A sample wish-to-forge walkthrough in this document matches the actual command guides.

## Verification Protocol
1. `rg "PRD" -n` and `rg "dev-planner" -n` (expect hits only in historical archives if any).  
2. `rg "Phase 0" .claude/commands/wish.md forge.md` (ensure consistent wording).  
3. `uv run pytest tests/cli/test_forge_workflow.py -v` (or create equivalent) to cover the approval + task-creation flow.  
4. Manual dry-run: read a wish, follow `/forge` instructions, verify all checkpoints exist before contacting Forge MCP.

## Rollback Plan
If the new workflow causes confusion, restore the previous version of this wish and associated docs from Git history (`git checkout <commit> -- genie/wishes/forge-planning-system-redesign.md .claude/commands/wish.md forge.md forge-master.md`) and document the feedback for another iteration.

## Success Metrics
- ✅ Wish authors can draft using the new template without referencing multiple conflicting guides.  
- ✅ Forge operators follow a single approval script that mirrors the docs.  
- ✅ Agent routing logs show `/wish` → `/forge` delegation without manual patching.  
- ✅ Stakeholders confirm the planning system feels lighter and TSD/DDD language is fully removed.

## Questions for Clarification
- Should we introduce automated linting for wish documents (e.g., schema or front-matter checks)?
- Is additional CLI support desired for surfacing approved wish metadata before `/forge` runs?

Let’s crystallize this redesign so every future wish flows cleanly into Forge execution! 🧞✨
