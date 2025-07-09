# TODO: Action Agents Developer

## Objective
Implement specialized action agents for technical escalation, feedback collection, and human transfer simulation, with integrated memory for pattern learning and support tool creation.

## Technical Requirements
- [ ] Implement Technical Escalation Agent:
  - Automatic ticket creation with context
  - Problem categorization system
  - Priority assignment based on severity
  - Pattern tracking for recurring issues
- [ ] Create Feedback Collector Agent:
  - Feedback categorization (UI/UX, Products, Service)
  - Sentiment analysis
  - Trend identification
  - Aggregation of similar suggestions
- [ ] Build Human Agent (mock for demo):
  - Transfer protocol simulation
  - Context summary generation
  - Protocol number creation
  - Demo-friendly termination
- [ ] Implement support tools:
  - create_support_ticket() function
  - normalize_text() for Portuguese
  - generate_protocol() with timestamp
  - summarize_conversation() for handoff
- [ ] Configure memory for pattern learning
- [ ] Create escalation metrics tracking

## Code Structure
```python
pagbank/
  agents/
    technical_escalation.py      # Technical problem handler
    feedback_collector.py        # Feedback aggregator
    human_agent_mock.py         # Human transfer simulator
    action_tools.py             # Shared tool functions
  utils/
    ticket_system.py            # Ticket management
    protocol_generator.py       # Protocol creation
    conversation_summary.py     # Summary generation
```

## Research Required
- Agno Agent configuration for specialized tasks
- Tool creation and integration
- Memory pattern analysis
- Ticket system best practices
- Conversation summarization techniques

## Integration Points
- Input from: Main orchestrator (escalated cases)
- Uses: Memory system (pattern storage)
- Output to: Dashboard (ticket/feedback data)
- Critical for: Demo scenarios requiring escalation

## Testing Checklist
- [ ] Unit tests for ticket creation
- [ ] Integration test with orchestrator
- [ ] Pattern detection validation
- [ ] Feedback categorization accuracy
- [ ] Human transfer flow testing
- [ ] Protocol generation uniqueness
- [ ] Summary quality assessment
- [ ] Memory integration verification

## Deliverables
1. Three action agent implementations
2. Support tool library
3. Ticket/protocol generation system
4. Pattern learning reports
5. Integration test results

