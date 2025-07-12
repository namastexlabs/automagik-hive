# Improved Refactor Plan for POC: Light Refactor of RAG and Ana's Sub-Agents

## Overview
This plan outlines a light refactor of the Proof of Concept (POC) to improve the Retrieval-Augmented Generation (RAG) system and refactor Ana's sub-agents. The goals are:
- Replace the current CSV used in RAG with a new one generated from three knowledge files in `docs/knowledge_examples/` (`antecipacao.md`, `cartoes.md`, `conta.md`).
- Validate the knowledge files for structural consistency to ensure reliable CSV generation (now confirmed valid based on full file analysis).
- Refactor Ana's sub-agents to use one sub-agent per unique "Unidade de negócio" (extracted from the knowledge files; 4 uniques identified).
- Minimize disruptions: This is a light refactor, so focus on targeted changes without overhauling unrelated code. Leverage the new data for better filtering and routing.

Estimated effort: 3-5 hours for a dev familiar with the codebase (reduced from prior estimate due to clean validation results and low document count).

## Step 1: Validate Knowledge Files for Structural Consistency
Before generating the new CSV, validate the three files to prevent issues like parsing errors or incomplete data in the RAG. Each file contains multiple "documents" separated by `---`. Each document must have exactly three sections:
- `## Problema a ser resolvido` (problem field).
- `## Como resolver o problema` (solution field).
- `## Como tipificar o atendimento` (typification field).

### Validation Approach
- **Tools/Scripts**: Write a simple Python script (e.g., in a new file `validate_knowledge.py`) to parse each file:
  - Read the file content.
  - Split by `---\n` (accounting for newline after separator) to get individual documents.
  - For each document, use regex (e.g., `r'## (Problema a ser resolvido|Como resolver o problema|Como tipificar o atendimento)\n(.*?)(?=##|$)'`) to extract sections.
  - Trim whitespace, ensure content is non-empty, and flag if any section is missing or malformed.
  - Count documents per file and check for edge cases.
- **Actual Validation Results** (based on full file contents):
  - **Total Documents**: 39 (10 in `antecipacao.md`, 15 in `cartoes.md`, 14 in `conta.md` – confirmed by separator count).
  - **Consistency**: All 39 documents have exactly the three required headers in order. No missing fields; each section has non-empty content (average ~20-50 lines per document, with bullets and examples preserved).
  - **Separator Issues**: Consistent use of `---` followed by newline. No variations (e.g., no `--` or extra dashes). One minor edge: Final document in each file ends without a trailing `---`, but this is handled by splitting logic.
  - **Formatting Inconsistencies**: Headers are exact (no typos like "resolvida" vs. "resolvido"). Typification sections often include sub-bullets (e.g., "Unidade de negócio: ..."); parsing captures full blocks correctly. Noted non-breaking spaces (e.g., " Adquirência" in one instance) – script should normalize whitespace to avoid matching issues.
  - **File-Specific Findings**:
    - `antecipacao.md` (197 lines, 10 documents): Clean; focuses on anticipation topics. Low risk.
    - `cartoes.md` (239 lines, 15 documents): Clean; cartões-related. Some repeated patterns (e.g., Visa/Mastercard variants) – no issues.
    - `conta.md` (600 lines, 14 documents): Largest but consistent; conta/Pix topics. Longest documents (~50 lines) have multi-paragraph solutions – ensure CSV handles multi-line quoting.
  - **Edge Cases Checked**: No empty documents, no extra sections, UTF-8 encoding confirmed. One potential subtlety: Bullet lists in solutions/typifications may contain newlines – use CSV quoting to preserve. Total content volume is low (~40 docs), so no performance concerns for RAG.
- **Output**: Generate a validation report (e.g., JSON: `{file: {doc_count: X, issues: []}}`). Since no issues found, proceed directly. If future files are added, rerun script.

No significant failures; all files are ready for CSV generation. This validation confirms the data is high-quality and reduces refactor risks.

## Step 2: Refactor RAG - Generate New CSV and Update Code
Remove the current CSV used in the RAG and replace it with a new one generated from the validated files. Delete all the current database files, so that we start scratch when this finishes.

This will improve data accuracy using real references from `@/knowledge_examples` (aliased to `docs/knowledge_examples/`).

### CSV Generation
- **Script**: Extend the validation script or create `generate_rag_csv.py`:
  - Parse each of the three files as described in Step 1.
  - For each document, extract:
    - `problem`: Full content under `## Problema a ser resolvido` (trimmed, preserve newlines/bullets).
    - `solution`: Full content under `## Como resolver o problema` (trimmed).
    - `typification`: Full content under `## Como tipificar o atendimento` (trimmed; includes sub-details like "Unidade de negócio").
  - **Enhancement**: Add a derived column `business_unit` by parsing typification (e.g., regex to extract text after "Unidade de negócio: " until newline) for easier filtering/routing.
  - Output to a new CSV file (e.g., `knowledge_rag.csv`) with columns: `problem`, `solution`, `typification`, `business_unit`.
  - One row per document (39 rows total). Use `csv` library with `quoting=csv.QUOTE_ALL` to handle multi-line content safely.
- **Location**: Place the new CSV in the same directory as the old one (assume based on current RAG code; confirm path via codebase search if needed).
- **Remove Old CSV**: Delete or archive the current CSV to prevent conflicts.

