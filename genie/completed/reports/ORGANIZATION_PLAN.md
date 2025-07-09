# PagBank Project Organization Plan

## 🚨 Issues Found

### Root Directory Clutter
- ❌ Database files: escalation_patterns.db, test_patterns_demo.db
- ❌ JSON files: tickets.json
- ❌ Orphan scripts: cleanup_dead_code.py, main.py
- ❌ Config files mixed with code

### Scattered Files
- Database files in multiple locations (root, tmp, data/memory)
- Demo scripts in apps/playground/
- Validation test script in knowledge/
- Original utility backup in utils/

## 📋 Organization Plan

### 1. Database Files
```bash
# Move all .db files to data/
escalation_patterns.db → data/escalation_patterns.db
test_patterns_demo.db → data/test_patterns_demo.db
tmp/*.db → data/temp/

# Update code references:
- escalation_systems/pattern_learner.py
- escalation_systems/ticket_system.py
```

### 2. Scripts & Utilities
```bash
# Move to appropriate locations
cleanup_dead_code.py → tmp/cleanup_backup/
main.py → tmp/cleanup_backup/ (appears unused)
tickets.json → data/tickets.json

# Move demo scripts
apps/playground/*.py → demo/playground_examples/
```

### 3. Knowledge Validation
```bash
knowledge/validation_tests.py → tests/unit/test_knowledge_validation.py
```

### 4. Utils Cleanup
```bash
utils/team_utils_original.py → tmp/cleanup_backup/
```

### 5. Config Files
```bash
.mcp.json → Keep in root (MCP config)
CLAUDE.md → Keep in root (dev guide)
README.md → Keep in root
```

## 🔧 Code Updates Required

### 1. Database Path Updates
- Update `escalation_systems/pattern_learner.py` to use `data/escalation_patterns.db`
- Update `escalation_systems/ticket_system.py` to use `data/tickets.json`
- Update memory configs to use `data/memory/` consistently

### 2. Import Updates
- None needed for moving scripts to backup
- Update tests if moving validation_tests.py

## 📁 Final Structure

```
pagbank/
├── .mcp.json            # MCP configuration
├── CLAUDE.md            # Development guide
├── README.md            # Project overview
├── playground.py        # Main entry point
├── pyproject.toml       # Python project config
│
├── data/                # All data files
│   ├── memory/          # Memory databases
│   ├── temp/            # Temporary databases
│   ├── escalation_patterns.db
│   └── tickets.json
│
├── config/              # Configuration only
├── orchestrator/        # Core routing
├── teams/              # Specialist teams
├── knowledge/          # Knowledge base (no tests)
├── memory/             # Memory system
├── escalation_systems/ # Escalation
├── utils/              # Clean utilities only
│
├── tests/              # All tests
│   ├── unit/
│   └── integration/
│
├── demo/               # Demo related
│   └── playground_examples/
│
├── docs/               # Documentation
│   └── knowledge_examples/
│
├── genie/              # Development history
│
└── tmp/                # Temporary files
    └── cleanup_backup/ # Archived scripts
```

## ⚠️ Actions Required

1. Move database files and update code paths
2. Clean up root directory
3. Consolidate demo scripts
4. Remove duplicate/unused files
5. Update any hardcoded paths in code