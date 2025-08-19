"""
AGNO Configuration Validation Tools

Comprehensive validation suite for AGNO team and agent configurations.
Detects configuration drift, validates inheritance, and ensures compliance.
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from agno.utils.log import logger


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    suggestions: list[str]
    drift_detected: bool = False


class AGNOConfigValidator:
    """Comprehensive AGNO configuration validator."""

    def __init__(self, base_path: str = "ai"):
        self.base_path = Path(base_path)
        self.teams_path = self.base_path / "teams"
        self.agents_path = self.base_path / "agents"

    def validate_all_configurations(self) -> ValidationResult:
        """Validate all team and agent configurations in the project."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[], suggestions=[])

        # Validate all teams and their members
        for team_path in self.teams_path.glob("*/config.yaml"):
            team_id = team_path.parent.name
            team_result = self.validate_team_configuration(team_id)
            self._merge_results(result, team_result)

        # Validate standalone agents (not part of any team)
        standalone_agents = self._find_standalone_agents()
        for agent_id in standalone_agents:
            agent_result = self.validate_agent_configuration(agent_id)
            self._merge_results(result, agent_result)

        # Overall project validation
        project_result = self._validate_project_consistency()
        self._merge_results(result, project_result)

        return result

    def validate_team_configuration(self, team_id: str) -> ValidationResult:
        """Validate a specific team and all its members."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[], suggestions=[])

        team_config_path = self.teams_path / team_id / "config.yaml"

        if not team_config_path.exists():
            result.errors.append(f"Team config not found: {team_config_path}")
            result.is_valid = False
            return result

        try:
            with open(team_config_path) as f:
                team_config = yaml.safe_load(f)
        except Exception as e:
            result.errors.append(f"Failed to load team config {team_id}: {e}")
            result.is_valid = False
            return result

        # Validate team structure
        team_validation = self._validate_team_structure(team_id, team_config)
        self._merge_results(result, team_validation)

        # Validate all team members
        members = team_config.get("members") or []
        member_configs = {}

        for member_id in members:
            member_path = self.agents_path / member_id / "config.yaml"
            if member_path.exists():
                try:
                    with open(member_path) as f:
                        member_configs[member_id] = yaml.safe_load(f)
                except Exception as e:
                    result.errors.append(f"Failed to load member {member_id}: {e}")
                    result.is_valid = False
                    continue
            else:
                result.errors.append(f"Member agent config not found: {member_id}")
                result.is_valid = False

        # Validate inheritance compliance
        if member_configs:
            inheritance_result = self._validate_inheritance_compliance(
                team_id, team_config, member_configs
            )
            self._merge_results(result, inheritance_result)

        return result

    def validate_agent_configuration(self, agent_id: str) -> ValidationResult:
        """Validate a specific agent configuration."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[], suggestions=[])

        agent_config_path = self.agents_path / agent_id / "config.yaml"

        if not agent_config_path.exists():
            result.errors.append(f"Agent config not found: {agent_config_path}")
            result.is_valid = False
            return result

        try:
            with open(agent_config_path) as f:
                agent_config = yaml.safe_load(f)
        except Exception as e:
            result.errors.append(f"Failed to load agent config {agent_id}: {e}")
            result.is_valid = False
            return result

        # Validate agent structure
        agent_validation = self._validate_agent_structure(agent_id, agent_config)
        self._merge_results(result, agent_validation)

        return result

    def detect_configuration_drift(self) -> ValidationResult:
        """Detect configuration drift across teams and agents."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[], suggestions=[])

        # Collect all configurations
        all_configs = self._collect_all_configurations()

        # Check for drift in common parameters
        drift_checks = [
            ("memory.num_history_runs", "Memory history depth"),
            ("memory.enable_user_memories", "User memory tracking"),
            ("storage.type", "Storage backend"),
            ("storage.auto_upgrade_schema", "Schema auto-upgrade"),
            ("model.provider", "Model provider"),
            ("model.temperature", "Model temperature"),
        ]

        for param_path, description in drift_checks:
            drift_analysis = self._analyze_parameter_drift(
                all_configs, param_path, description
            )
            if drift_analysis["has_drift"]:
                result.drift_detected = True
                result.warnings.append(drift_analysis["message"])
                if drift_analysis["severity"] == "high":
                    result.errors.append(f"Critical drift in {description}")
                    result.is_valid = False

        return result

    def _validate_team_structure(
        self, team_id: str, config: dict[str, Any]
    ) -> ValidationResult:
        """Validate team configuration structure."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[], suggestions=[])

        # Required team fields
        required_fields = ["team.team_id", "team.name", "members"]
        for field in required_fields:
            if not self._has_nested_field(config, field):
                result.errors.append(
                    f"Team {team_id}: Missing required field '{field}'"
                )
                result.is_valid = False

        # Validate team members exist
        members = config.get("members") or []
        if not members:
            result.warnings.append(f"Team {team_id}: No members defined")

        for member_id in members:
            member_path = self.agents_path / member_id / "config.yaml"
            if not member_path.exists():
                result.errors.append(
                    f"Team {team_id}: Member '{member_id}' config not found"
                )
                result.is_valid = False

        # Validate version field
        version = config.get("team", {}).get("version")
        if not version:
            result.warnings.append(f"Team {team_id}: No version specified")
        elif version == "dev":
            result.suggestions.append(
                f"Team {team_id}: Consider versioning for production"
            )

        return result

    def _validate_agent_structure(
        self, agent_id: str, config: dict[str, Any]
    ) -> ValidationResult:
        """Validate agent configuration structure."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[], suggestions=[])

        # Required agent fields
        required_fields = ["agent.agent_id", "agent.name", "instructions"]
        for field in required_fields:
            if not self._has_nested_field(config, field):
                result.errors.append(
                    f"Agent {agent_id}: Missing required field '{field}'"
                )
                result.is_valid = False

        # Validate agent_id consistency
        config_agent_id = config.get("agent", {}).get("agent_id")
        if config_agent_id and config_agent_id != agent_id:
            result.warnings.append(
                f"Agent {agent_id}: config.agent.agent_id '{config_agent_id}' "
                f"doesn't match directory name"
            )

        # Validate storage table_name uniqueness
        table_name = config.get("storage", {}).get("table_name")
        if table_name:
            if not table_name.startswith("agents_"):
                result.warnings.append(
                    f"Agent {agent_id}: table_name should start with 'agents_'"
                )
            if not table_name.endswith(agent_id.replace("-", "_")):
                result.suggestions.append(
                    f"Agent {agent_id}: Consider table_name 'agents_{agent_id.replace('-', '_')}'"
                )

        return result

    def _validate_inheritance_compliance(
        self,
        team_id: str,
        team_config: dict[str, Any],
        member_configs: dict[str, dict[str, Any]],
    ) -> ValidationResult:
        """Validate inheritance compliance between team and members."""
        # Config inheritance system removed - skip validation
        result = ValidationResult(is_valid=True, errors=[], warnings=[], suggestions=[])
        return result

    def _validate_project_consistency(self) -> ValidationResult:
        """Validate project-wide consistency."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[], suggestions=[])

        # Check for orphaned agents
        all_team_members = set()
        for team_path in self.teams_path.glob("*/config.yaml"):
            try:
                with open(team_path) as f:
                    team_config = yaml.safe_load(f)
                members = team_config.get("members") or []
                all_team_members.update(members)
            except Exception:
                continue

        all_agents = {
            agent_path.parent.name
            for agent_path in self.agents_path.glob("*/config.yaml")
        }
        orphaned_agents = all_agents - all_team_members

        if orphaned_agents:
            result.suggestions.append(
                f"Orphaned agents (not in any team): {', '.join(sorted(orphaned_agents))}"
            )

        return result

    def _collect_all_configurations(self) -> dict[str, dict[str, Any]]:
        """Collect all team and agent configurations."""
        configs = {}

        # Collect team configs
        for team_path in self.teams_path.glob("*/config.yaml"):
            team_id = team_path.parent.name
            try:
                with open(team_path) as f:
                    configs[f"team:{team_id}"] = yaml.safe_load(f)
            except Exception:
                continue

        # Collect agent configs
        for agent_path in self.agents_path.glob("*/config.yaml"):
            agent_id = agent_path.parent.name
            try:
                with open(agent_path) as f:
                    configs[f"agent:{agent_id}"] = yaml.safe_load(f)
            except Exception:
                continue

        return configs

    def _analyze_parameter_drift(
        self, configs: dict[str, dict[str, Any]], param_path: str, description: str
    ) -> dict[str, Any]:
        """Analyze drift in a specific parameter across configurations."""
        values = {}

        for config_id, config in configs.items():
            value = self._get_nested_value(config, param_path)
            if value is not None:
                if value not in values:
                    values[value] = []
                values[value].append(config_id)

        if len(values) <= 1:
            return {"has_drift": False}

        # Determine severity
        severity = "low"
        if len(values) > 3:
            severity = "high"
        elif len(values) > 2:
            severity = "medium"

        # Create drift message
        drift_summary = []
        for value, configs_list in values.items():
            drift_summary.append(f"{value}: {len(configs_list)} configs")

        message = (
            f"Parameter drift in {description} ({param_path}): "
            f"{', '.join(drift_summary)}"
        )

        return {
            "has_drift": True,
            "severity": severity,
            "message": message,
            "values": values,
        }

    def _find_standalone_agents(self) -> list[str]:
        """Find agents that are not part of any team."""
        all_team_members = set()

        for team_path in self.teams_path.glob("*/config.yaml"):
            try:
                with open(team_path) as f:
                    team_config = yaml.safe_load(f)
                members = team_config.get("members") or []
                all_team_members.update(members)
            except Exception:
                continue

        all_agents = {
            agent_path.parent.name
            for agent_path in self.agents_path.glob("*/config.yaml")
        }

        return list(all_agents - all_team_members)

    def _has_nested_field(self, config: dict[str, Any], field_path: str) -> bool:
        """Check if nested field exists in configuration."""
        return self._get_nested_value(config, field_path) is not None

    def _get_nested_value(self, config: dict[str, Any], path: str) -> Any:
        """Get nested value from configuration using dot notation."""
        keys = path.split(".")
        value = config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return None

    def _merge_results(
        self, target: ValidationResult, source: ValidationResult
    ) -> None:
        """Merge validation results."""
        target.errors.extend(source.errors)
        target.warnings.extend(source.warnings)
        target.suggestions.extend(source.suggestions)

        if not source.is_valid:
            target.is_valid = False

        if source.drift_detected:
            target.drift_detected = True


