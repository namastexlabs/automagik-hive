# Task: Review Imports and Dependencies

## Objective
Review all imports and dependencies for consistency and remove unused imports across the codebase.

## Priority: MEDIUM
**Code quality and maintenance optimization**

## Instructions

### 1. Audit Import Statements
```bash
# Search for import inconsistencies:
find . -name "*.py" -not -path "./.venv/*" -exec grep -l "^import\|^from" {} \;

# Common patterns to standardize:
# - Agno framework imports
# - Model imports (Claude, OpenAI)
# - Tool imports
# - Local module imports
```

### 2. Identify Unused Imports
- [ ] Scan all Python files for unused imports
- [ ] Remove imports not referenced in code
- [ ] Consolidate duplicate imports
- [ ] Standardize import order and style

### 3. Validate Dependency Consistency
```python
# Standard import patterns to enforce:

# Agno Framework
from agno.agent import Agent
from agno.team import Team
from agno.models.anthropic import Claude
from agno.knowledge.csv import CSVKnowledgeBase
from agno.vectordb.pgvector import PgVector
from agno.memory.v2.memory import Memory

# Local imports
from config.settings import settings
from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager
```

### 4. Check pyproject.toml Dependencies
- [ ] Validate all listed dependencies are used
- [ ] Remove unused dependencies
- [ ] Check for version conflicts
- [ ] Ensure dev dependencies are separate

### 5. Standardize Import Order
```python
# Recommended import order:
# 1. Standard library imports
# 2. Related third party imports
# 3. Agno framework imports
# 4. Local application imports

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from agno.agent import Agent
from agno.team import Team
from agno.models.anthropic import Claude

from config.settings import settings
from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
```

## Completion Criteria
- [ ] All unused imports removed
- [ ] Import order standardized
- [ ] Dependencies validated
- [ ] pyproject.toml cleaned up
- [ ] Import consistency achieved

## Dependencies
- Codebase analysis (complete)

## Testing Checklist
- [ ] Run import checks: `python -m flake8 --select=F401`
- [ ] Validate all imports resolve correctly
- [ ] Check for circular import issues
- [ ] Test that removed imports don't break functionality
- [ ] Verify pyproject.toml dependencies are minimal
- [ ] Run linting to catch import issues

## Files to Review
All Python files, focusing on:
- `/teams/*.py`
- `/orchestrator/*.py`
- `/knowledge/*.py`
- `/memory/*.py`
- `/escalation_systems/*.py`
- `/utils/*.py`
- `/config/*.py`
- `pyproject.toml`

## Tools to Use
```bash
# Check for unused imports
uv run python -m flake8 --select=F401

# Sort imports consistently
uv run python -m isort .

# Format code
uv run python -m black .

# Check dependencies
uv run python -m pip list --not-required
```

## Success Metrics
- Unused imports: 0 ❌ (35+ identified)
- Import order: Standardized ❌
- Dependencies: Minimal ❌
- Consistency: Achieved ❌
- Code quality: Improved ❌

## Notes
- Previous analysis found 35+ unused imports
- Focus on major files with most import issues
- Use automated tools where possible
- Test functionality after import cleanup