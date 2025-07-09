# TODO: Demo Environment Agent

## Objective
Create a comprehensive demonstration environment showcasing all 6 customer scenarios with a simple dashboard, logging system, and reset functionality for seamless POC presentations.

## Technical Requirements
- [ ] Create demo scripts for all 6 cases:
  1. Marina Oliveira - Educated customer with simple query
  2. José Santos - Elderly with tech difficulties
  3. Manoel Silva - Urgent family situation (frustration)
  4. Amanda Chen - Business owner with multiple needs
  5. Maria Silva - Fraud attempt victim
  6. Roberto Nakamura - Sophisticated investor
- [ ] Build simple routing dashboard:
  - Real-time agent routing visualization
  - Current conversation state display
  - Frustration level indicator
  - Memory/pattern insights panel
- [ ] Implement comprehensive logging:
  - All agent interactions
  - Routing decisions with reasoning
  - Knowledge base queries
  - Performance metrics
- [ ] Create reset functionality:
  - Clear session states
  - Reset memory for demo
  - Restore default knowledge
  - Initialize customer profiles
- [ ] Prepare customer profile system:
  - Pre-configured personas
  - Contextual backgrounds
  - Expected behaviors
- [ ] Implement playground integration

## Code Structure
```python
pagbank/
  demo/
    demo_runner.py              # Main demo orchestrator
    scenarios/
      scenario_1_marina.py      # Each scenario script
      scenario_2_jose.py
      scenario_3_manoel.py
      scenario_4_amanda.py
      scenario_5_maria.py
      scenario_6_roberto.py
    dashboard/
      dashboard_app.py          # Simple web dashboard
      static/                   # Dashboard assets
      templates/               # HTML templates
    logging/
      demo_logger.py           # Logging system
      log_analyzer.py          # Log analysis tools
    reset/
      reset_manager.py         # System reset tools
    profiles/
      customer_profiles.json   # Pre-defined personas
```

## Research Required
- Agno playground integration
- Streaming response handling
- Web dashboard frameworks (Flask/FastAPI)
- Real-time updates (WebSockets/SSE)
- Logging best practices
- Demo automation strategies

## Integration Points
- Input from: All system components
- Displays: Real-time system state
- Controls: Demo flow and reset
- Critical for: POC presentation success

## Testing Checklist
- [ ] All 6 scenarios run without errors
- [ ] Dashboard updates in real-time
- [ ] Logging captures all interactions
- [ ] Reset cleans system properly
- [ ] Customer profiles load correctly
- [ ] Performance metrics accurate
- [ ] Demo flow is smooth
- [ ] Error recovery works

## Deliverables
1. Complete demo runner application
2. All 6 scenario implementations
3. Interactive dashboard
4. Comprehensive logging system
5. Demo presentation guide

