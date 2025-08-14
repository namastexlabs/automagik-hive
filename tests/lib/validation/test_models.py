"""
Comprehensive tests for validation models.

Tests all validation logic, field constraints, and error handling
to achieve 50%+ coverage of lib/validation/models.py
"""

import pytest
from pydantic import Field, ValidationError

from lib.validation.models import (
    AgentRequest,
    BaseValidatedRequest,
    ErrorResponse,
    HealthRequest,
    SuccessResponse,
    TeamRequest,
    VersionRequest,
    WorkflowRequest,
)


class TestBaseValidatedRequest:
    """Test base validation model configuration."""

    def test_model_config_extra_forbid(self):
        """Test that extra fields are forbidden."""
        
        class TestModel(BaseValidatedRequest):
            field1: str

        # Valid data should work
        model = TestModel(field1="test")
        assert model.field1 == "test"

        # Extra fields should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            TestModel(field1="test", extra_field="not_allowed")
        
        assert "extra_field" in str(exc_info.value)

    def test_model_config_validate_assignment(self):
        """Test that assignment validation is enabled."""
        
        class TestModel(BaseValidatedRequest):
            field1: str = Field(min_length=1)

        model = TestModel(field1="test")
        
        # Invalid assignment should raise ValidationError
        with pytest.raises(ValidationError):
            model.field1 = ""  # Empty string violates min_length


class TestAgentRequest:
    """Test AgentRequest validation and sanitization."""

    def test_valid_agent_request_minimal(self):
        """Test valid minimal agent request."""
        request = AgentRequest(message="Hello world")
        assert request.message == "Hello world"
        assert request.session_id is None
        assert request.user_id is None
        assert request.context is None
        assert request.stream is False

    def test_valid_agent_request_full(self):
        """Test valid full agent request."""
        request = AgentRequest(
            message="Hello world",
            session_id="session_123",
            user_id="user_456",
            context={"key": "value"},
            stream=True
        )
        assert request.message == "Hello world"
        assert request.session_id == "session_123"
        assert request.user_id == "user_456"
        assert request.context == {"key": "value"}
        assert request.stream is True

    def test_message_validation_empty(self):
        """Test message validation with empty values."""
        # Empty string - may hit Pydantic min_length first
        with pytest.raises(ValidationError) as exc_info:
            AgentRequest(message="")
        # Could be either Pydantic or custom validation
        assert "Message cannot be empty" in str(exc_info.value) or "at least 1 character" in str(exc_info.value)

        # Whitespace only - should trigger custom validator
        with pytest.raises(ValidationError) as exc_info:
            AgentRequest(message="   ")
        assert "Message cannot be empty" in str(exc_info.value)

        # None is handled by Pydantic's required field validation
        with pytest.raises(ValidationError):
            AgentRequest()

    def test_message_length_constraints(self):
        """Test message length validation."""
        # Valid length
        request = AgentRequest(message="a" * 100)
        assert len(request.message) == 100

        # Max length
        request = AgentRequest(message="a" * 10000)
        assert len(request.message) == 10000

        # Too long
        with pytest.raises(ValidationError) as exc_info:
            AgentRequest(message="a" * 10001)
        assert "at most 10000 characters" in str(exc_info.value) or "string_too_long" in str(exc_info.value)

    def test_message_sanitization(self):
        """Test message content sanitization."""
        # Test removal of dangerous characters
        request = AgentRequest(message='Hello <script>alert("xss")</script> world')
        assert "<" not in request.message
        assert ">" not in request.message
        assert request.message == 'Hello scriptalert(xss)/script world'

        # Test quote removal
        request = AgentRequest(message='Say "hello" and \'goodbye\'')
        assert '"' not in request.message
        assert "'" not in request.message
        assert request.message == 'Say hello and goodbye'

        # Test whitespace trimming
        request = AgentRequest(message="  Hello world  ")
        assert request.message == "Hello world"

    def test_session_id_validation(self):
        """Test session_id pattern validation."""
        # Valid patterns
        valid_ids = ["session123", "session-123", "session_123", "a", "123"]
        for session_id in valid_ids:
            request = AgentRequest(message="test", session_id=session_id)
            assert request.session_id == session_id

        # Invalid patterns
        invalid_ids = ["session 123", "session@123", "session.123", "session#123"]
        for session_id in invalid_ids:
            with pytest.raises(ValidationError):
                AgentRequest(message="test", session_id=session_id)

    def test_session_id_length_constraints(self):
        """Test session_id length validation."""
        # Valid length
        request = AgentRequest(message="test", session_id="a" * 50)
        assert len(request.session_id) == 50

        # Max length
        request = AgentRequest(message="test", session_id="a" * 100)
        assert len(request.session_id) == 100

        # Too long
        with pytest.raises(ValidationError):
            AgentRequest(message="test", session_id="a" * 101)

        # Too short (empty)
        with pytest.raises(ValidationError):
            AgentRequest(message="test", session_id="")

    def test_user_id_validation(self):
        """Test user_id pattern and length validation."""
        # Valid patterns
        valid_ids = ["user123", "user-123", "user_123"]
        for user_id in valid_ids:
            request = AgentRequest(message="test", user_id=user_id)
            assert request.user_id == user_id

        # Invalid patterns
        invalid_ids = ["user 123", "user@123", "user.123"]
        for user_id in invalid_ids:
            with pytest.raises(ValidationError):
                AgentRequest(message="test", user_id=user_id)

        # Length constraints (same as session_id)
        with pytest.raises(ValidationError):
            AgentRequest(message="test", user_id="a" * 101)

    def test_context_validation_valid(self):
        """Test valid context validation."""
        # Test None context explicitly
        request = AgentRequest(message="test", context=None)
        assert request.context is None
        
        # Valid contexts
        valid_contexts = [
            {"simple": "value"},
            {"nested": {"key": "value"}},
            {"multiple": "values", "with": {"nested": "data"}},
            {"numbers": 123, "booleans": True},
        ]
        
        for context in valid_contexts:
            request = AgentRequest(message="test", context=context)
            assert request.context == context

    def test_context_validation_size_limit(self):
        """Test context size validation."""
        # Create large context
        large_context = {"key": "a" * 5000}
        
        # Should be rejected
        with pytest.raises(ValidationError) as exc_info:
            AgentRequest(message="test", context=large_context)
        assert "Context too large" in str(exc_info.value)

    def test_context_validation_dangerous_keys(self):
        """Test context dangerous key validation."""
        dangerous_keys = ["__", "eval", "exec", "import", "open", "file"]
        
        for key in dangerous_keys:
            dangerous_context = {key: "value"}
            with pytest.raises(ValidationError) as exc_info:
                AgentRequest(message="test", context=dangerous_context)
            assert f"Invalid context key: {key}" in str(exc_info.value)

        # Test partial matches
        partial_matches = ["__init__", "eval_func", "exec_command", "import_data"]
        for key in partial_matches:
            dangerous_context = {key: "value"}
            with pytest.raises(ValidationError) as exc_info:
                AgentRequest(message="test", context=dangerous_context)
            assert f"Invalid context key: {key}" in str(exc_info.value)

    def test_stream_field(self):
        """Test stream field validation."""
        # Default value
        request = AgentRequest(message="test")
        assert request.stream is False

        # Explicit values
        request = AgentRequest(message="test", stream=True)
        assert request.stream is True

        request = AgentRequest(message="test", stream=False)
        assert request.stream is False


