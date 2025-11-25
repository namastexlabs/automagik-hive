# 🧞 GENIE FRONTMATTER INTERPRETER WISH

**Status:** DRAFT

## Executive Summary

Extend the Hive YAML interpreter to recognize and parse Genie agent frontmatter (`.md` files with YAML between `---` delimiters), enabling agents defined in Genie format to be discovered and executed by Hive without manual conversion.

## Current State Analysis

**What exists:**
- Hive YAML interpreter: Pure `.yaml` files with AGENT_SCHEMA validation in `hive/scaffolder/`
- Genie frontmatter format: Markdown files with YAML between `---` delimiters in `.genie/agents/`, `.genie/code/agents/`, `.genie/spells/`
- Separate validation systems: Hive uses `validator.py` with schema validation, Genie uses `.genie/scripts/helpers/validate-frontmatter.js`

**Gap identified:**
- Two incompatible YAML interpretation systems prevent seamless integration
- Genie agents require manual conversion to Hive format
- No discovery mechanism for `.md` files with frontmatter in Hive
- Model name mappings differ between systems (e.g., `sonnet` vs `anthropic:claude-sonnet-4-20250514`)

**Solution approach:**
- Add frontmatter parser to extract YAML from markdown files
- Create mapper to convert Genie schema to Hive schema
- Extend discovery system to detect `.md` files alongside `config.yaml`
- Maintain backward compatibility with existing Hive `.yaml` format

## Change Isolation Strategy

- **Isolation principle:** New frontmatter parsing and mapping logic isolated in dedicated modules (`frontmatter_parser.py`, `genie_mapper.py`)
- **Extension pattern:** Extend discovery system without modifying core YAML loading; add parallel path for `.md` files
- **Stability assurance:** Existing `config.yaml` format maintains priority; `.md` files are secondary discovery option; all current Hive agents continue working unchanged

## Success Criteria

✅ Frontmatter parser correctly extracts YAML from `.md` files with `---` delimiters
✅ Mapper accurately converts Genie format to Hive-compatible agent configuration
✅ Discovery system finds Genie agents in `.genie/agents/` and `.genie/code/agents/`
✅ Agent ID derivation follows pattern: `.genie/agents/review.md` → `genie/review`
✅ Model names convert correctly: `sonnet` → `anthropic:claude-sonnet-4-20250514`
✅ Unit tests achieve ≥90% coverage for parser and mapper
✅ Integration tests validate end-to-end discovery and execution
✅ Existing Hive `.yaml` agents continue working without modification
✅ Documentation updated in `hive/scaffolder/README.md`

## Never Do (Protection Boundaries)

❌ Modify existing `config.yaml` parsing logic or break backward compatibility
❌ Change priority: `config.yaml` must always take precedence over `.md` files
❌ Remove or weaken existing AGENT_SCHEMA validation
❌ Introduce dependencies beyond PyYAML (already available)
❌ Auto-convert Genie agents to `.yaml` format (maintain source format)
❌ Modify `.genie/scripts/helpers/validate-frontmatter.js` (Genie-side validation stays separate)

## Technical Architecture

### Component Structure

Hive Scaffolder:
├── hive/scaffolder/
│   ├── generator.py              # Current YAML loading (line 317-340)
│   ├── validator.py              # AGENT_SCHEMA validation (line 28-45)
│   ├── discovery.py              # Agent discovery system
│   ├── frontmatter_parser.py     # NEW: Markdown frontmatter extraction
│   └── genie_mapper.py           # NEW: Genie → Hive schema conversion

Genie Agents:
├── .genie/agents/                # Genie agent definitions with frontmatter
├── .genie/code/agents/           # Code-specific Genie agents
└── .genie/spells/                # Genie spell definitions (optional support)

Tests:
├── tests/scaffolder/
│   ├── test_frontmatter_parser.py    # NEW: Parser unit tests
│   ├── test_genie_mapper.py          # NEW: Mapper unit tests
│   └── test_genie_discovery.py       # NEW: Integration tests

### Naming Conventions

