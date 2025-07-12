# Task Card: Create Ana Team V2 with Simple Mode Route

## Overview
This task card is part of the PagBank Multi-Agent Platform V2 development.

## Reference
- Main strategy: `/genie/active/pagbank-agents-platform-strategy.md`
- Demo app reference: `/genie/agno-demo-app/`
- Branch: `v2` (clean rewrite)

---

## Task Details

**Priority**: HIGH - This unblocks all other work  
**Risk**: LOW - Copy existing working patterns
**Strategy**: COPY 80% from agno-demo-app, modify 20% for PagBank

## V2 Target State (Copy Demo App Pattern)
- File: `teams/ana/team.py` (COPY from `genie/agno-demo-app/teams/finance_researcher.py`)
- Same function signature: `get_ana_team(model_id, user_id, session_id, debug_mode)`
- Same Team creation pattern with static config
- Instructions-based routing (copy demo app approach)

## Implementation Steps

### Step 1: Extract Routing Requirements 
```bash
# From POC branch, extract routing patterns for reference
git checkout poc
grep -n "route\|specialist" agents/orchestrator/main_orchestrator.py > v2-routing-requirements.txt
grep -n "frustration\|handoff" agents/orchestrator/human_handoff_detector.py >> v2-routing-requirements.txt
git checkout v2
```

### Step 2: Create Team Structure 
```bash
mkdir -p teams/ana
touch teams/ana/__init__.py
touch teams/ana/team.py
touch teams/ana/config.yaml
```

### Step 3: Copy Demo App Team Factory 
**COPY EXACTLY** from `genie/agno-demo-app/teams/finance_researcher.py` lines 83-117:

```python
# teams/ana/team.py
from textwrap import dedent
from typing import Optional
from agno.team import Team
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from db.session import db_url  # Copy this too
from db.session import db_url
from agents.registry import AgentRegistry

def get_ana_team(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    debug_mode: bool = True
) -> Team:
    # Load agents from registry
    members = [
        AgentRegistry.get_agent("adquirencia_specialist"),
        AgentRegistry.get_agent("emissao_specialist"),
        AgentRegistry.get_agent("pagbank_specialist"),
        AgentRegistry.get_agent("human_handoff_specialist")
    ]
    
    return Team(
        name="Ana - Atendimento PagBank",
        team_id="ana-pagbank-assistant",
        mode=config["team"]["mode"],  # From YAML
        members=members,
        model=Claude(
            id="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.7,
            thinking={"type": "enabled", "budget_tokens": 1024}
        ),
        storage=PostgresStorage(
            table_name="ana_team",
            db_url=db_url,
            mode="team",
            auto_upgrade_schema=True
        ),
        session_id=session_id,
        user_id=user_id,
        debug_mode=debug_mode,
        # Load all settings from YAML
        **load_yaml_settings("teams/ana/config.yaml")
    )
```

### Step 4: Convert Routing Logic to Instructions 
Extract from `routing_logic.py` and convert to natural language:

```yaml
# teams/ana/config.yaml
instructions: |
  Você é Ana, assistente virtual oficial do PagBank.
  
  ROTEAMENTO BASEADO EM PALAVRAS-CHAVE:
  
  Adquirência :
  - Palavras: antecipação, vendas, máquina, maquininha, multiadquirente
  - Contexto: antecipação de vendas, taxas de máquinas
  
  Emissão (emissao_specialist):
  - Palavras: cartão, card, senha, cvv, bloqueio, desbloqueio, limite
  - Contexto: cartões de crédito, débito, pré-pago
  
  PagBank (pagbank_specialist):
  - Palavras: pix, ted, conta, saldo, extrato, app, folha, pagamento
  - Contexto: conta digital, transferências, folha de pagamento
  
  Human Handoff (human_handoff_specialist):
  - Frustração nível 3+ (xingamentos, caps lock excessivo)
  - Solicitação explícita: "falar com atendente", "quero humano"
  - Pergunta repetida 3+ vezes
```

### Step 5: Create V2 Tests 
Create comprehensive test:

```python
# tests/test_ana_implement.py
import pytest
from teams.ana.team import get_ana_team
from agents.orchestrator.main_orchestrator import PagBankOrchestrator

test_cases = [
    ("quero antecipar minhas vendas", "adquirencia_specialist"),
    ("perdi meu cartão", "emissao_specialist"),
    ("fazer um pix de 100 reais", "pagbank_specialist"),
    ("QUERO FALAR COM ATENDENTE AGORA!", "human_handoff_specialist"),
]

def test_routing_parity():
    old_orchestrator = PagBankOrchestrator()
    new_ana = get_ana_team()
    
    mismatches = []
    for query, expected in test_cases:
        old_result = old_orchestrator.route(query)
        new_result = new_ana.run(query)
        
        if not verify_same_routing(old_result, new_result, expected):
            mismatches.append((query, old_result, new_result))
    
    assert len(mismatches) == 0, f"Routing mismatches: {mismatches}"
```

### Step 6: Test Complete V2 Implementation 
Test the new Ana team implementation:

```python
# tests/test_ana_v2.py
import pytest
from teams.ana.team import get_ana_team

def test_ana_v2_routing():
    """Test V2 Ana routing works correctly"""
    ana = get_ana_team()
    
    test_cases = [
        ("quero antecipar minhas vendas", "adquirencia_specialist"),
        ("perdi meu cartão", "emissao_specialist"),
        ("fazer um pix de 100 reais", "pagbank_specialist"),
        ("QUERO FALAR COM ATENDENTE AGORA!", "human_handoff_specialist"),
    ]
    
    for query, expected in test_cases:
        result = ana.run(query)
        # Verify correct specialist was called
        assert_specialist_handled(result, expected)
```

## Validation Checklist
- [ ] All 4 specialist agents properly loaded
- [ ] Routing keywords documented and converted to instructions
- [ ] Frustration detection implemented in instructions
- [ ] All test cases pass for V2
- [ ] Memory handled by Agno PostgresStorage
- [ ] Session management automatic
- [ ] Performance meets requirements

## Dependencies
- **Prerequisite**: None (this is the first task)
- **Blocks**: All other Phase 1 tasks
- **Branch**: Development happens in `v2` branch

## Success Metrics
- All V2 features working correctly
- Response time < 200ms
- All routing test cases pass
- Clean architecture with Agno patterns

Co-Authored-By: Automagik Genie <genie@namastex.ai>
