"""
AGNO Configuration Migration Utility

Migrates existing redundant configurations to use inheritance model.
Safely removes redundant parameters while preserving intentional overrides.
"""

import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from agno.utils.log import logger


class AGNOConfigMigrator:
    """Migrates AGNO configurations to inheritance model."""

    def __init__(self, base_path: str = "ai", dry_run: bool = True):
        self.base_path = Path(base_path)
        self.dry_run = dry_run
        self.backup_dir = Path(
            f"backups/config_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.migration_log = []

    def migrate_all_teams(self) -> dict[str, Any]:
        """Migrate all teams to inheritance model."""
        results = {
            "teams_processed": 0,
            "agents_processed": 0,
            "parameters_removed": 0,
            "overrides_preserved": 0,
            "errors": [],
            "warnings": [],
        }

        if not self.dry_run:
            self._create_backup()

        logger.info(f"🔄 Starting configuration migration (dry_run={self.dry_run})")

        # Process each team
        for team_path in self.base_path.glob("teams/*/config.yaml"):
            team_id = team_path.parent.name

            try:
                team_result = self.migrate_team(team_id)
                results["teams_processed"] += 1
                results["agents_processed"] += team_result["agents_processed"]
                results["parameters_removed"] += team_result["parameters_removed"]
                results["overrides_preserved"] += team_result["overrides_preserved"]
                results["warnings"].extend(team_result["warnings"])

                logger.info(f"✅ Migrated team {team_id}")

            except Exception as e:
                error_msg = f"Failed to migrate team {team_id}: {e}"
                results["errors"].append(error_msg)
                logger.error(f"❌ {error_msg}")

        logger.info(f"🔧 🎉 Migration complete: {results}")
        return results

    def migrate_team(self, team_id: str) -> dict[str, Any]:
        """Migrate a specific team to inheritance model."""
        from lib.utils.config_inheritance import ConfigInheritanceManager

        result = {
            "agents_processed": 0,
            "parameters_removed": 0,
            "overrides_preserved": 0,
            "warnings": [],
        }

        # Load team configuration
        team_config_path = self.base_path / "teams" / team_id / "config.yaml"
        with open(team_config_path) as f:
            team_config = yaml.safe_load(f)

        # Load all member configurations
        members = team_config.get("members") or []
        member_configs = {}
        original_configs = {}

        for member_id in members:
            member_path = self.base_path / "agents" / member_id / "config.yaml"
            if member_path.exists():
                with open(member_path) as f:
                    config = yaml.safe_load(f)
                    member_configs[member_id] = config
                    original_configs[member_id] = yaml.safe_load(
                        yaml.dump(config)
                    )  # Deep copy

        if not member_configs:
            result["warnings"].append(f"Team {team_id}: No member configs found")
            return result

        # Analyze inheritance opportunities
        ConfigInheritanceManager()
        migration_plan = self._create_migration_plan(team_config, member_configs)

        # Apply migration
        for member_id, plan in migration_plan.items():
            if plan["removable_params"]:
                result["parameters_removed"] += len(plan["removable_params"])

                if not self.dry_run:
                    self._apply_migration_to_agent(member_id, plan)

                self.migration_log.append(
                    {
                        "team_id": team_id,
                        "member_id": member_id,
                        "removed_params": plan["removable_params"],
                        "preserved_overrides": plan["preserved_overrides"],
                    }
                )

            if plan["preserved_overrides"]:
                result["overrides_preserved"] += len(plan["preserved_overrides"])

            result["agents_processed"] += 1

        return result

    def _create_migration_plan(
        self, team_config: dict[str, Any], member_configs: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Create migration plan for each member agent."""
        from lib.utils.config_inheritance import ConfigInheritanceManager

        manager = ConfigInheritanceManager()
        team_defaults = manager._extract_team_defaults(team_config)
        migration_plan = {}

        for member_id, member_config in member_configs.items():
            plan = {
                "removable_params": [],
                "preserved_overrides": [],
                "comments_to_add": [],
            }

            for category, defaults in team_defaults.items():
                if category not in member_config:
                    continue

                for param, team_value in defaults.items():
                    if param not in member_config[category]:
                        continue

                    member_value = member_config[category][param]

                    if member_value == team_value:
                        # Identical value - can be removed (inherited from team)
                        plan["removable_params"].append(f"{category}.{param}")
                    else:
                        # Different value - preserve as override with comment
                        plan["preserved_overrides"].append(f"{category}.{param}")
                        plan["comments_to_add"].append(
                            {
                                "path": f"{category}.{param}",
                                "comment": f"INTENTIONAL OVERRIDE: {param} differs from team default ({team_value})",
                            }
                        )

            migration_plan[member_id] = plan

        return migration_plan

    def _apply_migration_to_agent(self, member_id: str, plan: dict[str, Any]) -> None:
        """Apply migration plan to a specific agent."""
        member_path = self.base_path / "agents" / member_id / "config.yaml"

        # Load current config
        with open(member_path) as f:
            config = yaml.safe_load(f)

        # Remove redundant parameters
        for param_path in plan["removable_params"]:
            category, param = param_path.split(".")
            if category in config and param in config[category]:
                del config[category][param]

                # Remove category if empty
                if not config[category]:
                    del config[category]

        # Write updated config with comments for preserved overrides
        config_content = self._generate_config_with_comments(
            config, plan["comments_to_add"]
        )

        with open(member_path, "w") as f:
            f.write(config_content)

        logger.info(
            f"🔧 Migrated agent {member_id}: removed {len(plan['removable_params'])} redundant parameters"
        )

    def _generate_config_with_comments(
        self, config: dict[str, Any], comments: list[dict[str, str]]
    ) -> str:
        """Generate YAML config with override comments."""
        # Convert config to YAML
        config_yaml = yaml.dump(
            config, default_flow_style=False, sort_keys=False, allow_unicode=True
        )

        # Add comments for overrides
        lines = config_yaml.split("\n")
        commented_lines = []

        for line in lines:
            commented_lines.append(line)

            # Check if this line needs a comment
            for comment_info in comments:
                path_parts = comment_info["path"].split(".")
                if len(path_parts) == 2:
                    category, param = path_parts
                    if f"{param}:" in line and category in line:
                        commented_lines.append(f"  # {comment_info['comment']}")
                        break

        return "\n".join(commented_lines)

    def _create_backup(self) -> None:
        """Create backup of all configurations before migration."""
        logger.info(f"🔧 📦 Creating backup at {self.backup_dir}")

        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup teams
        teams_backup = self.backup_dir / "teams"
        if (self.base_path / "teams").exists():
            shutil.copytree(self.base_path / "teams", teams_backup)

        # Backup agents
        agents_backup = self.backup_dir / "agents"
        if (self.base_path / "agents").exists():
            shutil.copytree(self.base_path / "agents", agents_backup)

        # Save migration timestamp
        with open(self.backup_dir / "migration_info.yaml", "w") as f:
            yaml.dump(
                {
                    "migration_date": datetime.now().isoformat(),
                    "backup_source": str(self.base_path.absolute()),
                    "migration_type": "inheritance_model",
                },
                f,
            )

    def restore_from_backup(self, backup_path: str) -> None:
        """Restore configurations from backup."""
        backup_dir = Path(backup_path)

        if not backup_dir.exists():
            raise ValueError(f"Backup directory not found: {backup_path}")

        logger.warning(f"🔄 Restoring from backup: {backup_path}")

        # Restore teams
        teams_backup = backup_dir / "teams"
        if teams_backup.exists():
            if (self.base_path / "teams").exists():
                shutil.rmtree(self.base_path / "teams")
            shutil.copytree(teams_backup, self.base_path / "teams")

        # Restore agents
        agents_backup = backup_dir / "agents"
        if agents_backup.exists():
            if (self.base_path / "agents").exists():
                shutil.rmtree(self.base_path / "agents")
            shutil.copytree(agents_backup, self.base_path / "agents")

        logger.info("Restore completed")

    def generate_migration_report(self) -> str:
        """Generate detailed migration report."""
        report = [
            "🔄 AGNO Configuration Migration Report",
            "=" * 50,
            f"Migration Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Dry Run: {self.dry_run}",
            "",
        ]

        if self.migration_log:
            report.append("📋 Migration Details:")

            total_removed = 0
            total_preserved = 0

            for log_entry in self.migration_log:
                team_id = log_entry["team_id"]
                member_id = log_entry["member_id"]
                removed = len(log_entry["removed_params"])
                preserved = len(log_entry["preserved_overrides"])

                total_removed += removed
                total_preserved += preserved

                report.append("")
                report.append(f"  🤖 Agent: {member_id} (Team: {team_id})")

                if removed > 0:
                    report.append(f"    ✂️  Removed {removed} redundant parameters:")
                    for param in log_entry["removed_params"]:
                        report.append(f"       • {param}")

                if preserved > 0:
                    report.append(
                        f"    🔧 Preserved {preserved} intentional overrides:"
                    )
                    for param in log_entry["preserved_overrides"]:
                        report.append(f"       • {param}")

            report.extend(
                [
                    "",
                    "📊 Migration Summary:",
                    f"  • Teams processed: {len({log['team_id'] for log in self.migration_log})}",
                    f"  • Agents migrated: {len(self.migration_log)}",
                    f"  • Parameters removed: {total_removed}",
                    f"  • Overrides preserved: {total_preserved}",
                    f"  • Configuration reduction: {total_removed / (total_removed + total_preserved) * 100:.1f}%",
                ]
            )
        else:
            report.append("ℹ️  No migrations performed")

        return "\n".join(report)


# CLI interface for migration
def migrate_configurations(
    base_path: str = "ai", dry_run: bool = True, team_id: str | None = None
) -> dict[str, Any]:
    """Migrate AGNO configurations to inheritance model."""
    migrator = AGNOConfigMigrator(base_path, dry_run)

    if team_id:
        logger.info(f"🔄 Migrating specific team: {team_id}")
        result = migrator.migrate_team(team_id)
        result["teams_processed"] = 1
    else:
        logger.info("Migrating all teams")
        result = migrator.migrate_all_teams()

    # Generate and display report
    report = migrator.generate_migration_report()
    logger.info(f"🔧 {report}")

    if not dry_run and not result["errors"]:
        logger.info("Migration completed successfully!")
        logger.info("📦 Backup created for rollback if needed")
    elif result["errors"]:
        logger.error(f"❌ Migration completed with {len(result['errors'])} errors")

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AGNO Configuration Migrator")
    parser.add_argument("--path", default="ai", help="Base path to AI configurations")
    parser.add_argument("--team", help="Migrate specific team only")
    parser.add_argument(
        "--execute", action="store_true", help="Execute migration (default is dry run)"
    )
    parser.add_argument("--restore", help="Restore from backup directory")

    args = parser.parse_args()

    if args.restore:
        migrator = AGNOConfigMigrator(args.path, dry_run=False)
        migrator.restore_from_backup(args.restore)
    else:
        result = migrate_configurations(
            args.path, dry_run=not args.execute, team_id=args.team
        )
        sys.exit(0 if not result["errors"] else 1)
