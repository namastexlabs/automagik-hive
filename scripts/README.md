# Scripts Directory

This directory contains utility scripts for Automagik Hive development and deployment.

## Active Scripts

### `agno_db_migrate_v2.py`
**Purpose**: Database migration tool for Agno framework updates
**Usage**: Called automatically by startup orchestration and version sync services
**Entry Point**: `lib/utils/startup_orchestration.py`, `lib/services/version_sync_service.py`

```bash
# Manual execution (rarely needed)
uv run python scripts/agno_db_migrate_v2.py --dry-run
uv run python scripts/agno_db_migrate_v2.py
```

### `install-predeps.sh`
**Purpose**: Cross-platform prerequisite installer for developer onboarding
**Usage**: Public installation script (curl | bash pattern)
**Platforms**: Linux, macOS, WSL
**CI/CD**: Used in GitHub Actions (ubuntu-latest, macos-latest)

```bash
# Direct execution
bash scripts/install-predeps.sh

# Remote execution (public pattern)
curl -fsSL https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/scripts/install-predeps.sh | bash
```

### `test-install-predeps.sh`
**Purpose**: Comprehensive testing suite for install-predeps.sh
**Usage**: CI/CD validation across multiple platforms
**Features**: ShellCheck validation, dry-run testing, platform compatibility

```bash
# Run full test suite
bash scripts/test-install-predeps.sh

# Run specific test
bash scripts/test-install-predeps.sh --test-name basic_detection
```

## CI/CD Integration

These scripts are integrated into our CI/CD pipeline:

- **GitHub Actions**: `.github/workflows/ci-cd.yml` uses `install-predeps.sh` and `test-install-predeps.sh`
- **Startup Orchestration**: `lib/utils/startup_orchestration.py` calls `agno_db_migrate_v2.py`
- **Version Sync**: `lib/services/version_sync_service.py` calls `agno_db_migrate_v2.py`

## Development Guidelines

When adding new scripts:

1. **Prefer pytest over standalone scripts** for testing
2. **Integrate with CI/CD** if the script needs regular execution
3. **Document in this README** with purpose, usage, and integration points
4. **Follow naming conventions**: Use descriptive names, avoid test_* prefix unless pytest-compatible
5. **Make scripts executable**: `chmod +x scripts/your_script.sh`

## Removed Scripts (Historical Reference)

The following scripts were removed during cleanup (2025-10-29):

- **Test Analysis**: `test_analyzer.py` - Redundant with pytest ecosystem
- **Git Hooks**: `pre-commit-hook.sh`, `setup_git_hooks.py` - System never deployed
- **Validation**: `validate_build.py`, `validate_emoji_mappings.py`, `validate_logging.py` - Unused
- **Publishing**: `publish.py` - Automated via GitHub Actions
- **Utilities**: Various obsolete helper scripts

For full historical context, see: `.genie/reports/scripts-audit-20251029.md`
