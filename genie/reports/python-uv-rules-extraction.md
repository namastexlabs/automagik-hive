# Python/UV Commands - Complete Extraction from CLAUDE.md

## 📍 All Python/UV Rules Found

### Location 1: Lines 58-59 (Development Constraints)
```
- **NEVER use python directly**: Always use `uv run` for python commands
- **UV Package Management**: Use `uv add <package>` for dependencies, never pip
```

### Location 2: Line 337 (Architecture Comment)
```
├── pyproject.toml              # UV package manager (use `uv add <package>` - never pip!)
```

### Location 3: Lines 420-434 (Agent Development Workflow)
```bash
# Package management (NEVER use python directly - always use uv)
uv sync                           # Install dependencies when needed
uv run ruff check --fix          # Lint and fix code automatically
uv run mypy .                    # Type checking for quality assurance
uv run pytest                   # Run tests to validate functionality

# Database operations (when working with data)
uv run alembic revision --autogenerate -m "Description"
uv run alembic upgrade head

# Testing commands for validation
uv run pytest tests/agents/      # Test agent functionality
uv run pytest tests/workflows/   # Test workflow orchestration  
uv run pytest tests/api/         # Test API endpoints
uv run pytest --cov=ai --cov=api --cov=lib  # With test coverage
```

### Location 4: Lines 457-458 (Python Development Requirements)
```
- **Never use python directly**: Always use `uv run` for python commands
- **UV Package Management**: Use `uv add <package>` for dependencies, never pip
```

### Location 5: Lines 524-525, 541 (MCP Integration Examples)
```bash
uv run automagik-hive --status agent    # Check if services are up
uv run automagik-hive --logs agent 50   # Debug any connection issues
uv run automagik-hive --restart agent   # Clean restart of services
```

---

## 🎯 UNIFIED PYTHON/UV DEVELOPMENT RULES

### **PYTHON & UV PACKAGE MANAGEMENT - COMPREHENSIVE**

#### Core Requirements
- **NEVER use python directly** - Always use `uv run` for ALL Python commands
- **UV Package Management** - Use `uv add <package>` for dependencies, NEVER pip
- **Project Configuration** - pyproject.toml is the single source of truth for dependencies

#### Essential UV Commands

##### Package Management
```bash
uv sync                           # Install/sync all dependencies from pyproject.toml
uv add <package>                  # Add new dependency (NEVER use pip install)
uv add --dev <package>            # Add development dependency
uv run <command>                  # Execute any Python command in UV environment
```

##### Code Quality & Testing
```bash
uv run ruff check --fix          # Lint and auto-fix code issues
uv run mypy .                    # Type checking for quality assurance
uv run pytest                    # Run all tests
uv run pytest tests/agents/      # Test agent functionality
uv run pytest tests/workflows/   # Test workflow orchestration  
uv run pytest tests/api/         # Test API endpoints
uv run pytest --cov=ai --cov=api --cov=lib  # With coverage report
```

##### Database Operations
```bash
uv run alembic revision --autogenerate -m "Description"  # Create migration
uv run alembic upgrade head                              # Apply migrations
```

##### Automagik Hive CLI Operations
```bash
uv run automagik-hive --status agent      # Check agent service status
uv run automagik-hive --logs agent 50     # View last 50 log lines
uv run automagik-hive --restart agent     # Restart agent services
uv run automagik-hive --stop agent        # Stop agent services
uv run automagik-hive --start agent       # Start agent services
```

#### Why UV Instead of Python/Pip
1. **Dependency Isolation**: UV creates isolated environments automatically
2. **Reproducible Builds**: Lock files ensure consistent dependencies
3. **Performance**: Faster dependency resolution and installation
4. **Project Standards**: Automagik Hive standardized on UV for all Python operations
5. **No Virtual Env Management**: UV handles environment activation automatically

#### Common Mistakes to Avoid
- ❌ `python script.py` → ✅ `uv run python script.py`
- ❌ `pip install package` → ✅ `uv add package`
- ❌ `pytest` → ✅ `uv run pytest`
- ❌ `mypy .` → ✅ `uv run mypy .`
- ❌ `alembic upgrade head` → ✅ `uv run alembic upgrade head`

---

## 📊 Summary

**Total Instances Found**: 5 locations with Python/UV rules
**Redundancy Level**: High (core rules repeated 3x, examples scattered)
**Unique Information**: 
- 2 core rules (never use python, use uv add)
- 15+ command examples
- Project file reference (pyproject.toml)
- Rationale for UV usage

**Recommendation**: 
1. Keep core rules in Development Constraints section
2. Create single "UV Command Reference" section with ALL commands
3. Remove duplicate statements from other sections
4. Use references like "See UV Command Reference" where needed