- Parser module: `frontmatter_parser.py` with `parse_markdown_frontmatter()` function
- Mapper module: `genie_mapper.py` with `map_genie_to_hive()` function
- Schema constant: `GENIE_AGENT_SCHEMA` in `validator.py`
- Agent ID pattern: `genie/{path-relative-to-genie-dir}` (e.g., `genie/code/fix`)
- Test files: `test_frontmatter_parser.py`, `test_genie_mapper.py`, `test_genie_discovery.py`

### Field Mapping Reference

| Genie Field | Hive Field | Transformation | Example |
|-------------|------------|----------------|---------|
| `name` | `agent.name` | Direct copy | `fix` → `fix` |
| `description` | `agent.description` | Direct copy | `Apply fixes...` → `Apply fixes...` |
| `genie.executor` | `agent.executor_chain` | New field (list) | `[CLAUDE_CODE]` → `["claude_code"]` |
| `forge.<exec>.model` | `agent.model` | Model name conversion | `sonnet` → `anthropic:claude-sonnet-4-20250514` |
| Markdown content | `instructions` | Direct copy (post-frontmatter) | Full markdown body → `instructions` string |
| `genie.background` | `settings.background` | New field (bool) | `true` → `true` |
| `forge.*.dangerously_skip_permissions` | `settings.skip_permissions` | Boolean flag | `true` → `true` |

### Model Conversion Table

| Genie Model | Hive Model |
|-------------|------------|
| `sonnet` | `anthropic:claude-sonnet-4-20250514` |
| `opus` | `anthropic:claude-opus-4-20250514` |
| `haiku` | `anthropic:claude-haiku-3-5-20241022` |
| `gpt-5-codex` | `openai:gpt-4o` |
| `opencode/glm-4.6` | `openai:gpt-4o` (fallback) |

## Task Decomposition

### Dependency Graph

```
A[Foundation: Parser & Mapper] ---> B[Schema Validation]
A & B ---> C[Discovery Integration]
C ---> D[Testing & Documentation]
```

### Group A: Foundation (Parallel Tasks)

Dependencies: None | Execute simultaneously

**A1-frontmatter-parser**: Implement markdown frontmatter extraction
@hive/scaffolder/generator.py [context for current YAML loading patterns]
Creates: `hive/scaffolder/frontmatter_parser.py`
Exports: `parse_markdown_frontmatter(file_path: str) -> dict` function
Success: Function extracts YAML between `---` delimiters and returns `{"frontmatter": dict, "content": str}`

**A2-genie-mapper**: Implement Genie → Hive schema converter
@.genie/code/agents/fix.md [reference for Genie format]
@hive/scaffolder/validator.py [context for Hive AGENT_SCHEMA]
Creates: `hive/scaffolder/genie_mapper.py`
Exports: `map_genie_to_hive(genie_config: dict, markdown_content: str) -> dict` function
Success: Mapper converts all Genie fields to Hive format with model name translation

**A3-model-converter**: Create model name translation utility
@hive/scaffolder/genie_mapper.py [location for utility function]
Creates: `convert_genie_model_to_hive(model_name: str) -> str` helper function
Exports: Model conversion logic used by mapper
Success: All model names in conversion table handled correctly with fallback

### Group B: Schema Validation (After A)

Dependencies: A1-frontmatter-parser, A2-genie-mapper

**B1-genie-schema**: Define Genie agent validation schema
@hive/scaffolder/validator.py [context for AGENT_SCHEMA pattern]
Modifies: Adds `GENIE_AGENT_SCHEMA` constant
Exports: Validation rules for Genie frontmatter format
Success: Schema validates required fields (name, description) and optional fields (genie, forge)

**B2-schema-validator**: Add Genie schema validation function
@hive/scaffolder/validator.py [location for validation logic]
Modifies: Adds `validate_genie_agent(config: dict) -> bool` function
Exports: Validation function for Genie agents
Success: Validation rejects invalid configs and accepts valid Genie frontmatter

### Group C: Discovery Integration (After A & B)

Dependencies: All tasks in A and B

**C1-discovery-extension**: Extend agent discovery for .md files
@hive/scaffolder/discovery.py [context for current discovery logic]
Modifies: Adds `.md` file detection alongside `config.yaml`
Exports: Updated `discover_agents()` function with frontmatter support
Success: Discovery finds both `.yaml` and `.md` agent definitions

