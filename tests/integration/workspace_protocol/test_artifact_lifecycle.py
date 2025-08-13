"""
Workspace Protocol Validation: Artifact Lifecycle Management Tests

Tests that all agents properly implement the artifact lifecycle protocol:
/genie/ideas/ → /genie/wishes/ → DELETE progression
"""

import os
from pathlib import Path

import pytest

from tests.integration.workspace_protocol.utils.agent_tester import AgentTester
from tests.integration.workspace_protocol.utils.protocol_validator import ProtocolValidator


class TestArtifactLifecycle:
    """Test suite for artifact lifecycle management protocol compliance."""

    @pytest.fixture
    def agent_tester(self):
        """Initialize agent testing utility."""
        return AgentTester()

    @pytest.fixture
    def protocol_validator(self):
        """Initialize protocol validation utility."""
        return ProtocolValidator()

    @pytest.fixture
    def ideas_directory(self):
        """Ensure ideas directory exists for testing."""
        ideas_path = Path("/home/namastex/workspace/automagik-hive/genie/ideas")
        ideas_path.mkdir(parents=True, exist_ok=True)
        return ideas_path

    @pytest.fixture
    def wishes_directory(self):
        """Ensure wishes directory exists for testing."""
        wishes_path = Path("/home/namastex/workspace/automagik-hive/genie/wishes")
        wishes_path.mkdir(parents=True, exist_ok=True)
        return wishes_path

    @pytest.fixture
    def cleanup_test_artifacts(self):
        """Clean up test artifacts after tests."""
        test_files = []
        yield test_files

        # Cleanup any test files created during testing
        for file_path in test_files:
            if isinstance(file_path, str | Path) and os.path.exists(file_path):
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
    def test_ideas_phase_artifact_creation(
        self,
        agent_tester,
        protocol_validator,
        ideas_directory,
        cleanup_test_artifacts,
        agent_name,
    ):
        """Test agent creates initial artifacts in /genie/ideas/ directory."""

        # Arrange
        task_prompt = """
Create an initial analysis and brainstorming document for implementing a new
user authentication system with multi-factor authentication support.

This should be an initial draft/analysis phase.
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

        # Check for artifacts in response
        artifacts = json_data.get("artifacts", [])

        if artifacts:  # If agent created artifacts
            # Validate artifacts are in ideas directory for initial phase
            ideas_artifacts = [a for a in artifacts if "/genie/ideas/" in a]

            # For initial brainstorming, should prefer ideas directory
            if json_data.get("status") == "in_progress":
                assert len(ideas_artifacts) > 0, (
                    f"Agent {agent_name} should create initial artifacts in /genie/ideas/ during brainstorming"
                )

            # Validate artifact files actually exist
            for artifact_path in artifacts:
                cleanup_test_artifacts.append(artifact_path)
                if os.path.isabs(artifact_path):  # Only check absolute paths
                    assert os.path.exists(artifact_path), (
                        f"Agent {agent_name} reported artifact {artifact_path} but file does not exist"
                    )

    @pytest.mark.parametrize(
        "agent_name",
        [
            "genie-dev-planner",
            "genie-dev-designer",
            "genie-dev-coder",
            "genie-testing-maker",
            "genie-clone",
        ],
    )
    def test_wishes_phase_migration(
        self,
        agent_tester,
        protocol_validator,
        ideas_directory,
        wishes_directory,
        cleanup_test_artifacts,
        agent_name,
    ):
        """Test agent migrates refined plans to /genie/wishes/ directory."""

        # Arrange - Create initial idea file
        initial_idea_path = ideas_directory / f"test_auth_system_{agent_name}.md"
        with open(initial_idea_path, "w") as f:
            f.write("""# Authentication System Analysis

## Initial Brainstorming
- Multi-factor authentication
- JWT token management
- Session handling
- Password policies

## Next Steps
- Refine into executable plan
- Define implementation phases
- Create detailed specifications
""")
        cleanup_test_artifacts.append(str(initial_idea_path))

        task_prompt = f"""