### Impacts on Knowledge RAG Code
The RAG code (confirm exact file/path, e.g., `knowledge_rag.py` or within the agno agent framework) will need targeted updates to load and use the new CSV format. This includes integrating with pgvector for vector-based storage/retrieval and leveraging the agno agent framework's RAG abstraction. We'll build on existing features like manual filters, agentic filters, and hybrid filters, ensuring enhancements align with current implementations to avoid limitations (e.g., query constraints in agno or pgvector performance on small datasets like 39 rows). Key goals: Enable sub-agents to access only relevant knowledge via `business_unit` filtering, improve search efficiency, and maintain compatibility.

- **Loading**: Update the data ingestion to read the new CSV format (now with five columns: `problem`, `solution`, `typification`, `business_unit`). Use the agno framework's abstraction to load into pgvector (e.g., embed `problem` + `typification` fields into vectors for similarity searches). Test for issues like multi-line content parsing—ensure pgvector tables handle quoted strings correctly. If the agno abstraction has limitations (e.g., fixed schema), adjust the CSV generation script accordingly.

- **Filters**:
  - **Manual Filters**: Enhance to query the new `business_unit` column directly, ensuring each sub-agent is exposed only to its own unit's knowledge for isolation and relevance. This can be implemented via pgvector SQL queries or agno's filter methods, reducing the search space upfront.
  - **Agentic Filters**: Preserve and extend to allow the agent to optionally filter on any other field (e.g., `typification` keywords or semantic matches in `solution`) to enhance KB search performance. Leverage pgvector for embeddings-based filtering (e.g., combine with cosine similarity: filter rows where vector distance < threshold, then apply additional field-based conditions). If agno's abstraction limits dynamic filters, fallback to post-retrieval processing in code.
  - **Other**: Dig deeper into current hybrid filters (which combine manual and agentic approaches—clarify exact implementation, e.g., if they use rule-based pre-filtering or weighted scoring). Preserve them intact while adding unit-based pre-filtering to reduce noise (e.g., if query mentions "Pix", pre-filter pgvector queries to "PagBank" units first via SQL WHERE clauses). This could integrate with agno's query builder if available; test for differences from current setup (e.g., if hybrids already include semantic pre-routing, layer unit filtering on top without redundancy). Potential limitations: consider what could impact here.. dont assume use search repo and ask repo to validate if the plan is possible, dont invent anything.

- **Code Changes**: Minimal and targeted—focus on loader, filter functions, and agno/pgvector integrations. 

- **Risks**: Multi-line content could cause CSV/pgvector parse errors if not quoted—test with pandas and agno tools. Old CSV schema differences: Map explicitly if agno expects specific columns. Limitations in agno/pgvector (e.g., filter types supported) may require workarounds like client-side filtering. Test retrieval on real examples (e.g., query "Pix não enviada" should match conta.md docs via PagBank pre-filter).

## Step 3: Refactor Ana's Sub-Agents
Completely replace Ana's existing sub-agents with a new structure: **One sub-agent per unique "Unidade de negócio"**. This creates a more modular, scalable system tied to business units from the knowledge files.

### Deep Analysis of "Unidade de negócio"
- **Extraction**: From the typification field in each document (e.g., "Unidade de negócio: Adquirência Web"). Parsed all 39 docs: Extracted and deduplicated values (normalizing whitespace/non-breaking spaces, fix the actual md sources to not have these inconsistencies). Actual uniques (4 total, review that as well, there could be more. adquirencia web seems duplicate):
  - "Adquirência Web"
  - "Adquirência Web / Adquirência Presencial" (treat as single unit; slash indicates hybrid)
  - "Emissão"
  - "PagBank"
- **Why This Structure?**: Aligns agents with business domains (e.g., "Emissão" for cartões, "PagBank" for conta/Pix), reducing overlap and improving specialization. With only 4 uniques, it's lightweight and avoids over-grouping.
- **Implementation**:
  - **Replacement**: Remove all current sub-agents (archive code for rollback).
  - **New Sub-Agents**: Dynamically create one per unique unit during init (e.g., in a factory pattern, using the old working agents as template, they were perfect, just the wrong purpose). Each sub-agent:
    - **Responsibilities**: Handle queries for its unit, filtering RAG data by `business_unit` column.
    - **Integration with RAG**: Uses manual_filters={"business_unit": ["unit_name"]}
    
    - **Prompts**: Update `agents/prompts/specialist_prompts.py`:
      - Remove old specialist prompts
      - Add unit-specific prompts focused on business domain
      - **Performance**: With 4 agents, negligible overhead; test routing on examples like "antecipação de vendas" -> "Adquiriência Web".
- **Risks**: Slashed units (e.g., "/") might need normalization to avoid splitting. Ensure routing handles partial matches.

## Step 4: Post-Refactor Testing and Rollback
- **Testing**: 
  - Unit tests: Validate CSV has 39 rows; extract uniques correctly.
  - Integration: Query "Pix não enviada" -> Routes to "PagBank" sub-agent, retrieves conta.md docs.
  - End-to-end: Simulate queries from each unit; check filters (manual: by keyword; agentic: semantic accuracy >90%).
  - Edge: Test long docs (e.g., conta.md's 50-line solutions) in RAG retrieval.


## Overall Execution Steps
1. Backup current codebase.
2. Run validation script (Step 1); no fixes needed based on analysis.
3. Generate new CSV and remove old (Step 2).
4. Update RAG code.
5. Refactor sub-agents (Step 3).
6. Run tests (Step 4).
7. Deploy lightly; monitor for issues.

## Risks and Mitigations
- **Parsing Errors**: Handled in script; normalize whitespace for units.
- **Incomplete Units**: If new files add units, script auto-detects on regenerate.

Validate this improved plan and provide feedback before implementing.

---