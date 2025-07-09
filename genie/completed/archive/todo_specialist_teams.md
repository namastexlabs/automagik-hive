# TODO: Specialist Teams Agent

## Objective
Implement 5 specialized teams (Cards, Digital Account, Investments, Credit, Insurance) with domain-specific knowledge, language adaptation, compliance requirements, and fraud detection capabilities.

## Technical Requirements
- [ ] Create 5 specialist teams with coordination mode
- [ ] Configure knowledge filters for each team:
  - Cards: area="cartoes"
  - Digital Account: area="conta_digital"
  - Investments: area="investimentos"
  - Credit: area="credito"
  - Insurance: area="seguros"
- [ ] Implement specialized prompts with language adaptation
- [ ] Add compliance warnings for investment team
- [ ] Implement fraud detection for credit team
- [ ] Configure memory access for learning
- [ ] Set up knowledge base search for each team
- [ ] Implement response formatting with markdown
- [ ] Add contextual examples in responses
- [ ] Create fallback responses for unknown queries

## Code Structure
```python
pagbank/
  teams/
    cards_team.py                # Cards specialist team
    digital_account_team.py      # Digital account team
    investments_team.py          # Investments team with compliance
    credit_team.py              # Credit team with fraud detection
    insurance_team.py           # Insurance team
    team_prompts.py            # Specialized prompts
    team_tools.py              # Shared team tools
```

## Research Required
- Agno Team coordination mode
- Knowledge filter configuration
- Agent tools for teams
- Compliance requirements for financial advice
- Fraud detection patterns
- Portuguese language adaptation strategies

## Integration Points
- Input from: Main orchestrator (routed queries)
- Depends on: Knowledge base (filtered information)
- Uses: Memory system (historical context)
- Output to: Customer (through orchestrator)

## Testing Checklist
- [ ] Unit tests for each team's responses
- [ ] Knowledge filter validation
- [ ] Language adaptation testing
- [ ] Compliance warning presence (investments)
- [ ] Fraud detection accuracy (credit)
- [ ] Integration with knowledge base
- [ ] Response time optimization
- [ ] Fallback response testing

## Deliverables
1. All 5 specialist team implementations
2. Knowledge filter configurations
3. Language adaptation examples
4. Compliance and fraud detection reports
5. Integration test results