Context: @{initial_idea_path}

Refine the authentication system analysis into an execution-ready plan.
This should be ready for implementation.
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

        # Check for artifacts in response
        artifacts = json_data.get("artifacts", [])

        if artifacts and json_data.get("status") == "success":
            # Validate execution-ready artifacts are in wishes directory
            wishes_artifacts = [a for a in artifacts if "/genie/wishes/" in a]
            assert len(wishes_artifacts) > 0, (
                f"Agent {agent_name} should create execution-ready artifacts in /genie/wishes/"
            )

            # Validate artifact files actually exist
            for artifact_path in wishes_artifacts:
                cleanup_test_artifacts.append(artifact_path)
                assert os.path.exists(artifact_path), (
                    f"Agent {agent_name} reported wishes artifact {artifact_path} but file does not exist"
                )

    def test_completion_protocol_deletion(
        self, agent_tester, protocol_validator, wishes_directory, cleanup_test_artifacts
    ):
        """Test agent deletes artifacts from wishes upon task completion."""

        # Arrange - Create a wishes file that should be deleted upon completion
        test_wish_path = wishes_directory / "test_completion_protocol.md"
        with open(test_wish_path, "w") as f:
            f.write("""# Test Completion Protocol

This file should be deleted when the task is completed successfully.

## Task
- Simple file creation task
- Should result in completion
- Should trigger deletion protocol

## Expected Outcome
- Task marked as complete
- This file deleted from wishes
""")

        # Use a simple agent that can complete quickly
        agent_name = "genie-dev-planner"

        task_prompt = f"""
Context: @{test_wish_path}

Complete the simple task described in the context file.
This is a straightforward completion test.
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

        # If task is completed successfully
        if json_data.get("status") == "success":
            # The wishes file should be deleted per protocol
            assert not os.path.exists(test_wish_path), (
                f"Agent {agent_name} did not delete wishes artifact upon completion"
            )

        # Clean up if file still exists (for partial completion or errors)
        if os.path.exists(test_wish_path):
            cleanup_test_artifacts.append(str(test_wish_path))

    def test_no_direct_output_compliance(self, agent_tester, protocol_validator):
        """Test agents do not output large artifacts directly in response text."""

        # Test with an agent that might be tempted to output large content
        agent_name = "genie-dev-designer"

        task_prompt = """
Create a comprehensive system architecture document for a microservices-based
e-commerce platform with the following components:
- User authentication service
- Product catalog service
- Shopping cart service
- Payment processing service
- Order management service
- Notification service
- API gateway
- Database design
- Deployment architecture
- Security considerations

This should be a detailed, comprehensive document.
"""

        # Act
        response = agent_tester.execute_agent_task(agent_name, task_prompt)

        # Assert
        assert response is not None, f"Agent {agent_name} returned no response"

        # Validate JSON response format (should be concise)
        json_data = protocol_validator.extract_json_response(response)
        assert json_data is not None, (
            f"Agent {agent_name} did not return valid JSON response"
        )

        # Response should be concise JSON, not large document
        response_text = str(response)
        response_length = len(response_text)

        # Response should be reasonably short (just JSON + brief summary)
        # Large documents should be in artifact files, not response text
        assert response_length < 2000, (
            f"Agent {agent_name} output large content directly ({response_length} chars) instead of using artifacts"
        )

        # If artifacts were created, they should contain the actual content
        artifacts = json_data.get("artifacts", [])
        if artifacts:
            for artifact_path in artifacts:
                if os.path.exists(artifact_path):
                    with open(artifact_path) as f:
                        artifact_content = f.read()

                    # Artifact should contain substantial content
                    assert len(artifact_content) > response_length, (
                        f"Agent {agent_name} artifact should contain more content than response text"
                    )

    def test_artifact_path_consistency(self, agent_tester, protocol_validator):
        """Test that artifact paths reported in JSON responses are consistent and valid."""

        agent_name = "genie-dev-planner"

        task_prompt = """
