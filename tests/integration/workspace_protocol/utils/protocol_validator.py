"""
Protocol Validation Utility for Workspace Protocol Testing

Provides validation utilities for ensuring agents comply with
standardized workspace interaction protocols.
"""

import json
import os
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationResult:
    """Result of a protocol validation check."""

    passed: bool
    message: str
    details: dict[str, Any] | None = None


class ProtocolValidator:
    """Utility class for validating workspace protocol compliance."""

    def __init__(self):
        """Initialize protocol validator with default configuration."""
        self.required_json_fields = ["status", "context_validated"]
        self.valid_statuses = ["success", "error", "in_progress"]
        self.valid_directories = ["/genie/ideas/", "/genie/wishes/"]

    def extract_json_response(self, response: str) -> dict[str, Any] | None:
        """
        Extract JSON response object from agent response text.

        Args:
            response: Raw agent response text

        Returns:
            Parsed JSON object or None if no valid JSON found
        """
        if not response:
            return None

        # Try to find JSON object in response
        json_patterns = [
            # Look for complete JSON objects
            r'\{[^{}]*"status"[^{}]*\}',
            r'\{.*?"status".*?\}',
            # Look for JSON blocks in code fences
            r"```json\s*(\{.*?\})\s*```",
            r'```\s*(\{.*?"status".*?\})\s*```',
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    # If pattern captured group, use that; otherwise use full match
                    json_text = (
                        match
                        if isinstance(match, str) and match.startswith("{")
                        else match
                    )
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    continue

        # Try parsing the entire response as JSON
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass

        return None

    def validate_json_response_format(
        self, json_data: dict[str, Any]
    ) -> ValidationResult:
        """
        Validate that JSON response follows required format.

        Args:
            json_data: Parsed JSON response object

        Returns:
            ValidationResult indicating compliance
        """
        if not json_data:
            return ValidationResult(False, "No JSON response found")

        # Check required fields
        missing_fields = []
        for field in self.required_json_fields:
            if field not in json_data:
                missing_fields.append(field)

        if missing_fields:
            return ValidationResult(
                False,
                f"Missing required fields: {', '.join(missing_fields)}",
                {"missing_fields": missing_fields},
            )

        # Validate status field
        status = json_data.get("status")
        if status not in self.valid_statuses:
            return ValidationResult(
                False,
                f"Invalid status '{status}', must be one of: {', '.join(self.valid_statuses)}",
                {"invalid_status": status, "valid_statuses": self.valid_statuses},
            )

        # Validate context_validated field
        context_validated = json_data.get("context_validated")
        if not isinstance(context_validated, bool):
            return ValidationResult(
                False,
                f"context_validated must be boolean, got {type(context_validated).__name__}",
                {"context_validated_type": type(context_validated).__name__},
            )

        # Additional format checks based on status
        if status == "error" and "message" not in json_data:
            return ValidationResult(
                False, "Error status requires 'message' field", {"status": status}
            )

        if status in ["success", "in_progress"] and "artifacts" in json_data:
            artifacts = json_data["artifacts"]
            if not isinstance(artifacts, list):
                return ValidationResult(
                    False,
                    "artifacts field must be a list",
                    {"artifacts_type": type(artifacts).__name__},
                )

        return ValidationResult(True, "JSON response format is valid")

    def validate_artifact_paths(self, artifacts: list[str]) -> ValidationResult:
        """
        Validate that artifact paths follow workspace protocol requirements.

        Args:
            artifacts: List of artifact file paths

        Returns:
            ValidationResult indicating path compliance
        """
        if not artifacts:
            return ValidationResult(True, "No artifacts to validate")

        invalid_paths = []
        relative_paths = []
        wrong_directory_paths = []

        for artifact_path in artifacts:
            # Check if path is absolute
            if not os.path.isabs(artifact_path):
                relative_paths.append(artifact_path)
                continue

            # Check if path is in valid directory
            is_valid_directory = any(
                valid_dir in artifact_path for valid_dir in self.valid_directories
            )
            if "/genie/" in artifact_path and not is_valid_directory:
                wrong_directory_paths.append(artifact_path)

            # Check if file extension is appropriate
            if "/genie/" in artifact_path and not artifact_path.endswith(".md"):
                invalid_paths.append(artifact_path)

        errors = []
        details = {}

        if relative_paths:
            errors.append(f"Relative paths not allowed: {', '.join(relative_paths)}")
            details["relative_paths"] = relative_paths

        if wrong_directory_paths:
            errors.append(f"Invalid directories: {', '.join(wrong_directory_paths)}")
            details["wrong_directory_paths"] = wrong_directory_paths

        if invalid_paths:
            errors.append(f"Invalid extensions: {', '.join(invalid_paths)}")
            details["invalid_paths"] = invalid_paths

        if errors:
            return ValidationResult(False, "; ".join(errors), details)

        return ValidationResult(True, "All artifact paths are valid")

    def validate_context_ingestion_compliance(
        self, task_prompt: str, json_response: dict[str, Any]
    ) -> ValidationResult:
        """
        Validate that agent properly handled context file ingestion.

        Args:
            task_prompt: Original task prompt with context references
            json_response: Agent's JSON response

        Returns:
            ValidationResult indicating context ingestion compliance
        """
        # Extract context file references from prompt
        context_files = self._extract_context_files_from_prompt(task_prompt)

        if not context_files:
            # No context files in prompt, context_validated should still be present
            context_validated = json_response.get("context_validated")
            if context_validated is None:
                return ValidationResult(
                    False,
                    "context_validated field missing when no context files present",
                )
            return ValidationResult(True, "No context files to validate")

        # Check if any context files are missing
        missing_files = [f for f in context_files if not os.path.exists(f)]

        context_validated = json_response.get("context_validated")
        status = json_response.get("status")

        if missing_files:
            # If files are missing, agent should report error
            if context_validated is not False:
                return ValidationResult(
                    False,
                    "context_validated should be False when context files are missing",
                    {"missing_files": missing_files},
                )

            if status != "error":
                return ValidationResult(
                    False,
                    "status should be 'error' when context files are missing",
                    {"missing_files": missing_files, "status": status},
                )

        # If files exist, agent should validate successfully (unless other errors)
        elif context_validated is not True and status != "error":
            return ValidationResult(
                False,
                "context_validated should be True when context files are accessible",
                {"context_files": context_files},
            )

        return ValidationResult(True, "Context ingestion compliance is valid")

    def validate_artifact_lifecycle_compliance(
        self, json_response: dict[str, Any], expected_phase: str | None = None
    ) -> ValidationResult:
        """
        Validate that artifacts are created in appropriate lifecycle directories.

        Args:
            json_response: Agent's JSON response
            expected_phase: Expected lifecycle phase ('ideas', 'wishes', 'completion')

        Returns:
            ValidationResult indicating lifecycle compliance
        """
        artifacts = json_response.get("artifacts", [])
        status = json_response.get("status")

        if status == "success" and expected_phase == "completion":
            # Completion phase should not have artifacts (should be deleted)
            if artifacts:
                return ValidationResult(
                    False,
                    "Completion phase should not have artifacts (should be deleted)",
                    {"artifacts": artifacts},
                )
            return ValidationResult(True, "Completion phase compliance validated")

        if not artifacts:
            # No artifacts is okay for some agents/tasks
            return ValidationResult(True, "No artifacts to validate")

        # Check artifact directory placement
        ideas_artifacts = [a for a in artifacts if "/genie/ideas/" in a]
        wishes_artifacts = [a for a in artifacts if "/genie/wishes/" in a]

        if expected_phase == "ideas":
            if not ideas_artifacts and wishes_artifacts:
                return ValidationResult(
                    False,
                    "Ideas phase should create artifacts in /genie/ideas/, not /genie/wishes/",
                    {
                        "ideas_artifacts": ideas_artifacts,
                        "wishes_artifacts": wishes_artifacts,
                    },
                )

        elif expected_phase == "wishes":
            if status == "success" and not wishes_artifacts and ideas_artifacts:
                return ValidationResult(
                    False,
                    "Wishes phase with success status should create artifacts in /genie/wishes/",
                    {
                        "ideas_artifacts": ideas_artifacts,
                        "wishes_artifacts": wishes_artifacts,
                    },
                )

        return ValidationResult(True, "Artifact lifecycle compliance is valid")

    def validate_technical_standards_compliance(
        self, response_text: str
    ) -> ValidationResult:
        """
        Validate that agent enforces technical standards in recommendations.

        Args:
            response_text: Full agent response text

        Returns:
            ValidationResult indicating technical standards compliance
        """
        violations = []

        # Check for pip usage (should use uv instead)
        if re.search(r"\bpip\s+install\b", response_text, re.IGNORECASE):
            violations.append(
                "Found 'pip install' recommendation, should use 'uv add' instead"
            )

        # Check for direct python usage (should use 'uv run python')
        if re.search(r"\bpython\s+[^\s]", response_text) and not re.search(
            r"uv run python", response_text
        ):
            violations.append(
                "Found direct 'python' usage, should use 'uv run python' instead"
            )

        # Check for relative paths in file operations
        relative_path_patterns = [
            r'["\']\.\/[^"\']*["\']',  # "./path"
            r'["\'][^"\'\/][^"\']*\.py["\']',  # "script.py"
        ]

        for pattern in relative_path_patterns:
            if re.search(pattern, response_text):
                violations.append("Found relative paths, should use absolute paths")
                break

        if violations:
            return ValidationResult(
                False,
                f"Technical standards violations: {'; '.join(violations)}",
                {"violations": violations},
            )

        return ValidationResult(True, "Technical standards compliance is valid")

    def validate_response_conciseness(
        self, response_text: str, max_length: int = 2000
    ) -> ValidationResult:
        """
        Validate that response text is concise (large content should be in artifacts).

        Args:
            response_text: Full agent response text
            max_length: Maximum allowed response length

        Returns:
            ValidationResult indicating conciseness compliance
        """
        if len(response_text) > max_length:
            return ValidationResult(
                False,
                f"Response too long ({len(response_text)} chars), large content should be in artifacts",
                {"response_length": len(response_text), "max_length": max_length},
            )

        return ValidationResult(True, "Response conciseness is appropriate")

    def run_comprehensive_validation(
        self, task_prompt: str, agent_response: str, expected_phase: str | None = None
    ) -> dict[str, ValidationResult]:
        """
        Run comprehensive validation on agent response.

        Args:
            task_prompt: Original task prompt
            agent_response: Agent's response text
            expected_phase: Expected lifecycle phase for artifact validation

        Returns:
            Dictionary of validation results by category
        """
        results = {}

        # Extract JSON response
        json_data = self.extract_json_response(agent_response)

        # JSON format validation
        results["json_format"] = self.validate_json_response_format(json_data)

        if json_data:
            # Context ingestion validation
            results["context_ingestion"] = self.validate_context_ingestion_compliance(
                task_prompt, json_data
            )

            # Artifact path validation
            artifacts = json_data.get("artifacts", [])
            results["artifact_paths"] = self.validate_artifact_paths(artifacts)

            # Artifact lifecycle validation
            results["artifact_lifecycle"] = self.validate_artifact_lifecycle_compliance(
                json_data, expected_phase
            )

        # Technical standards validation
        results["technical_standards"] = self.validate_technical_standards_compliance(
            agent_response
        )

        # Response conciseness validation
        results["response_conciseness"] = self.validate_response_conciseness(
            agent_response
        )

        return results

    def calculate_compliance_score(
        self, validation_results: dict[str, ValidationResult]
    ) -> float:
        """
        Calculate overall compliance score from validation results.

        Args:
            validation_results: Dictionary of validation results

        Returns:
            Compliance score between 0.0 and 1.0
        """
        if not validation_results:
            return 0.0

        passed_checks = sum(
            1 for result in validation_results.values() if result.passed
        )
        total_checks = len(validation_results)

        return passed_checks / total_checks

    def generate_validation_report(
        self,
        validation_results: dict[str, ValidationResult],
        agent_name: str | None = None,
    ) -> str:
        """
        Generate human-readable validation report.

        Args:
            validation_results: Dictionary of validation results
            agent_name: Name of agent being validated

        Returns:
            Formatted validation report
        """
        compliance_score = self.calculate_compliance_score(validation_results)

        report = f"""
WORKSPACE PROTOCOL VALIDATION REPORT
{"=" * 50}
"""

        if agent_name:
            report += f"Agent: {agent_name}\n"

        report += f"Overall Compliance: {compliance_score:.1%}\n\n"

        for category, result in validation_results.items():
            status = "✓ PASS" if result.passed else "❌ FAIL"
            report += f"{category.replace('_', ' ').title():20} {status:10} {result.message}\n"

            if not result.passed and result.details:
                for key, value in result.details.items():
                    report += f"    {key}: {value}\n"

        return report

    def _extract_context_files_from_prompt(self, task_prompt: str) -> list[str]:
        """Extract context file paths from task prompt."""
        context_files = []

        for line in task_prompt.split("\n"):
            line = line.strip()
            if line.startswith("Context: @"):
                context_path = line[len("Context: @") :]
                context_files.append(context_path)

        return context_files
