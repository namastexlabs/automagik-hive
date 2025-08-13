"""Tests for domain value objects.

This module tests the immutable value objects that define configuration
and rules for the validation system.
"""

import pytest

from src.hooks.domain.value_objects import (
    GenieStructure,
    RootWhitelist,
    ValidationConfig,
)


class TestRootWhitelist:
    """Test suite for the RootWhitelist value object."""

    def test_default_whitelist_creation(self):
        """Test default whitelist contains expected patterns."""
        whitelist = RootWhitelist.default()

        assert isinstance(whitelist.patterns, list)
        assert len(whitelist.patterns) > 0

        # Check for essential patterns
        expected_patterns = [
            "pyproject.toml",
            "README.md",
            "CHANGELOG.md",
            "CLAUDE.md",
            "Makefile",
            "Dockerfile*",
            "docker-compose*.yml",
            ".gitignore",
            "*.sh",
        ]

        for pattern in expected_patterns:
            assert pattern in whitelist.patterns, (
                f"Pattern {pattern} not found in whitelist"
            )

    def test_whitelist_immutability(self):
        """Test that RootWhitelist is immutable."""
        whitelist = RootWhitelist(["test.txt"])

        # Should not be able to modify patterns directly
        with pytest.raises(AttributeError):
            whitelist.patterns = ["modified.txt"]

    def test_matches_pattern_exact(self):
        """Test pattern matching for exact matches."""
        whitelist = RootWhitelist(["README.md", "pyproject.toml"])

        assert whitelist.matches_pattern("README.md") is True
        assert whitelist.matches_pattern("pyproject.toml") is True
        assert whitelist.matches_pattern("NOTFOUND.md") is False

    def test_matches_pattern_wildcards(self):
        """Test pattern matching with wildcard patterns."""
        whitelist = RootWhitelist(["Dockerfile*", "docker-compose*.yml", "*.sh"])

        # Test Dockerfile patterns
        assert whitelist.matches_pattern("Dockerfile") is True
        assert whitelist.matches_pattern("Dockerfile.agent") is True
        assert whitelist.matches_pattern("Dockerfile.dev") is True

        # Test docker-compose patterns
        assert whitelist.matches_pattern("docker-compose.yml") is True
        assert whitelist.matches_pattern("docker-compose-agent.yml") is True
        assert (
            whitelist.matches_pattern("docker-compose.dev.yaml") is False
        )  # Different extension

        # Test shell script patterns
        assert whitelist.matches_pattern("setup.sh") is True
        assert whitelist.matches_pattern("deploy.sh") is True
        assert whitelist.matches_pattern("script.py") is False

    def test_matches_pattern_directories(self):
        """Test pattern matching for directory patterns."""
        whitelist = RootWhitelist([".github/", "scripts/", "templates/"])

        assert whitelist.matches_pattern(".github/") is True
        assert whitelist.matches_pattern("scripts/") is True
        assert whitelist.matches_pattern("templates/") is True
        assert whitelist.matches_pattern("custom/") is False

    def test_matches_pattern_case_sensitive(self):
        """Test that pattern matching is case sensitive."""
        whitelist = RootWhitelist(["README.md"])

        assert whitelist.matches_pattern("README.md") is True
        assert whitelist.matches_pattern("readme.md") is False
        assert whitelist.matches_pattern("ReadMe.md") is False

    def test_custom_whitelist(self):
        """Test creating custom whitelist patterns."""
        custom_patterns = ["custom.txt", "*.config", "special/"]
        whitelist = RootWhitelist(custom_patterns)

        assert whitelist.patterns == custom_patterns
        assert whitelist.matches_pattern("custom.txt") is True
        assert whitelist.matches_pattern("app.config") is True
        assert whitelist.matches_pattern("special/") is True


