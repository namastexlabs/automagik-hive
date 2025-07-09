# Sistema Multi-Agente PagBank

Sistema sofisticado de atendimento ao cliente multi-agente desenvolvido com o framework Agno, projetado especificamente para as necessidades do mercado brasileiro do PagBank.

## 🚀 Início Rápido

```bash
uv sync
```

```bash
uv run python playground.py
```

**Interface web opcional (em outro terminal):**
```bash
cd agent-ui
pnpm install
pnpm dev
```

O sistema estará disponível em: http://localhost:7777  
Interface web (opcional): http://localhost:3000

## 📋 Visão Geral do Sistema

O Sistema Multi-Agente PagBank utiliza arquitetura simplificada com agentes únicos (não mais teams coordenados) para fornecer atendimento ao cliente inteligente em cinco domínios especializados. O sistema usa Agno Team em modo "route" para direcionar consultas aos agentes especialistas apropriados:

### Agentes Especialistas
- **Agente de Cartões** 💳 - Problemas com cartões de crédito/débito, limites, faturas
- **Agente de Conta Digital** 🏦 - PIX, transferências, saldo, extratos
- **Agente de Investimentos** 💰 - CDB, produtos de investimento, compliance
- **Agente de Crédito** 💸 - Empréstimos, FGTS, proteção contra fraudes
- **Agente de Seguros** 🛡️ - Produtos de seguro, sinistros, coberturas

### Recursos Principais
- 🇧🇷 Suporte nativo ao português brasileiro
- 📱 Notificação WhatsApp instantânea para transferências humanas
- 🗣️ Transferência imediata quando solicitado ("quero humano")
- 🚨 Detecção avançada de fraudes e prevenção de golpes
- 🧠 Memória persistente e reconhecimento de padrões
- 📚 Filtragem de conhecimento específico por agente
- 🤔 Capacidade de "thinking" para melhor raciocínio
- 🔄 Compartilhamento de contexto entre agentes
- ⚡ Otimização de tempo de resposta <2s


## 🏗️ Arquitetura

### Visão Geral do Sistema (Arquitetura Simplificada)

```mermaid
graph TB
    CLIENT[👤 Cliente] --> ORCH[🎯 Orquestrador Principal<br/>Team mode=route<br/>main_orchestrator.py]
    
    ORCH --> PREP[📝 Pré-processamento]
    PREP --> NORM[🔧 Normalização de Texto<br/>text_normalizer.py]
    PREP --> FRUST[😤 Detecção de Frustração<br/>frustration_detector.py]
    PREP --> ROUT[🎯 Lógica de Roteamento<br/>routing_logic.py]
    
    ORCH --> STATE[📊 Estado Compartilhado<br/>team_session_state]
    STATE --> SYNC[🔄 Sincronização<br/>state_synchronizer.py]
    
    ORCH --> MEM[🧠 Sistema de Memória<br/>Agno Memory v2]
    MEM --> SQLITE[(🗄️ SQLite<br/>pagbank_memory_dev.db<br/>pagbank_sessions.db)]
    MEM --> PATTERNS[🔍 Detector de Padrões<br/>pattern_detector.py]
    
    ORCH --> AGENTS[🤖 Agentes Especialistas<br/>(Single Agents, not Teams)]
    AGENTS --> CARDS[💳 Agente de Cartões<br/>cards_agent.py]
    AGENTS --> ACCOUNT[🏦 Agente Conta Digital<br/>digital_account_agent.py]
    AGENTS --> INVEST[💰 Agente Investimentos<br/>investments_agent.py]
    AGENTS --> CREDIT[💸 Agente de Crédito<br/>credit_agent.py]
    AGENTS --> INSUR[🛡️ Agente de Seguros<br/>insurance_agent.py]
    
    AGENTS --> TOOLS[🛠️ Ferramentas<br/>agent_tools.py]
    AGENTS --> PROMPTS[📝 Prompts<br/>specialist_prompts.py]
    
    ORCH --> ESC[⚠️ Sistemas de Escalação<br/>escalation_manager.py]
    ESC --> HUMAN[👤 Escalação Humana<br/>human_agent_mock.py]
    ESC --> TECH[🔧 Escalação Técnica<br/>technical_escalation_agent.py]
    ESC --> TICK[🎫 Sistema de Tickets<br/>ticket_system.py]
    
    AGENTS --> KB[📚 Base de Conhecimento<br/>pagbank_knowledge.csv]
    KB --> FILTERS[🔍 Filtros por Agente<br/>knowledge_filters]
    KB --> VECTOR[(🎯 PgVector<br/>Embeddings OpenAI)]
    
    style ORCH fill:#fff3e0
    style AGENTS fill:#e1f5fe
    style ESC fill:#ffebee
    style KB fill:#e8f5e8
    style MEM fill:#e3f2fd
    style STATE fill:#f3e5f5
```

### Fluxo de Dados

