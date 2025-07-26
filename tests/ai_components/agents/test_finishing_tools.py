"""
Tests for ai/agents/tools/finishing_tools.py - Finishing tools for conversation completion
"""

from unittest.mock import Mock, patch

import pytest

from ai.agents.tools.finishing_tools import (
    send_farewell_message,
    trigger_conversation_typification_workflow,
)


class TestTriggerConversationTypificationWorkflow:
    """Test conversation typification workflow trigger."""

    @patch("ai.workflows.registry.get_workflow")
    @patch("ai.workflows.registry.is_workflow_registered")
    def test_successful_typification_with_protocol(
        self,
        mock_is_registered,
        mock_get_workflow,
    ):
        """Test successful typification with protocol generation."""
        mock_is_registered.return_value = True

        # Mock workflow result with protocol metadata
        mock_result = Mock()
        mock_result.metadata = {"protocol_info": {"protocol_id": "PROTO-123456"}}

        mock_workflow = Mock()
        mock_workflow.run.return_value = [mock_result]
        mock_get_workflow.return_value = mock_workflow

        result = trigger_conversation_typification_workflow.entrypoint(
            session_id="session-123",
            conversation_history="Customer: Help\nAgent: Sure",
            customer_message="Thank you",
            customer_id="customer-456",
        )

        assert "Tipificação concluída com sucesso" in result
        assert "PROTO-123456" in result

        # Verify workflow was called correctly
        mock_is_registered.assert_called_once_with("conversation-typification")
        mock_get_workflow.assert_called_once_with("conversation-typification")
        mock_workflow.run.assert_called_once_with(
            message="Customer: Help\nAgent: Sure",
            session_id="session-123",
            customer_id="customer-456",
        )

    @patch("ai.workflows.registry.get_workflow")
    @patch("ai.workflows.registry.is_workflow_registered")
    def test_typification_without_protocol_id(
        self,
        mock_is_registered,
        mock_get_workflow,
    ):
        """Test typification completed but no protocol ID found."""
        mock_is_registered.return_value = True

        # Mock workflow result without protocol ID
        mock_result = Mock()
        mock_result.metadata = {
            "protocol_info": {},  # No protocol_id
        }

        mock_workflow = Mock()
        mock_workflow.run.return_value = [mock_result]
        mock_get_workflow.return_value = mock_workflow

        result = trigger_conversation_typification_workflow.entrypoint(
            session_id="session-123",
            conversation_history="Customer: Help",
            customer_message="Thanks",
        )

        assert "Tipificação concluída, mas protocolo não encontrado" in result

    @patch("ai.workflows.registry.get_workflow")
    @patch("ai.workflows.registry.is_workflow_registered")
    def test_typification_without_metadata(self, mock_is_registered, mock_get_workflow) -> None:
        """Test typification completed but no metadata found."""
        mock_is_registered.return_value = True

        # Mock workflow result without metadata
        mock_result = Mock()
        mock_result.metadata = None

        mock_workflow = Mock()
        mock_workflow.run.return_value = [mock_result]
        mock_get_workflow.return_value = mock_workflow

        result = trigger_conversation_typification_workflow.entrypoint(
            session_id="session-123",
            conversation_history="Customer: Help",
            customer_message="Thanks",
        )

        assert "Tipificação concluída com sucesso!" in result

    @patch("ai.workflows.registry.get_workflow")
    @patch("ai.workflows.registry.is_workflow_registered")
    def test_typification_result_without_metadata_attribute(
        self,
        mock_is_registered,
        mock_get_workflow,
    ):
        """Test typification with result that has no metadata attribute."""
        mock_is_registered.return_value = True

        # Mock workflow result without metadata attribute
        mock_result = Mock(spec=[])  # spec=[] means no attributes

        mock_workflow = Mock()
        mock_workflow.run.return_value = [mock_result]
        mock_get_workflow.return_value = mock_workflow

        result = trigger_conversation_typification_workflow.entrypoint(
            session_id="session-123",
            conversation_history="Customer: Help",
            customer_message="Thanks",
        )

        assert "Tipificação concluída com sucesso!" in result

    @patch("ai.workflows.registry.is_workflow_registered")
    def test_workflow_not_registered(self, mock_is_registered) -> None:
        """Test when typification workflow is not registered."""
        mock_is_registered.return_value = False

        result = trigger_conversation_typification_workflow.entrypoint(
            session_id="session-123",
            conversation_history="Customer: Help",
            customer_message="Thanks",
        )

        assert "Workflow de tipificação não está disponível" in result
        mock_is_registered.assert_called_once_with("conversation-typification")

    @patch("ai.workflows.registry.get_workflow")
    @patch("ai.workflows.registry.is_workflow_registered")
    def test_empty_workflow_results(self, mock_is_registered, mock_get_workflow) -> None:
        """Test when workflow returns no results."""
        mock_is_registered.return_value = True

        mock_workflow = Mock()
        mock_workflow.run.return_value = []  # Empty results
        mock_get_workflow.return_value = mock_workflow

        result = trigger_conversation_typification_workflow.entrypoint(
            session_id="session-123",
            conversation_history="Customer: Help",
            customer_message="Thanks",
        )

        assert "Erro na tipificação: Nenhum resultado obtido" in result

    @patch("ai.workflows.registry.get_workflow")
    @patch("ai.workflows.registry.is_workflow_registered")
    def test_workflow_execution_exception(self, mock_is_registered, mock_get_workflow) -> None:
        """Test when workflow execution raises an exception."""
        mock_is_registered.return_value = True

        mock_workflow = Mock()
        mock_workflow.run.side_effect = Exception("Workflow failed")
        mock_get_workflow.return_value = mock_workflow

        result = trigger_conversation_typification_workflow.entrypoint(
            session_id="session-123",
            conversation_history="Customer: Help",
            customer_message="Thanks",
        )

        assert "Erro na tipificação: Workflow failed" in result

    @patch("ai.workflows.registry.is_workflow_registered")
    def test_workflow_registry_import_exception(self, mock_is_registered) -> None:
        """Test when workflow registry import fails."""
        mock_is_registered.side_effect = ImportError("Cannot import workflow registry")

        result = trigger_conversation_typification_workflow.entrypoint(
            session_id="session-123",
            conversation_history="Customer: Help",
            customer_message="Thanks",
        )

        assert "Erro na tipificação" in result
        assert "Cannot import workflow registry" in result

    @patch("ai.workflows.registry.get_workflow")
    @patch("ai.workflows.registry.is_workflow_registered")
    def test_multiple_workflow_results(self, mock_is_registered, mock_get_workflow) -> None:
        """Test with multiple workflow results (should use the last one)."""
        mock_is_registered.return_value = True

        # Mock multiple workflow results
        mock_result1 = Mock()
        mock_result1.metadata = {"protocol_info": {"protocol_id": "PROTO-111"}}

        mock_result2 = Mock()
        mock_result2.metadata = {"protocol_info": {"protocol_id": "PROTO-222"}}

        mock_workflow = Mock()
        mock_workflow.run.return_value = [mock_result1, mock_result2]
        mock_get_workflow.return_value = mock_workflow

        result = trigger_conversation_typification_workflow.entrypoint(
            session_id="session-123",
            conversation_history="Customer: Help",
            customer_message="Thanks",
        )

        # Should use the last result (PROTO-222)
        assert "PROTO-222" in result
        assert "PROTO-111" not in result