class TestGenieStructure:
    """Test suite for the GenieStructure value object."""

    def test_default_genie_structure(self):
        """Test default genie structure contains expected paths."""
        structure = GenieStructure.default()

        assert isinstance(structure.allowed_paths, list)
        assert len(structure.allowed_paths) > 0

        expected_paths = [
            "/genie/docs/",
            "/genie/ideas/",
            "/genie/wishes/",
            "/genie/reports/",
            "/genie/experiments/",
            "/genie/knowledge/",
        ]

        for path in expected_paths:
            assert path in structure.allowed_paths, (
                f"Path {path} not found in structure"
            )

    def test_genie_structure_immutability(self):
        """Test that GenieStructure is immutable."""
        structure = GenieStructure(["/genie/test/"])

        with pytest.raises(AttributeError):
            structure.allowed_paths = ["/genie/modified/"]

    def test_is_valid_genie_path_valid(self):
        """Test is_valid_genie_path for valid paths."""
        structure = GenieStructure.default()

        valid_paths = [
            "/genie/docs/architecture.md",
            "/genie/ideas/brainstorm.md",
            "/genie/wishes/feature-plan.md",
            "/genie/reports/completion.md",
            "/genie/experiments/prototype.py",
            "/genie/knowledge/patterns.md",
        ]

        for path in valid_paths:
            assert structure.is_valid_genie_path(path) is True, (
                f"Path {path} should be valid"
            )

    def test_is_valid_genie_path_invalid(self):
        """Test is_valid_genie_path for invalid paths."""
        structure = GenieStructure.default()

        invalid_paths = [
            "/lib/utils.py",  # Not in genie
            "/genie/invalid/file.md",  # Invalid genie subdirectory
            "/genie/",  # Just genie root
            "/genie",  # No trailing slash
            "genie/docs/file.md",  # No leading slash
            "/custom/docs/file.md",  # Different root
        ]

        for path in invalid_paths:
            assert structure.is_valid_genie_path(path) is False, (
                f"Path {path} should be invalid"
            )

    def test_get_suggested_genie_path_plan_words(self):
        """Test suggestion generation for plan-related files."""
        structure = GenieStructure.default()

        plan_files = ["feature-plan.md", "todo-list.md", "wish-implementation.md"]

        for filename in plan_files:
            suggestion = structure.get_suggested_genie_path(filename)
            assert suggestion.startswith("/genie/wishes/"), (
                f"Wrong suggestion for {filename}"
            )
            assert suggestion.endswith(filename)

    def test_get_suggested_genie_path_design_words(self):
        """Test suggestion generation for design-related files."""
        structure = GenieStructure.default()

        design_files = ["system-design.md", "architecture-spec.md", "ddd-document.md"]

        for filename in design_files:
            suggestion = structure.get_suggested_genie_path(filename)
            assert suggestion.startswith("/genie/docs/"), (
                f"Wrong suggestion for {filename}"
            )
            assert suggestion.endswith(filename)

    def test_get_suggested_genie_path_idea_words(self):
        """Test suggestion generation for idea-related files."""
        structure = GenieStructure.default()

        idea_files = ["brainstorm-ideas.md", "analysis-notes.md", "thinking-session.md"]

        for filename in idea_files:
            suggestion = structure.get_suggested_genie_path(filename)
            assert suggestion.startswith("/genie/ideas/"), (
                f"Wrong suggestion for {filename}"
            )
            assert suggestion.endswith(filename)

    def test_get_suggested_genie_path_report_words(self):
        """Test suggestion generation for report-related files."""
        structure = GenieStructure.default()

        report_files = ["completion-report.md", "summary-results.md", "final-report.md"]

        for filename in report_files:
            suggestion = structure.get_suggested_genie_path(filename)
            assert suggestion.startswith("/genie/reports/"), (
                f"Wrong suggestion for {filename}"
            )
            assert suggestion.endswith(filename)

    def test_get_suggested_genie_path_experiment_words(self):
        """Test suggestion generation for experiment-related files."""
        structure = GenieStructure.default()

        experiment_files = [
            "prototype-test.py",
            "trial-implementation.md",
            "experiment-results.md",
        ]

        for filename in experiment_files:
            suggestion = structure.get_suggested_genie_path(filename)
            assert suggestion.startswith("/genie/experiments/"), (
                f"Wrong suggestion for {filename}"
            )
            assert suggestion.endswith(filename)

    def test_get_suggested_genie_path_knowledge_words(self):
        """Test suggestion generation for knowledge-related files."""
        structure = GenieStructure.default()

        knowledge_files = [
            "learning-patterns.md",
            "wisdom-insights.md",
            "knowledge-base.md",
        ]

        for filename in knowledge_files:
            suggestion = structure.get_suggested_genie_path(filename)
            assert suggestion.startswith("/genie/knowledge/"), (
                f"Wrong suggestion for {filename}"
            )
            assert suggestion.endswith(filename)

    def test_get_suggested_genie_path_default(self):
        """Test suggestion generation defaults to docs for unclassified files."""
        structure = GenieStructure.default()

        generic_files = ["random-file.md", "unclassified.txt", "misc-document.md"]

        for filename in generic_files:
            suggestion = structure.get_suggested_genie_path(filename)
            assert suggestion.startswith("/genie/docs/"), (
                f"Should default to docs for {filename}"
            )
            assert suggestion.endswith(filename)