**C2-agent-id-derivation**: Implement Genie agent ID naming
@hive/scaffolder/discovery.py [location for ID derivation]
Modifies: Adds `derive_genie_agent_id(file_path: str) -> str` function
Exports: Agent ID generator following `genie/{path}` pattern
Success: `.genie/agents/review.md` → `genie/review`, `.genie/code/agents/fix.md` → `genie/code/fix`

**C3-discovery-priority**: Implement discovery precedence logic
@hive/scaffolder/discovery.py [location for precedence handling]
Modifies: Adds logic to prefer `config.yaml` over `agent.md` when both exist
Exports: Deterministic agent loading order
Success: When directory contains both formats, `config.yaml` loads first

**C4-genie-paths**: Add .genie directory paths to discovery
@hive/scaffolder/discovery.py [location for search paths]
Modifies: Adds `.genie/agents/` and `.genie/code/agents/` to discovery paths
Exports: Extended search path configuration
Success: Discovery traverses Genie directories and finds frontmatter agents

### Group D: Testing & Documentation (After C)

Dependencies: Complete integration (all C tasks)

**D1-parser-tests**: Unit tests for frontmatter parser
@hive/scaffolder/frontmatter_parser.py [test target]
Creates: `tests/scaffolder/test_frontmatter_parser.py`
Exports: ≥90% coverage for parser edge cases
Success: Tests pass for valid frontmatter, missing delimiters, malformed YAML, empty content

**D2-mapper-tests**: Unit tests for Genie → Hive mapper
@hive/scaffolder/genie_mapper.py [test target]
Creates: `tests/scaffolder/test_genie_mapper.py`
Exports: ≥90% coverage for field mapping and model conversion
Success: Tests validate all field mappings and model name conversions

**D3-discovery-tests**: Integration tests for end-to-end flow
@hive/scaffolder/discovery.py [test target]
Creates: `tests/scaffolder/test_genie_discovery.py`
Exports: Integration test coverage for discovery → parsing → mapping
Success: Tests load real Genie agents from `.genie/agents/` and validate execution

**D4-edge-case-tests**: Tests for error handling and edge cases
@tests/scaffolder/ [test suite location]
Creates: Additional test cases in existing test files
Exports: Edge case coverage (missing fields, invalid models, malformed frontmatter)
Success: Error messages are clear and validation gracefully handles invalid inputs

**D5-documentation**: Update scaffolder documentation
@hive/scaffolder/README.md [doc target]
Modifies: Adds section on Genie frontmatter support
Exports: User-facing documentation for frontmatter format
Success: Docs explain discovery precedence, field mapping, and model conversion

**D6-examples**: Create example Genie agent for testing
@examples/ [create if not exists]
Creates: `examples/genie-agent-example.md` with frontmatter
Exports: Reference implementation for users
Success: Example agent loads successfully and demonstrates all features

## Implementation Examples

### Frontmatter Parser Pattern

```python
# hive/scaffolder/frontmatter_parser.py
import re
import yaml
from pathlib import Path
from typing import Dict, Any

FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n(.*)$', re.DOTALL)


def parse_markdown_frontmatter(file_path: str) -> Dict[str, Any]:
    """
    Parse markdown file with YAML frontmatter.

    Args:
        file_path: Path to markdown file with frontmatter

    Returns:
        {
            "frontmatter": dict,  # Parsed YAML between --- delimiters
            "content": str        # Markdown content after frontmatter
        }

    Raises:
        ValueError: If file has no frontmatter or malformed YAML
        FileNotFoundError: If file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Markdown file not found: {file_path}")

    content = path.read_text(encoding="utf-8")
    match = FRONTMATTER_PATTERN.match(content)

    if not match:
        raise ValueError(f"No frontmatter found in {file_path}")

    yaml_content, markdown_content = match.groups()

    try:
        frontmatter = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in frontmatter: {e}")

    return {
        "frontmatter": frontmatter or {},
        "content": markdown_content.strip()
    }
```

### Genie → Hive Mapper Pattern

