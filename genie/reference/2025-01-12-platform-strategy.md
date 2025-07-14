# Automagik Agents Platform - Technical Implementation Plan
## Copy Agno Agent-API Structure, Keep Agent Logic Flexible

### Core Principle

Copy the **exact API structure** from Agno agent-api, but keep agents as Python code (not YAML templates). YAML is **mandatory** for all settings - no defaults, explicit configuration required.

### Critical Architecture Simplifications

**1. Remove Complex Orchestrator - Use Agno's Built-in Routing**
- Current: 400+ line orchestrator.py with manual routing logic
- Solution: Ana is just a Team with `mode=config["team"]["mode"]` - that's ALL!
- Agno provides routing, memory, sessions, and state management

**2. Typification is NEW Functionality**
- Current: System routes by keywords, NOT typification
- Solution: Add typification workflow for post-conversation analytics
- Must follow EXACT CSV hierarchy (4 units → 20 products → 40 motives → 53 submotives)

**3. Configuration Management Pattern**
- YAML files are source of truth (like docker-compose.yml)
- Database stores runtime configurations
- Hot reload by updating database, NOT YAML files
- Migration on startup: YAML → Database → Runtime

**4. Simple Agent Versioning**
- Just integer versions: v25, v26, v27
- Call any version directly via API
- No complex traffic routing needed
- Store versions in database with full config

### Complete API Endpoints (from agent-api + demo-app)

```python
# Core Agent API (from agent-api)
GET  /v1/agents                           # List all agents
POST /v1/agents/{agent_id}/runs           # Run specific agent
POST /v1/agents/{agent_id}/knowledge/load # Load agent knowledge

# Team API (enhanced from demo-app)
GET  /v1/teams                            # List all teams  
POST /v1/teams/{team_id}/runs             # Run specific team
GET  /v1/teams/{team_id}/sessions         # Team sessions

# NEW: Workflow API (TO BE CREATED - Not in demo-app)
# Note: These endpoints don't exist in the demo-app, they're proposed
GET  /v1/workflows                        # List all workflows
POST /v1/workflows/{workflow_id}/runs     # Execute workflow

# Future Workflow Management (proposed)
GET  /v1/workflows/{workflow_id}/config   # Get workflow config
PUT  /v1/workflows/{workflow_id}/config   # Update workflow config

# Simple Agent Versioning (PagBank Style)
GET  /v1/agents/{agent_id}/versions       # List all versions (25, 26, 27...)
POST /v1/agents/{agent_id}/versions       # Create new version

# Run Any Version Directly
POST /v1/agents/{agent_id}/v25/runs       # Run version 25 specifically  
POST /v1/agents/{agent_id}/v26/runs       # Run version 26 specifically
POST /v1/agents/{agent_id}/v27/runs       # Run version 27 specifically
POST /v1/agents/{agent_id}/runs           # Run latest version

# Advanced Analytics & Monitoring
GET  /v1/analytics/agents                 # Agent performance metrics
GET  /v1/analytics/teams                  # Team performance metrics  
GET  /v1/analytics/workflows              # Workflow execution stats
GET  /v1/analytics/customers              # Customer satisfaction metrics

# Playground & Testing
GET  /playground                          # Web UI for testing
POST /playground/agents/{agent_id}        # Test agent in playground
POST /playground/teams/{team_id}          # Test team in playground
POST /playground/workflows/{workflow_id}  # Test workflow in playground

# Health & Status
GET  /health                              # System health check
GET  /status                              # Detailed system status
GET  /metrics                             # Prometheus metrics
```

### Folder Structure (UV-based, Scalable)

```
pagbank-multiagents/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI app (copy from agent-api)
│   ├── routes/              # Scalable route structure
│   │   ├── __init__.py
│   │   ├── agents.py        # All agent endpoints (won't split)
│   │   ├── teams.py         # All team endpoints (won't split)
│   │   ├── sessions.py      # Session management
│   │   ├── knowledge.py     # Knowledge operations
│   │   └── health.py        # Health & monitoring
│   └── settings.py          # Pydantic settings
│
├── agents/                  # Agent implementations
│   ├── __init__.py
│   ├── registry.py          # Agent registry
│   ├── specialists/         # Specialist agents
│   │   ├── cards/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py     # CardsAgent class
│   │   │   └── config.yaml  # MANDATORY settings
│   │   ├── digital_account/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   └── config.yaml
│   │   ├── adquirencia/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   └── config.yaml
│   │   └── human_handoff/
│   │       ├── __init__.py
│   │       ├── agent.py
│   │       └── config.yaml
│   ├── _template/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   └── config.yaml
│   └── base_agent.py       # Base class
│
├── teams/                   # Team configurations
│   ├── __init__.py
│   ├── registry.py          # Team registry
│   ├── ana/                 # Ana's team (atendimento renamed)
│   │   ├── __init__.py
│   │   ├── team.py          # Ana team logic (simple Team with mode=config["team"]["mode"])
│   │   └── config.yaml      # MANDATORY settings
│   └── _template/
│       ├── __init__.py
│       ├── team.py
│       └── config.yaml
│
# NEW: Workflows (from demo-app) - Currently None in Codebase
├── workflows/               # Multi-agent workflows (to be created)
│   ├── __init__.py
│   ├── registry.py          # Workflow registry
│   ├── settings.py          # Workflow-specific settings
│   ├── conversation_typification/
│   │   ├── __init__.py
│   │   ├── workflow.py      # Smart typification workflow
│   │   └── config.yaml      # Typification configuration
│   └── _template/
│       ├── __init__.py
│       ├── workflow.py
│       └── config.yaml
│
├── shared/                  # Shared components
│   ├── memory/              # Memory system
│   ├── knowledge/           # Knowledge base
│   └── tools/               # Shared tools
│
# NEW: Database Management (from demo-app)
├── db/
│   ├── __init__.py
│   ├── session.py           # SQLAlchemy session management
│   ├── settings.py          # Database settings
│   ├── alembic.ini          # Alembic configuration
│   ├── migrations/          # Database migrations
│   │   ├── README
│   │   ├── env.py           # Migration environment
│   │   ├── script.py.mako   # Migration template
│   │   └── versions/        # Migration versions
│   └── tables/
│       ├── __init__.py
│       ├── base.py          # SQLAlchemy base models
│       ├── agents.py        # Agent configuration tables
│       ├── teams.py         # Team configuration tables
│       ├── workflows.py     # Workflow configuration tables
│       └── config_history.py # Configuration audit trail
│
# NEW: Workspace Management (from demo-app)
├── workspace/
│   ├── __init__.py
│   ├── settings.py          # Workspace configuration
│   ├── dev_resources.py     # Development resources
│   ├── prd_resources.py     # Production resources
│   └── example_secrets/
│       ├── dev_api_secrets.yml
│       ├── prd_api_secrets.yml
│       └── prd_db_secrets.yml
│
# NEW: Utilities (from demo-app)
├── utils/
│   ├── __init__.py
│   ├── log.py               # Enhanced logging with Rich
│   └── dttm.py              # Date/time utilities
│
# NEW: Enhanced Testing (from demo-app)
├── tests/
│   ├── __init__.py
│   ├── evals/               # Evaluation tests
│   │   ├── __init__.py
│   │   ├── test_agent_accuracy.py
│   │   ├── test_workflow_performance.py
│   │   └── test_team_coordination.py
│   ├── unit/                # Unit tests
│   │   ├── test_agents.py
│   │   ├── test_teams.py
│   │   └── test_workflows.py
│   └── integration/         # Integration tests
│       ├── test_api.py
│       └── test_end_to_end.py
│
# NEW: Scripts (from demo-app)
├── scripts/
│   ├── _utils.sh            # Utility functions
│   ├── dev_setup.sh         # Development setup
│   ├── build_dev_image.sh   # Development Docker build
│   ├── build_prd_image.sh   # Production Docker build
│   ├── format.sh            # Code formatting
│   ├── test.sh              # Test runner
│   └── validate.sh          # Code validation
│
├── docker/
│   ├── Dockerfile
│   └── .dockerignore
│
├── docker-compose.yml
├── alembic.ini              # Database migrations
├── example.env              # Environment variables template
└── pyproject.toml           # UV dependencies
```

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

