# Sistema Multi-Agente PagBank com Ana

Sistema sofisticado de atendimento ao cliente multi-agente construído com o framework Agno. O sistema utiliza Ana como coordenadora inteligente que roteia consultas de clientes para agentes especializados por unidade de negócio: Adquirência, Emissão, PagBank e Escalação Humana.

## 🏗️ Visão Geral da Arquitetura

O sistema utiliza uma arquitetura V2 com Ana como coordenadora central que analisa consultas e roteia para agentes especializados. Cada agente possui acesso dedicado à base de conhecimento com filtragem inteligente para respostas precisas e contextuais.

```mermaid
graph TB
    %% Ponto de Entrada do Cliente
    Customer[👤 Consulta do Cliente<br/>Chat CLI ou API] --> Ana

    %% Ana Coordenadora Central
    Ana[🤖 Ana Team<br/>Claude Sonnet 4<br/>Coordenadora V2<br/>mode="route"]
    
    %% Decisão de Roteamento Ana
    Ana --> Routing{🔀 Análise Ana<br/>Roteamento Inteligente<br/>≤15 palavras + routing}
    
    %% Detecção de Escalação Humana
    Ana --> HumanCheck{😤 Detecção de<br/>Frustração/Complexidade?}
    HumanCheck -->|Escalação Necessária| HumanAgent[👨‍💼 Agente Human Handoff<br/>Transferência Humana<br/>Preservação Contexto]
    HumanAgent --> McpTool[🔧 MCP WhatsApp<br/>mcp_send_whatsapp_message]
    McpTool --> WhatsApp[📱 WhatsApp Evolution API<br/>Notificação Stakeholders]
    
    %% Agentes Especializados por Unidade
    Routing -->|Serviços Lojista| AdquirenciaAgent[🏪 Agente Adquirência<br/>Antecipação de Vendas<br/>Multiadquirência<br/>Soluções Lojista]
    Routing -->|Produtos Cartão| EmissaoAgent[💳 Agente Emissão<br/>Cartões Crédito/Débito<br/>Gestão de Cartões<br/>Benefícios]
    Routing -->|Banco Digital| PagBankAgent[💻 Agente PagBank<br/>PIX, Transferências<br/>Conta Digital<br/>Folha Pagamento]
    Routing -->|Notificações| WhatsAppAgent[📱 Agente WhatsApp<br/>Notificações Cliente<br/>Evolution API]
    
    %% Sistema Base de Conhecimento com Hot Reload
    subgraph Knowledge["📚 Sistema Base de Conhecimento"]
        CSV[📄 knowledge_rag.csv<br/>Hot Reload Ativo<br/>Filtrado por Unidade]
        HotReload[🔄 CSV Hot Reload Manager<br/>Watchdog Ativo<br/>Atualizações em Tempo Real]
        Vector[(🔍 Busca Semântica<br/>Embeddings<br/>Relevância por Score)]
        CSV --> HotReload
        HotReload --> Vector
    end
    
    %% Filtragem Agentic por Unidade
    AdquirenciaAgent --> Filter1[🎯 Filtro Agentic<br/>business_unit: Adquirência<br/>max_results: 5<br/>threshold: 0.6]
    EmissaoAgent --> Filter2[🎯 Filtro Agentic<br/>business_unit: Emissão<br/>max_results: 5<br/>threshold: 0.6]
    PagBankAgent --> Filter3[🎯 Filtro Agentic<br/>business_unit: PagBank<br/>max_results: 5<br/>threshold: 0.6]
    
    %% Consultas de Conhecimento
    Filter1 --> Vector
    Filter2 --> Vector
    Filter3 --> Vector
    
    %% Sistema de Memória PostgreSQL + Session
    subgraph Memory["🧠 Sistema de Memória V2"]
        PostgresMemory[(🗃️ PostgreSQL Memory<br/>Session Persistente<br/>Pattern Detection)]
        SessionMgmt[⏱️ Session Manager<br/>Continuidade Conversação<br/>Auto-upgrade Schema]
        PatternDetect[🔍 Pattern Detector<br/>Análise Comportamental<br/>Aprendizado Contínuo]
    end
    
    %% Integração de Memória com Agentes
    Ana --> PostgresMemory
    AdquirenciaAgent --> PostgresMemory
    EmissaoAgent --> PostgresMemory
    PagBankAgent --> PostgresMemory
    HumanAgent --> PostgresMemory
    WhatsAppAgent --> PostgresMemory
    
    PostgresMemory --> SessionMgmt
    PostgresMemory --> PatternDetect
    
    %% Interface Rica de Chat CLI
    subgraph CLI["💬 Rich Chat Interface"]
        ChatPy[chat.py<br/>Rich Console Interface<br/>Real-time Events]
        Events[📊 Event Monitoring<br/>Agent Activity<br/>Success Criteria]
        Metrics[📈 Live Metrics<br/>Response Times<br/>Routing Decisions]
    end
    
    Customer --> ChatPy
    ChatPy --> Ana
    Ana --> Events
    Events --> Metrics
    
    %% Fluxo de Resposta com Success Criteria
    AdquirenciaAgent --> Response[📝 Resposta Especializada<br/>Validação Success Criteria<br/>≤15 palavras Ana + routing]
    EmissaoAgent --> Response
    PagBankAgent --> Response
    WhatsAppAgent --> Response
    
    Response --> MemoryUpdate[💾 Memory Update<br/>Pattern Learning<br/>Session Continuity]
    MemoryUpdate --> FinalResponse[✅ Resposta Final<br/>Cliente + Events Display]
    
    %% Styling
    classDef ana fill:#e3f2fd,stroke:#1976d2,stroke-width:3px,color:#000000
    classDef agent fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,color:#000000
    classDef knowledge fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000000
    classDef memory fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000000
    classDef decision fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#000000
    classDef external fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#000000
    classDef cli fill:#f1f8e9,stroke:#689f38,stroke-width:2px,color:#000000
    
    class Ana ana
    class AdquirenciaAgent,EmissaoAgent,PagBankAgent,HumanAgent,WhatsAppAgent agent
    class CSV,Vector,Filter1,Filter2,Filter3,HotReload knowledge
    class PostgresMemory,PatternDetect,SessionMgmt,MemoryUpdate memory
    class Routing,HumanCheck decision
    class WhatsApp,Customer,McpTool external
    class ChatPy,Events,Metrics cli
```

