#!/usr/bin/env python3
"""
Script to batch-fix remaining ruff errors.
"""

from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# File-specific fixes
FIXES = {
    # N802 - Fix function naming
    "cli/docker_manager.py": [
        ("def PORTS(self)", "def ports(self)"),
        (".PORTS", ".ports"),
    ],
    "lib/config/settings.py": [
        ("def BASE_DIR(self)", "def base_dir(self)"),
    ],
    "tests/api/test_serve.py": [
        ("def setLevel(self, level)", "def set_level(self, level)"),
        (".setLevel", ".set_level"),
    ],
    # N818 - Fix exception naming
    "lib/mcp/exceptions.py": [
        ("class MCPException(Exception)", "class MCPError(Exception)"),
        ("MCPException", "MCPError"),
    ],
    "scripts/agno_db_migrate_v2.py": [
        ("class _OperationFailure(Exception)", "class _OperationFailureError(Exception)"),
        ("_OperationFailure", "_OperationFailureError"),
    ],
    # B019 - Add noqa comments for lru_cache on methods
    "lib/config/models.py": [
        ("@lru_cache(maxsize=256)", "@lru_cache(maxsize=256)  # noqa: B019"),
    ],
    "lib/config/provider_registry.py": [
        ("@lru_cache(maxsize=1)", "@lru_cache(maxsize=1)  # noqa: B019"),
        ("@lru_cache(maxsize=128)", "@lru_cache(maxsize=128)  # noqa: B019"),
        ("@lru_cache(maxsize=512)", "@lru_cache(maxsize=512)  # noqa: B019"),
    ],
    "lib/utils/emoji_loader.py": [
        ("@lru_cache(maxsize=None)", "@lru_cache(maxsize=None)  # noqa: B019"),
    ],
    # E721 - Use `is` for type comparisons
    "tests/integration/lib/test_models_production_coverage.py": [
        ("if result_type == type(True):", "if result_type is type(True):"),
        ("if result_type == type(1):", "if result_type is type(1):"),
        ("if result_type == type(''):", "if result_type is type(''):"),
    ],
    # E741 - Rename ambiguous variables
    "tests/lib/auth/test_env_file_manager.py": [
        ("for l in lines:", "for line in lines:"),
        ("if l.strip():", "if line.strip():"),
    ],
    # B015 - Fix pointless comparison
    "scripts/test_tdd_hook_validator.py": [
        ("mock_result.status_code == 401", "assert mock_result.status_code == 401"),
    ],
}


def apply_fixes():
    """Apply all fixes."""
    for file_path, replacements in FIXES.items():
        full_path = PROJECT_ROOT / file_path
        if not full_path.exists():
            print(f"⚠️  Skipping {file_path} - file not found")
            continue

        content = full_path.read_text()
        original_content = content

        for old, new in replacements:
            content = content.replace(old, new)

        if content != original_content:
            full_path.write_text(content)
            print(f"✓ Fixed {file_path}")
        else:
            print(f"  No changes needed in {file_path}")


if __name__ == "__main__":
    print("Applying ruff fixes...")
    apply_fixes()
    print("\nDone!")
