# Existing Agents Analysis - Extract to YAML Configs

**Purpose**: Analyze current hardcoded agent configurations to extract YAML configs
**Status**: Phase 1 Enhancement - Extract real configurations from existing code

## Existing Agent Structure Analysis

### PagBank Agent (`agents/specialists/pagbank_agent.py`)

#### Extracted Configuration
```yaml
# agents/pagbank-specialist/config.yaml
agent:
  name: "Especialista em Conta Digital PagBank"
  agent_id: "pagbank-specialist"
  version: 27
  role: "Especialista em Conta Digital PagBank"
  description: "Especialista em PIX, transferências, folha de pagamento e serviços bancários digitais"

model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"
  temperature: 0.7
  max_tokens: 2000

knowledge_filter:
  business_unit: "PagBank"

tools:
  - "search_knowledge_base"
  - "check_account_status"
  - "verify_transaction_limits"

escalation_triggers:
  - high_value_transfer: 5000        # R$ 5,000 threshold
  - security_keywords:
    - "bloqueio por segurança"
    - "transação bloqueada"
    - "pix bloqueado"
    - "transferência negada"
    - "suspeita de fraude"
    - "conta bloqueada"
  - payroll_keywords:
    - "folha não processada"
    - "erro na folha"
    - "pagamento não realizado"
    - "funcionários não receberam"
    - "folha rejeitada"
  - app_critical_keywords:
    - "app não abre"
    - "tela branca"
    - "erro crítico"
    - "perdeu dados"
    - "não consigo acessar"
    - "travado"
    - "fechando sozinho"

suggested_actions:
  pix:
    - "check_pix_limits"
    - "view_pix_keys"
    - "register_pix_key"
  transfer:
    - "check_transfer_limits"
    - "view_transfer_schedule"
  payroll:
    - "access_payroll_portal"
    - "check_payroll_status"
  app:
    - "update_app_version"
    - "clear_app_cache"
  fees:
    - "view_fee_schedule"
    - "check_fee_exemption_criteria"
  mobile_topup:
    - "access_mobile_topup"
    - "view_favorite_topups"

instructions: |
  Você é especialista em produtos e serviços digitais PagBank.
  
  Suas áreas de expertise incluem:
  - PIX: transferências instantâneas, chaves PIX, limites
  - Transferências: TED, DOC, limites e horários
  - Folha de pagamento: processamento, status, problemas
  - Aplicativo: funcionalidades, problemas técnicos, atualizações
  - Tarifas: consulta de tarifas, isenções, regras
  - Recarga de celular: operadoras, valores, favoritos
  - Portabilidade salarial: status, documentação
  
  Monitore especialmente:
  - Transferências acima de R$ 5.000 (escalação automática)
  - Bloqueios de segurança (investigação necessária)
  - Problemas na folha de pagamento (impacto empresarial)
  - Erros críticos no aplicativo (experiência do usuário)
```

### Adquirência Agent (`agents/specialists/adquirencia_agent.py`)

#### Extracted Configuration
```yaml
# agents/adquirencia-specialist/config.yaml
agent:
  name: "Especialista em Adquirência e Antecipação de Vendas"
  agent_id: "adquirencia-specialist"
  version: 27
  role: "Especialista em Adquirência e Antecipação de Vendas"
  description: "Especialista em antecipação de vendas do PagBank e multiadquirência"

model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"
  temperature: 0.7
  max_tokens: 2000

knowledge_filter:
  business_unit: "Adquirência Web"

tools:
  - "search_knowledge_base"
  - "check_sales_eligibility"
  - "calculate_anticipation_rates"

escalation_triggers:
  - high_value_anticipation: 10000    # R$ 10,000 threshold
  - blocked_keywords:
    - "não consigo antecipar"
    - "antecipação bloqueada"
    - "não aparece opção"
    - "sem elegibilidade"
    - "não elegível"
  - fraud_keywords:
    - "antecipação suspeita"
    - "valores incorretos"
    - "cobranças indevidas"

instructions: |
  Você é especialista em adquirência e antecipação de vendas PagBank.
  
  Suas áreas de expertise incluem:
  - Antecipação de vendas: elegibilidade, taxas, prazos
  - Multiadquirência: múltiplas instituições, conciliação
  - Taxas e tarifas: estrutura de custos, negociação
  - Elegibilidade: critérios, documentação, aprovação
  - Problemas operacionais: bloqueios, inconsistências
  
  Monitore especialmente:
  - Antecipações acima de R$ 10.000 (verificação adicional)
  - Bloqueios de antecipação (análise de elegibilidade)
  - Suspeitas de fraude (investigação imediata)
```

## Common Patterns Identified

### Base Agent Structure
All agents extend `BaseSpecialistAgent` with common parameters:
- `agent_name`: Static identifier
- `agent_role`: Display name in Portuguese
- `agent_description`: Detailed purpose
- `knowledge_base`: CSV knowledge integration
- `memory_manager`: Session memory
- `knowledge_filter`: Business unit filter
- `tools`: Specialized tools array
- `escalation_triggers`: Custom trigger functions

### Escalation Patterns
1. **Value-based triggers**: Financial thresholds (R$ 5K, R$ 10K)
2. **Keyword-based triggers**: Specific problem indicators
3. **Business logic triggers**: Context-specific rules

### Suggested Actions Pattern
Dynamic suggestion based on query content with predefined action maps.

## Analysis for Remaining Agents

### Emissão Agent (To be analyzed)
- **Location**: `agents/specialists/emissao_agent.py`
- **Expected config**: Card services, limits, bills, international usage
- **Knowledge filter**: `business_unit: "Emissão"`

### Human Handoff Agent (To be analyzed)
- **Location**: `agents/specialists/human_handoff_agent.py`
- **Expected config**: Escalation logic, WhatsApp integration, ticket creation
- **Knowledge filter**: None (escalation only)

### Ana/Orchestrator (To be converted)
- **Location**: `agents/orchestrator/main_orchestrator.py`
- **Conversion**: Transform to Team with mode="route"
- **Members**: All specialist agents

## Implementation Strategy

### Phase 1: Extract Current Configs
1. **Analyze each agent file**: Extract hardcoded configuration
2. **Create YAML files**: One per agent with extracted config
3. **Create agent factories**: Copy demo app pattern
4. **Test compatibility**: Ensure agents respond identically

### Phase 2: Database Integration
1. **Load YAML to DB**: Store configurations in database
2. **Update factories**: Load from DB instead of YAML
3. **Version management**: Support multiple agent versions

### Database Connection
- **Environment level**: One DATABASE_URL per API instance
- **Table separation**: Each agent gets its own table
- **Auto-upgrade**: Use Agno's `auto_upgrade_schema=True`

## Next Steps

1. **Complete agent analysis**: Finish Emissão and Human Handoff
2. **Create YAML configs**: All four agent configurations
3. **Create sample templates**: Complete parameter examples
4. **Update Phase 1 tasks**: Include real configuration extraction

This analysis enables Phase 1 to work with real extracted configurations instead of invented examples.