"""
Technical Escalation Agent for PagBank Multi-Agent System
Handles complex technical issues, bug reports, and system problems
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from agno.agent import Agent
from agno.memory.v2.memory import Memory
from agno.models.anthropic import Claude
from agno.tools import tool

# Import ticket system
from .ticket_system import Ticket, TicketPriority, TicketManager, TicketType


class TechnicalIssueCategory(Enum):
    """Categories of technical issues"""
    APP_CRASH = "app_crash"
    LOGIN_ERROR = "login_error"
    TRANSACTION_FAILURE = "transaction_failure"
    PERFORMANCE_ISSUE = "performance_issue"
    FEATURE_BUG = "feature_bug"
    SECURITY_CONCERN = "security_concern"
    API_ERROR = "api_error"
    DATA_INCONSISTENCY = "data_inconsistency"
    INTEGRATION_PROBLEM = "integration_problem"
    UNKNOWN = "unknown"


class TechnicalEscalationAgent:
    """
    Agent specialized in handling technical escalations
    Provides technical support, bug triage, and escalation protocols
    """
    
    def __init__(self, ticket_system: Optional[TicketManager] = None, 
                 memory: Optional[Memory] = None):
        """
        Initialize Technical Escalation Agent
        
        Args:
            ticket_system: Ticket management system
            memory: Memory system for pattern tracking
        """
        self.ticket_system = ticket_system or TicketManager()
        self.memory = memory
        
        # Knowledge base of common issues and solutions
        self.knowledge_base = self._initialize_knowledge_base()
        
        # Create specialized agent with tools
        self.agent = self._create_agent()
        
        # Statistics tracking
        self.stats = {
            'total_escalations': 0,
            'resolved_internally': 0,
            'escalated_to_human': 0,
            'categories': {}
        }
    
    def _initialize_knowledge_base(self) -> Dict[str, Any]:
        """Initialize technical knowledge base"""
        return {
            'common_solutions': {
                'app_crash': [
                    "Reiniciar o aplicativo",
                    "Verificar atualizações disponíveis", 
                    "Limpar cache do aplicativo",
                    "Reinstalar o aplicativo"
                ],
                'login_error': [
                    "Verificar conexão com internet",
                    "Resetar senha",
                    "Verificar se CPF está correto",
                    "Aguardar 30 minutos (bloqueio temporário)"
                ],
                'transaction_failure': [
                    "Verificar saldo disponível",
                    "Confirmar dados do destinatário",
                    "Verificar limites diários",
                    "Tentar novamente em alguns minutos"
                ],
                'performance_issue': [
                    "Verificar espaço disponível no dispositivo",
                    "Fechar outros aplicativos",
                    "Reiniciar o dispositivo",
                    "Verificar velocidade da internet"
                ]
            },
            'diagnostic_questions': {
                'app_crash': [
                    "Em qual tela o aplicativo está travando?",
                    "Qual versão do aplicativo você está usando?",
                    "Qual modelo do seu celular?",
                    "O erro começou após alguma atualização?"
                ],
                'login_error': [
                    "Você consegue acessar pelo site?",
                    "Aparece alguma mensagem de erro específica?",
                    "Você tentou resetar sua senha?",
                    "Houve tentativas de login recentes?"
                ],
                'transaction_failure': [
                    "Qual tipo de transação está falhando?",
                    "Aparece algum código de erro?",
                    "O valor foi debitado da conta?",
                    "Isso acontece com todos os tipos de transação?"
                ]
            }
        }
    
    def _create_agent(self) -> Agent:
        """Create the technical escalation agent with specialized tools"""
        
        # Tool for analyzing technical issues
        @tool
        def analyze_technical_issue(issue_description: str, 
                                  error_messages: Optional[List[str]] = None,
                                  device_info: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
            """
            Analyze technical issue and provide diagnostic information
            
            Args:
                issue_description: Description of the technical problem
                error_messages: Any error messages shown
                device_info: Device and app information
                
            Returns:
                Analysis results with category and recommendations
            """
            # Categorize the issue
            category = self._categorize_issue(issue_description, error_messages)
            
            # Get relevant solutions
            solutions = self.knowledge_base['common_solutions'].get(
                category.value, 
                ["Problema não catalogado - escalonamento necessário"]
            )
            
            # Get diagnostic questions
            questions = self.knowledge_base['diagnostic_questions'].get(
                category.value,
                ["Pode fornecer mais detalhes sobre o problema?"]
            )
            
            # Check if issue requires immediate escalation
            requires_escalation = self._check_escalation_requirement(
                category, issue_description, error_messages
            )
            
            return {
                'category': category.value,
                'severity': self._assess_severity(category, issue_description),
                'solutions': solutions,
                'diagnostic_questions': questions,
                'requires_escalation': requires_escalation,
                'technical_details': {
                    'error_messages': error_messages,
                    'device_info': device_info,
                    'timestamp': datetime.now().isoformat()
                }
            }
        
        # Tool for creating technical support tickets
        @tool
        def create_technical_ticket(customer_id: str,
                                   issue_description: str,
                                   category: str,
                                   priority: str = "medium",
                                   technical_details: Optional[Dict] = None) -> Dict[str, Any]:
            """
            Create a technical support ticket
            
            Args:
                customer_id: Customer identifier
                issue_description: Detailed issue description
                category: Issue category
                priority: Ticket priority (low, medium, high, critical)
                technical_details: Additional technical information
                
            Returns:
                Created ticket information
            """
            # Map priority string to enum
            priority_map = {
                "low": TicketPriority.LOW,
                "medium": TicketPriority.MEDIUM,
                "high": TicketPriority.HIGH,
                "critical": TicketPriority.CRITICAL
            }
            
            ticket_priority = priority_map.get(priority, TicketPriority.MEDIUM)
            
            # Create the ticket
            ticket = self.ticket_system.create_ticket(
                customer_id=customer_id,
                issue_description=issue_description,
                priority=ticket_priority,
                ticket_type=TicketType.TECHNICAL,
                metadata={
                    'category': category,
                    'technical_details': technical_details or {},
                    'agent': 'technical_escalation',
                    'created_at': datetime.now().isoformat()
                }
            )
            
            # Generate response protocol
            protocol = self._generate_technical_protocol(ticket)
            
            return {
                'ticket_id': ticket.ticket_id,
                'status': ticket.status.value,
                'priority': ticket.priority.value,
                'protocol': protocol,
                'estimated_resolution': self._estimate_resolution_time(ticket_priority)
            }
        
        # Tool for checking known issues
        @tool
        def check_known_issues(error_code: Optional[str] = None,
                              feature: Optional[str] = None) -> Dict[str, Any]:
            """
            Check for known issues and system status
            
            Args:
                error_code: Specific error code to check
                feature: Feature or service to check
                
            Returns:
                Known issues and status information
            """
            # In a real implementation, this would check a live status board
            known_issues = {
                'PIX': {
                    'status': 'operational',
                    'last_incident': '2024-01-10',
                    'message': 'Sistema PIX operando normalmente'
                },
                'APP': {
                    'status': 'operational',
                    'last_incident': '2024-01-08',
                    'message': 'Aplicativo funcionando normalmente'
                },
                'CARDS': {
                    'status': 'partial_outage',
                    'last_incident': '2024-01-11',
                    'message': 'Intermitência na aprovação de transações internacionais'
                }
            }
            
            if feature and feature.upper() in known_issues:
                return known_issues[feature.upper()]
            
            return {
                'status': 'all_operational',
                'message': 'Todos os sistemas operando normalmente',
                'known_issues': []
            }
        
        # Create the agent
        agent = Agent(
            name="Technical Escalation Specialist",
            role="Especialista em Escalonamento Técnico do PagBank",
            model=Claude(id="claude-sonnet-4-20250514"),
            tools=[analyze_technical_issue, create_technical_ticket, check_known_issues],
            instructions=[
                "Você é um especialista técnico do PagBank responsável por resolver problemas complexos.",
                "Analise problemas técnicos de forma sistemática e profissional.",
                "Sempre tente resolver o problema antes de escalonar.",
                "Forneça soluções claras e passo a passo em português brasileiro.",
                "Se não conseguir resolver, crie um ticket detalhado para a equipe técnica.",
                "Seja empático e reconheça a frustração do cliente com problemas técnicos.",
                "Use linguagem simples, evitando jargões técnicos desnecessários.",
                "Sempre forneça um protocolo de atendimento ao criar tickets."
            ],
            markdown=True,
            show_tool_calls=True
        )
        
        return agent
    
    def _categorize_issue(self, description: str, 
                         error_messages: Optional[List[str]] = None) -> TechnicalIssueCategory:
        """Categorize technical issue based on description and errors"""
        description_lower = description.lower()
        
        # Check for specific patterns
        if any(word in description_lower for word in ['trava', 'fecha', 'crash', 'reinicia']):
            return TechnicalIssueCategory.APP_CRASH
        elif any(word in description_lower for word in ['login', 'senha', 'acesso', 'entrar']):
            return TechnicalIssueCategory.LOGIN_ERROR
        elif any(word in description_lower for word in ['pix', 'transferência', 'pagamento', 'transação']):
            return TechnicalIssueCategory.TRANSACTION_FAILURE
        elif any(word in description_lower for word in ['lento', 'demora', 'travando', 'performance']):
            return TechnicalIssueCategory.PERFORMANCE_ISSUE
        elif any(word in description_lower for word in ['erro', 'bug', 'problema', 'não funciona']):
            return TechnicalIssueCategory.FEATURE_BUG
        elif any(word in description_lower for word in ['segurança', 'fraude', 'invasão', 'suspeito']):
            return TechnicalIssueCategory.SECURITY_CONCERN
        elif any(word in description_lower for word in ['api', 'integração', 'webhook']):
            return TechnicalIssueCategory.API_ERROR
        elif any(word in description_lower for word in ['saldo', 'valor', 'divergência', 'diferente']):
            return TechnicalIssueCategory.DATA_INCONSISTENCY
        
        return TechnicalIssueCategory.UNKNOWN
    
    def _assess_severity(self, category: TechnicalIssueCategory, description: str) -> str:
        """Assess issue severity"""
        high_severity_keywords = ['urgente', 'crítico', 'parado', 'bloqueado', 'fraude', 'roubo']
        medium_severity_keywords = ['problema', 'erro', 'falha', 'não consigo']
        
        description_lower = description.lower()
        
        if category == TechnicalIssueCategory.SECURITY_CONCERN:
            return "critical"
        elif any(word in description_lower for word in high_severity_keywords):
            return "high"
        elif category in [TechnicalIssueCategory.TRANSACTION_FAILURE, 
                         TechnicalIssueCategory.LOGIN_ERROR]:
            return "high"
        elif any(word in description_lower for word in medium_severity_keywords):
            return "medium"
        
        return "low"
    
    def _check_escalation_requirement(self, category: TechnicalIssueCategory,
                                     description: str,
                                     error_messages: Optional[List[str]]) -> bool:
        """Check if issue requires immediate escalation"""
        # Security issues always escalate
        if category == TechnicalIssueCategory.SECURITY_CONCERN:
            return True
        
        # Check for critical keywords
        critical_keywords = ['fraude', 'invasão', 'dados vazados', 'conta invadida', 
                           'transação não autorizada', 'valor errado']
        
        if any(keyword in description.lower() for keyword in critical_keywords):
            return True
        
        # Check error messages for critical patterns
        if error_messages:
            critical_errors = ['SECURITY_BREACH', 'UNAUTHORIZED_ACCESS', 'DATA_CORRUPTION']
            for error in error_messages:
                if any(critical in error.upper() for critical in critical_errors):
                    return True
        
        return False
    
    def _generate_technical_protocol(self, ticket: Ticket) -> str:
        """Generate technical support protocol"""
        # Format: TECH-YYYYMMDD-XXXXX
        date_str = datetime.now().strftime("%Y%m%d")
        ticket_number = ticket.ticket_id.split('-')[-1]
        return f"TECH-{date_str}-{ticket_number}"
    
    def _estimate_resolution_time(self, priority: TicketPriority) -> str:
        """Estimate resolution time based on priority"""
        estimates = {
            TicketPriority.CRITICAL: "1-2 horas",
            TicketPriority.HIGH: "4-6 horas",
            TicketPriority.MEDIUM: "24-48 horas",
            TicketPriority.LOW: "3-5 dias úteis"
        }
        return estimates.get(priority, "24-48 horas")
    
    def handle_escalation(self, user_id: str, 
                         message: str,
                         context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle technical escalation from main orchestrator
        
        Args:
            user_id: User identifier
            message: User message
            context: Escalation context including session state
            
        Returns:
            Escalation handling result
        """
        self.stats['total_escalations'] += 1
        
        # Extract relevant context
        frustration_level = context.get('frustration_level', 0)
        interaction_count = context.get('interaction_count', 0)
        previous_attempts = context.get('routing_history', [])
        
        # Build enhanced prompt
        enhanced_prompt = self._build_enhanced_prompt(
            message, frustration_level, interaction_count, previous_attempts
        )
        
        # Process with agent
        response = self.agent.run(enhanced_prompt)
        
        # Track statistics
        if "escalonamento humano" in str(response).lower():
            self.stats['escalated_to_human'] += 1
        else:
            self.stats['resolved_internally'] += 1
        
        # Store pattern if memory available
        if self.memory:
            self._store_escalation_pattern(user_id, message, context, response)
        
        return {
            'response': response,
            'handled_by': 'technical_escalation_agent',
            'statistics': self.stats.copy()
        }
    
    def _build_enhanced_prompt(self, message: str, 
                              frustration_level: int,
                              interaction_count: int,
                              previous_attempts: List[Dict]) -> str:
        """Build enhanced prompt with context"""
        prompt = f"[CONTEXTO DO ESCALONAMENTO]\n"
        prompt += f"Nível de frustração: {frustration_level}/3\n"
        prompt += f"Número de interações: {interaction_count}\n"
        
        if previous_attempts:
            prompt += f"Tentativas anteriores: {len(previous_attempts)}\n"
            last_topic = previous_attempts[-1].get('topic', 'unknown')
            prompt += f"Último tópico: {last_topic}\n"
        
        prompt += f"\n[MENSAGEM DO CLIENTE]\n{message}"
        
        return prompt
    
    def _store_escalation_pattern(self, user_id: str, message: str,
                                 context: Dict[str, Any], response: Any):
        """Store escalation pattern for learning"""
        # This would integrate with the pattern learner
        pattern = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'frustration_level': context.get('frustration_level', 0),
            'category': self._categorize_issue(message).value,
            'resolved_internally': "escalonamento humano" not in str(response).lower()
        }
        
        # Store in memory if available
        if self.memory:
            # Memory storage would be handled here
            pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            'total_escalations': self.stats['total_escalations'],
            'resolved_internally': self.stats['resolved_internally'],
            'escalated_to_human': self.stats['escalated_to_human'],
            'resolution_rate': (
                self.stats['resolved_internally'] / self.stats['total_escalations']
                if self.stats['total_escalations'] > 0 else 0
            ),
            'categories': self.stats.get('categories', {})
        }


