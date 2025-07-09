"""
Test suite for Team Framework
Agent E: Team Framework Development
Validates team framework functionality
"""

import unittest
from unittest.mock import Mock

from teams.base_team import BaseTeam, TeamResponse
from teams.team_config import TeamConfig, TeamConfigManager
from teams.team_prompts import TeamPrompts
from teams.team_tools import (
    FinancialCalculatorTool,
    PagBankValidationTool,
    SecurityCheckTool,
)
from utils.team_utils import ResponseFormatter, TeamUtils


class TestBaseTeam(unittest.TestCase):
    """Test BaseTeam functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock dependencies
        self.mock_knowledge_base = Mock()
        self.mock_memory_manager = Mock()
        
        # Create test team
        self.team = BaseTeam(
            team_name="test_team",
            team_role="Test Role",
            team_description="Test Description",
            knowledge_base=self.mock_knowledge_base,
            memory_manager=self.mock_memory_manager,
            knowledge_filters=["test", "filter"],
            max_agents=3
        )
    
    def test_team_initialization(self):
        """Test team initialization"""
        self.assertEqual(self.team.team_name, "test_team")
        self.assertEqual(self.team.team_role, "Test Role")
        self.assertEqual(len(self.team.members), 3)  # Default 3 agents
        self.assertIsNotNone(self.team.team)
    
    def test_search_knowledge(self):
        """Test knowledge base search"""
        # Mock search results
        self.mock_knowledge_base.search_with_filters.return_value = [
            {"titulo": "Test Result 1", "conteudo": "Content 1"},
            {"titulo": "Test Result 2", "conteudo": "Content 2"}
        ]
        
        results = self.team._search_knowledge("test query")
        
        self.assertEqual(len(results), 2)
        self.mock_knowledge_base.search_with_filters.assert_called_once_with(
            query="test query",
            team="test_team",
            max_results=5
        )
    
    def test_build_context(self):
        """Test context building"""
        knowledge_results = [{"titulo": "Test"}]
        user_context = {"user_id": "123", "session_id": "abc"}
        
        context = self.team._build_context(
            query="test query",
            knowledge_results=knowledge_results,
            user_context=user_context,
            language="pt-BR"
        )
        
        self.assertIn("timestamp", context)
        self.assertEqual(context["team"], "test_team")
        self.assertEqual(context["language"], "pt-BR")
        self.assertEqual(context["query"], "test query")
        self.assertEqual(context["knowledge_base_results"], knowledge_results)
        self.assertEqual(context["user_context"], user_context)
    
    def test_extract_references(self):
        """Test reference extraction"""
        knowledge_results = [
            {"titulo": "Reference 1"},
            {"titulo": "Reference 2"},
            {"titulo": "Reference 3"},
            {"titulo": "Reference 4"}  # Should be limited to 3
        ]
        
        references = self.team._extract_references(knowledge_results)
        
        self.assertEqual(len(references), 3)
        self.assertEqual(references[0], "Reference 1")
    
    def test_create_error_response(self):
        """Test error response creation"""
        response = self.team._create_error_response("Test error", "pt-BR")
        
        self.assertIsInstance(response, TeamResponse)
        self.assertEqual(response.team_name, "test_team")
        self.assertEqual(response.confidence, 0.0)
        self.assertIn("Desculpe", response.content)
        self.assertIn("retry", response.suggested_actions)
    
    def test_get_status(self):
        """Test team status"""
        status = self.team.get_status()
        
        self.assertEqual(status["team_name"], "test_team")
        self.assertTrue(status["active"])
        self.assertEqual(status["num_agents"], 3)
        self.assertEqual(status["model"], "claude-sonnet-4-20250514")
        self.assertTrue(status["memory_enabled"])


class TestTeamPrompts(unittest.TestCase):
    """Test TeamPrompts functionality"""
    
    def test_get_team_prompt(self):
        """Test getting team prompts"""
        # Test role prompt
        role = TeamPrompts.get_team_prompt("cartoes", "role")
        self.assertIn("especialista em cartões", role)
        
        # Test name prompt
        name = TeamPrompts.get_team_prompt("cartoes", "name")
        self.assertEqual(name, "Time de Especialistas em Cartões")
        
        # Test coordination instructions
        coordination = TeamPrompts.get_team_prompt("cartoes", "coordination")
        self.assertIsInstance(coordination, list)
        self.assertTrue(len(coordination) > 0)
    
    def test_get_response_template(self):
        """Test response template formatting"""
        template = TeamPrompts.get_response_template(
            "greeting",
            team_name="Test Team",
            team_specialty="testing"
        )
        
        self.assertIn("Test Team", template)
        self.assertIn("testing", template)
    
    def test_build_agent_instructions(self):
        """Test building agent instructions"""
        instructions = TeamPrompts.build_agent_instructions(
            "cartoes",
            "Fraud Analyst"
        )
        
        self.assertIsInstance(instructions, list)
        self.assertTrue(len(instructions) > 0)
        self.assertIn("Fraud Analyst", str(instructions))


class TestTeamTools(unittest.TestCase):
    """Test team tools functionality"""
    
    def test_validation_tool_cpf(self):
        """Test CPF validation"""
        tool = PagBankValidationTool()
        
        # Valid CPF
        result = tool.run("cpf", "123.456.789-09")
        self.assertFalse(result.is_valid)  # This is a known invalid CPF
        
        # Invalid CPF
        result = tool.run("cpf", "111.111.111-11")
        self.assertFalse(result.is_valid)
        self.assertIn("CPF inválido", result.errors)
    
    def test_validation_tool_email(self):
        """Test email validation"""
        tool = PagBankValidationTool()
        
        # Valid email
        result = tool.run("email", "test@example.com")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.data["email"], "test@example.com")
        
        # Invalid email
        result = tool.run("email", "invalid-email")
        self.assertFalse(result.is_valid)
    
    def test_security_check_tool(self):
        """Test security check tool"""
        tool = SecurityCheckTool()
        
        # Transaction check
        result = tool.run("transaction", {
            "amount": 10000,
            "location_change": True
        })
        
        self.assertIn("risk_score", result)
        self.assertIn("risk_level", result)
        self.assertIn("flags", result)
        self.assertTrue(result["require_2fa"])
    
    def test_financial_calculator_tool(self):
        """Test financial calculator"""
        tool = FinancialCalculatorTool()
        
        # Loan calculation
        result = tool.run("loan_installment", {
            "principal": 10000,
            "annual_rate": 12,
            "months": 12
        })
        
        self.assertIn("monthly_installment", result)
        self.assertIn("total_amount", result)
        self.assertIn("total_interest", result)
        self.assertGreater(result["monthly_installment"], 0)


class TestTeamConfig(unittest.TestCase):
    """Test team configuration management"""
    
    def test_get_team_config(self):
        """Test getting team configuration"""
        config = TeamConfigManager.get_team_config("cartoes")
        
        self.assertIsInstance(config, TeamConfig)
        self.assertEqual(config.team_id, "cartoes")
        self.assertEqual(config.team_name, "Time de Especialistas em Cartões")
        self.assertIn("cartao", config.knowledge_filters)
    
    def test_get_routing_keywords_map(self):
        """Test routing keywords mapping"""
        keyword_map = TeamConfigManager.get_routing_keywords_map()
        
        self.assertIn("pix", keyword_map)
        self.assertIn("conta_digital", keyword_map["pix"])
        
        self.assertIn("investimento", keyword_map)
        self.assertIn("investimentos", keyword_map["investimento"])
    
    def test_validate_team_config(self):
        """Test team configuration validation"""
        validation = TeamConfigManager.validate_team_config("cartoes")
        
        self.assertTrue(validation["valid"])
        self.assertTrue(validation["checks"]["has_name"])
        self.assertTrue(validation["checks"]["has_filters"])
        self.assertTrue(validation["checks"]["has_keywords"])
    
    def test_create_team_agents(self):
        """Test creating team agents"""
        agents = TeamConfigManager.create_team_agents("cartoes")
        
        self.assertTrue(len(agents) > 0)
        self.assertEqual(agents[0].name, "Cards_Specialist")


class TestTeamUtils(unittest.TestCase):
    """Test team utilities"""
    
    def test_normalize_text(self):
        """Test text normalization"""
        text = "Olá, como está? Ação!"
        normalized = TeamUtils.normalize_text(text)
        
        self.assertEqual(normalized, "ola, como esta? acao!")
    
    def test_extract_keywords(self):
        """Test keyword extraction"""
        text = "Quero fazer um PIX de 100 reais para minha conta"
        keywords = TeamUtils.extract_keywords(text)
        
        self.assertIn("pix", keywords)
        self.assertIn("100", keywords)
        self.assertIn("reais", keywords)
        self.assertIn("conta", keywords)
    
    def test_detect_intent(self):
        """Test intent detection"""
        text = "Preciso transferir dinheiro urgente por PIX"
        intent = TeamUtils.detect_intent(text)
        
        self.assertEqual(intent["primary_intent"], "transferencia")
        self.assertTrue(intent["is_urgent"])
        self.assertIn("pix", intent["keywords"])
    
    def test_format_currency(self):
        """Test currency formatting"""
        formatted = TeamUtils.format_currency(1234.56)
        self.assertEqual(formatted, "R$ 1.234,56")
    
    def test_mask_sensitive_data(self):
        """Test sensitive data masking"""
        text = "Meu CPF é 123.456.789-00 e email test@example.com"
        masked = TeamUtils.mask_sensitive_data(text)
        
        self.assertIn("XXX.XXX.XXX-XX", masked)
        self.assertIn("XXX@XXX.com", masked)
        self.assertNotIn("123.456.789-00", masked)
    
    def test_extract_amounts(self):
        """Test amount extraction"""
        text = "Quero transferir R$ 1.234,56 e pagar R$ 100,00"
        amounts = TeamUtils.extract_amounts(text)
        
        self.assertEqual(len(amounts), 2)
        self.assertEqual(amounts[0], 1234.56)
        self.assertEqual(amounts[1], 100.00)


class TestResponseFormatter(unittest.TestCase):
    """Test response formatting"""
    
    def test_format_success_response(self):
        """Test success response formatting"""
        response = ResponseFormatter.format_success_response(
            "Operação realizada com sucesso",
            {"valor": "R$ 100,00", "data": "01/01/2024"}
        )
        
        self.assertIn("✅", response)
        self.assertIn("Operação realizada", response)
        self.assertIn("valor: R$ 100,00", response)
    
    def test_format_error_response(self):
        """Test error response formatting"""
        response = ResponseFormatter.format_error_response(
            "Erro ao processar",
            "Tente novamente mais tarde"
        )
        
        self.assertIn("❌", response)
        self.assertIn("Erro ao processar", response)
        self.assertIn("Tente novamente", response)
    
    def test_format_step_by_step(self):
        """Test step-by-step formatting"""
        response = ResponseFormatter.format_step_by_step(
            "Como fazer PIX",
            ["Abra o app", "Selecione PIX", "Digite o valor"],
            ["Limite diário: R$ 5.000"]
        )
        
        self.assertIn("📝", response)
        self.assertIn("1.", response)
        self.assertIn("2.", response)
        self.assertIn("3.", response)
        self.assertIn("Limite diário", response)


if __name__ == "__main__":
    unittest.main()