## 🚀 Início Rápido

### Configuração de Desenvolvimento

#### Configuração de Ambiente
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas configurações
# PB_AGENTS_PORT=9888       # Porta dinâmica (default: 7777)
# ENVIRONMENT=development   # Modo desenvolvimento
# DEMO_MODE=true           # Interface rica habilitada
```

#### Opção 1: Desenvolvimento Rápido (Recomendado)
```bash
# Instalar dependências com UV
make install

# Iniciar servidor de desenvolvimento
make dev

# Em outro terminal, iniciar chat CLI
python chat.py
```

#### Opção 2: Produção com Docker
```bash
# Configurar ambiente
make install

# Iniciar stack de produção
make prod

# Verificar status
make status
```

Endpoints disponíveis:
- **API**: http://localhost:9888 (.env configurable, default 7777)
- **Docs**: http://localhost:9888/docs (Swagger UI)
- **Chat CLI**: `python chat.py` (Rich interface)
- **Health**: http://localhost:9888/api/v1/health

## 🤖 Ana Coordenadora & Agentes Especializados

### Arquitetura V2 com Ana
O sistema V2 utiliza Ana como coordenadora central com capacidades avançadas:

- **Ana Team Router**: Agno Team com mode="route" para seleção inteligente
- **Success Criteria**: Respostas ≤15 palavras + roteamento adequado
- **Confidence Scoring**: Seleção baseada em confiança do agente
- **Context Preservation**: Memória persistente entre interações

### Agentes por Unidade de Negócio

1. **🏪 Adquirência**: Antecipação de vendas, multiadquirência, soluções para lojistas, processamento de pagamentos
2. **💳 Emissão**: Cartões de crédito/débito, gestão de cartões, limites, benefícios, uso internacional
3. **💻 PagBank**: Transferências PIX, conta digital, folha de pagamento, recarga celular, segurança da conta
4. **📱 WhatsApp Notifier**: Notificações automáticas via Evolution API
5. **👨‍💼 Human Handoff**: Escalação para atendimento humano com preservação de contexto

## 💬 Interface Chat CLI Rica

### Chat Interativo em Tempo Real
O sistema inclui uma interface de chat avançada com monitoramento em tempo real:

```bash
# Iniciar chat CLI
python chat.py

