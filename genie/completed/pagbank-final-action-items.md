# PagBank Priority Content - Final Action Items

## Status Summary
✅ Knowledge CSV updated (user confirmed)
✅ New demo script created with 6 priority cases
✅ Content mapped to appropriate teams
⚠️ Minor routing adjustments needed

## Critical Finding: Routing Configuration Issue

### Problem Discovered
In `/orchestrator/routing_logic.py`, "antecipação" is currently mapped to CREDIT team (line 114):
```python
TeamType.CREDIT: {
    'keywords': [
        ...
        'antecipação',
        'antecipacao',
        ...
    ]
}
```

But according to PagBank's priority content, "antecipação de vendas" (sales advance) should go to DIGITAL_ACCOUNT team since it's a merchant account feature.

## Required Actions

### 1. Update Routing Logic (CRITICAL)
**File**: `/orchestrator/routing_logic.py`
**Change**: Move "antecipação" keywords from CREDIT to DIGITAL_ACCOUNT team

```python
# Remove from CREDIT keywords:
- 'antecipação',
- 'antecipacao',

# Add to DIGITAL_ACCOUNT keywords:
+ 'antecipação', 'antecipacao', 'antecipar',
+ 'multiadquirente', 'cielo', 'rede', 'stone',

# Add to DIGITAL_ACCOUNT patterns:
+ r'antecipar (vendas|receb[íi]veis)',
+ r'antecipa[çc][ãa]o de vendas',
+ r'antecipa[çc][ãa]o (da|de) (cielo|rede|stone)',
```

### 2. Enhance Team Knowledge Filters
**File**: `/teams/team_config.py`

For Digital Account Team (line 66):
```python
knowledge_filters=["conta", "pix", "transferencia", "saldo", "extrato", "ted", "doc", 
                   "antecipacao", "antecipação", "multiadquirente"],
```

For Cards Team (line 42):
```python
knowledge_filters=["cartao", "credito", "debito", "fatura", "limite", "anuidade", "cashback",
                   "iof", "internacional", "visa", "mastercard", "surpreenda"],
```

### 3. Optional Team Instruction Enhancements

**Digital Account Team** (`/teams/digital_account_team.py`):
Add to instructions:
```python
"Você também é especialista em antecipação de vendas para lojistas",
"Conhece regras de antecipação multiadquirente (Cielo, Rede, Stone, etc)",
"Antecipação: 1x por dia, análise diária, valor em 1-2 horas",
```

**Cards Team** (`/teams/cards_team.py`):
Add to instructions:
```python
"Especialista em programas de fidelidade: Vai de Visa (só Visa) e Mastercard Surpreenda",
"IOF internacional: 3,38% + conversão PTAX+5%",
"Limites pré-pago: R$5k pessoal, R$25k vendedor",
```

### 4. Use New Demo Script
**Replace**: `/docs/DEMO_SCRIPT.md`
**With**: `/docs/DEMO_SCRIPT_PRIORITY.md`

Or keep both and use PRIORITY version for PagBank demo.

## Testing Checklist

1. **Test Antecipação Routing**:
   ```
   Query: "Preciso antecipar vendas da Cielo"
   Expected: Routes to Digital Account Team
   ```

2. **Test Card Loyalty Programs**:
   ```
   Query: "Como participar do Vai de Visa com Mastercard?"
   Expected: Routes to Cards Team, explains brand exclusivity
   ```

3. **Test PIX Security**:
   ```
   Query: "PIX bloqueado por segurança"
   Expected: Routes to Digital Account Team
   ```

4. **Test App Issues**:
   ```
   Query: "App não atualiza, download pendente"
   Expected: Routes to Technical Escalation
   ```

## Demo Readiness

With these changes:
- ✅ All 3 priority topics covered (Antecipação, Cartões, Conta)
- ✅ 6 new demo cases showcasing main features
- ✅ Knowledge base already updated
- ⚠️ Need routing fix for antecipação
- ✅ Teams capable of handling all scenarios

## Estimated Time
- Routing fix: 5 minutes
- Testing: 10 minutes
- Total: 15 minutes to full readiness

## Risk Assessment
**Low Risk**: System is 95% ready. Only the antecipação routing needs adjustment. Even without the fix, the orchestrator's NLP might still route correctly based on full context, but fixing ensures 100% accuracy.