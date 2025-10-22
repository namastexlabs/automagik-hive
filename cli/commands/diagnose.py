"""Diagnostic Commands for Troubleshooting Installation Issues.

Provides comprehensive diagnostics to help users troubleshoot:
- Workspace structure and required files
- Docker configuration and availability
- PostgreSQL container status
- Environment configuration
- API keys and credentials

Design:
- Fail-fast validation with actionable error messages
- Comprehensive reporting of ALL issues found
- Clear distinction between missing setup vs configuration errors
- Guidance on how to fix each class of problem
"""

import os
import subprocess
from pathlib import Path


class DiagnoseCommands:
    """Diagnose common installation and configuration issues."""

    def __init__(self, workspace_path: Path | None = None):
        """Initialize diagnostic commands.

        Args:
            workspace_path: Path to workspace directory (defaults to current directory)
        """
        self.workspace_path = workspace_path or Path()

    def diagnose_installation(self, verbose: bool = False) -> bool:
        """Run comprehensive installation diagnostics.

        Checks:
        - Workspace structure and required files
        - Docker configuration and availability
        - PostgreSQL container status
        - Environment configuration
        - API keys and credentials

        Args:
            verbose: Show additional details and warnings

        Returns:
            True if all checks pass, False otherwise
        """
        print("\n🔍 Automagik Hive Diagnostic Report")
        print("=" * 50)

        checks = [
            self._check_workspace_structure,
            self._check_docker_files,
            self._check_docker_daemon,
            self._check_postgres_status,
            self._check_environment_config,
            self._check_api_keys,
        ]

        all_passed = True
        results = []

        for check_func in checks:
            check_name, passed, issues = check_func()
            results.append((check_name, passed, issues))

            emoji = "✅" if passed else "❌"
            print(f"\n{emoji} {check_name}")

            if not passed:
                all_passed = False
                for issue in issues:
                    print(f"   • {issue}")
            elif verbose and issues:  # Warnings
                for issue in issues:
                    print(f"   ℹ️  {issue}")

        print("\n" + "=" * 50)

        if all_passed:
            print("✅ All checks passed!")
            print("\n💡 Next steps:")
            print("   • Start development server: automagik-hive dev")
            print("   • View API docs: http://localhost:8886/docs")
        else:
            print("⚠️  Some checks failed")
            print("\n💡 Fix the issues above, then run:")
            print("   automagik-hive diagnose --verbose")

        return all_passed

    def _check_workspace_structure(self) -> tuple[str, bool, list[str]]:
        """Check workspace has required directory structure.

        Returns:
            (check_name, passed, issues_found)
        """
        issues = []
        workspace = self.workspace_path

        required_dirs = [
            "ai/agents",
            "ai/teams",
            "ai/workflows",
            "knowledge",
        ]

        for dir_path in required_dirs:
            full_path = workspace / dir_path
            if not full_path.exists():
                issues.append(f"Missing directory: {dir_path}")

        if issues:
            issues.append("Run 'automagik-hive init' to create workspace structure")

        return ("Workspace Structure", len(issues) == 0, issues)

    def _check_docker_files(self) -> tuple[str, bool, list[str]]:
        """Check Docker configuration files exist.

        Returns:
            (check_name, passed, issues_found)
        """
        issues = []
        workspace = self.workspace_path

        docker_files = [
            "docker/main/docker-compose.yml",
            "docker/main/Dockerfile",
        ]

        for file_path in docker_files:
            full_path = workspace / file_path
            if not full_path.exists():
                issues.append(f"Missing: {file_path}")

        # Check if compose file has postgres service
        compose_file = workspace / "docker/main/docker-compose.yml"
        if compose_file.exists():
            try:
                content = compose_file.read_text()
                if "hive-postgres" not in content:
                    issues.append("docker-compose.yml missing 'hive-postgres' service")
            except Exception as e:
                issues.append(f"Cannot read docker-compose.yml: {e}")

        if issues:
            issues.append("Run 'automagik-hive init' to create Docker configuration")

        return ("Docker Configuration", len(issues) == 0, issues)

    def _check_docker_daemon(self) -> tuple[str, bool, list[str]]:
        """Check Docker daemon is running.

        Returns:
            (check_name, passed, issues_found)
        """
        issues = []

        try:
            result = subprocess.run(["docker", "ps"], capture_output=True, timeout=5, check=False)
            if result.returncode != 0:
                issues.append("Docker daemon not responding")
                issues.append("Try: 'sudo systemctl start docker' or start Docker Desktop")
        except FileNotFoundError:
            issues.append("Docker not installed")
            issues.append("Install from: https://docs.docker.com/get-docker/")
        except subprocess.TimeoutExpired:
            issues.append("Docker command timed out")

        return ("Docker Daemon", len(issues) == 0, issues)

    def _check_postgres_status(self) -> tuple[str, bool, list[str]]:
        """Check PostgreSQL container status.

        Returns:
            (check_name, passed, issues_found)
        """
        issues = []

        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=hive-postgres", "--format", "{{.Status}}"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            if result.returncode == 0:
                if result.stdout.strip():
                    if "Up" in result.stdout:
                        pass  # Running, all good
                    else:
                        issues.append("PostgreSQL container exists but not running")
                        issues.append("Try: 'automagik-hive postgres-start'")
                else:
                    issues.append("PostgreSQL container not found")
                    issues.append("Try: 'automagik-hive install'")
            else:
                issues.append("Could not check PostgreSQL status")
        except Exception:
            issues.append("Error checking PostgreSQL")

        return ("PostgreSQL Status", len(issues) == 0, issues)

    def _check_environment_config(self) -> tuple[str, bool, list[str]]:
        """Check .env file exists and has required keys.

        Returns:
            (check_name, passed, issues_found)
        """
        issues = []
        workspace = self.workspace_path

        env_file = workspace / ".env"
        if not env_file.exists():
            issues.append(".env file not found")
            issues.append("Try: 'cp .env.example .env'")
            return ("Environment Config", False, issues)

        try:
            content = env_file.read_text()
        except Exception as e:
            issues.append(f"Cannot read .env file: {e}")
            return ("Environment Config", False, issues)

        required_keys = [
            "HIVE_ENVIRONMENT",
            "HIVE_API_PORT",
            "HIVE_DATABASE_URL",
            "HIVE_API_KEY",
        ]

        for key in required_keys:
            if f"{key}=" not in content:
                issues.append(f"Missing key: {key}")

        # Check for placeholder values
        if "your-database-url-here" in content:
            issues.append("HIVE_DATABASE_URL contains placeholder value")

        if "your-api-key-here" in content:
            issues.append("HIVE_API_KEY contains placeholder value")

        if issues:
            issues.append("Run 'automagik-hive install' to generate proper configuration")

        return ("Environment Config", len(issues) == 0, issues)

    def _check_api_keys(self) -> tuple[str, bool, list[str]]:
        """Check AI provider API keys are configured.

        Returns:
            (check_name, passed, issues_found)
        """
        issues = []
        warnings = []

        # At least one provider key should be set
        provider_keys = [
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "GEMINI_API_KEY",
            "GROQ_API_KEY",
        ]

        found_keys = []
        for key in provider_keys:
            value = os.getenv(key, "")
            # Check for valid keys (not placeholders and reasonable length)
            is_placeholder = value in ("your-key-here", "")
            is_valid_length = len(value) > 10
            if value and not is_placeholder and is_valid_length:
                found_keys.append(key)

        if not found_keys:
            issues.append("No AI provider API keys configured")
            issues.append("Set at least one: ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.")
        else:
            warnings.append(f"Found API keys: {', '.join(found_keys)}")

        return ("API Keys", len(issues) == 0, warnings + issues)
