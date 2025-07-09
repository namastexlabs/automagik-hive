"""
Comprehensive tests for PagBank Escalation Systems
Tests all components of the escalation layer
"""


import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from escalation_systems.escalation_manager import (
    EscalationDecision,
    create_escalation_manager,
)
from escalation_systems.escalation_types import EscalationTrigger
from escalation_systems.pattern_learner import create_pattern_learner

# Import escalation components
from escalation_systems.technical_escalation_agent import (
    TechnicalIssueCategory,
    create_technical_escalation_agent,
)
from escalation_systems.ticket_system import (
    TicketPriority,
    TicketStatus,
    TicketSystem,
    TicketType,
)


class TestTicketSystem(unittest.TestCase):
    """Test ticket system functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_file = "test_tickets.json"
        self.ticket_system = TicketSystem(self.test_file)
    
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
    
    def test_ticket_creation(self):
        """Test creating tickets"""
        ticket = self.ticket_system.create_ticket(
            customer_id="TEST001",
            issue_description="Meu cartão foi clonado urgente!",
            metadata={'source': 'test'}
        )
        
        self.assertIsNotNone(ticket.ticket_id)
        self.assertIsNotNone(ticket.protocol)
        self.assertEqual(ticket.priority, TicketPriority.CRITICAL)
        self.assertEqual(ticket.ticket_type, TicketType.SECURITY)
        self.assertEqual(ticket.status, TicketStatus.OPEN)
    
    def test_priority_classification(self):
        """Test automatic priority classification"""
        test_cases = [
            ("Fraude no meu cartão!", TicketPriority.CRITICAL),
            ("Não consigo fazer login", TicketPriority.HIGH),
            ("Tenho um problema com PIX", TicketPriority.MEDIUM),
            ("Sugestão de melhoria", TicketPriority.LOW)
        ]
        
        for description, expected_priority in test_cases:
            priority = self.ticket_system._classify_priority(description)
            self.assertEqual(priority, expected_priority, 
                           f"Failed for: {description}")
    
    def test_type_classification(self):
        """Test automatic type classification"""
        test_cases = [
            ("App travando toda hora", TicketType.TECHNICAL),
            ("Preciso atualizar meus dados", TicketType.ACCOUNT),
            ("PIX não está funcionando", TicketType.TRANSACTION),
            ("Perdi meu cartão", TicketType.CARD),
            ("Acho que fui hackeado", TicketType.SECURITY),
            ("Quero dar um feedback", TicketType.FEEDBACK),
            ("Péssimo atendimento", TicketType.COMPLAINT)
        ]
        
        for description, expected_type in test_cases:
            ticket_type = self.ticket_system._classify_type(description)
            self.assertEqual(ticket_type, expected_type,
                           f"Failed for: {description}")
    
    def test_ticket_update(self):
        """Test updating tickets"""
        # Create ticket
        ticket = self.ticket_system.create_ticket(
            customer_id="TEST002",
            issue_description="Problema com login"
        )
        
        # Update ticket
        success = self.ticket_system.update_ticket(
            ticket.ticket_id,
            status=TicketStatus.IN_PROGRESS,
            assigned_to="tech_team",
            update_message="Investigando o problema"
        )
        
        self.assertTrue(success)
        
        # Verify update
        updated_ticket = self.ticket_system.get_ticket(ticket.ticket_id)
        self.assertEqual(updated_ticket.status, TicketStatus.IN_PROGRESS)
        self.assertEqual(updated_ticket.assigned_to, "tech_team")
        self.assertTrue(len(updated_ticket.updates) > 1)
    
    def test_customer_tickets(self):
        """Test retrieving customer tickets"""
        customer_id = "TEST003"
        
        # Create multiple tickets
        for i in range(3):
            self.ticket_system.create_ticket(
                customer_id=customer_id,
                issue_description=f"Problema {i+1}"
            )
        
        # Get customer tickets
        tickets = self.ticket_system.get_customer_tickets(customer_id)
        self.assertEqual(len(tickets), 3)
        
        # Test with status filter
        open_tickets = self.ticket_system.get_customer_tickets(
            customer_id,
            status_filter=[TicketStatus.OPEN]
        )
        self.assertEqual(len(open_tickets), 3)
    
    def test_sla_violations(self):
        """Test SLA violation detection"""
        # Create a critical ticket
        ticket = self.ticket_system.create_ticket(
            customer_id="TEST004",
            issue_description="Fraude urgente!",
            priority=TicketPriority.CRITICAL
        )
        
        # Manually set creation time to past
        ticket.created_at = (datetime.now() - timedelta(hours=2)).isoformat()
        
        # Check violations
        violations = self.ticket_system.check_sla_violations()
        
        # Should have first response violation (critical = 1 hour)
        self.assertTrue(len(violations) > 0)
        self.assertEqual(violations[0]['type'], 'first_response')


class TestTechnicalEscalationAgent(unittest.TestCase):
    """Test technical escalation agent"""
    
    def setUp(self):
        """Set up test environment"""
        self.ticket_system = TicketSystem("test_tech_tickets.json")
        self.agent = create_technical_escalation_agent(self.ticket_system)
    
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists("test_tech_tickets.json"):
            os.remove("test_tech_tickets.json")
    
    def test_issue_categorization(self):
        """Test technical issue categorization"""
        test_cases = [
            ("App trava quando abro", TechnicalIssueCategory.APP_CRASH),
            ("Não consigo fazer login", TechnicalIssueCategory.LOGIN_ERROR),
            ("PIX falhou 3 vezes", TechnicalIssueCategory.TRANSACTION_FAILURE),
            ("App muito lento", TechnicalIssueCategory.PERFORMANCE_ISSUE),
            ("Erro código E123", TechnicalIssueCategory.FEATURE_BUG),
            ("Minha conta foi invadida", TechnicalIssueCategory.SECURITY_CONCERN)
        ]
        
        for description, expected_category in test_cases:
            category = self.agent._categorize_issue(description)
            self.assertEqual(category, expected_category,
                           f"Failed for: {description}")
    
    def test_severity_assessment(self):
        """Test severity assessment"""
        test_cases = [
            (TechnicalIssueCategory.SECURITY_CONCERN, "qualquer", "critical"),
            (TechnicalIssueCategory.TRANSACTION_FAILURE, "urgente", "high"),
            (TechnicalIssueCategory.APP_CRASH, "problema", "medium"),
            (TechnicalIssueCategory.PERFORMANCE_ISSUE, "lento", "low")
        ]
        
        for category, description, expected_severity in test_cases:
            severity = self.agent._assess_severity(category, description)
            self.assertEqual(severity, expected_severity,
                           f"Failed for: {category.value} - {description}")
    
    def test_escalation_requirement(self):
        """Test escalation requirement detection"""
        # Security issues should always escalate
        requires_escalation = self.agent._check_escalation_requirement(
            TechnicalIssueCategory.SECURITY_CONCERN,
            "Conta invadida",
            None
        )
        self.assertTrue(requires_escalation)
        
        # Critical keywords should trigger escalation
        requires_escalation = self.agent._check_escalation_requirement(
            TechnicalIssueCategory.TRANSACTION_FAILURE,
            "Transação não autorizada apareceu",
            None
        )
        self.assertTrue(requires_escalation)
        
        # Normal issues shouldn't escalate
        requires_escalation = self.agent._check_escalation_requirement(
            TechnicalIssueCategory.PERFORMANCE_ISSUE,
            "App está lento",
            None
        )
        self.assertFalse(requires_escalation)
    
    @patch('agno.agent.Agent.run')
    def test_handle_escalation(self, mock_run):
        """Test handling escalation"""
        mock_run.return_value = "Entendo seu problema técnico. Vou ajudar."
        
        context = {
            'frustration_level': 2,
            'interaction_count': 5,
            'routing_history': []
        }
        
        result = self.agent.handle_escalation(
            user_id="TEST005",
            message="App travando sempre",
            context=context
        )
        
        self.assertEqual(result['handled_by'], 'technical_escalation_agent')
        self.assertIn('response', result)
        self.assertIn('statistics', result)
        self.assertEqual(self.agent.stats['total_escalations'], 1)


class TestEscalationManager(unittest.TestCase):
    """Test escalation manager"""
    
    def setUp(self):
        """Set up test environment"""
        self.ticket_system = TicketSystem("test_escalation_tickets.json")
        self.manager = create_escalation_manager(ticket_system=self.ticket_system)
    
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists("test_escalation_tickets.json"):
            os.remove("test_escalation_tickets.json")
    
    def test_explicit_request_detection(self):
        """Test explicit human request detection"""
        test_messages = [
            "Quero falar com um humano",
            "PRECISO DE UM ATENDENTE",
            "não quero robô, quero pessoa",
            "Chama um humano por favor"
        ]
        
        for message in test_messages:
            is_explicit = self.manager._check_explicit_request(message)
            self.assertTrue(is_explicit, f"Failed for: {message}")
        
        # Test negative cases
        normal_messages = [
            "Como faço PIX?",
            "Qual meu saldo?",
            "Preciso de ajuda"
        ]
        
        for message in normal_messages:
            is_explicit = self.manager._check_explicit_request(message)
            self.assertFalse(is_explicit, f"Failed for: {message}")
    
    def test_security_concern_detection(self):
        """Test security concern detection"""
        security_messages = [
            "Minha conta foi invadida",
            "Tem uma transação estranha",
            "Acho que fui hackeado",
            "Meu cartão foi clonado"
        ]
        
        for message in security_messages:
            is_security = self.manager._check_security_concern(message)
            self.assertTrue(is_security, f"Failed for: {message}")
    
    def test_escalation_evaluation(self):
        """Test escalation evaluation logic"""
        # Test high frustration
        session_state = {
            'frustration_level': 3,
            'interaction_count': 5,
            'customer_context': {'failed_attempts': 1}
        }
        
        decision = self.manager.evaluate_escalation(
            session_state,
            "Estou muito irritado!"
        )
        
        self.assertTrue(decision.should_escalate)
        self.assertEqual(decision.trigger, EscalationTrigger.HIGH_FRUSTRATION)
        self.assertEqual(decision.target, 'human')
        
        # Test explicit request
        session_state = {
            'frustration_level': 1,
            'interaction_count': 2,
            'customer_context': {}
        }
        
        decision = self.manager.evaluate_escalation(
            session_state,
            "Quero falar com um atendente humano"
        )
        
        self.assertTrue(decision.should_escalate)
        self.assertEqual(decision.trigger, EscalationTrigger.EXPLICIT_REQUEST)
        
        # Test no escalation
        session_state = {
            'frustration_level': 0,
            'interaction_count': 1,
            'customer_context': {}
        }
        
        decision = self.manager.evaluate_escalation(
            session_state,
            "Como faço um PIX?"
        )
        
        self.assertFalse(decision.should_escalate)
    
    def test_priority_determination(self):
        """Test priority determination"""
        test_cases = [
            ("Problema de segurança detectado", TicketPriority.CRITICAL),
            ("Cliente com alta frustração", TicketPriority.HIGH),
            ("Bug técnico identificado", TicketPriority.HIGH),
            ("Timeout de interação", TicketPriority.MEDIUM)
        ]
        
        for reason, expected_priority in test_cases:
            priority = self.manager._determine_priority(reason, {})
            self.assertEqual(priority, expected_priority,
                           f"Failed for: {reason}")
    
    @patch('agno.agent.Agent.run')
    def test_handle_escalation_to_human(self, mock_run):
        """Test handling escalation to human"""
        mock_run.return_value = "Summary generated"
        
        decision = EscalationDecision(
            should_escalate=True,
            trigger=EscalationTrigger.EXPLICIT_REQUEST,
            target='human',
            reason='Customer requested human',
            priority=TicketPriority.HIGH
        )
        
        session_state = {
            'customer_id': 'TEST006',
            'frustration_level': 2,
            'interaction_count': 5
        }
        
        result = self.manager.handle_escalation(
            decision,
            session_state,
            "Quero falar com humano"
        )
        
        self.assertTrue(result['escalated'])
        self.assertEqual(result['target'], 'human')
        self.assertIn('ticket_id', result)
        self.assertIn('protocol', result)
        self.assertEqual(result['handled_by'], 'human_handoff')


class TestPatternLearner(unittest.TestCase):
    """Test pattern learning system"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_db = "test_patterns.db"
        self.learner = create_pattern_learner(self.test_db)
    
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_record_escalation(self):
        """Test recording escalation events"""
        session_state = {
            'customer_id': 'TEST007',
            'frustration_level': 3,
            'interaction_count': 8
        }
        
        escalation_id = self.learner.record_escalation(
            session_state=session_state,
            trigger=EscalationTrigger.HIGH_FRUSTRATION,
            target='human',
            message='Muito frustrado!'
        )
        
        self.assertIsNotNone(escalation_id)
        self.assertTrue(escalation_id.startswith('ESC-'))
    
    def test_update_outcome(self):
        """Test updating escalation outcomes"""
        # Record escalation
        escalation_id = self.learner.record_escalation(
            session_state={'customer_id': 'TEST008'},
            trigger=EscalationTrigger.TECHNICAL_BUG,
            target='technical',
            message='Bug no app'
        )
        
        # Update outcome
        self.learner.update_outcome(
            escalation_id=escalation_id,
            was_successful=True,
            resolution_time_minutes=25.5,
            customer_satisfaction=4,
            notes='Resolved by tech team'
        )
        
        # Verify in database
        cursor = self.learner.conn.cursor()
        cursor.execute(
            'SELECT was_successful FROM escalation_outcomes WHERE escalation_id = ?',
            (escalation_id,)
        )
        result = cursor.fetchone()
        self.assertEqual(result[0], 1)  # 1 = True
    
    def test_keyword_extraction(self):
        """Test keyword extraction"""
        test_messages = [
            ("Erro no sistema", ['technical:erro']),
            ("Possível fraude na conta", ['security:fraude']),
            ("Estou com muita raiva", ['frustration:raiva']),
            ("Preciso urgente", ['urgency:urgente'])
        ]
        
        for message, expected_keywords in test_messages:
            keywords = self.learner._extract_keywords(message)
            for expected in expected_keywords:
                self.assertIn(expected, keywords,
                             f"Expected '{expected}' in keywords for: {message}")
    
    def test_pattern_insights(self):
        """Test getting pattern insights"""
        # Create some test data
        for i in range(10):
            trigger = EscalationTrigger.HIGH_FRUSTRATION if i % 2 == 0 else EscalationTrigger.TECHNICAL_BUG
            target = 'human' if i % 3 == 0 else 'technical'
            
            esc_id = self.learner.record_escalation(
                session_state={'customer_id': f'TEST{i}', 'frustration_level': i % 4},
                trigger=trigger,
                target=target,
                message=f'Test message {i}'
            )
            
            # Update some outcomes
            if i % 2 == 0:
                self.learner.update_outcome(
                    escalation_id=esc_id,
                    was_successful=i % 3 != 0,
                    resolution_time_minutes=15 + i * 5
                )
        
        # Get insights
        insights = self.learner.get_pattern_insights()
        
        self.assertIn('trigger_statistics', insights)
        self.assertIn('resolution_times', insights)
        self.assertIsInstance(insights['total_patterns'], int)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete escalation system"""
    
    def setUp(self):
        """Set up integrated test environment"""
        self.ticket_system = TicketSystem("test_integration_tickets.json")
        self.pattern_learner = create_pattern_learner("test_integration_patterns.db")
        self.technical_agent = create_technical_escalation_agent(self.ticket_system)
        self.manager = create_escalation_manager(
            ticket_system=self.ticket_system,
            technical_agent=self.technical_agent,
            pattern_learner=self.pattern_learner
        )
    
    def tearDown(self):
        """Clean up test files"""
        for file in ["test_integration_tickets.json", "test_integration_patterns.db"]:
            if os.path.exists(file):
                os.remove(file)
    
    @patch('agno.agent.Agent.run')
    def test_full_escalation_flow(self, mock_run):
        """Test complete escalation flow from detection to resolution"""
        mock_run.return_value = "Problema técnico resolvido"
        
        # Simulate a customer interaction that needs escalation
        session_state = {
            'customer_id': 'INTEGRATION_TEST',
            'customer_name': 'Test Customer',
            'frustration_level': 2,
            'interaction_count': 8,
            'customer_context': {'failed_attempts': 3},
            'message_history': [
                'Não consigo fazer PIX',
                'Já tentei várias vezes',
                'O erro continua aparecendo'
            ],
            'routing_history': [
                {'topic': 'conta_digital', 'timestamp': datetime.now().isoformat()},
                {'topic': 'transaction_support', 'timestamp': datetime.now().isoformat()}
            ]
        }
        
        # Evaluate escalation need
        decision = self.manager.evaluate_escalation(
            session_state,
            "ERRO E5521 TODA VEZ QUE TENTO!"
        )
        
        self.assertTrue(decision.should_escalate)
        
        # Handle the escalation
        result = self.manager.handle_escalation(
            decision,
            session_state,
            "ERRO E5521 TODA VEZ QUE TENTO!"
        )
        
        self.assertTrue(result['escalated'])
        
        # Verify ticket was created
        tickets = self.ticket_system.get_customer_tickets('INTEGRATION_TEST')
        self.assertEqual(len(tickets), 1)
        
        # Verify pattern was recorded
        self.assertEqual(self.pattern_learner.conn.execute(
            'SELECT COUNT(*) FROM escalation_records'
        ).fetchone()[0], 1)
        
        # Get statistics
        stats = self.manager.get_statistics()
        self.assertEqual(stats['total_escalations'], 1)


def run_all_tests():
    """Run all tests"""
    unittest.main(verbosity=2)


if __name__ == '__main__':
    run_all_tests()