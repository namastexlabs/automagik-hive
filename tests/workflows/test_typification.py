# tests/workflows/test_typification.py

import re
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import pytest
from pydantic import ValidationError

from ai.workflows.conversation_typification import models
from ai.workflows.conversation_typification import workflow as wf_mod
from agno.agent import Agent
from agno.workflow import RunResponse
from agno.storage.postgres import PostgresStorage


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def patched_hierarchy(monkeypatch):
    """
    Provide an in-memory minimal hierarchy for every test and
    patch all modules that rely on the global HIERARCHY symbol
    or load_hierarchy() helper.
    """
    test_hierarchy = {
        "Adquirência Web": {
            "Antecipação de Vendas": {
                "Dúvidas sobre a Antecipação de Vendas": ["Cliente orientado sobre a Antecipação de Vendas"],
                "Dúvidas sobre a Antecipação Agendada": ["Cliente orientado sobre Antecipação Agendada"],
                "Cliente deseja fazer a Antecipação de Vendas": [
                    "Cliente orientado a fazer o processo via app - vendas de outras adquirentes/máquinas",
                    "Cliente orientado a fazer o processo via máquina"
                ],
                "Dúvidas sobre a Antecipação": ["Esclarecimentos sobre a Antecipação de vendas de outras adquirentes/máquinas"]
            }
        },
        "Emissão": {
            "Cartão Pré-Pago": {
                "Uso do cartão": [
                    "Cobrança de mensalidade por falta de utilização do cartão",
                    "Como recarregar o cartão"
                ]
            },
            "Cartão da Conta (débito)": {
                "Entrega de cartão": ["Não recebimento do cartão"]
            }
        },
        "PagBank": {
            "Conta Digital": {
                "Problemas de acesso": [
                    "Esqueci minha senha",
                    "App não abre"
                ]
            }
        }
    }

    # Replace global constant in models.py
    monkeypatch.setattr(models, "HIERARCHY", test_hierarchy, raising=False)
    # workflow.ConversationTypificationWorkflow.__init__() calls load_hierarchy(); patch it
    monkeypatch.setattr(models, "load_hierarchy", lambda: test_hierarchy, raising=True)

    yield test_hierarchy


@pytest.fixture
def mock_storage():
    """Mock PostgreSQL storage for testing"""
    mock = Mock(spec=PostgresStorage)
    return mock


@pytest.fixture
def mock_claude_agent():
    """Mock Claude agent responses"""
    mock = Mock(spec=Agent)
    mock.run.return_value = Mock(content=Mock())
    return mock


# ---------------------------------------------------------------------------
# validate_typification_path utility tests
# ---------------------------------------------------------------------------

def test_validate_path_happy():
    """
    validate_typification_path should accept a fully valid 4-level path
    and return a ValidationResult(valid=True, level_reached=5)
    """
    res = models.validate_typification_path(
        "Adquirência Web",
        "Antecipação de Vendas",
        "Dúvidas sobre a Antecipação de Vendas",
        "Cliente orientado sobre a Antecipação de Vendas",
    )
    assert res.valid is True
    assert res.level_reached == 5
    assert res.error_message is None


@pytest.mark.parametrize(
    "business_unit,product,motive,submotive,expected_level",
    [
        ("Unknown BU", "Antecipação de Vendas", "Dúvidas sobre a Antecipação de Vendas", "Cliente orientado sobre a Antecipação de Vendas", 1),
        ("Adquirência Web", "Produto inválido", "Dúvidas sobre a Antecipação de Vendas", "Cliente orientado sobre a Antecipação de Vendas", 2),
        ("Adquirência Web", "Antecipação de Vendas", "Motivo inválido", "Cliente orientado sobre a Antecipação de Vendas", 3),
        ("Adquirência Web", "Antecipação de Vendas", "Dúvidas sobre a Antecipação de Vendas", "Submotive inválido", 4),
    ],
)
def test_validate_path_invalid_levels(
    business_unit, product, motive, submotive, expected_level
):
    """
    Each hierarchy level should stop validation at the first invalid element
    and return the correct level_reached counter (1-4).
    """
    res = models.validate_typification_path(
        business_unit, product, motive, submotive
    )
    assert res.valid is False
    assert res.level_reached == expected_level
    # Error message must reference the offending value
    error_prefixes = {
        1: "Unidade de negócio",
        2: "Produto",
        3: "Motivo",
        4: "Submotivo"
    }
    assert str(res.error_message).startswith(error_prefixes[expected_level])


def test_validate_path_provides_suggestions():
    """ValidationResult should provide suggested corrections for invalid paths"""
    res = models.validate_typification_path(
        "Adquirência Web",
        "Produto inválido",
        "Dúvidas sobre a Antecipação de Vendas",
        "Cliente orientado sobre a Antecipação de Vendas"
    )
    assert res.valid is False
    assert len(res.suggested_corrections) > 0
    assert "Antecipação de Vendas" in res.suggested_corrections