## Implementation Example
```python
from agno import Agent, Team
from agno.knowledge.csv import CSVKnowledgeBase

class SpecialistTeams:
    def __init__(self, knowledge_base: CSVKnowledgeBase, memory):
        self.knowledge_base = knowledge_base
        self.memory = memory
        
        # Create all specialist teams
        self.cards_team = self._create_cards_team()
        self.digital_account_team = self._create_digital_account_team()
        self.investments_team = self._create_investments_team()
        self.credit_team = self._create_credit_team()
        self.insurance_team = self._create_insurance_team()
    
    def _create_cards_team(self) -> Agent:
        return Agent(
            name="Time de Especialistas em Cartões",
            model=Claude("claude-sonnet-4-20250514"),
            instructions="""
            Você é especialista em cartões PagBank.
            
            INSTRUÇÕES:
            1. Use search_knowledge para buscar informações específicas
            2. Sempre busque dados atualizados sobre taxas e prazos
            3. Para limite, busque "reserva_saldo" e "cdb_limite"
            
            LINGUAGEM:
            - Evite jargões bancários
            - Use exemplos práticos
            - Mencione prazos e custos claramente
            
            CONHECIMENTO PRIORITÁRIO:
            - Cartão Crédito: grátis, limite via reserva/CDB
            - Cartão Débito: grátis, internacional
            - Cartão Pré-pago: R$ 12,90, controle total
            """,
            knowledge=self.knowledge_base,
            search_knowledge=True,
            enable_agentic_knowledge_filters=True,
            knowledge_filters={
                "area": "cartoes",
                "tipo_produto": ["cartao_credito", "cartao_debito", "cartao_prepago"]
            },
            memory=self.memory,
            markdown=True,
            show_tool_calls=True
        )
    
    def _create_investments_team(self) -> Agent:
        return Agent(
            name="Time de Assessoria de Investimentos",
            model=Claude("claude-sonnet-4-20250514"),
            instructions="""
            Você é assessor de investimentos PagBank.
            
            OBRIGATÓRIO EM TODA RESPOSTA:
            "Esta não é uma recomendação de investimento. Avalie se os produtos são adequados ao seu perfil."
            
            BUSCA DE CONHECIMENTO:
            1. Para CDB+Limite: busque "cdb_limite_cartao"
            2. Para isenção IR: busque "lci_lca_isencao"
            3. Para FGC: busque "garantia_fgc"
            
            SIMPLIFICAÇÃO MÁXIMA:
            - CDB = "deixar dinheiro guardado com data"
            - Ações = "ser dono de um pedacinho da empresa"
            - FII = "investir em imóveis sem comprar"
            """,
            knowledge=self.knowledge_base,
            search_knowledge=True,
            enable_agentic_knowledge_filters=True,
            knowledge_filters={
                "area": "investimentos",
                "tipo_produto": ["cdb", "lci", "lca", "renda_variavel", "tesouro_direto", "cofrinho"]
            },
            memory=self.memory,
            tools=[self.add_compliance_disclaimer],
            markdown=True
        )
    
    def _create_credit_team(self) -> Agent:
        return Agent(
            name="Time de Crédito e Financiamento",
            model=Claude("claude-sonnet-4-20250514"),
            instructions="""
            Você é especialista em crédito PagBank.
            
            ALERTAS CRÍTICOS:
            1. SEMPRE busque "golpes_credito" para avisos
            2. Nunca prometa aprovação garantida
            3. Se mencionarem pagamento antecipado: ALERTA MÁXIMO
            
            BUSCA ESPECÍFICA:
            - Taxas: filtrar por "atualizado_em" recente
            - Requisitos: buscar "requisitos_[produto]"
            - Simulador: orientar para app
            
            Detecte tentativas de golpe e proteja o cliente.
            """,
            knowledge=self.knowledge_base,
            search_knowledge=True,
            enable_agentic_knowledge_filters=True,
            knowledge_filters={
                "area": "credito",
                "tipo_produto": ["fgts", "consignado_inss"]
            },
            memory=self.memory,
            tools=[self.detect_fraud_attempt],
            markdown=True
        )
    
    def add_compliance_disclaimer(self, agent: Agent) -> str:
        """Add compliance disclaimer to investment responses"""
        return "\n\n⚠️ **Aviso Legal**: Esta não é uma recomendação de investimento. Avalie se os produtos são adequados ao seu perfil e objetivos."
    
    def detect_fraud_attempt(self, agent: Agent, message: str) -> Dict:
        """Detect potential fraud in credit requests"""
        fraud_keywords = [
            "pagamento antecipado",
            "pagar para liberar",
            "depósito antes",
            "taxa de liberação",
            "boleto para liberar"
        ]
        
        message_lower = message.lower()
        detected = any(keyword in message_lower for keyword in fraud_keywords)
        
        if detected:
            return {
                "fraud_detected": True,
                "alert_level": "HIGH",
                "action": "ESCALATE_IMMEDIATELY",
                "message": "ALERTA: Possível tentativa de golpe detectada!"
            }
        
        return {"fraud_detected": False}
```

## Team-Specific Configurations

### 1. Cards Team
- Focus on practical examples
- Clear pricing and deadlines
- Virtual card benefits
- Digital wallet integration

### 2. Digital Account Team
- Automatic yield emphasis (100% CDI)
- PIX advantages
- Cashback on services
- Portability benefits

### 3. Investments Team
- Mandatory compliance text
- Risk level explanation
- Simple analogies for complex products
- FGC protection mentions

### 4. Credit Team
- Fraud detection priority
- Clear requirement lists
- No false promises
- Simulator app direction

### 5. Insurance Team
- Coverage clarity
- Price transparency
- Monthly prize mentions (R$ 20k)
- No waiting period emphasis

## Language Adaptation Levels
```python
language_levels = {
    "basico": {
        "style": "Simple, short sentences",
        "examples": "Everyday comparisons",
        "technical_terms": "Avoid completely"
    },
    "intermediario": {
        "style": "Clear, structured",
        "examples": "Practical scenarios",
        "technical_terms": "Explain when used"
    },
    "avancado": {
        "style": "Professional, detailed",
        "examples": "Market comparisons",
        "technical_terms": "Use appropriately"
    }
}
```

## Priority Items
1. Fraud detection in credit team (critical)
2. Compliance text in investments (regulatory)
3. Language adaptation based on customer profile
4. Knowledge filter accuracy for each team
5. Response time optimization (<2s target)