class TestSendFarewellMessage:
    """Test farewell message generation."""

    def test_standard_farewell_with_customer_name(self) -> None:
        """Test standard farewell message with customer name."""
        result = send_farewell_message.entrypoint(
            protocol_id="PROTO-12345",
            customer_name="João Silva",
            message_type="standard",
        )

        assert "João Silva" in result
        assert "PROTO-12345" in result
        assert "Obrigado por entrar em contato" in result
        assert "finalizado com sucesso" in result

    def test_grateful_farewell_with_customer_name(self) -> None:
        """Test grateful farewell message with customer name."""
        result = send_farewell_message.entrypoint(
            protocol_id="PROTO-67890",
            customer_name="Maria Santos",
            message_type="grateful",
        )

        assert "Maria Santos" in result
        assert "PROTO-67890" in result
        assert "Fico feliz em ter ajudado" in result
        assert "Tenha um ótimo dia" in result

    def test_professional_farewell_with_customer_name(self) -> None:
        """Test professional farewell message with customer name."""
        result = send_farewell_message.entrypoint(
            protocol_id="PROTO-11111",
            customer_name="Carlos Oliveira",
            message_type="professional",
        )

        assert "Carlos Oliveira" in result
        assert "PROTO-11111" in result
        assert "Atendimento finalizado para" in result
        assert "Agradecemos" in result

    def test_standard_farewell_without_customer_name(self) -> None:
        """Test standard farewell message without customer name."""
        result = send_farewell_message.entrypoint(
            protocol_id="PROTO-22222",
            message_type="standard",
        )

        assert "PROTO-22222" in result
        assert "finalizado com sucesso" in result
        assert "Obrigado" in result
        # Should not contain any specific name
        assert "João" not in result
        assert "Maria" not in result

    def test_grateful_farewell_without_customer_name(self) -> None:
        """Test grateful farewell message without customer name."""
        result = send_farewell_message.entrypoint(
            protocol_id="PROTO-33333",
            message_type="grateful",
        )

        assert "PROTO-33333" in result
        assert "Fico feliz em ter ajudado" in result
        assert "Agradecemos" in result

    def test_professional_farewell_without_customer_name(self) -> None:
        """Test professional farewell message without customer name."""
        result = send_farewell_message.entrypoint(
            protocol_id="PROTO-44444",
            message_type="professional",
        )

        assert "PROTO-44444" in result
        assert "Atendimento finalizado com sucesso" in result
        assert "Agradecemos pela preferência" in result

    def test_default_message_type(self) -> None:
        """Test that standard is the default message type."""
        result = send_farewell_message.entrypoint(
            protocol_id="PROTO-55555",
            customer_name="Test User",
        )  # No message_type specified

        assert "Test User" in result
        assert "PROTO-55555" in result
        assert "Obrigado por entrar em contato" in result
        assert "finalizado com sucesso" in result

    def test_unknown_message_type_defaults_to_standard(self) -> None:
        """Test that unknown message types default to standard."""
        result = send_farewell_message.entrypoint(
            protocol_id="PROTO-66666",
            customer_name="Test User",
            message_type="unknown_type",
        )

        assert "Test User" in result
        assert "PROTO-66666" in result
        assert "Obrigado por entrar em contato" in result
        assert "finalizado com sucesso" in result

    @patch("ai.agents.tools.finishing_tools.logger")
    def test_logging_calls(self, mock_logger) -> None:
        """Test that appropriate logging calls are made."""
        send_farewell_message.entrypoint(
            protocol_id="PROTO-77777",
            customer_name="Log Test",
        )

        # Check that info logs were called
        assert mock_logger.info.call_count >= 2

        # Check log messages contain expected content
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Sending farewell message" in call for call in log_calls)
        assert any(
            "Farewell message created successfully" in call for call in log_calls
        )

    def test_protocol_formatting(self) -> None:
        """Test protocol ID formatting in messages."""
        protocol_id = "PROTO-FORMAT-TEST"
        result = send_farewell_message.entrypoint(protocol_id=protocol_id)

        assert f"Protocolo: {protocol_id}" in result

    def test_empty_protocol_id(self) -> None:
        """Test behavior with empty protocol ID."""
        result = send_farewell_message.entrypoint(protocol_id="")

        assert "Protocolo:" in result
        assert "finalizado com sucesso" in result

    def test_none_customer_name_handling(self) -> None:
        """Test explicit None customer name handling."""
        result = send_farewell_message.entrypoint(
            protocol_id="PROTO-NONE-TEST",
            customer_name=None,
        )

        assert "PROTO-NONE-TEST" in result
        assert "finalizado com sucesso" in result
        # Should not contain any customer name
        assert not any(name in result.lower() for name in ["joão", "maria", "carlos"])


if __name__ == "__main__":
    pytest.main([__file__])