# ---------------------------------------------------------------------------
# HierarchicalTypification model tests
# ---------------------------------------------------------------------------

def test_hierarchical_typification_success():
    """
    A correct combination must instantiate without ValidationError and expose
    convenient helpers (.hierarchy_path & .as_dict)
    """
    typ = models.HierarchicalTypification(
        unidade_negocio=models.UnidadeNegocio.ADQUIRENCIA_WEB,
        produto="Antecipação de Vendas",
        motivo="Dúvidas sobre a Antecipação de Vendas",
        submotivo="Cliente orientado sobre a Antecipação de Vendas",
    )
    assert "Cliente orientado sobre a Antecipação de Vendas" in typ.hierarchy_path
    assert typ.as_dict["Submotivo"] == "Cliente orientado sobre a Antecipação de Vendas"
    assert typ.as_dict["Conclusão"] == "Orientação"


def test_hierarchical_typification_invalid_submotive():
    """
    An invalid submotive for an otherwise valid path must raise pydantic.ValidationError.
    """
    with pytest.raises(ValidationError) as exc:
        models.HierarchicalTypification(
            unidade_negocio=models.UnidadeNegocio.ADQUIRENCIA_WEB,
            produto="Antecipação de Vendas",
            motivo="Dúvidas sobre a Antecipação de Vendas",
            submotivo="Outro submotivo inválido",  # not in patched hierarchy
        )
    # The message should clearly mention the invalid submotivo
    assert "Submotivo 'Outro submotivo inválido' inválido" in str(exc.value)


def test_hierarchical_typification_invalid_product():
    """Invalid product should raise ValidationError with clear message"""
    with pytest.raises(ValidationError) as exc:
        models.HierarchicalTypification(
            unidade_negocio=models.UnidadeNegocio.EMISSAO,
            produto="Produto Inexistente",
            motivo="Uso do cartão",
            submotivo="Como recarregar o cartão",
        )
    assert "Produto 'Produto Inexistente' inválido" in str(exc.value)


def test_hierarchical_typification_invalid_motive():
    """Invalid motive should raise ValidationError with valid options"""
    with pytest.raises(ValidationError) as exc:
        models.HierarchicalTypification(
            unidade_negocio=models.UnidadeNegocio.EMISSAO,
            produto="Cartão Pré-Pago",
            motivo="Motivo Inexistente",
            submotivo="Como recarregar o cartão",
        )
    assert "Motivo 'Motivo Inexistente' inválido" in str(exc.value)


# ---------------------------------------------------------------------------
# Hierarchy utility functions tests
# ---------------------------------------------------------------------------

def test_get_valid_products():
    """get_valid_products should return correct products for business unit"""
    products = models.get_valid_products("Adquirência Web")
    assert "Antecipação de Vendas" in products
    assert len(products) == 1

    products_emissao = models.get_valid_products("Emissão")
    assert "Cartão Pré-Pago" in products_emissao
    assert "Cartão da Conta (débito)" in products_emissao


def test_get_valid_motives():
    """get_valid_motives should return correct motives for business unit and product"""
    motives = models.get_valid_motives("Adquirência Web", "Antecipação de Vendas")
    expected_motives = [
        "Dúvidas sobre a Antecipação de Vendas",
        "Dúvidas sobre a Antecipação Agendada",
        "Cliente deseja fazer a Antecipação de Vendas",
        "Dúvidas sobre a Antecipação"
    ]
    for motive in expected_motives:
        assert motive in motives


def test_get_valid_submotives():
    """get_valid_submotives should return correct submotives for complete path"""
    submotives = models.get_valid_submotives(
        "Adquirência Web",
        "Antecipação de Vendas", 
        "Dúvidas sobre a Antecipação de Vendas"
    )
    assert "Cliente orientado sobre a Antecipação de Vendas" in submotives


def test_hierarchy_utilities_empty_results():
    """Utility functions should handle invalid inputs gracefully"""
    assert models.get_valid_products("Unidade Inexistente") == []
    assert models.get_valid_motives("Unidade Inexistente", "Produto") == []
    assert models.get_valid_submotives("Unidade", "Produto", "Motivo") == []


# ---------------------------------------------------------------------------
# ConversationTypificationWorkflow tests
# ---------------------------------------------------------------------------

def test_workflow_initialization(mock_storage):
    """Workflow should initialize with proper hierarchy and storage"""
    workflow = wf_mod.ConversationTypificationWorkflow(
        workflow_id="test-workflow",
        storage=mock_storage
    )
    assert workflow.hierarchy is not None
    assert len(workflow.hierarchy) > 0
    assert workflow.business_unit_classifier is not None