def create_technical_escalation_agent(ticket_system: Optional[TicketManager] = None,
                                     memory: Optional[Memory] = None) -> TechnicalEscalationAgent:
    """
    Create and return technical escalation agent instance
    
    Args:
        ticket_system: Ticket management system
        memory: Memory system for pattern tracking
        
    Returns:
        Configured technical escalation agent
    """
    return TechnicalEscalationAgent(ticket_system, memory)


if __name__ == '__main__':
    # Test the technical escalation agent
    print("=== PagBank Technical Escalation Agent Test ===")
    
    agent = create_technical_escalation_agent()
    
    # Test scenarios
    test_cases = [
        {
            'user_id': 'test_user_1',
            'message': "MEU APP ESTÁ TRAVANDO TODA HORA! JÁ TENTEI DE TUDO!",
            'context': {
                'frustration_level': 3,
                'interaction_count': 5,
                'routing_history': [
                    {'topic': 'conta_digital', 'timestamp': '2024-01-11T10:00:00'},
                    {'topic': 'tech_support', 'timestamp': '2024-01-11T10:05:00'}
                ]
            }
        },
        {
            'user_id': 'test_user_2',
            'message': "Não consigo fazer PIX, aparece erro E4521",
            'context': {
                'frustration_level': 1,
                'interaction_count': 2,
                'routing_history': []
            }
        },
        {
            'user_id': 'test_user_3', 
            'message': "Acho que minha conta foi invadida! Tem transações que não fiz!",
            'context': {
                'frustration_level': 3,
                'interaction_count': 1,
                'routing_history': []
            }
        }
    ]
    
    for test in test_cases:
        print(f"\n{'='*50}")
        print(f"Testing: {test['message']}")
        print(f"Context: Frustration={test['context']['frustration_level']}, " +
              f"Interactions={test['context']['interaction_count']}")
        
        result = agent.handle_escalation(
            test['user_id'],
            test['message'],
            test['context']
        )
        
        print(f"Handled by: {result['handled_by']}")
        print(f"Statistics: {result['statistics']}")
    
    # Show final statistics
    print(f"\n{'='*50}")
    print("Final Statistics:")
    stats = agent.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")