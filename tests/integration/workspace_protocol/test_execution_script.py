"""
Workspace Protocol Validation Test Execution Script

Comprehensive test execution orchestrator that validates all 15 agents
against the standardized workspace protocol requirements.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add the test utilities to path
sys.path.append(str(Path(__file__).parent))

from utils.agent_tester import AgentTester
from utils.protocol_validator import ProtocolValidator


class WorkspaceProtocolTestExecutor:
    """Orchestrates comprehensive workspace protocol validation testing."""

    def __init__(self):
        """Initialize test execution framework."""
        self.agent_tester = AgentTester()
        self.protocol_validator = ProtocolValidator()
        self.target_agents = [
            "genie-dev-planner",
            "genie-dev-designer",
            "genie-dev-coder",
            "genie-dev-fixer",
            "genie-testing-maker",
            "genie-testing-fixer",
            "genie-quality-ruff",
            "genie-quality-mypy",
            "genie-clone",
            "genie-self-learn",
            "genie-qa-tester",
            "genie-claudemd",
            "genie-agent-creator",
            "genie-agent-enhancer",
            "claude",
        ]

    def run_full_validation_suite(self) -> dict[str, Any]:
        """
        Execute complete validation suite across all agents.

        Returns:
            Comprehensive test results and compliance report
        """

        start_time = datetime.now()

        # Phase 1: Static compliance check
        static_results = self.run_static_compliance_check()

        # Phase 2: Functional validation tests
        functional_results = self.run_functional_validation_tests()

        # Phase 3: Integration testing
        integration_results = self.run_integration_tests()

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        # Compile comprehensive results
        comprehensive_results = {
            "timestamp": start_time.isoformat(),
            "execution_time_seconds": execution_time,
            "static_compliance": static_results,
            "functional_validation": functional_results,
            "integration_tests": integration_results,
            "summary": self.generate_summary_metrics(
                static_results, functional_results, integration_results
            ),
        }

        # Generate and display final report
        self.display_final_report(comprehensive_results)

        return comprehensive_results

    def run_static_compliance_check(self) -> dict[str, Any]:
        """Run static analysis of agent configurations for protocol compliance."""

        results = {}

        for agent_name in self.target_agents:
            compliance_result = self.agent_tester.validate_agent_protocol_compliance(
                agent_name
            )
            results[agent_name] = compliance_result

            "✓" if compliance_result["compliant"] else "❌"
            compliance_result.get("compliance_score", 0)

        # Calculate overall static compliance
        total_agents = len(results)
        compliant_agents = sum(1 for r in results.values() if r["compliant"])
        overall_compliance = compliant_agents / total_agents if total_agents > 0 else 0

        return {
            "overall_compliance": overall_compliance,
            "total_agents": total_agents,
            "compliant_agents": compliant_agents,
            "agent_results": results,
        }

    def run_functional_validation_tests(self) -> dict[str, Any]:
        """Run functional tests to validate protocol behavior."""

        test_scenarios = [
            {
                "name": "valid_context_processing",
                "description": "Test processing of valid context files",
                "test_func": self._test_valid_context_processing,
            },
            {
                "name": "missing_context_error_handling",
                "description": "Test error handling for missing context files",
                "test_func": self._test_missing_context_error_handling,
            },
            {
                "name": "artifact_lifecycle_management",
                "description": "Test artifact creation and lifecycle management",
                "test_func": self._test_artifact_lifecycle_management,
            },
            {
                "name": "json_response_format_compliance",
                "description": "Test JSON response format adherence",
                "test_func": self._test_json_response_format_compliance,
            },
            {
                "name": "technical_standards_enforcement",
                "description": "Test technical standards enforcement",
                "test_func": self._test_technical_standards_enforcement,
            },
        ]

        results = {}

        for scenario in test_scenarios:
            scenario_results = scenario["test_func"]()
            results[scenario["name"]] = {
                "description": scenario["description"],
                "results": scenario_results,
                "pass_rate": self._calculate_scenario_pass_rate(scenario_results),
            }

            results[scenario["name"]]["pass_rate"]

        return results

    def run_integration_tests(self) -> dict[str, Any]:
        """Run integration tests for cross-agent protocol consistency."""

        integration_scenarios = [
            {
                "name": "protocol_consistency_across_agents",
                "description": "Validate protocol consistency across all agents",
                "test_func": self._test_protocol_consistency,
            },
            {
                "name": "error_propagation_handling",
                "description": "Test error handling propagation across agent boundaries",
                "test_func": self._test_error_propagation,
            },
            {
                "name": "artifact_coordination",
                "description": "Test artifact coordination between agents",
                "test_func": self._test_artifact_coordination,
            },
        ]

        results = {}

        for scenario in integration_scenarios:
            scenario_results = scenario["test_func"]()
            results[scenario["name"]] = {
                "description": scenario["description"],
                "results": scenario_results,
                "pass_rate": self._calculate_scenario_pass_rate(scenario_results),
            }

            results[scenario["name"]]["pass_rate"]

        return results

    def _test_valid_context_processing(self) -> dict[str, Any]:
        """Test that agents properly process valid context files."""

        # Create temporary valid context file
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("""# Test Context File