def test_create_ticket_assigns_correct_team_and_format(mock_storage):
    """
    _create_ticket must:
      • embed session_id in the ticket_id with yyyyMMddHHmmss timestamp
      • map business unit to the correct support team
    """
    workflow = wf_mod.ConversationTypificationWorkflow(
        workflow_id="test",
        storage=mock_storage
    )

    typ = models.HierarchicalTypification(
        unidade_negocio=models.UnidadeNegocio.EMISSAO,
        produto="Cartão Pré-Pago",
        motivo="Uso do cartão",
        submotivo="Como recarregar o cartão",
    )

    ticket = workflow._create_ticket(
        session_id="test-session",
        typification=typ,
        conversation_history="Cliente pergunta sobre recarga",
        customer_id="c123",
    )

    assert ticket.assigned_team == "emissao_team"
    assert ticket.typification_data["Produto"] == "Cartão Pré-Pago"
    # ticket_id pattern: TKT-test-session-YYYYMMDDHHMMSS
    assert re.fullmatch(r"TKT-test-session-\d{14}", ticket.ticket_id)
    assert ticket.success is True


def test_create_ticket_team_mapping(mock_storage):
    """Test that different business units map to correct teams"""
    workflow = wf_mod.ConversationTypificationWorkflow(
        workflow_id="test",
        storage=mock_storage
    )

    # Test PagBank mapping
    typ_pagbank = models.HierarchicalTypification(
        unidade_negocio=models.UnidadeNegocio.PAGBANK,
        produto="Conta Digital",
        motivo="Problemas de acesso",
        submotivo="App não abre",
    )

    ticket = workflow._create_ticket(
        session_id="test-session",
        typification=typ_pagbank,
        conversation_history="Cliente com problema no app",
    )

    assert ticket.assigned_team == "pagbank_team"


def test_product_classifier_contains_all_options_in_prompt(mock_storage):
    """
    The dynamically built product classifier must mention every valid product
    in its instructions section to ensure the agent receives the full option list.
    """
    workflow = wf_mod.ConversationTypificationWorkflow(
        workflow_id="test",
        storage=mock_storage
    )

    agent = workflow.create_product_classifier("Adquirência Web")
    
    # Check that the available product appears in instructions
    assert "Antecipação de Vendas" in agent.instructions
    assert "PRODUTOS VÁLIDOS" in agent.instructions


def test_motive_classifier_dynamic_creation(mock_storage):
    """Motive classifier should be created with context-specific instructions"""
    workflow = wf_mod.ConversationTypificationWorkflow(
        workflow_id="test",
        storage=mock_storage
    )

    agent = workflow.create_motive_classifier("Emissão", "Cartão Pré-Pago")
    
    assert "Uso do cartão" in agent.instructions
    assert "Cartão Pré-Pago" in agent.instructions
    assert "MOTIVOS VÁLIDOS" in agent.instructions


def test_submotive_classifier_final_level(mock_storage):
    """Submotive classifier should handle final classification level"""
    workflow = wf_mod.ConversationTypificationWorkflow(
        workflow_id="test",
        storage=mock_storage
    )

    agent = workflow.create_submotive_classifier(
        "Emissão", 
        "Cartão Pré-Pago", 
        "Uso do cartão"
    )
    
    assert "Como recarregar o cartão" in agent.instructions
    assert "Cobrança de mensalidade" in agent.instructions
    assert "SUBMOTIVOS VÁLIDOS" in agent.instructions


def test_save_typification_persists_to_session_state(mock_storage):
    """
    After calling _save_typification_result, the session_state dict must hold
    a serialised record of the ConversationTypification object.
    """
    workflow = wf_mod.ConversationTypificationWorkflow(
        workflow_id="test",
        storage=mock_storage
    )

    typ = models.HierarchicalTypification(
        unidade_negocio=models.UnidadeNegocio.ADQUIRENCIA_WEB,
        produto="Antecipação de Vendas",
        motivo="Dúvidas sobre a Antecipação de Vendas",
        submotivo="Cliente orientado sobre a Antecipação de Vendas",
    )

    conv_typ = models.ConversationTypification(
        session_id="s01",
        typification=typ,
        conversation_summary="Cliente tem dúvidas sobre antecipação",
        resolution_provided="Orientações fornecidas sobre processo",
        confidence_scores={"business_unit": 0.9, "product": 0.85},
        conversation_turns=2,
    )

    workflow._save_typification_result(conv_typ)

    saved = workflow.session_state["typification_results"]
    assert len(saved) == 1
    assert saved[0]["session_id"] == "s01"
    assert saved[0]["typification"]["produto"] == "Antecipação de Vendas"


# ---------------------------------------------------------------------------
# Pydantic model validation tests
# ---------------------------------------------------------------------------