```python
# hive/scaffolder/genie_mapper.py
from typing import Dict, Any, List


MODEL_CONVERSION_MAP = {
    "sonnet": "anthropic:claude-sonnet-4-20250514",
    "opus": "anthropic:claude-opus-4-20250514",
    "haiku": "anthropic:claude-haiku-3-5-20241022",
    "gpt-5-codex": "openai:gpt-4o",
    "opencode/glm-4.6": "openai:gpt-4o",  # fallback
}


def convert_genie_model_to_hive(model_name: str) -> str:
    """Convert Genie model name to Hive model identifier."""
    return MODEL_CONVERSION_MAP.get(model_name, "openai:gpt-4o")


def map_genie_to_hive(genie_config: Dict[str, Any], markdown_content: str) -> Dict[str, Any]:
    """
    Convert Genie frontmatter format to Hive agent config.

    Args:
        genie_config: Parsed Genie frontmatter YAML
        markdown_content: Markdown content after frontmatter

    Returns:
        Hive-compatible agent configuration dict
    """
    # Extract executor and model from forge config
    genie_section = genie_config.get("genie", {})
    forge_section = genie_config.get("forge", {})

    # Get first executor (Hive uses single model, Genie supports multiple)
    executors = genie_section.get("executor", [])
    if isinstance(executors, str):
        executors = [executors]

    primary_executor = executors[0] if executors else "CLAUDE_CODE"

    # Get model from forge config for primary executor
    forge_config = forge_section.get(primary_executor, {})
    genie_model = forge_config.get("model", "sonnet")
    hive_model = convert_genie_model_to_hive(genie_model)

    # Build Hive agent config
    hive_config = {
        "agent": {
            "name": genie_config.get("name"),
            "id": genie_config.get("name"),  # Use name as ID by default
            "description": genie_config.get("description"),
            "model": hive_model,
        },
        "instructions": markdown_content,
        "tools": [],  # Genie doesn't specify tools in frontmatter
        "storage": {"type": "sqlite"},  # Default Hive storage
    }

    # Add optional fields
    if executors:
        hive_config["agent"]["executor_chain"] = [e.lower() for e in executors]

    if genie_section.get("background") is not None:
        hive_config.setdefault("settings", {})["background"] = genie_section["background"]

    if forge_config.get("dangerously_skip_permissions"):
        hive_config.setdefault("settings", {})["skip_permissions"] = True

    return hive_config
```

### Discovery Integration Pattern

```python
# hive/scaffolder/discovery.py (modifications)
from pathlib import Path
from typing import List, Dict, Any
from hive.scaffolder.frontmatter_parser import parse_markdown_frontmatter
from hive.scaffolder.genie_mapper import map_genie_to_hive
import yaml


GENIE_DISCOVERY_PATHS = [
    ".genie/agents",
    ".genie/code/agents",
]


def derive_genie_agent_id(file_path: str) -> str:
    """
    Derive agent ID from Genie .md file path.

    Examples:
        .genie/agents/review.md -> genie/review
        .genie/code/agents/fix.md -> genie/code/fix
    """
    path = Path(file_path)

    # Find which Genie base path this file is under
    for base_path in GENIE_DISCOVERY_PATHS:
        if base_path in str(path):
            # Extract relative path from base
            parts = path.parts
            base_parts = Path(base_path).parts

            # Find where base_path ends in the file path
            for i in range(len(parts) - len(base_parts) + 1):
                if parts[i:i+len(base_parts)] == base_parts:
                    # Get path after base_path, remove .md extension
                    relative_parts = parts[i+len(base_parts):]
                    relative_path = "/".join(relative_parts)
                    agent_name = relative_path.replace(".md", "")

                    # Build ID with genie/ prefix
                    if "code" in base_path:
                        return f"genie/code/{agent_name}"
                    else:
                        return f"genie/{agent_name}"

    # Fallback: use filename without extension
    return f"genie/{path.stem}"


def discover_agents_with_frontmatter(search_paths: List[str] = None) -> List[Dict[str, Any]]:
    """
    Discover agents from both .yaml and .md (frontmatter) files.

    Priority: config.yaml > agent.md if both exist in same directory.
    """
    if search_paths is None:
        search_paths = ["ai/agents"] + GENIE_DISCOVERY_PATHS

    discovered = []

    for search_path in search_paths:
        path = Path(search_path)
        if not path.exists():
            continue

        # Find all agent directories
        for agent_dir in path.iterdir():
            if not agent_dir.is_dir():
                continue

            config_yaml = agent_dir / "config.yaml"
            agent_md = agent_dir / "agent.md"

            # Priority: config.yaml first
            if config_yaml.exists():
                with config_yaml.open() as f:
                    config = yaml.safe_load(f)
                discovered.append({
                    "source": "yaml",
                    "path": str(config_yaml),
                    "config": config,
                })
            elif agent_md.exists():
                try:
                    parsed = parse_markdown_frontmatter(str(agent_md))
                    hive_config = map_genie_to_hive(
                        parsed["frontmatter"],
                        parsed["content"]
                    )
                    # Override ID with derived ID
                    agent_id = derive_genie_agent_id(str(agent_md))
                    hive_config["agent"]["id"] = agent_id

                    discovered.append({
                        "source": "genie-frontmatter",
                        "path": str(agent_md),
                        "config": hive_config,
                    })
                except (ValueError, KeyError) as e:
                    print(f"Warning: Failed to parse {agent_md}: {e}")

        # Also find standalone .md files (not in directories)
        if ".genie" in search_path:
            for md_file in path.glob("*.md"):
                try:
                    parsed = parse_markdown_frontmatter(str(md_file))
                    hive_config = map_genie_to_hive(
                        parsed["frontmatter"],
                        parsed["content"]
                    )
                    agent_id = derive_genie_agent_id(str(md_file))
                    hive_config["agent"]["id"] = agent_id

                    discovered.append({
                        "source": "genie-frontmatter",
                        "path": str(md_file),
                        "config": hive_config,
                    })
                except (ValueError, KeyError) as e:
                    print(f"Warning: Failed to parse {md_file}: {e}")

    return discovered
```

