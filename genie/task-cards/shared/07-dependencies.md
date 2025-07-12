# Task Card: UV Dependencies and Project Setup

## Overview
This task card is part of the PagBank Multi-Agent Platform V2 implementation.

## Reference
- Main strategy: `/genie/active/pagbank-agents-platform-strategy.md`
- Demo app reference: `/genie/agno-demo-app/`

---

### UV Dependencies (pyproject.toml) - Enhanced from demo-app

```toml
[project]
name = "pagbank-multiagents"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    # Core Agno framework
    "agno[aws]>=1.7.0",
    "anthropic>=0.31.0",
    "openai>=1.93.2",
    
    # FastAPI and web stack
    "fastapi[standard]>=0.110.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "httpx>=0.25.0",
    
    # Database stack (from demo-app)
    "alembic>=1.13.0",
    "sqlalchemy>=2.0.0",
    "psycopg[binary]>=3.1.0",
    "pgvector>=0.2.0",
    
    # Enhanced tools (from demo-app)
    "beautifulsoup4>=4.12.0",
    "newspaper4k>=0.9.0",
    "lxml_html_clean>=0.1.0",
    "duckduckgo-search>=4.0.0",
    "google-search-results>=2.4.0",
    "googlesearch-python>=1.2.0",
    "exa_py>=1.0.0",
    "yfinance>=0.2.0",
    
    # File processing
    "pypdf>=3.17.0",
    "python-docx>=0.8.0",
    "pillow>=10.0.0",
    
    # Configuration and utilities
    "pyyaml>=6.0",
    "pycountry>=22.0.0",
    "tiktoken>=0.5.0",
    "nest_asyncio>=1.5.0",
    "typer>=0.9.0",
    
    # Enhanced logging (from demo-app)
    "rich>=13.0.0",
    
    # Current PagBank dependencies
    "pandas>=2.0.0",
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
    "streamlit>=1.28.0",
    "plotly>=5.17.0",
]

[project.scripts]
serve = "api.main:run"
playground = "scripts.playground:main"
implement in V2 = "scripts.implement in V2:main"
setup-dev = "scripts.dev_setup:main"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "black>=24.0.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
    "types-beautifulsoup4>=4.12.0",
    "types-Pillow>=10.0.0",
]

[tool.ruff]
line-length = 110
exclude = ["aienv*", ".venv*", "V2 implementations/*"]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]
"V2 implementations/*" = ["E501", "F401", "F403"]

[tool.mypy]
check_untyped_defs = true
no_implicit_optional = true
warn_unused_configs = true
plugins = ["pydantic.mypy"]
exclude = ["aienv*", ".venv*", "V2 implementations/*"]

[[tool.mypy.overrides]]
module = ["pgvector.*", "agno.*", "exa_py.*", "yfinance.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
log_cli = true
testpaths = ["tests"]
addopts = "-v --tb=short"

[tool.alembic]
script_location = "db/V2 implementations"
prepend_sys_path = ["."]
```

---

## Validation Steps
TODO: Add specific validation steps for this task

## Dependencies
TODO: List dependencies on other task cards

Co-Authored-By: Automagik Genie <genie@namastex.ai>