## Requirements
- Feature A implementation
- Feature B integration
- Quality validation

## Success Criteria
- All tests pass
- Code coverage >85%
""")
            context_file = f.name

        results = {}

        try:
            # Test subset of agents for performance
            test_agents = [
                "genie-dev-planner",
                "genie-dev-designer",
                "genie-testing-maker",
            ]

            for agent_name in test_agents:
                task_prompt = f"""
Context: @{context_file}

Create a technical plan based on the context file requirements.
"""

                response = self.agent_tester.execute_agent_task(agent_name, task_prompt)
                validation_results = (
                    self.protocol_validator.run_comprehensive_validation(
                        task_prompt, response or ""
                    )
                )

                results[agent_name] = {
                    "response_received": response is not None,
                    "validation_results": validation_results,
                    "compliance_score": self.protocol_validator.calculate_compliance_score(
                        validation_results
                    ),
                }

        finally:
            if os.path.exists(context_file):
                os.unlink(context_file)

        return results

    def _test_missing_context_error_handling(self) -> dict[str, Any]:
        """Test that agents properly handle missing context files."""

        results = {}
        invalid_context = "/nonexistent/path/invalid_context.md"

        # Test subset of agents
        test_agents = ["genie-dev-planner", "genie-dev-designer", "genie-testing-maker"]

        for agent_name in test_agents:
            task_prompt = f"""
Context: @{invalid_context}

Create a technical plan based on the context file requirements.
"""

            response = self.agent_tester.execute_agent_task(agent_name, task_prompt)
            validation_results = self.protocol_validator.run_comprehensive_validation(
                task_prompt, response or ""
            )

            # Extract JSON to check error handling specifically
            json_data = self.protocol_validator.extract_json_response(response or "")

            results[agent_name] = {
                "response_received": response is not None,
                "json_extracted": json_data is not None,
                "error_status_correct": json_data.get("status") == "error"
                if json_data
                else False,
                "context_validated_false": json_data.get("context_validated") is False
                if json_data
                else False,
                "validation_results": validation_results,
                "compliance_score": self.protocol_validator.calculate_compliance_score(
                    validation_results
                ),
            }

        return results

    def _test_artifact_lifecycle_management(self) -> dict[str, Any]:
        """Test artifact lifecycle management across phases."""

        results = {}

        # Test with agents that create artifacts
        test_agents = ["genie-dev-planner", "genie-dev-designer"]

        for agent_name in test_agents:
            # Test ideas phase
            ideas_prompt = """
Brainstorm approaches for implementing a user notification system.
Consider different notification channels and delivery mechanisms.
This is initial exploration.
"""

            ideas_response = self.agent_tester.execute_agent_task(
                agent_name, ideas_prompt
            )
            ideas_validation = self.protocol_validator.run_comprehensive_validation(
                ideas_prompt, ideas_response or "", expected_phase="ideas"
            )

            # Test wishes phase
            wishes_prompt = """