### NEW: Conversation Typification Workflow (Based on CSV Hierarchy)

**CRITICAL: Typification must follow the exact 5-level hierarchy from knowledge_rag.csv**

```yaml
# workflows/conversation_typification/config.yaml
workflow:
  id: "conversation_typification"
  name: "Tipificação Automática de Atendimento"
  description: "Análise hierárquica da conversa seguindo padrão PagBank"
  
storage:
  type: "postgres"
  table_name: "conversation_typification_workflows"
  url: "${DATABASE_URL}"
  mode: "workflow"
  auto_upgrade_schema: true

agents:
  # Step 1: Identify Business Unit
  business_unit_classifier:
    model:
      provider: "anthropic"
      id: "claude-haiku-4-20250514"
      max_tokens: 200
    tools:
      - conversation_analyzer
    instructions: |
      Analise a conversa e identifique a Unidade de Negócio.
      Opções válidas APENAS (exatamente como no CSV):
      - "Adquirência Web"
      - "Adquirência Web / Adquirência Presencial"
      - "Emissão"
      - "PagBank"
      
  # Step 2: Identify Product (based on Business Unit)
  product_classifier:
    model:
      provider: "anthropic"
      id: "claude-haiku-4-20250514"
      max_tokens: 200
    instructions: |
      Baseado na Unidade de Negócio selecionada, identifique o Produto.
      Use APENAS produtos válidos para a unidade escolhida.
      
  # Step 3: Identify Motive (based on Product)
  motive_classifier:
    model:
      provider: "anthropic"
      id: "claude-haiku-4-20250514"
      max_tokens: 300
    instructions: |
      Baseado no Produto selecionado, identifique o Motivo.
      Use APENAS motivos válidos para o produto escolhido.
      
  # Step 4: Identify Submotive (based on Motive)
  submotive_classifier:
    model:
      provider: "anthropic"
      id: "claude-sonnet-4-20250514"
      max_tokens: 500
    instructions: |
      Baseado no Motivo selecionado, identifique o Submotivo.
      Use APENAS submotivos válidos para o motivo escolhido.
      
  # Step 5: Generate Ticket
  ticket_generator:
    model:
      provider: "anthropic"
      id: "claude-haiku-4-20250514"
      max_tokens: 300
    tools:
      - ticket_system_integration
    instructions: |
      Gere ticket com a tipificação completa.
      Conclusão é sempre "Orientação".

flow:
  steps:
    - business_unit_classification
    - product_classification
    - motive_classification
    - submotive_classification
    - ticket_generation
  sequential: true  # Must be sequential for hierarchy
  
settings:
  timeout: 180  # 3 minutes for all steps
  structured_outputs: true
  enable_cache: false  # Always fresh analysis
```

```python
# workflows/conversation_typification/models.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from enum import Enum

# EXACT enums from knowledge_rag.csv hierarchy
class UnidadeNegocio(str, Enum):
    """Business Unit - Level 1 of hierarchy"""
    ADQUIRENCIA_WEB = "Adquirência Web"
    ADQUIRENCIA_WEB_PRESENCIAL = "Adquirência Web / Adquirência Presencial"
    EMISSAO = "Emissão"
    PAGBANK = "PagBank"

# Product mappings per Business Unit
PRODUCTS_BY_UNIT = {
    "Adquirência Web": ["Antecipação de Vendas"],
    "Adquirência Web / Adquirência Presencial": ["Antecipação de Vendas"],
    "Emissão": [
        "Cartão Múltiplo PagBank",
        "Cartão Múltiplo PagBank (débito internacional)",
        "Cartão PagBank Mastercard",
        "Cartão PagBank Visa",
        "Cartão Pré-Pago",
        "Cartão Pré-Pago Mastercard",
        "Cartão Pré-Pago Visa",
        "Cartão da Conta (débito)",
        "Cartão da Conta PagBank (débito Visa)",
        "Cartão da Conta Visa (débito)",
        "Cartão de Crédito PagBank"
    ],
    "PagBank": [
        "Aplicativo PagBank",
        "Conta PagBank",
        "Folha de Pagamento",
        "Pix",
        "Pix (Contatos Seguros)",
        "Portabilidade de Salário",
        "Recarga de Celular",
        "TED"
    ]
}

# Motives mapped to products (would need complete mapping from CSV)
MOTIVES_BY_PRODUCT = {
    "Antecipação de Vendas": [
        "Dúvidas sobre a Antecipação de Vendas",
        "Elegibilidade da Antecipação de Vendas",
        # ... other motives
    ],
    "Folha de Pagamento": [
        "Atualização da folha",
        "Como gerar arquivo CNAB",
        "Como liberar a folha dos meus colaboradores",
        # ... 14 total motives for payroll
    ],
    # ... complete mapping needed
}

class HierarchicalTypification(BaseModel):
    """Strict hierarchical typification following CSV structure"""
    
    # Level 1: Business Unit
    unidade_negocio: UnidadeNegocio = Field(..., description="Unidade de negócio")
    
    # Level 2: Product (validated based on business unit)
    produto: str = Field(..., description="Produto relacionado")
    
    # Level 3: Motive (validated based on product)
    motivo: str = Field(..., description="Motivo do atendimento")
    
    # Level 4: Submotive (validated based on motive)
    submotivo: str = Field(..., description="Submotivo específico")
    
    # Level 5: Conclusion (always "Orientação")
    conclusao: Literal["Orientação"] = Field(default="Orientação", description="Tipo de conclusão")
    
    @validator('produto')
    def validate_produto(cls, v, values):
        """Ensure product is valid for the selected business unit"""
        if 'unidade_negocio' in values:
            unit = values['unidade_negocio'].value
            valid_products = PRODUCTS_BY_UNIT.get(unit, [])
            if v not in valid_products:
                raise ValueError(f"Produto '{v}' inválido para unidade '{unit}'")
        return v
    
    @validator('motivo')
    def validate_motivo(cls, v, values):
        """Ensure motive is valid for the selected product"""
        if 'produto' in values:
            product = values['produto']
            valid_motives = MOTIVES_BY_PRODUCT.get(product, [])
            if valid_motives and v not in valid_motives:
                raise ValueError(f"Motivo '{v}' inválido para produto '{product}'")
        return v

class ConversationTypification(BaseModel):
    """Complete conversation typification with hierarchy"""
    
    # Session identification
    session_id: str = Field(..., description="ID da sessão do atendimento")
    customer_id: Optional[str] = Field(None, description="ID do cliente")
    ticket_id: Optional[str] = Field(None, description="ID do ticket gerado")
    
    # Hierarchical classification (REQUIRED)
    typification: HierarchicalTypification = Field(..., description="Tipificação hierárquica")
    
    # Conversation analysis
    conversation_summary: str = Field(..., description="Resumo da conversa")
    resolution_provided: str = Field(..., description="Resolução fornecida")
    
    # Metrics
    conversation_turns: int = Field(..., description="Número de interações")
    resolution_time_minutes: Optional[float] = Field(None, description="Tempo de resolução")
    escalated_to_human: bool = Field(False, description="Se foi escalado para humano")

class TicketCreationResult(BaseModel):
    """Resultado da criação/atualização de ticket"""
    
    ticket_id: str = Field(..., description="ID do ticket")
    action: str = Field(..., description="created ou updated")
    status: str = Field(..., description="Status do ticket")
    assigned_team: Optional[str] = Field(None, description="Equipe atribuída")
```

