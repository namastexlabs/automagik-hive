"""Infrastructure adapter for file system operations.

This module provides file system operations needed by the pre-commit
validation system, including bypass flag management and project
structure detection.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class FileSystemAdapter:
    """Adapter for file system operations and bypass management.

    This class handles file system interactions needed for the validation
    system, including bypass flag creation/removal and project path resolution.
    """

    def __init__(self, project_root: str | None = None):
        """Initialize filesystem adapter with project root.

        Args:
            project_root: Root directory of project, uses current directory if None
        """
        self.project_root = Path(project_root or os.getcwd())
        self.hooks_dir = self.project_root / ".git" / "hooks"
        self.bypass_file = self.hooks_dir / "BYPASS_ROOT_VALIDATION"
        self.metrics_file = self.hooks_dir / "validation_metrics.json"

    def check_bypass_flag(self) -> bool:
        """Check if bypass flag exists and is still valid.

        Returns:
            True if valid bypass flag exists, False otherwise
        """
        if not self.bypass_file.exists():
            return False

        try:
            # Check if bypass has expired
            bypass_info = self._read_bypass_info()
            if bypass_info and self._is_bypass_expired(bypass_info):
                self.remove_bypass_flag()
                return False

            return True
        except Exception:
            # If we can't read bypass info, assume it's invalid
            return False

    def create_bypass_flag(
        self, reason: str, duration_hours: int = 1, created_by: str | None = None
    ) -> bool:
        """Create bypass flag with metadata and expiration.

        Args:
            reason: Reason for creating bypass
            duration_hours: How long bypass should last (default: 1 hour)
            created_by: Who created the bypass (auto-detected if None)

        Returns:
            True if bypass flag was created successfully
        """
        try:
            # Ensure hooks directory exists
            self.hooks_dir.mkdir(parents=True, exist_ok=True)

            # Get user info
            if not created_by:
                created_by = self._get_git_user() or "unknown"

            # Create bypass info
            bypass_info = {
                "reason": reason,
                "duration_hours": duration_hours,
                "created_by": created_by,
                "created_at": datetime.now().isoformat(),
                "expires_at": (
                    datetime.now() + timedelta(hours=duration_hours)
                ).isoformat(),
            }

            # Write bypass file
            with open(self.bypass_file, "w") as f:
                f.write("# Pre-commit hook bypass flag\n")
                f.write(f"# Created: {bypass_info['created_at']}\n")
                f.write(f"# Expires: {bypass_info['expires_at']}\n")
                f.write(f"# Created by: {bypass_info['created_by']}\n")
                f.write(f"# Reason: {bypass_info['reason']}\n")
                f.write(f"# Duration: {duration_hours} hours\n")
                f.write("\n")
                f.write(json.dumps(bypass_info, indent=2))

            return True

        except Exception as e:
            print(f"Warning: Failed to create bypass flag: {e}")
            return False

    def remove_bypass_flag(self) -> bool:
        """Remove bypass flag if it exists.

        Returns:
            True if bypass flag was removed or didn't exist
        """
        try:
            if self.bypass_file.exists():
                self.bypass_file.unlink()
            return True
        except Exception as e:
            print(f"Warning: Failed to remove bypass flag: {e}")
            return False

    def get_bypass_info(self) -> dict[str, Any] | None:
        """Get bypass flag information if it exists.

        Returns:
            Dictionary with bypass information, or None if no bypass
        """
        return self._read_bypass_info()

    def get_project_root(self) -> str:
        """Get absolute path to project root directory.

        Returns:
            Absolute path to project root
        """
        return str(self.project_root.absolute())

    def ensure_directories_exist(self) -> None:
        """Ensure required directories exist for the hook system."""
        directories = [
            self.hooks_dir,
            self.project_root / "src" / "hooks" / "domain",
            self.project_root / "src" / "hooks" / "application",
            self.project_root / "src" / "hooks" / "infrastructure",
            self.project_root / "tests" / "hooks",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def record_validation_metrics(self, metrics: dict[str, Any]) -> None:
        """Record validation metrics to file.

        Args:
            metrics: Dictionary containing validation metrics
        """
        try:
            # Load existing metrics
            existing_metrics = []
            if self.metrics_file.exists():
                with open(self.metrics_file) as f:
                    existing_metrics = json.load(f)

            # Add new metrics with timestamp
            metrics["timestamp"] = datetime.now().isoformat()
            existing_metrics.append(metrics)

            # Keep only last 1000 entries to prevent file from growing too large
            if len(existing_metrics) > 1000:
                existing_metrics = existing_metrics[-1000:]

            # Write back to file
            self.hooks_dir.mkdir(parents=True, exist_ok=True)
            with open(self.metrics_file, "w") as f:
                json.dump(existing_metrics, f, indent=2)

        except Exception as e:
            print(f"Warning: Failed to record metrics: {e}")

    def get_validation_metrics(self, days: int = 7) -> dict[str, Any]:
        """Get validation metrics for the specified number of days.

        Args:
            days: Number of days to look back for metrics

        Returns:
            Dictionary with aggregated metrics
        """
        try:
            if not self.metrics_file.exists():
                return {"total_validations": 0}

            with open(self.metrics_file) as f:
                all_metrics = json.load(f)

            # Filter by date range
            cutoff = datetime.now() - timedelta(days=days)
            recent_metrics = []

            for metric in all_metrics:
                try:
                    metric_time = datetime.fromisoformat(metric["timestamp"])
                    if metric_time > cutoff:
                        recent_metrics.append(metric)
                except (KeyError, ValueError):
                    continue

            if not recent_metrics:
                return {"total_validations": 0}

            # Calculate summary statistics
            total = len(recent_metrics)
            blocked = sum(1 for m in recent_metrics if m.get("blocked_count", 0) > 0)
            bypassed = sum(1 for m in recent_metrics if m.get("bypass_used", False))

            return {
                "total_validations": total,
                "blocked_validations": blocked,
                "bypassed_validations": bypassed,
                "success_rate": (total - blocked) / total if total > 0 else 1.0,
                "bypass_rate": bypassed / total if total > 0 else 0.0,
                "avg_files_per_validation": sum(
                    m.get("files_checked", 0) for m in recent_metrics
                )
                / total
                if total > 0
                else 0.0,
            }

        except Exception as e:
            print(f"Warning: Failed to get metrics: {e}")
            return {"total_validations": 0, "error": str(e)}

    def _read_bypass_info(self) -> dict[str, Any] | None:
        """Read bypass information from bypass flag file.

        Returns:
            Dictionary with bypass info, or None if file doesn't exist or is invalid
        """
        try:
            if not self.bypass_file.exists():
                return None

            with open(self.bypass_file) as f:
                content = f.read()

            # Find JSON content (everything after the comments)
            lines = content.split("\n")
            json_start = None
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith("#"):
                    json_start = i
                    break

            if json_start is None:
                return None

            json_content = "\n".join(lines[json_start:])
            return json.loads(json_content)

        except Exception:
            return None

    def _is_bypass_expired(self, bypass_info: dict[str, Any]) -> bool:
        """Check if bypass has expired based on its metadata.

        Args:
            bypass_info: Dictionary containing bypass information

        Returns:
            True if bypass has expired
        """
        try:
            expires_at = datetime.fromisoformat(bypass_info["expires_at"])
            return datetime.now() > expires_at
        except (KeyError, ValueError):
            # If we can't parse expiration, consider it expired
            return True

    def _get_git_user(self) -> str | None:
        """Get current Git user name.

        Returns:
            Git user name, or None if unable to determine
        """
        try:
            import subprocess

            result = subprocess.run(
                ["git", "config", "user.name"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return None
