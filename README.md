# Sistema Multi-Agente de Atendimento PagBank

Sistema sofisticado de atendimento ao cliente multi-agente construído com o framework Agno. O sistema roteia consultas de clientes para agentes especializados por unidade de negócio: Adquirência, Emissão, PagBank e Escalação Humana.

## 🏗️ Visão Geral da Arquitetura

O sistema utiliza uma arquitetura de orquestração inteligente onde o Orquestrador Principal roteia consultas de clientes para agentes especializados. Cada agente possui acesso dedicado à base de conhecimento com filtragem inteligente para respostas precisas e contextuais.

```mermaid
graph TB
    %% Customer Entry Point
    Customer[👤 Customer Query<br/>Portuguese Language] --> Orchestrator

    %% Main Orchestrator
    Orchestrator[🎯 Main Orchestrator<br/>Claude Sonnet 4<br/>Query Analysis & Routing]
    
    %% Routing Decision
    Orchestrator --> Routing{🔀 Business Unit Routing}
    
    %% Human Handoff Detection
    Orchestrator --> HumanCheck{😤 Frustration<br/>Detection?}
    HumanCheck -->|Level 3+| HumanAgent[👨‍💼 Human Handoff Agent<br/>WhatsApp Integration]
    HumanAgent --> WhatsApp[📱 WhatsApp Evolution API<br/>Direct HTTP Integration]
    
    %% Business Unit Agents
    Routing -->|Merchant Services| AdquirenciaAgent[🏪 Adquirência Agent<br/>Sales Advance<br/>Multi-acquirer Services]
    Routing -->|Card Products| EmissaoAgent[💳 Emissão Agent<br/>Credit/Debit Cards<br/>Card Management]
    Routing -->|Digital Banking| PagBankAgent[💻 PagBank Agent<br/>PIX, Transfers<br/>Digital Account Services]
    
    %% Knowledge Base System
    subgraph Knowledge["📚 Knowledge Base System"]
        CSV[📄 CSV Knowledge<br/>622 Documents<br/>Business Unit Filtered]
        Vector[(🔍 Vector Database<br/>OpenAI Embeddings<br/>Semantic Search)]
        CSV --> Vector
    end
    
    %% Business Unit Filtering
    AdquirenciaAgent --> Filter1[🎯 Business Filter<br/>unit: adquirencia<br/>Merchant-focused]
    EmissaoAgent --> Filter2[🎯 Business Filter<br/>unit: emissao<br/>Card-focused]
    PagBankAgent --> Filter3[🎯 Business Filter<br/>unit: pagbank<br/>Banking-focused]
    
    %% Knowledge Queries
    Filter1 --> Vector
    Filter2 --> Vector
    Filter3 --> Vector
    
    %% Memory System
    subgraph Memory["🧠 Memory System"]
        AgnoMemory[(🗃️ Agno Memory v2<br/>SQLite Storage<br/>Cross-Session Context)]
        PatternDetect[🔍 Pattern Detection<br/>Learning System]
        SessionMgmt[⏱️ Session Management<br/>30min Timeout<br/>20 Turn Limit]
    end
    
    %% Memory Integration
    AdquirenciaAgent --> AgnoMemory
    EmissaoAgent --> AgnoMemory
    PagBankAgent --> AgnoMemory
    HumanAgent --> AgnoMemory
    Orchestrator --> AgnoMemory
    
    AgnoMemory --> PatternDetect
    AgnoMemory --> SessionMgmt
    
    %% Response Flow
    AdquirenciaAgent --> Response[📝 Agent Response<br/>Business Unit Specialized]
    EmissaoAgent --> Response
    PagBankAgent --> Response
    
    Response --> MemoryUpdate[💾 Memory Update<br/>Context Preservation]
    MemoryUpdate --> FinalResponse[✅ Final Response<br/>to Customer]
    
    %% Escalation System
    Response --> EscalationCheck{🚨 Escalation<br/>Needed?}
    EscalationCheck -->|Complex Case| TechnicalEsc[🔧 Technical Escalation<br/>Cross-Unit Support]
    EscalationCheck -->|No| FinalResponse
    
    %% Styling
    classDef agent fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef knowledge fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef memory fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef decision fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef external fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    
    class AdquirenciaAgent,EmissaoAgent,PagBankAgent,HumanAgent agent
    class CSV,Vector,Filter1,Filter2,Filter3 knowledge
    class AgnoMemory,PatternDetect,SessionMgmt,MemoryUpdate memory
    class Routing,HumanCheck,EscalationCheck decision
    class WhatsApp,Customer external
```