### Validation Schema Pattern

```python
# hive/scaffolder/validator.py (additions)

GENIE_AGENT_SCHEMA = {
    "name": {
        "required": True,
        "type": str,
        "description": "Agent name (kebab-case)",
    },
    "description": {
        "required": True,
        "type": str,
        "description": "Brief description of agent purpose",
    },
    "genie": {
        "required": False,
        "type": dict,
        "description": "Genie-specific configuration",
        "fields": {
            "executor": {
                "required": False,
                "type": (str, list),
                "description": "Executor(s) for agent execution",
            },
            "background": {
                "required": False,
                "type": bool,
                "default": True,
                "description": "Run in background mode",
            },
            "variant": {
                "required": False,
                "type": str,
                "description": "Agent variant identifier",
            },
            "permissionMode": {
                "required": False,
                "type": str,
                "description": "Permission handling mode",
            },
        },
    },
    "forge": {
        "required": False,
        "type": dict,
        "description": "Forge executor configurations (dynamic keys)",
    },
}


def validate_genie_agent(config: dict) -> bool:
    """
    Validate Genie agent frontmatter against schema.

    Args:
        config: Parsed Genie frontmatter YAML

    Returns:
        True if valid, raises ValueError if invalid
    """
    errors = []

    # Check required fields
    if "name" not in config:
        errors.append("Missing required field: name")
    if "description" not in config:
        errors.append("Missing required field: description")

    # Validate types
    if "name" in config and not isinstance(config["name"], str):
        errors.append("Field 'name' must be string")
    if "description" in config and not isinstance(config["description"], str):
        errors.append("Field 'description' must be string")

    # Validate optional genie section
    if "genie" in config:
        genie = config["genie"]
        if not isinstance(genie, dict):
            errors.append("Field 'genie' must be object")
        else:
            if "executor" in genie:
                executor = genie["executor"]
                if not isinstance(executor, (str, list)):
                    errors.append("Field 'genie.executor' must be string or array")
            if "background" in genie and not isinstance(genie["background"], bool):
                errors.append("Field 'genie.background' must be boolean")

    # Validate optional forge section
    if "forge" in config:
        if not isinstance(config["forge"], dict):
            errors.append("Field 'forge' must be object")

    if errors:
        raise ValueError(f"Invalid Genie agent config: {'; '.join(errors)}")

    return True
```

## Testing Protocol