```
1. Cliente envia mensagem
    ↓
2. Orquestrador processa:
   - Normaliza texto (erros PT-BR)
   - Detecta frustração (0-3)
   - Analisa intenção
    ↓
3. Roteamento (Team mode="route"):
   - Seleciona agente especialista
   - Compartilha estado via team_session_state
   - Habilita contexto agêntico
    ↓
4. Agente Especialista:
   - Ativa "thinking" para raciocínio
   - Busca conhecimento filtrado
   - Acessa memórias do usuário
   - Gera resposta (max 3-4 frases)
    ↓
5. Pós-processamento:
   - Atualiza estado compartilhado
   - Salva na memória
   - Detecta necessidade de escalação
    ↓
6. Resposta ao cliente
```


## 🛠️ Stack Técnico

- **Framework**: Agno (Orquestração Multi-Agente)
- **LLM**: Claude Sonnet 4 (claude-sonnet-4-20250514) com thinking habilitado
- **Arquitetura**: Team (route mode) → Single Agents (não mais teams)
- **Base de Conhecimento**: CSV com embeddings PgVector
- **Memória**: Agno Memory v2 com SqliteMemoryDb
- **Estado Compartilhado**: team_session_state com propagação automática
- **Linguagem**: Python 3.12+
- **Armazenamento**: SQLite para sessões e memória

## 📁 Estrutura do Projeto

```
pagbank/
├── agents/               # Nova estrutura de agentes únicos
│   ├── orchestrator/             # Orquestrador principal
│   │   ├── __init__.py
│   │   └── main_orchestrator.py  # Team mode="route"
│   ├── specialists/              # Agentes especialistas (não times!)
│   │   ├── __init__.py
│   │   ├── base_agent.py        # Classe base para agentes
│   │   ├── cards_agent.py       # Agente de cartões
│   │   ├── digital_account_agent.py  # Agente conta digital
│   │   ├── investments_agent.py # Agente investimentos
│   │   ├── credit_agent.py      # Agente de crédito
│   │   └── insurance_agent.py   # Agente de seguros
│   ├── prompts/                  # Prompts centralizados
│   │   ├── __init__.py
│   │   └── specialist_prompts.py # Todos os prompts
│   └── tools/                    # Ferramentas compartilhadas
│       ├── __init__.py
│       └── agent_tools.py        # Ferramentas dos agentes
├── orchestrator/         # Módulos de suporte (mantidos)
│   ├── routing_logic.py          # Lógica de roteamento
│   ├── frustration_detector.py   # Detector de frustração
│   ├── text_normalizer.py        # Normalizador de texto
│   ├── clarification_handler.py  # Esclarecimentos
│   └── state_synchronizer.py     # Sincronizador de estado
├── teams/                # LEGADO - será removido
├── knowledge/            # Base de conhecimento
│   ├── csv_knowledge_base.py     # Base CSV
│   ├── agentic_filters.py        # Filtros por agente
│   └── pagbank_knowledge.csv     # 571 entradas
├── memory/               # Sistema de memória
│   ├── memory_manager.py         # Agno Memory v2
│   ├── pattern_detector.py       # Detecção de padrões
│   └── session_manager.py        # Sessões
├── escalation_systems/   # Escalação
├── config/               # Configurações
├── data/                 # Bancos SQLite
├── playground.py         # Entry point principal
└── docs/                 # Documentação
```

## 🔧 Configuração

Configurações principais em `config/settings.py`:
- Timeout de roteamento de time: 30s
- Máximo de turnos de conversa: 20
- Limite de frustração: Nível 3
- Timeout de sessão: 30 minutos

## 🔒 Recursos de Segurança

- Detecção de golpes de antecipação de pagamentos
- Proteção de clientes vulneráveis
- Reconhecimento de padrões de fraude
- Avisos de compliance para investimentos
- Manuseio seguro de credenciais

## 🧠 Sistema de Memória

- **Memória Persistente**: Contexto do usuário mantido entre sessões
- **Detecção de Padrões**: Reconhecimento de comportamentos recorrentes
- **Insights Contextuais**: Análise de histórico de interações
- **Estado Compartilhado**: team_session_state sincronizado entre agentes
- **Contexto Agêntico**: Propagação automática com enable_agentic_context=True

## 🎯 Recursos Avançados

### Capacidades dos Agentes
- **Thinking Habilitado**: Raciocínio aprofundado com budget de 1024 tokens
- **Busca Agêntica**: search_knowledge=True com filtros específicos
- **Estado Compartilhado**: Acesso via agent.team_session_state
- **Interações Compartilhadas**: share_member_interactions=True

### Ferramentas Disponíveis
- **search_knowledge**: Busca na base com filtros
- **create_support_ticket**: Criação de tickets
- **normalize_text**: Normalização PT-BR  
- **check_user_history**: Acesso ao histórico
- **pagbank_validator**: Validação CPF/CNPJ/PIX
- **security_checker**: Detecção de fraudes
- **financial_calculator**: Cálculos financeiros

### Recursos do Sistema
- **Normalização de Texto**: Correção automática de erros de português
- **Detecção de Frustração**: Escala 0-3 com keywords e padrões
- **Esclarecimentos Inteligentes**: Máximo 1 pergunta por vez
- **Escalação Automática**: Frustração ≥3 ou palavras-chave
- **Filtragem de Conhecimento**: Por área/departamento

## 👥 Equipe

Desenvolvido com o Framework Agno pelas equipes **Namastex Labs** e **Yaitech**

## 📝 Licença

Proprietário - PagBank 2025