def test_business_unit_selection_validation():
    """BusinessUnitSelection should validate confidence scores"""
    # Valid confidence
    selection = models.BusinessUnitSelection(
        unidade_negocio=models.UnidadeNegocio.ADQUIRENCIA_WEB,
        confidence=0.85,
        reasoning="Keywords indicate web acquisition"
    )
    assert selection.confidence == 0.85

    # Invalid confidence (too high)
    with pytest.raises(ValidationError):
        models.BusinessUnitSelection(
            unidade_negocio=models.UnidadeNegocio.ADQUIRENCIA_WEB,
            confidence=1.5,  # > 1.0
            reasoning="Test"
        )

    # Invalid confidence (negative)
    with pytest.raises(ValidationError):
        models.BusinessUnitSelection(
            unidade_negocio=models.UnidadeNegocio.ADQUIRENCIA_WEB,
            confidence=-0.1,  # < 0.0
            reasoning="Test"
        )


def test_conversation_typification_complete():
    """ConversationTypification should handle complete metadata"""
    typ = models.HierarchicalTypification(
        unidade_negocio=models.UnidadeNegocio.PAGBANK,
        produto="Conta Digital",
        motivo="Problemas de acesso",
        submotivo="App não abre",
    )

    conv_typ = models.ConversationTypification(
        session_id="session-123",
        customer_id="customer-456",
        ticket_id="TKT-session-123-20250714140000",
        typification=typ,
        conversation_summary="Cliente reportou que o app não abre no celular",
        resolution_provided="Orientações sobre reinstalação do app",
        confidence_scores={
            "business_unit": 0.95,
            "product": 0.88,
            "motive": 0.92,
            "submotive": 0.85
        },
        conversation_turns=4,
        resolution_time_minutes=3.5,
        escalated_to_human=False,
        started_at="2025-07-14T14:00:00Z",
        completed_at="2025-07-14T14:03:30Z"
    )

    assert conv_typ.session_id == "session-123"
    assert conv_typ.escalated_to_human is False
    assert conv_typ.resolution_time_minutes == 3.5
    assert len(conv_typ.confidence_scores) == 4


def test_ticket_creation_result_validation():
    """TicketCreationResult should validate required fields"""
    ticket = models.TicketCreationResult(
        ticket_id="TKT-123-20250714140000",
        action="created",
        status="resolved",
        assigned_team="pagbank_team",
        priority="high",
        typification_data={
            "Unidade de negócio": "PagBank",
            "Produto": "Conta Digital",
            "Motivo": "Problemas de acesso",
            "Submotivo": "App não abre",
            "Conclusão": "Orientação"
        }
    )

    assert ticket.success is True  # default value
    assert ticket.error_message is None  # default value
    assert ticket.priority == "high"


# ---------------------------------------------------------------------------
# Error handling and edge cases
# ---------------------------------------------------------------------------

def test_hierarchy_loading_file_not_found():
    """Test error handling when hierarchy.json is missing"""
    # Test the original load_hierarchy function without the fixture override
    with patch("builtins.open", side_effect=FileNotFoundError("No such file or directory")):
        with pytest.raises(FileNotFoundError):
            # Call the original function
            with open("ai/workflows/conversation_typification/hierarchy.json", "r", encoding="utf-8") as f:
                import json
                json.load(f)


def test_workflow_helper_methods(mock_storage):
    """Test workflow helper methods for conversation analysis"""
    workflow = wf_mod.ConversationTypificationWorkflow(
        workflow_id="test",
        storage=mock_storage
    )

    # Test conversation summary generation
    conversation = "Cliente: Meu cartão não chegou ainda\nAna: Vou verificar o status do seu cartão\nCliente: Obrigado"
    summary = workflow._generate_summary(conversation)
    assert "Cliente:" in summary
    assert len(summary) > 0

    # Test resolution extraction  
    resolution = workflow._extract_resolution(conversation)
    assert "Ana:" in resolution

    # Test turn counting
    turns = workflow._count_turns(conversation)
    assert turns == 3  # Three lines with ':'


def test_workflow_demo_mode_logging(mock_storage, monkeypatch):
    """Test demo mode logging functionality"""
    # Mock Rich console
    mock_console = Mock()
    monkeypatch.setenv("DEMO_MODE", "true")
    
    workflow = wf_mod.ConversationTypificationWorkflow(
        workflow_id="test",
        storage=mock_storage,
        debug_mode=True
    )
    workflow.console = mock_console

    # Test demo mode methods
    workflow._log_workflow_start("test-session", "Test conversation")
    mock_console.print.assert_called()

    workflow._log_step_start(1, "Business Unit Classification", ["Adquirência Web", "Emissão", "PagBank"])
    assert mock_console.print.call_count >= 2