```python
# workflows/conversation_typification/workflow.py
from typing import Iterator, Union
from agno.workflow import Workflow, WorkflowCompletedEvent
from agno.agent import Agent, RunResponse
from agno.models.anthropic import Claude
from .models import ConversationTypification, TicketCreationResult

class ConversationTypificationWorkflow(Workflow):
    """Sequential workflow for hierarchical typification"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load complete hierarchy from CSV on initialization
        self.hierarchy = self._load_hierarchy_from_csv()
    
    def _load_hierarchy_from_csv(self):
        """Load complete typification hierarchy from knowledge_rag.csv"""
        import pandas as pd
        from collections import defaultdict
        
        # Parse CSV and extract hierarchy
        df = pd.read_csv("context/knowledge/knowledge_rag.csv")
        hierarchy = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        
        for _, row in df.iterrows():
            typification = row['typification']
            lines = typification.strip().split('\n')
            
            unit = lines[0].split(': ')[1]
            product = lines[1].split(': ')[1]
            motive = lines[2].split(': ')[1]
            submotive = lines[3].split(': ')[1]
            
            hierarchy[unit][product][motive].append(submotive)
        
        return dict(hierarchy)
    
    # Step 1: Business Unit Classifier
    business_unit_classifier: Agent = Agent(
        name="Business Unit Classifier",
        model=Claude(id="claude-haiku-4-20250514"),
        instructions="""
        Analise a conversa e selecione a Unidade de Negócio apropriada.
        
        Opções válidas (exatamente como aparece no CSV):
        1. "Adquirência Web" - Para antecipação de vendas online
        2. "Adquirência Web / Adquirência Presencial" - Para antecipação multi-canal
        3. "Emissão" - Para cartões (múltiplo, pré-pago, crédito, débito)
        4. "PagBank" - Para conta digital, Pix, TED, folha de pagamento, app
        
        Responda APENAS com uma das opções acima.
        """,
        response_model=BusinessUnitSelection,
        structured_outputs=True
    )
    
    # Dynamic agent creation for subsequent steps
    def create_product_classifier(self, business_unit: str) -> Agent:
        """Create product classifier with valid options for selected unit"""
        valid_products = list(self.hierarchy[business_unit].keys())
        
        return Agent(
            name="Product Classifier",
            model=Claude(id="claude-haiku-4-20250514"),
            instructions=f"""
            Baseado na Unidade de Negócio '{business_unit}', selecione o Produto.
            
            Opções válidas APENAS:
            {chr(10).join(f'- "{p}"' for p in valid_products)}
            
            Responda APENAS com uma das opções acima.
            """,
            response_model=ProductSelection,
            structured_outputs=True
        )
    
    def run(self, session_id: str, conversation_history: str) -> Iterator[WorkflowCompletedEvent]:
        """Execute hierarchical typification workflow"""
        
        # Step 1: Classify Business Unit
        unit_response = self.business_unit_classifier.run(
            f"Conversa:\n{conversation_history}"
        )
        business_unit = unit_response.content.unidade_negocio
        
        # Step 2: Classify Product (based on unit)
        product_classifier = self.create_product_classifier(business_unit)
        product_response = product_classifier.run(
            f"Unidade: {business_unit}\nConversa:\n{conversation_history}"
        )
        product = product_response.content.produto
        
        # Step 3: Classify Motive (based on product)
        motive_classifier = self.create_motive_classifier(business_unit, product)
        motive_response = motive_classifier.run(
            f"Produto: {product}\nConversa:\n{conversation_history}"
        )
        motive = motive_response.content.motivo
        
        # Step 4: Classify Submotive (based on motive)
        submotive_classifier = self.create_submotive_classifier(business_unit, product, motive)
        submotive_response = submotive_classifier.run(
            f"Motivo: {motive}\nConversa:\n{conversation_history}"
        )
        submotive = submotive_response.content.submotivo
        
        # Step 5: Generate final typification and ticket
        final_typification = HierarchicalTypification(
            unidade_negocio=business_unit,
            produto=product,
            motivo=motive,
            submotivo=submotive,
            conclusao="Orientação"
        )
        
        # Create ticket with complete typification
        ticket_result = self._create_ticket(session_id, final_typification, conversation_history)
        
        yield WorkflowCompletedEvent(
            run_id=self.run_id,
            content={
                "typification": final_typification.model_dump(),
                "ticket": ticket_result.model_dump(),
                "hierarchy_path": f"{business_unit} > {product} > {motive} > {submotive}",
                "status": "completed"
            }
        )

def get_conversation_typification_workflow(debug_mode: bool = False) -> ConversationTypificationWorkflow:
    return ConversationTypificationWorkflow(
        workflow_id="conversation-typification",
        storage=PostgresStorage(
            table_name="conversation_typification_workflows",
            db_url=db_url,
            mode="workflow",
            auto_upgrade_schema=True,
        ),
        debug_mode=debug_mode,
    )
```