## 🚀 Início Rápido

### Configuração de Desenvolvimento

```bash
# Instalar dependências
uv sync

# Iniciar o sistema
uv run python playground.py
```

O sistema estará disponível em: http://localhost:7777

## 🤖 Agentes por Unidade de Negócio

### Arquitetura dos Agentes
Cada agente de unidade de negócio opera independentemente com:

- **Claude Sonnet 4**: Raciocínio avançado com capacidade de thinking
- **Filtragem por Unidade**: Filtragem especializada da base de conhecimento
- **Integração de Memória**: Contexto persistente entre conversas
- **Expertise de Domínio**: Conhecimento profundo para cada unidade de negócio

### Unidades de Negócio

1. **🏪 Adquirência**: Antecipação de vendas, multiadquirência, soluções para lojistas, processamento de pagamentos
2. **💳 Emissão**: Cartões de crédito/débito, gestão de cartões, limites, benefícios, uso internacional
3. **💻 PagBank**: Transferências PIX, conta digital, folha de pagamento, recarga celular, segurança da conta
4. **👨‍💼 Escalação Humana**: Gestão de escalações, integração WhatsApp, roteamento de casos complexos

## 🎯 Filtragem Inteligente de Conhecimento

### Sistema de Filtros por Unidade de Negócio
O sistema automaticamente aplica filtros precisos baseados nas unidades de negócio:

```
Consulta: "Como solicitar antecipação de vendas?"
↓ Análise Automática ↓
Filtros Aplicados:
- business_unit: "adquirencia" (contexto do agente)
- typification: auto-detectado da consulta
↓ Resultado ↓
Documentos mais relevantes da unidade de negócio
```

### Estrutura da Base de Conhecimento
- **📄 622 Documentos**: Conhecimento abrangente dos serviços
- **🎯 4 Colunas Principais**: 
  - `problem`: Descrição do problema/consulta
  - `solution`: Solução detalhada
  - `typification`: Classificação do tipo de atendimento
  - `business_unit`: Unidade de negócio responsável
- **🔍 Embeddings OpenAI**: Busca semântica rápida
- **🔄 Hot Reload**: Atualizações do CSV sem parada do sistema

## 🧠 Gestão de Memória e Contexto

### Integração Agno Memory v2
- **Persistência Entre Sessões**: Contexto do cliente mantido entre conversas
- **Detecção de Padrões**: Sistema aprende com problemas e comportamentos recorrentes
- **Estado Compartilhado**: Transferências perfeitas entre agentes
- **Limites de Conversa**: Sessões de 30 minutos com máximo de 20 turnos

### Funcionalidades de Memória
- **Contexto do Usuário**: Interações anteriores e preferências
- **Rastreamento de Problemas**: Histórico de resolução de problemas
- **Sistema de Aprendizado**: Melhoria adaptativa através de padrões
- **Trilha de Auditoria**: Log completo de interações para compliance

## 📱 Escalação Humana & Integração WhatsApp

### Detecção de Frustração
- **Monitoramento Automático**: Rastreamento em tempo real do nível de frustração
- **Trigger Nível 3**: Escalação imediata para agente humano
- **Preservação de Contexto**: Histórico completo da conversa transferido

### Integração WhatsApp Evolution API
```
Frustração Detectada → Agente de Escalação → Evolution API
                                          ↓
                        Chamada HTTP direta para serviço WhatsApp
                        com contexto completo da conversa
```

## 🛠️ Stack Técnico

- **🤖 Framework IA**: Sistema Multi-Agente Agno
- **🧠 LLM**: Claude Sonnet 4 com capacidade de thinking
- **💾 Memória**: SQLite com Agno Memory v2
- **🔍 Vector Store**: Banco vetorial com indexação
- **📄 Embeddings**: OpenAI text-embedding-3-small
- **🔧 Linguagem**: Python 3.12+ com gerenciamento UV

## 📁 Estrutura do Projeto

