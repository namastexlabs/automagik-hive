  Codebase Comment Cleanup and Standardization

  Task Overview

  Analyze and clean up ALL comments in the Genie Agents codebase to
  align with our established commenting standards. This is a
  systematic code quality improvement task.

  Our Commenting Rules (from CLAUDE.md)

  🚫 AVOID VERBOSE COMMENTS

  - Never add explanatory comments in parentheses like:
    - # Load config (required for startup)
    - # Create team (V2 architecture)
    - # Send notification (non-blocking with delay)
    - # Add middleware (unified from main.py)

  ✅ CONCISE COMMENTS

  - Use brief, clear comments like:
    - # Load config
    - # Create team
    - # Send notification
    - # Add middleware

  RATIONALE

  Code should be self-documenting; verbose comments create noise and
  maintenance overhead.

  Search and Analysis Phase

  Step 1: Find All Comments
  # Search for all comments with verbose patterns
  grep -r "# .* (" --include="*.py" .
  grep -r "# .*-.*-" --include="*.py" .
  grep -r "# .*:" --include="*.py" . | grep -v
  "def\|class\|Args:\|Returns:\|Raises:"
  grep -r "# .*\[.*\]" --include="*.py" .
  grep -r "# .*TODO\|FIXME\|NOTE\|WARNING" --include="*.py" .

  Step 2: Categorize Comments
  - Verbose explanatory comments (need cleanup)
  - Architecture/implementation details (usually should be removed)
  - TODO/FIXME comments (evaluate if still needed)
  - Docstrings (keep as-is, these are good)
  - Brief functional comments (keep as-is)

  Cleanup Tasks

  Priority 1: Remove Verbose Parenthetical Explanations

  Pattern: # Something (explanation here)
  Action: Convert to # Something or remove entirely

  Examples:
  - # Initialize database (with auto-migrations) → # Initialize 
  database
  - # Load agents (from YAML configs) → # Load agents
  - # Create storage (PostgreSQL with schema upgrade) → # Create 
  storage

  Priority 2: Remove Implementation Details

  Pattern: Comments explaining HOW instead of WHAT
  Action: Remove entirely (code should be self-documenting)

  Examples:
  - # Use factory pattern to create versioned components → Remove
  - # This replaces the old database-based approach → Remove
  - # Following Agno v2.0 patterns for better performance → Remove

  Priority 3: Clean Architecture References

  Pattern: Comments with version numbers, architecture details,
  cleanup references
  Action: Simplify or remove

  Examples:
  - # V2 Architecture implementation → # Create team or remove
  - # API Architecture Cleanup - T-005 → Remove
  - # Following SOLID principles here → Remove

  Priority 4: Evaluate TODOs and FIXMEs

  Pattern: # TODO:, # FIXME:, # NOTE:
  Action: Either implement the change or remove the comment

  Priority 5: Clean Section Headers

  Pattern: Long decorative comment blocks
  Action: Simplify to essential information only

  Examples:
  # ==================================================================
  ===========
  # Agent Configuration Loading and Factory Management System (V2 
  Architecture)
  # ==================================================================
  ===========
  →
  # Agent factory

  File-by-File Cleanup Process

  1. Read each Python file
  2. Identify all comments using the patterns above
  3. Apply cleanup rules:
    - Remove verbose parenthetical explanations
    - Remove implementation detail comments
    - Simplify architecture references
    - Evaluate and resolve TODOs
    - Keep only essential functional comments
  4. Ensure no information loss: If a comment contains truly important
   information that isn't obvious from the code, refactor the code to
  be more self-documenting rather than keeping the verbose comment

  Key Areas to Focus On

  High Priority Files

  - api/serve.py (already partially cleaned)
  - lib/utils/version_factory.py
  - lib/versioning/agno_version_service.py
  - ai/agents/registry.py
  - ai/teams/ana/team.py
  - ai/workflows/*/workflow.py

  Comment Patterns to Target

  1. # ✅ SOMETHING (explanation)
  2. # Create/Load/Initialize X (details about how)
  3. # Following [pattern/architecture]
  4. # This replaces/updates [old approach]
  5. # [Technology] integration (with details)

  Quality Standards

  Good Comments (Keep These)

  # Load configuration
  # Create agent
  # Send notification
  # Initialize storage
  # Start server

  Bad Comments (Clean These)

  # Load configuration (required for startup with validation)
  # Create agent (using factory pattern with version support)
  # Send notification (asynchronous with retry logic)
  # Initialize storage (PostgreSQL with auto-schema upgrade)
  # Start server (with development hot-reload capabilities)

  Execution Instructions

  For each file:
  1. Search for verbose comment patterns
  2. Clean according to the rules above
  3. Test that functionality remains unchanged
  4. Verify that the code is still understandable without verbose
  comments
  5. Document any cases where important information might be lost

  Deliverable:
  - Clean, standardized comments across the entire codebase
  - Improved code readability through self-documenting patterns
  - Consistent commenting style following established standards
  - Removal of maintenance overhead from verbose explanatory comments

  Success Criteria:
  - No comments with parenthetical explanations
  - No architecture/implementation detail comments
  - All TODOs either resolved or confirmed as necessary
  - Code remains fully understandable and maintainable
  - Consistent brief, functional comments where needed

  ---