Create a detailed implementation plan for the user notification system.
This should be execution-ready with specific requirements.
"""

            wishes_response = self.agent_tester.execute_agent_task(
                agent_name, wishes_prompt
            )
            wishes_validation = self.protocol_validator.run_comprehensive_validation(
                wishes_prompt, wishes_response or "", expected_phase="wishes"
            )

            results[agent_name] = {
                "ideas_phase": {
                    "response_received": ideas_response is not None,
                    "validation_results": ideas_validation,
                    "compliance_score": self.protocol_validator.calculate_compliance_score(
                        ideas_validation
                    ),
                },
                "wishes_phase": {
                    "response_received": wishes_response is not None,
                    "validation_results": wishes_validation,
                    "compliance_score": self.protocol_validator.calculate_compliance_score(
                        wishes_validation
                    ),
                },
            }

        return results

    def _test_json_response_format_compliance(self) -> dict[str, Any]:
        """Test JSON response format compliance across agents."""

        results = {}

        # Test all agents with simple task
        for agent_name in self.target_agents[:5]:  # Test subset for performance
            task_prompt = """
Create a simple technical analysis of implementing a REST API endpoint
for user profile management. This is a straightforward task.
"""

            response = self.agent_tester.execute_agent_task(agent_name, task_prompt)
            json_data = self.protocol_validator.extract_json_response(response or "")
            json_validation = self.protocol_validator.validate_json_response_format(
                json_data
            )

            results[agent_name] = {
                "response_received": response is not None,
                "json_extracted": json_data is not None,
                "json_valid": json_validation.passed,
                "json_details": json_data,
                "validation_message": json_validation.message,
            }

        return results

    def _test_technical_standards_enforcement(self) -> dict[str, Any]:
        """Test technical standards enforcement in agent responses."""

        results = {}

        # Test agents that might provide technical recommendations
        test_agents = ["genie-dev-planner", "genie-dev-coder", "genie-quality-ruff"]

        for agent_name in test_agents:
            task_prompt = """
Create recommendations for setting up a Python development environment
including package management, code formatting, and testing frameworks.
"""

            response = self.agent_tester.execute_agent_task(agent_name, task_prompt)
            standards_validation = (
                self.protocol_validator.validate_technical_standards_compliance(
                    response or ""
                )
            )

            results[agent_name] = {
                "response_received": response is not None,
                "standards_compliant": standards_validation.passed,
                "validation_message": standards_validation.message,
                "violations": standards_validation.details.get("violations", [])
                if standards_validation.details
                else [],
            }

        return results

    def _test_protocol_consistency(self) -> dict[str, Any]:
        """Test protocol consistency across agents."""

        # This tests that all agents implement the protocol the same way
        all_agent_configs = {}

        for agent_name in self.target_agents:
            compliance_result = self.agent_tester.validate_agent_protocol_compliance(
                agent_name
            )
            all_agent_configs[agent_name] = compliance_result

        # Analyze consistency
        protocol_features = [
            "has_workspace_protocol",
            "has_json_response_format",
            "has_context_validation",
            "has_artifact_lifecycle",
        ]

        consistency_results = {}

        for feature in protocol_features:
            agents_with_feature = []
            agents_without_feature = []

            for agent_name, config in all_agent_configs.items():
                if config.get("checks", {}).get(feature, False):
                    agents_with_feature.append(agent_name)
                else:
                    agents_without_feature.append(agent_name)

            consistency_rate = len(agents_with_feature) / len(self.target_agents)

            consistency_results[feature] = {
                "consistency_rate": consistency_rate,
                "agents_with_feature": agents_with_feature,
                "agents_without_feature": agents_without_feature,
            }

        return consistency_results

    def _test_error_propagation(self) -> dict[str, Any]:
        """Test error handling propagation."""

        # Test that errors are handled consistently across agents
        results = {}

        test_agents = ["genie-dev-planner", "genie-dev-designer", "genie-testing-maker"]

        for agent_name in test_agents:
            # Test with invalid context file
            error_prompt = """
Context: @/definitely/invalid/path/error.md