class TestTeamRequest:
    """Test TeamRequest validation and sanitization."""

    def test_valid_team_request_minimal(self):
        """Test valid minimal team request."""
        request = TeamRequest(task="Create a simple function")
        assert request.task == "Create a simple function"
        assert request.team_id is None
        assert request.session_id is None
        assert request.user_id is None
        assert request.context == {}  # default_factory=dict
        assert request.stream is False

    def test_valid_team_request_full(self):
        """Test valid full team request."""
        request = TeamRequest(
            task="Create a complex system",
            team_id="dev_team",
            session_id="session_789",
            user_id="user_123",
            context={"complexity": "high"},
            stream=True
        )
        assert request.task == "Create a complex system"
        assert request.team_id == "dev_team"
        assert request.session_id == "session_789"
        assert request.user_id == "user_123"
        assert request.context == {"complexity": "high"}
        assert request.stream is True

    def test_task_validation_empty(self):
        """Test task validation with empty values."""
        # Empty string - may hit Pydantic min_length first
        with pytest.raises(ValidationError) as exc_info:
            TeamRequest(task="")
        # Could be either Pydantic or custom validation
        assert "Task cannot be empty" in str(exc_info.value) or "at least 1 character" in str(exc_info.value)

        # Whitespace only - should trigger custom validator
        with pytest.raises(ValidationError) as exc_info:
            TeamRequest(task="   ")
        assert "Task cannot be empty" in str(exc_info.value)

    def test_task_length_constraints(self):
        """Test task length validation."""
        # Valid length
        request = TeamRequest(task="a" * 100)
        assert len(request.task) == 100

        # Max length
        request = TeamRequest(task="a" * 5000)
        assert len(request.task) == 5000

        # Too long
        with pytest.raises(ValidationError):
            TeamRequest(task="a" * 5001)

    def test_task_sanitization(self):
        """Test task description sanitization."""
        # Test removal of dangerous characters
        request = TeamRequest(task='Create <script>alert("xss")</script> component')
        assert "<" not in request.task
        assert ">" not in request.task
        assert '"' not in request.task
        assert "'" not in request.task

        # Test whitespace trimming
        request = TeamRequest(task="  Create function  ")
        assert request.task == "Create function"

    def test_team_id_validation(self):
        """Test team_id pattern and length validation."""
        # Valid patterns
        valid_ids = ["team123", "team-123", "team_123", "dev"]
        for team_id in valid_ids:
            request = TeamRequest(task="test", team_id=team_id)
            assert request.team_id == team_id

        # Invalid patterns
        invalid_ids = ["team 123", "team@123", "team.123"]
        for team_id in invalid_ids:
            with pytest.raises(ValidationError):
                TeamRequest(task="test", team_id=team_id)

        # Length constraints
        request = TeamRequest(task="test", team_id="a" * 50)
        assert len(request.team_id) == 50

        with pytest.raises(ValidationError):
            TeamRequest(task="test", team_id="a" * 51)

    def test_context_default_factory(self):
        """Test context default_factory behavior."""
        request1 = TeamRequest(task="test1")
        request2 = TeamRequest(task="test2")
        
        # Should have separate dict instances
        request1.context["key1"] = "value1"
        assert "key1" not in request2.context