### Typification as Workflow (Not Endpoint)

```python
# Usage: Run typification workflow at end of conversation
workflow = get_conversation_typification_workflow()

# Execute workflow
result = None
for event in workflow.run(session_id, conversation_history):
    if isinstance(event, WorkflowCompletedEvent):
        result = event.content

# Result contains structured typification + ticket info
typification = result["typification"]
ticket = result["ticket"]
```

### Advanced Playground Configuration (from demo-app)

```python
# api/routes/playground.py
from agno.playground import Playground

# Import all components
from agents.registry import AgentRegistry
from teams.registry import TeamRegistry
from workflows.registry import WorkflowRegistry

# Create unified playground
playground = Playground(
    agents=AgentRegistry.list_all(),
    workflows=WorkflowRegistry.list_all(),
    teams=TeamRegistry.list_all(),
)

# Register with Agno platform (production feature)
if settings.runtime_env == "prd":
    playground.register_app_on_platform()

playground_router = playground.get_router()
```

### API Implementation (Scalable Structure)

```python
# api/routes/teams.py - All team endpoints in one file
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from teams.registry import TeamRegistry

router = APIRouter()

# Current endpoints
@router.get("")
async def list_teams():
    """List all teams with their configurations"""
    return TeamRegistry.list_teams()

@router.post("/{team_id}/runs")
async def run_team(team_id: str, request: TeamRunRequest):
    """Run team with message"""
    # Implementation

@router.get("/{team_id}/config")
async def get_team_config(team_id: str):
    """Get team YAML configuration"""
    # Return parsed YAML

@router.put("/{team_id}/config")
async def update_team_config(team_id: str, config: dict):
    """Hot reload team configuration"""
    # Update YAML and reload

# Future endpoints already structured
@router.get("/{team_id}/sessions")
async def get_team_sessions(team_id: str):
    """Get all sessions for team"""
    # Implementation

@router.post("/{team_id}/feedback")
async def submit_feedback(team_id: str, feedback: FeedbackRequest):
    """Submit feedback for team interaction"""
    # Implementation
```

### Team Factory with Mandatory YAML (Simplified Ana)

```python
# teams/ana/team.py
from pathlib import Path
import yaml
from agno.team import Team
from agno.models.anthropic import Claude
from agents.registry import AgentRegistry

def create_ana_team():
    """Create Ana team - Simple routing with Agno's built-in capabilities"""
    config_path = Path(__file__).parent / "config.yaml"
    
    if not config_path.exists():
        raise ValueError("config.yaml is MANDATORY for all teams")
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Model configuration with Claude 4
    model_config = config['model']
    model = Claude(
        id=model_config['id'],
        max_tokens=model_config.get('max_tokens', 2000),
        temperature=model_config.get('temperature', 0.7),
        thinking=model_config.get('thinking', {"type": "enabled", "budget_tokens": 1024})
    )
    
    # Get member agents from database
    members = []
    for agent_id in config['members']:
        agent = AgentRegistry.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        members.append(agent)
    
    # Create team - Ana IS the orchestrator with mode=config["team"]["mode"],  # From YAML
    team = Team(
        name=config['team']['name'],
        mode=config["team"]["mode"],  # From YAML
        role=config['team'].get('role'),
        model=model,
        members=members,
        instructions=config.get('instructions', ''),
        **config['settings']  # ALL settings from YAML
    )
    
    return team
```

### UV Dependencies (pyproject.toml) - Enhanced from demo-app

```toml
[project]
name = "pagbank-multiagents"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    # Core Agno framework
    "agno[aws]>=1.7.0",
    "anthropic>=0.31.0",
    "openai>=1.93.2",
    
    # FastAPI and web stack
    "fastapi[standard]>=0.110.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "httpx>=0.25.0",
    
    # Database stack (from demo-app)
    "alembic>=1.13.0",
    "sqlalchemy>=2.0.0",
    "psycopg[binary]>=3.1.0",
    "pgvector>=0.2.0",
    
    # Enhanced tools (from demo-app)
    "beautifulsoup4>=4.12.0",
    "newspaper4k>=0.9.0",
    "lxml_html_clean>=0.1.0",
    "duckduckgo-search>=4.0.0",
    "google-search-results>=2.4.0",
    "googlesearch-python>=1.2.0",
    "exa_py>=1.0.0",
    "yfinance>=0.2.0",
    
    # File processing
    "pypdf>=3.17.0",
    "python-docx>=0.8.0",
    "pillow>=10.0.0",
    
    # Configuration and utilities
    "pyyaml>=6.0",
    "pycountry>=22.0.0",
    "tiktoken>=0.5.0",
    "nest_asyncio>=1.5.0",
    "typer>=0.9.0",
    
    # Enhanced logging (from demo-app)
    "rich>=13.0.0",
    
    # Current PagBank dependencies
    "pandas>=2.0.0",
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
    "streamlit>=1.28.0",
    "plotly>=5.17.0",
]

[project.scripts]
serve = "api.main:run"
playground = "scripts.playground:main"
migrate = "scripts.migrate:main"
setup-dev = "scripts.dev_setup:main"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "black>=24.0.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
    "types-beautifulsoup4>=4.12.0",
    "types-Pillow>=10.0.0",
]

[tool.ruff]
line-length = 110
exclude = ["aienv*", ".venv*", "migrations/*"]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]
"migrations/*" = ["E501", "F401", "F403"]

[tool.mypy]
check_untyped_defs = true
no_implicit_optional = true
warn_unused_configs = true
plugins = ["pydantic.mypy"]
exclude = ["aienv*", ".venv*", "migrations/*"]

[[tool.mypy.overrides]]
module = ["pgvector.*", "agno.*", "exa_py.*", "yfinance.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
log_cli = true
testpaths = ["tests"]
addopts = "-v --tb=short"

[tool.alembic]
script_location = "db/migrations"
prepend_sys_path = ["."]
```

### Settings Compatibility Matrix

```yaml
# _docs/settings_compatibility.yaml
# Which settings work with what

team_only_settings:
  - show_members_responses         # Teams have members
  - stream_intermediate_steps      # Team processing steps
  - enable_agentic_context        # Team context sharing
  - share_member_interactions     # Member coordination
  - add_member_tools_to_system_message
  - get_member_information_tool
  - read_team_history

agent_only_settings:
  - introduction                  # Agent intro message
  - read_chat_history            # Agent history tool
  - read_tool_call_history       # Agent tool history
  - update_knowledge             # Agent knowledge updates
  - output_dir                   # Agent output settings
  - save_output_to_file
  - print_output

both_agent_and_team:
  - show_tool_calls
  - markdown
  - enable_agentic_memory
  - enable_user_memories
  - add_history_to_messages
  - num_history_runs
  - search_knowledge
  - tool_call_limit
  - reasoning
  - parse_response

model_specific_settings:
  anthropic_claude_4:
    thinking:                    # Claude 4 thinking mode
      - type: "enabled"
      - budget_tokens: 1024
    models:
      - claude-opus-4-20250514   # Most capable
      - claude-sonnet-4-20250514 # Balanced
      - claude-haiku-4-20250514  # Fast & cheap
      
  openai:
    response_format:             # OpenAI JSON mode
      type: "json_object"
    models:
      - gpt-4-turbo
      - gpt-4o
```