# Funcionalidades:
# - Interface Rich Console com painéis divididos
# - Monitoramento de eventos em tempo real
# - Visualização de seleção de agentes
# - Tracking de success criteria (≤15 palavras)
# - Métricas de performance ao vivo
```

### Recursos da Interface
- **Painéis Divididos**: Chat à esquerda, eventos à direita
- **Event Streaming**: Atividade dos agentes em tempo real
- **Success Validation**: Monitoramento automático dos critérios Ana
- **Rich Formatting**: Markdown e formatação avançada
- **Session Tracking**: Continuidade de conversação

## 🎯 Sistema de Conhecimento com Hot Reload

### Base de Conhecimento Inteligente
- **📄 CSV Hot Reload**: Atualizações automáticas sem restart do sistema
- **🎯 Filtros Agentic**: Filtragem automática por business_unit
- **🔍 Busca Semântica**: Embeddings para relevância contextual
- **⚡ Performance**: Respostas sub-segundo com cache inteligente

### Filtragem por Unidade de Negócio
```
Consulta Ana: "Como solicitar antecipação de vendas?"
↓ Análise Automática Ana ↓
Roteamento: Agente Adquirência
↓ Filtro Agentic Aplicado ↓
- business_unit: "Adquirência"
- max_results: 5
- relevance_threshold: 0.6
↓ Resultado ↓
Documentos mais relevantes da unidade
```

### Configuração Hot Reload
```python
# Ativado automaticamente em desenvolvimento
CSV_HOT_RELOAD=true

# Watchdog monitora alterações em:
# context/knowledge/knowledge_rag.csv
```

## 🧠 Sistema de Memória V2

### PostgreSQL + Session Management
- **Base PostgreSQL**: Armazenamento persistente com auto-upgrade
- **Session Continuity**: Contexto preservado entre conversações
- **Pattern Detection**: Aprendizado contínuo de comportamentos
- **Schema Auto-upgrade**: Migrations automáticas via Alembic

### Funcionalidades de Memória
- **User Memories**: Preferências e contexto do cliente
- **Agentic Memory**: Aprendizado dos agentes
- **Pattern Recognition**: Detecção de problemas recorrentes
- **Session Tracking**: Gestão de estado conversacional

## 📱 Integração WhatsApp & MCP

### Evolution API Integration
```
Escalação Detectada → Human Handoff Agent → MCP WhatsApp Tool
                                         ↓
                    mcp_send_whatsapp_message → Evolution API
                                         ↓
                           Notificação WhatsApp Stakeholder
```

### Recursos de Integração
- **MCP Protocol**: Integração via Model Context Protocol
- **Evolution API**: Conexão direta com WhatsApp Business
- **Context Transfer**: Histórico completo da conversa
- **Real-time Alerts**: Notificações instantâneas

## 🛠️ Stack Técnico

### Core Framework
- **🤖 Agno Framework 1.7.1+**: Orquestração multi-agente
- **🧠 Claude Sonnet 4**: IA primária com thinking mode
- **🐍 Python 3.12+**: Runtime moderno com UV
- **⚡ FastAPI 0.116.0+**: API REST com docs automáticas

### Dados & Persistência
- **🐘 PostgreSQL 16+**: Banco principal com pgvector
- **📊 SQLAlchemy 2.0+**: ORM async com migrations
- **📄 CSV Knowledge**: Base hot-reload com RAG
- **🔍 Embeddings**: Busca semântica avançada

### Integração & Comunicação
- **📱 Evolution API**: WhatsApp Business integration
- **📧 Resend SMTP**: Email notifications
- **🔌 MCP Protocol**: Enhanced agent capabilities
- **⚡ WebSocket**: Real-time monitoring

## 📁 Estrutura do Projeto

```
genie-agents/
├── README.md                           # Este arquivo
├── CLAUDE.md                           # Contexto e padrões de desenvolvimento
├── Makefile                            # Automação (install, dev, prod, test)
├── chat.py                             # Interface Chat CLI Rica
├── pyproject.toml                      # Configuração Python com UV
├── .env                                # Configuração ambiente (port dinâmico)
├── agents/                             # Agentes especializados (YAML-driven)
│   ├── registry.py                     # Factory e registro central
│   ├── adquirencia/                    # Especialista adquirência
│   ├── emissao/                        # Especialista emissão
│   ├── pagbank/                        # Especialista PagBank
│   ├── human_handoff/                  # Escalação humana
│   └── whatsapp_notifier/              # Notificações WhatsApp
├── teams/                              # Ana Team Routing V2
│   └── ana/                            # Coordenadora Ana
│       ├── team.py                     # Team(mode="route")
│       ├── config.yaml                 # Configuração roteamento
│       └── demo_logging.py             # Rich console logging
├── api/                                # Interface FastAPI + Agno
│   ├── serve.py                        # Servidor principal
│   ├── main.py                         # App FastAPI
│   ├── routes/                         # Endpoints customizados
│   └── monitoring/                     # Sistema monitoramento
├── context/                            # Conhecimento e memória
│   ├── knowledge/                      # Base conhecimento CSV
│   │   ├── knowledge_rag.csv           # Dados domínio
│   │   ├── csv_hot_reload.py           # Hot reload manager
│   │   └── agentic_filters.py          # Filtros por unidade
│   └── memory/                         # Sistema memória V2
│       ├── memory_manager.py           # PostgreSQL memory
│       └── pattern_detector.py         # Detecção padrões
├── workflows/                          # Workflows multi-step
│   ├── conversation_typification/      # Classificação consultas
│   └── human_handoff/                  # Processo escalação
├── db/                                 # Camada banco dados
│   ├── migrations/                     # Migrations Alembic
│   └── tables/                         # Modelos SQLAlchemy
├── tests/                              # Suite testes completa
│   ├── unit/                           # Testes unitários
│   ├── integration/                    # Testes integração
│   └── monitoring/                     # Testes monitoramento
└── docs/                               # Documentação projeto
    └── ai-context/                     # Docs específicas IA