Create a technical specification for implementing a REST API with the following endpoints:
- GET /users - List all users
- POST /users - Create new user
- GET /users/{id} - Get specific user
- PUT /users/{id} - Update user
- DELETE /users/{id} - Delete user

Include authentication, validation, and error handling requirements.
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

        # Check artifact path consistency
        artifacts = json_data.get("artifacts", [])

        for artifact_path in artifacts:
            # Path should be absolute
            assert os.path.isabs(artifact_path), (
                f"Agent {agent_name} reported relative path {artifact_path}, should be absolute"
            )

            # Path should be in expected directories
            valid_directories = ["/genie/ideas/", "/genie/wishes/"]
            is_valid_location = any(
                valid_dir in artifact_path for valid_dir in valid_directories
            )
            assert is_valid_location, (
                f"Agent {agent_name} created artifact in invalid location {artifact_path}"
            )

            # Path should use .md extension for markdown files
            if "/genie/" in artifact_path:
                assert artifact_path.endswith(".md"), (
                    f"Agent {agent_name} artifact {artifact_path} should use .md extension"
                )

    def test_lifecycle_state_progression(
        self,
        agent_tester,
        protocol_validator,
        ideas_directory,
        wishes_directory,
        cleanup_test_artifacts,
    ):
        """Test complete lifecycle progression from ideas to wishes to deletion."""

        # This is an integration test of the full lifecycle
        agent_name = "genie-dev-planner"

        # Phase 1: Initial brainstorming (should create in ideas)
        brainstorm_prompt = """
Brainstorm approaches for implementing a caching system for a web application.
Consider different caching strategies, technologies, and trade-offs.
This is initial exploration.
"""

        response1 = agent_tester.execute_agent_task(agent_name, brainstorm_prompt)
        json_data1 = protocol_validator.extract_json_response(response1)

        assert json_data1 is not None
        artifacts1 = json_data1.get("artifacts", [])

        # Should have created something in ideas if status is in_progress
        if json_data1.get("status") == "in_progress" and artifacts1:
            ideas_artifacts = [a for a in artifacts1 if "/genie/ideas/" in a]
            assert len(ideas_artifacts) > 0, (
                "Phase 1 should create artifacts in ideas directory"
            )

            # Track for cleanup
            cleanup_test_artifacts.extend(artifacts1)

            # Phase 2: Refine to execution-ready (should move to wishes)
            refine_prompt = f"""
Context: @{ideas_artifacts[0]}

Refine the caching system analysis into a detailed implementation plan
ready for development execution.
"""

            response2 = agent_tester.execute_agent_task(agent_name, refine_prompt)
            json_data2 = protocol_validator.extract_json_response(response2)

            assert json_data2 is not None
            artifacts2 = json_data2.get("artifacts", [])

            if json_data2.get("status") == "success" and artifacts2:
                wishes_artifacts = [a for a in artifacts2 if "/genie/wishes/" in a]
                assert len(wishes_artifacts) > 0, (
                    "Phase 2 should create artifacts in wishes directory"
                )

                # Track for cleanup
                cleanup_test_artifacts.extend(artifacts2)

                # Phase 3: Mark as complete (should delete from wishes)
                completion_prompt = f"""
Context: @{wishes_artifacts[0]}

Mark this caching system implementation plan as completed.
The plan is ready and task is finished.
"""

                response3 = agent_tester.execute_agent_task(
                    agent_name, completion_prompt
                )
                json_data3 = protocol_validator.extract_json_response(response3)

                assert json_data3 is not None

                # If marked as complete, wishes artifact should be deleted
                if json_data3.get("status") == "success":
                    for wishes_path in wishes_artifacts:
                        assert not os.path.exists(wishes_path), (
                            f"Wishes artifact {wishes_path} should be deleted upon completion"
                        )