This should trigger consistent error handling across all agents.
"""

            response = self.agent_tester.execute_agent_task(agent_name, error_prompt)
            json_data = self.protocol_validator.extract_json_response(response or "")

            results[agent_name] = {
                "response_received": response is not None,
                "json_extracted": json_data is not None,
                "error_status": json_data.get("status") == "error"
                if json_data
                else False,
                "context_validated_false": json_data.get("context_validated") is False
                if json_data
                else False,
                "has_error_message": bool(json_data.get("message"))
                if json_data
                else False,
            }

        return results

    def _test_artifact_coordination(self) -> dict[str, Any]:
        """Test artifact coordination between agents."""

        # This would test multi-agent workflows, simplified for now
        return {
            "coordination_test": "Not implemented - requires multi-agent workflow testing",
            "status": "skipped",
        }

    def _calculate_scenario_pass_rate(self, scenario_results: dict[str, Any]) -> float:
        """Calculate pass rate for a test scenario."""

        if not scenario_results:
            return 0.0

        total_tests = 0
        passed_tests = 0

        for agent_result in scenario_results.values():
            if isinstance(agent_result, dict):
                if "compliance_score" in agent_result:
                    total_tests += 1
                    if agent_result["compliance_score"] >= 0.8:  # 80% threshold
                        passed_tests += 1
                elif "error_status_correct" in agent_result:  # Error handling test
                    total_tests += 1
                    if (
                        agent_result["error_status_correct"]
                        and agent_result["context_validated_false"]
                    ):
                        passed_tests += 1
                elif "standards_compliant" in agent_result:  # Standards test
                    total_tests += 1
                    if agent_result["standards_compliant"]:
                        passed_tests += 1

        return passed_tests / total_tests if total_tests > 0 else 0.0

    def generate_summary_metrics(
        self,
        static_results: dict[str, Any],
        functional_results: dict[str, Any],
        integration_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate comprehensive summary metrics."""

        # Static compliance metrics
        static_compliance = static_results.get("overall_compliance", 0.0)

        # Functional test metrics
        functional_pass_rates = []
        for scenario_data in functional_results.values():
            functional_pass_rates.append(scenario_data.get("pass_rate", 0.0))

        avg_functional_pass_rate = (
            sum(functional_pass_rates) / len(functional_pass_rates)
            if functional_pass_rates
            else 0.0
        )

        # Integration test metrics
        integration_pass_rates = []
        for scenario_data in integration_results.values():
            integration_pass_rates.append(scenario_data.get("pass_rate", 0.0))

        avg_integration_pass_rate = (
            sum(integration_pass_rates) / len(integration_pass_rates)
            if integration_pass_rates
            else 0.0
        )

        # Overall compliance calculation
        overall_compliance = (
            static_compliance + avg_functional_pass_rate + avg_integration_pass_rate
        ) / 3

        # Determine compliance level
        if overall_compliance >= 0.95:
            compliance_level = "LEVEL 5 - FULL COMPLIANCE"
        elif overall_compliance >= 0.85:
            compliance_level = "LEVEL 4 - OPERATIONAL"
        elif overall_compliance >= 0.70:
            compliance_level = "LEVEL 3 - FUNCTIONAL"
        elif overall_compliance >= 0.50:
            compliance_level = "LEVEL 2 - PARTIAL"
        else:
            compliance_level = "LEVEL 1 - FAILING"

        return {
            "overall_compliance": overall_compliance,
            "compliance_level": compliance_level,
            "static_compliance": static_compliance,
            "functional_pass_rate": avg_functional_pass_rate,
            "integration_pass_rate": avg_integration_pass_rate,
            "total_agents_tested": len(self.target_agents),
            "test_categories_completed": len(functional_results)
            + len(integration_results),
        }

    def display_final_report(self, comprehensive_results: dict[str, Any]):
        """Display comprehensive final validation report."""

        summary = comprehensive_results["summary"]

        # Display recommendations based on compliance level
        if summary["overall_compliance"] < 0.70 or summary["overall_compliance"] < 0.85:
            pass
        else:
            pass


def main():
    """Main execution function for running workspace protocol validation."""

    executor = WorkspaceProtocolTestExecutor()
    results = executor.run_full_validation_suite()

    # Save results to file
    results_file = Path(
        "/home/namastex/workspace/automagik-hive/genie/wishes/workspace-protocol-validation-results.json"
    )
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    return results


if __name__ == "__main__":
    main()