## Implementation Example
```python
from agno import Playground
from typing import Dict, List
import asyncio
import json
from datetime import datetime

class DemoEnvironment:
    def __init__(self, orchestrator, teams, memory, knowledge):
        self.orchestrator = orchestrator
        self.teams = teams
        self.memory = memory
        self.knowledge = knowledge
        
        # Load customer profiles
        self.profiles = self._load_customer_profiles()
        
        # Initialize dashboard
        self.dashboard = DemoDashboard()
        
        # Setup logging
        self.logger = DemoLogger()
        
        # Create playground app
        self.playground = self._create_playground()
    
    def _create_playground(self):
        """Create Agno playground for demo"""
        playground = Playground(
            agents=[
                self.orchestrator,
                *self.teams.values()
            ],
            markdown=True,
            show_tool_calls=True,
            show_reasoning=True
        )
        
        return playground
    
    def _load_customer_profiles(self) -> Dict:
        """Load pre-configured customer personas"""
        return {
            "marina": {
                "name": "Dra. Marina Oliveira",
                "age": 35,
                "profile": "Médica, alta escolaridade",
                "communication": "clara e objetiva",
                "initial_message": "Boa tarde! Gostaria de informações sobre os tipos de cartão de crédito disponíveis e suas vantagens.",
                "expected_routing": "Time de Especialistas em Cartões",
                "demo_duration": 3
            },
            "jose": {
                "name": "Sr. José Santos",
                "age": 72,
                "profile": "Aposentado, pouca familiaridade com tecnologia",
                "communication": "confusa, erros de digitação",
                "initial_message": "ola moça eu quero saber desse negocio de guardar dinheiro que rende mais que a poupança mas nao entendo nada disso de cdb",
                "expected_routing": "Time de Assessoria de Investimentos",
                "demo_duration": 4
            },
            "manoel": {
                "name": "Manoel Silva",
                "age": 47,
                "profile": "Comerciante, urgência familiar",
                "communication": "desesperada, frustrada",
                "initial_message": "preciso aumentar o limite do meu cartao urgente minha familia ta precisando e o app nao ta funcionando",
                "expected_routing": "Time de Especialistas em Cartões → Agente Humano",
                "demo_duration": 5
            },
            "amanda": {
                "name": "Amanda Chen",
                "age": 28,
                "profile": "Empresária, tech-savvy",
                "communication": "direta, múltiplas necessidades",
                "initial_message": "Oi! Preciso de 3 coisas: 1) maquininha com taxa competitiva 2) conta PJ com API para integração 3) cartão corporativo pros funcionários",
                "expected_routing": "Múltiplos times em sequência",
                "demo_duration": 4
            },
            "maria": {
                "name": "Dona Maria Silva",
                "age": 65,
                "profile": "Pensionista, vulnerável",
                "communication": "preocupada, menciona golpe",
                "initial_message": "moça o rapaz do pagbank me ligou dizendo que eu tenho que pagar 500 reais pra liberar meu emprestimo consignado é assim mesmo",
                "expected_routing": "Detecção de Fraude → Segurança",
                "demo_duration": 4
            },
            "roberto": {
                "name": "Roberto Nakamura",
                "age": 40,
                "profile": "Analista financeiro, CPA-20",
                "communication": "técnica, questões complexas",
                "initial_message": "Boa tarde. Gostaria de informações sobre a estrutura de FIDCs ou FIMs disponíveis na plataforma, especificamente sobre liquidez D+N, taxa de administração e performance, e se há produtos com estratégias de hedge cambial.",
                "expected_routing": "Time de Assessoria de Investimentos",
                "demo_duration": 3
            }
        }
    
    async def run_scenario(self, scenario_name: str):
        """Run a specific demo scenario"""
        profile = self.profiles.get(scenario_name)
        if not profile:
            raise ValueError(f"Scenario {scenario_name} not found")
        
        # Reset system for clean demo
        await self.reset_system()
        
        # Initialize customer context
        self.orchestrator.team_session_state.update({
            "customer_id": f"DEMO_{scenario_name.upper()}",
            "customer_name": profile["name"],
            "customer_context": {
                "age": profile["age"],
                "profile": profile["profile"],
                "communication_style": profile["communication"]
            }
        })
        
        # Log scenario start
        self.logger.log_event({
            "type": "scenario_start",
            "scenario": scenario_name,
            "profile": profile,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update dashboard
        await self.dashboard.update_status({
            "current_scenario": scenario_name,
            "customer": profile["name"],
            "expected_duration": profile["demo_duration"]
        })
        
        # Run the conversation
        response = await self.orchestrator.run(
            profile["initial_message"],
            stream=True,
            stream_intermediate_steps=True
        )
        
        # Stream to dashboard
        async for event in response:
            await self.dashboard.stream_event(event)
            self.logger.log_event(event)
    
    async def reset_system(self):
        """Reset system state for clean demo"""
        # Clear session states
        self.orchestrator.team_session_state.clear()
        self.orchestrator.team_session_state.update(self._default_session_state())
        
        # Clear demo memories (but keep patterns)
        demo_memories = self.memory.search("type:demo", limit=1000)
        for memory in demo_memories:
            self.memory.delete(memory.id)
        
        # Reset dashboard
        await self.dashboard.reset()
        
        # Log reset
        self.logger.log_event({
            "type": "system_reset",
            "timestamp": datetime.now().isoformat()
        })
    
    def _default_session_state(self) -> Dict:
        """Default session state structure"""
        return {
            "customer_id": "",
            "customer_name": "",
            "interaction_count": 0,
            "clarification_count": 0,
            "frustration_level": 0,
            "message_history": [],
            "routing_history": [],
            "current_topic": "",
            "last_topic": "",
            "resolved": False,
            "awaiting_human": False,
            "tickets": [],
            "protocols": [],
            "satisfaction_score": None,
            "resolution_time": None,
            "customer_context": {
                "education_level": "unknown",
                "communication_style": "unknown",
                "preferred_channel": "chat"
            }
        }
```

## Dashboard Components

### Real-time Display
```html
<!-- Dashboard Template -->
<div class="dashboard">
    <div class="current-state">
        <h3>Current Conversation</h3>
        <div class="customer-info">
            <span class="name">{{ customer_name }}</span>
            <span class="profile">{{ profile }}</span>
        </div>
        <div class="frustration-meter">
            <div class="level-{{ frustration_level }}"></div>
        </div>
    </div>
    
    <div class="routing-flow">
        <h3>Agent Routing</h3>
        <div class="flow-diagram">
            <!-- Dynamic SVG showing routing -->
        </div>
    </div>
    
    <div class="metrics">
        <h3>Performance Metrics</h3>
        <ul>
            <li>Response Time: <span>{{ response_time }}ms</span></li>
            <li>Routing Accuracy: <span>{{ accuracy }}%</span></li>
            <li>Knowledge Hits: <span>{{ knowledge_hits }}</span></li>
        </ul>
    </div>
    
    <div class="insights">
        <h3>Pattern Insights</h3>
        <div class="patterns">
            <!-- Memory patterns display -->
        </div>
    </div>
</div>
```

## Demo Flow Script
```yaml
demo_presentation:
  introduction: 2 minutes
    - System overview
    - Architecture explanation
    - Key capabilities
  
  scenarios: 20-25 minutes
    - scenario_1: 3 min (Simple query)
    - scenario_2: 4 min (Language adaptation)
    - scenario_3: 5 min (Frustration/escalation)
    - scenario_4: 4 min (Multi-routing)
    - scenario_5: 4 min (Fraud detection)
    - scenario_6: 3 min (Technical expertise)
  
  insights: 3 minutes
    - Pattern analysis
    - Memory demonstration
    - Improvement opportunities
  
  q_and_a: 5 minutes
```

## Priority Items
1. All scenarios must run flawlessly
2. Dashboard must be visually impressive
3. Reset must be instantaneous
4. Logging must capture everything
5. Performance must be optimal (<2s responses)