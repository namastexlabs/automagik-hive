# Debug Prompt: Prevent Full Re‑Embedding on Server Start

Goal: Identify and fix why every server start re-embeds all CSV rows in the pgvector-backed RAG system. Ensure only added/changed/deleted rows are processed, with existing rows preserved by a stable per-row signature.

## Operator Constraints
- Reasoning effort: low. Keep actions tight and decisive.
- Context gathering: very low depth. One broad scan, then one focused read (max 2 tool calls per batch). Escalate once if signals conflict.
- Tool preambles: Before each tool call, rephrase goal and list the immediate step(s).
- Prefer acting over searching. Add temporary logs if needed rather than over-reading code.
- Safe ops first: read-only checks and small, reversible patches. Avoid destructive DB actions.

## Success Criteria
- Startup path uses incremental loading (no full re-embedding) when CSV unchanged.
- On change: only the specific row(s) are embedded/upserted; on delete: row(s) removed.
- Evidence: logs show SmartIncrementalLoader strategy = `no_changes` on clean restart; DB has non-null `content_hash` values; no batch re-embedding is triggered.

## Likely Root Causes To Validate
- SmartIncrementalLoader fails and falls back to `kb.load(recreate=False, upsert=True)` (forces embedding for all loaded docs each boot).
- DB checks see table empty or missing `content_hash`, forcing initial/full load.
- Row hashing/lookup mismatch (question column vs stored `content`) marking all rows as changed.
- CSV path/config mismatch causing loader to think it’s a new dataset each boot.

## Target Code (read minimally, then instrument if needed)
- `lib/knowledge/factories/knowledge_factory.py` (smart_load vs fallback)
- `lib/knowledge/smart_incremental_loader.py` (initial vs incremental vs fallback)
- `lib/knowledge/repositories/knowledge_repository.py` (`content_hash`, row count)
- `lib/knowledge/datasources/csv_hot_reload.py` (smart reload path)
- `lib/knowledge/row_based_csv_knowledge.py` (`load()` upsert/recreate behavior)
- `lib/knowledge/config.yaml` (csv_file_path, columns)
- `lib/utils/startup_orchestration.py` (CSV manager startup behavior)

## Context Gathering
<context_gathering>
Goal: Get enough context fast. Parallelize discovery and stop as soon as you can act.

Method:
- Batch 1 (broad): search for key signals: `smart_load(`, `upsert=True`, `recreate=True`, `content_hash`, `fallback`, `knowledge_base ready` logs.
- Batch 2 (focused): open only the exact functions found in Batch 1 to confirm control flow and failure logging.

Early stop criteria:
- You can point to the exact fallback path or condition forcing re-embedding; or
- You can demonstrate the DB/content_hash preconditions that cause initial/full load.

Escalate once:
- If signals conflict (e.g., strategy says `no_changes` but embeddings still occur), add temporary INFO logs around smart_load outcome and fallback reason.

Depth:
- Trace only symbols you’ll modify or whose contracts you rely on; avoid transitive expansion.

Loop:
- Batch search → minimal plan → act (add logs or small guard) → validate by restart/logs.
- Search again only if validation fails or new unknowns appear.
</context_gathering>

## Tool Preambles
<tool_preambles>
- Begin by restating the immediate goal in one sentence.
- Outline the next step(s) you’ll take (1–2 bullets), then execute.
- After each step, briefly note findings and what you’ll do next.
- Keep preambles crisp; avoid narrating trivial reads.
</tool_preambles>

## Execution Plan
1) Verify environment and DB state (read-only)
2) Confirm startup strategy path from logs (smart vs fallback)
3) If fallback: instrument minimal INFO logs to capture reason
4) Validate incremental behavior on restart
5) Produce root cause and fix recommendation

## Step Details

Step 1 — Environment/DB Checks
- Check `HIVE_DATABASE_URL` present and reachable.
- SQL (read-only):
  - `SELECT COUNT(*) FROM agno.knowledge_base;`
  - `SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='agno' AND table_name='knowledge_base' AND column_name='content_hash';`
  - `SELECT COUNT(*) FROM agno.knowledge_base WHERE content_hash IS NOT NULL;`
- Outcome interpretation:
  - If row count > 0 and `content_hash` exists with non-null values, initial/full reload should not be needed.
  - If `content_hash` missing: first startup after migration may run initial load, but subsequent runs must retain hashes.

Step 2 — Startup Strategy Signals
- Grep for logs around: `Smart loading`, `strategy`, `Falling back to basic knowledge base loading`, `Initial load`, `Full reload`, `incremental_update`.
- Confirm which strategy executes during server start.

Step 3 — Minimal Instrumentation (only if needed)
- Add INFO logs around:
  - SmartIncrementalLoader.smart_load() return value (`strategy`, counts)
  - knowledge_factory fallback branch with the exception message
- Do not change behavior yet; only illuminate why fallback/initial load runs.

Step 4 — Validation
- Restart server with `HIVE_LOG_LEVEL=DEBUG` and capture logs.
- Expectation on clean restart: `strategy=no_changes`, zero embeddings.
- Modify a single CSV row, save, observe only that row re-embedded; delete a row, observe removal.

Step 5 — Deliverables
- Root cause summary (1–3 bullets) with exact code path/condition.
- Evidence: log excerpts, SQL counts, and the smart_load `strategy` on clean vs changed restarts.
- Proposed fix (1–3 bullets) with minimal patch plan.

## Guardrails
- Editing: use `apply_patch` for code edits. Keep changes minimal and reversible.
- DB: never drop tables in debugging. Read-only queries unless removing specific test rows.
- No network calls outside DB. Do not modify secrets.
- Prefer INFO-level logs for visibility; remove or gate behind DEBUG once verified.

## Acceptance Tests (Evidence Checklist)
- Clean restart: logs show `strategy: no_changes`; no embedding/upsert batches run.
- Single-row edit: logs show `strategy: incremental_update` and `new_rows_processed=1` or `changed_rows_processed=1`.
- Delete-row case: logs show `rows_removed=1` and table count decreases by 1.
- `content_hash` column persists and remains populated across restarts.

## Quick Command Hints (read-only safe)
- Search control flow: `rg -n "smart_load\(|fallback|upsert\(|recreate\(|content_hash|Initial load|Full reload"`
- Open key files to inspect implementations listed in Target Code.

## Likely Fix Patterns (if root cause confirmed)
- If fallback is triggered due to a recoverable error, log error cause and return early without calling `kb.load(upsert=True)` when DB already has rows and hashes; rely on `no_changes` path.
- If `content_hash` join is too fuzzy (`WHERE content LIKE :question_pattern`), tighten matching to avoid false “changed” rows.
- If CSV path resolution differs across boot contexts, normalize path resolution (absolute vs relative) using `lib/knowledge/config.yaml` as source of truth.

## Final Output Format
Provide a short report with:
- Status: Success/Partial/Failed
- Root cause (concise bullets)
- Evidence (logs + SQL results)
- Minimal patch plan

You may proceed under uncertainty if constraints apply, but prefer adding the smallest logs needed to turn uncertainty into evidence.