class TestValidationConfig:
    """Test suite for the ValidationConfig value object."""

    def test_default_config_creation(self):
        """Test default configuration has expected values."""
        config = ValidationConfig.default()

        assert config.enforce_genie_structure is True
        assert config.strict_mode is True
        assert isinstance(config.allow_root_md_files, list)
        assert isinstance(config.custom_whitelist_patterns, list)

        # Check default allowed MD files
        expected_md_files = ["README.md", "CHANGELOG.md", "CLAUDE.md"]
        assert config.allow_root_md_files == expected_md_files

    def test_config_immutability(self):
        """Test that ValidationConfig is immutable."""
        config = ValidationConfig(
            enforce_genie_structure=True,
            allow_root_md_files=["test.md"],
            custom_whitelist_patterns=["*.test"],
            strict_mode=False,
        )

        with pytest.raises(AttributeError):
            config.enforce_genie_structure = False

    def test_is_allowed_root_md_valid(self):
        """Test is_allowed_root_md for allowed files."""
        config = ValidationConfig.default()

        allowed_files = ["README.md", "CHANGELOG.md", "CLAUDE.md"]

        for filename in allowed_files:
            assert config.is_allowed_root_md(filename) is True, (
                f"{filename} should be allowed"
            )

    def test_is_allowed_root_md_invalid(self):
        """Test is_allowed_root_md for disallowed files."""
        config = ValidationConfig.default()

        disallowed_files = [
            "setup.md",
            "notes.md",
            "custom.md",
            "readme.md",  # Case sensitive
            "README.MD",  # Case sensitive
        ]

        for filename in disallowed_files:
            assert config.is_allowed_root_md(filename) is False, (
                f"{filename} should not be allowed"
            )

    def test_custom_allowed_md_files(self):
        """Test custom allowed MD files configuration."""
        custom_config = ValidationConfig(
            enforce_genie_structure=True,
            allow_root_md_files=["README.md", "CUSTOM.md"],
            custom_whitelist_patterns=[],
            strict_mode=True,
        )

        assert custom_config.is_allowed_root_md("README.md") is True
        assert custom_config.is_allowed_root_md("CUSTOM.md") is True
        assert (
            custom_config.is_allowed_root_md("CHANGELOG.md") is False
        )  # Not in custom list

    def test_non_strict_mode(self):
        """Test configuration with strict mode disabled."""
        config = ValidationConfig(
            enforce_genie_structure=False,
            allow_root_md_files=["README.md"],
            custom_whitelist_patterns=["*.custom"],
            strict_mode=False,
        )

        assert config.enforce_genie_structure is False
        assert config.strict_mode is False
        assert config.custom_whitelist_patterns == ["*.custom"]

    def test_custom_whitelist_patterns(self):
        """Test custom whitelist patterns configuration."""
        custom_patterns = ["*.custom", "special.txt", "config/*.json"]
        config = ValidationConfig(
            enforce_genie_structure=True,
            allow_root_md_files=["README.md"],
            custom_whitelist_patterns=custom_patterns,
            strict_mode=True,
        )

        assert config.custom_whitelist_patterns == custom_patterns
