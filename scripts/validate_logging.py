#!/usr/bin/env python3
"""Logging Standards Validator.

Comprehensive validator for Automagik Hive logging standards.
Detects violations and provides helpful error messages for developers.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

# Emoji categories for validation
EMOJI_CATEGORIES = {
    "🔧": "System/Config",
    "📊": "Data/Knowledge",
    "🤖": "Agent/AI",
    "📱": "Communication",
    "🔐": "Security/Auth",
    "🌐": "API/Network",
    "⚡": "Performance",
    "🐛": "Debug/Dev",
    "🎯": "Focus/Target",
    "🚨": "Alert/Critical",
    "⚠️": "Warning/Caution",
}


class LoggingViolation:
    def __init__(
        self,
        file_path: str,
        line_number: int,
        violation_type: str,
        line_content: str,
        message: str,
        fix_suggestion: str | None = None,
    ):
        self.file_path = file_path
        self.line_number = line_number
        self.violation_type = violation_type
        self.line_content = line_content.strip()
        self.message = message
        self.fix_suggestion = fix_suggestion

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file_path,
            "line": self.line_number,
            "type": self.violation_type,
            "content": self.line_content,
            "message": self.message,
            "fix": self.fix_suggestion,
        }


class LoggingValidator:
    def __init__(self, whitelist_config: str | None = None):
        self.violations = []
        self.whitelist = self._load_whitelist(whitelist_config)

    def _load_whitelist(self, config_path: str | None) -> dict[str, list[str]]:
        """Load whitelist configuration."""
        default_whitelist = {
            "print_statements_allowed": [
                "lib/auth/cli.py",
                "lib/utils/startup_display.py",
                "common/startup_display.py",
                "api/serve.py",  # console.print for tables
            ],
            "emoji_exempt_patterns": ["test_*.py", "*_test.py", "tests/*.py"],
            "logging_import_exempt": [
                "lib/logging/config.py",  # Core logging configuration
            ],
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path) as f:
                    user_whitelist = yaml.safe_load(f)
                    default_whitelist.update(user_whitelist)
            except Exception:
                # Warning: Could not load whitelist config - using defaults
                pass

        return default_whitelist

    def _is_whitelisted(self, file_path: str, violation_type: str) -> bool:
        """Check if file is whitelisted for specific violation type."""
        whitelist_key = {
            "print_statement": "print_statements_allowed",
            "missing_emoji": "emoji_exempt_patterns",
            "wrong_import": "logging_import_exempt",
        }.get(violation_type)

        if not whitelist_key:
            return False

        patterns = self.whitelist.get(whitelist_key, [])

        for pattern in patterns:
            if pattern in file_path or file_path.endswith(pattern.replace("*", "")):
                return True
        return False

    def validate_file(self, file_path: Path) -> None:
        """Validate a single Python file for logging violations."""
        if file_path.suffix != ".py":
            return

        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            return  # Skip files that can't be read

        try:
            relative_path = str(file_path.relative_to(Path.cwd()))
        except ValueError:
            # File is outside current directory, use absolute path
            relative_path = str(file_path)

        for line_num, line in enumerate(lines, 1):
            self._check_import_violations(relative_path, line_num, line)
            self._check_print_violations(relative_path, line_num, line)
            self._check_emoji_violations(relative_path, line_num, line)

    def _check_import_violations(
        self,
        file_path: str,
        line_num: int,
        line: str,
    ) -> None:
        """Check for incorrect logging import patterns."""
        if self._is_whitelisted(file_path, "wrong_import"):
            return

        # Check for various logging import patterns
        wrong_import_patterns = [
            (r"^\s*import\s+logging\s*$", "Direct 'import logging' detected"),
            (r"^\s*import\s+logging\s+as\s+\w+", "Import logging with alias detected"),
            (r"^\s*from\s+logging\s+import", "Import from logging module detected"),
        ]

        for pattern, message in wrong_import_patterns:
            if re.match(pattern, line):
                self.violations.append(
                    LoggingViolation(
                        file_path=file_path,
                        line_number=line_num,
                        violation_type="wrong_import",
                        line_content=line,
                        message=message,
                        fix_suggestion="Replace with: from lib.logging import logger",
                    ),
                )
                return  # Only report first match

        # Check for getLogger pattern (but skip string literals and comments)
        if (
            "getLogger(__name__)" in line or "getLogger(" in line
        ) and not line.strip().startswith("#"):
            # Skip if it's in a string literal or comment about getLogger
            if not any(
                skip in line for skip in ['"getLogger', "'getLogger", "# ", "pattern"]
            ):
                self.violations.append(
                    LoggingViolation(
                        file_path=file_path,
                        line_number=line_num,
                        violation_type="wrong_import",
                        line_content=line,
                        message="getLogger pattern detected",
                        fix_suggestion="Replace with: from lib.logging import logger",
                    ),
                )

    def _check_print_violations(self, file_path: str, line_num: int, line: str) -> None:
        """Check for print statements in production code."""
        if self._is_whitelisted(file_path, "print_statement"):
            return

        # Skip test files and comments
        if any(pattern in file_path for pattern in ["test", "spec"]):
            return

        # Enhanced print detection - catch actual print calls, not regex patterns
        if re.search(r"\bprint\s*\(", line) and not line.strip().startswith("#"):
            # Don't flag console.print (Rich library) or stdout.write
            if any(
                allowed in line
                for allowed in ["console.print", "stdout.write", "stderr.write"]
            ):
                return

            # Skip regex pattern definitions and comments
            if any(skip in line for skip in [r'r"', r"r'", "# ", "regex", "pattern"]):
                return

            # Get context-aware emoji and fix suggestion
            suggested_emoji = self._suggest_emoji_from_context(file_path, line)

            # Extract the print content for better suggestion
            print_match = re.search(r"print\s*\(\s*([^)]+)\)", line)
            if print_match:
                print_content = print_match.group(1).strip()
                # Clean up quotes for the suggestion
                if (print_content.startswith('"') and print_content.endswith('"')) or (
                    print_content.startswith("'") and print_content.endswith("'")
                ):
                    clean_content = print_content[1:-1]
                else:
                    clean_content = print_content

                fix_suggestion = f"logger.info('{suggested_emoji} {clean_content}')"
            else:
                fix_suggestion = f"logger.info('{suggested_emoji} Your message here')"

            self.violations.append(
                LoggingViolation(
                    file_path=file_path,
                    line_number=line_num,
                    violation_type="print_statement",
                    line_content=line,
                    message="Print statement detected in production code",
                    fix_suggestion=fix_suggestion,
                ),
            )

    def _check_emoji_violations(self, file_path: str, line_num: int, line: str) -> None:
        """Check for logger calls missing emoji prefixes."""
        if self._is_whitelisted(file_path, "missing_emoji"):
            return

        # Match logger calls - handle both regular strings and f-strings
        logger_match = re.search(
            r"logger\.(info|debug|warning|error|critical)\s*\(",
            line,
        )
        if not logger_match:
            return

        log_level = logger_match.group(1)

        # Extract message content (handle f-strings and regular strings)
        message_match = re.search(
            r"logger\." + log_level + r'\s*\(\s*[f]?["\']([^"\']*)["\']',
            line,
        )
        if message_match:
            message = message_match.group(1)
        else:
            # Complex string formatting - check if line has emojis anywhere
            message = ""

        # Skip if line contains ANY emojis (standard or custom)
        all_emojis = [
            *list(EMOJI_CATEGORIES.keys()),
            "✅",
            "❌",
            "🔄",
            "📋",
            "👤",
            "💬",
            "📞",
            "🔍",
            "🏁",
            "\U0001f9ea",
        ]
        if any(emoji in line for emoji in all_emojis):
            return

        # Skip fix suggestions and variable assignments
        if any(skip in line for skip in ["fix_suggestion", 'f"logger.', "f'logger."]):
            return

        # Suggest appropriate emoji based on context and file path
        suggested_emoji = self._suggest_emoji_from_context(file_path, line)

        self.violations.append(
            LoggingViolation(
                file_path=file_path,
                line_number=line_num,
                violation_type="missing_emoji",
                line_content=line,
                message=f"Logger call missing emoji prefix (level: {log_level})",
                fix_suggestion=f"Add emoji prefix: logger.{log_level}('{suggested_emoji} {message}')",
            ),
        )

    def _suggest_emoji(self, file_path: str) -> str:
        """Suggest appropriate emoji based on file path."""
        path_lower = file_path.lower()

        if any(
            keyword in path_lower for keyword in ["api", "route", "endpoint", "mcp"]
        ):
            return "🌐"
        if any(
            keyword in path_lower for keyword in ["agent", "team", "workflow", "ai"]
        ):
            return "🤖"
        if any(
            keyword in path_lower
            for keyword in ["notification", "whatsapp", "communication"]
        ):
            return "📱"
        if any(keyword in path_lower for keyword in ["auth", "security", "key"]):
            return "🔐"
        if any(keyword in path_lower for keyword in ["metric", "performance", "async"]):
            return "⚡"
        if any(keyword in path_lower for keyword in ["data", "csv", "knowledge", "db"]):
            return "📊"
        if any(
            keyword in path_lower for keyword in ["config", "storage", "util", "proxy"]
        ):
            return "🔧"
        return "🔧"  # Default system emoji

    def _suggest_emoji_from_context(self, file_path: str, line: str) -> str:
        """Suggest emoji based on both file path and line content context."""
        line_lower = line.lower()

        # Analyze line content for specific keywords
        if any(
            keyword in line_lower
            for keyword in ["api", "request", "response", "http", "endpoint", "url"]
        ):
            return "🌐"
        if any(
            keyword in line_lower
            for keyword in [
                "database",
                "query",
                "sql",
                "db",
                "data",
                "csv",
                "knowledge",
            ]
        ):
            return "📊"
        if any(
            keyword in line_lower
            for keyword in ["auth", "login", "password", "token", "security", "key"]
        ):
            return "🔐"
        if any(
            keyword in line_lower
            for keyword in ["agent", "ai", "model", "prompt", "completion"]
        ):
            return "🤖"
        if any(
            keyword in line_lower
            for keyword in ["notification", "message", "whatsapp", "send", "notify"]
        ):
            return "📱"
        if any(
            keyword in line_lower
            for keyword in ["performance", "metric", "time", "speed", "async", "await"]
        ):
            return "⚡"
        if any(
            keyword in line_lower
            for keyword in ["error", "exception", "failed", "critical", "alert"]
        ):
            return "🚨"
        if any(
            keyword in line_lower
            for keyword in ["warning", "warn", "caution", "deprecated"]
        ):
            return "⚠️"
        if any(keyword in line_lower for keyword in ["debug", "trace", "dev", "test"]):
            return "🐛"
        if any(
            keyword in line_lower
            for keyword in ["target", "focus", "goal", "objective"]
        ):
            return "🎯"
        # Fall back to file path analysis
        return self._suggest_emoji(file_path)

    def validate_project(self, project_path: Path | None = None) -> None:
        """Validate entire project for logging violations."""
        if project_path is None:
            project_path = Path.cwd()

        # Find all Python files
        python_files = []
        for pattern in ["**/*.py"]:
            python_files.extend(project_path.glob(pattern))

        # Filter out virtual environments and build directories
        python_files = [
            f
            for f in python_files
            if not any(
                exclude in str(f)
                for exclude in [
                    ".venv",
                    "venv",
                    "__pycache__",
                    ".git",
                    "node_modules",
                    "dist",
                    "build",
                    ".pytest_cache",
                ]
            )
        ]

        for file_path in python_files:
            self.validate_file(file_path)

    def get_violations_by_type(self) -> dict[str, list[LoggingViolation]]:
        """Group violations by type."""
        violations_by_type = {}
        for violation in self.violations:
            if violation.violation_type not in violations_by_type:
                violations_by_type[violation.violation_type] = []
            violations_by_type[violation.violation_type].append(violation)
        return violations_by_type

    def generate_report(self, output_format: str = "text") -> str:
        """Generate violation report."""
        if output_format == "json":
            return json.dumps([v.to_dict() for v in self.violations], indent=2)

        # Text format
        if not self.violations:
            return "✅ No logging violations found! 100% compliance achieved."

        report = []
        report.append("🚨 LOGGING VIOLATIONS DETECTED")
        report.append("=" * 50)
        report.append(f"Total violations: {len(self.violations)}")
        report.append("")

        violations_by_type = self.get_violations_by_type()

        for violation_type, violations in violations_by_type.items():
            violation_type_name = {
                "print_statement": "PRINT STATEMENTS",
                "missing_emoji": "MISSING EMOJIS",
                "wrong_import": "WRONG IMPORTS",
            }.get(violation_type, violation_type.upper())

            report.append(f"📋 {violation_type_name} ({len(violations)} violations)")
            report.append("-" * 40)

            for violation in violations:
                report.append(f"📁 {violation.file_path}:{violation.line_number}")
                report.append(f"   ❌ FOUND: {violation.line_content.strip()}")
                report.append(f"   💡 ISSUE: {violation.message}")
                if violation.fix_suggestion:
                    report.append(f"   ✅ FIX TO: {violation.fix_suggestion}")
                report.append("")

        # Add emoji reference
        report.append("📚 EMOJI REFERENCE")
        report.append("-" * 20)
        for emoji, category in EMOJI_CATEGORIES.items():
            report.append(f"{emoji} {category}")

        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Validate logging standards compliance",
    )
    parser.add_argument(
        "--path",
        type=str,
        help="Path to validate (default: current directory)",
    )
    parser.add_argument("--file", type=str, help="Validate single file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument("--whitelist", type=str, help="Path to whitelist configuration")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode - exit with error code if violations found",
    )
    parser.add_argument(
        "--staged-files",
        action="store_true",
        help="Only validate git staged files (for pre-commit hook)",
    )

    args = parser.parse_args()

    validator = LoggingValidator(whitelist_config=args.whitelist)

    if args.staged_files:
        # Get staged files from git
        import subprocess

        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                capture_output=True,
                text=True,
                check=True,
            )
            staged_files = [f.strip() for f in result.stdout.split("\n") if f.strip()]
            staged_python_files = [f for f in staged_files if f.endswith(".py")]

            for file_path in staged_python_files:
                path_obj = Path(file_path)
                if path_obj.exists():
                    validator.validate_file(path_obj)
        except subprocess.CalledProcessError:
            sys.stderr.write("Error: Could not get staged files from git\n")
            sys.exit(1)
    elif args.file:
        validator.validate_file(Path(args.file))
    else:
        project_path = Path(args.path) if args.path else Path.cwd()
        validator.validate_project(project_path)

    # Generate and print report
    report = validator.generate_report(args.format)
    sys.stdout.write(report + "\n")

    # Exit with error code if violations found and strict mode enabled
    if args.strict and validator.violations:
        sys.exit(1)


if __name__ == "__main__":
    main()