# CLI interface for validation
def validate_configurations(
    base_path: str = "ai", verbose: bool = False
) -> ValidationResult:
    """Validate all AGNO configurations in the project."""
    validator = AGNOConfigValidator(base_path)

    logger.info("Starting AGNO configuration validation...")

    result = validator.validate_all_configurations()

    # Print results
    if result.errors:
        logger.error(f"❌ Validation failed with {len(result.errors)} errors:")
        for error in result.errors:
            logger.error(f"🚨    • {error}")

    if result.warnings:
        logger.warning(f"⚠️  {len(result.warnings)} warnings found:")
        for warning in result.warnings:
            logger.warning(f"⚠️    • {warning}")

    if result.suggestions and verbose:
        logger.info(f"🔧 {len(result.suggestions)} suggestions:")
        for suggestion in result.suggestions:
            logger.info(f"🔧    • {suggestion}")

    if result.drift_detected:
        logger.warning("Configuration drift detected - consider standardization")

    if result.is_valid and not result.warnings:
        logger.info("All configurations valid!")
    elif result.is_valid:
        logger.info("Configurations valid with warnings")

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AGNO Configuration Validator")
    parser.add_argument("--path", default="ai", help="Base path to AI configurations")
    parser.add_argument("--verbose", action="store_true", help="Show suggestions")
    parser.add_argument("--drift-only", action="store_true", help="Check drift only")

    args = parser.parse_args()

    if args.drift_only:
        validator = AGNOConfigValidator(args.path)
        result = validator.detect_configuration_drift()
    else:
        result = validate_configurations(args.path, args.verbose)

    sys.exit(0 if result.is_valid else 1)