### NEW: Workflow Factory Pattern (from demo-app)

```python
# workflows/registry.py
from pathlib import Path
import yaml
from typing import Dict, List
from agno.workflow import Workflow
from agno.storage.postgres import PostgresStorage

class WorkflowRegistry:
    """Registry for managing all PagBank workflows"""
    
    _workflows: Dict[str, Workflow] = {}
    
    @classmethod
    def register_workflow(cls, workflow_id: str, workflow: Workflow):
        """Register a workflow in the registry"""
        cls._workflows[workflow_id] = workflow
    
    @classmethod
    def get_workflow(cls, workflow_id: str) -> Workflow:
        """Get workflow by ID"""
        if workflow_id not in cls._workflows:
            cls._load_workflow(workflow_id)
        return cls._workflows.get(workflow_id)
    
    @classmethod
    def list_all(cls) -> List[Workflow]:
        """List all registered workflows"""
        cls._load_all_workflows()
        return list(cls._workflows.values())
    
    @classmethod
    def _load_workflow(cls, workflow_id: str):
        """Load workflow from YAML configuration"""
        workflow_dir = Path(__file__).parent / workflow_id
        config_path = workflow_dir / "config.yaml"
        
        if not config_path.exists():
            raise ValueError(f"Workflow config not found: {config_path}")
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Import workflow class dynamically
        module_path = f"workflows.{workflow_id}.workflow"
        module = __import__(module_path, fromlist=["get_workflow"])
        workflow = module.get_workflow()
        
        cls._workflows[workflow_id] = workflow
    
    @classmethod
    def _load_all_workflows(cls):
        """Load all workflows from directory"""
        workflows_dir = Path(__file__).parent
        for workflow_dir in workflows_dir.iterdir():
            if workflow_dir.is_dir() and not workflow_dir.name.startswith('_'):
                if (workflow_dir / "config.yaml").exists():
                    cls._load_workflow(workflow_dir.name)
```

### NEW: Database Management (from demo-app)

```python
# db/session.py
from typing import Generator
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from db.settings import db_settings

# Create SQLAlchemy Engine using database URL
db_url: str = db_settings.get_db_url()
db_engine: Engine = create_engine(db_url, pool_pre_ping=True)

# Create SessionLocal class
SessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False, autoflush=False, bind=db_engine
)

def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

```python
# db/settings.py
from pydantic_settings import BaseSettings

class DatabaseSettings(BaseSettings):
    """Database settings from environment variables"""
    
    database_url: str = "postgresql://pagbank:password@localhost:5432/pagbank_agents"
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "pagbank_agents"
    database_user: str = "pagbank"
    database_password: str = "password"
    
    def get_db_url(self) -> str:
        """Get complete database URL"""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

db_settings = DatabaseSettings()
```

### NEW: Configuration Management Database Schema

```python
# db/tables/agents.py
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class AgentVersion(Base):
    """Simple agent version storage"""
    __tablename__ = "agent_versions"
    
    # Composite primary key: agent_id + version
    agent_id = Column(String(50), primary_key=True)
    version = Column(Integer, primary_key=True)  # 25, 26, 27, etc.
    
    # Core configuration (JSON storage for flexibility)
    agent_metadata = Column(JSONB)  # {id, name, role}
    model_config = Column(JSONB)    # {provider, id, max_tokens, temperature}
    settings = Column(JSONB)        # All agent settings
    tools = Column(JSONB)           # Tool configurations
    instructions = Column(Text)     # Agent instructions
    
    # Simple metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    notes = Column(Text)  # What changed

class TeamConfig(Base):
    """Runtime team configuration"""
    __tablename__ = "team_configs"
    
    team_id = Column(String(50), primary_key=True)
    config_version = Column(Integer, default=1)
    
    # Core configuration
    team_metadata = Column(JSONB)   # {id, name, role, mode}
    model_config = Column(JSONB)    # Model settings
    settings = Column(JSONB)        # All team settings
    members = Column(JSONB)         # List of member agent IDs
    storage_config = Column(JSONB)  # Storage configuration
    instructions = Column(Text)     # Team instructions
    
    # Metadata
    created_from_yaml = Column(String(255))
    last_updated = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(String(100))
    is_active = Column(Boolean, default=True)
```

```python
# db/tables/config_history.py
class ConfigHistory(Base):
    """Audit trail for all configuration changes"""
    __tablename__ = "config_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_type = Column(String(20))  # 'agent', 'team', 'workflow'
    resource_id = Column(String(50))
    config_version = Column(Integer)
    
    # Change tracking
    changed_fields = Column(JSONB)      # Which fields were modified
    old_config = Column(JSONB)          # Previous configuration
    new_config = Column(JSONB)          # New configuration
    change_reason = Column(String(255)) # Why the change was made
    
    # Metadata
    changed_at = Column(DateTime, default=datetime.utcnow)
    changed_by = Column(String(100))
    change_source = Column(String(50))  # 'api', 'yaml_migration', 'admin'
```

### Configuration Migration System (YAML → Database)

```python
# db/config_migrator.py
import yaml
from pathlib import Path
from typing import Dict, Any
from sqlalchemy.orm import Session
from db.tables.agents import AgentConfig, TeamConfig
from db.tables.config_history import ConfigHistory

