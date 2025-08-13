"""Tests for the ValidatePreCommitUseCase application layer.

This module tests the core business logic of the pre-commit validation system,
ensuring that file changes are properly validated against organizational rules.
"""

from src.hooks.application.validate_precommit import (
    ValidatePreCommitUseCase,
    ValidationMetrics,
)
from src.hooks.domain.entities import FileChange, FileOperation, ValidationResult
from src.hooks.domain.value_objects import (
    GenieStructure,
    RootWhitelist,
    ValidationConfig,
)


class TestValidatePreCommitUseCase:
    """Test suite for the ValidatePreCommitUseCase class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.whitelist = RootWhitelist.default()
        self.genie_structure = GenieStructure.default()
        self.config = ValidationConfig.default()
        self.use_case = ValidatePreCommitUseCase(
            self.whitelist, self.genie_structure, self.config
        )

    def test_empty_changes_allowed(self):
        """Test that empty change list returns allowed result."""
        result = self.use_case.execute([])

        assert result.result == ValidationResult.ALLOWED
        assert len(result.blocked_files) == 0
        assert len(result.allowed_files) == 0
        assert len(result.error_messages) == 0

    def test_allowed_root_files(self):
        """Test that whitelisted files are allowed at root level."""
        changes = [
            FileChange("README.md", FileOperation.CREATE, True, ".md", False),
            FileChange("pyproject.toml", FileOperation.MODIFY, True, ".toml", False),
            FileChange("Makefile", FileOperation.CREATE, True, None, False),
            FileChange(".gitignore", FileOperation.MODIFY, True, None, False),
        ]

        result = self.use_case.execute(changes)

        assert result.result == ValidationResult.ALLOWED
        assert len(result.blocked_files) == 0
        assert len(result.allowed_files) == 4
        assert len(result.error_messages) == 0

    def test_blocked_root_md_files(self):
        """Test that non-whitelisted .md files are blocked at root level."""
        changes = [
            FileChange("setup.md", FileOperation.CREATE, True, ".md", False),
            FileChange("notes.md", FileOperation.CREATE, True, ".md", False),
        ]

        result = self.use_case.execute(changes)

        assert result.result == ValidationResult.BLOCKED
        assert len(result.blocked_files) == 2
        assert len(result.allowed_files) == 0
        assert len(result.error_messages) == 2

        # Check error messages contain expected content
        for error_msg in result.error_messages:
            assert "BLOCKED:" in error_msg
            assert "Markdown files must be created in /genie/ structure" in error_msg

    def test_allowed_md_files_at_root(self):
        """Test that specifically allowed .md files are permitted at root."""
        changes = [
            FileChange("README.md", FileOperation.CREATE, True, ".md", False),
            FileChange("CHANGELOG.md", FileOperation.MODIFY, True, ".md", False),
            FileChange("CLAUDE.md", FileOperation.MODIFY, True, ".md", False),
        ]

        result = self.use_case.execute(changes)

        assert result.result == ValidationResult.ALLOWED
        assert len(result.blocked_files) == 0
        assert len(result.allowed_files) == 3

    def test_blocked_root_directories(self):
        """Test that unauthorized directories are blocked at root level."""
        changes = [
            FileChange("newdir", FileOperation.CREATE, True, None, True),
            FileChange("custom_lib", FileOperation.CREATE, True, None, True),
        ]

        result = self.use_case.execute(changes)

        assert result.result == ValidationResult.BLOCKED
        assert len(result.blocked_files) == 2
        assert len(result.allowed_files) == 0

        # Check error messages for directories
        for error_msg in result.error_messages:
            assert "BLOCKED:" in error_msg
            assert "New directories should be created in /lib/" in error_msg

    def test_allowed_whitelisted_directories(self):
        """Test that whitelisted directories are allowed at root level."""
        changes = [
            FileChange("scripts/", FileOperation.CREATE, True, None, True),
            FileChange(".github/", FileOperation.CREATE, True, None, True),
            FileChange("templates/", FileOperation.CREATE, True, None, True),
        ]

        result = self.use_case.execute(changes)

        assert result.result == ValidationResult.ALLOWED
        assert len(result.blocked_files) == 0
        assert len(result.allowed_files) == 3

    def test_non_root_files_always_allowed(self):
        """Test that files not at root level are always allowed."""
        changes = [
            FileChange("lib/custom.py", FileOperation.CREATE, False, ".py", False),
            FileChange("src/test.md", FileOperation.CREATE, False, ".md", False),
            FileChange("api/routes/new.py", FileOperation.CREATE, False, ".py", False),
        ]

        result = self.use_case.execute(changes)

        assert result.result == ValidationResult.ALLOWED
        assert len(result.blocked_files) == 0
        assert len(result.allowed_files) == 3

    def test_mixed_allowed_and_blocked_files(self):
        """Test validation with mix of allowed and blocked files."""
        changes = [
            FileChange(
                "README.md", FileOperation.CREATE, True, ".md", False
            ),  # Allowed
            FileChange(
                "custom.md", FileOperation.CREATE, True, ".md", False
            ),  # Blocked
            FileChange(
                "pyproject.toml", FileOperation.MODIFY, True, ".toml", False
            ),  # Allowed
            FileChange(
                "lib/utils.py", FileOperation.CREATE, False, ".py", False
            ),  # Allowed (non-root)
        ]

        result = self.use_case.execute(changes)

        assert result.result == ValidationResult.BLOCKED
        assert len(result.blocked_files) == 1
        assert len(result.allowed_files) == 3
        assert len(result.error_messages) == 1
        assert "custom.md" in result.error_messages[0]

    def test_bypass_mode_active(self):
        """Test that bypass mode allows all files through."""
        changes = [
            FileChange("blocked.md", FileOperation.CREATE, True, ".md", False),
            FileChange("baddir/", FileOperation.CREATE, True, None, True),
            FileChange("unauthorized.py", FileOperation.CREATE, True, ".py", False),
        ]

        result = self.use_case.execute(changes, bypass_flag=True)

        assert result.result == ValidationResult.BYPASS
        assert len(result.blocked_files) == 0
        assert len(result.allowed_files) == 0
        assert len(result.bypass_files) == 3
        assert "BYPASS ACTIVE" in result.error_messages[0]

    def test_suggestion_generation(self):
        """Test that helpful suggestions are generated for blocked files."""
        changes = [
            FileChange("docs.md", FileOperation.CREATE, True, ".md", False),
            FileChange("newlib/", FileOperation.CREATE, True, None, True),
        ]

        result = self.use_case.execute(changes)

        assert result.result == ValidationResult.BLOCKED
        assert len(result.suggestions) >= 2

        # Check that suggestions contain expected paths
        suggestion_text = " ".join(result.suggestions)
        assert "/genie/" in suggestion_text
        assert "docs.md" in suggestion_text

    def test_file_operation_types(self):
        """Test validation works with different file operations."""
        changes = [
            FileChange("test.md", FileOperation.CREATE, True, ".md", False),
            FileChange("temp.md", FileOperation.MODIFY, True, ".md", False),
            FileChange("old.md", FileOperation.DELETE, True, ".md", False),
            FileChange("renamed.md", FileOperation.RENAME, True, ".md", False),
        ]

        result = self.use_case.execute(changes)

        # All should be blocked except delete operations might be treated differently
        assert result.result == ValidationResult.BLOCKED
        assert len(result.blocked_files) == 4  # All operations subject to validation

    def test_dockerfile_patterns_allowed(self):
        """Test that Dockerfile patterns are properly whitelisted."""
        changes = [
            FileChange("Dockerfile", FileOperation.CREATE, True, None, False),
            FileChange("Dockerfile.agent", FileOperation.CREATE, True, None, False),
            FileChange("Dockerfile.dev", FileOperation.CREATE, True, None, False),
        ]

        result = self.use_case.execute(changes)

        assert result.result == ValidationResult.ALLOWED
        assert len(result.blocked_files) == 0
        assert len(result.allowed_files) == 3

    def test_docker_compose_patterns_allowed(self):
        """Test that docker-compose patterns are properly whitelisted."""
        changes = [
            FileChange("docker-compose.yml", FileOperation.CREATE, True, ".yml", False),
            FileChange(
                "docker-compose-agent.yml", FileOperation.CREATE, True, ".yml", False
            ),
            FileChange(
                "docker-compose.dev.yaml", FileOperation.CREATE, True, ".yaml", False
            ),
        ]

        result = self.use_case.execute(changes)

        assert result.result == ValidationResult.ALLOWED
        assert len(result.blocked_files) == 0
        assert len(result.allowed_files) == 3

    def test_shell_scripts_allowed(self):
        """Test that shell scripts are allowed at root level."""
        changes = [
            FileChange("setup.sh", FileOperation.CREATE, True, ".sh", False),
            FileChange("deploy.sh", FileOperation.CREATE, True, ".sh", False),
        ]

        result = self.use_case.execute(changes)

        assert result.result == ValidationResult.ALLOWED
        assert len(result.blocked_files) == 0
        assert len(result.allowed_files) == 2


class TestValidationMetrics:
    """Test suite for the ValidationMetrics helper class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.metrics = ValidationMetrics()

    def test_initial_metrics_empty(self):
        """Test that metrics start with zero counts."""
        summary = self.metrics.get_summary()

        assert summary["total_validations"] == 0
        assert summary["blocked_count"] == 0
        assert summary["bypassed_count"] == 0
        assert summary["success_rate"] == 1.0
        assert summary["file_type_stats"] == {}

    def test_record_allowed_validation(self):
        """Test recording successful validation."""
        # Create a mock validation result
        from src.hooks.domain.entities import HookValidationResult

        result = HookValidationResult(
            result=ValidationResult.ALLOWED,
            blocked_files=[],
            allowed_files=[
                FileChange("README.md", FileOperation.CREATE, True, ".md", False),
                FileChange("test.py", FileOperation.CREATE, False, ".py", False),
            ],
            bypass_files=[],
            error_messages=[],
            suggestions=[],
        )

        self.metrics.record_validation(result)
        summary = self.metrics.get_summary()

        assert summary["total_validations"] == 1
        assert summary["blocked_count"] == 0
        assert summary["bypassed_count"] == 0
        assert summary["success_rate"] == 1.0
        assert summary["file_type_stats"][".md"] == 1
        assert summary["file_type_stats"][".py"] == 1

    def test_record_blocked_validation(self):
        """Test recording blocked validation."""
        from src.hooks.domain.entities import HookValidationResult

        result = HookValidationResult(
            result=ValidationResult.BLOCKED,
            blocked_files=[
                FileChange("bad.md", FileOperation.CREATE, True, ".md", False),
            ],
            allowed_files=[
                FileChange("good.toml", FileOperation.MODIFY, True, ".toml", False),
            ],
            bypass_files=[],
            error_messages=["Error"],
            suggestions=[],
        )

        self.metrics.record_validation(result)
        summary = self.metrics.get_summary()

        assert summary["total_validations"] == 1
        assert summary["blocked_count"] == 1
        assert summary["bypassed_count"] == 0
        assert summary["success_rate"] == 0.0
        assert summary["file_type_stats"][".md"] == 1
        assert summary["file_type_stats"][".toml"] == 1

    def test_record_bypassed_validation(self):
        """Test recording bypassed validation."""
        from src.hooks.domain.entities import HookValidationResult

        result = HookValidationResult(
            result=ValidationResult.BYPASS,
            blocked_files=[],
            allowed_files=[],
            bypass_files=[
                FileChange("bypass.md", FileOperation.CREATE, True, ".md", False),
            ],
            error_messages=["Bypass active"],
            suggestions=[],
        )

        self.metrics.record_validation(result)
        summary = self.metrics.get_summary()

        assert summary["total_validations"] == 1
        assert summary["blocked_count"] == 0
        assert summary["bypassed_count"] == 1
        assert summary["success_rate"] == 1.0  # Bypass counts as success
        assert summary["file_type_stats"][".md"] == 1

    def test_multiple_validations(self):
        """Test metrics with multiple validation records."""
        from src.hooks.domain.entities import HookValidationResult

        # Record successful validation
        success_result = HookValidationResult(
            result=ValidationResult.ALLOWED,
            blocked_files=[],
            allowed_files=[
                FileChange("good.py", FileOperation.CREATE, False, ".py", False)
            ],
            bypass_files=[],
            error_messages=[],
            suggestions=[],
        )

        # Record blocked validation
        blocked_result = HookValidationResult(
            result=ValidationResult.BLOCKED,
            blocked_files=[
                FileChange("bad.md", FileOperation.CREATE, True, ".md", False)
            ],
            allowed_files=[],
            bypass_files=[],
            error_messages=["Error"],
            suggestions=[],
        )

        self.metrics.record_validation(success_result)
        self.metrics.record_validation(blocked_result)

        summary = self.metrics.get_summary()

        assert summary["total_validations"] == 2
        assert summary["blocked_count"] == 1
        assert summary["bypassed_count"] == 0
        assert summary["success_rate"] == 0.5
        assert summary["file_type_stats"][".py"] == 1
        assert summary["file_type_stats"][".md"] == 1