```bash
# Group D1: Parser unit tests
uv run pytest tests/scaffolder/test_frontmatter_parser.py -v --cov=hive.scaffolder.frontmatter_parser

# Group D2: Mapper unit tests
uv run pytest tests/scaffolder/test_genie_mapper.py -v --cov=hive.scaffolder.genie_mapper

# Group D3: Discovery integration tests
uv run pytest tests/scaffolder/test_genie_discovery.py -v

# Group D4: Edge case tests
uv run pytest tests/scaffolder/ -k "genie" -v

# Full test suite (after all groups complete)
uv run pytest tests/scaffolder/ -v --cov=hive.scaffolder

# Static analysis
uv run ruff check hive/scaffolder/frontmatter_parser.py hive/scaffolder/genie_mapper.py
uv run mypy hive/scaffolder/frontmatter_parser.py hive/scaffolder/genie_mapper.py

# Manual smoke test (after all implementation complete)
# Create test Genie agent
cat > /tmp/test-genie-agent.md << 'EOF'
---
name: test-agent
description: Test agent for frontmatter parsing
genie:
  executor: CLAUDE_CODE
  background: true
forge:
  CLAUDE_CODE:
    model: sonnet
    dangerously_skip_permissions: false
---

# Test Agent Instructions

This is a test agent for validating Genie frontmatter parsing.
EOF

# Test discovery
python -c "
from hive.scaffolder.discovery import discover_agents_with_frontmatter
agents = discover_agents_with_frontmatter(['/tmp'])
print(f'Found {len(agents)} agents')
for agent in agents:
    print(f'  - {agent[\"config\"][\"agent\"][\"id\"]}: {agent[\"source\"]}')
"
```

## Validation Checklist

- [ ] `parse_markdown_frontmatter()` extracts YAML between `---` delimiters
- [ ] `map_genie_to_hive()` converts all field mappings correctly
- [ ] `convert_genie_model_to_hive()` handles all model names in conversion table
- [ ] `derive_genie_agent_id()` follows naming pattern `genie/{path}`
- [ ] `validate_genie_agent()` rejects invalid configs with clear errors
- [ ] Discovery finds `.md` files in `.genie/agents/` and `.genie/code/agents/`
- [ ] Discovery priority: `config.yaml` > `agent.md` when both exist
- [ ] Unit tests achieve ≥90% coverage for parser and mapper
- [ ] Integration tests validate end-to-end discovery → parsing → mapping
- [ ] Edge case tests cover: missing frontmatter, malformed YAML, invalid models, missing required fields
- [ ] Existing Hive `.yaml` agents continue working without modification
- [ ] Documentation updated with frontmatter format explanation and examples
- [ ] Example Genie agent created and tested successfully
- [ ] No new dependencies introduced (uses existing PyYAML)
- [ ] Error messages are clear and actionable
- [ ] Comments explain "why" not "what"

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Name conflicts between Genie and Hive agents | Prefix all Genie agent IDs with `genie/` namespace |
| Genie models don't map 1:1 to Hive | Explicit conversion table with fallback to `openai:gpt-4o` |
| Malformed frontmatter breaks discovery | Try-except with clear error messages; skip invalid files with warnings |
| Performance impact on discovery | Cache parsed frontmatter; lazy loading; discovery runs once at startup |
| YAML parsing security vulnerabilities | Use `yaml.safe_load()` (not `yaml.load()`) to prevent code execution |
| Breaking changes to Genie format | Add version field to GENIE_AGENT_SCHEMA; validate and migrate if needed |

## References

- **Current Implementation:**
  - `hive/scaffolder/generator.py:317-340` - Current YAML loading logic
  - `hive/scaffolder/validator.py:28-45` - Current AGENT_SCHEMA validation
  - `hive/scaffolder/discovery.py` - Current agent discovery system

- **Genie Format:**
  - `.genie/scripts/helpers/validate-frontmatter.js` - Genie-side validation
  - `.genie/code/agents/fix.md` - Example Genie agent with frontmatter
  - `.genie/agents/README.md` - Genie frontmatter documentation

- **Standards:**
  - YAML frontmatter: Standard markdown convention (Jekyll, Hugo, etc.)
  - PyYAML documentation: https://pyyaml.org/wiki/PyYAMLDocumentation
  - Regex patterns: Python `re` module for frontmatter extraction

## Labels

- `enhancement`
- `hive`
- `genie`
- `yaml`
- `integration`