## Implementation Example
```python
from agno import Agent
from datetime import datetime
from typing import Dict, Optional
import hashlib

class ActionAgents:
    def __init__(self, memory, knowledge_base):
        self.memory = memory
        self.knowledge_base = knowledge_base
        
        # Create action agents
        self.technical_escalation = self._create_technical_agent()
        self.feedback_collector = self._create_feedback_agent()
        self.human_agent = self._create_human_agent()
    
    def _create_technical_agent(self) -> Agent:
        return Agent(
            name="Agente de Escalonamento Técnico",
            model=Claude("claude-sonnet-4-20250514"),
            instructions="""
            Você registra problemas técnicos e aprende padrões.
            
            PROCESSO:
            1. Identifique o tipo de problema
            2. Verifique se é recorrente (busque na memória)
            3. Crie protocolo técnico
            4. Classifique prioridade
            5. Registre para aprendizado futuro
            
            RESPOSTA PADRÃO:
            "Protocolo [NÚMERO] criado.
            [Se recorrente]: Este problema já foi reportado X vezes.
            Equipe técnica notificada com prioridade [ALTA/MÉDIA]."
            """,
            memory=self.memory,
            enable_user_memories=True,
            tools=[
                self.create_support_ticket,
                self.check_recurring_issue,
                self.generate_protocol
            ],
            markdown=True
        )
    
    def _create_feedback_agent(self) -> Agent:
        return Agent(
            name="Agente Coletor de Feedback",
            model=Claude("claude-sonnet-4-20250514"),
            instructions="""
            Você coleta e categoriza sugestões dos clientes.
            
            CATEGORIAS:
            - UI/UX: Interface e experiência
            - Produtos: Novos produtos ou melhorias
            - Atendimento: Qualidade do serviço
            
            PROCESSO:
            1. Categorize o feedback
            2. Busque sugestões similares
            3. Agrupe se aplicável
            4. Registre com prioridade
            
            RESPOSTA:
            "Sua sugestão sobre [TEMA] foi registrada!
            [Se similar existe]: Outros clientes também pediram isso.
            Obrigado por ajudar a melhorar o PagBank!"
            """,
            memory=self.memory,
            enable_user_memories=True,
            tools=[
                self.categorize_feedback,
                self.find_similar_feedback,
                self.aggregate_suggestions
            ],
            markdown=True
        )
    
    def _create_human_agent(self) -> Agent:
        return Agent(
            name="Agente Humano (Mock)",
            model=Claude("claude-sonnet-4-20250514"),
            instructions="""
            Você simula a transferência para atendimento humano.
            
            QUANDO ATIVADO:
            1. Crie resumo completo do atendimento
            2. Gere protocolo de transferência
            3. Mostre mensagem de transferência
            4. ENCERRE o fluxo (demo)
            
            MENSAGEM:
            "[NOME], vou te transferir agora para um especialista.
            Protocolo: [NÚMERO]
            Status: TRANSFERIDO PARA ATENDIMENTO HUMANO
            [DEMO: Atendimento automatizado encerrado]"
            """,
            tools=[
                self.summarize_conversation,
                self.generate_protocol,
                self.create_transfer_record
            ],
            markdown=True
        )
    
    # Support Tools
    def create_support_ticket(self, agent: Agent, issue: Dict) -> Dict:
        """Create a support ticket with full context"""
        ticket_id = self.generate_protocol("TECH")
        
        ticket = {
            "id": ticket_id,
            "type": issue.get("type", "technical"),
            "description": issue.get("description"),
            "customer_id": agent.session_state.get("customer_id"),
            "priority": self._calculate_priority(issue),
            "created_at": datetime.now().isoformat(),
            "status": "open",
            "recurring": self._check_recurrence(issue)
        }
        
        # Store in memory for pattern detection
        agent.memory.add(
            content=f"Technical issue: {issue['description']}",
            metadata={
                "type": "support_ticket",
                "ticket_id": ticket_id,
                "issue_type": issue.get("type")
            }
        )
        
        return ticket
    
    def check_recurring_issue(self, agent: Agent, issue_type: str) -> Dict:
        """Check if this issue has occurred before"""
        similar_issues = agent.memory.search(
            f"issue_type:{issue_type}",
            limit=10
        )
        
        count = len(similar_issues)
        patterns = self._analyze_patterns(similar_issues)
        
        return {
            "is_recurring": count > 2,
            "occurrence_count": count,
            "patterns": patterns,
            "priority_boost": count > 5
        }
    
    def generate_protocol(self, prefix: str = "PGB") -> str:
        """Generate unique protocol number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hash_suffix = hashlib.md5(timestamp.encode()).hexdigest()[:4].upper()
        return f"{prefix}-{timestamp}-{hash_suffix}"
    
    def categorize_feedback(self, feedback: str) -> Dict:
        """Categorize customer feedback"""
        categories = {
            "ui_ux": ["interface", "design", "botão", "tela", "app", "site"],
            "products": ["produto", "cartão", "conta", "investimento", "seguro"],
            "service": ["atendimento", "demora", "resposta", "ajuda", "suporte"]
        }
        
        feedback_lower = feedback.lower()
        detected_categories = []
        
        for category, keywords in categories.items():
            if any(keyword in feedback_lower for keyword in keywords):
                detected_categories.append(category)
        
        return {
            "categories": detected_categories or ["general"],
            "primary_category": detected_categories[0] if detected_categories else "general"
        }
    
    def summarize_conversation(self, agent: Agent) -> str:
        """Create conversation summary for handoff"""
        session_state = agent.session_state
        
        summary = f"""
        ## Resumo do Atendimento
        
        **Cliente**: {session_state.get('customer_name', 'Não identificado')}
        **ID**: {session_state.get('customer_id', 'N/A')}
        
        ### Histórico de Interações
        - Total de mensagens: {session_state.get('interaction_count', 0)}
        - Nível de frustração: {session_state.get('frustration_level', 0)}/3
        - Tópicos abordados: {', '.join(session_state.get('routing_history', []))}
        
        ### Problema Principal
        {session_state.get('current_topic', 'Não especificado')}
        
        ### Tentativas de Resolução
        {self._format_resolution_attempts(session_state)}
        
        ### Motivo da Transferência
        {self._get_transfer_reason(session_state)}
        """
        
        return summary
```

## Tool Functions Detail

### create_support_ticket
- Generate unique ticket ID
- Capture full conversation context
- Assign priority based on impact
- Track in memory for patterns

### normalize_text
- Fix common Portuguese misspellings
- Standardize informal language
- Preserve meaning and intent
- Handle regional variations

### generate_protocol
- Create unique identifiers
- Include timestamp for tracking
- Use standard format (PGB-YYYYMMDDHHMMSS-XXXX)
- Ensure no collisions

### summarize_conversation
- Extract key information
- Highlight unresolved issues
- Include customer sentiment
- Format for easy handoff

## Priority Items
1. Ticket creation must capture full context
2. Pattern detection for product improvement
3. Human transfer must feel natural
4. Feedback aggregation for insights
5. Protocol generation must be reliable