class ConfigMigrator:
    """Migrates YAML configurations to database on startup"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def migrate_all_configs(self):
        """Load all YAML configs into database (like docker-compose up)"""
        self.migrate_agents()
        self.migrate_teams()
        self.migrate_workflows()
    
    def migrate_agents(self):
        """Load agent configs from YAML to DB"""
        agents_dir = Path("agents/specialists")
        
        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir() and not agent_dir.name.startswith('_'):
                config_path = agent_dir / "config.yaml"
                if config_path.exists():
                    self._migrate_agent_config(agent_dir.name, config_path)
    
    def _migrate_agent_config(self, agent_id: str, config_path: Path):
        """Migrate single agent YAML to database"""
        with open(config_path) as f:
            yaml_config = yaml.safe_load(f)
        
        # Check if already exists
        existing = self.db.query(AgentConfig).filter_by(agent_id=agent_id).first()
        
        if existing:
            # Skip if already migrated (don't overwrite runtime changes)
            return
        
        # Create new database record
        agent_config = AgentConfig(
            agent_id=agent_id,
            agent_metadata=yaml_config.get('agent', {}),
            model_config=yaml_config.get('model', {}),
            settings=yaml_config.get('settings', {}),
            tools=yaml_config.get('tools', []),
            instructions=yaml_config.get('instructions', ''),
            created_from_yaml=str(config_path),
            updated_by='yaml_migration'
        )
        
        self.db.add(agent_config)
        
        # Create history record
        history = ConfigHistory(
            resource_type='agent',
            resource_id=agent_id,
            config_version=1,
            new_config=yaml_config,
            change_reason='Initial migration from YAML',
            changed_by='system',
            change_source='yaml_migration'
        )
        
        self.db.add(history)
        self.db.commit()
```

### Database-Driven Configuration API

```python
# api/routes/agents.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.tables.agents import AgentConfig
from db.tables.config_history import ConfigHistory

@router.get("/{agent_id}/config")
async def get_agent_config(agent_id: str, db: Session = Depends(get_db)):
    """Get current runtime configuration from database"""
    config = db.query(AgentConfig).filter_by(
        agent_id=agent_id, is_active=True
    ).first()
    
    if not config:
        raise HTTPException(404, f"Agent {agent_id} not found")
    
    return {
        "agent": config.agent_metadata,
        "model": config.model_config,
        "settings": config.settings,
        "tools": config.tools,
        "instructions": config.instructions,
        "meta": {
            "version": config.config_version,
            "last_updated": config.last_updated,
            "source": "database"
        }
    }

@router.put("/{agent_id}/config")
async def update_agent_config(
    agent_id: str, 
    config_update: dict,
    reason: str = "API update",
    db: Session = Depends(get_db)
):
    """Update runtime configuration in database (NOT YAML file)"""
    
    # Get current config
    current = db.query(AgentConfig).filter_by(
        agent_id=agent_id, is_active=True
    ).first()
    
    if not current:
        raise HTTPException(404, f"Agent {agent_id} not found")
    
    # Store old config for history
    old_config = {
        "agent": current.agent_metadata,
        "model": current.model_config,
        "settings": current.settings,
        "tools": current.tools,
        "instructions": current.instructions
    }
    
    # Apply updates (merge, don't replace)
    if "model" in config_update:
        current.model_config = {**current.model_config, **config_update["model"]}
    if "settings" in config_update:
        current.settings = {**current.settings, **config_update["settings"]}
    if "instructions" in config_update:
        current.instructions = config_update["instructions"]
    
    # Increment version
    current.config_version += 1
    current.last_updated = datetime.utcnow()
    current.updated_by = "api_user"  # TODO: Get from auth
    
    # Create history record
    history = ConfigHistory(
        resource_type='agent',
        resource_id=agent_id,
        config_version=current.config_version,
        changed_fields=list(config_update.keys()),
        old_config=old_config,
        new_config=config_update,
        change_reason=reason,
        changed_by="api_user",
        change_source="api"
    )
    
    db.add(history)
    db.commit()
    
    # Hot reload agent in registry
    AgentRegistry.reload_from_database(agent_id)
    
    return {"status": "updated", "version": current.config_version}

@router.post("/{agent_id}/config/reset")
async def reset_agent_config(agent_id: str, db: Session = Depends(get_db)):
    """Reset to original YAML configuration"""
    
    current = db.query(AgentConfig).filter_by(
        agent_id=agent_id, is_active=True
    ).first()
    
    if not current:
        raise HTTPException(404, f"Agent {agent_id} not found")
    
    # Load original YAML
    yaml_path = Path(current.created_from_yaml)
    if not yaml_path.exists():
        raise HTTPException(400, "Original YAML file not found")
    
    with open(yaml_path) as f:
        yaml_config = yaml.safe_load(f)
    
    # Reset to YAML values
    current.agent_metadata = yaml_config.get('agent', {})
    current.model_config = yaml_config.get('model', {})
    current.settings = yaml_config.get('settings', {})
    current.tools = yaml_config.get('tools', [])
    current.instructions = yaml_config.get('instructions', '')
    current.config_version += 1
    current.last_updated = datetime.utcnow()
    current.updated_by = "yaml_reset"
    
    db.commit()
    
    # Hot reload
    AgentRegistry.reload_from_database(agent_id)
    
    return {"status": "reset", "version": current.config_version}

@router.get("/{agent_id}/config/history")
async def get_config_history(agent_id: str, db: Session = Depends(get_db)):
    """Get configuration change audit trail"""
    history = db.query(ConfigHistory).filter_by(
        resource_type='agent',
        resource_id=agent_id
    ).order_by(ConfigHistory.changed_at.desc()).limit(50).all()
    
    return [
        {
            "version": h.config_version,
            "changed_at": h.changed_at,
            "changed_by": h.changed_by,
            "change_reason": h.change_reason,
            "changed_fields": h.changed_fields,
            "source": h.change_source
        }
        for h in history
    ]
```

### Agent Registry (Database-Driven)

```python
# agents/registry.py
from typing import Dict, Optional
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.tables.agents import AgentConfig
from agno.agent import Agent

class AgentRegistry:
    """Agent registry that loads from database, not YAML"""
    
    _agents: Dict[str, Agent] = {}
    
    @classmethod
    def get_agent(cls, agent_id: str) -> Optional[Agent]:
        """Get agent (load from database if not cached)"""
        if agent_id not in cls._agents:
            cls._load_agent_from_database(agent_id)
        return cls._agents.get(agent_id)
    
    @classmethod
    def _load_agent_from_database(cls, agent_id: str):
        """Load agent configuration from database"""
        db = SessionLocal()
        try:
            config = db.query(AgentConfig).filter_by(
                agent_id=agent_id, is_active=True
            ).first()
            
            if not config:
                raise ValueError(f"Agent {agent_id} not found in database")
            
            # Create Agent from database config
            agent = Agent(
                name=config.agent_metadata['name'],
                agent_id=agent_id,
                model=cls._create_model_from_config(config.model_config),
                instructions=config.instructions,
                **config.settings  # All settings from database
            )
            
            cls._agents[agent_id] = agent
        finally:
            db.close()
    
    @classmethod
    def reload_from_database(cls, agent_id: str):
        """Hot reload agent from updated database config"""
        if agent_id in cls._agents:
            del cls._agents[agent_id]
        cls._load_agent_from_database(agent_id)
```

### NEW: Workspace Management (from demo-app)

```python
# workspace/settings.py
from pathlib import Path

# Workspace configuration
WS_NAME = "pagbank-multiagents"
WS_ROOT = Path(__file__).parent.parent.resolve()

# Environment names
DEV_ENV = "dev"
PRD_ENV = "prd"

# Resource naming
DEV_KEY = f"{WS_NAME}-{DEV_ENV}"
PRD_KEY = f"{WS_NAME}-{PRD_ENV}"

# AWS settings for production deployment
AWS_REGION = "us-east-1"
AWS_PROFILE = "pagbank"

# Image settings
IMAGE_REPO = "pagbank"
BUILD_IMAGES = True
```

## Implementation Steps - Enhanced with Demo App Features

### Application Startup Process (YAML → Database Migration)

```python
# api/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from db.session import db_engine
from db.tables.base import Base
from db.config_migrator import ConfigMigrator
from db.session import SessionLocal

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    
    # 1. Create database tables
    Base.metadata.create_all(bind=db_engine)
    
    # 2. Migrate YAML configs to database (like docker-compose up)
    db = SessionLocal()
    try:
        migrator = ConfigMigrator(db)
        migrator.migrate_all_configs()
        print("✅ Configuration migration complete")
    finally:
        db.close()
    
    # 3. Start application
    yield
    
    # Cleanup on shutdown
    print("🛑 Application shutdown")

app = FastAPI(
    title="PagBank Multi-Agent Platform",
    version="1.0.0",
    lifespan=lifespan
)
```

### Configuration Flow Architecture

```
┌─────────────────┐    startup     ┌──────────────────┐    runtime     ┌─────────────────┐
│   YAML Files    │   ──────────►  │    Database      │   ──────────► │   Live Agents   │
│                 │   migration    │                  │   API calls   │                 │
│ agents/*/       │                │ agent_configs    │               │ AgentRegistry   │
│ config.yaml     │                │ team_configs     │               │ TeamRegistry    │
│                 │                │ config_history   │               │ WorkflowRegistry│
│ (Source of      │                │                  │               │                 │
│  Truth for      │                │ (Runtime State)  │               │ (Live Objects)  │
│  Deployment)    │                │                  │               │                 │
└─────────────────┘                └──────────────────┘               └─────────────────┘
         │                                   │                                   │
         │ Manual edits                      │ API updates                       │
         │ (version control)                 │ (hot reloading)                   │
         ▼                                   ▼                                   ▼
┌─────────────────┐                ┌──────────────────┐               ┌─────────────────┐
│ Git Repository  │                │ Audit Trail      │               │ Zero Downtime   │
│ config.yaml     │                │ config_history   │               │ Updates         │
│ changes         │                │ who/what/when    │               │                 │
└─────────────────┘                └──────────────────┘               └─────────────────┘
```

### Week 1: Core Infrastructure & Ana Simplification
1. Setup UV project structure with all dependencies  
2. **Refactor Ana**: Move orchestrator logic to teams/ana/team.py (simple Team with mode=config["team"]["mode"])
3. Implement database management with Alembic migrations
4. Create configuration tables (agent_versions, team_configs, config_history)
5. Implement YAML-to-database migration system
6. Create workspace management for dev/prd environments
7. Setup enhanced logging with Rich

### Week 2: Typification Workflow Implementation
1. **Extract complete hierarchy from knowledge_rag.csv**
2. Build hierarchy loader that parses CSV typification structure
3. Create sequential typification workflow with 5 steps:
   - Business Unit selection (4 options)
   - Product selection (filtered by unit)
   - Motive selection (filtered by product)
   - Submotive selection (filtered by motive)
   - Ticket generation with "Orientação" conclusion
4. Implement Pydantic models with hierarchical validation
5. Test workflow with real CSV data

### Week 3: Database-Driven Configuration & Versioning
1. Implement simple agent versioning (v25, v26, v27 style)
2. Create database configuration API endpoints
3. Implement version-specific routing: `/v1/agents/{agent_id}/v{version}/runs`
4. Create config.yaml for Ana team (simplified)
5. Create config.yaml for each specialist agent  
6. Update registries to load from database
7. Test hot reloading without YAML file changes

### Week 4: Advanced Playground & API
1. Implement unified playground for agents, teams, workflows
2. Add platform registration capabilities
3. Create comprehensive API endpoints
4. Implement streaming responses for all components
5. Add configuration management endpoints

### Week 5: Testing & Production Ready
1. Setup evaluation framework with evals/ directory
2. Create comprehensive unit and integration tests
3. Implement database migrations
4. Setup Docker deployment with scripts
5. Add monitoring and analytics endpoints

### Week 6: Documentation & Polish
1. Create settings compatibility matrix
2. Document YAML examples for each component
3. API documentation (auto-generated)
4. Migration guide from current system
5. Production deployment guide

## What We Get - Complete Platform Capabilities

### Core Infrastructure (Enhanced from demo-app)
1. **Mandatory YAML configs** - No hidden defaults, explicit configuration
2. **UV-based project** - Modern Python packaging with comprehensive dependencies
3. **Scalable API structure** - Production-ready endpoints for all components
4. **Database migrations** - Alembic integration for schema management
5. **Workspace management** - Dev/prod environment separation

### Agent & Team Capabilities
6. **Claude 4 models** - Latest Opus, Sonnet, and Haiku with thinking mode
7. **Clear settings matrix** - Complete compatibility documentation
8. **Ana as proper team** - Clean orchestrator separation
9. **Agent registry** - Dynamic loading from YAML configurations
10. **Advanced tools integration** - Web search, finance tools, document processing

### NEW: Workflow Orchestration (from demo-app)
11. **Multi-agent workflows** - BlogPost, Investment, Onboarding patterns
12. **Workflow registry** - Factory pattern for dynamic workflow loading
13. **Structured outputs** - Pydantic models for reliable data exchange
14. **Conditional flows** - Complex business process automation
15. **Workflow caching** - Session state management across steps
16. **Parallel execution** - Concurrent agent collaboration

### Advanced Platform Features (from demo-app)
17. **Unified playground** - Single interface for agents, teams, workflows
18. **Platform registration** - Integration with app.agno.com
19. **Enhanced logging** - Rich formatting and detailed traceability
20. **Evaluation framework** - Built-in testing for agent performance
21. **Configuration management** - Hot reload capabilities via API
22. **Analytics endpoints** - Performance monitoring and insights

### Production Readiness (from demo-app)
23. **Docker-first deployment** - Complete containerization strategy
24. **Environment secrets** - Secure configuration management
25. **Database session management** - SQLAlchemy with proper pooling
26. **Migration scripts** - Automated deployment pipelines
27. **Testing framework** - Unit, integration, and evaluation tests
28. **Monitoring support** - Health checks and metrics endpoints

### Business Value for PagBank C-Level
29. **Infinite scalability** - Add new business units through YAML
30. **Cost optimization** - Claude 4 model selection per use case
31. **Compliance ready** - Audit trails and structured data flows
32. **Rapid deployment** - From concept to production in days
33. **Risk mitigation** - Comprehensive testing and validation
34. **Technical debt reduction** - Modern architecture and best practices

### Business Unit Examples Ready for Implementation
- **Conversation Typification** - Automatic conversation analysis and ticket generation (immediate need)
- **Future Workflows** - Can be added as needed for specific business processes

This comprehensive platform gives us explicit configuration with no magic, modern dependency management with UV, production-ready infrastructure from day one, and unlimited scalability for ALL PagBank business units through workflow orchestration.

## Configuration Management Architecture Benefits

### ✅ **YAML as Infrastructure as Code**
- **YAML files** = Source of truth for deployments (version controlled)
- **Database** = Runtime state for live operations (hot reloadable)
- **API** = Management interface for zero-downtime updates

### 🔄 **Real-World Configuration Scenarios**

#### Scenario 1: Emergency Model Switch
```bash
# Cards agent giving bad responses? Switch model instantly:
curl -X PUT /v1/agents/cards_specialist/config \
  -d '{"model": {"id": "claude-opus-4-20250514", "temperature": 0.3}}' \
  -H "Content-Type: application/json"

# Response: {"status": "updated", "version": 2}
# Result: Agent immediately uses new model, no restart needed
```

#### Scenario 2: A/B Testing
```bash
# Test higher temperature for investment agent:
curl -X PUT /v1/agents/investment_advisor/config \
  -d '{"model": {"temperature": 0.8}, "reason": "A/B test for creativity"}'

# Monitor performance, then reset if needed:
curl -X POST /v1/agents/investment_advisor/config/reset
# Result: Back to original YAML configuration
```

#### Scenario 3: Audit Trail
```bash
# Who changed what and when?
curl /v1/agents/cards_specialist/config/history

# Response:
[
  {
    "version": 3,
    "changed_at": "2024-07-12T14:30:00Z",
    "changed_by": "admin@pagbank.com",
    "change_reason": "Emergency fix for customer complaints",
    "changed_fields": ["model.temperature", "instructions"],
    "source": "api"
  },
  {
    "version": 2,
    "changed_at": "2024-07-12T09:15:00Z", 
    "changed_by": "system",
    "change_reason": "Initial migration from YAML",
    "source": "yaml_migration"
  }
]
```

#### Scenario 4: Production Deployment
```bash
# 1. Deploy new YAML configs
git push origin main

# 2. Restart service (YAML → Database migration)
docker-compose up -d

# 3. YAML configs now in database, ready for runtime updates
# 4. Any API changes preserve across restarts (database persisted)
```

### 🏗️ **Architecture Advantages**

1. **Zero Downtime Updates** - Change configurations without restarting
2. **Version Control** - YAML files tracked in Git for deployment consistency  
3. **Audit Trail** - Every change logged with who/what/when
4. **Rollback Safety** - Reset to YAML defaults anytime
5. **Environment Consistency** - Same YAML deploys to dev/staging/prod
6. **Hot Configuration** - Runtime adjustments for performance tuning
7. **Change Management** - Controlled through API with proper authorization

### 🎯 **Business Impact**

- **Faster Incident Response** - Fix agent issues in seconds, not hours
- **Safe Experimentation** - A/B test configurations with instant rollback
- **Compliance Ready** - Complete audit trail for regulatory requirements

## Implementation Timeline & Migration Strategy

### Phase 1: Foundation (Week 1-2)
**Goal: Simplify current architecture and prepare for platform**

1. **Refactor Ana Team** (2 days)
   - Remove 400+ line orchestrator.py 
   - Create simple teams/ana/team.py using Team with mode=config["team"]["mode"]
   - Move routing logic to Ana's instructions in config.yaml
   - Test that all current functionality still works

2. **Setup Database Infrastructure** (3 days)
   - Create PostgreSQL database schema with Alembic
   - Implement configuration tables (agents, teams, workflows)
   - Build config migrator for YAML → Database
   - Add audit trail tables

3. **Create Base API Structure** (3 days)
   - Copy exact structure from agent-api repository
   - Implement core endpoints (agents, teams, health)
   - Add database session management
   - Setup UV dependencies and Docker

4. **Migrate Existing Agents** (2 days)
   - Convert current specialists to new structure
   - Create mandatory YAML configs for each
   - Test with Ana team integration

### Phase 2: Platform Core (Week 3-4)
**Goal: Build production-ready platform features**

1. **Agent Versioning System** (3 days)
   - Implement version storage (v25, v26, v27 style)
   - Add version-specific endpoints
   - Create version management API
   - Test version switching

2. **Typification Workflow** (4 days)
   - Extract complete hierarchy from knowledge_rag.csv
   - Build sequential classification workflow
   - Create validation for each hierarchy level
   - Integrate with ticket system

3. **Configuration Hot Reload** (3 days)
   - Implement runtime config updates via API
   - Add configuration history tracking
   - Create rollback mechanisms
   - Test zero-downtime updates

### Phase 3: Production Features (Week 5-6)
**Goal: Add enterprise features for scalability**

1. **Enhanced Monitoring** (3 days)
   - Add Prometheus metrics
   - Create performance dashboards
   - Implement health checks
   - Add alerting for failures

2. **Advanced Playground** (2 days)
   - Setup unified playground for all components
   - Add workflow testing capabilities
   - Create demo scenarios
   - Build interactive documentation

3. **Security & Compliance** (3 days)
   - Add API authentication
   - Implement role-based access
   - Create audit logging
   - Add data encryption

4. **Load Testing & Optimization** (2 days)
   - Performance benchmarks
   - Database query optimization
   - Caching implementation
   - Horizontal scaling tests

### Migration Checklist

#### Pre-Migration
- [ ] Backup current system
- [ ] Document all custom routing logic
- [ ] Map all agent dependencies
- [ ] Create rollback plan

#### During Migration
- [ ] Run old and new systems in parallel
- [ ] Migrate one agent at a time
- [ ] Validate each migration step
- [ ] Monitor for errors

#### Post-Migration
- [ ] Verify all functionality
- [ ] Performance comparison
- [ ] Update documentation
- [ ] Train operations team

### Success Metrics

1. **Technical Metrics**
   - API response time < 200ms (p95)
   - Configuration update time < 5 seconds
   - Zero downtime deployments
   - 99.9% uptime SLA

2. **Business Metrics**
   - New agent deployment time < 1 hour
   - Configuration changes without engineering
   - Complete audit trail for compliance
   - Support for 50+ agents

### Risk Mitigation

1. **Technical Risks**
   - Database becomes bottleneck → Use caching and read replicas
   - Complex migrations fail → Incremental approach with rollbacks
   - Performance degradation → Load testing before production

2. **Business Risks**
   - Team resistance to change → Show immediate benefits
   - Training requirements → Create comprehensive documentation
   - Migration disruption → Parallel running with gradual cutover

### Next Steps

1. **Immediate Actions**
   - Review and approve this strategy
   - Allocate development resources
   - Setup development environment
   - Begin Phase 1 implementation

2. **Communication Plan**
   - Weekly progress updates
   - Demo sessions after each phase
   - Stakeholder feedback loops
   - Documentation updates

This platform transformation will position PagBank as a leader in AI-powered customer service, enabling rapid innovation and seamless scaling across all business units.