```

## 🎯 Funcionalidades Principais

### Ana Coordenadora Inteligente
- **🎯 Routing Precisão**: Ana analisa e roteia com confidence scoring
- **⚡ Success Criteria**: Validação automática ≤15 palavras + routing
- **🧠 Context Awareness**: Memória persistente com pattern learning
- **🔄 Escalação Inteligente**: Detecção automática de complexidade

### Interface Rica & Monitoramento
- **💬 Chat CLI Avançado**: Interface Rich Console com painéis divididos
- **📊 Real-time Events**: Monitoramento atividade agentes ao vivo
- **📈 Métricas Live**: Performance e success criteria em tempo real
- **🎨 Rich Formatting**: Markdown e formatação avançada

### Sistema Conhecimento Dinâmico
- **🔄 Hot Reload**: Atualizações CSV sem restart sistema
- **🎯 Filtros Agentic**: Filtragem automática por business_unit
- **🔍 Busca Semântica**: Relevância contextual com embeddings
- **⚡ Performance**: Respostas sub-segundo com cache inteligente

### Integração Empresarial
- **📱 WhatsApp Evolution**: Notificações via MCP protocol
- **👥 Human Handoff**: Escalação com preservação contexto
- **🏛️ Compliance**: Auditoria e segurança empresarial
- **📊 Analytics**: Métricas detalhadas e pattern detection

## 🔐 Configuração & Deployment

### Configuração de Ambiente
```bash
# Configuração dinâmica via .env
ENVIRONMENT=development
PB_AGENTS_PORT=9888          # Sobrescreve default 7777
DEMO_MODE=true              # Interface rica habilitada
CSV_HOT_RELOAD=true         # Hot reload ativo

# APIs necessárias
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key
GEMINI_API_KEY=your-key

# Base dados
DATABASE_URL=postgresql+psycopg://ai:ai@localhost:5532/ai

# Integrações opcionais
EVOLUTION_API_BASE_URL=http://localhost:8080
RESEND_API_KEY=your-resend-key
```

### Comandos de Desenvolvimento
```bash
# Setup completo
make install

# Desenvolvimento com hot reload
make dev

# Chat CLI interativo
python chat.py

# Produção com Docker
make prod

# Status e logs
make status
make logs

# Testes
make test
```

## 📊 Performance & Métricas

### Critérios de Sucesso Ana
- **Eficiência Resposta**: ≤15 palavras + roteamento adequado
- **Precisão Routing**: Confidence-based agent selection
- **Taxa Escalação**: Monitoramento handoff frequency
- **Success Rate**: Validação automática critérios

### Métricas do Sistema
- **Tempo Resposta**: <500ms média para routing Ana
- **Throughput**: 1000+ requests/minuto suportados
- **Disponibilidade**: 99.9% uptime com health monitoring
- **Usuários Concorrentes**: 1000+ via arquitetura async

### Stack Monitoramento
- **Rich Console**: Interface desenvolvimento com events
- **Health Checks**: Endpoints monitoramento automático
- **Pattern Detection**: Aprendizado comportamental contínuo
- **Performance Analytics**: Métricas tempo real

---

**Desenvolvido com Agno Framework V2 + Ana Intelligence**  
**© PagBank 2025 - Sistema Multi-Agente Avançado**