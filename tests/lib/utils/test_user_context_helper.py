import unittest
from unittest.mock import Mock, patch

from lib.utils import user_context_helper


class TestCreateUserContextState(unittest.TestCase):
    """Test cases for create_user_context_state function."""

    def test_creates_session_state_with_all_fields(self):
        """Verify proper session_state structure when all user fields are provided."""
        result = user_context_helper.create_user_context_state(
            user_id="42",
            user_name="Alice Silva",
            phone_number="11987654321",
            cpf="12345678900"
        )
        
        expected = {
            "user_context": {
                "user_id": "42",
                "user_name": "Alice Silva",
                "phone_number": "11987654321",
                "cpf": "12345678900"
            }
        }
        self.assertEqual(result, expected)

    def test_handles_partial_user_data(self):
        """Ensure function works correctly when only some fields are provided."""
        result = user_context_helper.create_user_context_state(
            user_id="99",
            user_name="Bob Santos"
        )
        
        expected = {
            "user_context": {
                "user_id": "99",
                "user_name": "Bob Santos"
            }
        }
        self.assertEqual(result, expected)

    def test_filters_none_values(self):
        """Verify that None values are properly filtered out from session state."""
        result = user_context_helper.create_user_context_state(
            user_id=None,
            user_name="Charlie",
            phone_number=None,
            cpf="98765432100"
        )
        
        expected = {
            "user_context": {
                "user_name": "Charlie",
                "cpf": "98765432100"
            }
        }
        self.assertEqual(result, expected)

    def test_accepts_custom_kwargs(self):
        """Test that additional custom fields can be passed via kwargs."""
        result = user_context_helper.create_user_context_state(
            user_id="7",
            user_name="Diana",
            role="admin",
            department="engineering"
        )
        
        expected = {
            "user_context": {
                "user_id": "7",
                "user_name": "Diana",
                "role": "admin",
                "department": "engineering"
            }
        }
        self.assertEqual(result, expected)

    def test_filters_none_from_kwargs(self):
        """Ensure None values in kwargs are also filtered out."""
        result = user_context_helper.create_user_context_state(
            user_id="10",
            custom_field=None,
            valid_field="value"
        )
        
        expected = {
            "user_context": {
                "user_id": "10",
                "valid_field": "value"
            }
        }
        self.assertEqual(result, expected)

    def test_empty_input_returns_empty_context(self):
        """When no data is provided, should return session_state with empty user_context."""
        result = user_context_helper.create_user_context_state()
        
        expected = {"user_context": {}}
        self.assertEqual(result, expected)

    @patch("lib.utils.user_context_helper.logger")
    def test_logs_creation_with_data(self, mock_logger):
        """Verify that user context creation is logged when data is present."""
        user_context_helper.create_user_context_state(
            user_id="123",
            user_name="Test User"
        )
        
        # Verify logger.info was called
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("Created user context state", call_args)

    @patch("lib.utils.user_context_helper.logger")
    def test_no_logging_for_empty_context(self, mock_logger):
        """Verify that no logging occurs when user_context is empty."""
        user_context_helper.create_user_context_state()
        
        # Logger should not be called for empty context
        mock_logger.info.assert_not_called()


class TestGetUserContextFromAgent(unittest.TestCase):
    """Test cases for get_user_context_from_agent function."""

    def test_extracts_context_from_valid_agent(self):
        """Extract user context from agent with valid session_state."""
        agent = Mock()
        agent.session_state = {
            "user_context": {
                "user_id": "55",
                "user_name": "Eduardo"
            }
        }
        
        result = user_context_helper.get_user_context_from_agent(agent)
        
        expected = {
            "user_id": "55",
            "user_name": "Eduardo"
        }
        self.assertEqual(result, expected)

    def test_returns_empty_when_no_session_state(self):
        """Should return empty dict when agent has no session_state."""
        agent = Mock()
        agent.session_state = None
        
        result = user_context_helper.get_user_context_from_agent(agent)
        
        self.assertEqual(result, {})

    def test_returns_empty_when_session_state_empty(self):
        """Should return empty dict when session_state is empty dict."""
        agent = Mock()
        agent.session_state = {}
        
        result = user_context_helper.get_user_context_from_agent(agent)
        
        self.assertEqual(result, {})

    def test_handles_agent_without_session_state_attr(self):
        """Handle agents that don't have session_state attribute at all."""
        # Create object without session_state attribute
        class DummyAgent:
            pass
        
        agent = DummyAgent()
        result = user_context_helper.get_user_context_from_agent(agent)
        
        self.assertEqual(result, {})

    def test_returns_empty_when_no_user_context_key(self):
        """Return empty dict when session_state exists but has no user_context key."""
        agent = Mock()
        agent.session_state = {"other_data": "value"}
        
        result = user_context_helper.get_user_context_from_agent(agent)
        
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
