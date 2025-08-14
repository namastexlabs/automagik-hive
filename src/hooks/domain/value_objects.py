"""Domain value objects for pre-commit hook validation system.

This module contains immutable value objects that define configuration
and rules for the validation system. These objects encapsulate business
logic about what files are allowed and where they should be placed.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RootWhitelist:
    """Immutable whitelist of allowed root-level file patterns.

    This value object defines which files and directories are permitted
    at the project root level. All patterns support shell-style wildcards.
    """

    patterns: list[str]

    @classmethod
    def default(cls) -> "RootWhitelist":
        """Create default whitelist based on common project files.

        Returns:
            RootWhitelist with standard allowed patterns for Python projects.
        """
        return cls(
            patterns=[
                # Package management
                "pyproject.toml",
                "requirements*.txt",
                "setup.py",
                "setup.cfg",
                # Documentation (specific allowed files)
                "README.md",
                "CHANGELOG.md",
                "CLAUDE.md",
                "LICENSE",
                "LICENSE.*",
                # Build and deployment
                "Makefile",
                "Dockerfile*",
                "docker-compose*.yml",
                "docker-compose*.yaml",
                # Configuration files
                ".env.example",
                ".gitignore",
                ".gitattributes",
                ".editorconfig",
                ".pre-commit-config.yaml",
                ".mcp.json",
                # Standard directories
                ".github/",
                ".claude/",
                "scripts/",
                "templates/",
                # Shell scripts (common at root)
                "*.sh",
                # CI/CD files
                ".gitlab-ci.yml",
                "Jenkinsfile",
                "azure-pipelines.yml",
                # Language specific
                "package.json",
                "yarn.lock",
                "uv.lock",
                "Cargo.toml",
                "go.mod",
                # IDE files that may legitimately be at root
                ".vscode/",
                ".idea/",
            ]
        )

    def matches_pattern(self, file_path: str) -> bool:
        """Check if a file path matches any whitelisted pattern.

        Args:
            file_path: Path to check against whitelist patterns.

        Returns:
            True if file matches any pattern, False otherwise.
        """
        import fnmatch

        return any(fnmatch.fnmatch(file_path, pattern) for pattern in self.patterns)


@dataclass(frozen=True)
class GenieStructure:
    """Immutable genie workspace structure definition.

    This value object defines the allowed subdirectories within the
    /genie/ workspace and their intended purposes.
    """

    allowed_paths: list[str]

    @classmethod
    def default(cls) -> "GenieStructure":
        """Create default genie structure based on CLAUDE.md rules.

        Returns:
            GenieStructure with standard genie workspace organization.
        """
        return cls(
            allowed_paths=[
                "/genie/docs/",  # Design documents and architecture
                "/genie/ideas/",  # Brainstorming and analysis files
                "/genie/wishes/",  # Execution-ready plans
                "/genie/experiments/",  # Prototype and test files
                "/genie/knowledge/",  # Learning and wisdom storage
            ]
        )

    def is_valid_genie_path(self, file_path: str) -> bool:
        """Check if a file path follows proper /genie/ structure.

        Args:
            file_path: Path to validate against genie structure.

        Returns:
            True if path follows genie structure, False otherwise.
        """
        if not file_path.startswith("/genie/"):
            return False

        for allowed_path in self.allowed_paths:
            if file_path.startswith(allowed_path):
                return True

        return False

    def get_suggested_genie_path(self, filename: str) -> str:
        """Suggest appropriate /genie/ path based on filename patterns.

        Args:
            filename: Name of file to suggest path for.

        Returns:
            Suggested full path within genie structure.
        """
        filename_lower = filename.lower()

        # Pattern-based suggestions (order matters - more specific patterns first)
        if any(word in filename_lower for word in ["plan", "wish", "todo"]):
            return f"/genie/wishes/{filename}"
        if any(
            word in filename_lower for word in ["design", "architecture", "ddd", "spec"]
        ):
            return f"/genie/docs/{filename}"
        if any(
            word in filename_lower for word in ["idea", "analysis", "brain", "think"]
        ):
            return f"/genie/ideas/{filename}"
        if any(word in filename_lower for word in ["experiment", "prototype", "trial"]):
            return f"/genie/experiments/{filename}"
        if any(
            word in filename_lower
            for word in ["report", "complete", "summary", "result"]
        ):
            return f"/genie/ideas/{filename}"
        if any(
            word in filename_lower
            for word in ["learn", "knowledge", "pattern", "wisdom"]
        ):
            return f"/genie/knowledge/{filename}"
        if any(word in filename_lower for word in ["test"]):
            return f"/genie/experiments/{filename}"
        # Default to docs for unclassified files
        return f"/genie/docs/{filename}"


@dataclass(frozen=True)
class ValidationConfig:
    """Immutable configuration for validation behavior.

    This value object encapsulates all configuration needed to customize
    the behavior of the validation system.
    """

    enforce_genie_structure: bool
    allow_root_md_files: list[str]
    custom_whitelist_patterns: list[str]
    strict_mode: bool

    @classmethod
    def default(cls) -> "ValidationConfig":
        """Create default validation configuration.

        Returns:
            ValidationConfig with standard settings.
        """
        return cls(
            enforce_genie_structure=True,
            allow_root_md_files=["README.md", "CHANGELOG.md", "CLAUDE.md"],
            custom_whitelist_patterns=[],
            strict_mode=True,
        )

    def is_allowed_root_md(self, filename: str) -> bool:
        """Check if markdown file is allowed at root level.

        Args:
            filename: Name of markdown file to check.

        Returns:
            True if markdown file is allowed at root, False otherwise.
        """
        return filename in self.allow_root_md_files
