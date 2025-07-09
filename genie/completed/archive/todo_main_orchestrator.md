# TODO: Main Orchestrator Agent

## Objective
Create the central routing system that analyzes customer messages, detects frustration, performs clarification when needed, and routes to appropriate specialist teams while maintaining session state.

## Technical Requirements
- [ ] Create main Team with mode="route" configuration
- [ ] Implement integrated clarification logic (no separate agent)
- [ ] Build frustration detection system:
  - Keyword analysis (Portuguese frustration indicators)
  - Interaction count monitoring
  - Failed attempt tracking
  - Explicit human request detection
- [ ] Create message normalization for Portuguese errors:
  - Common misspellings (cartao→cartão, pra→para)
  - Informal language standardization
  - Punctuation correction
- [ ] Implement team_session_state management
- [ ] Configure routing logic to all specialist teams
- [ ] Set up human escalation triggers (3 interactions or high frustration)
- [ ] Create interaction logging system
- [ ] Implement context preservation across routing

## Code Structure
```python
pagbank/
  orchestrator/
    main_orchestrator.py          # Main routing team
    frustration_detector.py       # Frustration analysis
    text_normalizer.py           # Portuguese text correction
    routing_logic.py             # Routing decision engine
    clarification_handler.py     # Ambiguity resolution
  tools/
    orchestrator_tools.py        # Custom tool functions
```

## Research Required
- Agno Team with mode="route" documentation
- team_session_state implementation
- Tool creation for teams
- Message interception and modification
- Portuguese NLP for frustration detection
- Routing strategies and fallbacks

## Integration Points
- Input from: Customer (initial messages)
- Output to: All specialist teams (routed queries)
- Depends on: Memory system (pattern detection)
- Critical for: All downstream agents

## Testing Checklist
- [ ] Unit tests for frustration detection accuracy
- [ ] Integration test with all specialist teams
- [ ] Routing accuracy validation (95%+ target)
- [ ] Clarification effectiveness testing
- [ ] Text normalization validation
- [ ] Session state persistence testing
- [ ] Escalation trigger accuracy
- [ ] Load testing with concurrent users

## Deliverables
1. Main orchestrator team implementation
2. Frustration detection module
3. Text normalization system
4. Routing accuracy metrics
5. Integration test results

## Implementation Example
```python
from agno import Team, Agent
from typing import Dict, List, Optional

class MainOrchestrator:
    def __init__(self, specialist_teams: Dict[str, Agent]):
        self.specialist_teams = specialist_teams
        
        # Frustration keywords (Portuguese)
        self.frustration_keywords = [
            "droga", "merda", "porra", "não funciona", "péssimo",
            "horrível", "raiva", "ódio", "incompetente", "lixo",
            "não aguento mais", "cansei", "desisto", "que saco"
        ]
        
        # Create main routing team
        self.team = Team(
            name="PagBank Customer Service",
            mode="route",
            model=Claude("claude-sonnet-4-20250514"),
            members=list(specialist_teams.values()),
            instructions=[self._create_routing_prompt()],
            tools=[
                self.detect_frustration,
                self.normalize_text,
                self.check_escalation
            ],
            team_session_state=self._init_session_state(),
            show_members_responses=True
        )
    
    def _create_routing_prompt(self) -> str:
        return """
        Você é o Gerente de Atendimento Virtual do PagBank.
        
        PROCESSO DE ATENDIMENTO:
        1. Normalize a mensagem do cliente
        2. Detecte sinais de frustração
        3. Se ambíguo, faça UMA pergunta simples para esclarecer
        4. Roteie para o especialista apropriado:
           - Cartões → Time de Especialistas em Cartões
           - Conta, Pix, TEDs → Time de Conta Digital
           - Investimentos → Time de Assessoria de Investimentos
           - Empréstimos, FGTS → Time de Crédito e Financiamento
           - Seguros → Time de Seguros e Saúde
           - Bugs → Agente de Escalonamento Técnico
           - Sugestões → Agente Coletor de Feedback
        
        TRANSFERÊNCIA HUMANA se:
        - frustration_level >= 3
        - interaction_count > 3 sem resolução
        - Cliente pede explicitamente
        """
    
    def detect_frustration(self, team: Team, message: str) -> Dict:
        """Detect frustration indicators in customer message"""
        frustration_score = 0
        detected_keywords = []
        
        normalized_message = message.lower()
        
        for keyword in self.frustration_keywords:
            if keyword in normalized_message:
                frustration_score += 1
                detected_keywords.append(keyword)
        
        # Update session state
        current_level = team.team_session_state["frustration_level"]
        new_level = min(current_level + frustration_score, 3)
        team.team_session_state["frustration_level"] = new_level
        
        return {
            "frustration_detected": frustration_score > 0,
            "keywords": detected_keywords,
            "current_level": new_level,
            "escalate": new_level >= 3
        }
    
    def normalize_text(self, message: str) -> str:
        """Normalize common Portuguese errors"""
        corrections = {
            "cartao": "cartão",
            "nao": "não",
            "pra": "para",
            "ta": "está",
            "vc": "você",
            "pq": "porque",
            "tb": "também"
        }
        
        normalized = message
        for wrong, correct in corrections.items():
            normalized = normalized.replace(wrong, correct)
        
        return normalized
```

## Routing Decision Matrix
```yaml
keywords_to_team:
  cartoes:
    keywords: ["cartão", "cartao", "limite", "crédito", "débito", "pré-pago"]
    team: "Time de Especialistas em Cartões"
  
  conta_digital:
    keywords: ["pix", "transferência", "ted", "conta", "saldo", "extrato"]
    team: "Time de Conta Digital"
  
  investimentos:
    keywords: ["investir", "cdb", "lci", "lca", "render", "poupança"]
    team: "Time de Assessoria de Investimentos"
  
  credito:
    keywords: ["empréstimo", "fgts", "consignado", "crédito pessoal"]
    team: "Time de Crédito e Financiamento"
  
  seguros:
    keywords: ["seguro", "saúde", "vida", "residência", "proteção"]
    team: "Time de Seguros e Saúde"
  
  technical:
    keywords: ["erro", "bug", "não funciona", "travou", "problema técnico"]
    team: "Agente de Escalonamento Técnico"
  
  feedback:
    keywords: ["sugestão", "melhoria", "reclamação", "feedback", "opinião"]
    team: "Agente Coletor de Feedback"
```

## Priority Items
1. Frustration detection must be highly accurate
2. Routing must handle ambiguous queries gracefully
3. Text normalization should preserve meaning
4. Session state must track all interactions
5. Human escalation must trigger at right time