```
pagbank-multiagents/
├── agents/                    # Sistema de agentes por unidade de negócio
│   ├── orchestrator/
│   │   └── main_orchestrator.py    # Orquestrador principal de roteamento
│   ├── specialists/               # Agentes especializados por unidade
│   │   ├── base_agent.py         # Classe base dos agentes
│   │   ├── adquirencia_agent.py  # Agente de Adquirência
│   │   ├── emissao_agent.py      # Agente de Emissão
│   │   ├── pagbank_agent.py      # Agente PagBank
│   │   └── human_handoff_agent.py # Escalação humana
│   ├── prompts/                   # Prompts dos agentes
│   │   └── specialists/           # Prompts especializados por unidade
│   └── tools/                     # Ferramentas compartilhadas
├── orchestrator/              # Utilitários de orquestração
│   ├── clarification_handler.py   # Tratamento de esclarecimentos
│   ├── human_handoff_detector.py  # Detecção de frustração
│   ├── routing_logic.py           # Algoritmos de roteamento
│   └── state_synchronizer.py     # Gestão de estado
├── knowledge/                 # Sistema de base de conhecimento
│   ├── csv_knowledge_base.py      # Integração CSV
│   ├── enhanced_csv_reader.py     # Extração de metadados
│   ├── agentic_filters.py         # Filtragem inteligente
│   └── knowledge_rag.csv          # 622 entradas de conhecimento
├── memory/                    # Sistema de memória
│   ├── memory_manager.py          # Agno Memory v2
│   ├── pattern_detector.py        # Reconhecimento de padrões
│   └── session_manager.py         # Gestão de sessões
├── escalation_systems/        # Sistemas de escalação
│   ├── escalation_manager.py      # Coordenação de escalações
│   ├── feedback_human_systems/    # Sistema de feedback humano
│   └── ticket_system.py           # Sistema de tickets
├── config/                    # Configuração do sistema
├── data/                      # Bancos de dados SQLite
├── tests/                     # Testes automatizados
│   ├── unit/                      # Testes unitários
│   ├── integration/               # Testes de integração
│   └── performance/               # Testes de performance
├── scripts/                   # Scripts utilitários
└── playground.py              # Ponto de entrada do sistema
```

## 🎯 Funcionalidades Principais

### Inteligência & Automação
- **🎯 Filtragem de Precisão**: Filtros por unidade de negócio entregam respostas mais relevantes
- **🧠 Consciência de Contexto**: Conversas alimentadas por memória com capacidades de aprendizado
- **⚡ Performance**: Tempos de resposta sub-2-segundos com roteamento inteligente
- **🔄 Escalabilidade**: Agentes independentes com infraestrutura de conhecimento compartilhada

### Integração Humana
- **👥 Escalação Perfeita**: Detecção automática de frustração com notificações WhatsApp
- **📱 Evolution API**: Integração HTTP direta com serviço WhatsApp
- **📊 Transferência de Contexto**: Histórico completo de conversa preservado durante transferências
- **🎫 Sistema de Tickets**: Gestão estruturada e rastreamento de casos

### Gestão de Conhecimento
- **📚 Busca Inteligente**: Consultas em linguagem natural automaticamente filtradas
- **🔄 Hot Reload**: Atualizações de conhecimento em tempo real sem reinicialização
- **🎯 Expertise de Domínio**: Especialização por unidade de negócio
- **📈 Sistema de Aprendizado**: Melhoria contínua através de detecção de padrões

## 🔐 Segurança & Compliance

- **🔒 Privacidade de Dados**: Proteção de informações do cliente com trilhas de auditoria abrangentes
- **🏛️ Compliance Bancário**: Aderência total às regulamentações financeiras
- **📊 Garantia de Qualidade**: Validação de respostas e monitoramento de precisão
- **🛡️ Detecção de Fraude**: Reconhecimento avançado de padrões para ameaças de segurança
- **🔑 Controle de Acesso**: Permissões baseadas em função e integração segura de API

## 📊 Performance do Sistema

### Otimização de Resposta
- **Roteamento Inteligente**: Distribuição de consultas consciente de contexto entre agentes especializados
- **Filtragem de Precisão**: Redução significativa no espaço de busca através de filtragem por unidade
- **Eficiência de Memória**: Gestão de contexto persistente sem redundância
- **Tempo de Resposta**: < 2 segundos em média com respostas altamente relevantes e contextuais

### Métricas de Escalabilidade
- **Independência de Agentes**: Especialização por unidade sem overhead de coordenação
- **Eficiência de Conhecimento**: Filtragem reduz overhead de processamento
- **Escalabilidade de Memória**: Armazenamento e recuperação eficientes entre sessões
- **Distribuição de Carga**: Roteamento automático balanceia carga do sistema efetivamente

---

**Desenvolvido pela Namastex Labs & Yaitech usando o Framework Agno**  
**© PagBank 2025**