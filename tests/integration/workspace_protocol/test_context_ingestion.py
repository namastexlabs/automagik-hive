"""
Workspace Protocol Validation: Context File Ingestion Tests

Tests that all agents properly implement context file ingestion protocol
according to the standardized workspace interaction requirements.
"""

import os
import tempfile

import pytest

from tests.integration.workspace_protocol.utils.agent_tester import AgentTester
from tests.integration.workspace_protocol.utils.protocol_validator import ProtocolValidator


class TestContextIngestion:
    """Test suite for context file ingestion protocol compliance."""

    @pytest.fixture
    def agent_tester(self):
        """Initialize agent testing utility."""
        return AgentTester()

    @pytest.fixture
    def protocol_validator(self):
        """Initialize protocol validation utility."""
        return ProtocolValidator()

    @pytest.fixture
    def valid_context_file(self):
        """Create a valid temporary context file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("""# Test Context File

This is a valid context file for workspace protocol testing.

## Requirements
- Feature A implementation
- Feature B integration
- Quality validation

## Success Criteria
- All tests pass
- Code coverage >85%
- Performance benchmarks met
""")
            yield f.name
        os.unlink(f.name)

    @pytest.fixture
    def invalid_context_path(self):
        """Return path to non-existent context file."""
        return "/nonexistent/path/invalid_context.md"

    @pytest.fixture
    def multiple_context_files(self):
        """Create multiple temporary context files for testing."""
        files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=f"_context_{i}.md", delete=False
            ) as f:
                f.write(f"""# Context File {i + 1}

Content for context file number {i + 1}.
This tests multiple context file handling.

## Section {i + 1}
- Requirement {i + 1}A
- Requirement {i + 1}B
""")
                files.append(f.name)

        yield files

        for file_path in files:
            if os.path.exists(file_path):
                os.unlink(file_path)

    @pytest.mark.parametrize(
        "agent_name",
        [
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
        ],
    )
    def test_valid_context_file_processing(
        self, agent_tester, protocol_validator, valid_context_file, agent_name
    ):
        """Test agent processes valid context file correctly."""

        # Arrange
        context_reference = f"Context: @{valid_context_file}"
        task_prompt = f"""
{context_reference}

Create a technical plan based on the context file requirements.
"""

        # Act
        response = agent_tester.execute_agent_task(agent_name, task_prompt)

        # Assert
        assert response is not None, f"Agent {agent_name} returned no response"

        # Validate JSON response format
        json_data = protocol_validator.extract_json_response(response)
        assert json_data is not None, (
            f"Agent {agent_name} did not return valid JSON response"
        )

        # Validate context validation flag
        assert json_data.get("context_validated") is True, (
            f"Agent {agent_name} did not validate context correctly"
        )

        # Validate status is success or in_progress (not error)
        assert json_data.get("status") in ["success", "in_progress"], (
            f"Agent {agent_name} reported error status for valid context file"
        )

    @pytest.mark.parametrize(
        "agent_name",
        [
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
        ],
    )
    def test_missing_context_file_error_handling(
        self, agent_tester, protocol_validator, invalid_context_path, agent_name
    ):
        """Test agent properly handles missing context file with error response."""

        # Arrange
        context_reference = f"Context: @{invalid_context_path}"
        task_prompt = f"""
{context_reference}

Create a technical plan based on the context file requirements.
"""

        # Act
        response = agent_tester.execute_agent_task(agent_name, task_prompt)

        # Assert
        assert response is not None, f"Agent {agent_name} returned no response"

        # Validate JSON response format
        json_data = protocol_validator.extract_json_response(response)
        assert json_data is not None, (
            f"Agent {agent_name} did not return valid JSON response"
        )

        # Validate error status
        assert json_data.get("status") == "error", (
            f"Agent {agent_name} did not report error status for missing context file"
        )

        # Validate context validation flag is false
        assert json_data.get("context_validated") is False, (
            f"Agent {agent_name} incorrectly validated missing context file"
        )

        # Validate error message exists
        assert "message" in json_data, (
            f"Agent {agent_name} did not provide error message"
        )

        # Validate error message mentions context file issue
        error_message = json_data.get("message", "").lower()
        assert any(
            keyword in error_message for keyword in ["context", "file", "access"]
        ), f"Agent {agent_name} error message does not mention context file issue"

    @pytest.mark.parametrize(
        "agent_name",
        [
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
        ],
    )
    def test_multiple_context_file_management(
        self, agent_tester, protocol_validator, multiple_context_files, agent_name
    ):
        """Test agent processes multiple context files correctly."""

        # Arrange
        context_references = "\n".join(
            [f"Context: @{file_path}" for file_path in multiple_context_files]
        )
        task_prompt = f"""
{context_references}

