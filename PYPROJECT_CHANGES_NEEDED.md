# pyproject.toml Changes Needed for Hive V2

## Why These Changes Are Needed

Hive V2 introduces a new `hive` package with CLI commands that need to be properly configured in pyproject.toml for UVX installation and usage.

## Required Changes

### 1. Add New CLI Entry Point

**Current:**
```toml
[project.scripts]
automagik-hive = "cli.main:main"
```

**Add:**
```toml
[project.scripts]
hive = "hive.cli:app"
automagik-hive = "cli.main:main"  # Keep for backward compatibility
```

**Reason:** Enables `hive` command for V2 CLI while maintaining V1 compatibility.

### 2. Update Package Metadata (Optional)

**Current:**
```toml
version = "0.2.0"
description = "Automagik Hive"
requires-python = ">=3.12"
```

**Suggested:**
```toml
version = "2.0.0"
description = "AI-powered multi-agent framework with UVX CLI"
requires-python = ">=3.11"  # Allow 3.11+ for broader compatibility
```

**Reason:** Reflects V2 launch and broader Python version support.

### 3. Add V2 Dependencies (Required)

Add typer for CLI:
```bash
uv add typer
```

**Reason:** Typer is required for the new `hive` CLI commands.

### 4. Update Wheel Packages

**Current:**
```toml
[tool.hatch.build.targets.wheel]
packages = ["ai", "api", "lib", "cli", "common"]
```

**Update to:**
```toml
[tool.hatch.build.targets.wheel]
packages = ["ai", "api", "lib", "cli", "common", "hive"]
```

**Reason:** Include the new `hive` package in distribution.

## Verification After Changes

Run these commands to verify:

```bash
# Test CLI works
uv run python -c "from hive.cli import app; print('CLI imported successfully')"

# Test version command
uv run python -c "from hive.cli import app; app(['version', 'show'], standalone_mode=False)"

# Run infrastructure tests
uv run pytest tests/hive_v2/test_infrastructure.py -v

# Test package can be built
uv build
```

## Migration Path

1. Keep both V1 (`automagik-hive`) and V2 (`hive`) commands
2. V1 continues to work for existing users
3. V2 is the recommended path for new projects
4. Future: Deprecate V1 in favor of V2
