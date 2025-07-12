# Task Card: YAML Configuration Examples

## Overview
This task card is part of the PagBank Multi-Agent Platform V2 implementation.

## Reference
- Main strategy: `/genie/active/pagbank-agents-platform-strategy.md`
- Demo app reference: `/genie/agno-demo-app/`

---

### Ana Team Configuration (MANDATORY YAML - Simplified)

```yaml
# teams/ana/config.yaml
team:
  id: "ana"
  name: "Ana - Atendimento PagBank"
  role: "Assistente virtual unificada"
  
model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"  # Claude 4 Sonnet
  thinking:
    type: "enabled"
    budget_tokens: 1024  # For better routing decisions
  max_tokens: 2000
  temperature: 0.7
  
# ALL settings MUST be specified - no defaults
settings:
  # Display Control - Hide internal routing
  show_tool_calls: false              
  show_members_responses: false       # Ana presents unified response
  stream_intermediate_steps: false    # Critical: Hide routing details
  markdown: true                      
  
  # Memory Settings 
  enable_agentic_memory: true         # Ana remembers users
  enable_user_memories: true          
  add_memory_references: false        
  enable_session_summaries: false     
  add_session_summary_references: false
  
  # History Settings
  add_history_to_messages: true       
  num_history_runs: 5                 
  search_previous_sessions_history: false
  num_history_sessions: 0
  
  # Context & State 
  enable_agentic_context: true        # Share context between agents
  share_member_interactions: false    
  add_state_in_messages: false        
  
  # System Message
  add_datetime_to_instructions: true  
  add_location_to_instructions: false 
  add_member_tools_to_system_message: false  
  timezone_identifier: "America/Sao_Paulo"
  
  # Knowledge & RAG
  enable_agentic_knowledge_filters: false  
  add_references: false               
  references_format: "json"
  search_knowledge: true              # Access to knowledge base
  
  # Tools
  get_member_information_tool: false
  read_team_history: false
  tool_call_limit: 10                 
  tool_choice: null                   
  
  # Response
  parse_response: true
  use_json_mode: false               
  
  # Reasoning 
  reasoning: false                    # Using thinking mode instead
  reasoning_min_steps: 1
  reasoning_max_steps: 10
  
members:
  - adquirencia_specialist    # Antecipação de vendas
  - emissao_specialist        # Cartões  
  - pagbank_specialist        # Conta, Pix, TED
  - human_handoff_specialist  # Escalação
  
storage:
  type: "postgres"  
  url: "${DATABASE_URL}"
  
instructions: |
  Você é Ana, a assistente virtual oficial do PagBank.
  
  IMPORTANTE: Você deve rotear internamente para o especialista apropriado baseado no assunto:
  - Adquirência: antecipação de vendas, máquinas, multiadquirente
  - Emissão: cartões (crédito, débito, pré-pago), senha, bloqueio
  - PagBank: conta, Pix, TED, folha de pagamento, app
  - Human Handoff: frustração detectada (nível >= 3) ou solicitação explícita
  
  Você SEMPRE se apresenta como Ana e fornece uma resposta unificada ao cliente.
  Nunca mencione que está usando especialistas internamente.
```

### Specialist Agent Configuration Example (Emissão)

```yaml
# agents/specialists/emissao/config.yaml
agent:
  id: "emissao_specialist"
  name: "Especialista em Emissão"
  role: "Especialista em cartões PagBank"
  
model:
  provider: "anthropic"
  id: "claude-haiku-4-20250514"  # Fast and efficient
  max_tokens: 1000
  temperature: 0.5  
  
settings:
  # Minimal settings for specialist agents
  show_tool_calls: false              
  markdown: false                     # Ana handles formatting
  enable_agentic_memory: false        # Ana handles memory
  enable_user_memories: false
  add_history_to_messages: true       # Get context from Ana
  num_history_runs: 3
  search_knowledge: true              # Access emissão knowledge
  tool_call_limit: 5                  
  create_default_system_message: true
  add_context: true                   # Receive routing context
  parse_response: true
  use_json_mode: false
  
  # All other required settings (set to defaults)
  add_memory_references: false
  enable_session_summaries: false
  read_chat_history: false
  enable_agentic_knowledge_filters: false
  add_references: false
  references_format: "json"
  update_knowledge: false
  read_tool_call_history: false
  add_name_to_instructions: true
  add_datetime_to_instructions: false
  add_location_to_instructions: false
  resolve_context: true
  search_previous_sessions_history: false
  num_history_sessions: 0
  reasoning: false
  reasoning_min_steps: 1
  reasoning_max_steps: 5
  output_dir: "./outputs"
  save_output_to_file: false
  print_output: false
  
knowledge_filters:
  business_unit: "Emissão"  # Filter knowledge to cards only
  
instructions: |
  Você é especialista em cartões PagBank (Emissão).
  
  Seu conhecimento cobre:
  - Cartão Múltiplo, Pré-Pago, Crédito, Débito
  - Cartões Visa e Mastercard
  - Bloqueio/desbloqueio
  - Senha e CVV
  - Limites e faturas
  - Programas de benefícios
  
  Responda de forma clara e direta.
```

### Human Handoff Configuration (Special Case)

```yaml
# agents/specialists/human_handoff/config.yaml
agent:
  id: "human_handoff"
  name: "Escalação Humana"
  role: "Transferência para atendente humano"
  
model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"  # Claude 4 Haiku (cheapest)
  max_tokens: 200                 # Short responses
  
settings:
  # Minimal settings for handoff
  show_tool_calls: false
  markdown: false
  enable_agentic_memory: false
  enable_user_memories: false
  add_history_to_messages: true
  num_history_runs: 10            # Full context for human
  search_knowledge: false         # No KB needed
  tool_call_limit: 2              # Just handoff tools
  create_default_system_message: true
  parse_response: true
  use_json_mode: false
  
  # All other settings must be specified even if false
  add_memory_references: false
  enable_session_summaries: false
  read_chat_history: false
  enable_agentic_knowledge_filters: false
  add_references: false
  references_format: "json"
  update_knowledge: false
  read_tool_call_history: false
  add_name_to_instructions: false
  add_datetime_to_instructions: true
  add_location_to_instructions: false
  add_context: true
  resolve_context: true
  search_previous_sessions_history: false
  num_history_sessions: 0
  reasoning: false
  reasoning_min_steps: 1
  reasoning_max_steps: 1
  output_dir: "./outputs"
  save_output_to_file: false
  print_output: false
  
tools:
  - whatsapp_notification
  - create_ticket
  
instructions: |
  Você detecta frustração e realiza transferência para humano.
  Seja empático e informe que um atendente ajudará em breve.
```

---

## Validation Steps
TODO: Add specific validation steps for this task

## Dependencies
TODO: List dependencies on other task cards

Co-Authored-By: Automagik Genie <genie@namastex.ai>
