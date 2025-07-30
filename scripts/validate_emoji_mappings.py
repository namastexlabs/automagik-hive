#!/usr/bin/env python3
"""Emoji mapping validation for git hooks.

Validates that new resource types have appropriate emoji mappings
in the centralized emoji configuration file.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

from lib.logging import logger


class EmojiMappingValidator:
    """Validates emoji mappings for codebase resources."""

    def __init__(self, emoji_config_path: str | None = None):
        """Initialize validator with emoji configuration.

        Args:
            emoji_config_path: Path to emoji_mappings.yaml file
        """
        if emoji_config_path is None:
            # Default to lib/config/emoji_mappings.yaml
            project_root = Path(__file__).parent.parent
            emoji_config_path = project_root / "lib" / "config" / "emoji_mappings.yaml"

        self.emoji_config_path = Path(emoji_config_path)
        self.config = self._load_emoji_config()

        # Common patterns that indicate new resource types
        self.resource_patterns = {
            "new_directory": re.compile(r"^[AM]\s+([^/]+/[^/]*/)$"),
            "new_service": re.compile(r"class\s+(\w+Service|Manager|Handler|Provider)"),
            "new_component": re.compile(r"(ai/(agents|teams|workflows)/\w+/)"),
            "new_script": re.compile(r"^[AM]\s+(scripts/\w+\.(py|sh))$"),
            "config_file": re.compile(r"^[AM]\s+.*\.(yaml|yml|json|toml)$"),
        }

        # Validation results
        self.violations = []
        self.warnings = []

    def _load_emoji_config(self) -> dict:
        """Load emoji mappings configuration."""
        try:
            if not self.emoji_config_path.exists():
                return {}

            with open(self.emoji_config_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}

        except Exception as e:
            logger.warning(f"Could not load emoji config: {e}")
            return {}

    def validate_staged_files(self, file_paths: list[str]) -> bool:
        """Validate emoji mappings for staged files.

        Args:
            file_paths: List of staged file paths

        Returns:
            True if validation passes, False otherwise
        """
        # Analyze staged files for new resource types
        new_resources = self._detect_new_resources(file_paths)

        # Check if emoji mappings exist for detected resources
        missing_mappings = self._check_missing_mappings(new_resources)

        # Generate suggestions for missing mappings
        if missing_mappings:
            self._generate_mapping_suggestions(missing_mappings)

        return len(self.violations) == 0

    def _detect_new_resources(self, file_paths: list[str]) -> dict[str, set[str]]:
        """Detect new resource types from file paths.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            Dictionary mapping resource types to detected resources
        """
        detected = {
            "directories": set(),
            "services": set(),
            "scripts": set(),
            "config_files": set(),
        }

        for file_path in file_paths:
            # Normalize path separators
            normalized_path = file_path.replace("\\", "/")

            # Check for new directories
            if "/" in normalized_path:
                directory = "/".join(normalized_path.split("/")[:-1]) + "/"
                detected["directories"].add(directory)

            # Check for service/component patterns in file content (if accessible)
            if normalized_path.endswith(".py"):
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()

                    # Look for service class patterns
                    service_matches = self.resource_patterns["new_service"].findall(
                        content,
                    )
                    detected["services"].update(service_matches)

                except Exception:
                    # Skip files that can't be read
                    pass

            # Check for script files
            if self.resource_patterns["new_script"].match(f"A {normalized_path}"):
                detected["scripts"].add(normalized_path)

            # Check for config files
            if self.resource_patterns["config_file"].match(f"A {normalized_path}"):
                detected["config_files"].add(normalized_path)

        return detected

    def _check_missing_mappings(
        self,
        detected_resources: dict[str, set[str]],
    ) -> dict[str, set[str]]:
        """Check for missing emoji mappings.

        Args:
            detected_resources: Detected resource types

        Returns:
            Dictionary of missing mappings
        """
        missing = {}
        resource_types = self.config.get("resource_types", {})

        # Check directories
        directory_mappings = resource_types.get("directories", {})
        missing_dirs = set()

        for directory in detected_resources.get("directories", set()):
            # Skip common directories that don't need specific mappings
            if self._is_common_directory(directory):
                continue

            # Check if mapping exists (exact match or pattern match)
            if not self._has_directory_mapping(directory, directory_mappings):
                missing_dirs.add(directory)

        if missing_dirs:
            missing["directories"] = missing_dirs

        # Check services (would go in 'services' section)
        service_mappings = resource_types.get("services", {})
        missing_services = set()

        for service in detected_resources.get("services", set()):
            service_key = (
                service.lower()
                .replace("service", "")
                .replace("manager", "")
                .replace("handler", "")
            )
            if service_key not in service_mappings:
                missing_services.add(service)

        if missing_services:
            missing["services"] = missing_services

        return missing

    def _is_common_directory(self, directory: str) -> bool:
        """Check if directory is common and doesn't need specific mapping."""
        common_dirs = {
            ".git/",
            ".github/",
            "__pycache__/",
            ".pytest_cache/",
            "node_modules/",
            ".vscode/",
            ".idea/",
            "dist/",
            "build/",
            ".env/",
            "venv/",
            ".venv/",
        }
        return directory in common_dirs or directory.endswith("/__pycache__/")

    def _has_directory_mapping(self, directory: str, mappings: dict[str, str]) -> bool:
        """Check if directory has an emoji mapping (exact or pattern match)."""
        # Exact match
        if directory in mappings:
            return True

        # Check if any parent directory has a mapping
        parts = directory.rstrip("/").split("/")
        for i in range(len(parts)):
            parent_dir = "/".join(parts[: i + 1]) + "/"
            if parent_dir in mappings:
                return True

        return False

    def _generate_mapping_suggestions(
        self,
        missing_mappings: dict[str, set[str]],
    ) -> None:
        """Generate suggestions for missing emoji mappings."""
        for resource_type, resources in missing_mappings.items():
            for resource in resources:
                suggestion = self._suggest_emoji(resource_type, resource)

                violation = {
                    "type": "missing_emoji_mapping",
                    "resource_type": resource_type,
                    "resource": resource,
                    "suggestion": suggestion,
                    "config_path": str(self.emoji_config_path),
                }

                self.violations.append(violation)

    def _suggest_emoji(self, resource_type: str, resource: str) -> str:
        """Suggest appropriate emoji for resource."""
        suggestions = {
            # Directory-based suggestions
            "lib/": "🔧",
            "api/": "🌐",
            "scripts/": "📜",
            "tests/": "🧪",
            "docs/": "📚",
            "config/": "⚙️",
            "data/": "💾",
            "static/": "🎨",
            "templates/": "📄",
            "migrations/": "🔄",
            # Service-based suggestions
            "auth": "🔐",
            "database": "🗄️",
            "cache": "⚡",
            "queue": "📬",
            "storage": "💾",
            "notification": "📱",
            "logging": "📝",
            "metrics": "📊",
            "monitoring": "📊",
            "backup": "💾",
            "security": "🔐",
        }

        # Try to find a good suggestion based on keywords
        resource_lower = resource.lower()

        for keyword, emoji in suggestions.items():
            if keyword in resource_lower:
                return emoji

        # Default fallback
        return "📄"

    def format_violations(self, output_format: str = "text") -> str:
        """Format validation violations for output.

        Args:
            output_format: Output format ('text' or 'json')

        Returns:
            Formatted violation report
        """
        if output_format == "json":
            return json.dumps(
                {
                    "violations": self.violations,
                    "warnings": self.warnings,
                    "total_violations": len(self.violations),
                    "total_warnings": len(self.warnings),
                },
                indent=2,
            )

        # Text format
        output = []

        if self.violations:
            output.append("❌ EMOJI MAPPING VIOLATIONS:")
            output.append("")

            for i, violation in enumerate(self.violations, 1):
                resource_type = violation["resource_type"]
                resource = violation["resource"]
                suggestion = violation["suggestion"]
                config_path = violation["config_path"]

                output.append(
                    f"{i}. Missing emoji mapping for {resource_type}: {resource}",
                )
                output.append(f"   Suggested emoji: {suggestion}")
                output.append(f"   Add to {config_path}:")
                output.append("   resource_types:")
                output.append(f"     {resource_type}:")
                output.append(f'       "{resource}": "{suggestion}"')
                output.append("")

        if self.warnings:
            output.append("⚠️ WARNINGS:")
            output.append("")

            for i, warning in enumerate(self.warnings, 1):
                output.append(f"{i}. {warning}")
                output.append("")

        if not self.violations and not self.warnings:
            output.append("✅ All emoji mappings are up to date!")

        return "\n".join(output)


def main():
    """Main entry point for emoji mapping validation."""
    parser = argparse.ArgumentParser(
        description="Validate emoji mappings for codebase resources",
    )

    parser.add_argument(
        "--staged-files",
        action="store_true",
        help="Validate staged files (for git hooks)",
    )

    parser.add_argument("--files", nargs="*", help="Specific files to validate")

    parser.add_argument("--config", help="Path to emoji_mappings.yaml file")

    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )

    args = parser.parse_args()

    # Create validator
    validator = EmojiMappingValidator(args.config)

    # Get files to validate
    if args.staged_files:
        # Get staged files from git
        import subprocess

        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                check=True,
            )
            files_to_check = (
                result.stdout.strip().split("\n") if result.stdout.strip() else []
            )
        except subprocess.CalledProcessError:
            logger.error("Could not get staged files from git")
            sys.exit(1)
    elif args.files:
        files_to_check = args.files
    else:
        logger.error("Must specify --staged-files or --files")
        sys.exit(1)

    # Validate files
    validation_passed = validator.validate_staged_files(files_to_check)

    # Output results
    output = validator.format_violations(args.format)
    logger.info(output)

    # Exit with appropriate code
    sys.exit(0 if validation_passed else 1)


if __name__ == "__main__":
    main()