class TestWorkflowRequest:
    """Test WorkflowRequest validation."""

    def test_valid_workflow_request_minimal(self):
        """Test valid minimal workflow request."""
        request = WorkflowRequest(workflow_id="workflow123")
        assert request.workflow_id == "workflow123"
        assert request.input_data == {}
        assert request.session_id is None
        assert request.user_id is None

    def test_valid_workflow_request_full(self):
        """Test valid full workflow request."""
        request = WorkflowRequest(
            workflow_id="complex_workflow",
            input_data={"param1": "value1", "param2": 123},
            session_id="session_999",
            user_id="user_789"
        )
        assert request.workflow_id == "complex_workflow"
        assert request.input_data == {"param1": "value1", "param2": 123}
        assert request.session_id == "session_999"
        assert request.user_id == "user_789"

    def test_workflow_id_validation(self):
        """Test workflow_id pattern and length validation."""
        # Valid patterns
        valid_ids = ["workflow123", "workflow-123", "workflow_123", "wf"]
        for workflow_id in valid_ids:
            request = WorkflowRequest(workflow_id=workflow_id)
            assert request.workflow_id == workflow_id

        # Invalid patterns
        invalid_ids = ["workflow 123", "workflow@123", "workflow.123"]
        for workflow_id in invalid_ids:
            with pytest.raises(ValidationError):
                WorkflowRequest(workflow_id=workflow_id)

        # Length constraints
        request = WorkflowRequest(workflow_id="a" * 50)
        assert len(request.workflow_id) == 50

        with pytest.raises(ValidationError):
            WorkflowRequest(workflow_id="a" * 51)

        with pytest.raises(ValidationError):
            WorkflowRequest(workflow_id="")

    def test_input_data_size_validation(self):
        """Test input_data size validation."""
        # Create large input data
        large_data = {"key": "a" * 10000}
        
        # Should be rejected
        with pytest.raises(ValidationError) as exc_info:
            WorkflowRequest(workflow_id="test", input_data=large_data)
        assert "Input data too large" in str(exc_info.value)

    def test_input_data_dangerous_keys(self):
        """Test input_data dangerous key validation."""
        dangerous_keys = ["__", "eval", "exec", "import", "open", "file"]
        
        for key in dangerous_keys:
            dangerous_data = {key: "value"}
            with pytest.raises(ValidationError) as exc_info:
                WorkflowRequest(workflow_id="test", input_data=dangerous_data)
            assert f"Invalid input key: {key}" in str(exc_info.value)

    def test_input_data_recursive_validation(self):
        """Test recursive validation of nested input data."""
        # Nested dangerous key
        nested_data = {
            "safe_key": {
                "nested": {
                    "eval": "dangerous_value"
                }
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            WorkflowRequest(workflow_id="test", input_data=nested_data)
        assert "Invalid input key: eval" in str(exc_info.value)

        # Safe nested data should work
        safe_nested_data = {
            "safe_key": {
                "nested": {
                    "safe_nested": "safe_value"
                }
            }
        }
        
        request = WorkflowRequest(workflow_id="test", input_data=safe_nested_data)
        assert request.input_data == safe_nested_data

    def test_input_data_default_factory(self):
        """Test input_data default_factory behavior."""
        request1 = WorkflowRequest(workflow_id="test1")
        request2 = WorkflowRequest(workflow_id="test2")
        
        # Should have separate dict instances
        request1.input_data["key1"] = "value1"
        assert "key1" not in request2.input_data


class TestHealthRequest:
    """Test HealthRequest minimal validation."""

    def test_valid_health_request(self):
        """Test valid health request."""
        request = HealthRequest()
        assert isinstance(request, HealthRequest)
        assert isinstance(request, BaseValidatedRequest)

    def test_health_request_inherits_config(self):
        """Test that HealthRequest inherits base configuration."""
        # Should forbid extra fields
        with pytest.raises(ValidationError):
            HealthRequest(extra_field="not_allowed")


class TestVersionRequest:
    """Test VersionRequest minimal validation."""

    def test_valid_version_request(self):
        """Test valid version request."""
        request = VersionRequest()
        assert isinstance(request, VersionRequest)
        assert isinstance(request, BaseValidatedRequest)

    def test_version_request_inherits_config(self):
        """Test that VersionRequest inherits base configuration."""
        # Should forbid extra fields
        with pytest.raises(ValidationError):
            VersionRequest(extra_field="not_allowed")


class TestErrorResponse:
    """Test ErrorResponse model."""

    def test_valid_error_response_minimal(self):
        """Test valid minimal error response."""
        response = ErrorResponse(error="Something went wrong")
        assert response.error == "Something went wrong"
        assert response.detail is None
        assert response.error_code is None

    def test_valid_error_response_full(self):
        """Test valid full error response."""
        response = ErrorResponse(
            error="Validation failed",
            detail="Field 'message' is required",
            error_code="VALIDATION_ERROR"
        )
        assert response.error == "Validation failed"
        assert response.detail == "Field 'message' is required"
        assert response.error_code == "VALIDATION_ERROR"

    def test_error_required_field(self):
        """Test that error field is required."""
        with pytest.raises(ValidationError):
            ErrorResponse()

    def test_error_response_serialization(self):
        """Test error response serialization."""
        response = ErrorResponse(error="Test error", detail="Test detail")
        data = response.model_dump()
        assert data == {
            "error": "Test error",
            "detail": "Test detail",
            "error_code": None
        }


class TestSuccessResponse:
    """Test SuccessResponse model."""

    def test_valid_success_response_minimal(self):
        """Test valid minimal success response."""
        response = SuccessResponse()
        assert response.success is True
        assert response.message is None
        assert response.data is None

    def test_valid_success_response_full(self):
        """Test valid full success response."""
        response = SuccessResponse(
            success=True,
            message="Operation completed successfully",
            data={"result": "success", "count": 42}
        )
        assert response.success is True
        assert response.message == "Operation completed successfully"
        assert response.data == {"result": "success", "count": 42}

    def test_success_response_false(self):
        """Test success response with false value."""
        response = SuccessResponse(success=False)
        assert response.success is False

    def test_success_response_serialization(self):
        """Test success response serialization."""
        response = SuccessResponse(message="Test", data={"key": "value"})
        data = response.model_dump()
        assert data == {
            "success": True,
            "message": "Test",
            "data": {"key": "value"}
        }

    def test_success_response_any_data_type(self):
        """Test success response with various data types."""
        # String data
        response = SuccessResponse(data="string_data")
        assert response.data == "string_data"

        # List data
        response = SuccessResponse(data=[1, 2, 3])
        assert response.data == [1, 2, 3]

        # None data
        response = SuccessResponse(data=None)
        assert response.data is None


# Integration tests
class TestModelIntegration:
    """Test model integration and edge cases."""

    def test_all_models_inherit_base_config(self):
        """Test that all request models inherit base configuration."""
        models = [AgentRequest, TeamRequest, WorkflowRequest, HealthRequest, VersionRequest]
        
        for model_class in models:
            # Test extra field prohibition
            with pytest.raises(ValidationError):
                if model_class in [HealthRequest, VersionRequest]:
                    model_class(extra_field="not_allowed")
                elif model_class == AgentRequest:
                    model_class(message="test", extra_field="not_allowed")
                elif model_class == TeamRequest:
                    model_class(task="test", extra_field="not_allowed")
                elif model_class == WorkflowRequest:
                    model_class(workflow_id="test", extra_field="not_allowed")

    def test_field_validator_inheritance(self):
        """Test that field validators work correctly."""
        # Test that validators are applied
        with pytest.raises(ValidationError):
            AgentRequest(message="")  # Should trigger sanitize_message validator

        with pytest.raises(ValidationError):
            TeamRequest(task="")  # Should trigger sanitize_task validator

        with pytest.raises(ValidationError):
            WorkflowRequest(workflow_id="test", input_data={"eval": "bad"})  # Should trigger validate_input_data

    def test_model_dump_and_load(self):
        """Test model serialization and deserialization."""
        original = AgentRequest(
            message="Test message",
            session_id="session_123",
            context={"key": "value"}
        )
        
        # Serialize
        data = original.model_dump()
        
        # Deserialize
        reconstructed = AgentRequest(**data)
        
        assert reconstructed.message == original.message
        assert reconstructed.session_id == original.session_id
        assert reconstructed.context == original.context