Create a technical plan integrating requirements from all context files.
"""

        # Act
        response = agent_tester.execute_agent_task(agent_name, task_prompt)

        # Assert
        assert response is not None, f"Agent {agent_name} returned no response"

        # Validate JSON response format
        json_data = protocol_validator.extract_json_response(response)
        assert json_data is not None, (
            f"Agent {agent_name} did not return valid JSON response"
        )

        # Validate context validation flag
        assert json_data.get("context_validated") is True, (
            f"Agent {agent_name} did not validate multiple context files correctly"
        )

        # Validate status is success or in_progress (not error)
        assert json_data.get("status") in ["success", "in_progress"], (
            f"Agent {agent_name} reported error status for valid multiple context files"
        )

    def test_context_content_integration_quality(
        self, agent_tester, protocol_validator, valid_context_file
    ):
        """Test that agents actually use context file content, not just validate access."""

        # Create context file with specific, unique requirements
        unique_context_path = valid_context_file.replace(".md", "_unique.md")
        with open(unique_context_path, "w") as f:
            f.write("""# Unique Context Requirements

## CRITICAL UNIQUE REQUIREMENT
- Implementation must include SPECIAL_VALIDATION_FLAG
- Code must reference UNIQUE_CONTEXT_MARKER
- Documentation must mention CONTEXT_INTEGRATION_TEST

## Success Criteria
- All unique markers present in output
- Context integration clearly demonstrated
""")

        try:
            # Test with a representative agent
            agent_name = "genie-dev-planner"
            context_reference = f"Context: @{unique_context_path}"
            task_prompt = f"""
{context_reference}

Create a technical specification based on the context file requirements.
"""

            # Act
            response = agent_tester.execute_agent_task(agent_name, task_prompt)

            # Assert context integration
            assert response is not None
            response_text = str(response).lower()

            # Check that unique context markers appear in response or artifacts
            unique_markers = [
                "special_validation_flag",
                "unique_context_marker",
                "context_integration_test",
            ]

            # At least one unique marker should be referenced
            marker_found = any(
                marker.lower() in response_text for marker in unique_markers
            )
            assert marker_found, (
                f"Agent {agent_name} did not demonstrate actual use of context file content"
            )

        finally:
            if os.path.exists(unique_context_path):
                os.unlink(unique_context_path)

    def test_context_file_access_validation_timing(
        self, agent_tester, protocol_validator
    ):
        """Test that agents validate context file access BEFORE task execution."""

        # This test ensures agents fail fast on context issues
        # rather than proceeding with task and failing later

        agent_name = "genie-dev-planner"
        invalid_context = "/definitely/does/not/exist/invalid.md"
        context_reference = f"Context: @{invalid_context}"
        task_prompt = f"""
{context_reference}

This is a complex task that would take significant processing time.
Create a comprehensive technical specification with:
- Detailed architecture analysis
- Multiple implementation phases
- Complex integration requirements
- Performance optimization strategies
"""

        # Measure response time - should be fast for immediate context validation failure
        import time

        start_time = time.time()

        response = agent_tester.execute_agent_task(agent_name, task_prompt)

        end_time = time.time()
        response_time = end_time - start_time

        # Validate quick failure (context validation should be immediate)
        assert response_time < 10.0, (
            f"Agent {agent_name} took too long ({response_time:.2f}s) to detect context file error"
        )

        # Validate error response
        json_data = protocol_validator.extract_json_response(response)
        assert json_data is not None
        assert json_data.get("status") == "error"
        assert json_data.get("context_validated") is False
